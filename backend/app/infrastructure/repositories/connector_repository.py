"""
Connector Repository
Database operations for external database connections
Created with love by Angela & David - 1 January 2026
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import json

import asyncpg

from app.infrastructure.database import Database
from app.infrastructure.repositories.base_repository import BaseRepository
from app.domain.entities.connector import (
    DatabaseConnection,
    DatabaseType,
    SyncStatus,
    SyncConfig,
)


class ConnectorRepository(BaseRepository[DatabaseConnection]):
    """Repository for database connection operations"""

    def __init__(self):
        super().__init__(
            table_name="database_connections",
            primary_key_column="connection_id"
        )

    def _row_to_entity(self, row: asyncpg.Record) -> DatabaseConnection:
        """Convert database row to entity"""
        sync_config = None
        if row.get("sync_config"):
            config_data = row["sync_config"]
            if isinstance(config_data, str):
                config_data = json.loads(config_data)
            sync_config = SyncConfig.from_dict(config_data)

        return DatabaseConnection(
            connection_id=row["connection_id"],
            created_by=row.get("created_by"),
            name=row["name"],
            db_type=DatabaseType(row["db_type"]),
            host=row["host"],
            port=row["port"],
            database_name=row["database_name"],
            username=row["username"],
            password_encrypted=row["password_encrypted"],
            sync_enabled=row.get("sync_enabled", False),
            sync_config=sync_config,
            last_sync_at=row.get("last_sync_at"),
            last_sync_status=SyncStatus(row["last_sync_status"]) if row.get("last_sync_status") else None,
            last_sync_error=row.get("last_sync_error"),
            total_chunks_synced=row.get("total_chunks_synced", 0),
            is_active=row.get("is_active", True),
            created_at=row.get("created_at", datetime.now()),
            updated_at=row.get("updated_at", datetime.now()),
        )

    def _entity_to_dict(self, entity: DatabaseConnection) -> Dict[str, Any]:
        """Convert entity to dictionary for database"""
        return {
            "connection_id": entity.connection_id,
            "created_by": entity.created_by,
            "name": entity.name,
            "db_type": entity.db_type.value,
            "host": entity.host,
            "port": entity.port,
            "database_name": entity.database_name,
            "username": entity.username,
            "password_encrypted": entity.password_encrypted,
            "sync_enabled": entity.sync_enabled,
            "sync_config": json.dumps(entity.sync_config.to_dict()) if entity.sync_config else None,
            "last_sync_at": entity.last_sync_at,
            "last_sync_status": entity.last_sync_status.value if entity.last_sync_status else None,
            "last_sync_error": entity.last_sync_error,
            "total_chunks_synced": entity.total_chunks_synced,
            "is_active": entity.is_active,
        }

    async def create(self, connection: DatabaseConnection) -> DatabaseConnection:
        """Create a new database connection"""
        query = """
            INSERT INTO database_connections (
                connection_id, created_by, name, db_type, host, port,
                database_name, username, password_encrypted,
                sync_enabled, sync_config, is_active
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
        """
        row = await Database.fetchrow(
            query,
            connection.connection_id,
            connection.created_by,
            connection.name,
            connection.db_type.value,
            connection.host,
            connection.port,
            connection.database_name,
            connection.username,
            connection.password_encrypted,
            connection.sync_enabled,
            json.dumps(connection.sync_config.to_dict()) if connection.sync_config else None,
            connection.is_active,
        )
        return self._row_to_entity(row)

    async def update(self, connection: DatabaseConnection) -> DatabaseConnection:
        """Update an existing connection"""
        query = """
            UPDATE database_connections
            SET name = $2,
                db_type = $3,
                host = $4,
                port = $5,
                database_name = $6,
                username = $7,
                password_encrypted = $8,
                sync_enabled = $9,
                sync_config = $10,
                is_active = $11,
                updated_at = NOW()
            WHERE connection_id = $1
            RETURNING *
        """
        row = await Database.fetchrow(
            query,
            connection.connection_id,
            connection.name,
            connection.db_type.value,
            connection.host,
            connection.port,
            connection.database_name,
            connection.username,
            connection.password_encrypted,
            connection.sync_enabled,
            json.dumps(connection.sync_config.to_dict()) if connection.sync_config else None,
            connection.is_active,
        )
        if row is None:
            raise ValueError(f"Connection {connection.connection_id} not found")
        return self._row_to_entity(row)

    async def update_sync_status(
        self,
        connection_id: UUID,
        status: SyncStatus,
        error: Optional[str] = None,
        chunks_synced: Optional[int] = None
    ) -> None:
        """Update sync status for a connection"""
        if status == SyncStatus.COMPLETED:
            query = """
                UPDATE database_connections
                SET last_sync_status = $2,
                    last_sync_at = NOW(),
                    last_sync_error = NULL,
                    total_chunks_synced = COALESCE($3, total_chunks_synced),
                    updated_at = NOW()
                WHERE connection_id = $1
            """
            await Database.execute(query, connection_id, status.value, chunks_synced)
        elif status == SyncStatus.FAILED:
            query = """
                UPDATE database_connections
                SET last_sync_status = $2,
                    last_sync_at = NOW(),
                    last_sync_error = $3,
                    updated_at = NOW()
                WHERE connection_id = $1
            """
            await Database.execute(query, connection_id, status.value, error)
        else:
            query = """
                UPDATE database_connections
                SET last_sync_status = $2,
                    last_sync_error = NULL,
                    updated_at = NOW()
                WHERE connection_id = $1
            """
            await Database.execute(query, connection_id, status.value)

    async def get_active_connections(
        self,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DatabaseConnection]:
        """Get all active connections, optionally filtered by user"""
        if user_id:
            query = """
                SELECT * FROM database_connections
                WHERE is_active = true AND created_by = $1
                ORDER BY created_at DESC
                OFFSET $2 LIMIT $3
            """
            rows = await Database.fetch(query, user_id, skip, limit)
        else:
            query = """
                SELECT * FROM database_connections
                WHERE is_active = true
                ORDER BY created_at DESC
                OFFSET $1 LIMIT $2
            """
            rows = await Database.fetch(query, skip, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_by_name(self, name: str) -> Optional[DatabaseConnection]:
        """Get connection by name"""
        query = """
            SELECT * FROM database_connections
            WHERE name = $1 AND is_active = true
        """
        row = await Database.fetchrow(query, name)
        if row is None:
            return None
        return self._row_to_entity(row)

    async def get_sync_enabled(self) -> List[DatabaseConnection]:
        """Get all connections with sync enabled"""
        query = """
            SELECT * FROM database_connections
            WHERE is_active = true AND sync_enabled = true
            ORDER BY last_sync_at ASC NULLS FIRST
        """
        rows = await Database.fetch(query)
        return [self._row_to_entity(row) for row in rows]

    async def count_by_user(self, user_id: UUID) -> int:
        """Count connections for a user"""
        query = """
            SELECT COUNT(*) FROM database_connections
            WHERE created_by = $1 AND is_active = true
        """
        return await Database.fetchval(query, user_id)

    async def deactivate(self, connection_id: UUID) -> bool:
        """Soft delete (deactivate) a connection"""
        query = """
            UPDATE database_connections
            SET is_active = false,
                sync_enabled = false,
                updated_at = NOW()
            WHERE connection_id = $1
            RETURNING connection_id
        """
        result = await Database.fetchval(query, connection_id)
        return result is not None

    async def update_password(
        self,
        connection_id: UUID,
        encrypted_password: str
    ) -> None:
        """Update encrypted password for a connection"""
        query = """
            UPDATE database_connections
            SET password_encrypted = $2,
                updated_at = NOW()
            WHERE connection_id = $1
        """
        await Database.execute(query, connection_id, encrypted_password)
