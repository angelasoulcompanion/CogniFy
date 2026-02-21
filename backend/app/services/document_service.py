"""
CogniFy Document Service
Document processing pipeline: Extract → Chunk → Embed → Store
Now with OCR support for images and scanned PDFs!
Created with love by Angela & David - 1 January 2026
"""

import os
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.core.config import settings
from app.core.logging import logger
from app.core.pgvector import embedding_to_pgvector
from app.domain.entities.document import Document, DocumentChunk, ProcessingStatus, FileType
from app.infrastructure.repositories.document_repository import DocumentRepository, DocumentChunkRepository
from app.services.embedding_service import get_embedding_service, build_embedding_text
from app.services.chunking_service import get_chunking_service, Chunk
from app.services.text_extraction import TextExtractor


class DocumentService:
    """
    Document processing service.

    Pipeline:
    1. Extract text from document
    2. Chunk text with overlap
    3. Generate embeddings for chunks
    4. Store chunks in database
    """

    def __init__(self):
        self.document_repo = DocumentRepository()
        self.chunk_repo = DocumentChunkRepository()
        self.embedding_service = get_embedding_service()
        self.chunking_service = get_chunking_service()

    async def process_document(
        self,
        document_id: UUID,
        on_progress: Optional[callable] = None
    ) -> Document:
        """
        Process a document: extract → chunk → embed → store.

        Args:
            document_id: ID of the document to process
            on_progress: Optional callback for progress updates

        Returns:
            Updated Document entity
        """
        # Get document
        document = await self.document_repo.get_by_id(document_id)
        if document is None:
            raise ValueError(f"Document not found: {document_id}")

        if not document.file_path or not os.path.exists(document.file_path):
            await self._fail_document(document_id, "File not found")
            raise FileNotFoundError(f"File not found: {document.file_path}")

        try:
            # Update status to processing
            await self.document_repo.update_status(document_id, ProcessingStatus.PROCESSING)

            if on_progress:
                await on_progress("extracting", 0)

            # 1. Extract text
            logger.info("Extracting text from {}", document.original_filename)
            full_text, page_count, pages = await TextExtractor.extract(
                document.file_path,
                document.file_type
            )

            if not full_text.strip():
                await self._fail_document(document_id, "No text content found")
                raise ValueError("No text content found in document")

            # Update page count
            document.page_count = page_count

            if on_progress:
                await on_progress("chunking", 20)

            # 2. Chunk text
            logger.info("Chunking text into segments")
            if len(pages) > 1:
                chunks = self.chunking_service.chunk_by_pages(pages)
            else:
                chunks = self.chunking_service.chunk_text(full_text)

            logger.info("Created {} chunks", len(chunks))

            if on_progress:
                await on_progress("embedding", 40)

            # 3. Generate embeddings with enriched context
            logger.info("Generating embeddings with document context")
            document_title = document.original_filename
            chunk_texts = [
                build_embedding_text(
                    content=chunk.content,
                    document_title=document_title,
                    section_title=chunk.section_title,
                    page_number=chunk.page_number
                )
                for chunk in chunks
            ]
            embeddings = await self.embedding_service.get_embeddings_batch(
                chunk_texts,
                batch_size=5
            )

            # Count successful embeddings
            successful = sum(1 for e in embeddings if e is not None)
            logger.info("Generated {}/{} embeddings", successful, len(chunks))

            if on_progress:
                await on_progress("storing", 80)

            # 4. Create DocumentChunk entities
            logger.info("Storing chunks")
            document_chunks: List[DocumentChunk] = []

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                doc_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    token_count=chunk.token_count,
                    embedding=embedding,
                )
                document_chunks.append(doc_chunk)

            # 5. Delete existing chunks and insert new ones
            await self.chunk_repo.delete_by_document(document_id)
            await self.chunk_repo.create_batch(document_chunks)

            # 6. Update document status to COMPLETED
            document.processing_status = ProcessingStatus.COMPLETED
            document.page_count = page_count
            document.total_chunks = len(document_chunks)
            document.processed_at = datetime.now()
            await self.document_repo.update(document)

            if on_progress:
                await on_progress("completed", 100)

            logger.info("Document processed: {} — pages={}, chunks={}", document.original_filename, page_count, len(document_chunks))

            return await self.document_repo.get_by_id(document_id)

        except Exception as e:
            logger.error("Document processing error: {}", e)
            await self._fail_document(document_id, str(e))
            raise

    async def _fail_document(self, document_id: UUID, error: str) -> None:
        """Mark document as failed"""
        await self.document_repo.update_status(
            document_id,
            ProcessingStatus.FAILED,
            error=error
        )

    async def reprocess_document(self, document_id: UUID) -> Document:
        """Reprocess an existing document"""
        # Delete existing chunks
        await self.chunk_repo.delete_by_document(document_id)

        # Reset status
        await self.document_repo.update_status(document_id, ProcessingStatus.PENDING)

        # Process again
        return await self.process_document(document_id)

    async def get_document_stats(self, document_id: UUID) -> Dict[str, Any]:
        """Get statistics for a document"""
        document = await self.document_repo.get_by_id(document_id)
        if document is None:
            raise ValueError(f"Document not found: {document_id}")

        chunks = await self.chunk_repo.get_by_document(document_id)

        total_tokens = sum(c.token_count or 0 for c in chunks)
        chunks_with_embeddings = sum(1 for c in chunks if c.embedding)

        return {
            "document_id": str(document_id),
            "filename": document.original_filename,
            "status": document.processing_status.value,
            "page_count": document.page_count,
            "total_chunks": len(chunks),
            "chunks_with_embeddings": chunks_with_embeddings,
            "total_tokens": total_tokens,
            "avg_tokens_per_chunk": total_tokens // len(chunks) if chunks else 0,
        }


