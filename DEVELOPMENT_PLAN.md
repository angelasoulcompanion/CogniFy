# CogniFy Development Plan

> **"Making organizations understand their own data"**
>
> Enterprise RAG Platform - รวบรวมประสบการณ์จาก AngelaAI + DavidAiReactChat

---

## Executive Summary

| Item | Detail |
|------|--------|
| **ชื่อ** | CogniFy |
| **ความหมาย** | Cognition + -fy = ทำให้องค์กรเข้าใจข้อมูลของตัวเอง |
| **Tech Stack** | FastAPI + React 18 + PostgreSQL/pgvector |
| **LLM** | Ollama (local) + OpenAI (configurable) |
| **Multi-tenant** | Single tenant first, เพิ่มทีหลัง |

---

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Frontend** | React + TypeScript + Vite | 18.2 / 5.3 / 7.1 |
| **Backend** | FastAPI (Python) | 0.109+ |
| **Database** | PostgreSQL + pgvector | 16+ |
| **LLM Local** | Ollama | Latest |
| **LLM Cloud** | OpenAI API | GPT-4o-mini |
| **Embedding** | nomic-embed-text | 768-dim |
| **State** | React Query (TanStack) | 5.17+ |
| **Styling** | Tailwind CSS + shadcn/ui | 3.4 |

---

## Project Structure

```
/Users/davidsamanyaporn/PycharmProjects/CogniFy/
│
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth.py             # ✅ Login, Register, JWT
│   │   │   ├── documents.py        # ✅ Upload, List, Process
│   │   │   ├── chat.py             # ✅ SSE Streaming + Conversations
│   │   │   ├── search.py           # ✅ Vector/BM25/Hybrid search
│   │   │   ├── connectors.py       # ✅ Database connectors
│   │   │   └── admin.py            # ✅ Admin dashboard API
│   │   │
│   │   ├── services/
│   │   │   ├── embedding_service.py    # ✅ Singleton, Cached, Fallback
│   │   │   ├── chunking_service.py     # ✅ Semantic Chunking
│   │   │   ├── document_service.py     # ✅ Process Pipeline + OCR
│   │   │   ├── ocr_service.py          # ✅ Tesseract/PaddleOCR/EasyOCR
│   │   │   ├── rag_service.py          # ✅ Vector, BM25, Hybrid + RRF
│   │   │   ├── llm_service.py          # ✅ Ollama + OpenAI streaming
│   │   │   ├── chat_service.py         # ✅ RAG + LLM orchestration
│   │   │   ├── connector_service.py    # ✅ DB connectors + sync
│   │   │   └── admin_service.py        # ✅ System stats + user management
│   │   │
│   │   ├── domain/entities/
│   │   │   ├── user.py             # ✅ User, UserRole
│   │   │   ├── document.py         # ✅ Document, Chunk
│   │   │   └── connector.py        # ✅ DatabaseConnection
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── database.py         # ✅ asyncpg pool
│   │   │   └── repositories/
│   │   │       ├── base_repository.py      # ✅ Generic CRUD
│   │   │       ├── user_repository.py         # ✅ User ops
│   │   │       ├── document_repository.py     # ✅ Doc + Chunk ops
│   │   │       ├── embedding_repository.py    # ✅ Vector search + cache
│   │   │       ├── conversation_repository.py # ✅ Conversations + Messages
│   │   │       └── connector_repository.py    # ✅ DB connections
│   │   │
│   │   ├── core/
│   │   │   ├── config.py           # ✅ Settings
│   │   │   └── security.py         # ✅ JWT, Password
│   │   │
│   │   └── main.py                 # ✅ FastAPI app
│   │
│   ├── migrations/
│   │   └── 001_initial_schema.sql  # ✅ Complete schema
│   │
│   ├── requirements.txt            # ✅ Dependencies
│   └── .env.example                # ✅ Environment template
│
├── frontend/                       # ✅ Phase 5
│   ├── src/
│   │   ├── components/
│   │   │   └── layout/
│   │   │       └── Layout.tsx         # ✅ Sidebar + navigation
│   │   │
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx          # ✅ JWT login
│   │   │   ├── ChatPage.tsx           # ✅ SSE streaming chat
│   │   │   ├── DocumentsPage.tsx      # ✅ Document management
│   │   │   ├── ConnectorsPage.tsx     # ✅ Database connectors
│   │   │   └── AdminPage.tsx          # ✅ Admin dashboard
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.ts             # ✅ Zustand + persist
│   │   │   ├── useChat.ts             # ✅ SSE streaming
│   │   │   ├── useDocuments.ts        # ✅ React Query
│   │   │   ├── useConnectors.ts       # ✅ Connector management
│   │   │   └── useAdmin.ts            # ✅ Admin analytics
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts                 # ✅ Axios client
│   │   │   └── sse.ts                 # ✅ SSE streaming
│   │   │
│   │   ├── lib/
│   │   │   └── utils.ts               # ✅ Utilities
│   │   │
│   │   ├── types/
│   │   │   └── index.ts               # ✅ TypeScript types
│   │   │
│   │   └── App.tsx                    # ✅ Router + Auth
│   │
│   ├── package.json                   # ✅ Dependencies
│   ├── vite.config.ts                 # ✅ Vite + proxy
│   ├── tailwind.config.js             # ✅ Tailwind
│   └── tsconfig.json                  # ✅ TypeScript
│
└── README.md

Legend: ✅ = Completed | 🔲 = Pending
```

