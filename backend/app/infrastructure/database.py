"""
CogniFy Database Module
Async PostgreSQL connection using asyncpg with connection pooling
Pattern from AngelaAI
"""

from typing import Optional, List, Any, Dict
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool, Connection, Record

from app.core.config import settings


class Database:
    """
    Async PostgreSQL database connection manager.
    Uses connection pooling for efficient resource usage.
    """

    _pool: Optional[Pool] = None

    @classmethod
    async def connect(cls) -> None:
        """Initialize the database connection pool"""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=2,
                max_size=settings.DATABASE_POOL_SIZE,
                max_inactive_connection_lifetime=300,
                command_timeout=60,
            )
            print(f"✅ Database pool created: {settings.DATABASE_URL.split('@')[-1]}")

    @classmethod
    async def disconnect(cls) -> None:
        """Close the database connection pool"""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None
            print("✅ Database pool closed")

    @classmethod
    async def health_check(cls) -> bool:
        """Check if database is healthy"""
        try:
            if cls._pool is None:
                return False
            async with cls._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    @classmethod
    def get_pool(cls) -> Pool:
        """Get the connection pool"""
        if cls._pool is None:
            raise RuntimeError("Database pool not initialized. Call Database.connect() first.")
        return cls._pool

    @classmethod
    @asynccontextmanager
    async def acquire(cls):
        """Acquire a connection from the pool"""
        pool = cls.get_pool()
        async with pool.acquire() as connection:
            yield connection

    @classmethod
    async def fetch(cls, query: str, *args) -> List[Record]:
        """Execute a query and return all results"""
        async with cls.acquire() as conn:
            return await conn.fetch(query, *args)

    @classmethod
    async def fetchrow(cls, query: str, *args) -> Optional[Record]:
        """Execute a query and return first row"""
        async with cls.acquire() as conn:
            return await conn.fetchrow(query, *args)

    @classmethod
    async def fetchval(cls, query: str, *args) -> Any:
        """Execute a query and return first column of first row"""
        async with cls.acquire() as conn:
            return await conn.fetchval(query, *args)

    @classmethod
    async def execute(cls, query: str, *args) -> str:
        """Execute a query without returning results"""
        async with cls.acquire() as conn:
            return await conn.execute(query, *args)

    @classmethod
    async def executemany(cls, query: str, args: List[tuple]) -> None:
        """Execute a query with multiple sets of arguments"""
        async with cls.acquire() as conn:
            await conn.executemany(query, args)

    @classmethod
    @asynccontextmanager
    async def transaction(cls):
        """Context manager for database transactions"""
        async with cls.acquire() as conn:
            async with conn.transaction():
                yield conn


# Dependency for FastAPI
async def get_db() -> Connection:
    """FastAPI dependency to get database connection"""
    async with Database.acquire() as conn:
        yield conn


# Alias for convenience
db = Database


async def get_db_pool() -> Pool:
    """Get database connection pool (async function for services)"""
    return Database.get_pool()
