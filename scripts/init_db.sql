-- Agentic AI Platform Database Initialization Script
-- PostgreSQL 15

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create schema
CREATE SCHEMA IF NOT EXISTS agentic_ai;

-- Set search path
SET search_path TO agentic_ai, public;

-- ==========================================
-- Tasks Table
-- ==========================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    task_data JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100),
    INDEX idx_agent_name (agent_name),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

COMMENT ON TABLE tasks IS 'Agent task execution records';

-- ==========================================
-- Agent Executions Table
-- ==========================================
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    execution_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_end TIMESTAMP WITH TIME ZONE,
    duration_seconds NUMERIC(10, 2),
    status VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    error_details TEXT,
    llm_calls INTEGER DEFAULT 0,
    llm_total_tokens INTEGER DEFAULT 0,
    INDEX idx_task_id (task_id),
    INDEX idx_agent_name (agent_name),
    INDEX idx_execution_start (execution_start)
);

COMMENT ON TABLE agent_executions IS 'Detailed agent execution logs';

-- ==========================================
-- Users Table
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(200),
    hashed_password VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

COMMENT ON TABLE users IS 'User accounts for the platform';

-- ==========================================
-- API Keys Table
-- ==========================================
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_api_key (api_key),
    INDEX idx_user_id (user_id)
);

COMMENT ON TABLE api_keys IS 'API keys for authentication';

-- ==========================================
-- Knowledge Base Metadata Table
-- ==========================================
CREATE TABLE IF NOT EXISTS knowledge_base_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_name VARCHAR(100) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    filename VARCHAR(500),
    file_type VARCHAR(50),
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    UNIQUE (collection_name, document_id),
    INDEX idx_collection_name (collection_name),
    INDEX idx_indexed_at (indexed_at)
);

COMMENT ON TABLE knowledge_base_metadata IS 'Metadata for documents in vector database';

-- ==========================================
-- Audit Log Table
-- ==========================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
);

COMMENT ON TABLE audit_logs IS 'Audit trail for all system actions';

-- ==========================================
-- System Configuration Table
-- ==========================================
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

COMMENT ON TABLE system_config IS 'System-wide configuration settings';

-- ==========================================
-- Create Indexes
-- ==========================================

-- Full-text search index for tasks
CREATE INDEX IF NOT EXISTS idx_tasks_search ON tasks USING GIN (to_tsvector('english', task_data::text));

-- Partial index for active tasks
CREATE INDEX IF NOT EXISTS idx_active_tasks ON tasks (agent_name, status) WHERE status IN ('pending', 'running');

-- ==========================================
-- Create Views
-- ==========================================

-- Active tasks view
CREATE OR REPLACE VIEW v_active_tasks AS
SELECT
    t.id,
    t.agent_name,
    t.task_type,
    t.status,
    t.priority,
    t.created_at,
    t.started_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - t.started_at)) as running_duration_seconds
FROM tasks t
WHERE t.status IN ('pending', 'running')
ORDER BY t.priority DESC, t.created_at ASC;

-- Agent performance view
CREATE OR REPLACE VIEW v_agent_performance AS
SELECT
    agent_name,
    COUNT(*) as total_executions,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
    ROUND(AVG(duration_seconds), 2) as avg_duration_seconds,
    SUM(llm_total_tokens) as total_llm_tokens
FROM agent_executions
WHERE execution_start >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY agent_name;

-- ==========================================
-- Insert Default Configuration
-- ==========================================

INSERT INTO system_config (key, value, description) VALUES
    ('version', '1.0.0', 'System version'),
    ('maintenance_mode', 'false', 'Maintenance mode flag'),
    ('max_concurrent_tasks', '10', 'Maximum concurrent tasks'),
    ('task_timeout_seconds', '1800', 'Default task timeout in seconds')
ON CONFLICT (key) DO NOTHING;

-- ==========================================
-- Create Functions
-- ==========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- Grant Permissions
-- ==========================================

-- Grant all privileges on all tables to the database user
-- Note: In production, use more restrictive permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agentic_ai TO CURRENT_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agentic_ai TO CURRENT_USER;

-- ==========================================
-- Insert Sample Data (Development Only)
-- ==========================================

-- Insert a test user
INSERT INTO users (username, email, full_name, is_active, is_superuser)
VALUES ('admin', 'admin@agentic-ai.com', 'System Administrator', true, true)
ON CONFLICT (username) DO NOTHING;

-- Commit
COMMIT;
