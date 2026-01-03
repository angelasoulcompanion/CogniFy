"""
Document Repository
Database operations for Document and DocumentChunk entities
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
import asyncpg

from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.database import Database
from app.domain.entities.document import Document, DocumentChunk, ProcessingStatus, ProcessingStep, FileType


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document entity"""

    def __init__(self):
        super().__init__("documents", "document_id")

    def _row_to_entity(self, row: asyncpg.Record) -> Document:
        """Convert database row to Document entity"""
        try:
            status = ProcessingStatus(row["processing_status"])
        except ValueError:
            status = ProcessingStatus.PENDING

        try:
            step = ProcessingStep(row.get("processing_step", "pending"))
        except (ValueError, TypeError):
            step = ProcessingStep.PENDING

        try:
            file_type = FileType(row["file_type"])
        except ValueError:
            file_type = FileType.TXT

        return Document(
            document_id=row["document_id"],
            uploaded_by=row.get("uploaded_by"),
            filename=row["filename"],
            original_filename=row["original_filename"],
            file_type=file_type,
            file_size_bytes=row.get("file_size_bytes"),
            file_path=row.get("file_path"),
            title=row.get("title"),
            description=row.get("description"),
            page_count=row.get("page_count"),
            language=row.get("language", "th"),
            tags=row.get("tags") or [],
            processing_status=status,
            processing_step=step,
            processing_progress=row.get("processing_progress", 0) or 0,
            processing_error=row.get("processing_error"),
            total_chunks=row.get("total_chunks", 0),
            is_deleted=row.get("is_deleted", False),
            created_at=row["created_at"],
            processed_at=row.get("processed_at"),
        )

    def _entity_to_dict(self, entity: Document) -> Dict[str, Any]:
        """Convert Document entity to dictionary"""
        return {
            "document_id": entity.document_id,
            "uploaded_by": entity.uploaded_by,
            "filename": entity.filename,
            "original_filename": entity.original_filename,
            "file_type": entity.file_type.value,
            "file_size_bytes": entity.file_size_bytes,
            "file_path": entity.file_path,
            "title": entity.title,
            "description": entity.description,
            "page_count": entity.page_count,
            "language": entity.language,
            "tags": entity.tags,
            "processing_status": entity.processing_status.value,
            "processing_step": entity.processing_step.value if entity.processing_step else "pending",
            "processing_progress": entity.processing_progress,
            "processing_error": entity.processing_error,
            "total_chunks": entity.total_chunks,
            "is_deleted": entity.is_deleted,
            "created_at": entity.created_at,
            "processed_at": entity.processed_at,
        }

    async def create(self, document: Document) -> Document:
        """Create a new document"""
        query = """
            INSERT INTO documents (
                document_id, uploaded_by, filename, original_filename, file_type,
                file_size_bytes, file_path, title, description, page_count,
                language, tags, processing_status, processing_error, total_chunks,
                is_deleted, created_at, processed_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            RETURNING *
        """
        row = await Database.fetchrow(
            query,
            document.document_id,
            document.uploaded_by,
            document.filename,
            document.original_filename,
            document.file_type.value,
            document.file_size_bytes,
            document.file_path,
            document.title,
            document.description,
            document.page_count,
            document.language,
            document.tags,
            document.processing_status.value,
            document.processing_error,
            document.total_chunks,
            document.is_deleted,
            document.created_at,
            document.processed_at,
        )
        return self._row_to_entity(row)

    async def update(self, document: Document) -> Document:
        """Update document"""
        query = """
            UPDATE documents SET
                title = $2,
                description = $3,
                tags = $4,
                processing_status = $5,
                processing_error = $6,
                total_chunks = $7,
                page_count = $8,
                processed_at = $9
            WHERE document_id = $1
            RETURNING *
        """
        row = await Database.fetchrow(
            query,
            document.document_id,
            document.title,
            document.description,
            document.tags,
            document.processing_status.value,
            document.processing_error,
            document.total_chunks,
            document.page_count,
            document.processed_at,
        )
        if row is None:
            raise ValueError(f"Document {document.document_id} not found")
        return self._row_to_entity(row)

    async def get_all_active(
        self,
        skip: int = 0,
        limit: int = 100,
        uploaded_by: Optional[UUID] = None
    ) -> List[Document]:
        """Get all non-deleted documents"""
        if uploaded_by:
            query = """
                SELECT * FROM documents
                WHERE is_deleted = false AND uploaded_by = $3
                ORDER BY created_at DESC
                OFFSET $1 LIMIT $2
            """
            rows = await Database.fetch(query, skip, limit, uploaded_by)
        else:
            query = """
                SELECT * FROM documents
                WHERE is_deleted = false
                ORDER BY created_at DESC
                OFFSET $1 LIMIT $2
            """
            rows = await Database.fetch(query, skip, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_status(self, status: ProcessingStatus) -> List[Document]:
        """Get documents by processing status"""
        query = """
            SELECT * FROM documents
            WHERE processing_status = $1 AND is_deleted = false
            ORDER BY created_at DESC
        """
        rows = await Database.fetch(query, status.value)
        return [self._row_to_entity(row) for row in rows]

    async def update_status(
        self,
        document_id: UUID,
        status: ProcessingStatus,
        error: Optional[str] = None,
        chunk_count: Optional[int] = None
    ) -> bool:
        """Update document processing status"""
        # Ensure document_id is UUID type for PostgreSQL
        doc_id = document_id if isinstance(document_id, UUID) else UUID(str(document_id))

        if status == ProcessingStatus.COMPLETED:
            query = """
                UPDATE documents
                SET processing_status = $2, total_chunks = $3, processed_at = NOW()
                WHERE document_id = $1
                RETURNING document_id
            """
            result = await Database.fetchval(query, doc_id, status.value, chunk_count or 0)
        elif status == ProcessingStatus.FAILED:
            query = """
                UPDATE documents
                SET processing_status = $2, processing_error = $3
                WHERE document_id = $1
                RETURNING document_id
            """
            result = await Database.fetchval(query, doc_id, status.value, error)
        else:
            query = """
                UPDATE documents
                SET processing_status = $2
                WHERE document_id = $1
                RETURNING document_id
            """
            result = await Database.fetchval(query, doc_id, status.value)

        return result is not None

    async def update_progress(
        self,
        document_id: UUID,
        step: ProcessingStep,
        progress: int
    ) -> bool:
        """Update document processing step and progress"""
        doc_id = document_id if isinstance(document_id, UUID) else UUID(str(document_id))
        query = """
            UPDATE documents
            SET processing_step = $2, processing_progress = $3
            WHERE document_id = $1
            RETURNING document_id
        """
        result = await Database.fetchval(query, doc_id, step.value, progress)
        return result is not None

    async def soft_delete(self, document_id: UUID) -> bool:
        """Soft delete a document"""
        query = """
            UPDATE documents
            SET is_deleted = true
            WHERE document_id = $1
            RETURNING document_id
        """
        result = await Database.fetchval(query, document_id)
        return result is not None

    async def search_by_title(self, search_term: str, limit: int = 20) -> List[Document]:
        """Search documents by title"""
        query = """
            SELECT * FROM documents
            WHERE is_deleted = false
              AND (title ILIKE $1 OR original_filename ILIKE $1)
            ORDER BY created_at DESC
            LIMIT $2
        """
        rows = await Database.fetch(query, f"%{search_term}%", limit)
        return [self._row_to_entity(row) for row in rows]


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    """Repository for DocumentChunk entity"""

    def __init__(self):
        super().__init__("document_chunks", "chunk_id")

    def _embedding_to_pgvector(self, embedding) -> str:
        """Convert embedding to pgvector string format"""
        # Already a string - return as-is (but validate format)
        if isinstance(embedding, str):
            if embedding.startswith('[') and embedding.endswith(']'):
                return embedding
            return "[" + embedding + "]"

        # Nested list [[...]] - unwrap
        if isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], list):
            embedding = embedding[0]

        # Normal list of floats
        if isinstance(embedding, list):
            return "[" + ",".join(str(float(x)) for x in embedding) + "]"

        raise ValueError(f"Invalid embedding type: {type(embedding)}")

    def _row_to_entity(self, row: asyncpg.Record) -> DocumentChunk:
        """Convert database row to DocumentChunk entity"""
        return DocumentChunk(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            page_number=row.get("page_number"),
            section_title=row.get("section_title"),
            token_count=row.get("token_count"),
            embedding=list(row["embedding"]) if row.get("embedding") else None,
            embedding_model=row.get("embedding_model", "nomic-embed-text"),
            created_at=row["created_at"],
        )

    def _entity_to_dict(self, entity: DocumentChunk) -> Dict[str, Any]:
        """Convert DocumentChunk entity to dictionary"""
        return {
            "chunk_id": entity.chunk_id,
            "document_id": entity.document_id,
            "chunk_index": entity.chunk_index,
            "content": entity.content,
            "page_number": entity.page_number,
            "section_title": entity.section_title,
            "token_count": entity.token_count,
            "embedding": entity.embedding,
            "embedding_model": entity.embedding_model,
            "created_at": entity.created_at,
        }

    async def create(self, chunk: DocumentChunk) -> DocumentChunk:
        """Create a new chunk"""
        query = """
            INSERT INTO document_chunks (
                chunk_id, document_id, chunk_index, content, page_number,
                section_title, token_count, embedding, embedding_model, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::vector, $9, $10)
            RETURNING *
        """
        embedding_str = self._embedding_to_pgvector(chunk.embedding) if chunk.embedding else None
        # Truncate section_title to 500 chars to fit VARCHAR(500)
        section_title = chunk.section_title[:500] if chunk.section_title else None
        row = await Database.fetchrow(
            query,
            chunk.chunk_id,
            chunk.document_id,
            chunk.chunk_index,
            chunk.content,
            chunk.page_number,
            section_title,
            chunk.token_count,
            embedding_str,
            chunk.embedding_model,
            chunk.created_at,
        )
        return self._row_to_entity(row)

    async def create_batch(self, chunks: List[DocumentChunk]) -> int:
        """Create multiple chunks in batch"""
        if not chunks:
            return 0

        query = """
            INSERT INTO document_chunks (
                chunk_id, document_id, chunk_index, content, page_number,
                section_title, token_count, embedding, embedding_model, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::vector, $9, $10)
        """

        args = [
            (
                chunk.chunk_id,
                chunk.document_id,
                chunk.chunk_index,
                chunk.content,
                chunk.page_number,
                # Truncate section_title to 500 chars to fit VARCHAR(500)
                chunk.section_title[:500] if chunk.section_title else None,
                chunk.token_count,
                self._embedding_to_pgvector(chunk.embedding) if chunk.embedding else None,
                chunk.embedding_model,
                chunk.created_at,
            )
            for chunk in chunks
        ]

        await Database.executemany(query, args)
        return len(chunks)

    async def get_by_document(self, document_id: UUID) -> List[DocumentChunk]:
        """Get all chunks for a document"""
        query = """
            SELECT * FROM document_chunks
            WHERE document_id = $1
            ORDER BY chunk_index ASC
        """
        rows = await Database.fetch(query, document_id)
        return [self._row_to_entity(row) for row in rows]

    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all chunks for a document"""
        query = """
            DELETE FROM document_chunks
            WHERE document_id = $1
        """
        result = await Database.execute(query, document_id)
        # Extract count from "DELETE X"
        return int(result.split()[-1]) if result else 0

    async def search_similar(
        self,
        embedding: List[float],
        top_k: int = 10,
        threshold: float = 0.3,
        document_ids: Optional[List[UUID]] = None
    ) -> List[tuple[DocumentChunk, float]]:
        """Search for similar chunks using vector similarity"""
        embedding_str = self._embedding_to_pgvector(embedding)
        if document_ids:
            query = """
                SELECT *, (embedding <=> $1::vector) as distance
                FROM document_chunks
                WHERE embedding IS NOT NULL
                  AND document_id = ANY($4)
                  AND (1 - (embedding <=> $1::vector)) >= $3
                ORDER BY distance ASC
                LIMIT $2
            """
            rows = await Database.fetch(query, embedding_str, top_k, threshold, document_ids)
        else:
            query = """
                SELECT *, (embedding <=> $1::vector) as distance
                FROM document_chunks
                WHERE embedding IS NOT NULL
                  AND (1 - (embedding <=> $1::vector)) >= $3
                ORDER BY distance ASC
                LIMIT $2
            """
            rows = await Database.fetch(query, embedding_str, top_k, threshold)

        results = []
        for row in rows:
            chunk = self._row_to_entity(row)
            similarity = 1 - row["distance"]  # Convert distance to similarity
            results.append((chunk, similarity))

        return results
