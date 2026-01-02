# CogniFy Changelog - 2 January 2026

> Created with love by Angela & David

---

## Summary

วันนี้ทำ 2 เรื่องหลัก:
1. **Revert JSON → Normal Streaming** - กลับไปใช้ markdown streaming (เร็วกว่า)
2. **Prompt Management System** - Admin UI สำหรับจัดการ prompt templates

---

## Part 1: Revert to Normal Streaming

### Problem
JSON structured response ต้องรอ LLM generate ครบก่อนแล้วค่อย parse → ช้า

### Solution
กลับไปใช้ markdown streaming แบบ real-time

### Files Modified

| File | Changes |
|------|---------|
| `backend/app/services/chat_service.py` | ลบ JSON parsing, ใช้ markdown format |
| `frontend/src/pages/ChatPage.tsx` | ลบ StructuredResponseRenderer, ใช้ ReactMarkdown เสมอ |
| `frontend/src/hooks/useChat.ts` | ลบ structured_response event handling |

---

## Part 2: Prompt Management System

### Database Schema

```sql
-- Table: prompt_templates
CREATE TABLE prompt_templates (
    template_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,  -- rag, system, summarization, analysis, custom
    expert_role VARCHAR(50),        -- general, financial, legal, technical, data, business
    template_content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    example_input JSONB DEFAULT '{}',
    example_output TEXT,
    language VARCHAR(10) DEFAULT 'th',
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Backend Files Created

| File | Purpose |
|------|---------|
| `migrations/004_prompt_templates.sql` | Database schema + seed data |
| `domain/entities/prompt.py` | PromptTemplate entity + Template Guides |
| `services/prompt_service.py` | CRUD + AI generation + stats |
| `api/v1/prompts.py` | REST endpoints (admin protected) |

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/v1/prompts` | List prompts (filter by category, role) |
| GET | `/v1/prompts/{id}` | Get prompt by ID |
| POST | `/v1/prompts` | Create new prompt |
| PUT | `/v1/prompts/{id}` | Update prompt |
| DELETE | `/v1/prompts/{id}` | Delete prompt (soft) |
| POST | `/v1/prompts/{id}/set-default` | Set as default |
| POST | `/v1/prompts/ai-generate` | AI generate prompt |
| GET | `/v1/prompts/templates` | Template guides |
| GET | `/v1/prompts/stats` | Usage statistics |
| GET | `/v1/prompts/categories` | Categories & roles |

### Frontend Files Created

| File | Purpose |
|------|---------|
| `types/prompt.ts` | TypeScript types |
| `hooks/usePrompts.ts` | React Query hooks |
| `pages/PromptsPage.tsx` | Main admin page with tabs |
| `components/prompts/AIWizardModal.tsx` | 4-step AI wizard |

### UI Features

- **Category Tabs**: RAG, System, Summarization, Analysis, Custom
- **Prompt List**: Left panel with search/filter
- **Prompt Editor**: Right panel with form
- **Variables Editor**: Add/edit template variables
- **Template Guide**: Inline hints per category
- **AI Wizard**: 4-step prompt generation wizard
- **Stats Header**: Total prompts, usage stats

---

## Part 3: Bug Fixes

### 3.1 SessionStorage for Auth

**Change:** เปลี่ยนจาก localStorage → sessionStorage

**Files Modified:**
- `frontend/src/services/api.ts`
- `frontend/src/hooks/useAuth.ts`

**Result:** ปิด browser → ต้อง login ใหม่

### 3.2 Hydration Fix for Navigation

**Problem:** Navigate ระหว่าง pages แล้ว redirect ไป login เพราะ zustand persist มี hydration delay

**Solution:** เพิ่ม `_hasHydrated` flag และรอ hydration ก่อน check auth

**Files Modified:**
- `frontend/src/hooks/useAuth.ts` - เพิ่ม `_hasHydrated`, `setHasHydrated`, `onRehydrateStorage`
- `frontend/src/App.tsx` - ProtectedRoute รอ hydration

**Result:** Navigate ได้ปกติ, chat state ไม่หาย

---

## Seed Data

Default prompts ที่ seed เข้าไป:

| Name | Category | Expert Role | Language |
|------|----------|-------------|----------|
| RAG Default (Thai) | rag | general | th |
| RAG Default (English) | rag | general | en |
| Financial Analyst | rag | financial | th |
| System Default | system | general | th |
| Document Summarization | summarization | general | th |
| Data Analysis | analysis | data | th |

---

## How to Run

```bash
# 1. Run migration
psql -d cognify -f backend/migrations/004_prompt_templates.sql

# 2. Start backend
cd backend && uvicorn app.main:app --reload

# 3. Start frontend
cd frontend && npm run dev

# 4. Login as admin → Go to "Prompts" in sidebar
```

---

## Files Summary

### Backend
- `backend/migrations/004_prompt_templates.sql` (NEW)
- `backend/app/domain/entities/prompt.py` (NEW)
- `backend/app/services/prompt_service.py` (NEW)
- `backend/app/api/v1/prompts.py` (NEW)
- `backend/app/main.py` (MODIFIED - add prompts router)
- `backend/app/services/chat_service.py` (MODIFIED - remove JSON parsing)

### Frontend
- `frontend/src/types/prompt.ts` (NEW)
- `frontend/src/hooks/usePrompts.ts` (NEW)
- `frontend/src/pages/PromptsPage.tsx` (NEW)
- `frontend/src/components/prompts/AIWizardModal.tsx` (NEW)
- `frontend/src/pages/ChatPage.tsx` (MODIFIED)
- `frontend/src/hooks/useChat.ts` (MODIFIED)
- `frontend/src/hooks/useAuth.ts` (MODIFIED - sessionStorage + hydration)
- `frontend/src/services/api.ts` (MODIFIED - sessionStorage + promptsApi)
- `frontend/src/App.tsx` (MODIFIED - add route + hydration check)
- `frontend/src/components/layout/Layout.tsx` (MODIFIED - add Prompts nav)

---

*Documented by Angela - 2 January 2026* 💜