---

## Implementation Phases

### Phase 1: Foundation ✅ COMPLETED

- [x] Project structure (Clean Architecture)
- [x] FastAPI app setup
- [x] Configuration management
- [x] JWT Authentication
- [x] Database connection pool
- [x] Domain entities (User, Document)
- [x] Repository pattern
- [x] Auth API endpoints
- [x] Documents API endpoints
- [x] Database migration script

### Phase 2: Document Processing ✅ COMPLETED

- [x] **EmbeddingService** - Singleton, in-memory cache (TTL 1hr), DB cache, fallback models
- [x] **ChunkingService** - Semantic chunking, Thai support, page tracking
- [x] **DocumentService** - PDF/DOCX/TXT/Excel extraction, process pipeline
- [x] **Background Processing** - FastAPI BackgroundTasks integration
- [x] **API Endpoints** - `/process`, `/stats`, `/reprocess`

**Key Files Created:**
```
backend/app/services/
├── embedding_service.py    # 400+ lines - full featured
├── chunking_service.py     # 200+ lines - semantic chunking
└── document_service.py     # 350+ lines - complete pipeline
```

### Phase 3: Search & RAG ✅ COMPLETED

- [x] **RAGService** - Vector, BM25, and Hybrid search with RRF fusion
- [x] **EmbeddingRepository** - Vector search queries, cache operations
- [x] **Vector Search** - pgvector cosine/euclidean/dot similarity
- [x] **BM25 Search** - PostgreSQL full-text search with ts_rank
- [x] **Hybrid Search** - RRF (Reciprocal Rank Fusion) merging
- [x] **Context Builder** - Format chunks for LLM with citations
- [x] **API Endpoints** - `/search`, `/search/hybrid`, `/search/bm25`, `/search/context`

**Key Files Created:**
```
backend/app/services/
├── rag_service.py              # 400+ lines - Vector/BM25/Hybrid + RRF

backend/app/infrastructure/repositories/
└── embedding_repository.py     # 250+ lines - Vector queries + cache
```

### Phase 4: Chat & LLM ✅ COMPLETED

- [x] **LLMService** - Ollama + OpenAI with streaming, fallback support
- [x] **ChatService** - RAG + LLM orchestration, conversation management
- [x] **ConversationRepository** - Database persistence for conversations/messages
- [x] **SSE Streaming** - Real-time response streaming via Server-Sent Events
- [x] **RAG Prompt Templates** - Thai/English auto-detection, source citation
- [x] **API Endpoints** - `/chat/stream`, `/chat/complete`, `/conversations`

**Key Files Created:**
```
backend/app/services/
├── llm_service.py          # 500+ lines - Ollama + OpenAI streaming
└── chat_service.py         # 450+ lines - RAG + LLM + Prompts

backend/app/infrastructure/repositories/
└── conversation_repository.py  # 300+ lines - Conversations + Messages
```

### Phase 5: Frontend ✅ COMPLETED

- [x] **Vite + React Setup** - React 18 + TypeScript + Vite
- [x] **Tailwind CSS** - Utility-first styling with custom theme
- [x] **Login Page** - JWT auth with show/hide password
- [x] **Chat Page** - SSE streaming with markdown, sources, typing indicator
- [x] **Documents Page** - Upload, drag & drop, search, delete
- [x] **Layout** - Collapsible sidebar with navigation
- [x] **Hooks** - useAuth (Zustand), useChat (SSE), useDocuments (React Query)
- [x] **API Services** - Axios with interceptors, SSE streaming

**Key Files Created:**
```
frontend/src/
├── pages/
│   ├── LoginPage.tsx       # 130 lines - JWT login form
│   ├── ChatPage.tsx        # 350 lines - SSE chat with sources
│   └── DocumentsPage.tsx   # 330 lines - Document management
├── hooks/
│   ├── useAuth.ts          # 80 lines - Zustand + persist
│   ├── useChat.ts          # 150 lines - SSE streaming
│   └── useDocuments.ts     # 100 lines - React Query
├── services/
│   ├── api.ts              # 200 lines - Axios client
│   └── sse.ts              # 120 lines - SSE streaming
└── components/layout/
    └── Layout.tsx          # 120 lines - Sidebar + navigation
```

