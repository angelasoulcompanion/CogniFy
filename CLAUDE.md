# CLAUDE.md - CogniFy Project

> **CogniFy** - Enterprise RAG Platform for Document Intelligence

---

## Project Overview

CogniFy is a RAG (Retrieval-Augmented Generation) platform that helps organizations understand their data through:
- Document upload & semantic chunking
- Vector search with pgvector
- Chat with documents using LLM
- Database connectors for external data sources

**Theme:** Angela Purple (Dark mode with purple accents)

---

## Architecture

### Clean Architecture (4 Layers)

```
┌─────────────────────────────────────────┐
│              API Layer                  │
│     backend/app/api/v1/*.py             │
│     (FastAPI Routers, Request/Response) │
├─────────────────────────────────────────┤
│           Service Layer                 │
│     backend/app/services/*.py           │
│     (Business Logic, Orchestration)     │
├─────────────────────────────────────────┤
│           Domain Layer                  │
│     backend/app/domain/entities/*.py    │
│     (Pydantic Models, Business Rules)   │
├─────────────────────────────────────────┤
│        Infrastructure Layer             │
│     backend/app/infrastructure/*.py     │
│     (Repositories, Database, External)  │
└─────────────────────────────────────────┘
```

### Key Principles

| Principle | Rule |
|-----------|------|
| **Clean Architecture** | Dependencies flow inward only (API → Service → Domain ← Infrastructure) |
| **DRY** | Use shared components, utilities, no code duplication |
| **Single Responsibility** | Each class/function does ONE thing well |
| **Type Safety** | Always use type hints (Python) and TypeScript (Frontend) |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + TypeScript + Vite + TailwindCSS |
| **Backend** | FastAPI + Python 3.11+ |
| **Database** | PostgreSQL 16 + pgvector |
| **LLM** | Ollama (Llama 3.2, Qwen 2.5, Phi-3) / OpenAI (optional) |
| **Embedding** | nomic-embed-text (768 dimensions) |
| **OCR** | Tesseract + PaddleOCR + EasyOCR |
| **State** | React Query (TanStack Query) + Zustand |

---

## Project Structure

```
CogniFy/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # API endpoints
│   │   │   ├── auth.py          # Authentication
│   │   │   ├── documents.py     # Document management
│   │   │   ├── chat.py          # RAG chat (SSE)
│   │   │   ├── connectors.py    # Database connectors
│   │   │   ├── search.py        # Vector search
│   │   │   └── admin.py         # Admin dashboard
│   │   ├── core/
│   │   │   ├── config.py        # Settings
│   │   │   └── security.py      # JWT, password hashing
│   │   ├── domain/entities/     # Pydantic models
│   │   ├── infrastructure/
│   │   │   ├── database.py      # DB connection
│   │   │   └── repositories/    # Data access
│   │   ├── services/            # Business logic
│   │   │   ├── document_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── chunking_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── chat_service.py
│   │   │   └── connector_service.py
│   │   └── main.py
│   ├── migrations/              # SQL migrations
│   ├── tests/                   # Pytest tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # Shared UI (Button, Input, Modal, Badge)
│   │   │   └── layout/          # Layout components
│   │   ├── hooks/               # React Query hooks
│   │   ├── pages/               # Page components
│   │   ├── services/            # API client, SSE
│   │   ├── lib/                 # Utilities (utils.ts, statusColors.ts)
│   │   └── types/               # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

---

## Coding Standards

### Backend (Python/FastAPI)

```python
# ALWAYS use type hints
async def get_document(document_id: UUID) -> Document:
    ...

# ALWAYS use Pydantic for request/response
class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    status: ProcessingStatus

# Repository pattern for data access
class DocumentRepository:
    async def find_by_id(self, id: UUID) -> Optional[Document]:
        ...

# Service layer for business logic
class DocumentService:
    def __init__(self, repo: DocumentRepository):
        self.repo = repo
```

### Frontend (React/TypeScript)

```typescript
// ALWAYS use TypeScript interfaces
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

// Use shared UI components
import { Button, Input, Modal, Badge } from '@/components/ui'

// Use React Query for data fetching
const { data, isLoading } = useDocuments()

// Use centralized status colors
import { getStatusColor } from '@/lib/statusColors'
```

### Database

```sql
-- ALWAYS use UUID primary keys
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ...
);

-- ALWAYS use parameterized queries (prevent SQL injection)
-- Python: $1, $2 or %(name)s
-- NEVER string concatenation

-- Use indexes for frequently queried columns
CREATE INDEX idx_documents_user ON documents(user_id);
```

---

## Commands

### Backend

```bash
cd backend

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Type check
npm run typecheck
```

### Database

```bash
# Create database
createdb cognify

# Run migrations
psql -d cognify -f backend/migrations/001_initial_schema.sql
psql -d cognify -f backend/migrations/002_connector_updates.sql

