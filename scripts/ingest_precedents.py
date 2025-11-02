"""
Ingest precedents (planning appeals) from JSONL.
Uses sentence-transformers for real embeddings.
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
    input_file = Path("fixtures/lpa_demo/precedents.jsonl")
    
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        return
    
    conn = psycopg.connect(db_url)
    count = 0
    
    with open(input_file) as f:
        for line in f:
            prec = json.loads(line)
            
            # Compute embedding from summary + key points
            text = prec["summary"] + " " + " ".join(prec["key_points"])
            embedding = compute_embedding(text)
            
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO precedent (
                        case_ref, decision, decision_date, inspector,
                        summary, key_points, policy_refs, embedding
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (case_ref) DO UPDATE SET
                        decision = EXCLUDED.decision,
                        summary = EXCLUDED.summary
                """, (
                    prec["case_ref"],
                    prec["decision"],
                    prec.get("decision_date"),
                    prec.get("inspector"),
                    prec["summary"],
                    prec["key_points"],
                    prec["policy_refs"],
                    embedding
                ))
            
            count += 1
    
    conn.commit()
    conn.close()
    
    print(f"✓ Ingested {count} precedents")
    print("  (Using sentence-transformers/all-MiniLM-L6-v2 → padded to 1024d)")

if __name__ == "__main__":
    main()
