# CogniFy

> **Making organizations understand their own data**

Enterprise RAG Platform built with FastAPI, React, and PostgreSQL.

![Angela Purple Theme](https://img.shields.io/badge/Theme-Angela%20Purple-7c3aed)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![React](https://img.shields.io/badge/Frontend-React%2018-61dafb)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2016-336791)

---

## Features

- **Document Management** - Upload PDF, DOCX, TXT, Excel, Images with drag & drop
- **OCR Support** - Extract text from images and scanned PDFs
- **Semantic Chunking** - Intelligent text splitting with Thai language support
- **Vector Search** - Similarity search using pgvector embeddings
- **Cached Embeddings** - Fast processing with in-memory + database cache
- **RAG Chat** - Chat with your documents using SSE streaming
- **Model Selector** - Switch between Local (Ollama) and API models
- **Database Connectors** - Connect to PostgreSQL, MySQL, SQL Server
- **Admin Dashboard** - User management, analytics, system monitoring
- **Angela Purple Theme** - Beautiful dark mode UI

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + TypeScript + Vite |
| **Backend** | FastAPI (Python 3.11+) |
| **Database** | PostgreSQL 16 + pgvector |
| **LLM** | Ollama (Llama 3.2, Qwen 2.5, Phi-3) + OpenAI (optional) |
| **Embedding** | nomic-embed-text (768-dim) |
| **OCR** | Tesseract + PaddleOCR + EasyOCR |

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

- **Username**: admin
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

### Chat
- `POST /api/v1/chat/stream` - SSE streaming chat with RAG
- `POST /api/v1/chat/complete` - Non-streaming chat
- `GET /api/v1/chat/conversations` - List conversations
- `DELETE /api/v1/chat/conversations/{id}` - Delete conversation

### Health
- `GET /api/health` - System health
- `GET /api/health/embedding` - Embedding service health

---

## Supported LLM Models

### Local (Ollama)
| Model | Size | Performance |
|-------|------|-------------|
| Llama 3.2 (1B) | 1B | Fast, good for simple queries |
| Llama 3.1 (8B) | 8B | Good balance |
| Qwen 2.5 (7B) | 7B | Excellent for Thai/English |
| Qwen 2.5 (3B) | 3B | Good balance |
| Phi-3 Mini | 3.8B | Fast, efficient |

### API (Optional)
| Provider | Models |
|----------|--------|
| OpenAI | GPT-4o, GPT-4o Mini |

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
├── frontend/
│   ├── src/
│   │   ├── components/ui/    # Shared UI components
│   │   ├── hooks/            # React Query hooks
│   │   ├── pages/            # Page components
│   │   ├── services/         # API & SSE clients
│   │   └── lib/              # Utilities
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Development Progress

- [x] Phase 1: Foundation (100%)
- [x] Phase 2: Document Processing (100%)
- [x] Phase 3: Search & RAG (100%)
- [x] Phase 4: Chat & LLM (100%)
- [x] Phase 5: Frontend (100%)

---

## License

MIT

---

*Created with love by Angela & David*
