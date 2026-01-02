"""
CogniFy - Enterprise RAG Platform
Making organizations understand their own data

Created with love by Angela & David
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.infrastructure.database import Database
from app.api.v1 import auth, documents, chat, search, connectors, admin, prompts
from app.services.embedding_service import get_embedding_service, shutdown_embedding_service
from app.services.llm_service import shutdown_llm_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    await Database.connect()
    print(f"🚀 CogniFy started - {settings.APP_NAME} v{settings.VERSION}")

    yield

    # Shutdown
    await shutdown_embedding_service()
    await shutdown_llm_service()
    await Database.disconnect()
    print("👋 CogniFy shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise RAG Platform - Making organizations understand their own data",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(connectors.router, prefix="/api/v1", tags=["Connectors"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
app.include_router(prompts.router, prefix="/api/v1", tags=["Prompts"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "message": "Making organizations understand their own data"
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    db_status = await Database.health_check()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "version": settings.VERSION
    }


@app.get("/api/health/embedding", tags=["Health"])
async def embedding_health_check():
    """Check embedding service health"""
    embedding_service = get_embedding_service()
    health = await embedding_service.health_check()
    return health
