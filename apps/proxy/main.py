"""
Light Proxy Service for The Planner's Assistant
Fetches, caches, and extracts policy documents with security controls.
"""
import os
import re
import gzip
import time
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, HttpUrl
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser
import yaml
import aiohttp
import psycopg

app = FastAPI(title="TPA Proxy Service")

# Configuration
PROXY_INTERNAL_TOKEN = os.getenv("PROXY_INTERNAL_TOKEN", "change-me-long-random")
ALLOWED_SOURCES_PATH = os.getenv("ALLOWED_SOURCES_PATH", "apps/proxy/allowed_sources.yml")
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_DB = CACHE_DIR / "manifest.db"
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "60"))
USER_AGENT = os.getenv("PROXY_USER_AGENT", "TPA-Proxy/1.0")

# Initialize cache database
def init_cache_db() -> None:
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache_entries (
            cache_key TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            content_type TEXT,
            size_bytes INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_cache_db()

# Load allowed sources
def load_allowed_sources() -> Dict[str, Any]:
    if not Path(ALLOWED_SOURCES_PATH).exists():
        return {
            "schemes": ["https"],
            "domains": ["www.gov.uk", "www.london.gov.uk", "www.planningportal.co.uk"],
            "paths_regex": [".*"],
            "content_types": ["application/pdf", "text/html"],
            "max_bytes": 10485760,  # 10MB
            "disallowed_query_keys": []
        }
    with open(ALLOWED_SOURCES_PATH, 'r') as f:
        return yaml.safe_load(f)

ALLOWED_SOURCES = load_allowed_sources()

# Database (for provenance)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://tpa:tpa@127.0.0.1:5432/tpa")
KERNEL_BASE_URL = os.getenv("KERNEL_BASE_URL", "http://127.0.0.1:8081")

def db_conn():
    return psycopg.connect(DATABASE_URL)

# Simple per-domain token bucket
RATE_BUCKETS: Dict[str, Dict[str, Any]] = {}
RATE_REFILL_PER_SEC = 1.0  # tokens per second
RATE_BUCKET_SIZE = 5       # max burst

def rate_limit_check(domain: str):
    now = time.time()
    b = RATE_BUCKETS.get(domain)
    if not b:
        RATE_BUCKETS[domain] = {"tokens": RATE_BUCKET_SIZE - 1, "ts": now}
        return
    # Refill
    elapsed = now - b["ts"]
    b["tokens"] = min(RATE_BUCKET_SIZE, b["tokens"] + elapsed * RATE_REFILL_PER_SEC)
    b["ts"] = now
    if b["tokens"] < 1:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded for domain {domain}")
    b["tokens"] -= 1

async def robots_allowed(url: str, session: aiohttp.ClientSession) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status >= 400:
                # No robots file → allow by default per runbook "where present"
                return True
            text = await resp.text()
    except Exception:
        return True
    rp = robotparser.RobotFileParser()
    rp.parse(text.splitlines())
    return rp.can_fetch(USER_AGENT, parsed.path)

# Models
class SearchRequest(BaseModel):
    q: str

class DownloadRequest(BaseModel):
    url: HttpUrl

class ExtractRequest(BaseModel):
    cache_key: str

class IngestRequest(BaseModel):
    paras: List[Dict[str, Any]]
    source_url: Optional[str] = None
    title: Optional[str] = None
    sha256: Optional[str] = None

class SourceCheck(BaseModel):
    allowed: bool
    reason: Optional[str] = None

# Security functions
def check_url_allowed(url: str) -> SourceCheck:
    """Check if URL is allowed based on security policy."""
    parsed = urlparse(str(url))
    
    # Check scheme
    if parsed.scheme not in ALLOWED_SOURCES["schemes"]:
        return SourceCheck(allowed=False, reason=f"Scheme {parsed.scheme} not allowed")
    
    # Check domain
    domain = parsed.netloc.lower()
    domain_match = any(
        domain == allowed_domain or domain.endswith(f".{allowed_domain}")
        for allowed_domain in ALLOWED_SOURCES["domains"]
    )
    if not domain_match:
        return SourceCheck(allowed=False, reason=f"Domain {domain} not in allow-list")
    
    # Check path regex
    path_match = any(
        re.match(pattern, parsed.path)
        for pattern in ALLOWED_SOURCES["paths_regex"]
    )
    if not path_match:
        return SourceCheck(allowed=False, reason=f"Path {parsed.path} doesn't match allowed patterns")
    
    # Check for disallowed query keys
    if parsed.query:
        query_params = [p.split('=')[0] for p in parsed.query.split('&')]
        disallowed = [k for k in query_params if k in ALLOWED_SOURCES.get("disallowed_query_keys", [])]
        if disallowed:
            return SourceCheck(allowed=False, reason=f"Query contains disallowed keys: {disallowed}")
    
    return SourceCheck(allowed=True)

async def guarded_head(url: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Perform HEAD request with security checks."""
    try:
        async with session.head(url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as resp:
            content_type = resp.headers.get('Content-Type', '').split(';')[0].strip()
            content_length = int(resp.headers.get('Content-Length', 0))
            
            # Check final URL after redirects
            final_url = str(resp.url)
            check = check_url_allowed(final_url)
            if not check.allowed:
                return {"error": f"Redirect target not allowed: {check.reason}"}
            
            # Check content type
            if content_type not in ALLOWED_SOURCES["content_types"]:
                return {"error": f"Content-Type {content_type} not allowed"}
            
            # Check size
            if content_length > ALLOWED_SOURCES["max_bytes"]:
                return {"error": f"Content size {content_length} exceeds limit"}
            
            return {
                "url": final_url,
                "content_type": content_type,
                "content_length": content_length
            }
    except Exception as e:
        return {"error": str(e)}

def verify_auth(x_proxy_token: Optional[str] = Header(None)):
    """Verify internal proxy token."""
    if x_proxy_token != PROXY_INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid proxy token")

# Endpoints
@app.get("/status")
async def status():
    return {"status": "ok", "service": "tpa-proxy"}

@app.post("/search")
async def search(req: SearchRequest, _: None = Depends(verify_auth)):
    """Search for policy documents (placeholder - returns mock results)."""
    # In production, this would search government/LPA domains
    return {
        "results": [
            {
                "title": f"Policy Document matching '{req.q}'",
                "url": "https://www.gov.uk/example/policy.pdf",
                "snippet": "Relevant policy guidance..."
            }
        ]
    }

@app.post("/download")
async def download(req: DownloadRequest, _: None = Depends(verify_auth)):
    """Download a file with security checks and caching."""
    url = str(req.url)
    
    # Check if URL is allowed
    check = check_url_allowed(url)
    if not check.allowed:
        raise HTTPException(status_code=403, detail=f"URL not allowed: {check.reason}")
    
    # Rate limit per domain
    parsed = urlparse(url)
    rate_limit_check(parsed.netloc)

    # Generate cache key
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    cache_key = f"GET_{url_hash}"
    cache_path = CACHE_DIR / f"{cache_key}.bin"
    
    # Check cache
    if cache_path.exists():
        return {"cache_key": cache_key, "cached": True}
    
    # Download
    async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        # First, HEAD request for security check
        head_result = await guarded_head(url, session)
        if "error" in head_result:
            raise HTTPException(status_code=400, detail=head_result["error"])
        
        # robots.txt check if present
        robots_ok = await robots_allowed(url, session)
        if not robots_ok:
            raise HTTPException(status_code=403, detail="robots.txt disallows fetching this path")

        # Now GET the content
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)) as resp:
                content = await resp.read()
                
                # Verify MIME magic matches declared type
                # (simplified check)
                if len(content) > 4:
                    magic = content[:4]
                    if magic == b'%PDF' and 'pdf' not in head_result["content_type"]:
                        raise HTTPException(status_code=400, detail="MIME mismatch: PDF magic but non-PDF content-type")
                    if content[:1] == b'<' and 'html' not in head_result["content_type"]:
                        raise HTTPException(status_code=400, detail="MIME mismatch: HTML content but non-HTML content-type")
                
                # Store in cache
                with open(cache_path, 'wb') as f:
                    f.write(content)
                
                # Record in manifest
                sha256_hash = hashlib.sha256(content).hexdigest()
                conn = sqlite3.connect(CACHE_DB)
                conn.execute(
                    "INSERT OR REPLACE INTO cache_entries VALUES (?, ?, ?, ?, ?, ?)",
                    (cache_key, url, datetime.utcnow().isoformat(), sha256_hash,
                     head_result["content_type"], len(content))
                )
                conn.commit()
                conn.close()

                # Write provenance to database
                try:
                    with db_conn() as db:
                        domain = urlparse(url).netloc
                        db.execute(
                            """
                            INSERT INTO source_provenance (source_url, fetched_at, sha256, domain, robots_allowed)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (url, datetime.utcnow(), sha256_hash, domain, True)
                        )
                        db.commit()
                except Exception:
                    # Best-effort provenance; do not break download on DB error
                    pass
                
                return {
                    "cache_key": cache_key,
                    "cached": False,
                    "sha256": sha256_hash,
                    "size_bytes": len(content)
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.post("/extract")
async def extract(req: ExtractRequest, _: None = Depends(verify_auth)):
    """Extract text paragraphs from cached document."""
    cache_path = CACHE_DIR / f"{req.cache_key}.bin"
    extract_path = CACHE_DIR / f"EXTRACT_{req.cache_key}.json.gz"
    
    if not cache_path.exists():
        raise HTTPException(status_code=404, detail="Cache key not found")
    
    # Check if already extracted
    if extract_path.exists():
        with gzip.open(extract_path, 'rt', encoding='utf-8') as f:
            return json.load(f)
    
    # Get content type from manifest
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.execute("SELECT content_type FROM cache_entries WHERE cache_key = ?", (req.cache_key,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Cache entry not found in manifest")
    
    content_type = row[0]
    
    # Extract based on content type
    with open(cache_path, 'rb') as f:
        content = f.read()
    
    paragraphs = []
    
    if 'pdf' in content_type:
        # Simplified PDF extraction (in production, use pdfminer or surya-ocr)
        paragraphs = [
            {"text": "Sample extracted paragraph from PDF", "page": 1, "para_idx": 0}
        ]
    elif 'html' in content_type:
        # HTML extraction
        soup = BeautifulSoup(content, 'html.parser')
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for idx, elem in enumerate(text_elements):
            text = elem.get_text(strip=True)
            if text:
                paragraphs.append({
                    "text": text,
                    "tag": elem.name,
                    "para_idx": idx
                })
    
    result = {"paragraphs": paragraphs, "count": len(paragraphs)}
    
    # Cache extraction
    with gzip.open(extract_path, 'wt', encoding='utf-8') as f:
        json.dump(result, f)
    
    return result

@app.post("/ingest")
async def ingest(req: IngestRequest, _: None = Depends(verify_auth)):
    """Forward paragraphs to kernel for ingestion."""
    kernel_url = os.getenv("KERNEL_BASE_URL", "http://127.0.0.1:8081")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{kernel_url}/services/ingest/paras",
                json={
                    "source_url": "http://example.com/placeholder",
                    "title": "Ingested Document",
                    "paragraphs": [{"text": p.get("text", ""), "page": p.get("page")} for p in req.paras]
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status >= 400:
                    detail = await resp.text()
                    raise HTTPException(status_code=resp.status, detail=f"Kernel ingest failed: {detail}")
                data = await resp.json()
                return {"ingested": data.get("inserted", len(req.paras)), "policy_id": data.get("policy_id")}
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Kernel unreachable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest forward failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8082)
