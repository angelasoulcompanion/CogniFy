"""
Connector Service
Business logic for external database connections
Supports PostgreSQL, MySQL, and SQL Server
Created with love by Angela & David - 1 January 2026
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime
from abc import ABC, abstractmethod

from cryptography.fernet import Fernet
import asyncpg

from app.core.config import settings
from app.domain.entities.connector import (
    DatabaseConnection,
    DatabaseType,
    SyncStatus,
    SyncConfig,
    TableInfo,
)
from app.infrastructure.repositories.connector_repository import ConnectorRepository
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


# Encryption key for passwords (should be in settings)
ENCRYPTION_KEY = getattr(settings, 'ENCRYPTION_KEY', None)
if ENCRYPTION_KEY is None:
    # Generate a default key (in production, should be from environment)
    ENCRYPTION_KEY = Fernet.generate_key()
else:
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY

fernet = Fernet(ENCRYPTION_KEY)


def encrypt_password(password: str) -> str:
    """Encrypt a password for storage"""
    return fernet.encrypt(password.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    """Decrypt a stored password"""
    return fernet.decrypt(encrypted.encode()).decode()


class DatabaseConnector(ABC):
    """Abstract base class for database connectors"""

    def __init__(self, connection: DatabaseConnection, password: str):
        self.connection = connection
        self.password = password
        self.conn = None

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the database"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the database connection"""
        pass

    @abstractmethod
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test the connection, return (success, error_message)"""
        pass

    @abstractmethod
    async def get_tables(self, schema: str = None) -> List[TableInfo]:
        """Get list of tables in the database"""
        pass

    @abstractmethod
    async def get_table_data(
        self,
        table_name: str,
        schema: str = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get data from a table"""
        pass

    @abstractmethod
    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a custom query"""
        pass


class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL database connector"""

    async def connect(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.conn = await asyncpg.connect(
                host=self.connection.host,
                port=self.connection.port,
                database=self.connection.database_name,
                user=self.connection.username,
                password=self.password,
                timeout=10,
            )
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL"""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test PostgreSQL connection"""
        try:
            conn = await asyncpg.connect(
                host=self.connection.host,
                port=self.connection.port,
                database=self.connection.database_name,
                user=self.connection.username,
                password=self.password,
                timeout=10,
            )
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            return True, None
        except Exception as e:
            return False, str(e)

    async def get_tables(self, schema: str = "public") -> List[TableInfo]:
        """Get PostgreSQL tables"""
        if not self.conn:
            await self.connect()

        query = """
            SELECT
                t.table_name,
                t.table_schema,
                (SELECT COUNT(*) FROM information_schema.columns c
                 WHERE c.table_name = t.table_name AND c.table_schema = t.table_schema) as column_count,
                obj_description(pgc.oid) as description
            FROM information_schema.tables t
            LEFT JOIN pg_class pgc ON pgc.relname = t.table_name
            WHERE t.table_schema = $1
            AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name
        """
        rows = await self.conn.fetch(query, schema)

        tables = []
        for row in rows:
            # Get columns
            col_query = """
                SELECT column_name, data_type, is_nullable,
                       column_default, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = $1 AND table_schema = $2
                ORDER BY ordinal_position
            """
            cols = await self.conn.fetch(col_query, row['table_name'], schema)

            # Get primary key
            pk_query = """
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = $1::regclass AND i.indisprimary
            """
            try:
                pk_rows = await self.conn.fetch(pk_query, f"{schema}.{row['table_name']}")
                primary_key = pk_rows[0]['attname'] if pk_rows else None
            except:
                primary_key = None

            # Get row count (approximate)
            try:
                count_query = f"SELECT COUNT(*) FROM {schema}.{row['table_name']}"
                row_count = await self.conn.fetchval(count_query)
            except:
                row_count = None

            tables.append(TableInfo(
                table_name=row['table_name'],
                schema_name=schema,
                column_count=row['column_count'],
                row_count=row_count,
                columns=[dict(c) for c in cols],
                primary_key=primary_key,
                description=row['description'],
            ))

        return tables

    async def get_table_data(
        self,
        table_name: str,
        schema: str = "public",
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get data from PostgreSQL table"""
        if not self.conn:
            await self.connect()

        query = f'SELECT * FROM "{schema}"."{table_name}" LIMIT $1'
        rows = await self.conn.fetch(query, limit)
        return [dict(row) for row in rows]

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute custom query on PostgreSQL"""
        if not self.conn:
            await self.connect()

        rows = await self.conn.fetch(query)
        return [dict(row) for row in rows]


class MySQLConnector(DatabaseConnector):
    """MySQL database connector"""

    async def connect(self) -> bool:
        """Connect to MySQL database"""
        try:
            import aiomysql
            self.conn = await aiomysql.connect(
                host=self.connection.host,
                port=self.connection.port,
                db=self.connection.database_name,
                user=self.connection.username,
                password=self.password,
                connect_timeout=10,
            )
            return True
        except ImportError:
            logger.error("aiomysql not installed. Install with: pip install aiomysql")
            return False
        except Exception as e:
            logger.error(f"MySQL connection error: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from MySQL"""
        if self.conn:
            self.conn.close()
            self.conn = None

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test MySQL connection"""
        try:
            import aiomysql
            conn = await aiomysql.connect(
                host=self.connection.host,
                port=self.connection.port,
                db=self.connection.database_name,
                user=self.connection.username,
                password=self.password,
                connect_timeout=10,
            )
            async with conn.cursor() as cur:
                await cur.execute("SELECT VERSION()")
                await cur.fetchone()
            conn.close()
            return True, None
        except ImportError:
            return False, "aiomysql not installed"
        except Exception as e:
            return False, str(e)

    async def get_tables(self, schema: str = None) -> List[TableInfo]:
        """Get MySQL tables"""
        if not self.conn:
            await self.connect()

        schema = schema or self.connection.database_name

        async with self.conn.cursor() as cur:
            await cur.execute("""
                SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
            """, (schema,))
            rows = await cur.fetchall()

        tables = []
        for row in rows:
            table_name, row_count, description = row

            # Get columns
            async with self.conn.cursor() as cur:
                await cur.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE,
                           COLUMN_DEFAULT, CHARACTER_MAXIMUM_LENGTH, COLUMN_KEY
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (schema, table_name))
                cols = await cur.fetchall()

            columns = []
            primary_key = None
            for col in cols:
                columns.append({
                    'column_name': col[0],
                    'data_type': col[1],
                    'is_nullable': col[2],
                    'column_default': col[3],
                    'character_maximum_length': col[4],
                })
                if col[5] == 'PRI':
                    primary_key = col[0]

            tables.append(TableInfo(
                table_name=table_name,
                schema_name=schema,
                column_count=len(columns),
                row_count=row_count,
                columns=columns,
                primary_key=primary_key,
                description=description,
            ))

        return tables

    async def get_table_data(
        self,
        table_name: str,
        schema: str = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get data from MySQL table"""
        if not self.conn:
            await self.connect()

        async with self.conn.cursor() as cur:
            await cur.execute(f"SELECT * FROM `{table_name}` LIMIT %s", (limit,))
            columns = [desc[0] for desc in cur.description]
            rows = await cur.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute custom query on MySQL"""
        if not self.conn:
            await self.connect()

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = await cur.fetchall()

        return [dict(zip(columns, row)) for row in rows]


class SQLServerConnector(DatabaseConnector):
    """SQL Server database connector"""

    async def connect(self) -> bool:
        """Connect to SQL Server database"""
        try:
            import aioodbc
            dsn = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.connection.host},{self.connection.port};"
                f"DATABASE={self.connection.database_name};"
                f"UID={self.connection.username};"
                f"PWD={self.password}"
            )
            self.conn = await aioodbc.connect(dsn=dsn, timeout=10)
            return True
        except ImportError:
            logger.error("aioodbc not installed. Install with: pip install aioodbc")
            return False
        except Exception as e:
            logger.error(f"SQL Server connection error: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from SQL Server"""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test SQL Server connection"""
        try:
            import aioodbc
            dsn = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.connection.host},{self.connection.port};"
                f"DATABASE={self.connection.database_name};"
                f"UID={self.connection.username};"
                f"PWD={self.password}"
            )
            conn = await aioodbc.connect(dsn=dsn, timeout=10)
            async with conn.cursor() as cur:
                await cur.execute("SELECT @@VERSION")
                await cur.fetchone()
            await conn.close()
            return True, None
        except ImportError:
            return False, "aioodbc not installed"
        except Exception as e:
            return False, str(e)

    async def get_tables(self, schema: str = "dbo") -> List[TableInfo]:
        """Get SQL Server tables"""
        if not self.conn:
            await self.connect()

        async with self.conn.cursor() as cur:
            await cur.execute("""
                SELECT t.TABLE_NAME, t.TABLE_SCHEMA,
                       (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS c
                        WHERE c.TABLE_NAME = t.TABLE_NAME AND c.TABLE_SCHEMA = t.TABLE_SCHEMA) as column_count
                FROM INFORMATION_SCHEMA.TABLES t
                WHERE t.TABLE_SCHEMA = ? AND t.TABLE_TYPE = 'BASE TABLE'
                ORDER BY t.TABLE_NAME
            """, schema)
            rows = await cur.fetchall()

        tables = []
        for row in rows:
            table_name, table_schema, column_count = row

            # Get columns
            async with self.conn.cursor() as cur:
                await cur.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE,
                           COLUMN_DEFAULT, CHARACTER_MAXIMUM_LENGTH
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = ? AND TABLE_SCHEMA = ?
                    ORDER BY ORDINAL_POSITION
                """, table_name, schema)
                cols = await cur.fetchall()

            columns = [{
                'column_name': col[0],
                'data_type': col[1],
                'is_nullable': col[2],
                'column_default': col[3],
                'character_maximum_length': col[4],
            } for col in cols]

            # Get primary key
            async with self.conn.cursor() as cur:
                await cur.execute("""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_NAME = ? AND TABLE_SCHEMA = ?
                    AND CONSTRAINT_NAME LIKE 'PK_%'
                """, table_name, schema)
                pk_row = await cur.fetchone()
                primary_key = pk_row[0] if pk_row else None

            # Get row count
            try:
                async with self.conn.cursor() as cur:
                    await cur.execute(f"SELECT COUNT(*) FROM [{schema}].[{table_name}]")
                    count_row = await cur.fetchone()
                    row_count = count_row[0] if count_row else None
            except:
                row_count = None

            tables.append(TableInfo(
                table_name=table_name,
                schema_name=table_schema,
                column_count=column_count,
                row_count=row_count,
                columns=columns,
                primary_key=primary_key,
            ))

        return tables

    async def get_table_data(
        self,
        table_name: str,
        schema: str = "dbo",
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get data from SQL Server table"""
        if not self.conn:
            await self.connect()

        async with self.conn.cursor() as cur:
            await cur.execute(f"SELECT TOP {limit} * FROM [{schema}].[{table_name}]")
            columns = [desc[0] for desc in cur.description]
            rows = await cur.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute custom query on SQL Server"""
        if not self.conn:
            await self.connect()

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = await cur.fetchall()

        return [dict(zip(columns, row)) for row in rows]


def get_connector(connection: DatabaseConnection, password: str) -> DatabaseConnector:
    """Factory to get appropriate connector for database type"""
    connectors = {
        DatabaseType.POSTGRESQL: PostgreSQLConnector,
        DatabaseType.MYSQL: MySQLConnector,
        DatabaseType.SQLSERVER: SQLServerConnector,
    }
    connector_class = connectors.get(connection.db_type)
    if not connector_class:
        raise ValueError(f"Unsupported database type: {connection.db_type}")
    return connector_class(connection, password)


class ConnectorService:
    """Service for managing database connections and sync"""

    def __init__(self):
        self.repository = ConnectorRepository()

    async def create_connection(
        self,
        name: str,
        db_type: str,
        host: str,
        port: int,
        database_name: str,
        username: str,
        password: str,
        created_by: Optional[UUID] = None,
    ) -> DatabaseConnection:
        """Create a new database connection"""
        # Encrypt password
        encrypted_password = encrypt_password(password)

        # Create entity
        connection = DatabaseConnection.create(
            name=name,
            db_type=db_type,
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password_encrypted=encrypted_password,
            created_by=created_by,
        )

        # Save to database
        return await self.repository.create(connection)

    async def get_connection(self, connection_id: UUID) -> Optional[DatabaseConnection]:
        """Get a connection by ID"""
        return await self.repository.get_by_id(connection_id)

    async def list_connections(
        self,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DatabaseConnection]:
        """List all active connections"""
        return await self.repository.get_active_connections(user_id, skip, limit)

    async def update_connection(
        self,
        connection_id: UUID,
        name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        sync_enabled: Optional[bool] = None,
        sync_config: Optional[Dict] = None,
    ) -> Optional[DatabaseConnection]:
        """Update a connection"""
        connection = await self.repository.get_by_id(connection_id)
        if not connection:
            return None

        if name:
            connection.name = name
        if host:
            connection.host = host
        if port:
            connection.port = port
        if database_name:
            connection.database_name = database_name
        if username:
            connection.username = username
        if password:
            connection.password_encrypted = encrypt_password(password)
        if sync_enabled is not None:
            connection.sync_enabled = sync_enabled
        if sync_config:
            connection.sync_config = SyncConfig.from_dict(sync_config)

        return await self.repository.update(connection)

    async def delete_connection(self, connection_id: UUID) -> bool:
        """Deactivate a connection"""
        return await self.repository.deactivate(connection_id)

    async def test_connection(self, connection_id: UUID) -> Tuple[bool, Optional[str]]:
        """Test a connection"""
        connection = await self.repository.get_by_id(connection_id)
        if not connection:
            return False, "Connection not found"

        try:
            password = decrypt_password(connection.password_encrypted)
            connector = get_connector(connection, password)
            success, error = await connector.test_connection()
            await connector.disconnect()
            return success, error
        except Exception as e:
            return False, str(e)

    async def test_new_connection(
        self,
        db_type: str,
        host: str,
        port: int,
        database_name: str,
        username: str,
        password: str,
    ) -> Tuple[bool, Optional[str]]:
        """Test a new connection before saving"""
        try:
            connection = DatabaseConnection(
                name="test",
                db_type=DatabaseType(db_type),
                host=host,
                port=port,
                database_name=database_name,
                username=username,
                password_encrypted="",
            )
            connector = get_connector(connection, password)
            success, error = await connector.test_connection()
            await connector.disconnect()
            return success, error
        except Exception as e:
            return False, str(e)

    async def discover_schema(self, connection_id: UUID) -> List[TableInfo]:
        """Discover database schema (tables and columns)"""
        connection = await self.repository.get_by_id(connection_id)
        if not connection:
            raise ValueError("Connection not found")

        password = decrypt_password(connection.password_encrypted)
        connector = get_connector(connection, password)

        try:
            if await connector.connect():
                tables = await connector.get_tables()
                await connector.disconnect()
                return tables
            else:
                raise ValueError("Failed to connect to database")
        finally:
            await connector.disconnect()

    async def sync_to_chunks(
        self,
        connection_id: UUID,
        tables: Optional[List[str]] = None,
        max_rows: int = 1000,
        chunk_size: int = 500,
    ) -> Tuple[int, Optional[str]]:
        """
        Sync database data to document chunks for RAG.
        Returns (chunks_created, error_message)
        """
        from app.infrastructure.repositories.document_repository import (
            DocumentRepository,
            DocumentChunkRepository,
        )
        from app.domain.entities.document import Document, DocumentChunk, FileType
        from uuid import uuid4

        connection = await self.repository.get_by_id(connection_id)
        if not connection:
            return 0, "Connection not found"

        # Update status
        await self.repository.update_sync_status(connection_id, SyncStatus.SYNCING)

        try:
            password = decrypt_password(connection.password_encrypted)
            connector = get_connector(connection, password)

            if not await connector.connect():
                await self.repository.update_sync_status(
                    connection_id, SyncStatus.FAILED, "Failed to connect"
                )
                return 0, "Failed to connect to database"

            # Get tables to sync
            all_tables = await connector.get_tables()
            if tables:
                all_tables = [t for t in all_tables if t.table_name in tables]

            embedding_service = await get_embedding_service()
            doc_repo = DocumentRepository()
            chunk_repo = DocumentChunkRepository()
            total_chunks = 0

            # Create a virtual document for this sync
            doc = Document(
                document_id=uuid4(),
                filename=f"connector_{connection_id}.db",
                original_filename=f"{connection.name} - Database Sync",
                file_type=FileType.TXT,
                title=f"Database: {connection.name}",
                description=f"Synced from {connection.db_type.value} database: {connection.database_name}",
                tags=["database", "connector", connection.db_type.value],
            )
            doc = await doc_repo.create(doc)

            for table in all_tables:
                # Get table data
                data = await connector.get_table_data(table.table_name, limit=max_rows)

                if not data:
                    continue

                # Convert rows to text chunks
                chunks_text = []
                current_chunk = f"# Table: {table.table_name}\n"
                current_chunk += f"Database: {connection.name}\n"
                current_chunk += f"Schema: {table.schema_name}\n"
                current_chunk += f"Columns: {', '.join([c['column_name'] for c in table.columns])}\n\n"

                for row in data:
                    row_text = " | ".join([f"{k}: {v}" for k, v in row.items() if v is not None])
                    if len(current_chunk) + len(row_text) > chunk_size * 4:  # ~4 chars per word
                        chunks_text.append(current_chunk)
                        current_chunk = f"Table: {table.table_name}\n"
                    current_chunk += row_text + "\n"

                if current_chunk.strip():
                    chunks_text.append(current_chunk)

                # Create embeddings and store as document chunks
                chunks_to_create = []
                for i, chunk_text in enumerate(chunks_text):
                    embedding = await embedding_service.get_embedding(chunk_text)

                    chunk = DocumentChunk(
                        chunk_id=uuid4(),
                        document_id=doc.document_id,
                        chunk_index=total_chunks + i,
                        content=chunk_text,
                        section_title=f"Table: {table.table_name}",
                        embedding=embedding,
                    )
                    chunks_to_create.append(chunk)

                if chunks_to_create:
                    await chunk_repo.create_batch(chunks_to_create)
                    total_chunks += len(chunks_to_create)

            await connector.disconnect()

            # Update document with chunk count
            doc.complete_processing(total_chunks)
            await doc_repo.update(doc)

            # Update sync status
            await self.repository.update_sync_status(
                connection_id, SyncStatus.COMPLETED, chunks_synced=total_chunks
            )
            return total_chunks, None

        except Exception as e:
            logger.error(f"Sync error: {e}")
            await self.repository.update_sync_status(
                connection_id, SyncStatus.FAILED, str(e)
            )
            return 0, str(e)

    async def preview_data(
        self,
        connection_id: UUID,
        table_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Preview data from a table"""
        connection = await self.repository.get_by_id(connection_id)
        if not connection:
            raise ValueError("Connection not found")

        password = decrypt_password(connection.password_encrypted)
        connector = get_connector(connection, password)

        try:
            if await connector.connect():
                data = await connector.get_table_data(table_name, limit=limit)
                await connector.disconnect()
                return data
            else:
                raise ValueError("Failed to connect to database")
        finally:
            await connector.disconnect()

    async def execute_query(
        self,
        connection_id: UUID,
        query: str
    ) -> List[Dict[str, Any]]:
        """Execute a custom query"""
        connection = await self.repository.get_by_id(connection_id)
        if not connection:
            raise ValueError("Connection not found")

        # Security: basic query validation
        query_lower = query.lower().strip()
        if any(word in query_lower for word in ['drop', 'delete', 'truncate', 'alter', 'insert', 'update']):
            raise ValueError("Only SELECT queries are allowed")

        password = decrypt_password(connection.password_encrypted)
        connector = get_connector(connection, password)

        try:
            if await connector.connect():
                data = await connector.execute_query(query)
                await connector.disconnect()
                return data
            else:
                raise ValueError("Failed to connect to database")
        finally:
            await connector.disconnect()


# Singleton instance
_connector_service: Optional[ConnectorService] = None


async def get_connector_service() -> ConnectorService:
    """Get or create connector service instance"""
    global _connector_service
    if _connector_service is None:
        _connector_service = ConnectorService()
    return _connector_service
