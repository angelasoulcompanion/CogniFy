# CogniFy

> **Making organizations understand their own data**

Enterprise RAG Platform built with FastAPI, React, and PostgreSQL.

![Version](https://img.shields.io/badge/Version-1.0.0-7c3aed)
![Angela Purple Theme](https://img.shields.io/badge/Theme-Angela%20Purple-7c3aed)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![React](https://img.shields.io/badge/Frontend-React%2018-61dafb)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2016-336791)
![Ollama](https://img.shields.io/badge/LLM-Ollama-white)

---

## Features

- **Document Management** - Upload PDF, DOCX, TXT, Excel, Images with drag & drop
- **OCR Support** - Typhoon-OCR 1.5-3B for images, Tesseract for scanned PDFs (Thai + English)
- **Semantic Chunking** - Intelligent text splitting with Thai language support
- **Hybrid Search** - Vector + BM25 + Reciprocal Rank Fusion (RRF)
- **HyDE** - Hypothetical Document Embedding for better retrieval
- **Re-ranking** - LLM-based relevance scoring
- **Cached Embeddings** - Fast processing with in-memory + database cache
- **Ask AI** - RAG-powered answers with source references
- **RAG Chat** - Chat with your documents using SSE streaming
- **Model Selector** - Switch between Local (Ollama) and Anthropic Claude
- **Database Connectors** - Connect to PostgreSQL, MySQL, SQL Server
- **Prompt Templates** - Customizable system prompts with AI wizard
- **Admin Dashboard** - User management, analytics, system monitoring
- **Announcements** - Organization news with pinned & categorized posts
- **Angela Purple Theme** - Beautiful dark mode UI

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS |
| **Backend** | FastAPI (Python 3.11+) |
| **Database** | PostgreSQL 16 + pgvector |
| **LLM (Local)** | Ollama — Typhoon 2.5 Qwen3 4B (Thai+English bilingual) |
| **LLM (API)** | Anthropic Claude (Sonnet 4.6, Haiku 4.5) |
| **Embedding** | BGE-M3 (1024-dim, 8192 tokens, 100+ languages) |
| **OCR** | Typhoon-OCR 1.5-3B (Ollama Vision) + Tesseract |
| **Search** | pgvector (cosine/euclidean/dot) + BM25 + RRF |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+ with pgvector extension
- Ollama

### Ollama Models

```bash
# Required
ollama pull bge-m3                          # Embedding (1024-dim, multilingual)
ollama pull scb10x/typhoon2.5-qwen3-4b     # LLM (Thai+English 4B)

# Optional
ollama pull scb10x/typhoon-ocr1.5-3b       # OCR for images
ollama pull qwen2.5:7b                      # HyDE + Re-ranking
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Create database
createdb cognify
psql -d cognify -f migrations/001_initial_schema.sql

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### Access

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/api/health

---

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@cognify.com | admin123 |

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register
- `GET /api/v1/auth/me` - Current user

### Documents
- `GET /api/v1/documents` - List documents
- `POST /api/v1/documents/upload` - Upload & process
- `GET /api/v1/documents/{id}` - Get document
- `GET /api/v1/documents/{id}/chunks` - Get chunks
- `POST /api/v1/documents/{id}/reprocess` - Reprocess document
- `DELETE /api/v1/documents/{id}` - Delete document

### Search
- `POST /api/v1/search` - Hybrid search (vector + BM25 + RRF)
- `GET /api/v1/search/stats` - Search statistics

### AI
- `POST /api/v1/ai/complete` - AI completion (Ask AI)
- `GET /api/v1/ai/models` - List available models
- `GET /api/v1/ai/health` - AI service health

### Chat
- `POST /api/v1/chat/stream` - SSE streaming chat with RAG
- `GET /api/v1/chat/conversations` - List conversations
- `DELETE /api/v1/chat/conversations/{id}` - Delete conversation

### Database Connectors
- `POST /api/v1/connectors` - Create connection
- `POST /api/v1/connectors/{id}/test` - Test connection
- `POST /api/v1/connectors/{id}/sync` - Sync schema to RAG

### Admin
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/users` - User management
- `GET /api/v1/admin/usage-metrics` - Usage analytics

---

## Supported Models

### Local (Ollama)
| Model | Type | Languages |
|-------|------|-----------|
| Typhoon 2.5 Qwen3 (4B) | Chat/Completion | Thai + English |
| Typhoon-OCR 1.5 (3B) | Vision/OCR | Thai + English |
| BGE-M3 | Embedding (1024-dim) | 100+ languages |
| Qwen 2.5 (7B) | HyDE + Re-ranking | Multilingual |

### API (Anthropic Claude)
| Model | Use Case |
|-------|----------|
| Claude Sonnet 4.6 | High-quality responses |
| Claude Haiku 4.5 | Fast, cost-efficient |

---

## Project Structure

```
CogniFy/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # FastAPI routers
│   │   ├── core/             # Config, Security, Encryption
│   │   ├── domain/           # Entities & Enums
│   │   ├── infrastructure/   # Repositories (asyncpg)
│   │   ├── services/         # Business logic
│   │   │   ├── document_service.py    # Extract → Chunk → Embed → Store
│   │   │   ├── rag_service.py         # Hybrid search + HyDE + Re-rank
│   │   │   ├── llm_service.py         # Ollama + Anthropic providers
│   │   │   ├── ocr_service.py         # Typhoon-OCR + Tesseract
│   │   │   ├── embedding_service.py   # BGE-M3 with caching
│   │   │   └── chunking_service.py    # Thai-aware text splitting
│   │   └── main.py
│   ├── migrations/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # UI components + Layout
│   │   ├── hooks/            # React Query hooks
│   │   ├── pages/            # Page components
│   │   ├── services/         # API & SSE clients
│   │   ├── stores/           # Zustand state
│   │   └── types/            # TypeScript types
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Development Progress

- [x] Phase 1: Foundation — Auth, Database, Clean Architecture
- [x] Phase 2: Document Processing — Extract, Chunk, Embed pipeline
- [x] Phase 3: Search & RAG — Hybrid search, HyDE, Re-ranking
- [x] Phase 4: Chat & LLM — SSE streaming, Ollama + Anthropic
- [x] Phase 5: Frontend — React 18, Angela Purple Theme
- [x] Phase 6: Advanced — OCR, Database Connectors, Prompts, Announcements
- [x] **v1.0.0** — Typhoon OCR, Anthropic Claude, Thai text quality

---

## License

MIT

---

*Created with love by Angela & David - 2026*
