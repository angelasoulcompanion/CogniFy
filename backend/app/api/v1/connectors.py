"""
Database Connectors API
Endpoints for managing external database connections
Created with love by Angela & David - 1 January 2026
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user, TokenPayload
from app.services.connector_service import get_connector_service
from app.domain.entities.connector import DatabaseType, SyncStatus


router = APIRouter(prefix="/connectors", tags=["connectors"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ConnectionCreate(BaseModel):
    """Create connection request"""
    name: str = Field(..., min_length=1, max_length=255)
    db_type: str = Field(..., description="postgresql, mysql, or sqlserver")
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., gt=0, lt=65536)
    database_name: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class ConnectionUpdate(BaseModel):
    """Update connection request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, gt=0, lt=65536)
    database_name: Optional[str] = Field(None, min_length=1, max_length=255)
    username: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = None
    sync_enabled: Optional[bool] = None


class ConnectionTest(BaseModel):
    """Test connection request"""
    db_type: str
    host: str
    port: int
    database_name: str
    username: str
    password: str


class SyncRequest(BaseModel):
    """Sync request"""
    tables: Optional[List[str]] = None
    max_rows: int = Field(default=1000, ge=1, le=10000)
    chunk_size: int = Field(default=500, ge=100, le=2000)


class QueryRequest(BaseModel):
    """Query request"""
    query: str = Field(..., min_length=1)


class ConnectionResponse(BaseModel):
    """Connection response"""
    connection_id: str
    name: str
    db_type: str
    host: str
    port: int
    database_name: str
    username: str
    sync_enabled: bool
    last_sync_at: Optional[str] = None
    last_sync_status: Optional[str] = None
    last_sync_error: Optional[str] = None
    total_chunks_synced: int
    is_active: bool
    created_at: str
    updated_at: str


class TableInfoResponse(BaseModel):
    """Table info response"""
    table_name: str
    schema_name: str
    column_count: int
    row_count: Optional[int] = None
    columns: List[dict]
    primary_key: Optional[str] = None
    description: Optional[str] = None


class TestConnectionResponse(BaseModel):
    """Test connection response"""
    success: bool
    error: Optional[str] = None


class SyncResponse(BaseModel):
    """Sync response"""
    success: bool
    chunks_created: int
    error: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    request: ConnectionCreate,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Create a new database connection"""
    try:
        # Validate db_type
        try:
            DatabaseType(request.db_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid database type. Must be one of: postgresql, mysql, sqlserver"
            )

        service = await get_connector_service()
        connection = await service.create_connection(
            name=request.name,
            db_type=request.db_type,
            host=request.host,
            port=request.port,
            database_name=request.database_name,
            username=request.username,
            password=request.password,
            created_by=UUID(current_user.sub),
        )

        return _connection_to_response(connection)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=List[ConnectionResponse])
async def list_connections(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenPayload = Depends(get_current_user),
):
    """List all database connections"""
    service = await get_connector_service()

    # Admin sees all, others see only their own
    user_id = None if current_user.role == "admin" else UUID(current_user.sub)
    connections = await service.list_connections(user_id=user_id, skip=skip, limit=limit)

    return [_connection_to_response(c) for c in connections]


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get a specific database connection"""
    service = await get_connector_service()
    connection = await service.get_connection(connection_id)

    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    # Check ownership (admin can see all)
    if current_user.role != "admin" and str(connection.created_by) != current_user.sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return _connection_to_response(connection)


@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: UUID,
    request: ConnectionUpdate,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Update a database connection"""
    service = await get_connector_service()
    connection = await service.get_connection(connection_id)

    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    # Check ownership
    if current_user.role != "admin" and str(connection.created_by) != current_user.sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    updated = await service.update_connection(
        connection_id=connection_id,
        name=request.name,
        host=request.host,
        port=request.port,
        database_name=request.database_name,
        username=request.username,
        password=request.password,
        sync_enabled=request.sync_enabled,
    )

    return _connection_to_response(updated)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Delete (deactivate) a database connection"""
    service = await get_connector_service()
    connection = await service.get_connection(connection_id)

    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    # Check ownership
    if current_user.role != "admin" and str(connection.created_by) != current_user.sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    await service.delete_connection(connection_id)


