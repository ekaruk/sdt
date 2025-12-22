CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS question_embeddings (
  question_id INTEGER PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
  embedding vector(3072) NOT NULL,
  source_text TEXT NOT NULL,
  updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL
);

-- Optional: add vector index if the table grows large.
-- CREATE INDEX IF NOT EXISTS idx_question_embeddings_embedding
--   ON question_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
