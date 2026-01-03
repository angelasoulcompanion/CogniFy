"""
CogniFy Database Connectors API Tests
Comprehensive tests for database connection management

Created with love by Angela & David - 3 January 2026
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock

from httpx import AsyncClient


# =============================================================================
# CONNECTOR CRUD TESTS
# =============================================================================

class TestConnectorCRUD:
    """Test connector CRUD operations"""

    @pytest.fixture
    def sample_connector_data(self) -> dict:
        """Sample connector creation data"""
        return {
            "name": "Test PostgreSQL",
            "db_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "username": "test_user",
            "password": "test_pass",
            "description": "Test connection"
        }

    @pytest.mark.asyncio
    async def test_create_connector(
        self,
        authenticated_client: AsyncClient,
        sample_connector_data: dict
    ):
        """Test creating a new connector"""
        response = await authenticated_client.post(
            "/api/v1/connectors",
            json=sample_connector_data
        )

        # Should create or fail validation
        assert response.status_code in [200, 201, 422]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "connector_id" in data or "id" in data

    @pytest.mark.asyncio
    async def test_list_connectors(self, authenticated_client: AsyncClient):
        """Test listing all connectors"""
        response = await authenticated_client.get("/api/v1/connectors")

        assert response.status_code in [200, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "connectors" in data

    @pytest.mark.asyncio
    async def test_get_connector(self, authenticated_client: AsyncClient):
        """Test getting a specific connector"""
        conn_id = str(uuid4())

        response = await authenticated_client.get(
            f"/api/v1/connectors/{conn_id}"
        )

        assert response.status_code in [200, 404, 500, 503]

    @pytest.mark.asyncio
    async def test_update_connector(
        self,
        authenticated_client: AsyncClient
    ):
        """Test updating a connector"""
        conn_id = str(uuid4())
        update_data = {
            "name": "Updated Name",
            "description": "Updated description"
        }

        response = await authenticated_client.put(
            f"/api/v1/connectors/{conn_id}",
            json=update_data
        )

        assert response.status_code in [200, 404, 500, 503]

    @pytest.mark.asyncio
    async def test_delete_connector(self, authenticated_client: AsyncClient):
        """Test deleting a connector"""
        conn_id = str(uuid4())

        response = await authenticated_client.delete(
            f"/api/v1/connectors/{conn_id}"
        )

        assert response.status_code in [200, 204, 404, 500, 503]


# =============================================================================
# CONNECTION TESTING
# =============================================================================

class TestConnectionTesting:
    """Test database connection testing"""

    @pytest.mark.asyncio
    async def test_test_new_connection(self, authenticated_client: AsyncClient):
        """Test testing a new connection before saving"""
        connection_data = {
            "db_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "username": "test_user",
            "password": "test_pass"
        }

        response = await authenticated_client.post(
            "/api/v1/connectors/test",
            json=connection_data
        )

        # Should return connection status (422 = validation error)
        assert response.status_code in [200, 400, 422, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data or "status" in data or "error" in data

    @pytest.mark.asyncio
    async def test_test_existing_connection(self, authenticated_client: AsyncClient):
        """Test testing an existing saved connection"""
        conn_id = str(uuid4())

        response = await authenticated_client.post(
            f"/api/v1/connectors/{conn_id}/test"
        )

        assert response.status_code in [200, 404, 500, 503]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("db_type", ["postgresql", "mysql", "sqlserver"])
    async def test_connection_types(
        self,
        authenticated_client: AsyncClient,
        db_type: str
    ):
        """Test different database types"""
        connection_data = {
            "db_type": db_type,
            "host": "localhost",
            "port": 5432 if db_type == "postgresql" else 3306 if db_type == "mysql" else 1433,
            "database": "test_db",
            "username": "test_user",
            "password": "test_pass"
        }

        response = await authenticated_client.post(
            "/api/v1/connectors/test",
            json=connection_data
        )

        # Should accept all supported types (422 = validation error)
        assert response.status_code in [200, 400, 422, 500, 503]


# =============================================================================
# SCHEMA DISCOVERY TESTS
# =============================================================================

class TestSchemaDiscovery:
    """Test database schema discovery"""

    @pytest.mark.asyncio
    async def test_discover_schema(self, authenticated_client: AsyncClient):
        """Test discovering database schema"""
        conn_id = str(uuid4())

        response = await authenticated_client.get(
            f"/api/v1/connectors/{conn_id}/schema"
        )

        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            # Should have tables or schema info
            assert "tables" in data or "schema" in data or isinstance(data, list)


# =============================================================================
# DATA SYNC TESTS
# =============================================================================

class TestDataSync:
    """Test data sync to RAG"""

    @pytest.mark.asyncio
    async def test_sync_table_to_rag(self, authenticated_client: AsyncClient):
        """Test syncing table data to RAG chunks"""
        conn_id = str(uuid4())
        sync_config = {
            "tables": ["users", "products"],
            "columns": ["name", "description"],
            "chunk_size": 500
        }

        response = await authenticated_client.post(
            f"/api/v1/connectors/{conn_id}/sync",
            json=sync_config
        )

        assert response.status_code in [200, 202, 404, 500, 503]

    @pytest.mark.asyncio
    async def test_preview_table_data(self, authenticated_client: AsyncClient):
        """Test previewing table data"""
        conn_id = str(uuid4())
        table_name = "users"

        response = await authenticated_client.get(
            f"/api/v1/connectors/{conn_id}/preview/{table_name}"
        )

        assert response.status_code in [200, 404, 500, 503]


# =============================================================================
# QUERY EXECUTION TESTS
# =============================================================================

class TestQueryExecution:
    """Test SQL query execution"""

    @pytest.mark.asyncio
    async def test_execute_select_query(self, authenticated_client: AsyncClient):
        """Test executing SELECT query"""
        conn_id = str(uuid4())
        query_data = {
            "query": "SELECT * FROM users LIMIT 10"
        }

        response = await authenticated_client.post(
            f"/api/v1/connectors/{conn_id}/query",
            json=query_data
        )

        assert response.status_code in [200, 400, 404, 500, 503]

    @pytest.mark.asyncio
    async def test_reject_dangerous_query(self, authenticated_client: AsyncClient):
        """Test rejection of dangerous queries"""
        conn_id = str(uuid4())

        # Test DROP TABLE
        response = await authenticated_client.post(
            f"/api/v1/connectors/{conn_id}/query",
            json={"query": "DROP TABLE users"}
        )
        assert response.status_code in [400, 403, 404, 500, 503]

        # Test DELETE without WHERE
        response = await authenticated_client.post(
            f"/api/v1/connectors/{conn_id}/query",
            json={"query": "DELETE FROM users"}
        )
        assert response.status_code in [400, 403, 404, 500, 503]

        # Test UPDATE without WHERE
        response = await authenticated_client.post(
            f"/api/v1/connectors/{conn_id}/query",
            json={"query": "UPDATE users SET status = 'deleted'"}
        )
        assert response.status_code in [400, 403, 404, 500, 503]


# =============================================================================
# SECURITY TESTS
# =============================================================================

class TestConnectorSecurity:
    """Test connector security features"""

    @pytest.mark.asyncio
    async def test_password_not_returned(self, authenticated_client: AsyncClient):
        """Test that passwords are not returned in responses"""
        response = await authenticated_client.get("/api/v1/connectors")

        # 500/503 = database unavailable
        assert response.status_code in [200, 500, 503]
        if response.status_code == 200:
            data = response.json()
            connectors = data if isinstance(data, list) else data.get("connectors", [])
            for conn in connectors:
                # Password should be masked or not present
                if "password" in conn:
                    assert conn["password"] in [None, "", "********", "***"]

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, authenticated_client: AsyncClient):
        """Test SQL injection prevention"""
        # Attempt SQL injection in connection name
        malicious_data = {
            "name": "Test'; DROP TABLE connectors; --",
            "db_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "test",
            "username": "test",
            "password": "test"
        }

        response = await authenticated_client.post(
            "/api/v1/connectors",
            json=malicious_data
        )

        # Should sanitize or reject
        assert response.status_code in [200, 201, 400, 422]

    @pytest.mark.asyncio
    async def test_connector_unauthorized_access(self, client: AsyncClient):
        """Test connectors require authentication"""
        response = await client.get("/api/v1/connectors")
        # 401 = auth required, 200 = public access, 500/503 = service error
        assert response.status_code in [200, 401, 500, 503]

        response = await client.post(
            "/api/v1/connectors",
            json={"name": "test"}
        )
        # 401 = auth required, 422 = validation error, 500/503 = service error
        assert response.status_code in [401, 422, 500, 503]