# ============================================================================
# BACKGROUND PROCESSING
# ============================================================================

def process_document_background(document_id: UUID) -> None:
    """
    Background task to process a document.
    Uses a completely separate database connection to avoid event loop issues.
    """
    import asyncio
    import asyncpg

    logger.info("Starting background processing for document: {}", document_id)

    async def _process_with_own_connection():
        """Process document with its own database connection"""
        from app.core.config import settings
        from app.domain.entities.document import ProcessingStatus
        from datetime import datetime

        # Create dedicated connection for this background task
        conn = await asyncpg.connect(settings.DATABASE_URL)

        try:
            # 1. Get document
            doc_row = await conn.fetchrow(
                "SELECT * FROM documents WHERE document_id = $1",
                document_id
            )

            if not doc_row:
                logger.error("Document not found: {}", document_id)
                return

            file_path = doc_row['file_path']
            file_type_str = doc_row['file_type']
            original_filename = doc_row['original_filename']

            if not file_path or not os.path.exists(file_path):
                await conn.execute(
                    "UPDATE documents SET processing_status = $1, processing_error = $2 WHERE document_id = $3",
                    'failed', 'File not found', document_id
                )
                logger.error("File not found: {}", file_path)
                return

            # 2. Update status to processing
            await conn.execute(
                "UPDATE documents SET processing_status = $1, processing_step = $2, processing_progress = $3 WHERE document_id = $4",
                'processing', 'extracting', 0, document_id
            )

            # 3. Extract text
            logger.info("Extracting text from {}", original_filename)
            from app.domain.entities.document import FileType
            file_type = FileType(file_type_str)
            full_text, page_count, pages = await TextExtractor.extract(file_path, file_type)

            if not full_text.strip():
                await conn.execute(
                    "UPDATE documents SET processing_status = $1, processing_error = $2 WHERE document_id = $3",
                    'failed', 'No text content found', document_id
                )
                logger.error("No text content found")
                return

            # 4. Chunk text
            await conn.execute(
                "UPDATE documents SET processing_step = $1, processing_progress = $2 WHERE document_id = $3",
                'chunking', 25, document_id
            )
            logger.info("Chunking text into segments")
            chunking_service = get_chunking_service()

            # Calculate average chars per page to detect slides/short content
            avg_chars_per_page = len(full_text) / max(page_count, 1)

            if avg_chars_per_page < 500 and len(pages) > 1:
                # Short content per page (likely slides) - use 1 page = 1 chunk
                logger.info("Detected slides/short content ({:.0f} chars/page avg)", avg_chars_per_page)
                chunks = []
                for page_num, page_text in pages:
                    if page_text.strip():  # Skip empty pages
                        from app.services.chunking_service import Chunk
                        chunks.append(Chunk(
                            content=page_text.strip(),
                            index=len(chunks),
                            start_char=0,
                            end_char=len(page_text),
                            token_count=len(page_text.split()),
                            page_number=page_num,
                            section_title=None
                        ))
            elif len(pages) > 1:
                chunks = chunking_service.chunk_by_pages(pages)
            else:
                chunks = chunking_service.chunk_text(full_text)
            logger.info("Created {} chunks", len(chunks))

            # 5. Generate embeddings (direct Ollama call to avoid event loop issues)
            await conn.execute(
                "UPDATE documents SET processing_step = $1, processing_progress = $2 WHERE document_id = $3",
                'embedding', 40, document_id
            )
            logger.info("Generating embeddings")
            import httpx
            embeddings = []
            total_chunks = len(chunks)
            for i, chunk in enumerate(chunks):
                # Update progress for each embedding (40-90% range)
                embed_progress = 40 + int((i / total_chunks) * 50)
                await conn.execute(
                    "UPDATE documents SET processing_progress = $1 WHERE document_id = $2",
                    embed_progress, document_id
                )
                try:
                    async with httpx.AsyncClient(timeout=60.0) as http_client:
                        # bge-m3 supports 8192 tokens, use full chunk content
                        response = await http_client.post(
                            "http://localhost:11434/api/embeddings",
                            json={"model": settings.EMBEDDING_MODEL, "prompt": chunk.content}
                        )
                        if response.status_code == 200:
                            data = response.json()
                            embeddings.append(data.get("embedding"))
                        else:
                            embeddings.append(None)
                except Exception as emb_err:
                    logger.warning("Embedding error for chunk {}: {}", i, emb_err)
                    embeddings.append(None)
            successful = sum(1 for e in embeddings if e is not None)
            logger.info("Generated {}/{} embeddings", successful, len(chunks))

            # 6. Delete existing chunks
            await conn.execute(
                "DELETE FROM document_chunks WHERE document_id = $1",
                document_id
            )

            # 7. Insert new chunks
            await conn.execute(
                "UPDATE documents SET processing_step = $1, processing_progress = $2 WHERE document_id = $3",
                'storing', 90, document_id
            )
            logger.info("Storing chunks")
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                import uuid
                chunk_id = uuid.uuid4()
                embedding_str = embedding_to_pgvector(embedding) if embedding else None
                # Truncate section_title to 500 chars to fit VARCHAR(500)
                section_title = chunk.section_title[:500] if chunk.section_title else None
                await conn.execute(
                    """
                    INSERT INTO document_chunks
                    (chunk_id, document_id, chunk_index, content, page_number, section_title, token_count, embedding)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::vector)
                    """,
                    chunk_id, document_id, i, chunk.content, chunk.page_number,
                    section_title, chunk.token_count, embedding_str
                )

            # 8. Update document as completed
            await conn.execute(
                """
                UPDATE documents
                SET processing_status = $1, processing_step = $2, processing_progress = $3,
                    page_count = $4, total_chunks = $5, processed_at = $6
                WHERE document_id = $7
                """,
                'completed', 'completed', 100, page_count, len(chunks), datetime.now(), document_id
            )

            logger.info("Document processed: {} — pages={}, chunks={}", original_filename, page_count, len(chunks))

        except Exception as e:
            logger.exception("Processing error: {}", e)
            await conn.execute(
                "UPDATE documents SET processing_status = $1, processing_error = $2 WHERE document_id = $3",
                'failed', str(e)[:500], document_id
            )
        finally:
            await conn.close()

    # Run in new event loop
    try:
        asyncio.run(_process_with_own_connection())
    except Exception as e:
        logger.exception("Background task failed: {}", e)


# ============================================================================
# SINGLETON ACCESS (delegates to ServiceContainer)
# ============================================================================

def get_document_service() -> DocumentService:
    """Get DocumentService via the global ServiceContainer"""
    from app.core.container import get_container
    return get_container().document
