"""
Base Repository Pattern
Generic CRUD operations for all repositories
Pattern from AngelaAI
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Any, Dict
from uuid import UUID
import asyncpg

from app.infrastructure.database import Database


T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository with generic CRUD operations.
    All concrete repositories should extend this class.
    """

    def __init__(self, table_name: str, primary_key_column: str = "id"):
        self.table_name = table_name
        self.primary_key_column = primary_key_column

    @abstractmethod
    def _row_to_entity(self, row: asyncpg.Record) -> T:
        """Convert database row to domain entity"""
        pass

    @abstractmethod
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert domain entity to dictionary for database"""
        pass

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID"""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {self.primary_key_column} = $1
        """
        row = await Database.fetchrow(query, id)
        if row is None:
            return None
        return self._row_to_entity(row)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[T]:
        """Get all entities with pagination"""
        order_direction = "DESC" if order_desc else "ASC"
        query = f"""
            SELECT * FROM {self.table_name}
            ORDER BY {order_by} {order_direction}
            OFFSET $1 LIMIT $2
        """
        rows = await Database.fetch(query, skip, limit)
        return [self._row_to_entity(row) for row in rows]

    async def count(self) -> int:
        """Count all entities"""
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        return await Database.fetchval(query)

    async def exists(self, id: UUID) -> bool:
        """Check if entity exists"""
        query = f"""
            SELECT EXISTS(
                SELECT 1 FROM {self.table_name}
                WHERE {self.primary_key_column} = $1
            )
        """
        return await Database.fetchval(query, id)

    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID"""
        query = f"""
            DELETE FROM {self.table_name}
            WHERE {self.primary_key_column} = $1
            RETURNING {self.primary_key_column}
        """
        result = await Database.fetchval(query, id)
        return result is not None

    async def _execute_query(self, query: str, *args) -> str:
        """Execute a query without returning results"""
        return await Database.execute(query, *args)

    async def _fetch_all(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch all rows from a query"""
        return await Database.fetch(query, *args)

    async def _fetch_one(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch one row from a query"""
        return await Database.fetchrow(query, *args)

    async def _fetch_val(self, query: str, *args) -> Any:
        """Fetch single value from a query"""
        return await Database.fetchval(query, *args)
