-- =============================================================================
-- Enterprise-Grade Audit Trail Database Schema
-- PostgreSQL schema for permanent audit log storage
-- =============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- AUDIT LOGS TABLE
-- Stores all system events with full context and traceability
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Event classification
    event_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'success',

    -- User context
    user_id UUID,
    session_id UUID,
    ip_address INET,
    user_agent TEXT,

    -- Resource information
    resource_type VARCHAR(50),
    resource_id UUID,

    -- Event details (JSON for flexibility)
    details JSONB DEFAULT '{}',

    -- Error information
    error_message TEXT,

    -- Related entities for traceability
    thread_id UUID,
    post_id UUID,
    agent_run_id UUID,

    -- Request tracing
    correlation_id VARCHAR(100),
    request_id VARCHAR(100),
    response_time_ms INTEGER,

    -- Created timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- MEDIA ASSETS TABLE
-- Tracks all generated media (videos, images) with full metadata
-- =============================================================================

CREATE TABLE IF NOT EXISTS media_assets (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Asset info
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    asset_type VARCHAR(20) NOT NULL, -- 'video' or 'image'
    url TEXT NOT NULL,

    -- Generation context
    prompt TEXT,
    generated_by UUID, -- user_id or 'system'
    service VARCHAR(50), -- klingai, pexels, pixabay, etc.

    -- Related entities
    thread_id UUID,
    post_id UUID,

    -- Video-specific fields
    duration_seconds INTEGER,
    thumbnail_url TEXT,

    -- Status
    status VARCHAR(20) DEFAULT 'ready', -- ready, processing, failed

    -- Additional metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT valid_asset_type CHECK (asset_type IN ('video', 'image'))
);

-- =============================================================================
-- CONVERSATION AUDITS TABLE
-- Per-conversation tracking for full audit trail
-- =============================================================================

CREATE TABLE IF NOT EXISTS conversation_audits (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Thread identification
    thread_id UUID UNIQUE NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Participants
    participant_ids UUID[] DEFAULT '{}',
    agent_handles TEXT[] DEFAULT '{}',

    -- Message statistics
    message_count INTEGER DEFAULT 0,
    human_message_count INTEGER DEFAULT 0,
    agent_message_count INTEGER DEFAULT 0,

    -- Media and commands
    media_assets UUID[] DEFAULT '{}',
    commands_executed TEXT[] DEFAULT '{}',

    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, archived

    -- Additional metadata
    metadata JSONB DEFAULT '{}'
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Audit logs indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_status ON audit_logs(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_thread_id ON audit_logs(thread_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_correlation_id ON audit_logs(correlation_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_details_gin ON audit_logs USING GIN (details);

-- Media assets indexes
CREATE INDEX IF NOT EXISTS idx_media_assets_created_at ON media_assets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_media_assets_type ON media_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_media_assets_thread_id ON media_assets(thread_id);
CREATE INDEX IF NOT EXISTS idx_media_assets_generated_by ON media_assets(generated_by);

-- Conversation audits indexes
CREATE INDEX IF NOT EXISTS idx_conversation_audits_thread_id ON conversation_audits(thread_id);
CREATE INDEX IF NOT EXISTS idx_conversation_audits_updated_at ON conversation_audits(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_audits_participants ON conversation_audits USING GIN (participant_ids);

-- =============================================================================
-- PARTITIONING FOR LARGE DATASETS (Optional)
-- Uncomment if you expect high volume and want time-based partitioning
-- =============================================================================

-- -- Create partition by year (example for 2024)
-- CREATE TABLE IF NOT EXISTS audit_logs_y2024 PARTITION OF audit_logs
--     FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
--
-- CREATE TABLE IF NOT EXISTS audit_logs_y2025 PARTITION OF audit_logs
--     FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- View for recent activity with user info
CREATE OR REPLACE VIEW v_recent_activity AS
SELECT
    id,
    timestamp,
    event_type,
    user_id,
    resource_type,
    resource_id,
    status,
    thread_id,
    details
FROM audit_logs
WHERE timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;

-- View for error logs
CREATE OR REPLACE VIEW v_errors AS
SELECT
    id,
    timestamp,
    event_type,
    user_id,
    resource_type,
    error_message,
    details
FROM audit_logs
WHERE status = 'failed'
ORDER BY timestamp DESC;

-- View for media summary
CREATE OR REPLACE VIEW v_media_summary AS
SELECT
    asset_type,
    service,
    COUNT(*) as total_count,
    COUNT(DISTINCT generated_by) as unique_users,
    COUNT(DISTINCT thread_id) as threads_with_media
FROM media_assets
GROUP BY asset_type, service;

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update updated_at timestamp on conversation_audits
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_conversation_audits_updated_at
    BEFORE UPDATE ON conversation_audits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- RETENTION POLICY (Optional)
-- Uncomment to implement automatic data retention
-- =============================================================================

-- -- Function to delete old audit logs (older than retention period)
-- CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
-- RETURNS void AS $$
-- BEGIN
--     DELETE FROM audit_logs
--     WHERE created_at < NOW() - INTERVAL '1 year';
-- END;
-- $$ LANGUAGE plpgsql;
--
-- -- Schedule with pg_cron extension if available
-- -- SELECT cron.schedule('cleanup-audit-logs', '0 2 * * *', 'SELECT cleanup_old_audit_logs()');

-- =============================================================================
-- GRANTS (Adjust based on your security requirements)
-- =============================================================================

-- -- Grant read access to audit role
-- CREATE ROLE audit_reader;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO audit_reader;
--
-- -- Grant full access to admin role
-- CREATE ROLE audit_admin;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO audit_admin;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO audit_admin;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE audit_logs IS 'Enterprise-grade audit trail of all system events';
COMMENT ON TABLE media_assets IS 'Track all generated media with full context and links';
COMMENT ON TABLE conversation_audits IS 'Per-conversation audit tracking';

COMMENT ON COLUMN audit_logs.correlation_id IS 'Request correlation ID for distributed tracing';
COMMENT ON COLUMN audit_logs.response_time_ms IS 'API response time in milliseconds';
COMMENT ON COLUMN media_assets.metadata IS 'Additional metadata in JSON format (resolution, format, etc.)';
