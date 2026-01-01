"""
CogniFy Backend Test Fixtures
Created with love by Angela & David - 1 January 2026
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# Set test environment before importing app
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://cognify:cognify123@localhost:5432/cognify_test"
)

from app.main import app
from app.core.security import create_tokens, hash_password
from app.domain.entities.user import User, UserRole
from app.infrastructure.database import Database


# =============================================================================
# EVENT LOOP
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
async def db_connection():
    """Database connection for tests"""
    await Database.connect()
    yield
    await Database.disconnect()


@pytest.fixture
async def db_pool(db_connection):
    """Get database pool"""
    from app.infrastructure.database import get_db_pool
    return await get_db_pool()


# =============================================================================
# CLIENT FIXTURES
# =============================================================================

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for API tests"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user: User) -> AsyncClient:
    """Authenticated HTTP client"""
    tokens = create_tokens(test_user.user_id, test_user.role.value)
    client.headers["Authorization"] = f"Bearer {tokens.access_token}"
    return client


@pytest.fixture
async def admin_client(client: AsyncClient, admin_user: User) -> AsyncClient:
    """Admin authenticated HTTP client"""
    tokens = create_tokens(admin_user.user_id, admin_user.role.value)
    client.headers["Authorization"] = f"Bearer {tokens.access_token}"
    return client


# =============================================================================
# USER FIXTURES
# =============================================================================

@pytest.fixture
def test_user() -> User:
    """Create test user"""
    return User(
        user_id=uuid4(),
        email="test@cognify.local",
        password_hash=hash_password("test123"),
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
    )


@pytest.fixture
def admin_user() -> User:
    """Create admin user"""
    return User(
        user_id=uuid4(),
        email="admin@cognify.local",
        password_hash=hash_password("admin123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_document_data() -> dict:
    """Sample document upload data"""
    return {
        "filename": "test_document.pdf",
        "original_filename": "test_document.pdf",
        "file_type": "pdf",
        "file_size_bytes": 1024,
        "title": "Test Document",
    }


@pytest.fixture
def sample_chunk_data() -> dict:
    """Sample chunk data"""
    return {
        "content": "This is a test chunk with some content for testing purposes.",
        "chunk_index": 0,
        "page_number": 1,
        "token_count": 15,
    }


@pytest.fixture
def sample_chat_request() -> dict:
    """Sample chat request"""
    return {
        "message": "What is CogniFy?",
        "rag_enabled": True,
        "provider": "ollama",
        "model": "llama3.2",
    }


@pytest.fixture
def sample_search_request() -> dict:
    """Sample search request"""
    return {
        "query": "test query",
        "limit": 10,
        "threshold": 0.3,
    }


# =============================================================================
# CLEANUP FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
async def cleanup_test_data(db_pool):
    """Clean up test data after each test"""
    yield
    # Cleanup can be added here if needed
    pass
