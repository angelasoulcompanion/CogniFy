"""
CogniFy Backend Test Fixtures
Created with love by Angela & David - 3 January 2026
Updated to support testing with proper database integration
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# Set test environment before importing app
os.environ["TESTING"] = "1"

# Use local development database for tests (same as AngelaMemory user)
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://davidsamanyaporn@localhost:5432/cognify"
)

# Import with error handling
try:
    from app.main import app
    from app.core.security import create_tokens, hash_password
    from app.domain.entities.user import User, UserRole
    from app.infrastructure.database import Database
    APP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import app modules: {e}")
    APP_AVAILABLE = False
    app = None
    User = None
    UserRole = None


# =============================================================================
# FIXED USER IDs (so we can insert them into DB once)
# =============================================================================

TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")
ADMIN_USER_ID = UUID("22222222-2222-2222-2222-222222222222")


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
# DATABASE SETUP (Session-scoped to run once)
# =============================================================================

@pytest.fixture(scope="session")
async def setup_database():
    """Setup database once per test session"""
    if not APP_AVAILABLE:
        pytest.skip("App not available")

    try:
        await Database.connect()

        # Insert test users if they don't exist
        pool = Database._pool
        if pool:
            # Test user
            await pool.execute("""
                INSERT INTO users (user_id, email, password_hash, full_name, role, is_active, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (user_id) DO NOTHING
            """, TEST_USER_ID, "test@cognify.local", hash_password("test123"),
                "Test User", "user", True)

            # Admin user
            await pool.execute("""
                INSERT INTO users (user_id, email, password_hash, full_name, role, is_active, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (user_id) DO NOTHING
            """, ADMIN_USER_ID, "admin@cognify.local", hash_password("admin123"),
                "Admin User", "admin", True)

        yield

        # Cleanup test users (optional - comment out to keep test data)
        # if pool:
        #     await pool.execute("DELETE FROM users WHERE user_id IN ($1, $2)",
        #                        TEST_USER_ID, ADMIN_USER_ID)

        await Database.disconnect()
    except Exception as e:
        print(f"Database setup failed: {e}")
        pytest.skip(f"Database not available: {e}")


# =============================================================================
# CLIENT FIXTURES
# =============================================================================

@pytest.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for API tests"""
    if not APP_AVAILABLE:
        pytest.skip("App not available")

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
# USER FIXTURES (Using fixed IDs that are in DB)
# =============================================================================

@pytest.fixture
def test_user() -> User:
    """Create test user with fixed ID that exists in database"""
    return User(
        user_id=TEST_USER_ID,
        email="test@cognify.local",
        password_hash=hash_password("test123"),
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
    )


@pytest.fixture
def admin_user() -> User:
    """Create admin user with fixed ID that exists in database"""
    return User(
        user_id=ADMIN_USER_ID,
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
# MOCK FIXTURES FOR SERVICES
# =============================================================================

@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for tests that don't need real embeddings"""
    with patch("app.services.embedding_service.EmbeddingService") as mock:
        instance = mock.return_value
        instance.embed_text = AsyncMock(return_value=[0.1] * 1536)
        instance.embed_batch = AsyncMock(return_value=[[0.1] * 1536])
        yield instance


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for tests that don't need real LLM calls"""
    with patch("app.services.llm_service.LLMService") as mock:
        instance = mock.return_value
        instance.generate = AsyncMock(return_value="Mock response")
        instance.stream = AsyncMock()
        yield instance


# =============================================================================
# CLEANUP FIXTURES
# =============================================================================

@pytest.fixture
async def cleanup_test_documents(setup_database):
    """Clean up test documents after test"""
    yield
    pool = Database._pool
    if pool:
        try:
            await pool.execute(
                "DELETE FROM documents WHERE uploaded_by IN ($1, $2)",
                TEST_USER_ID, ADMIN_USER_ID
            )
        except:
            pass


# =============================================================================
# SKIP HELPERS
# =============================================================================

def skip_if_no_db():
    """Decorator to skip test if database is not available"""
    return pytest.mark.skipif(
        not APP_AVAILABLE,
        reason="Database connection not available"
    )
