-- ============================================================================
-- CogniFy Database - Full Schema
-- Enterprise RAG Platform
-- Version: 1.0.0
-- Created: 4 January 2026 by Angela & David
--
-- Run this script to create a fresh CogniFy database:
--   createdb cognify
--   psql -d cognify -f full_schema.sql
-- ============================================================================

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

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

-- Function to cleanup expired refresh tokens
CREATE OR REPLACE FUNCTION cleanup_expired_refresh_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM refresh_tokens
    WHERE expires_at < NOW()
    RETURNING 1 INTO deleted_count;

    RETURN COALESCE(deleted_count, 0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_refresh_tokens IS 'Removes expired refresh tokens - call via scheduled job';

-- ============================================================================
-- TABLE: users
-- User accounts for CogniFy platform
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

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE users IS 'User accounts for CogniFy platform';

-- ============================================================================
-- TABLE: refresh_tokens
-- Secure refresh token storage with rotation support
-- ============================================================================

CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    family_id UUID NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    is_used BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    rotated_at TIMESTAMPTZ,
    user_agent TEXT,
    ip_address INET,
    device_info TEXT
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family_id ON refresh_tokens(family_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_active ON refresh_tokens(user_id, is_revoked, is_used)
    WHERE is_revoked = FALSE AND is_used = FALSE;

COMMENT ON TABLE refresh_tokens IS 'Secure refresh token storage with rotation support';
COMMENT ON COLUMN refresh_tokens.token_hash IS 'Bcrypt hash of the refresh token - never store plain tokens';
COMMENT ON COLUMN refresh_tokens.family_id IS 'Groups tokens in same rotation chain for reuse detection';
COMMENT ON COLUMN refresh_tokens.is_used IS 'True after token has been rotated - prevents reuse';
COMMENT ON COLUMN refresh_tokens.is_revoked IS 'True if token family was compromised or user logged out';

-- ============================================================================
-- TABLE: documents
-- Uploaded documents for RAG processing
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

COMMENT ON TABLE documents IS 'Uploaded documents for RAG processing';

-- ============================================================================
-- TABLE: document_chunks
-- Document chunks with vector embeddings
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

    -- Vector embedding (1024 dimensions for BGE-M3)
    embedding VECTOR(1024),
    embedding_model VARCHAR(100) DEFAULT 'bge-m3',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_index ON document_chunks(chunk_index);
CREATE INDEX IF NOT EXISTS idx_chunks_page ON document_chunks(page_number);

COMMENT ON TABLE document_chunks IS 'Document chunks with vector embeddings';

-- ============================================================================
-- TABLE: conversations
-- Chat conversations with RAG
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

DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE conversations IS 'Chat conversations with RAG';

-- ============================================================================
-- TABLE: messages
-- Messages within conversations
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

COMMENT ON TABLE messages IS 'Messages within conversations';

-- ============================================================================
-- TABLE: database_connections
-- External database connections for data sync
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
    sync_config JSONB DEFAULT '{}',
    last_sync_at TIMESTAMPTZ,
    last_sync_status VARCHAR(50),
    last_sync_error TEXT,
    total_chunks_synced INTEGER DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_connections_created_by ON database_connections(created_by);
CREATE INDEX IF NOT EXISTS idx_connections_type ON database_connections(db_type);
CREATE INDEX IF NOT EXISTS idx_connections_active ON database_connections(is_active);

DROP TRIGGER IF EXISTS update_connections_updated_at ON database_connections;
CREATE TRIGGER update_connections_updated_at
    BEFORE UPDATE ON database_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE database_connections IS 'External database connections for data sync';
COMMENT ON COLUMN database_connections.sync_config IS 'Sync configuration (tables, options)';
COMMENT ON COLUMN database_connections.total_chunks_synced IS 'Total document chunks created from sync';
COMMENT ON COLUMN database_connections.last_sync_error IS 'Error message from last sync attempt';

-- ============================================================================
-- TABLE: embedding_cache
-- Cache for text embeddings (TTL based)
-- ============================================================================

CREATE TABLE IF NOT EXISTS embedding_cache (
    cache_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    text_hash VARCHAR(64) NOT NULL,  -- MD5 hash of text
    embedding VECTOR(1024) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '1 hour',
    UNIQUE(text_hash, model_name)
);

CREATE INDEX IF NOT EXISTS idx_cache_hash ON embedding_cache(text_hash);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON embedding_cache(expires_at);

COMMENT ON TABLE embedding_cache IS 'Cache for text embeddings (TTL 1 hour)';

-- ============================================================================
-- TABLE: prompt_templates
-- Reusable LLM prompt templates for RAG system
-- ============================================================================

CREATE TABLE IF NOT EXISTS prompt_templates (
    template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,

    -- Template Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,  -- rag, system, summarization, analysis, custom
    expert_role VARCHAR(50),        -- general, financial, legal, technical, data, business, researcher

    -- Template Content
    template_content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',   -- [{name: "query", required: true, description: "..."}]

    -- Example & Preview
    example_input JSONB DEFAULT '{}',
    example_output TEXT,

    -- Settings
    language VARCHAR(10) DEFAULT 'th',
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    usage_count INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_role ON prompt_templates(expert_role);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_active ON prompt_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_default ON prompt_templates(is_default);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_created_by ON prompt_templates(created_by);

DROP TRIGGER IF EXISTS update_prompt_templates_updated_at ON prompt_templates;
CREATE TRIGGER update_prompt_templates_updated_at
    BEFORE UPDATE ON prompt_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE prompt_templates IS 'Reusable LLM prompt templates for RAG system';
COMMENT ON COLUMN prompt_templates.category IS 'Prompt category: rag, system, summarization, analysis, custom';
COMMENT ON COLUMN prompt_templates.expert_role IS 'Expert role: general, financial, legal, technical, data, business, researcher';
COMMENT ON COLUMN prompt_templates.variables IS 'JSON array of variables: [{name, required, description}]';

-- ============================================================================
-- TABLE: announcements
-- Organization news and announcements
-- ============================================================================

CREATE TABLE IF NOT EXISTS announcements (
    announcement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,                           -- Markdown content
    cover_image_url VARCHAR(1000),                   -- Optional cover image URL
    category VARCHAR(50) DEFAULT 'general',          -- general, important, update, event
    is_pinned BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_announcements_published
ON announcements(is_published, published_at DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_announcements_pinned
ON announcements(is_pinned, is_published, published_at DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_announcements_category
ON announcements(category) WHERE is_published = TRUE;

DROP TRIGGER IF EXISTS update_announcements_updated_at ON announcements;
CREATE TRIGGER update_announcements_updated_at
    BEFORE UPDATE ON announcements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE announcements IS 'Organization news and announcements';
COMMENT ON COLUMN announcements.content IS 'Markdown formatted content';
COMMENT ON COLUMN announcements.cover_image_url IS 'Optional URL for cover/thumbnail image';
COMMENT ON COLUMN announcements.category IS 'Category: general, important, update, event';
COMMENT ON COLUMN announcements.is_pinned IS 'Pinned announcements appear at top';
COMMENT ON COLUMN announcements.is_published IS 'Only published announcements are visible to users';
COMMENT ON COLUMN announcements.published_at IS 'Timestamp when announcement was published';

-- ============================================================================
-- SEED DATA: Default Admin User
-- ============================================================================

-- Create default admin user (password: admin123)
INSERT INTO users (email, password_hash, full_name, role)
VALUES (
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.bBJZmNluYYvGIe',  -- admin123
    'Administrator',
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- SEED DATA: Default Prompt Templates
-- ============================================================================

-- RAG Default (Thai)
INSERT INTO prompt_templates (
    name, description, category, expert_role, template_content, variables,
    example_input, example_output, language, is_default, is_active
) VALUES (
    'RAG Default (Thai)',
    'Default RAG prompt for Thai language responses',
    'rag',
    'general',
    E'คุณคือ CogniFy ผู้ช่วยอัจฉริยะที่ช่วยผู้ใช้เข้าใจเอกสารและข้อมูลของพวกเขา

ด้านล่างนี้คือบริบทจากเอกสาร ใช้ตอบคำถาม

--- บริบท ---
{context}
--- จบบริบท ---

คำแนะนำ:
1. ตอบเป็นภาษาไทย
2. ใช้รูปแบบ Markdown เพื่อความชัดเจน
3. อ้างอิงแหล่งที่มาด้วย [แหล่งที่ X]
4. ถ้าไม่พบข้อมูลในบริบท ให้บอกชัดเจน

แนวทางการจัดรูปแบบ:
- ใช้ ## สำหรับหัวข้อหลัก
- ใช้ ### สำหรับหัวข้อย่อย
- ใช้ **ตัวหนา** สำหรับคำสำคัญและค่าสำคัญ
- ใช้ bullet points (-) สำหรับรายการ',
    '[{"name": "context", "required": true, "description": "Context from documents"}, {"name": "query", "required": true, "description": "User question"}]',
    '{"query": "รายได้ปี 2567 เป็นเท่าไหร่", "context": "รายได้รวมปี 2567 อยู่ที่ 539 ล้านบาท..."}',
    E'## สรุปรายได้ปี 2567

- **รายได้รวม**: 539 ล้านบาท [แหล่งที่ 1]

รายได้ลดลงจากปีก่อนที่มีรายได้ 646 ล้านบาท',
    'th',
    true,
    true
) ON CONFLICT DO NOTHING;

-- RAG Default (English)
INSERT INTO prompt_templates (
    name, description, category, expert_role, template_content, variables,
    example_input, example_output, language, is_default, is_active
) VALUES (
    'RAG Default (English)',
    'Default RAG prompt for English language responses',
    'rag',
    'general',
    E'You are CogniFy, an intelligent assistant that helps users understand their documents and data.

Below is relevant context from the user''s documents. Answer the question using this context.

--- CONTEXT ---
{context}
--- END CONTEXT ---

INSTRUCTIONS:
1. Respond in English
2. Use Markdown formatting for clear, structured responses
3. Always cite sources using [Source X] notation
4. If information is not in the context, say so clearly

FORMATTING GUIDELINES:
- Use ## for main headings
- Use ### for subheadings
- Use **bold** for key terms and important values
- Use bullet points (-) for lists',
    '[{"name": "context", "required": true, "description": "Context from documents"}, {"name": "query", "required": true, "description": "User question"}]',
    '{"query": "What was the revenue in 2024?", "context": "Total revenue for 2024 was $5.2 million..."}',
    E'## Revenue Summary 2024

- **Total Revenue**: $5.2 million [Source 1]

Revenue increased by 12% compared to the previous year.',
    'en',
    false,
    true
) ON CONFLICT DO NOTHING;

-- Financial Analyst
INSERT INTO prompt_templates (
    name, description, category, expert_role, template_content, variables,
    example_input, example_output, language, is_default, is_active
) VALUES (
    'Financial Analyst',
    'Expert prompt for financial data analysis',
    'rag',
    'financial',
    E'คุณคือ CogniFy ในบทบาทนักวิเคราะห์การเงินผู้เชี่ยวชาญ

คุณเชี่ยวชาญในการวิเคราะห์ข้อมูลทางการเงิน อ่านงบการเงิน เข้าใจแนวโน้มตลาด และให้ข้อมูลเชิงลึกเกี่ยวกับรายได้ ต้นทุน กำไร และสถานะทางการเงิน

--- บริบท ---
{context}
--- จบบริบท ---

คำแนะนำ:
1. วิเคราะห์ตัวเลขอย่างละเอียด
2. เปรียบเทียบปีต่อปี หรือ quarter ต่อ quarter
3. คำนวณอัตราส่วนทางการเงินที่เกี่ยวข้อง
4. สรุป trend และ insight ที่สำคัญ
5. อ้างอิงแหล่งที่มาด้วย [แหล่งที่ X]

รูปแบบการนำเสนอ:
- ใช้ตารางเมื่อเปรียบเทียบตัวเลข
- แสดงเปอร์เซ็นต์การเปลี่ยนแปลง
- highlight ตัวเลขสำคัญด้วย **bold**',
    '[{"name": "context", "required": true, "description": "Financial data context"}, {"name": "query", "required": true, "description": "Financial question"}]',
    '{"query": "วิเคราะห์รายได้และกำไรปี 2567", "context": "รายได้ปี 2567: 539 ล้านบาท, กำไรสุทธิ: 45 ล้านบาท..."}',
    E'## การวิเคราะห์ทางการเงินปี 2567

### ภาพรวม
| รายการ | ปี 2566 | ปี 2567 | เปลี่ยนแปลง |
|--------|---------|---------|------------|
| รายได้รวม | 646 M | 539 M | -16.6% |
| กำไรสุทธิ | 52 M | 45 M | -13.5% |

### วิเคราะห์
- **อัตรากำไรสุทธิ**: 8.3% (ลดลงจาก 8.0%)
- แนวโน้มรายได้ลดลงต่อเนื่อง [แหล่งที่ 1]',
    'th',
    true,
    true
) ON CONFLICT DO NOTHING;

-- Document Summarization
INSERT INTO prompt_templates (
    name, description, category, expert_role, template_content, variables,
    example_input, example_output, language, is_default, is_active
) VALUES (
    'Document Summarization',
    'Summarize documents concisely',
    'summarization',
    'general',
    E'คุณคือ CogniFy สรุปเนื้อหาต่อไปนี้อย่างกระชับและครบถ้วน

--- เนื้อหา ---
{content}
--- จบเนื้อหา ---

คำแนะนำ:
1. สรุปใจความสำคัญ
2. ความยาว: {length} (short = 2-3 ประโยค, medium = 1 ย่อหน้า, long = หลายย่อหน้า)
3. ใช้ภาษาที่เข้าใจง่าย
4. คงข้อมูลสำคัญไว้ครบถ้วน

รูปแบบ:
- ใช้ bullet points สำหรับประเด็นสำคัญ
- highlight คำสำคัญด้วย **bold**',
    '[{"name": "content", "required": true, "description": "Content to summarize"}, {"name": "length", "required": false, "description": "Summary length: short, medium, long"}]',
    '{"content": "รายงานประจำปี 2567 ของบริษัท ABC...", "length": "medium"}',
    E'## สรุปรายงานประจำปี 2567

- **รายได้รวม**: 539 ล้านบาท (ลดลง 16.6%)
- **กำไรสุทธิ**: 45 ล้านบาท
- **แนวโน้ม**: ธุรกิจชะลอตัวตามเศรษฐกิจ
- **แผนปี 2568**: ขยายตลาดต่างประเทศ',
    'th',
    true,
    true
) ON CONFLICT DO NOTHING;

-- Data Analysis
INSERT INTO prompt_templates (
    name, description, category, expert_role, template_content, variables,
    example_input, example_output, language, is_default, is_active
) VALUES (
    'Data Analysis',
    'Analyze data and provide insights',
    'analysis',
    'data',
    E'คุณคือ CogniFy ในบทบาทนักวิเคราะห์ข้อมูลผู้เชี่ยวชาญ

วิเคราะห์ข้อมูลต่อไปนี้:
--- ข้อมูล ---
{data}
--- จบข้อมูล ---

จุดเน้น: {focus}

คำแนะนำ:
1. ระบุ patterns และ trends ที่สำคัญ
2. หา correlations ระหว่างตัวแปร
3. สรุป insights ที่นำไปใช้ได้
4. แนะนำ action items

รูปแบบ:
- ใช้ตารางแสดงข้อมูลเปรียบเทียบ
- ใช้ bullet points สำหรับ insights
- แยก section ชัดเจน',
    '[{"name": "data", "required": true, "description": "Data to analyze"}, {"name": "focus", "required": false, "description": "Analysis focus area"}]',
    '{"data": "ยอดขายรายเดือน: ม.ค. 45M, ก.พ. 52M...", "focus": "trend การเติบโต"}',
    E'## การวิเคราะห์ข้อมูลยอดขาย

### Pattern ที่พบ
- **Upward trend**: ยอดขายเพิ่มขึ้นเฉลี่ย 8% ต่อเดือน
- **Seasonality**: พีคในเดือน ธ.ค. ทุกปี

### Insights
- ไตรมาส 4 มียอดขายสูงสุด
- ควรเพิ่ม stock ในเดือน พ.ย.-ธ.ค.

### Action Items
1. เพิ่มงบการตลาดไตรมาส 4
2. วางแผน inventory ล่วงหน้า 2 เดือน',
    'th',
    true,
    true
) ON CONFLICT DO NOTHING;

-- System Default
INSERT INTO prompt_templates (
    name, description, category, expert_role, template_content, variables,
    example_input, example_output, language, is_default, is_active
) VALUES (
    'System Default',
    'Default system prompt when no RAG context',
    'system',
    'general',
    E'คุณคือ CogniFy ผู้ช่วยอัจฉริยะที่ช่วยผู้ใช้เข้าใจเอกสารและข้อมูล

คำถามของผู้ใช้ไม่ต้องการบริบทจากเอกสาร ตอบจากความรู้ทั่วไปของคุณ

คำแนะนำ:
1. ตอบอย่างกระชับและตรงประเด็น
2. ใช้รูปแบบ Markdown
3. ใช้ภาษาไทยหรืออังกฤษตามคำถาม
4. ถ้าไม่แน่ใจ ให้บอกตรงๆ

รูปแบบ:
- ใช้ ## สำหรับหัวข้อ
- ใช้ bullet points สำหรับรายการ
- ใช้ **bold** สำหรับคำสำคัญ',
    '[]',
    '{}',
    NULL,
    'th',
    true,
    true
) ON CONFLICT DO NOTHING;

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================

-- Summary of tables created:
-- 1. users              - User accounts
-- 2. refresh_tokens     - JWT refresh tokens with rotation
-- 3. documents          - Uploaded documents
-- 4. document_chunks    - Document chunks with embeddings
-- 5. conversations      - Chat conversations
-- 6. messages           - Chat messages
-- 7. database_connections - External DB connectors
-- 8. embedding_cache    - Embedding cache
-- 9. prompt_templates   - LLM prompt templates
-- 10. announcements     - Organization news

SELECT 'CogniFy database schema created successfully!' AS status;
