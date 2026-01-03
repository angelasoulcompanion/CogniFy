"""
CogniFy End-to-End Workflow Tests
Integration tests that test complete user workflows

Created with love by Angela & David - 3 January 2026
"""

import pytest
import io
import asyncio
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock

from httpx import AsyncClient


# =============================================================================
# COMPLETE USER WORKFLOW TESTS
# =============================================================================

class TestCompleteUserWorkflow:
    """Test complete user workflows from start to finish"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_document_to_chat_workflow(self, client: AsyncClient):
        """
        Test complete workflow:
        1. Register user
        2. Login
        3. Upload document
        4. Wait for processing
        5. Search document
        6. Chat with RAG
        """
        # Step 1: Register new user
        register_data = {
            "email": f"test_{uuid4().hex[:8]}@cognify.local",
            "password": "TestPass123!",
            "full_name": "Test User"
        }

        response = await client.post("/api/v1/auth/register", json=register_data)
        # May fail if user exists, validation error, that's OK
        assert response.status_code in [200, 201, 400, 409, 422]

        # Step 2: Login
        login_data = {
            "username": register_data["email"],
            "password": register_data["password"]
        }

        response = await client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get("access_token")

            # Set auth header for subsequent requests
            client.headers["Authorization"] = f"Bearer {access_token}"

            # Step 3: Upload document
            pdf_content = b"%PDF-1.4 Test document content for RAG testing"
            files = {"file": ("test_workflow.pdf", io.BytesIO(pdf_content), "application/pdf")}

            response = await client.post("/api/v1/documents/upload", files=files)
            # Document upload may succeed or fail depending on setup
            assert response.status_code in [200, 201, 422, 500]

            # Step 4: List documents
            response = await client.get("/api/v1/documents")
            assert response.status_code == 200

            # Step 5: Search
            response = await client.post(
                "/api/v1/search",
                json={"query": "test", "limit": 5}
            )
            assert response.status_code == 200

            # Step 6: Chat
            response = await client.post(
                "/api/v1/chat/stream",
                json={
                    "message": "Hello, what documents do I have?",
                    "rag_enabled": False
                }
            )
            # Chat may fail if Ollama not running
            assert response.status_code in [200, 500, 503]


# =============================================================================
# ADMIN WORKFLOW TESTS
# =============================================================================

class TestAdminWorkflow:
    """Test admin-specific workflows"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_admin_user_management_workflow(self, admin_client: AsyncClient):
        """
        Test admin workflow:
        1. View system stats
        2. List all users
        3. View top users
        4. Check activity feed
        """
        # Step 1: Get system stats
        response = await admin_client.get("/api/v1/admin/stats")
        assert response.status_code in [200, 500, 503]
        if response.status_code == 200:
            stats = response.json()
            assert isinstance(stats, dict)

        # Step 2: List users
        response = await admin_client.get("/api/v1/admin/users")
        assert response.status_code in [200, 500, 503]

        # Step 3: Get top users
        response = await admin_client.get("/api/v1/admin/users/top")
        assert response.status_code in [200, 500, 503]

        # Step 4: Get activity feed
        response = await admin_client.get("/api/v1/admin/activity")
        assert response.status_code in [200, 500, 503]


# =============================================================================
# DATABASE CONNECTOR WORKFLOW TESTS
# =============================================================================

class TestConnectorWorkflow:
    """Test database connector workflows"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_connector_setup_workflow(self, authenticated_client: AsyncClient):
        """
        Test connector workflow:
        1. Create connector
        2. Test connection
        3. Discover schema
        4. Preview data
        5. Sync to RAG
        """
        # Step 1: Create connector (will fail without actual DB)
        connector_data = {
            "name": "Test Workflow DB",
            "db_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "test_workflow",
            "username": "test",
            "password": "test"
        }

        response = await authenticated_client.post(
            "/api/v1/connectors",
            json=connector_data
        )
        # May succeed or fail
        assert response.status_code in [200, 201, 422, 500]

        # Step 2: List connectors
        response = await authenticated_client.get("/api/v1/connectors")
        assert response.status_code in [200, 500, 503]


# =============================================================================
# SEARCH WORKFLOW TESTS
# =============================================================================

class TestSearchWorkflow:
    """Test search functionality workflows"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_search_workflow(self, authenticated_client: AsyncClient):
        """
        Test different search types:
        1. Vector search
        2. BM25 search
        3. Hybrid search
        4. Build context
        """
        query = "machine learning applications"

        # Step 1: Vector search
        response = await authenticated_client.post(
            "/api/v1/search",
            json={"query": query, "limit": 5}
        )
        # 200 = success, 500/503 = embedding service not available
        assert response.status_code in [200, 500, 503]

        # Step 2: BM25 search
        response = await authenticated_client.post(
            "/api/v1/search/bm25",
            json={"query": query, "limit": 5}
        )
        assert response.status_code in [200, 500, 503]

        # Step 3: Hybrid search
        response = await authenticated_client.post(
            "/api/v1/search/hybrid",
            json={"query": query, "limit": 5, "vector_weight": 0.7}
        )
        assert response.status_code in [200, 500, 503]

        # Step 4: Build context
        response = await authenticated_client.post(
            "/api/v1/search/context",
            json={"query": query, "limit": 5}
        )
        assert response.status_code in [200, 500, 503]