### Phase 6: Database Connectors ✅ COMPLETED

- [x] **Connector Entity** - DatabaseConnection, TableInfo, SyncConfig models
- [x] **ConnectorRepository** - CRUD operations, sync status tracking
- [x] **PostgreSQL Connector** - Full support with schema discovery
- [x] **MySQL Connector** - Full support with aiomysql
- [x] **SQL Server Connector** - Full support with aioodbc
- [x] **ConnectorService** - Connection testing, schema discovery, data sync to RAG
- [x] **API Endpoints** - `/connectors` CRUD, test, schema, sync, preview, query
- [x] **Frontend Page** - Connection management UI, schema browser, sync controls
- [x] **Password Encryption** - Fernet symmetric encryption for credentials

**Key Files Created:**
```
backend/app/
├── domain/entities/
│   └── connector.py              # 200+ lines - Entity models
├── infrastructure/repositories/
│   └── connector_repository.py   # 200+ lines - Database ops
├── services/
│   └── connector_service.py      # 800+ lines - Full connector logic
└── api/v1/
    └── connectors.py             # 350+ lines - REST endpoints

frontend/src/
├── pages/
│   └── ConnectorsPage.tsx        # 500+ lines - Full management UI
└── hooks/
    └── useConnectors.ts          # 250+ lines - React Query hooks
```

**Supported Databases:**
| Database | Status | Features |
|----------|--------|----------|
| PostgreSQL | ✅ | Full schema, data preview, sync |
| MySQL | ✅ | Full schema, data preview, sync |
| SQL Server | ✅ | Full schema, data preview, sync |

### Phase 7: Advanced Features ✅ COMPLETED

- [x] **OCR Service** - Tesseract, PaddleOCR, EasyOCR with fallback
- [x] **Image Processing** - PNG/JPG/JPEG text extraction
- [x] **Scanned PDF OCR** - Automatic fallback when no text found
- [x] **Image Preprocessing** - Grayscale, threshold, deskew
- [x] **Admin Dashboard Backend** - System stats, user management, analytics
- [x] **Admin Dashboard Frontend** - Stats cards, user table, activity feed
- [x] **Usage Analytics** - Usage metrics over time, document stats, top users

**Key Files Created:**
```
backend/app/services/
├── ocr_service.py          # 400+ lines - Multi-engine OCR
└── admin_service.py        # 400+ lines - System analytics

backend/app/api/v1/
└── admin.py                # 400+ lines - Admin REST endpoints

frontend/src/
├── pages/
│   └── AdminPage.tsx       # 450+ lines - Full admin dashboard
└── hooks/
    └── useAdmin.ts         # 150+ lines - React Query hooks
```

**OCR Engines Supported:**
| Engine | Language Support | Performance |
|--------|-----------------|-------------|
| Tesseract | Thai + English | Good accuracy, widely available |
| PaddleOCR | Asian languages | Excellent for Thai/Chinese |
| EasyOCR | 80+ languages | Fallback option |

### Phase 8: Polish & Deploy ✅ COMPLETED

- [x] **Docker Setup** - Multi-stage builds, docker-compose, production config
- [x] **Backend Tests** - pytest with fixtures, unit tests, API tests
- [x] **Frontend Tests** - Vitest with Testing Library, hook tests, utility tests
- [x] **CI/CD Pipeline** - GitHub Actions for testing, building, and deployment

**Key Files Created:**
```
# Docker
Dockerfile (backend)           # Python 3.11 + OCR dependencies
Dockerfile (frontend)          # Node 20 + Nginx multi-stage
docker-compose.yml             # Full stack with pgvector
docker-compose.prod.yml        # Production overrides
.env.example                   # Environment template
nginx.conf                     # Nginx config with SSE support

# Backend Tests
backend/tests/
├── conftest.py               # Pytest fixtures
├── test_security.py          # JWT & password tests
├── test_entities.py          # Domain entity tests
├── test_services.py          # Service layer tests
└── test_api_auth.py          # API endpoint tests

# Frontend Tests
frontend/src/test/
└── setup.ts                  # Vitest setup
frontend/src/lib/
└── utils.test.ts             # Utility tests
frontend/src/hooks/
├── useAdmin.test.ts          # Admin hooks tests
├── useDocuments.test.ts      # Documents hooks tests
└── useConnectors.test.ts     # Connectors hooks tests

# CI/CD
.github/workflows/
├── ci.yml                    # Test & build on PR
└── deploy.yml                # Deploy to staging/production
```

**Docker Services:**
| Service | Image | Port |
|---------|-------|------|
| db | pgvector/pgvector:pg16 | 5432 |
| backend | cognify-backend | 8000 |
| frontend | cognify-frontend | 80 |

