"""
CogniFy Conversation Repository

Handles conversation and message persistence

Created with love by Angela & David - 1 January 2026
"""

import json
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.infrastructure.database import Database


class ConversationRepository:
    """Repository for conversation operations"""

    # =========================================================================
    # CONVERSATION OPERATIONS
    # =========================================================================

    async def create_conversation(
        self,
        user_id: Optional[UUID] = None,
        title: Optional[str] = None,
        model_provider: str = "ollama",
        model_name: str = "llama3.2:1b",
        rag_enabled: bool = True,
        rag_settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new conversation"""
        sql = """
            INSERT INTO conversations (
                user_id, title, model_provider, model_name,
                rag_enabled, rag_settings
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING
                conversation_id, user_id, session_id, title,
                model_provider, model_name, rag_enabled, rag_settings,
                message_count, created_at, updated_at
        """

        pool = await Database.get_pool()
        row = await pool.fetchrow(
            sql,
            str(user_id) if user_id else None,
            title,
            model_provider,
            model_name,
            rag_enabled,
            json.dumps(rag_settings) if rag_settings else None,
        )

        return self._row_to_conversation(row)

    async def get_conversation(self, conversation_id: UUID) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        sql = """
            SELECT
                conversation_id, user_id, session_id, title,
                model_provider, model_name, rag_enabled, rag_settings,
                message_count, created_at, updated_at
            FROM conversations
            WHERE conversation_id = $1
        """

        pool = await Database.get_pool()
        row = await pool.fetchrow(sql, str(conversation_id))

        if not row:
            return None

        return self._row_to_conversation(row)

    async def list_conversations(
        self,
        user_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List conversations with optional user filter"""
        sql = """
            SELECT
                conversation_id, user_id, session_id, title,
                model_provider, model_name, rag_enabled, rag_settings,
                message_count, created_at, updated_at
            FROM conversations
            WHERE ($1::uuid IS NULL OR user_id = $1)
            ORDER BY updated_at DESC
            LIMIT $2 OFFSET $3
        """

        pool = await Database.get_pool()
        rows = await pool.fetch(sql, str(user_id) if user_id else None, limit, offset)

        return [self._row_to_conversation(row) for row in rows]

    async def update_conversation(
        self,
        conversation_id: UUID,
        title: Optional[str] = None,
        rag_enabled: Optional[bool] = None,
        rag_settings: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update conversation"""
        # Build dynamic update
        updates = ["updated_at = NOW()"]
        params: List[Any] = [str(conversation_id)]
        param_idx = 2

        if title is not None:
            updates.append(f"title = ${param_idx}")
            params.append(title)
            param_idx += 1

        if rag_enabled is not None:
            updates.append(f"rag_enabled = ${param_idx}")
            params.append(rag_enabled)
            param_idx += 1

        if rag_settings is not None:
            updates.append(f"rag_settings = ${param_idx}")
            params.append(json.dumps(rag_settings))
            param_idx += 1

        sql = f"""
            UPDATE conversations
            SET {', '.join(updates)}
            WHERE conversation_id = $1
            RETURNING
                conversation_id, user_id, session_id, title,
                model_provider, model_name, rag_enabled, rag_settings,
                message_count, created_at, updated_at
        """

        pool = await Database.get_pool()
        row = await pool.fetchrow(sql, *params)

        if not row:
            return None

        return self._row_to_conversation(row)

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """Delete conversation and its messages"""
        sql = "DELETE FROM conversations WHERE conversation_id = $1"

        pool = await Database.get_pool()
        result = await pool.execute(sql, str(conversation_id))

        return "DELETE 1" in result

    async def generate_title(self, conversation_id: UUID) -> Optional[str]:
        """Generate title from first user message"""
        sql = """
            SELECT content
            FROM messages
            WHERE conversation_id = $1
              AND message_type = 'user'
            ORDER BY created_at
            LIMIT 1
        """

        pool = await Database.get_pool()
        row = await pool.fetchrow(sql, str(conversation_id))

        if not row:
            return None

        # Generate title from first message (first 50 chars)
        content = row["content"]
        title = content[:50] + "..." if len(content) > 50 else content

        # Update conversation
        await self.update_conversation(conversation_id, title=title)

        return title

    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================

    async def add_message(
        self,
        conversation_id: UUID,
        message_type: str,  # user, assistant, system
        content: str,
        sources_used: Optional[List[Dict[str, Any]]] = None,
        response_time_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add message to conversation"""
        sql = """
            INSERT INTO messages (
                conversation_id, message_type, content,
                sources_used, response_time_ms
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING
                message_id, conversation_id, message_type, content,
                sources_used, response_time_ms, created_at
        """

        pool = await Database.get_pool()

        # Insert message
        row = await pool.fetchrow(
            sql,
            str(conversation_id),
            message_type,
            content,
            json.dumps(sources_used) if sources_used else None,
            response_time_ms,
        )

        # Update message count
        await pool.execute(
            """
            UPDATE conversations
            SET message_count = message_count + 1, updated_at = NOW()
            WHERE conversation_id = $1
            """,
            str(conversation_id),
        )

        return self._row_to_message(row)

    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 50,
        before_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Get messages for conversation"""
        sql = """
            SELECT
                message_id, conversation_id, message_type, content,
                sources_used, response_time_ms, created_at
            FROM messages
            WHERE conversation_id = $1
        """

        params: List[Any] = [str(conversation_id)]

        if before_id:
            sql += " AND created_at < (SELECT created_at FROM messages WHERE message_id = $2)"
            params.append(str(before_id))

        sql += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)

        pool = await Database.get_pool()
        rows = await pool.fetch(sql, *params)

        # Reverse to get chronological order
        return [self._row_to_message(row) for row in reversed(rows)]

    async def get_last_messages(
        self,
        conversation_id: UUID,
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get last N messages for conversation history"""
        sql = """
            SELECT
                message_id, conversation_id, message_type, content,
                sources_used, response_time_ms, created_at
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        pool = await Database.get_pool()
        rows = await pool.fetch(sql, str(conversation_id), count)

        # Reverse to get chronological order
        return [self._row_to_message(row) for row in reversed(rows)]

    async def delete_message(self, message_id: UUID) -> bool:
        """Delete a specific message"""
        sql = "DELETE FROM messages WHERE message_id = $1 RETURNING conversation_id"

        pool = await Database.get_pool()
        row = await pool.fetchrow(sql, str(message_id))

        if row:
            # Update message count
            await pool.execute(
                """
                UPDATE conversations
                SET message_count = message_count - 1, updated_at = NOW()
                WHERE conversation_id = $1
                """,
                row["conversation_id"],
            )
            return True

        return False

    # =========================================================================
    # SEARCH & STATS
    # =========================================================================

    async def search_conversations(
        self,
        user_id: Optional[UUID] = None,
        query: str = "",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search conversations by title or message content"""
        sql = """
            SELECT DISTINCT ON (c.conversation_id)
                c.conversation_id, c.user_id, c.session_id, c.title,
                c.model_provider, c.model_name, c.rag_enabled, c.rag_settings,
                c.message_count, c.created_at, c.updated_at
            FROM conversations c
            LEFT JOIN messages m ON c.conversation_id = m.conversation_id
            WHERE ($1::uuid IS NULL OR c.user_id = $1)
              AND (
                  c.title ILIKE '%' || $2 || '%'
                  OR m.content ILIKE '%' || $2 || '%'
              )
            ORDER BY c.conversation_id, c.updated_at DESC
            LIMIT $3
        """

        pool = await Database.get_pool()
        rows = await pool.fetch(sql, str(user_id) if user_id else None, query, limit)

        return [self._row_to_conversation(row) for row in rows]

    async def get_conversation_stats(
        self,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get conversation statistics"""
        sql = """
            SELECT
                COUNT(*) as total_conversations,
                SUM(message_count) as total_messages,
                COUNT(*) FILTER (WHERE rag_enabled = true) as rag_enabled_count,
                COUNT(DISTINCT model_provider) as providers_used,
                MAX(updated_at) as last_activity
            FROM conversations
            WHERE ($1::uuid IS NULL OR user_id = $1)
        """

        pool = await Database.get_pool()
        row = await pool.fetchrow(sql, str(user_id) if user_id else None)

        return {
            "total_conversations": row["total_conversations"],
            "total_messages": row["total_messages"] or 0,
            "rag_enabled_count": row["rag_enabled_count"],
            "providers_used": row["providers_used"],
            "last_activity": row["last_activity"].isoformat() if row["last_activity"] else None,
        }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _row_to_conversation(self, row) -> Dict[str, Any]:
        """Convert database row to conversation dict"""
        rag_settings = None
        if row["rag_settings"]:
            if isinstance(row["rag_settings"], str):
                rag_settings = json.loads(row["rag_settings"])
            else:
                rag_settings = row["rag_settings"]

        return {
            "conversation_id": str(row["conversation_id"]),
            "user_id": str(row["user_id"]) if row["user_id"] else None,
            "session_id": row["session_id"],
            "title": row["title"],
            "model_provider": row["model_provider"],
            "model_name": row["model_name"],
            "rag_enabled": row["rag_enabled"],
            "rag_settings": rag_settings,
            "message_count": row["message_count"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

    def _row_to_message(self, row) -> Dict[str, Any]:
        """Convert database row to message dict"""
        sources = None
        if row["sources_used"]:
            if isinstance(row["sources_used"], str):
                sources = json.loads(row["sources_used"])
            else:
                sources = row["sources_used"]

        return {
            "message_id": str(row["message_id"]),
            "conversation_id": str(row["conversation_id"]),
            "message_type": row["message_type"],
            "content": row["content"],
            "sources_used": sources,
            "response_time_ms": row["response_time_ms"],
            "created_at": row["created_at"].isoformat(),
        }


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_conversation_repository: Optional[ConversationRepository] = None


def get_conversation_repository() -> ConversationRepository:
    """Get or create ConversationRepository singleton"""
    global _conversation_repository
    if _conversation_repository is None:
        _conversation_repository = ConversationRepository()
    return _conversation_repository
