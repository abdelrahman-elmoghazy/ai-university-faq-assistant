-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to chunks table
-- 384 is the dimension for common small models like all-MiniLM-L6-v2
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding vector(384);
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding_status VARCHAR(50) DEFAULT 'pending';

-- Add index for vector similarity search (IVFFlat or HNSW)
-- IVFFlat is simpler for small-to-medium datasets
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
