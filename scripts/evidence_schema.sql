-- Evidence Base Schema Extension
-- Adds evidence management tables to support the Evidence Base mode

-- Evidence items (documents, datasets, studies)
CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL, -- SHMA, HENA, SFRA, Viability, SHELAA, etc.
    topic_tags TEXT[] DEFAULT '{}', -- housing, economy, transport, climate, etc.
    geographic_scope TEXT, -- LPA name, sub-area, corridor
    author TEXT,
    publisher TEXT,
    year INTEGER,
    source_type TEXT NOT NULL, -- 'upload', 'cached_url', 'live_url'
    spatial_layer_ref INTEGER REFERENCES layer(id) ON DELETE SET NULL,
    key_findings TEXT,
    status TEXT DEFAULT 'draft', -- draft, adopted, superseded
    reliability_flags JSONB DEFAULT '{}', -- {currency: bool, method: string, ...}
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Evidence versions (immutable audit trail)
CREATE TABLE IF NOT EXISTS evidence_version (
    id SERIAL PRIMARY KEY,
    evidence_id INTEGER REFERENCES evidence(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    cas_hash TEXT NOT NULL, -- content-addressed storage hash (SHA-256)
    source_url TEXT,
    etag TEXT,
    last_modified TIMESTAMP,
    file_size BIGINT,
    mime_type TEXT,
    fetched_at TIMESTAMP DEFAULT NOW(),
    fetched_by TEXT,
    license TEXT,
    robots_allowed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(evidence_id, version_number)
);

-- Evidence text chunks (for retrieval)
CREATE TABLE IF NOT EXISTS evidence_chunk (
    id SERIAL PRIMARY KEY,
    evidence_version_id INTEGER REFERENCES evidence_version(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    page INTEGER,
    section_ref TEXT,
    embedding vector(1024),
    tsv tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, text)) STORED,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Evidence to policy links
CREATE TABLE IF NOT EXISTS evidence_policy_link (
    id SERIAL PRIMARY KEY,
    evidence_id INTEGER REFERENCES evidence(id) ON DELETE CASCADE,
    policy_id INTEGER REFERENCES policy(id) ON DELETE CASCADE,
    rationale TEXT,
    strength TEXT DEFAULT 'supporting', -- 'core', 'supporting', 'tangential'
    created_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT,
    UNIQUE(evidence_id, policy_id)
);

-- Evidence spatial layers (many-to-many)
CREATE TABLE IF NOT EXISTS evidence_layer (
    id SERIAL PRIMARY KEY,
    evidence_id INTEGER REFERENCES evidence(id) ON DELETE CASCADE,
    layer_id INTEGER REFERENCES layer(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(evidence_id, layer_id)
);

-- Evidence cache manifest (proxy downloads)
CREATE TABLE IF NOT EXISTS evidence_cache (
    id SERIAL PRIMARY KEY,
    cache_key TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    domain TEXT NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    content_type TEXT,
    size_bytes BIGINT,
    sha256 TEXT NOT NULL,
    etag TEXT,
    last_modified TEXT,
    robots_allowed BOOLEAN DEFAULT TRUE,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(type);
CREATE INDEX IF NOT EXISTS idx_evidence_year ON evidence(year);
CREATE INDEX IF NOT EXISTS idx_evidence_status ON evidence(status);
CREATE INDEX IF NOT EXISTS idx_evidence_topic_tags ON evidence USING GIN(topic_tags);
CREATE INDEX IF NOT EXISTS idx_evidence_version_evidence_id ON evidence_version(evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_version_cas_hash ON evidence_version(cas_hash);
CREATE INDEX IF NOT EXISTS idx_evidence_chunk_version_id ON evidence_chunk(evidence_version_id);
CREATE INDEX IF NOT EXISTS idx_evidence_chunk_embedding ON evidence_chunk USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_evidence_chunk_tsv ON evidence_chunk USING GIN (tsv);
CREATE INDEX IF NOT EXISTS idx_evidence_policy_link_evidence ON evidence_policy_link(evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_policy_link_policy ON evidence_policy_link(policy_id);
CREATE INDEX IF NOT EXISTS idx_evidence_cache_domain ON evidence_cache(domain);
CREATE INDEX IF NOT EXISTS idx_evidence_cache_sha256 ON evidence_cache(sha256);

-- Grant permissions
GRANT ALL PRIVILEGES ON evidence TO tpa;
GRANT ALL PRIVILEGES ON evidence_version TO tpa;
GRANT ALL PRIVILEGES ON evidence_chunk TO tpa;
GRANT ALL PRIVILEGES ON evidence_policy_link TO tpa;
GRANT ALL PRIVILEGES ON evidence_layer TO tpa;
GRANT ALL PRIVILEGES ON evidence_cache TO tpa;
GRANT ALL PRIVILEGES ON SEQUENCE evidence_id_seq TO tpa;
GRANT ALL PRIVILEGES ON SEQUENCE evidence_version_id_seq TO tpa;
GRANT ALL PRIVILEGES ON SEQUENCE evidence_chunk_id_seq TO tpa;
GRANT ALL PRIVILEGES ON SEQUENCE evidence_policy_link_id_seq TO tpa;
GRANT ALL PRIVILEGES ON SEQUENCE evidence_layer_id_seq TO tpa;
GRANT ALL PRIVILEGES ON SEQUENCE evidence_cache_id_seq TO tpa;
