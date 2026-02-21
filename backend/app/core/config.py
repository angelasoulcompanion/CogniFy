"""
CogniFy Configuration
Settings management using Pydantic BaseSettings
"""

from typing import List, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App Info
    APP_NAME: str = "CogniFy"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://davidsamanyaporn@localhost:5432/cognify"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # JWT Settings
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Encryption (for database connector passwords)
    ENCRYPTION_KEY: Optional[str] = None  # 32-byte Fernet key, auto-generated if not set

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"]

    # Embedding Settings
    EMBEDDING_MODEL: str = "bge-m3"  # Best: 1024 dims, 8192 context, 100+ languages
    EMBEDDING_FALLBACK_MODEL: str = "mxbai-embed-large"
    EMBEDDING_DIMENSION: int = 1024
    EMBEDDING_CACHE_TTL: int = 3600  # 1 hour

    # OCR Settings
    OCR_MODEL: str = "scb10x/typhoon-ocr1.5-3b"  # Bilingual Thai+English vision model via Ollama

    # LLM Settings - General
    LLM_PROVIDER: str = "ollama"  # ollama or anthropic
    LLM_MODEL: str = "scb10x/typhoon2.5-qwen3-4b"  # Bilingual Thai+English 4B based on Qwen3
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    # LLM Settings - Ollama (Primary)
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # LLM Settings - Anthropic (Optional)
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"

    # OpenAI Embedding (Optional - for text-embedding-3-small fallback)
    OPENAI_API_KEY: Optional[str] = None

    # RAG Settings - Chunking
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 100  # Increased for better context (was 50)
    RAG_DEFAULT_TOP_K: int = 10
    RAG_DEFAULT_THRESHOLD: float = 0.3

    # RAG Settings - HyDE (Hypothetical Document Embedding)
    HYDE_ENABLED: bool = True
    HYDE_MODEL: str = "scb10x/typhoon2.5-qwen3-4b"  # Same as LLM_MODEL, bilingual Thai+English

    # RAG Settings - Re-ranking
    RERANK_ENABLED: bool = True
    RERANK_MODEL: str = "scb10x/typhoon2.5-qwen3-4b"  # Same as LLM_MODEL, bilingual Thai+English
    RERANK_TOP_N: int = 10  # Fetch this many before re-ranking (was 20, reduced for speed)
    RERANK_RETURN_K: int = 5  # Return this many after re-ranking

    # Logging
    LOG_LEVEL: str = "INFO"

    @model_validator(mode="after")
    def _check_jwt_secret(self) -> "Settings":
        """Auto-generate JWT secret for local dev, fail in production"""
        if self.JWT_SECRET_KEY.startswith("your-"):
            import os
            if os.environ.get("DOCKER_CONTAINER") or os.environ.get("PRODUCTION"):
                raise ValueError(
                    "JWT_SECRET_KEY must be changed from the default placeholder in production. "
                    "Set JWT_SECRET_KEY in your environment or .env file."
                )
            import secrets
            self.JWT_SECRET_KEY = secrets.token_urlsafe(32)
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
