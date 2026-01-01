# CogniFy

> **Making organizations understand their own data**

Enterprise RAG Platform built with FastAPI, React, and PostgreSQL.

---

## Features

- **Document Management** - Upload PDF, DOCX, TXT, Excel files
- **Semantic Chunking** - Intelligent text splitting with Thai support
- **Vector Search** - Similarity search using pgvector
- **Cached Embeddings** - Fast processing with in-memory + DB cache
- **RAG Chat** - Chat with your documents (coming soon)
- **Database Connectors** - Connect to external databases (coming soon)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + TypeScript + Vite |
| **Backend** | FastAPI (Python 3.11+) |
| **Database** | PostgreSQL 16 + pgvector |
| **LLM** | Ollama (local) + OpenAI (optional) |
| **Embedding** | nomic-embed-text (768-dim) |

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ with pgvector
- Ollama (for embeddings)

### Setup

```bash
cd /Users/davidsamanyaporn/PycharmProjects/CogniFy/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

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

### Access

- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/api/health

---

## Default Credentials

- **Email**: admin@cognify.local
- **Password**: admin123

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
- `GET /api/v1/documents/{id}/stats` - Processing stats
- `POST /api/v1/documents/{id}/process` - Trigger processing
- `DELETE /api/v1/documents/{id}` - Delete document

### Health
- `GET /api/health` - System health
- `GET /api/health/embedding` - Embedding service health

---

## Project Structure

```
CogniFy/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # FastAPI routers
│   │   ├── core/             # Config & Security
│   │   ├── domain/           # Entities
│   │   ├── infrastructure/   # Repositories
│   │   ├── services/         # Business logic
│   │   └── main.py
│   ├── migrations/
│   └── requirements.txt
└── frontend/                 # Coming soon
```

---

## Development Progress

- [x] Phase 1: Foundation (100%)
- [x] Phase 2: Document Processing (100%)
- [ ] Phase 3: Search & RAG
- [ ] Phase 4: Chat & LLM
- [ ] Phase 5: Frontend

---

## License

MIT

---

*Created with love by Angela & David*