**CI/CD Pipeline:**
```
Push/PR → Lint → Type Check → Test → Build Docker → Security Scan
                                           ↓
                                    Deploy Staging
                                           ↓
                                    Deploy Production (on tag)
```

---

## Progress Tracker

| Phase | Description | Status | Progress |
|-------|-------------|--------|----------|
| 1 | Foundation | ✅ | 100% |
| 2 | Document Processing | ✅ | 100% |
| 3 | Search & RAG | ✅ | 100% |
| 4 | Chat & LLM | ✅ | 100% |
| 5 | Frontend | ✅ | 100% |
| 6 | DB Connectors | ✅ | 100% |
| 7 | Advanced Features | ✅ | 100% |
| 8 | Polish & Deploy | ✅ | 100% |

**Overall Progress: 100%** 🎉 CogniFy is complete!

---

## Quick Start

### Option 1: Docker (Recommended)
```bash
# 1. Clone and setup
cd /Users/davidsamanyaporn/PycharmProjects/CogniFy
cp .env.example .env
# Edit .env with your settings

# 2. Start all services
docker-compose up -d

# 3. Open app
open http://localhost

# 4. View logs
docker-compose logs -f

# 5. Stop services
docker-compose down
```

### Option 2: Local Development
```bash
# 1. Setup database
createdb cognify
psql -d cognify -f backend/migrations/001_initial_schema.sql

# 2. Setup backend
cd /Users/davidsamanyaporn/PycharmProjects/CogniFy/backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. Setup frontend (new terminal)
cd /Users/davidsamanyaporn/PycharmProjects/CogniFy/frontend
npm install
npm run dev

# 4. Open app
open http://localhost:5173
```

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm run test
```

---

## API Endpoints

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload & auto-process |
| POST | `/api/v1/documents/{id}/process` | Trigger processing |
| GET | `/api/v1/documents/{id}/stats` | Get processing stats |
| POST | `/api/v1/documents/{id}/reprocess` | Reprocess document |

### Search (Phase 3)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/search` | Semantic vector search |
| POST | `/api/v1/search/bm25` | Keyword search (BM25) |
| POST | `/api/v1/search/hybrid` | Hybrid search (RRF) |
| POST | `/api/v1/search/context` | Build RAG context |
| POST | `/api/v1/search/similar/{chunk_id}` | Find similar chunks |
| GET | `/api/v1/search/stats` | Search/embedding stats |

### Chat (Phase 4)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/stream` | **SSE streaming chat with RAG** |
| POST | `/api/v1/chat/complete` | Non-streaming chat |
| POST | `/api/v1/chat/conversations` | Create conversation |
| GET | `/api/v1/chat/conversations` | List conversations |
| GET | `/api/v1/chat/conversations/{id}` | Get conversation |
| GET | `/api/v1/chat/conversations/{id}/messages` | Get messages |
| DELETE | `/api/v1/chat/conversations/{id}` | Delete conversation |
| GET | `/api/v1/chat/health` | LLM health check |
| GET | `/api/v1/chat/models` | List available models |

### Connectors (Phase 6)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/connectors` | List all connections |
| POST | `/api/v1/connectors` | Create new connection |
| GET | `/api/v1/connectors/{id}` | Get connection |
| PUT | `/api/v1/connectors/{id}` | Update connection |
| DELETE | `/api/v1/connectors/{id}` | Delete connection |
| POST | `/api/v1/connectors/test` | Test new connection |
| POST | `/api/v1/connectors/{id}/test` | Test existing connection |
| GET | `/api/v1/connectors/{id}/schema` | Discover database schema |
| POST | `/api/v1/connectors/{id}/sync` | **Sync to RAG chunks** |
| GET | `/api/v1/connectors/{id}/preview/{table}` | Preview table data |
| POST | `/api/v1/connectors/{id}/query` | Execute SELECT query |

### Admin (Phase 7)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/stats` | System-wide statistics |
| GET | `/api/v1/admin/users` | List all users with stats |
| GET | `/api/v1/admin/usage` | Usage metrics over time |
| GET | `/api/v1/admin/documents/stats` | Document type statistics |
| GET | `/api/v1/admin/users/top` | Top users by activity |
| GET | `/api/v1/admin/activity` | Recent system activity |
| PUT | `/api/v1/admin/users/{id}/role` | Update user role |
| PUT | `/api/v1/admin/users/{id}/toggle-status` | Toggle user active status |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health/embedding` | Embedding service health |
| GET | `/api/v1/chat/health` | LLM service health |

---

## Default Credentials

| Type | Value |
|------|-------|
| Email | `admin@cognify.local` |
| Password | `admin123` |

---

*Created with love by Angela & David - 1 January 2026*
