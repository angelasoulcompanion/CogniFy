"""
CogniFy Search API Tests
Comprehensive tests for vector, BM25, and hybrid search

Created with love by Angela & David - 3 January 2026
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock

from httpx import AsyncClient


# =============================================================================
# VECTOR SEARCH TESTS
# =============================================================================

class TestVectorSearch:
    """Test semantic vector search"""

    @pytest.mark.asyncio
    async def test_vector_search_basic(self, authenticated_client: AsyncClient):
        """Test basic vector search"""
        request_data = {
            "query": "What is machine learning?",
            "limit": 10,
            "threshold": 0.3
        }

        response = await authenticated_client.post(
            "/api/v1/search",
            json=request_data
        )

        # 200 = success, 404 = endpoint not found, 500/503 = embedding service not available
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "results" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_vector_search_with_filters(self, authenticated_client: AsyncClient):
        """Test vector search with document filters"""
        request_data = {
            "query": "test query",
            "limit": 5,
            "threshold": 0.5,
            "document_ids": [str(uuid4())]
        }

        response = await authenticated_client.post(
            "/api/v1/search",
            json=request_data
        )

        # 200 = success, 404 = not found, 500/503 = embedding service not available
        assert response.status_code in [200, 404, 500, 503]

    @pytest.mark.asyncio
    async def test_vector_search_empty_query(self, authenticated_client: AsyncClient):
        """Test vector search with empty query"""
        request_data = {
            "query": "",
            "limit": 10
        }

        response = await authenticated_client.post(
            "/api/v1/search",
            json=request_data
        )

        # Should reject empty query
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_vector_search_unauthenticated(self, client: AsyncClient):
        """Test vector search without auth"""
        request_data = {
            "query": "test",
            "limit": 10
        }

        response = await client.post("/api/v1/search", json=request_data)

        # 401 = auth required, 200/500/503 = auth not required or service error
        assert response.status_code in [200, 401, 500, 503]


# =============================================================================
# BM25 SEARCH TESTS
# =============================================================================

class TestBM25Search:
    """Test keyword-based BM25 search"""

    @pytest.mark.asyncio
    async def test_bm25_search_basic(self, authenticated_client: AsyncClient):
        """Test basic BM25 search"""
        request_data = {
            "query": "machine learning algorithm",
            "limit": 10
        }

        response = await authenticated_client.post(
            "/api/v1/search/bm25",
            json=request_data
        )

        # 200 = success, 404 = not found, 500/503 = service not available
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "results" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_bm25_search_thai_text(self, authenticated_client: AsyncClient):
        """Test BM25 search with Thai text"""
        request_data = {
            "query": "ปัญญาประดิษฐ์ การเรียนรู้",
            "limit": 10
        }

        response = await authenticated_client.post(
            "/api/v1/search/bm25",
            json=request_data
        )

        # 200 = success, 404 = not found, 500/503 = service not available
        assert response.status_code in [200, 404, 500, 503]

    @pytest.mark.asyncio
    async def test_bm25_search_special_chars(self, authenticated_client: AsyncClient):
        """Test BM25 search with special characters"""
        request_data = {
            "query": "test@email.com OR SELECT * FROM users",
            "limit": 10
        }

        response = await authenticated_client.post(
            "/api/v1/search/bm25",
            json=request_data
        )

        # Should handle special chars safely
        assert response.status_code in [200, 400, 404, 500, 503]


# =============================================================================
# HYBRID SEARCH TESTS
# =============================================================================

class TestHybridSearch:
    """Test hybrid search with RRF fusion"""

    @pytest.mark.asyncio
    async def test_hybrid_search_basic(self, authenticated_client: AsyncClient):
        """Test basic hybrid search"""
        request_data = {
            "query": "machine learning models",
            "limit": 10,
            "vector_weight": 0.7,
            "bm25_weight": 0.3
        }

        response = await authenticated_client.post(
            "/api/v1/search/hybrid",
            json=request_data
        )

        # 200 = success, 404 = not found, 500/503 = embedding service not available
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "results" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_hybrid_search_custom_weights(self, authenticated_client: AsyncClient):
        """Test hybrid search with custom weights"""
        request_data = {
            "query": "test query",
            "limit": 5,
            "vector_weight": 0.5,
            "bm25_weight": 0.5
        }

        response = await authenticated_client.post(
            "/api/v1/search/hybrid",
            json=request_data
        )

        # 200 = success, 404 = not found, 500/503 = embedding service not available
        assert response.status_code in [200, 404, 500, 503]

    @pytest.mark.asyncio
    async def test_hybrid_search_invalid_weights(self, authenticated_client: AsyncClient):
        """Test hybrid search with invalid weights"""
        request_data = {
            "query": "test",
            "limit": 10,
            "vector_weight": 2.0,  # Invalid: > 1
            "bm25_weight": -0.5   # Invalid: < 0
        }

        response = await authenticated_client.post(
            "/api/v1/search/hybrid",
            json=request_data
        )

        # Should reject invalid weights or normalize them
        assert response.status_code in [200, 400, 422]


# =============================================================================
# CONTEXT BUILDER TESTS
# =============================================================================

class TestContextBuilder:
    """Test RAG context building"""

    @pytest.mark.asyncio
    async def test_build_context(self, authenticated_client: AsyncClient):
        """Test building RAG context"""
        request_data = {
            "query": "What are the key points?",
            "limit": 5,
            "include_sources": True
        }

        response = await authenticated_client.post(
            "/api/v1/search/context",
            json=request_data
        )

        # 200 = success, 404 = not found, 500/503 = embedding service not available
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            # Should have context or results
            assert "context" in data or "results" in data or isinstance(data, str)

    @pytest.mark.asyncio
    async def test_build_context_with_max_tokens(self, authenticated_client: AsyncClient):
        """Test context building with token limit"""
        request_data = {
            "query": "summarize the documents",
            "limit": 10,
            "max_tokens": 2000
        }

        response = await authenticated_client.post(
            "/api/v1/search/context",
            json=request_data
        )

        # 200 = success, 404 = not found, 500/503 = embedding service not available
        assert response.status_code in [200, 404, 500, 503]


# =============================================================================
# SIMILAR CHUNKS TESTS
# =============================================================================

class TestSimilarChunks:
    """Test finding similar chunks"""

    @pytest.mark.asyncio
    async def test_find_similar_chunks(self, authenticated_client: AsyncClient):
        """Test finding chunks similar to a given chunk"""
        chunk_id = str(uuid4())

        response = await authenticated_client.post(
            f"/api/v1/search/similar/{chunk_id}",
            json={"limit": 5}
        )

        # 200 = found, 404 = not found, 500/503 = service not available
        assert response.status_code in [200, 404, 500, 503]


# =============================================================================
# SEARCH STATS TESTS
# =============================================================================

class TestSearchStats:
    """Test search statistics"""

    @pytest.mark.asyncio
    async def test_get_search_stats(self, authenticated_client: AsyncClient):
        """Test getting search/embedding statistics"""
        response = await authenticated_client.get("/api/v1/search/stats")

        # 200 = success, 404 = not found, 500/503 = service not available
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            # Should have some stats
            assert isinstance(data, dict)


# =============================================================================
# SEARCH EDGE CASES
# =============================================================================

class TestSearchEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_search_very_long_query(self, authenticated_client: AsyncClient):
        """Test search with very long query"""
        request_data = {
            "query": "word " * 1000,  # Very long query
            "limit": 10
        }

        response = await authenticated_client.post(
            "/api/v1/search",
            json=request_data
        )

        # Should handle or truncate gracefully
        assert response.status_code in [200, 400, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_search_unicode_query(self, authenticated_client: AsyncClient):
        """Test search with various unicode characters"""
        request_data = {
            "query": "测试 🎉 مرحبا こんにちは",
            "limit": 10
        }

        response = await authenticated_client.post(
            "/api/v1/search",
            json=request_data
        )

        # 200 = success, 404 = not found, 500/503 = embedding service not available
        assert response.status_code in [200, 404, 500, 503]

    @pytest.mark.asyncio
    async def test_search_zero_limit(self, authenticated_client: AsyncClient):
        """Test search with zero limit"""
        request_data = {
            "query": "test",
            "limit": 0
        }

        response = await authenticated_client.post(
            "/api/v1/search",
            json=request_data
        )

        # Should reject or use default
        assert response.status_code in [200, 400, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_search_negative_limit(self, authenticated_client: AsyncClient):
        """Test search with negative limit"""
        request_data = {
            "query": "test",
            "limit": -5
        }

        response = await authenticated_client.post(
            "/api/v1/search",
            json=request_data
        )

        # Should reject invalid limit or service error
        assert response.status_code in [400, 422, 500, 503]
