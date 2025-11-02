"""
Seed sample evidence data for demonstration
Can be run via docker exec or directly if psycopg is installed
"""
import sys
import json
from datetime import datetime

SAMPLE_EVIDENCE = [
    {
        "title": "Westminster Strategic Housing Market Assessment 2024",
        "type": "SHMA",
        "topic_tags": ["housing", "economy"],
        "geographic_scope": "Westminster City Council",
        "author": "GL Hearn",
        "publisher": "Westminster City Council",
        "year": 2024,
        "source_type": "upload",
        "key_findings": "Identified need for 1,200 new homes per year. Strong demand for affordable housing (45% of total need). Need for family housing (3+ beds) particularly acute in zones 2-3.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Core evidence for Local Plan housing policies",
    },
    {
        "title": "London Plan Strategic Flood Risk Assessment",
        "type": "SFRA",
        "topic_tags": ["environment", "climate", "infrastructure"],
        "geographic_scope": "Greater London Authority",
        "author": "JBA Consulting",
        "publisher": "Greater London Authority",
        "year": 2023,
        "source_type": "cached_url",
        "key_findings": "15% of London at significant flood risk. Climate change projections show 20% increase in flood zones by 2050. Sequential test required for all developments in Flood Zone 2 or 3.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Supersedes 2019 SFRA",
    },
    {
        "title": "Camden Transport Strategy Evidence Base",
        "type": "Transport Assessment",
        "topic_tags": ["transport", "infrastructure", "climate"],
        "geographic_scope": "Camden Council",
        "author": "Transport for London",
        "publisher": "Camden Council",
        "year": 2022,
        "source_type": "upload",
        "key_findings": "Public transport accessibility (PTAL) ranges from 1a to 6b. Northern Line at capacity during peak hours. 30% of trips by active travel by 2030 target.",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Supports sustainable transport policies",
    },
    {
        "title": "Islington Whole Plan Viability Assessment",
        "type": "Viability Study",
        "topic_tags": ["housing", "economy", "infrastructure"],
        "geographic_scope": "Islington Council",
        "author": "BNP Paribas Real Estate",
        "publisher": "Islington Council",
        "year": 2021,
        "source_type": "upload",
        "key_findings": "35% affordable housing viable in high value areas, 25% elsewhere. CIL rates supportable up to £200/sqm in most areas. Infrastructure funding gap of £150m over plan period.",
        "status": "adopted",
        "reliability_flags": {"stale": True},
        "notes": "May need updating due to post-2021 market changes",
    },
    {
        "title": "Bristol Strategic Housing and Employment Land Availability Assessment",
        "type": "SHELAA",
        "topic_tags": ["housing", "economy", "environment"],
        "geographic_scope": "Bristol City Council",
        "author": "Arup",
        "publisher": "Bristol City Council",
        "year": 2023,
        "source_type": "cached_url",
        "key_findings": "Capacity for 25,000 new homes on identified sites. 60% on brownfield land. Major employment sites include Temple Quarter Enterprise Zone (50ha).",
        "status": "adopted",
        "reliability_flags": {},
        "notes": "Annual update due Q1 2025",
    },
    {
        "title": "City of London Heritage and Tall Buildings Study",
        "type": "Heritage Assessment",
        "topic_tags": ["heritage", "design", "environment"],
        "geographic_scope": "City of London Corporation",
        "author": "Historic England",
        "publisher": "City of London Corporation",
        "year": 2020,
        "source_type": "upload",
        "key_findings": "Protected views framework covers 15 key vistas. Eastern Cluster suitable for tall buildings (up to 300m). Conservation areas cover 40% of the City.",
        "status": "adopted",
        "reliability_flags": {"stale": True},
        "notes": "Pre-dates recent tall building applications",
    },
]

def seed_evidence():
    """Insert sample evidence into database"""
    try:
        import psycopg
        conn = psycopg.connect("postgresql://tpa:tpa@127.0.0.1:5432/tpa")
    except ImportError:
        print("❌ psycopg not installed. Install with: pip install psycopg[binary]")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Could not connect to database: {e}")
        sys.exit(1)
    
    try:
        with conn.cursor() as cur:
            for item in SAMPLE_EVIDENCE:
                # Insert evidence item
                cur.execute("""
                    INSERT INTO evidence (
                        title, type, topic_tags, geographic_scope,
                        author, publisher, year, source_type,
                        key_findings, status, reliability_flags, notes,
                        created_at, updated_at
                    ) VALUES (
                        %(title)s, %(type)s, %(topic_tags)s, %(geographic_scope)s,
                        %(author)s, %(publisher)s, %(year)s, %(source_type)s,
                        %(key_findings)s, %(status)s, %(reliability_flags)s::jsonb, %(notes)s,
                        NOW(), NOW()
                    )
                    RETURNING id
                """, item)
                
                evidence_id = cur.fetchone()[0]
                
                # Create initial version
                cur.execute("""
                    INSERT INTO evidence_version (
                        evidence_id, version_number, cas_hash,
                        fetched_at, robots_allowed
                    ) VALUES (
                        %s, 1, %s, NOW(), TRUE
                    )
                """, (evidence_id, f"mock_hash_{evidence_id}"))
                
                print(f"✓ Added: {item['title']}")
        
        conn.commit()
        print(f"\n✅ Seeded {len(SAMPLE_EVIDENCE)} evidence items")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🌱 Seeding evidence database...\n")
    try:
        seed_evidence()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
