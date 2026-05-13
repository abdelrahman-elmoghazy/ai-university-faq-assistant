-- ============================================================
--  Migration 002 — Service Logs Table (Logging Service)
-- ============================================================

CREATE TABLE IF NOT EXISTS service_logs (
    id          SERIAL PRIMARY KEY,
    source      VARCHAR(50)  NOT NULL DEFAULT 'unknown',
    action      VARCHAR(100) NOT NULL,
    user_id     INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    user_email  VARCHAR(120),
    ip_address  VARCHAR(45),
    status      VARCHAR(20),
    details     JSONB,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_service_logs_action     ON service_logs(action);
CREATE INDEX IF NOT EXISTS idx_service_logs_user_id    ON service_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_service_logs_status     ON service_logs(status);
CREATE INDEX IF NOT EXISTS idx_service_logs_created_at ON service_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_service_logs_source     ON service_logs(source);
