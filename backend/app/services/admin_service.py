"""
CogniFy Admin Service
System administration, analytics, and user management
Created with love by Angela & David - 1 January 2026
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from app.infrastructure.database import get_db_pool

logger = logging.getLogger(__name__)


@dataclass
class SystemStats:
    """System-wide statistics"""
    total_users: int
    active_users_7d: int
    total_documents: int
    total_chunks: int
    total_conversations: int
    total_messages: int
    total_embeddings: int
    storage_used_mb: float
    avg_response_time_ms: float


@dataclass
class UserStats:
    """Per-user statistics"""
    user_id: UUID
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    document_count: int
    conversation_count: int
    message_count: int
    last_active: Optional[datetime]
    created_at: datetime


@dataclass
class UsageMetrics:
    """Usage metrics over time"""
    date: datetime
    documents_uploaded: int
    messages_sent: int
    embeddings_created: int
    unique_users: int


@dataclass
class DocumentTypeStats:
    """Statistics by document type"""
    file_type: str
    count: int
    total_size_mb: float
    total_chunks: int


class AdminService:
    """
    Admin service for system management and analytics.

    Features:
    - System-wide statistics
    - User management
    - Usage analytics
    - Storage monitoring
    """

    async def get_system_stats(self) -> SystemStats:
        """Get system-wide statistics"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Total users
            total_users = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE is_active = true"
            )

            # Active users in last 7 days
            active_users = await conn.fetchval("""
                SELECT COUNT(DISTINCT user_id)
                FROM conversations
                WHERE updated_at >= NOW() - INTERVAL '7 days'
            """)

            # Total documents
            total_documents = await conn.fetchval(
                "SELECT COUNT(*) FROM documents WHERE is_deleted = false"
            )

            # Total chunks
            total_chunks = await conn.fetchval(
                "SELECT COUNT(*) FROM document_chunks"
            )

            # Total conversations
            total_conversations = await conn.fetchval(
                "SELECT COUNT(*) FROM conversations"
            )

            # Total messages
            total_messages = await conn.fetchval(
                "SELECT COUNT(*) FROM messages"
            )

            # Total embeddings (chunks with embeddings)
            total_embeddings = await conn.fetchval(
                "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"
            )

            # Storage used (documents)
            storage_result = await conn.fetchval("""
                SELECT COALESCE(SUM(file_size_bytes), 0)
                FROM documents
                WHERE is_deleted = false
            """)
            storage_mb = (storage_result or 0) / (1024 * 1024)

            # Average response time
            avg_response = await conn.fetchval("""
                SELECT COALESCE(AVG(response_time_ms), 0)
                FROM messages
                WHERE response_time_ms IS NOT NULL
            """)

        return SystemStats(
            total_users=total_users or 0,
            active_users_7d=active_users or 0,
            total_documents=total_documents or 0,
            total_chunks=total_chunks or 0,
            total_conversations=total_conversations or 0,
            total_messages=total_messages or 0,
            total_embeddings=total_embeddings or 0,
            storage_used_mb=round(storage_mb, 2),
            avg_response_time_ms=round(avg_response or 0, 2),
        )

    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 50,
        include_inactive: bool = False,
    ) -> List[UserStats]:
        """Get all users with their statistics"""
        pool = await get_db_pool()

        active_clause = "" if include_inactive else "WHERE u.is_active = true"

        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT
                    u.user_id,
                    u.email,
                    u.full_name,
                    u.role,
                    u.is_active,
                    u.created_at,
                    COALESCE(d.doc_count, 0) as document_count,
                    COALESCE(c.conv_count, 0) as conversation_count,
                    COALESCE(m.msg_count, 0) as message_count,
                    c.last_active
                FROM users u
                LEFT JOIN (
                    SELECT uploaded_by, COUNT(*) as doc_count
                    FROM documents
                    WHERE is_deleted = false
                    GROUP BY uploaded_by
                ) d ON d.uploaded_by = u.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as conv_count, MAX(updated_at) as last_active
                    FROM conversations
                    GROUP BY user_id
                ) c ON c.user_id = u.user_id
                LEFT JOIN (
                    SELECT c.user_id, COUNT(m.message_id) as msg_count
                    FROM messages m
                    JOIN conversations c ON c.conversation_id = m.conversation_id
                    GROUP BY c.user_id
                ) m ON m.user_id = u.user_id
                {active_clause}
                ORDER BY u.created_at DESC
                OFFSET $1 LIMIT $2
            """, skip, limit)

        return [
            UserStats(
                user_id=row['user_id'],
                email=row['email'],
                full_name=row['full_name'],
                role=row['role'],
                is_active=row['is_active'],
                document_count=row['document_count'],
                conversation_count=row['conversation_count'],
                message_count=row['message_count'],
                last_active=row['last_active'],
                created_at=row['created_at'],
            )
            for row in rows
        ]

    async def get_user_count(self, include_inactive: bool = False) -> int:
        """Get total user count"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            if include_inactive:
                return await conn.fetchval("SELECT COUNT(*) FROM users")
            return await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = true")

    async def get_usage_metrics(
        self,
        days: int = 30,
        interval: str = "day",
    ) -> List[UsageMetrics]:
        """
        Get usage metrics over time.

        Args:
            days: Number of days to look back
            interval: Grouping interval ('day', 'week', 'month')
        """
        pool = await get_db_pool()

        # Determine date truncation
        date_trunc = interval if interval in ('day', 'week', 'month') else 'day'

        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                WITH date_series AS (
                    SELECT generate_series(
                        DATE_TRUNC('{date_trunc}', NOW() - INTERVAL '{days} days'),
                        DATE_TRUNC('{date_trunc}', NOW()),
                        INTERVAL '1 {date_trunc}'
                    ) AS date
                ),
                docs AS (
                    SELECT DATE_TRUNC('{date_trunc}', created_at) as date, COUNT(*) as count
                    FROM documents
                    WHERE created_at >= NOW() - INTERVAL '{days} days'
                    GROUP BY 1
                ),
                msgs AS (
                    SELECT DATE_TRUNC('{date_trunc}', created_at) as date, COUNT(*) as count
                    FROM messages
                    WHERE created_at >= NOW() - INTERVAL '{days} days'
                    GROUP BY 1
                ),
                chunks AS (
                    SELECT DATE_TRUNC('{date_trunc}', created_at) as date, COUNT(*) as count
                    FROM document_chunks
                    WHERE created_at >= NOW() - INTERVAL '{days} days'
                    GROUP BY 1
                ),
                users AS (
                    SELECT DATE_TRUNC('{date_trunc}', updated_at) as date, COUNT(DISTINCT user_id) as count
                    FROM conversations
                    WHERE updated_at >= NOW() - INTERVAL '{days} days'
                    GROUP BY 1
                )
                SELECT
                    ds.date,
                    COALESCE(d.count, 0) as documents_uploaded,
                    COALESCE(m.count, 0) as messages_sent,
                    COALESCE(c.count, 0) as embeddings_created,
                    COALESCE(u.count, 0) as unique_users
                FROM date_series ds
                LEFT JOIN docs d ON d.date = ds.date
                LEFT JOIN msgs m ON m.date = ds.date
                LEFT JOIN chunks c ON c.date = ds.date
                LEFT JOIN users u ON u.date = ds.date
                ORDER BY ds.date
            """)

        return [
            UsageMetrics(
                date=row['date'],
                documents_uploaded=row['documents_uploaded'],
                messages_sent=row['messages_sent'],
                embeddings_created=row['embeddings_created'],
                unique_users=row['unique_users'],
            )
            for row in rows
        ]

    async def get_document_type_stats(self) -> List[DocumentTypeStats]:
        """Get statistics grouped by document type"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    d.file_type,
                    COUNT(*) as count,
                    COALESCE(SUM(d.file_size_bytes), 0) / (1024.0 * 1024.0) as total_size_mb,
                    COALESCE(SUM(d.total_chunks), 0) as total_chunks
                FROM documents d
                WHERE d.is_deleted = false
                GROUP BY d.file_type
                ORDER BY count DESC
            """)

        return [
            DocumentTypeStats(
                file_type=row['file_type'],
                count=row['count'],
                total_size_mb=round(row['total_size_mb'], 2),
                total_chunks=row['total_chunks'],
            )
            for row in rows
        ]

    async def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by activity"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    u.user_id,
                    u.email,
                    u.full_name,
                    COUNT(DISTINCT c.conversation_id) as conversations,
                    COUNT(DISTINCT m.message_id) as messages,
                    COUNT(DISTINCT d.document_id) as documents
                FROM users u
                LEFT JOIN conversations c ON c.user_id = u.user_id
                LEFT JOIN messages m ON m.conversation_id = c.conversation_id
                LEFT JOIN documents d ON d.uploaded_by = u.user_id AND d.is_deleted = false
                WHERE u.is_active = true
                GROUP BY u.user_id, u.email, u.full_name
                ORDER BY messages DESC
                LIMIT $1
            """, limit)

        return [
            {
                "user_id": str(row['user_id']),
                "email": row['email'],
                "full_name": row['full_name'],
                "conversations": row['conversations'],
                "messages": row['messages'],
                "documents": row['documents'],
            }
            for row in rows
        ]

    async def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent system activity"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Recent documents
            docs = await conn.fetch("""
                SELECT
                    'document' as type,
                    d.document_id as id,
                    d.original_filename as title,
                    u.email as user_email,
                    d.created_at as timestamp
                FROM documents d
                JOIN users u ON u.user_id = d.uploaded_by
                WHERE d.is_deleted = false
                ORDER BY d.created_at DESC
                LIMIT $1
            """, limit // 2)

            # Recent conversations
            convs = await conn.fetch("""
                SELECT
                    'conversation' as type,
                    c.conversation_id as id,
                    COALESCE(c.title, 'New Conversation') as title,
                    u.email as user_email,
                    c.created_at as timestamp
                FROM conversations c
                JOIN users u ON u.user_id = c.user_id
                ORDER BY c.created_at DESC
                LIMIT $1
            """, limit // 2)

        # Combine and sort
        activity = []
        for row in docs:
            activity.append({
                "type": row['type'],
                "id": str(row['id']),
                "title": row['title'],
                "user_email": row['user_email'],
                "timestamp": row['timestamp'].isoformat(),
            })
        for row in convs:
            activity.append({
                "type": row['type'],
                "id": str(row['id']),
                "title": row['title'],
                "user_email": row['user_email'],
                "timestamp": row['timestamp'].isoformat(),
            })

        # Sort by timestamp descending
        activity.sort(key=lambda x: x['timestamp'], reverse=True)
        return activity[:limit]

    async def update_user_role(
        self,
        user_id: UUID,
        new_role: str,
    ) -> bool:
        """Update user role"""
        if new_role not in ('admin', 'editor', 'user'):
            raise ValueError(f"Invalid role: {new_role}")

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE users
                SET role = $1, updated_at = NOW()
                WHERE user_id = $2
            """, new_role, user_id)

        return result == "UPDATE 1"

    async def toggle_user_status(
        self,
        user_id: UUID,
    ) -> bool:
        """Toggle user active status"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE users
                SET is_active = NOT is_active, updated_at = NOW()
                WHERE user_id = $1
            """, user_id)

        return result == "UPDATE 1"


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_admin_service: Optional[AdminService] = None


def get_admin_service() -> AdminService:
    """Get global AdminService instance"""
    global _admin_service
    if _admin_service is None:
        _admin_service = AdminService()
    return _admin_service
