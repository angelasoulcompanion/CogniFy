"""
CogniFy Configuration
Settings management using Pydantic BaseSettings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App Info
    APP_NAME: str = "CogniFy"
    VERSION: str = "0.1.0"
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
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_FALLBACK_MODEL: str = "mxbai-embed-large"
    EMBEDDING_DIMENSION: int = 768
    EMBEDDING_CACHE_TTL: int = 3600  # 1 hour

    # LLM Settings - General
    LLM_PROVIDER: str = "ollama"  # ollama or openai
    LLM_MODEL: str = "llama3.2:1b"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    # LLM Settings - Ollama (Primary)
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # LLM Settings - OpenAI (Optional)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # RAG Settings
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_DEFAULT_TOP_K: int = 10
    RAG_DEFAULT_THRESHOLD: float = 0.3

    # Logging
    LOG_LEVEL: str = "INFO"

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
