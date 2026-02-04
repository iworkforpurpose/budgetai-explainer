-- ============================================================================
-- Supabase Setup SQL for Budget 2026 AI Platform
-- Run this in your Supabase SQL Editor
-- ============================================================================

-- Step 1: Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Create budget_chunks table
CREATE TABLE IF NOT EXISTS budget_chunks (
  id BIGSERIAL PRIMARY KEY,
  chunk_id TEXT UNIQUE NOT NULL,
  document_name TEXT NOT NULL,
  page_number INTEGER,
  chunk_index INTEGER,
  text TEXT NOT NULL,
  word_count INTEGER,
  quality_score FLOAT,
  
  -- Embedding (384 dimensions for sentence-transformers/all-MiniLM-L6-v2)
  embedding vector(384),
  embedding_model TEXT,
  
  -- Metadata (JSONB for flexible querying)
  metadata JSONB,
  
  -- Versioning
  pipeline_version TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 3: Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_document_name ON budget_chunks(document_name);
CREATE INDEX IF NOT EXISTS idx_quality_score ON budget_chunks(quality_score);
CREATE INDEX IF NOT EXISTS idx_metadata_gin ON budget_chunks USING GIN(metadata);

-- Step 4: Create vector similarity index (IVFFlat for fast approximate search)
-- This significantly speeds up vector similarity searches
CREATE INDEX IF NOT EXISTS idx_embedding_vector 
ON budget_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Step 5: Create similarity search function
-- This function performs vector similarity search with optional metadata filtering
CREATE OR REPLACE FUNCTION match_budget_chunks(
  query_embedding vector(384),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 5,
  filter_metadata jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
  chunk_id text,
  document_name text,
  page_number int,
  text text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    budget_chunks.chunk_id,
    budget_chunks.document_name,
    budget_chunks.page_number,
    budget_chunks.text,
    budget_chunks.metadata,
    1 - (budget_chunks.embedding <=> query_embedding) as similarity
  FROM budget_chunks
  WHERE 
    (filter_metadata = '{}'::jsonb OR budget_chunks.metadata @> filter_metadata)
    AND 1 - (budget_chunks.embedding <=> query_embedding) > match_threshold
  ORDER BY budget_chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Step 6: Create helper function for metadata queries
-- Example: Get all chunks for salaried individuals about taxation
CREATE OR REPLACE FUNCTION get_chunks_by_metadata(
  user_type_filter text DEFAULT NULL,
  topic_filter text DEFAULT NULL,
  income_range_filter text DEFAULT NULL
)
RETURNS TABLE (
  chunk_id text,
  document_name text,
  text text,
  metadata jsonb
)
LANGUAGE plpgsql
AS $$
DECLARE
  filter_json jsonb := '{}'::jsonb;
BEGIN
  -- Build filter dynamically
  IF user_type_filter IS NOT NULL THEN
    filter_json := jsonb_set(filter_json, '{user_types}', to_jsonb(ARRAY[user_type_filter]));
  END IF;
  
  RETURN QUERY
  SELECT
    budget_chunks.chunk_id,
    budget_chunks.document_name,
    budget_chunks.text,
    budget_chunks.metadata
  FROM budget_chunks
  WHERE 
    (user_type_filter IS NULL OR budget_chunks.metadata->'user_types' ? user_type_filter)
    AND (income_range_filter IS NULL OR budget_chunks.metadata->'income_ranges' ? income_range_filter);
END;
$$;

-- Step 7: Grant necessary permissions (for anon/authenticated roles)
-- Adjust based on your security requirements
GRANT SELECT ON budget_chunks TO anon, authenticated;
GRANT INSERT, UPDATE ON budget_chunks TO authenticated;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check if pgvector is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check table structure
\d budget_chunks;

-- Check indexes
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'budget_chunks';

-- Test similarity search (after data is loaded)
-- SELECT * FROM match_budget_chunks(
--   (SELECT embedding FROM budget_chunks LIMIT 1),
--   0.5,
--   5
-- );

-- ============================================================================
-- Cleanup (if needed)
-- ============================================================================

-- Drop table and start fresh (USE WITH CAUTION!)
-- DROP TABLE IF EXISTS budget_chunks CASCADE;
-- DROP FUNCTION IF EXISTS match_budget_chunks CASCADE;
-- DROP FUNCTION IF EXISTS get_chunks_by_metadata CASCADE;
