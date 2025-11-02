"""Light Proxy client for kernel.

Calls the internal proxy with token, performs /search, /download, /extract.
"""
from __future__ import annotations

import os
import json
from typing import Dict, Any, List, Optional
import aiohttp

PROXY_BASE_URL = os.getenv("PROXY_BASE_URL", "http://127.0.0.1:8082")
PROXY_TOKEN = os.getenv("PROXY_INTERNAL_TOKEN", "change-me-long-random")
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "60"))


async def proxy_search(q: str) -> List[Dict[str, Any]]:
    url = f"{PROXY_BASE_URL}/search"
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
    headers = {"X-Proxy-Token": PROXY_TOKEN}
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json={"q": q}, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("results", [])


async def proxy_download(url_in: str) -> Dict[str, Any]:
    url = f"{PROXY_BASE_URL}/download"
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
    headers = {"X-Proxy-Token": PROXY_TOKEN}
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json={"url": url_in}, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()


async def proxy_extract(cache_key: str) -> Dict[str, Any]:
    url = f"{PROXY_BASE_URL}/extract"
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
    headers = {"X-Proxy-Token": PROXY_TOKEN}
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json={"cache_key": cache_key}, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()


def domain_from_url(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower()
    except Exception:
        return ""
