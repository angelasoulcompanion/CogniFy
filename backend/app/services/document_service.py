"""
CogniFy Document Service
Document processing pipeline: Extract → Chunk → Embed → Store
Now with OCR support for images and scanned PDFs!
Created with love by Angela & David - 1 January 2026
"""

import os
import asyncio
import logging
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.domain.entities.document import Document, DocumentChunk, ProcessingStatus, FileType
from app.infrastructure.repositories.document_repository import DocumentRepository, DocumentChunkRepository
from app.services.embedding_service import get_embedding_service
from app.services.chunking_service import get_chunking_service, Chunk

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extract text from various document formats"""

    @staticmethod
    async def extract_pdf(file_path: str) -> Tuple[str, int, List[Tuple[int, str]]]:
        """
        Extract text from PDF using PyMuPDF.

        Returns:
            Tuple of (full_text, page_count, [(page_num, page_text), ...])
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            pages: List[Tuple[int, str]] = []
            full_text_parts = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                pages.append((page_num + 1, text))
                full_text_parts.append(text)

            doc.close()

            full_text = "\n\n".join(full_text_parts)
            return full_text, len(pages), pages

        except ImportError:
            print("⚠️ PyMuPDF not installed. Install with: pip install PyMuPDF")
            raise
        except Exception as e:
            print(f"❌ PDF extraction error: {e}")
            raise

    @staticmethod
    async def extract_docx(file_path: str) -> Tuple[str, int, List[Tuple[int, str]]]:
        """
        Extract text from DOCX using python-docx.

        Returns:
            Tuple of (full_text, page_count, [(page_num, page_text), ...])
        """
        try:
            from docx import Document as DocxDocument

            doc = DocxDocument(file_path)
            paragraphs = []

            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)

            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        paragraphs.append(" | ".join(row_text))

            full_text = "\n\n".join(paragraphs)

            # DOCX doesn't have clear page breaks, estimate 1 page per 3000 chars
            estimated_pages = max(1, len(full_text) // 3000)
            pages = [(1, full_text)]  # Treat as single page

            return full_text, estimated_pages, pages

        except ImportError:
            print("⚠️ python-docx not installed. Install with: pip install python-docx")
            raise
        except Exception as e:
            print(f"❌ DOCX extraction error: {e}")
            raise

    @staticmethod
    async def extract_txt(file_path: str) -> Tuple[str, int, List[Tuple[int, str]]]:
        """
        Extract text from plain text file.

        Returns:
            Tuple of (full_text, page_count, [(page_num, page_text), ...])
        """
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'tis-620', 'cp874', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        full_text = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Could not decode file with any encoding: {encodings}")

            # Estimate pages (1 page per 3000 chars)
            estimated_pages = max(1, len(full_text) // 3000)
            pages = [(1, full_text)]

            return full_text, estimated_pages, pages

        except Exception as e:
            print(f"❌ TXT extraction error: {e}")
            raise

    @staticmethod
    async def extract_xlsx(file_path: str) -> Tuple[str, int, List[Tuple[int, str]]]:
        """
        Extract text from Excel file.

        Returns:
            Tuple of (full_text, sheet_count, [(sheet_num, sheet_text), ...])
        """
        try:
            from openpyxl import load_workbook

            wb = load_workbook(file_path, read_only=True, data_only=True)
            sheets: List[Tuple[int, str]] = []
            full_text_parts = []

            for sheet_num, sheet_name in enumerate(wb.sheetnames, 1):
                ws = wb[sheet_name]
                sheet_lines = [f"## Sheet: {sheet_name}\n"]

                for row in ws.iter_rows(values_only=True):
                    row_values = [str(cell) if cell is not None else "" for cell in row]
                    if any(v.strip() for v in row_values):
                        sheet_lines.append(" | ".join(row_values))

                sheet_text = "\n".join(sheet_lines)
                sheets.append((sheet_num, sheet_text))
                full_text_parts.append(sheet_text)

            wb.close()

            full_text = "\n\n".join(full_text_parts)
            return full_text, len(sheets), sheets

        except ImportError:
            print("⚠️ openpyxl not installed. Install with: pip install openpyxl")
            raise
        except Exception as e:
            print(f"❌ Excel extraction error: {e}")
            raise

    @staticmethod
    async def extract_image(file_path: str) -> Tuple[str, int, List[Tuple[int, str]]]:
        """
        Extract text from image using OCR.

        Supports: PNG, JPG, JPEG
        Uses multiple OCR engines with fallback (Tesseract → PaddleOCR → EasyOCR)

        Returns:
            Tuple of (full_text, page_count, [(page_num, page_text), ...])
        """
        try:
            from app.services.ocr_service import get_ocr_service

            ocr_service = get_ocr_service()
            result = await ocr_service.extract_text(file_path, preprocess=True)

            full_text = result.text
            confidence = result.confidence

            logger.info(f"🔍 OCR completed: {len(full_text)} chars, {confidence:.1%} confidence, engine: {result.engine}")

            # Return as single page
            pages = [(1, full_text)]
            return full_text, 1, pages

        except ImportError as e:
            logger.warning(f"⚠️ OCR dependencies not installed: {e}")
            raise ValueError(
                "OCR is not available. Install with: pip install pytesseract pillow opencv-python\n"
                "Also install Tesseract: brew install tesseract tesseract-lang"
            )
        except Exception as e:
            logger.error(f"❌ Image OCR error: {e}")
            raise

    @staticmethod
    async def extract_pdf_with_ocr(file_path: str) -> Tuple[str, int, List[Tuple[int, str]]]:
        """
        Extract text from scanned PDF using OCR.

        This is used when regular PDF extraction returns no text (scanned document).

        Returns:
            Tuple of (full_text, page_count, [(page_num, page_text), ...])
        """
        try:
            from app.services.ocr_service import get_ocr_service

            ocr_service = get_ocr_service()
            full_text, page_results = await ocr_service.extract_from_pdf_images(file_path, dpi=300)

            pages = [(p['page'], p['text']) for p in page_results]

            avg_confidence = sum(p['confidence'] for p in page_results) / len(page_results) if page_results else 0
            logger.info(f"🔍 PDF OCR completed: {len(pages)} pages, {avg_confidence:.1%} avg confidence")

            return full_text, len(pages), pages

        except ImportError as e:
            logger.warning(f"⚠️ OCR dependencies not installed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ PDF OCR error: {e}")
            raise

    @classmethod
    async def extract(
        cls,
        file_path: str,
        file_type: FileType,
        use_ocr_fallback: bool = True,
    ) -> Tuple[str, int, List[Tuple[int, str]]]:
        """
        Extract text from document based on file type.

        Args:
            file_path: Path to the file
            file_type: Type of file
            use_ocr_fallback: If True, use OCR for scanned PDFs with no text

        Returns:
            Tuple of (full_text, page_count, [(page_num, page_text), ...])
        """
        # Image files - always use OCR
        if file_type in (FileType.PNG, FileType.JPG, FileType.JPEG):
            logger.info(f"🖼️ Processing image file with OCR: {file_path}")
            return await cls.extract_image(file_path)

        # PDF files - try text extraction first, fallback to OCR
        if file_type == FileType.PDF:
            full_text, page_count, pages = await cls.extract_pdf(file_path)

            # Check if PDF is scanned (no text)
            if use_ocr_fallback and not full_text.strip():
                logger.info(f"📄 PDF appears to be scanned, using OCR fallback...")
                return await cls.extract_pdf_with_ocr(file_path)

            return full_text, page_count, pages

        # Other document types
        if file_type in (FileType.DOCX, FileType.DOC):
            return await cls.extract_docx(file_path)
        elif file_type == FileType.TXT:
            return await cls.extract_txt(file_path)
        elif file_type in (FileType.XLSX, FileType.XLS):
            return await cls.extract_xlsx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")


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
            print(f"📄 Extracting text from {document.original_filename}...")
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
            print(f"✂️ Chunking text into segments...")
            if len(pages) > 1:
                chunks = self.chunking_service.chunk_by_pages(pages)
            else:
                chunks = self.chunking_service.chunk_text(full_text)

            print(f"   Created {len(chunks)} chunks")

            if on_progress:
                await on_progress("embedding", 40)

            # 3. Generate embeddings
            print(f"🧠 Generating embeddings...")
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.get_embeddings_batch(
                chunk_texts,
                batch_size=5
            )

            # Count successful embeddings
            successful = sum(1 for e in embeddings if e is not None)
            print(f"   Generated {successful}/{len(chunks)} embeddings")

            if on_progress:
                await on_progress("storing", 80)

            # 4. Create DocumentChunk entities
            print(f"💾 Storing chunks...")
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

            print(f"✅ Document processed successfully: {document.original_filename}")
            print(f"   Pages: {page_count}, Chunks: {len(document_chunks)}")

            return await self.document_repo.get_by_id(document_id)

        except Exception as e:
            print(f"❌ Document processing error: {e}")
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

async def process_document_background(document_id: UUID) -> None:
    """
    Background task to process a document.
    Can be called from FastAPI BackgroundTasks.
    """
    service = DocumentService()
    try:
        await service.process_document(document_id)
    except Exception as e:
        print(f"❌ Background processing failed for {document_id}: {e}")


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    """Get global DocumentService instance"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
