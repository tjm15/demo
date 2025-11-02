-- Add generated tsvector columns and GIN indexes for fast full-text search
-- Run this after the main schema.sql to enhance search performance

\c tpa

-- Add tsvector column to policy_para
ALTER TABLE policy_para 
ADD COLUMN IF NOT EXISTS text_tsv tsvector 
GENERATED ALWAYS AS (to_tsvector('english', text)) STORED;

-- Add GIN index on the tsvector column
CREATE INDEX IF NOT EXISTS idx_policy_para_text_tsv ON policy_para USING GIN(text_tsv);

-- Add tsvector column to precedent
ALTER TABLE precedent 
ADD COLUMN IF NOT EXISTS summary_tsv tsvector 
GENERATED ALWAYS AS (to_tsvector('english', summary)) STORED;

-- Add GIN index on the tsvector column for precedent
CREATE INDEX IF NOT EXISTS idx_precedent_summary_tsv ON precedent USING GIN(summary_tsv);

-- Note: This will automatically populate for existing rows since it's a GENERATED column
-- For large tables, consider CREATE INDEX CONCURRENTLY in production