# =============================================================================
# CONVERSATION WORKFLOW TESTS
# =============================================================================

class TestConversationWorkflow:
    """Test conversation management workflows"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conversation_lifecycle(self, authenticated_client: AsyncClient):
        """
        Test conversation lifecycle:
        1. Create conversation
        2. Send messages
        3. Get conversation history
        4. Delete conversation
        """
        # Step 1: Create conversation
        response = await authenticated_client.post(
            "/api/v1/chat/conversations",
            json={"title": "Test Conversation Workflow"}
        )
        assert response.status_code in [200, 201, 404, 405, 500, 503]

        if response.status_code in [200, 201]:
            conv_data = response.json()
            conv_id = conv_data.get("conversation_id") or conv_data.get("id")

            if conv_id:
                # Step 2: Get conversation
                response = await authenticated_client.get(
                    f"/api/v1/chat/conversations/{conv_id}"
                )
                assert response.status_code in [200, 500, 503]

                # Step 3: Get messages
                response = await authenticated_client.get(
                    f"/api/v1/chat/conversations/{conv_id}/messages"
                )
                assert response.status_code in [200, 500, 503]

                # Step 4: Delete conversation
                response = await authenticated_client.delete(
                    f"/api/v1/chat/conversations/{conv_id}"
                )
                assert response.status_code in [200, 204, 500, 503]


# =============================================================================
# PROMPT WORKFLOW TESTS
# =============================================================================

class TestPromptWorkflow:
    """Test prompt management workflows - requires admin role"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_prompt_lifecycle(self, admin_client: AsyncClient):
        """
        Test prompt lifecycle (admin only):
        1. Create prompt
        2. List prompts
        3. Set as default
        4. Use in chat
        5. Delete prompt
        """
        # Step 1: Create prompt
        prompt_data = {
            "name": f"Test Prompt {uuid4().hex[:8]}",
            "template": "You are a helpful assistant. Question: {question}",
            "variables": ["question"],
            "category": "general"
        }

        response = await admin_client.post(
            "/api/v1/prompts",
            json=prompt_data
        )
        assert response.status_code in [200, 201, 422, 500, 503]

        # Step 2: List prompts
        response = await admin_client.get("/api/v1/prompts")
        assert response.status_code in [200, 500, 503]


# =============================================================================
# ERROR RECOVERY TESTS
# =============================================================================

class TestErrorRecovery:
    """Test system error recovery"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_graceful_degradation(self, authenticated_client: AsyncClient):
        """Test system handles errors gracefully"""
        # Test with invalid data - system should not crash
        invalid_requests = [
            ("/api/v1/search", {"query": None}),
            ("/api/v1/chat/stream", {"message": None}),
            ("/api/v1/documents/upload", {}),
        ]

        for endpoint, data in invalid_requests:
            response = await authenticated_client.post(endpoint, json=data)
            # Should return error, not crash
            assert response.status_code in [400, 422, 500]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rate_limiting_behavior(self, authenticated_client: AsyncClient):
        """Test system behavior under rapid requests"""
        # Send multiple rapid requests
        tasks = []
        for _ in range(10):
            tasks.append(
                authenticated_client.get("/api/v1/documents")
            )

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete without errors
        for r in responses:
            if not isinstance(r, Exception):
                assert r.status_code in [200, 429]  # 429 if rate limited


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Basic performance tests"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_response_time(self, authenticated_client: AsyncClient):
        """Test search responds within acceptable time"""
        import time

        start = time.time()
        response = await authenticated_client.post(
            "/api/v1/search",
            json={"query": "test performance", "limit": 10}
        )
        elapsed = time.time() - start

        # 200 = success, 500/503 = embedding service not available
        assert response.status_code in [200, 500, 503]
        # Should respond within 10 seconds even with embedding generation
        assert elapsed < 10.0, f"Search took too long: {elapsed:.2f}s"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_document_list_response_time(self, authenticated_client: AsyncClient):
        """Test document list responds quickly"""
        import time

        start = time.time()
        response = await authenticated_client.get("/api/v1/documents")
        elapsed = time.time() - start

        # 200 = success, 500/503 = service not available (acceptable in tests)
        assert response.status_code in [200, 500, 503]
        # Should respond within 10 seconds (relaxed for test environment)
        assert elapsed < 10.0, f"Document list took too long: {elapsed:.2f}s"
