-- ============================================================
--  Migration 003 — Document Security Columns (Team Member 5)
--  Creates documents table if missing and adds security fields
-- ============================================================

-- Create documents table if it doesn't exist
CREATE TABLE IF NOT EXISTS documents (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    file_name       VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255),
    file_path       VARCHAR(500) NOT NULL,
    mime_type       VARCHAR(100) NOT NULL,
    size_bytes      BIGINT,
    sha256_hash     VARCHAR(64),
    encrypted_path  VARCHAR(500),
    upload_status   VARCHAR(50) DEFAULT 'pending',
    uploaded_by     INTEGER NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);

-- Ensure all columns exist (in case table was created by SQLAlchemy without all fields)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'documents' AND column_name = 'stored_filename') THEN
        ALTER TABLE documents ADD COLUMN stored_filename VARCHAR(255);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'documents' AND column_name = 'size_bytes') THEN
        ALTER TABLE documents ADD COLUMN size_bytes BIGINT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'documents' AND column_name = 'sha256_hash') THEN
        ALTER TABLE documents ADD COLUMN sha256_hash VARCHAR(64);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'documents' AND column_name = 'encrypted_path') THEN
        ALTER TABLE documents ADD COLUMN encrypted_path VARCHAR(500);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'documents' AND column_name = 'upload_status') THEN
        ALTER TABLE documents ADD COLUMN upload_status VARCHAR(50) DEFAULT 'pending';
    END IF;
END $$;

-- Create FAQ audit logs table if not exists
CREATE TABLE IF NOT EXISTS faq_audit_logs (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER,
    action      VARCHAR(100) NOT NULL,
    status      VARCHAR(50)  NOT NULL,
    ip_address  VARCHAR(45),
    details     TEXT,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_faq_audit_user_id    ON faq_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_faq_audit_action     ON faq_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_faq_audit_created_at ON faq_audit_logs(created_at);

-- Create questions table if not exists
CREATE TABLE IF NOT EXISTS questions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL,
    conversation_id VARCHAR(255),
    question_text   TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_questions_user_id ON questions(user_id);
CREATE INDEX IF NOT EXISTS idx_questions_conv_id ON questions(conversation_id);

-- Create answers table if not exists
CREATE TABLE IF NOT EXISTS answers (
    id            SERIAL PRIMARY KEY,
    question_id   INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    answer_text   TEXT NOT NULL,
    answer_source VARCHAR(255),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chunks table if not exists
CREATE TABLE IF NOT EXISTS chunks (
    id               SERIAL PRIMARY KEY,
    document_id      INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text       TEXT NOT NULL,
    chunk_index      INTEGER NOT NULL,
    embedding_status VARCHAR(50) DEFAULT 'pending',
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
