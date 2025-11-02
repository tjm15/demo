-- The Planner's Assistant - Database Schema
-- PostgreSQL 17 + PostGIS 3.6 + pgvector

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- Policy documents table
CREATE TABLE policy (
    id SERIAL PRIMARY KEY,
    doc_id TEXT NOT NULL,
    title TEXT NOT NULL,
    authority TEXT,
    doc_type TEXT,
    published_date DATE,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Policy paragraphs with embeddings
CREATE TABLE policy_para (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER REFERENCES policy(id) ON DELETE CASCADE,
    para_ref TEXT NOT NULL,
    text TEXT NOT NULL,
    page INTEGER,
    embedding vector(1024),
    tsv tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, text)) STORED,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Policy relationships (cross-references)
CREATE TABLE policy_rel (
    id SERIAL PRIMARY KEY,
    from_policy_id INTEGER REFERENCES policy(id),
    to_policy_id INTEGER REFERENCES policy(id),
    rel_type TEXT NOT NULL, -- 'reference', 'supersedes', 'exception'
    notes TEXT
);

-- Policy tests/standards
CREATE TABLE policy_test (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER REFERENCES policy(id),
    test_name TEXT NOT NULL,
    operator TEXT, -- '>=', '<=', '==', etc.
    value NUMERIC,
    unit TEXT,
    notes TEXT
);

-- Spatial layers
CREATE TABLE layer (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    layer_type TEXT NOT NULL, -- 'constraint', 'designation', 'zone'
    authority TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Layer geometries
CREATE TABLE layer_geom (
    id SERIAL PRIMARY KEY,
    layer_id INTEGER REFERENCES layer(id) ON DELETE CASCADE,
    name TEXT,
    geom GEOMETRY(GEOMETRY, 27700), -- EPSG:27700 British National Grid
    properties JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Precedents (planning appeals, decisions)
CREATE TABLE precedent (
    id SERIAL PRIMARY KEY,
    case_ref TEXT NOT NULL UNIQUE,
    decision TEXT NOT NULL, -- 'Allowed', 'Dismissed', 'Split'
    decision_date DATE,
    inspector TEXT,
    summary TEXT,
    key_points TEXT[],
    policy_refs TEXT[],
    embedding vector(1024),
    tsv tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, summary)) STORED,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Source provenance (security audit)
CREATE TABLE source_provenance (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    sha256 TEXT NOT NULL,
    domain TEXT NOT NULL,
    robots_allowed BOOLEAN DEFAULT TRUE,
    ingested_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_policy_para_policy_id ON policy_para(policy_id);
CREATE INDEX idx_policy_para_embedding ON policy_para USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_policy_para_tsv ON policy_para USING GIN (tsv);
CREATE INDEX idx_layer_geom_geom ON layer_geom USING GIST(geom);
CREATE INDEX idx_precedent_embedding ON precedent USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_precedent_tsv ON precedent USING GIN (tsv);
CREATE INDEX idx_source_provenance_domain ON source_provenance(domain);
CREATE INDEX idx_source_provenance_url ON source_provenance(source_url);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tpa;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tpa;