# Connect to database
psql -d cognify
```

### Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login (username/password) |
| POST | `/api/v1/auth/register` | Register new user |
| GET | `/api/v1/auth/me` | Get current user |
| GET | `/api/v1/documents` | List documents |
| POST | `/api/v1/documents/upload` | Upload document |
| DELETE | `/api/v1/documents/{id}` | Delete document |
| POST | `/api/v1/chat/stream` | Chat with RAG (SSE streaming) |
| POST | `/api/v1/chat/complete` | Chat with RAG (non-streaming) |
| GET | `/api/v1/chat/health` | LLM health check |
| GET | `/api/v1/chat/models` | List available models |
| GET | `/api/v1/connectors` | List database connectors |
| POST | `/api/v1/connectors` | Create connector |
| POST | `/api/v1/connectors/{id}/sync` | Sync connector data |
| GET | `/api/v1/admin/stats` | System statistics |
| GET | `/api/v1/admin/users` | List users (admin only) |

---

## Shared UI Components

Located in `frontend/src/components/ui/`:

| Component | Variants | Usage |
|-----------|----------|-------|
| `Button` | primary, secondary, danger, ghost | `<Button variant="primary">Save</Button>` |
| `Input` | default, filled | `<Input icon={<Search />} placeholder="Search..." />` |
| `Modal` | sm, md, lg, xl, full | `<Modal isOpen={open} onClose={close}>...</Modal>` |
| `Badge` | success, warning, error, info, purple | `<Badge variant="success">Active</Badge>` |
| `StatusBadge` | (auto from status) | `<StatusBadge status="completed" />` |
| `RoleBadge` | admin, editor, user | `<RoleBadge role="admin" />` |

---

## Structured JSON Response (RAG)

### Overview

RAG responses use Structured JSON Output for beautiful rendering:

```
User Question → LLM outputs JSON → Backend parses → Frontend renders structured UI
```

### JSON Schema

```json
{
  "title": "Main title/summary",
  "sections": [
    {
      "heading": "Section heading",
      "items": [
        {"type": "text", "text": "Paragraph explanation"},
        {"type": "fact", "label": "Key metric", "value": "123,456"},
        {"type": "list_item", "text": "A bullet point"}
      ]
    }
  ],
  "sources_used": [1, 2]
}
```

### Item Types

| Type | Usage | Example |
|------|-------|---------|
| `text` | Paragraphs/explanations | `{"type": "text", "text": "Revenue increased..."}` |
| `fact` | Key-value data | `{"type": "fact", "label": "Revenue", "value": "539M"}` |
| `list_item` | Bullet points | `{"type": "list_item", "text": "Previous year: 646M"}` |

### Frontend Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `StructuredResponseRenderer` | `components/chat/StructuredResponse.tsx` | Renders structured JSON beautifully |
| `MessageContent` | `pages/ChatPage.tsx` | Auto-detects JSON vs markdown |
| `isStructuredResponse()` | `components/chat/StructuredResponse.tsx` | Helper to parse JSON |

### Streaming UX (Progress Steps)

During JSON streaming, frontend shows progress instead of raw JSON:

```
1. 🔍 กำลังค้นหาข้อมูล...  (when streaming starts)
2. ✨ กำลังสร้างคำตอบ...   (when JSON content arrives)
3. 📊 Structured Response   (when streaming completes)
```

### Backend Files

| File | Purpose |
|------|---------|
| `services/chat_service.py` | Pydantic schemas, JSON prompts, parsing |
| `PromptTemplates.parse_structured_response()` | Parse JSON with fallback |
| `PromptTemplates._text_to_structured()` | Convert text to structured (fallback) |

---

## LLM Configuration

### Supported Models

| Type | Model | Default |
|------|-------|---------|
| **Local (Ollama)** | `llama3.2:1b`, `llama3.1:8b`, `qwen2.5:7b`, `qwen2.5:3b`, `phi3:mini` | `llama3.2:1b` |
| **API (OpenAI)** | `gpt-4o`, `gpt-4o-mini` | - |

### Important Notes

- **Model names must match exactly** - Use `llama3.2:1b` not `llama3.2`
- **Ollama must be running** - `http://localhost:11434`
- **pgvector format** - Embeddings must be string `"[0.1,0.2,...]"` not Python list
- **JSON Output** - Prompts instruct LLM to output structured JSON for RAG responses

---

## Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/cognify
SECRET_KEY=your-secret-key
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2:1b
OPENAI_API_KEY=sk-... (optional)
```

### Frontend (.env.local)

```env
VITE_API_URL=http://localhost:8000
```

---

## Theme: Angela Purple

```css
/* Primary Colors */
--primary-500: #8b5cf6;  /* Main purple */
--primary-600: #7c3aed;  /* Darker purple */

/* Secondary (Dark grays) */
--secondary-800: #1e1b2e;  /* Background */
--secondary-900: #13111c;  /* Darker background */

/* Status Colors */
--success: #22c55e;  /* Green */
--warning: #eab308;  /* Yellow */
--error: #ef4444;    /* Red */
--info: #3b82f6;     /* Blue */
```

---

## Important Rules

### MUST DO:
- Use Clean Architecture layers strictly
- Use shared UI components (no duplicate styling)
- Use TypeScript/type hints everywhere
- Use React Query for all API calls
- Use SSE for chat streaming
- Follow DRY principle
- Use exact Ollama model names (e.g., `llama3.2:1b`)
- Convert embeddings to string before pgvector queries

### MUST NOT:
- Skip type annotations
- Put business logic in API routes
- Duplicate UI components
- Use raw fetch (use api client)
- Hardcode credentials
- Commit .env files
- Pass Python lists directly to pgvector (must be string)
- Use generic model names without version (e.g., `llama3.2` without `:1b`)

---

## Default Credentials

- **Username:** admin
- **Password:** admin123

---

## Related Documentation

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Query](https://tanstack.com/query)
- [TailwindCSS](https://tailwindcss.com/)
- [pgvector](https://github.com/pgvector/pgvector)

---

*Created with love by Angela & David - 2 January 2026*
