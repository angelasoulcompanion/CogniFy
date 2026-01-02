-- ============================================================================
-- Migration: 004_prompt_templates.sql
-- Description: Prompt templates for RAG system with categories and AI wizard
-- Created: 2026-01-02 by Angela & David
-- ============================================================================

-- Prompt Templates Table
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
    example_input JSONB DEFAULT '{}',    -- {"query": "รายได้ปี 2024", "context": "..."}
    example_output TEXT,                  -- ตัวอย่างผลลัพธ์ที่ควรได้

    -- Settings
    language VARCHAR(10) DEFAULT 'th',    -- th, en, multi
    is_default BOOLEAN DEFAULT false,     -- prompt หลักของ category นั้น
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    usage_count INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_role ON prompt_templates(expert_role);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_active ON prompt_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_default ON prompt_templates(is_default);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_created_by ON prompt_templates(created_by);

-- Update trigger
DROP TRIGGER IF EXISTS update_prompt_templates_updated_at ON prompt_templates;
CREATE TRIGGER update_prompt_templates_updated_at
    BEFORE UPDATE ON prompt_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DATA: Default Prompts
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

-- Summarization
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

-- Analysis
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

-- System prompt
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

-- Comment
COMMENT ON TABLE prompt_templates IS 'Reusable LLM prompt templates for RAG system';
COMMENT ON COLUMN prompt_templates.category IS 'Prompt category: rag, system, summarization, analysis, custom';
COMMENT ON COLUMN prompt_templates.expert_role IS 'Expert role: general, financial, legal, technical, data, business, researcher';
COMMENT ON COLUMN prompt_templates.variables IS 'JSON array of variables: [{name, required, description}]';
