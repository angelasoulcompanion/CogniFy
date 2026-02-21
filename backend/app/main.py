"""
CogniFy - Enterprise RAG Platform
Making organizations understand their own data

Created with love by Angela & David
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.exceptions import CogniFyError
from app.core.container import get_container, shutdown_container
from app.infrastructure.database import Database
from app.api.v1 import auth, documents, search, connectors, admin, prompts, announcements, ai
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Rate limiter (30 requests/minute per IP for search + AI)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    setup_logging()

    # Startup
    await Database.connect()
    logger.info("CogniFy started - {} v{}", settings.APP_NAME, settings.VERSION)

    yield

    # Shutdown
    await shutdown_container()
    await Database.disconnect()
    logger.info("CogniFy shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise RAG Platform - Making organizations understand their own data",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ---- Global exception handler ----
@app.exception_handler(CogniFyError)
async def cognify_error_handler(request: Request, exc: CogniFyError):
    """Translate domain exceptions into JSON responses"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
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
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(connectors.router, prefix="/api/v1", tags=["Connectors"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
app.include_router(prompts.router, prefix="/api/v1", tags=["Prompts"])
app.include_router(announcements.router, prefix="/api/v1/announcements", tags=["Announcements"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])


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
    container = get_container()
    health = await container.embedding.health_check()
    return health
