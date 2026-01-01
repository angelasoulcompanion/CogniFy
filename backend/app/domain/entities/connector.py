"""
Database Connector Entity
Domain model for external database connections
Created with love by Angela & David - 1 January 2026
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"


class SyncStatus(str, Enum):
    """Sync status"""
    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TableInfo:
    """Database table information"""
    table_name: str
    schema_name: str = "public"
    column_count: int = 0
    row_count: Optional[int] = None
    columns: List[Dict[str, Any]] = field(default_factory=list)
    primary_key: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "table_name": self.table_name,
            "schema_name": self.schema_name,
            "column_count": self.column_count,
            "row_count": self.row_count,
            "columns": self.columns,
            "primary_key": self.primary_key,
            "description": self.description,
        }


@dataclass
class SyncConfig:
    """Configuration for data sync"""
    tables: List[str] = field(default_factory=list)
    include_schema: bool = True
    include_data: bool = True
    max_rows_per_table: int = 1000
    chunk_size: int = 500  # words per chunk
    custom_queries: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tables": self.tables,
            "include_schema": self.include_schema,
            "include_data": self.include_data,
            "max_rows_per_table": self.max_rows_per_table,
            "chunk_size": self.chunk_size,
            "custom_queries": self.custom_queries,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SyncConfig":
        return cls(
            tables=data.get("tables", []),
            include_schema=data.get("include_schema", True),
            include_data=data.get("include_data", True),
            max_rows_per_table=data.get("max_rows_per_table", 1000),
            chunk_size=data.get("chunk_size", 500),
            custom_queries=data.get("custom_queries", {}),
        )


@dataclass
class DatabaseConnection:
    """Database connection entity"""

    name: str
    db_type: DatabaseType
    host: str
    port: int
    database_name: str
    username: str
    password_encrypted: str  # Encrypted password
    connection_id: UUID = field(default_factory=uuid4)
    created_by: Optional[UUID] = None
    sync_enabled: bool = False
    sync_config: Optional[SyncConfig] = None
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[SyncStatus] = None
    last_sync_error: Optional[str] = None
    total_chunks_synced: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate entity after initialization"""
        self._validate()

    def _validate(self):
        """Validate connection data"""
        if not self.name:
            raise ValueError("Connection name is required")
        if not self.host:
            raise ValueError("Host is required")
        if not self.database_name:
            raise ValueError("Database name is required")
        if not self.username:
            raise ValueError("Username is required")

    @property
    def default_port(self) -> int:
        """Get default port for database type"""
        ports = {
            DatabaseType.POSTGRESQL: 5432,
            DatabaseType.MYSQL: 3306,
            DatabaseType.SQLSERVER: 1433,
        }
        return ports.get(self.db_type, 5432)

    def get_connection_string(self, decrypted_password: str) -> str:
        """Get connection string for the database"""
        if self.db_type == DatabaseType.POSTGRESQL:
            return f"postgresql://{self.username}:{decrypted_password}@{self.host}:{self.port}/{self.database_name}"
        elif self.db_type == DatabaseType.MYSQL:
            return f"mysql+aiomysql://{self.username}:{decrypted_password}@{self.host}:{self.port}/{self.database_name}"
        elif self.db_type == DatabaseType.SQLSERVER:
            return f"mssql+aioodbc://{self.username}:{decrypted_password}@{self.host}:{self.port}/{self.database_name}?driver=ODBC+Driver+17+for+SQL+Server"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def start_sync(self) -> None:
        """Mark sync as started"""
        self.last_sync_status = SyncStatus.SYNCING
        self.last_sync_error = None

    def complete_sync(self, chunks_synced: int) -> None:
        """Mark sync as completed"""
        self.last_sync_status = SyncStatus.COMPLETED
        self.last_sync_at = datetime.now()
        self.total_chunks_synced = chunks_synced

    def fail_sync(self, error: str) -> None:
        """Mark sync as failed"""
        self.last_sync_status = SyncStatus.FAILED
        self.last_sync_error = error
        self.last_sync_at = datetime.now()

    def deactivate(self) -> None:
        """Deactivate connection"""
        self.is_active = False
        self.sync_enabled = False

    def to_dict(self, include_password: bool = False) -> dict:
        """Convert to dictionary"""
        result = {
            "connection_id": str(self.connection_id),
            "created_by": str(self.created_by) if self.created_by else None,
            "name": self.name,
            "db_type": self.db_type.value,
            "host": self.host,
            "port": self.port,
            "database_name": self.database_name,
            "username": self.username,
            "sync_enabled": self.sync_enabled,
            "sync_config": self.sync_config.to_dict() if self.sync_config else None,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_sync_status": self.last_sync_status.value if self.last_sync_status else None,
            "last_sync_error": self.last_sync_error,
            "total_chunks_synced": self.total_chunks_synced,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_password:
            result["password_encrypted"] = self.password_encrypted
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "DatabaseConnection":
        """Create entity from dictionary"""
        sync_config = None
        if data.get("sync_config"):
            sync_config = SyncConfig.from_dict(data["sync_config"])

        return cls(
            connection_id=UUID(data["connection_id"]) if isinstance(data.get("connection_id"), str) else data.get("connection_id", uuid4()),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            name=data["name"],
            db_type=DatabaseType(data["db_type"]) if isinstance(data.get("db_type"), str) else data.get("db_type"),
            host=data["host"],
            port=data["port"],
            database_name=data["database_name"],
            username=data["username"],
            password_encrypted=data.get("password_encrypted", ""),
            sync_enabled=data.get("sync_enabled", False),
            sync_config=sync_config,
            last_sync_at=data.get("last_sync_at"),
            last_sync_status=SyncStatus(data["last_sync_status"]) if data.get("last_sync_status") else None,
            last_sync_error=data.get("last_sync_error"),
            total_chunks_synced=data.get("total_chunks_synced", 0),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", datetime.now()),
            updated_at=data.get("updated_at", datetime.now()),
        )

    @classmethod
    def create(
        cls,
        name: str,
        db_type: str,
        host: str,
        port: int,
        database_name: str,
        username: str,
        password_encrypted: str,
        created_by: Optional[UUID] = None,
    ) -> "DatabaseConnection":
        """Factory method to create a new connection"""
        return cls(
            name=name,
            db_type=DatabaseType(db_type),
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password_encrypted=password_encrypted,
            created_by=created_by,
        )
