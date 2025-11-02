#!/bin/bash
# Seed evidence data via Docker

cat <<'EOF' | docker exec -i tpa-postgres psql -U tpa -d tpa
-- Seed sample evidence data

INSERT INTO evidence (title, type, topic_tags, geographic_scope, author, publisher, year, source_type, key_findings, status, reliability_flags, notes, created_at, updated_at) VALUES
('Westminster Strategic Housing Market Assessment 2024', 'SHMA', ARRAY['housing', 'economy'], 'Westminster City Council', 'GL Hearn', 'Westminster City Council', 2024, 'upload', 'Identified need for 1,200 new homes per year. Strong demand for affordable housing (45% of total need). Need for family housing (3+ beds) particularly acute in zones 2-3.', 'adopted', '{}', 'Core evidence for Local Plan housing policies', NOW(), NOW()),
('London Plan Strategic Flood Risk Assessment', 'SFRA', ARRAY['environment', 'climate', 'infrastructure'], 'Greater London Authority', 'JBA Consulting', 'Greater London Authority', 2023, 'cached_url', '15% of London at significant flood risk. Climate change projections show 20% increase in flood zones by 2050. Sequential test required for all developments in Flood Zone 2 or 3.', 'adopted', '{}', 'Supersedes 2019 SFRA', NOW(), NOW()),
('Camden Transport Strategy Evidence Base', 'Transport Assessment', ARRAY['transport', 'infrastructure', 'climate'], 'Camden Council', 'Transport for London', 'Camden Council', 2022, 'upload', 'Public transport accessibility (PTAL) ranges from 1a to 6b. Northern Line at capacity during peak hours. 30% of trips by active travel by 2030 target.', 'adopted', '{}', 'Supports sustainable transport policies', NOW(), NOW()),
('Islington Whole Plan Viability Assessment', 'Viability Study', ARRAY['housing', 'economy', 'infrastructure'], 'Islington Council', 'BNP Paribas Real Estate', 'Islington Council', 2021, 'upload', '35% affordable housing viable in high value areas, 25% elsewhere. CIL rates supportable up to £200/sqm in most areas. Infrastructure funding gap of £150m over plan period.', 'adopted', '{"stale": true}', 'May need updating due to post-2021 market changes', NOW(), NOW()),
('Bristol Strategic Housing and Employment Land Availability Assessment', 'SHELAA', ARRAY['housing', 'economy', 'environment'], 'Bristol City Council', 'Arup', 'Bristol City Council', 2023, 'cached_url', 'Capacity for 25,000 new homes on identified sites. 60% on brownfield land. Major employment sites include Temple Quarter Enterprise Zone (50ha).', 'adopted', '{}', 'Annual update due Q1 2025', NOW(), NOW()),
('City of London Heritage and Tall Buildings Study', 'Heritage Assessment', ARRAY['heritage', 'design', 'environment'], 'City of London Corporation', 'Historic England', 'City of London Corporation', 2020, 'upload', 'Protected views framework covers 15 key vistas. Eastern Cluster suitable for tall buildings (up to 300m). Conservation areas cover 40% of the City.', 'adopted', '{"stale": true}', 'Pre-dates recent tall building applications', NOW(), NOW());

-- Create initial versions for each evidence item
INSERT INTO evidence_version (evidence_id, version_number, cas_hash, fetched_at, robots_allowed)
SELECT id, 1, 'mock_hash_' || id::text, NOW(), TRUE
FROM evidence;

-- Show results
SELECT COUNT(*) as evidence_count FROM evidence;
SELECT title, type, year FROM evidence ORDER BY id;
EOF
