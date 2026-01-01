-- ============================================================================
-- CogniFy Database Schema
-- Enterprise RAG Platform
-- Version: 0.1.0
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',  -- admin, editor, user
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- ============================================================================
-- DOCUMENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uploaded_by UUID REFERENCES users(user_id) ON DELETE SET NULL,

    -- File info
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,  -- pdf, docx, xlsx, txt, png, jpg
    file_size_bytes BIGINT,
    file_path VARCHAR(1000),

    -- Content metadata
    title VARCHAR(500),
    description TEXT,
    page_count INTEGER,
    language VARCHAR(10) DEFAULT 'th',
    tags TEXT[] DEFAULT '{}',

    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    processing_error TEXT,
    total_chunks INTEGER DEFAULT 0,

    -- Soft delete
    is_deleted BOOLEAN DEFAULT false,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_deleted ON documents(is_deleted);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at DESC);

-- ============================================================================
-- DOCUMENT CHUNKS WITH EMBEDDINGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,

    -- Chunk content
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,

    -- Position info
    page_number INTEGER,
    section_title VARCHAR(500),

    -- Token info
    token_count INTEGER,

    -- Vector embedding (768 dimensions for nomic-embed-text)
    embedding VECTOR(768),
    embedding_model VARCHAR(100) DEFAULT 'nomic-embed-text',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat index for fast similarity search (~100 lists recommended)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_index ON document_chunks(chunk_index);
CREATE INDEX IF NOT EXISTS idx_chunks_page ON document_chunks(page_number);

-- ============================================================================
-- CONVERSATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    session_id VARCHAR(100),
    title VARCHAR(500),

    -- Settings used
    model_provider VARCHAR(50),
    model_name VARCHAR(100),
    temperature FLOAT DEFAULT 0.7,
    rag_enabled BOOLEAN DEFAULT true,
    rag_settings JSONB DEFAULT '{}',

    -- Metadata
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at DESC);

-- ============================================================================
-- MESSAGES
-- ============================================================================

CREATE TABLE IF NOT EXISTS messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    -- Message content
    message_type VARCHAR(20) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,

    -- RAG context
    sources_used JSONB DEFAULT '[]',

    -- Metrics
    response_time_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);

-- ============================================================================
-- DATABASE CONNECTORS
-- ============================================================================

CREATE TABLE IF NOT EXISTS database_connections (
    connection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,

    -- Connection info
    name VARCHAR(255) NOT NULL,
    db_type VARCHAR(50) NOT NULL,  -- postgresql, mysql, sqlserver
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    database_name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password_encrypted TEXT NOT NULL,

    -- Sync settings
    sync_enabled BOOLEAN DEFAULT false,
    last_sync_at TIMESTAMPTZ,
    last_sync_status VARCHAR(50),

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_connections_created_by ON database_connections(created_by);
CREATE INDEX IF NOT EXISTS idx_connections_type ON database_connections(db_type);
CREATE INDEX IF NOT EXISTS idx_connections_active ON database_connections(is_active);

-- ============================================================================
-- EMBEDDING CACHE
-- ============================================================================

CREATE TABLE IF NOT EXISTS embedding_cache (
    cache_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    text_hash VARCHAR(64) NOT NULL,  -- MD5 hash of text
    embedding VECTOR(768) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '1 hour',  -- TTL 3600s
    UNIQUE(text_hash, model_name)
);

CREATE INDEX IF NOT EXISTS idx_cache_hash ON embedding_cache(text_hash);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON embedding_cache(expires_at);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_connections_updated_at ON database_connections;
CREATE TRIGGER update_connections_updated_at
    BEFORE UPDATE ON database_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Create default admin user (password: admin123)
-- Password hash generated with bcrypt
INSERT INTO users (email, password_hash, full_name, role)
VALUES (
    'angelasoulcompanion@gmail.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.bBJZmNluYYvGIe',  -- admin123
    'admin',
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- CLEANUP EXPIRED CACHE (Run periodically)
-- ============================================================================

-- Delete expired embedding cache entries
-- CREATE OR REPLACE FUNCTION cleanup_expired_cache()
-- RETURNS INTEGER AS $$
-- DECLARE
--     deleted_count INTEGER;
-- BEGIN
--     DELETE FROM embedding_cache WHERE expires_at < NOW();
--     GET DIAGNOSTICS deleted_count = ROW_COUNT;
--     RETURN deleted_count;
-- END;
-- $$ language 'plpgsql';

-- ============================================================================
-- GRANT PERMISSIONS (if needed)
-- ============================================================================

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

COMMENT ON TABLE users IS 'User accounts for CogniFy platform';
COMMENT ON TABLE documents IS 'Uploaded documents for RAG processing';
COMMENT ON TABLE document_chunks IS 'Document chunks with vector embeddings';
COMMENT ON TABLE conversations IS 'Chat conversations with RAG';
COMMENT ON TABLE messages IS 'Messages within conversations';
COMMENT ON TABLE database_connections IS 'External database connections';
COMMENT ON TABLE embedding_cache IS 'Cache for text embeddings (TTL 1 hour)';