@router.post("/test", response_model=TestConnectionResponse)
async def test_new_connection(
    request: ConnectionTest,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Test a new connection without saving"""
    try:
        service = await get_connector_service()
        success, error = await service.test_new_connection(
            db_type=request.db_type,
            host=request.host,
            port=request.port,
            database_name=request.database_name,
            username=request.username,
            password=request.password,
        )
        return TestConnectionResponse(success=success, error=error)
    except Exception as e:
        return TestConnectionResponse(success=False, error=str(e))


@router.post("/{connection_id}/test", response_model=TestConnectionResponse)
async def test_existing_connection(
    connection_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Test an existing connection"""
    service = await get_connector_service()
    connection = await service.get_connection(connection_id)

    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    success, error = await service.test_connection(connection_id)
    return TestConnectionResponse(success=success, error=error)


@router.get("/{connection_id}/schema", response_model=List[TableInfoResponse])
async def discover_schema(
    connection_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Discover database schema (tables and columns)"""
    service = await get_connector_service()
    connection = await service.get_connection(connection_id)

    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    # Check ownership
    if current_user.role != "admin" and str(connection.created_by) != current_user.sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    try:
        tables = await service.discover_schema(connection_id)
        return [TableInfoResponse(**t.to_dict()) for t in tables]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{connection_id}/sync", response_model=SyncResponse)
async def sync_connection(
    connection_id: UUID,
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Sync database data to document chunks for RAG.
    Runs in background for large datasets.
    """
    service = await get_connector_service()
    connection = await service.get_connection(connection_id)

    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    # Check ownership
    if current_user.role != "admin" and str(connection.created_by) != current_user.sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # Run sync
    chunks_created, error = await service.sync_to_chunks(
        connection_id=connection_id,
        tables=request.tables,
        max_rows=request.max_rows,
        chunk_size=request.chunk_size,
    )

    return SyncResponse(
        success=error is None,
        chunks_created=chunks_created,
        error=error,
    )


@router.get("/{connection_id}/preview/{table_name}")
async def preview_table_data(
    connection_id: UUID,
    table_name: str,
    limit: int = 10,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Preview data from a table"""
    service = await get_connector_service()
    connection = await service.get_connection(connection_id)

    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    # Check ownership
    if current_user.role != "admin" and str(connection.created_by) != current_user.sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    try:
        data = await service.preview_data(connection_id, table_name, limit=min(limit, 100))
        return {"table_name": table_name, "data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{connection_id}/query")
async def execute_query(
    connection_id: UUID,
    request: QueryRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Execute a custom SELECT query"""
    service = await get_connector_service()
    connection = await service.get_connection(connection_id)

    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    # Check ownership
    if current_user.role != "admin" and str(connection.created_by) != current_user.sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    try:
        data = await service.execute_query(connection_id, request.query)
        return {"query": request.query, "data": data, "count": len(data)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# HELPERS
# =============================================================================

def _connection_to_response(connection) -> ConnectionResponse:
    """Convert connection entity to response model"""
    return ConnectionResponse(
        connection_id=str(connection.connection_id),
        name=connection.name,
        db_type=connection.db_type.value,
        host=connection.host,
        port=connection.port,
        database_name=connection.database_name,
        username=connection.username,
        sync_enabled=connection.sync_enabled,
        last_sync_at=connection.last_sync_at.isoformat() if connection.last_sync_at else None,
        last_sync_status=connection.last_sync_status.value if connection.last_sync_status else None,
        last_sync_error=connection.last_sync_error,
        total_chunks_synced=connection.total_chunks_synced,
        is_active=connection.is_active,
        created_at=connection.created_at.isoformat(),
        updated_at=connection.updated_at.isoformat(),
    )
