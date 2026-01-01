"""
CogniFy Embedding Repository

Handles embedding cache operations with PostgreSQL

Created with love by Angela & David - 1 January 2026
"""

import hashlib
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from app.infrastructure.database import Database


class EmbeddingRepository:
    """Repository for embedding cache operations"""

    # =========================================================================
    # CACHE OPERATIONS
    # =========================================================================

    async def get_cached_embedding(
        self,
        text: str,
        model_name: str = "nomic-embed-text"
    ) -> Optional[List[float]]:
        """
        Get embedding from cache if exists and not expired

        Args:
            text: The text to get embedding for
            model_name: The embedding model name

        Returns:
            List of floats (embedding) or None if not found/expired
        """
        text_hash = self._hash_text(text)

        sql = """
            SELECT embedding::text
            FROM embedding_cache
            WHERE text_hash = $1
              AND model_name = $2
              AND expires_at > NOW()
        """

        pool = await Database.get_pool()
        row = await pool.fetchrow(sql, text_hash, model_name)

        if row and row["embedding"]:
            # Parse pgvector format: [0.1,0.2,0.3,...]
            embedding_str = row["embedding"]
            return self._parse_vector_string(embedding_str)

        return None

    async def cache_embedding(
        self,
        text: str,
        embedding: List[float],
        model_name: str = "nomic-embed-text",
        ttl_hours: int = 1
    ) -> bool:
        """
        Cache an embedding with TTL

        Args:
            text: The original text
            embedding: The embedding vector
            model_name: The embedding model name
            ttl_hours: Time to live in hours

        Returns:
            True if cached successfully
        """
        text_hash = self._hash_text(text)
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        sql = """
            INSERT INTO embedding_cache (text_hash, embedding, model_name, expires_at)
            VALUES ($1, $2::vector, $3, $4)
            ON CONFLICT (text_hash, model_name)
            DO UPDATE SET
                embedding = EXCLUDED.embedding,
                expires_at = EXCLUDED.expires_at,
                created_at = NOW()
        """

        try:
            pool = await Database.get_pool()
            await pool.execute(sql, text_hash, embedding, model_name, expires_at)
            return True
        except Exception as e:
            print(f"Failed to cache embedding: {e}")
            return False

    async def delete_expired_cache(self) -> int:
        """
        Delete expired cache entries

        Returns:
            Number of deleted entries
        """
        sql = """
            WITH deleted AS (
                DELETE FROM embedding_cache
                WHERE expires_at < NOW()
                RETURNING cache_id
            )
            SELECT COUNT(*) as count FROM deleted
        """

        pool = await Database.get_pool()
        row = await pool.fetchrow(sql)
        return row["count"] if row else 0

    async def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        sql = """
            SELECT
                COUNT(*) as total_entries,
                COUNT(*) FILTER (WHERE expires_at > NOW()) as active_entries,
                COUNT(*) FILTER (WHERE expires_at <= NOW()) as expired_entries,
                COUNT(DISTINCT model_name) as models_cached,
                MIN(created_at) as oldest_entry,
                MAX(created_at) as newest_entry
            FROM embedding_cache
        """

        pool = await Database.get_pool()
        row = await pool.fetchrow(sql)

        return {
            "total_entries": row["total_entries"],
            "active_entries": row["active_entries"],
            "expired_entries": row["expired_entries"],
            "models_cached": row["models_cached"],
            "oldest_entry": row["oldest_entry"].isoformat() if row["oldest_entry"] else None,
            "newest_entry": row["newest_entry"].isoformat() if row["newest_entry"] else None,
        }

    # =========================================================================
    # VECTOR SEARCH QUERIES
    # =========================================================================

    async def find_similar_chunks(
        self,
        embedding: List[float],
        limit: int = 10,
        threshold: float = 0.3,
        document_ids: Optional[List[UUID]] = None,
        similarity_method: str = "cosine"
    ) -> List[dict]:
        """
        Find similar chunks using vector similarity

        Args:
            embedding: Query embedding vector
            limit: Maximum results
            threshold: Minimum similarity threshold
            document_ids: Optional filter by document IDs
            similarity_method: cosine, euclidean, or dot

        Returns:
            List of chunk dictionaries with similarity scores
        """
        # Get operator
        operator = self._get_operator(similarity_method)

        sql = f"""
            SELECT
                c.chunk_id,
                c.document_id,
                c.content,
                c.page_number,
                c.section_title,
                c.chunk_index,
                d.title as document_title,
                d.original_filename,
                1 - (c.embedding {operator} $1::vector) as similarity
            FROM document_chunks c
            JOIN documents d ON c.document_id = d.document_id
            WHERE c.embedding IS NOT NULL
              AND d.is_deleted = false
              AND d.processing_status = 'completed'
        """

        params: list = [embedding]
        param_idx = 2

        if document_ids:
            sql += f" AND d.document_id = ANY(${param_idx}::uuid[])"
            params.append([str(d) for d in document_ids])
            param_idx += 1

        sql += f"""
              AND 1 - (c.embedding {operator} $1::vector) >= ${param_idx}
            ORDER BY c.embedding {operator} $1::vector
            LIMIT ${param_idx + 1}
        """
        params.extend([threshold, limit])

        pool = await Database.get_pool()
        rows = await pool.fetch(sql, *params)

        return [
            {
                "chunk_id": str(row["chunk_id"]),
                "document_id": str(row["document_id"]),
                "content": row["content"],
                "page_number": row["page_number"],
                "section_title": row["section_title"],
                "chunk_index": row["chunk_index"],
                "document_title": row["document_title"],
                "document_filename": row["original_filename"],
                "similarity": float(row["similarity"]),
            }
            for row in rows
        ]

    async def find_similar_documents(
        self,
        embedding: List[float],
        limit: int = 5,
        threshold: float = 0.3
    ) -> List[dict]:
        """
        Find similar documents based on average chunk similarity

        Returns documents ranked by their best matching chunk
        """
        sql = """
            WITH chunk_similarities AS (
                SELECT
                    d.document_id,
                    d.title,
                    d.original_filename,
                    d.file_type,
                    1 - (c.embedding <=> $1::vector) as similarity,
                    ROW_NUMBER() OVER (
                        PARTITION BY d.document_id
                        ORDER BY c.embedding <=> $1::vector
                    ) as rn
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.document_id
                WHERE c.embedding IS NOT NULL
                  AND d.is_deleted = false
                  AND d.processing_status = 'completed'
            )
            SELECT
                document_id,
                title,
                original_filename,
                file_type,
                similarity as best_chunk_similarity
            FROM chunk_similarities
            WHERE rn = 1
              AND similarity >= $2
            ORDER BY similarity DESC
            LIMIT $3
        """

        pool = await Database.get_pool()
        rows = await pool.fetch(sql, embedding, threshold, limit)

        return [
            {
                "document_id": str(row["document_id"]),
                "title": row["title"],
                "filename": row["original_filename"],
                "file_type": row["file_type"],
                "similarity": float(row["best_chunk_similarity"]),
            }
            for row in rows
        ]

    # =========================================================================
    # CHUNK EMBEDDING OPERATIONS
    # =========================================================================

    async def update_chunk_embedding(
        self,
        chunk_id: UUID,
        embedding: List[float],
        model_name: str = "nomic-embed-text"
    ) -> bool:
        """Update embedding for a specific chunk"""
        sql = """
            UPDATE document_chunks
            SET embedding = $2::vector,
                embedding_model = $3
            WHERE chunk_id = $1
        """

        try:
            pool = await Database.get_pool()
            await pool.execute(sql, str(chunk_id), embedding, model_name)
            return True
        except Exception as e:
            print(f"Failed to update chunk embedding: {e}")
            return False

    async def get_chunks_without_embeddings(
        self,
        limit: int = 100
    ) -> List[dict]:
        """Get chunks that need embeddings generated"""
        sql = """
            SELECT
                c.chunk_id,
                c.document_id,
                c.content,
                c.chunk_index
            FROM document_chunks c
            JOIN documents d ON c.document_id = d.document_id
            WHERE c.embedding IS NULL
              AND d.is_deleted = false
            ORDER BY c.created_at
            LIMIT $1
        """

        pool = await Database.get_pool()
        rows = await pool.fetch(sql, limit)

        return [
            {
                "chunk_id": str(row["chunk_id"]),
                "document_id": str(row["document_id"]),
                "content": row["content"],
                "chunk_index": row["chunk_index"],
            }
            for row in rows
        ]

    async def count_embeddings_by_document(
        self,
        document_id: UUID
    ) -> dict:
        """Get embedding statistics for a document"""
        sql = """
            SELECT
                COUNT(*) as total_chunks,
                COUNT(embedding) as chunks_with_embeddings,
                COUNT(*) - COUNT(embedding) as chunks_without_embeddings
            FROM document_chunks
            WHERE document_id = $1
        """

        pool = await Database.get_pool()
        row = await pool.fetchrow(sql, str(document_id))

        return {
            "total_chunks": row["total_chunks"],
            "with_embeddings": row["chunks_with_embeddings"],
            "without_embeddings": row["chunks_without_embeddings"],
            "completion_rate": (
                row["chunks_with_embeddings"] / row["total_chunks"]
                if row["total_chunks"] > 0 else 0.0
            ),
        }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _hash_text(self, text: str) -> str:
        """Create SHA-256 hash of text for cache key"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _get_operator(self, method: str) -> str:
        """Get pgvector operator for similarity method"""
        operators = {
            "cosine": "<=>",
            "euclidean": "<->",
            "dot": "<#>",
        }
        return operators.get(method, "<=>")

    def _parse_vector_string(self, vector_str: str) -> List[float]:
        """Parse pgvector string format to list of floats"""
        # Remove brackets and split
        clean = vector_str.strip("[]")
        if not clean:
            return []
        return [float(x) for x in clean.split(",")]


# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_embedding_repository: Optional[EmbeddingRepository] = None


def get_embedding_repository() -> EmbeddingRepository:
    """Get or create EmbeddingRepository singleton"""
    global _embedding_repository
    if _embedding_repository is None:
        _embedding_repository = EmbeddingRepository()
    return _embedding_repository
