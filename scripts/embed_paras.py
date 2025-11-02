"""
Compute embeddings for policy paragraphs and store in PostgreSQL.
Uses sentence-transformers for real embeddings (all-MiniLM-L6-v2 produces 384-dim).
Note: Schema expects vector(1024); we pad or use a different model for production.
For demo purposes, we'll use all-mpnet-base-v2 which is 768-dim and pad to 1024.
"""
import json
import os
from pathlib import Path
import psycopg

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_MODEL = None

def _get_model():
    global _MODEL
    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _MODEL = SentenceTransformer(_MODEL_NAME)
        except Exception as e:
            raise RuntimeError("sentence-transformers is required to run this script") from e
    return _MODEL

def _pad_1024(vec):
    if len(vec) >= 1024:
        return vec[:1024]
    return vec + [0.0] * (1024 - len(vec))

def compute_embedding(text: str) -> list:
    """Return 1024-dim embedding using sentence-transformers, padded to 1024."""
    model = _get_model()
    v = model.encode([text], normalize_embeddings=True)[0].tolist()
    return _pad_1024(v)

def main():
    db_url = os.getenv("DATABASE_URL", "postgresql://tpa:tpa@127.0.0.1:5432/tpa")
    input_file = Path("fixtures/lpa_demo/policy_paras.jsonl")
    
    if not input_file.exists():
        print(f"Error: {input_file} not found. Run extract_paras.py first.")
        return
    
    print("Connecting to database...")
    conn = psycopg.connect(db_url)
    
    # Insert policy doc if not exists
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO policy (doc_id, title, authority, doc_type)
            VALUES ('local_plan', 'Local Plan 2024', 'Demo LPA', 'local_plan')
            ON CONFLICT DO NOTHING
            RETURNING id
        """)
        result = cur.fetchone()
        policy_id = result[0] if result else 1
    
    print(f"Processing paragraphs from {input_file}...")
    count = 0
    
    with open(input_file) as f:
        for line in f:
            para = json.loads(line)
            embedding = compute_embedding(para["text"])
            
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO policy_para (policy_id, para_ref, text, page, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                """, (policy_id, para["para_ref"], para["text"], para["page"], embedding))
            
            count += 1
    
    conn.commit()
    conn.close()
    
    print(f"✓ Inserted {count} paragraphs with embeddings")
    print("  (Using sentence-transformers/all-MiniLM-L6-v2 → padded to 1024d)")

if __name__ == "__main__":
    main()
