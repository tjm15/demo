"""
Ingest policy graph (relationships and tests) from JSON.
"""
import json
import os
from pathlib import Path
import psycopg

def main():
    db_url = os.getenv("DATABASE_URL", "postgresql://tpa:tpa@127.0.0.1:5432/tpa")
    input_file = Path("fixtures/lpa_demo/policy_graph.json")
    
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        return
    
    print("Loading policy graph...")
    with open(input_file) as f:
        data = json.load(f)
    
    conn = psycopg.connect(db_url)
    
    # Create policy ID mapping
    policy_map = {}
    for policy in data["policies"]:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO policy (doc_id, title, authority, doc_type)
                VALUES (%s, %s, 'Demo LPA', 'policy')
                RETURNING id
            """, (policy["id"], policy["title"]))
            policy_map[policy["id"]] = cur.fetchone()[0]
        conn.commit()
    
    # Insert relationships
    for policy in data["policies"]:
        from_id = policy_map[policy["id"]]
        
        for ref in policy["references"]:
            if ref in policy_map:
                to_id = policy_map[ref]
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO policy_rel (from_policy_id, to_policy_id, rel_type)
                        VALUES (%s, %s, 'reference')
                        ON CONFLICT DO NOTHING
                    """, (from_id, to_id))
        
        # Insert tests
        for test in policy.get("tests", []):
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO policy_test (policy_id, test_name, operator, value, unit)
                    VALUES (%s, %s, %s, %s, %s)
                """, (from_id, test["name"], test["operator"], test["value"], test["unit"]))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Ingested {len(data['policies'])} policies with relationships")

if __name__ == "__main__":
    main()
