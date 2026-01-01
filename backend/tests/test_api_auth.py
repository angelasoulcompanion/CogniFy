"""
CogniFy Auth API Tests
Created with love by Angela & David - 1 January 2026
"""

import pytest
from httpx import AsyncClient


class TestAuthAPI:
    """Test authentication API endpoints"""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login"""
        # Note: This test requires a user in the database
        # Skip if running without database
        pytest.skip("Requires database setup")

        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin@cognify.local",
                "password": "admin123",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "tokens" in data
        assert "user" in data
        assert data["tokens"]["access_token"] is not None

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "wrong@email.com",
                "password": "wrongpassword",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 401

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Test /me endpoint without authentication"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, authenticated_client: AsyncClient):
        """Test /me endpoint with authentication"""
        # Skip if running without database
        pytest.skip("Requires database setup")

        response = await authenticated_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "role" in data


class TestHealthAPI:
    """Test health check endpoints"""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_root_health(self, client: AsyncClient):
        """Test root health endpoint"""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_api_health(self, client: AsyncClient):
        """Test API health endpoint"""
        # Skip if running without database
        pytest.skip("Requires database setup")

        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
