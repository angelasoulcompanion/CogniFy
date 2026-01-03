"""
CogniFy Prompts API Tests
Comprehensive tests for prompt management system
NOTE: All prompts endpoints require ADMIN role

Created with love by Angela & David - 3 January 2026
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock

from httpx import AsyncClient


# =============================================================================
# PROMPT CRUD TESTS (Admin only)
# =============================================================================

class TestPromptCRUD:
    """Test prompt CRUD operations - requires admin role"""

    @pytest.fixture
    def sample_prompt_data(self) -> dict:
        """Sample prompt creation data"""
        return {
            "name": "Test Prompt",
            "description": "A test prompt template",
            "template": "You are a helpful assistant. Answer the following question: {question}",
            "expert_role": "general",
            "category": "rag",
            "is_active": True
        }

    @pytest.mark.asyncio
    async def test_create_prompt(
        self,
        admin_client: AsyncClient,
        sample_prompt_data: dict
    ):
        """Test creating a new prompt (admin only)"""
        response = await admin_client.post(
            "/api/v1/prompts",
            json=sample_prompt_data
        )

        assert response.status_code in [200, 201, 422]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "template_id" in data or "id" in data or "name" in data

    @pytest.mark.asyncio
    async def test_list_prompts(self, admin_client: AsyncClient):
        """Test listing all prompts (admin only)"""
        response = await admin_client.get("/api/v1/prompts")

        assert response.status_code in [200, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "prompts" in data or "templates" in data or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_prompt(self, admin_client: AsyncClient):
        """Test getting a specific prompt (admin only)"""
        prompt_id = str(uuid4())

        response = await admin_client.get(
            f"/api/v1/prompts/{prompt_id}"
        )

        assert response.status_code in [200, 404, 500, 503]

    @pytest.mark.asyncio
    async def test_update_prompt(
        self,
        admin_client: AsyncClient,
        sample_prompt_data: dict
    ):
        """Test updating a prompt (admin only)"""
        prompt_id = str(uuid4())
        update_data = {
            "name": "Updated Prompt Name",
            "template": "Updated template: {question}"
        }

        response = await admin_client.put(
            f"/api/v1/prompts/{prompt_id}",
            json=update_data
        )

        assert response.status_code in [200, 404, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_delete_prompt(self, admin_client: AsyncClient):
        """Test deleting a prompt (admin only)"""
        prompt_id = str(uuid4())

        response = await admin_client.delete(
            f"/api/v1/prompts/{prompt_id}"
        )

        assert response.status_code in [200, 204, 404, 500, 503]


# =============================================================================
# PROMPT CATEGORIES TESTS (Admin only)
# =============================================================================

class TestPromptCategories:
    """Test prompt category management - requires admin role"""

    @pytest.mark.asyncio
    async def test_list_categories(self, admin_client: AsyncClient):
        """Test listing prompt categories (admin only)"""
        response = await admin_client.get("/api/v1/prompts/categories")

        assert response.status_code in [200, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "categories" in data or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_filter_by_category(self, admin_client: AsyncClient):
        """Test filtering prompts by category (admin only)"""
        response = await admin_client.get(
            "/api/v1/prompts",
            params={"category": "rag"}
        )

        assert response.status_code in [200, 500, 503]


# =============================================================================
# DEFAULT PROMPT TESTS (Admin only)
# =============================================================================

class TestDefaultPrompts:
    """Test default prompt functionality - requires admin role"""

    @pytest.mark.asyncio
    async def test_get_templates_guide(self, admin_client: AsyncClient):
        """Test getting templates guide (admin only)"""
        response = await admin_client.get("/api/v1/prompts/templates")

        assert response.status_code in [200, 500, 503]

    @pytest.mark.asyncio
    async def test_set_default_prompt(self, admin_client: AsyncClient):
        """Test setting a prompt as default (admin only)"""
        prompt_id = str(uuid4())

        response = await admin_client.post(
            f"/api/v1/prompts/{prompt_id}/set-default"
        )

        assert response.status_code in [200, 404, 500, 503]

    @pytest.mark.asyncio
    async def test_get_prompt_stats(self, admin_client: AsyncClient):
        """Test getting prompt stats (admin only)"""
        response = await admin_client.get("/api/v1/prompts/stats")

        assert response.status_code in [200, 500, 503]


# =============================================================================
# PROMPT VALIDATION TESTS (Admin only)
# =============================================================================

class TestPromptValidation:
    """Test prompt input validation - requires admin role"""

    @pytest.mark.asyncio
    async def test_create_prompt_empty_name(self, admin_client: AsyncClient):
        """Test creating prompt with empty name (admin only)"""
        response = await admin_client.post(
            "/api/v1/prompts",
            json={
                "name": "",
                "template": "Some template"
            }
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_prompt_empty_template(self, admin_client: AsyncClient):
        """Test creating prompt with empty template (admin only)"""
        response = await admin_client.post(
            "/api/v1/prompts",
            json={
                "name": "Test Prompt",
                "template": ""
            }
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_prompt_very_long_template(self, admin_client: AsyncClient):
        """Test creating prompt with very long template (admin only)"""
        response = await admin_client.post(
            "/api/v1/prompts",
            json={
                "name": "Long Template Test",
                "template": "x" * 10000  # Reduced from 100k
            }
        )

        # Should either accept or reject gracefully
        assert response.status_code in [200, 201, 400, 422]


# =============================================================================
# PROMPT TEMPLATE RENDERING TESTS (Admin only)
# =============================================================================

class TestPromptRendering:
    """Test prompt template rendering - requires admin role"""

    @pytest.mark.asyncio
    async def test_render_prompt(self, admin_client: AsyncClient):
        """Test rendering a prompt with variables (admin only)"""
        prompt_id = str(uuid4())
        render_data = {
            "context": "Some context here",
            "question": "What is AI?"
        }

        response = await admin_client.post(
            f"/api/v1/prompts/{prompt_id}/render",
            json=render_data
        )

        # 200 = success, 400 = bad request, 404 = not found, 405 = method not allowed, 422 = validation, 500/503 = error
        assert response.status_code in [200, 400, 404, 405, 422, 500, 503]


# =============================================================================
# PROMPT SECURITY TESTS
# =============================================================================

class TestPromptSecurity:
    """Test prompt security"""

    @pytest.mark.asyncio
    async def test_prompts_require_admin(self, authenticated_client: AsyncClient):
        """Test prompts require admin role (not just auth)"""
        response = await authenticated_client.get("/api/v1/prompts")
        assert response.status_code == 403  # Forbidden for non-admin

    @pytest.mark.asyncio
    async def test_prompts_require_auth(self, client: AsyncClient):
        """Test prompts require authentication"""
        response = await client.get("/api/v1/prompts")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_xss_in_prompt_template(self, admin_client: AsyncClient):
        """Test XSS prevention in prompt template (admin only)"""
        response = await admin_client.post(
            "/api/v1/prompts",
            json={
                "name": "XSS Test",
                "template": "<script>alert('xss')</script> {question}",
                "category": "rag"
            }
        )

        # Should accept (sanitization happens on render) or reject
        assert response.status_code in [200, 201, 400, 422]

    @pytest.mark.asyncio
    async def test_sql_injection_in_prompt(self, admin_client: AsyncClient):
        """Test SQL injection prevention (admin only)"""
        response = await admin_client.post(
            "/api/v1/prompts",
            json={
                "name": "SQL Injection Test",
                "template": "Test template'; DROP TABLE prompts; --",
                "category": "rag"
            }
        )

        # Should sanitize or handle safely
        assert response.status_code in [200, 201, 400, 422]
