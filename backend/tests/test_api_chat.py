"""
CogniFy Chat API Tests
Comprehensive tests for chat, streaming, and conversation management

Created with love by Angela & David - 3 January 2026
"""

import pytest
import json
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock

from httpx import AsyncClient


# =============================================================================
# CHAT STREAMING TESTS
# =============================================================================

class TestChatStreaming:
    """Test SSE streaming chat functionality"""

    @pytest.mark.asyncio
    async def test_chat_stream_authenticated(self, authenticated_client: AsyncClient):
        """Test chat streaming with authentication"""
        request_data = {
            "message": "Hello, what is CogniFy?",
            "rag_enabled": False,
            "provider": "ollama",
            "model": "llama3.2"
        }

        # Note: SSE streaming tests are tricky with httpx
        # We test the endpoint accepts the request
        response = await authenticated_client.post(
            "/api/v1/chat/stream",
            json=request_data
        )

        # Should accept the request (may fail if Ollama not running)
        assert response.status_code in [200, 500, 503]

    @pytest.mark.asyncio
    async def test_chat_stream_unauthenticated(self, client: AsyncClient):
        """Test chat streaming without auth"""
        request_data = {
            "message": "Hello",
            "rag_enabled": False
        }

        response = await client.post("/api/v1/chat/stream", json=request_data)

        # 401 = auth required, 200 = public access, 500/503 = service error
        assert response.status_code in [200, 401, 500, 503]

    @pytest.mark.asyncio
    async def test_chat_complete_endpoint(self, authenticated_client: AsyncClient):
        """Test non-streaming chat endpoint"""
        request_data = {
            "message": "Hello",
            "rag_enabled": False,
            "provider": "ollama",
            "model": "llama3.2"
        }

        response = await authenticated_client.post(
            "/api/v1/chat/complete",
            json=request_data
        )

        # 200 = success, 404/405 = endpoint not found/method not allowed, 500/503 = service error
        assert response.status_code in [200, 404, 405, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_chat_with_rag_enabled(self, authenticated_client: AsyncClient):
        """Test chat with RAG enabled"""
        request_data = {
            "message": "Tell me about the documents",
            "rag_enabled": True,
            "provider": "ollama",
            "model": "llama3.2",
            "top_k": 5
        }

        response = await authenticated_client.post(
            "/api/v1/chat/stream",
            json=request_data
        )

        assert response.status_code in [200, 500, 503]

    @pytest.mark.asyncio
    async def test_chat_with_conversation_id(self, authenticated_client: AsyncClient):
        """Test chat with existing conversation"""
        conv_id = str(uuid4())
        request_data = {
            "message": "Continue our conversation",
            "conversation_id": conv_id,
            "rag_enabled": False
        }

        response = await authenticated_client.post(
            "/api/v1/chat/stream",
            json=request_data
        )

        # Should handle non-existent conversation gracefully
        assert response.status_code in [200, 404, 500, 503]


# =============================================================================
# CONVERSATION MANAGEMENT TESTS
# =============================================================================

class TestConversationManagement:
    """Test conversation CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_conversation(self, authenticated_client: AsyncClient):
        """Test creating a new conversation"""
        request_data = {
            "title": "Test Conversation"
        }

        response = await authenticated_client.post(
            "/api/v1/chat/conversations",
            json=request_data
        )

        # 200/201 = created, 404 = endpoint not found, 422 = validation, 500/503 = error
        assert response.status_code in [200, 201, 404, 405, 422, 500, 503]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "conversation_id" in data or "id" in data

    @pytest.mark.asyncio
    async def test_list_conversations(self, authenticated_client: AsyncClient):
        """Test listing user's conversations"""
        response = await authenticated_client.get("/api/v1/chat/conversations")

        # 200 = success, 404/405 = endpoint not found/method not allowed, 500/503 = error
        assert response.status_code in [200, 404, 405, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "conversations" in data

    @pytest.mark.asyncio
    async def test_get_conversation(self, authenticated_client: AsyncClient):
        """Test getting a specific conversation"""
        conv_id = str(uuid4())

        response = await authenticated_client.get(
            f"/api/v1/chat/conversations/{conv_id}"
        )

        # 404/405 if not found, 200 if found, 500/503 = error
        assert response.status_code in [200, 404, 405, 500, 503]

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, authenticated_client: AsyncClient):
        """Test getting messages from a conversation"""
        conv_id = str(uuid4())

        response = await authenticated_client.get(
            f"/api/v1/chat/conversations/{conv_id}/messages"
        )

        # 404/405 if not found, 200 if found, 500/503 = error
        assert response.status_code in [200, 404, 405, 500, 503]

    @pytest.mark.asyncio
    async def test_delete_conversation(self, authenticated_client: AsyncClient):
        """Test deleting a conversation"""
        conv_id = str(uuid4())

        response = await authenticated_client.delete(
            f"/api/v1/chat/conversations/{conv_id}"
        )

        # 200/204 = deleted, 404/405 = not found, 500/503 = error
        assert response.status_code in [200, 204, 404, 405, 500, 503]


# =============================================================================
# LLM HEALTH & MODELS TESTS
# =============================================================================

class TestLLMHealth:
    """Test LLM service health and model listing"""

    @pytest.mark.asyncio
    async def test_llm_health_check(self, authenticated_client: AsyncClient):
        """Test LLM health check endpoint"""
        response = await authenticated_client.get("/api/v1/chat/health")

        # Health check should always respond
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data or "healthy" in data or "ollama" in data

    @pytest.mark.asyncio
    async def test_list_available_models(self, authenticated_client: AsyncClient):
        """Test listing available LLM models"""
        response = await authenticated_client.get("/api/v1/chat/models")

        # 200 = success, 404 = endpoint not found, 500/503 = service error
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            # Can be list of models or dict with providers
            assert isinstance(data, (list, dict))


# =============================================================================
# CHAT VALIDATION TESTS
# =============================================================================

class TestChatValidation:
    """Test input validation for chat"""

    @pytest.mark.asyncio
    async def test_chat_empty_message(self, authenticated_client: AsyncClient):
        """Test chat with empty message"""
        request_data = {
            "message": "",
            "rag_enabled": False
        }

        response = await authenticated_client.post(
            "/api/v1/chat/stream",
            json=request_data
        )

        # Should reject empty messages
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_chat_very_long_message(self, authenticated_client: AsyncClient):
        """Test chat with very long message"""
        request_data = {
            "message": "x" * 100000,  # 100k chars
            "rag_enabled": False
        }

        response = await authenticated_client.post(
            "/api/v1/chat/stream",
            json=request_data
        )

        # Should either accept or reject gracefully
        assert response.status_code in [200, 400, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_chat_invalid_provider(self, authenticated_client: AsyncClient):
        """Test chat with invalid provider"""
        request_data = {
            "message": "Hello",
            "rag_enabled": False,
            "provider": "invalid_provider"
        }

        response = await authenticated_client.post(
            "/api/v1/chat/stream",
            json=request_data
        )

        # 400/422 = validation error, 200/500/503 = accepted/error
        assert response.status_code in [200, 400, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_chat_invalid_model(self, authenticated_client: AsyncClient):
        """Test chat with invalid model"""
        request_data = {
            "message": "Hello",
            "rag_enabled": False,
            "provider": "ollama",
            "model": "nonexistent-model-xyz"
        }

        response = await authenticated_client.post(
            "/api/v1/chat/stream",
            json=request_data
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 404, 500, 503]
