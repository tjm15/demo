"""
Embed evidence key findings into evidence_chunk with pgvector embeddings.

- For each evidence item, find the latest evidence_version
- Generate 1..N text chunks (from key_findings or synthesized metadata)
- Compute 1024-d embeddings using apps/kernel/embedding.embed
- Insert rows into evidence_chunk (chunk_index, text, embedding)

Prereqs:
- PostgreSQL with pgvector extension, schema loaded (scripts/evidence_schema.sql)
- Python deps installed per apps/kernel/requirements.txt (sentence-transformers, torch)

Usage:
  python scripts/embed_evidence_chunks.py [--limit N]

Tip:
  To use the same Python environment as the kernel:
    cd apps/kernel && . .venv/bin/activate && python ../../scripts/embed_evidence_chunks.py
"""
from __future__ import annotations

import os
import re
import sys
import math
import argparse
from typing import List, Tuple

import psycopg

# Make kernel modules importable (embedding)
ROOT = os.path.dirname(os.path.dirname(__file__))
KERNEL_DIR = os.path.join(ROOT, 'apps', 'kernel')
if KERNEL_DIR not in sys.path:
    sys.path.insert(0, KERNEL_DIR)

from embedding import embed as embed_vec  # uses sentence-transformers and pads to 1024

DB_URL = os.getenv("DATABASE_URL", "postgresql://tpa:tpa@127.0.0.1:5432/tpa")


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _chunk_text(text: str, target_len: int = 480, overlap: int = 64) -> List[str]:
    """Chunk text roughly by characters with a bit of overlap.
    Keeps chunks in the 300-600 char range for decent embedding semantics.
    """
    text = _normalize_ws(text)
    if not text:
        return []

    if len(text) <= target_len:
        return [text]

    chunks: List[str] = []
    start = 0
    step = max(1, target_len - overlap)
    while start < len(text):
        end = min(len(text), start + target_len)
        # try to break on sentence boundary
        sub = text[start:end]
        last_period = sub.rfind('.')
        if last_period > target_len * 0.4:
            end = start + last_period + 1
            sub = text[start:end]
        chunks.append(sub.strip())
        if end >= len(text):
            break
        start = end - overlap
    return [c for c in (s.strip() for s in chunks) if c]


def _synth_meta(e: tuple) -> str:
    """Synthesize a minimal text if key_findings is missing.
    e row columns: (id,title,type,topic_tags,geographic_scope,author,publisher,year,source_type,spatial_layer_ref,key_findings,status,reliability_flags,notes,created_at,updated_at)
    """
    _, title, etype, topic_tags, scope, author, publisher, year, *_ = e
    parts = [title or ""]
    if etype:
        parts.append(f"Type: {etype}")
    if scope:
        parts.append(f"Geography: {scope}")
    if year:
        parts.append(f"Year: {year}")
    if author:
        parts.append(f"Author: {author}")
    if publisher:
        parts.append(f"Publisher: {publisher}")
    if topic_tags:
        parts.append(f"Topics: {', '.join(topic_tags)}")
    return ". ".join([p for p in parts if p])


def upsert_chunks(limit: int | None = None) -> Tuple[int, int]:
    """Create embeddings for evidence without chunks. Returns (items, chunks)."""
    created_items = 0
    created_chunks = 0

    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            # Find evidence + latest version where no chunks exist
            cur.execute(
                """
                SELECT e.*, ev.id as version_id
                FROM evidence e
                JOIN LATERAL (
                    SELECT id
                    FROM evidence_version
                    WHERE evidence_id = e.id
                    ORDER BY version_number DESC NULLS LAST, id DESC
                    LIMIT 1
                ) ev ON true
                LEFT JOIN evidence_chunk ec ON ec.evidence_version_id = ev.id
                WHERE ec.id IS NULL
                ORDER BY e.updated_at DESC
                """
            )
            rows = cur.fetchall()

            if limit is not None:
                rows = rows[:limit]

            for row in rows:
                version_id = row[16]  # appended alias position after e.* (0..15)
                text = (row[10] or "").strip()  # key_findings
                if not text:
                    text = _synth_meta(row)
                chunks = _chunk_text(text)
                if not chunks:
                    continue

                created_items += 1
                for idx, ch in enumerate(chunks):
                    vec = embed_vec(ch)
                    cur.execute(
                        """
                        INSERT INTO evidence_chunk (evidence_version_id, chunk_index, text, embedding)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (version_id, idx, ch, vec),
                    )
                    created_chunks += 1
            conn.commit()

    return created_items, created_chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Max evidence items to process")
    args = ap.parse_args()

    items, chunks = upsert_chunks(limit=args.limit)
    print(f"✓ Embedded chunks for {items} evidence item(s), inserted {chunks} chunk(s)")


if __name__ == "__main__":
    main()
