"""
Document Entity
Domain model for document management with chunks and embeddings
Pattern from AngelaAI
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4


class ProcessingStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStep(str, Enum):
    """Document processing step"""
    PENDING = "pending"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"


class FileType(str, Enum):
    """Supported file types"""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    XLSX = "xlsx"
    XLS = "xls"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"


@dataclass
class DocumentChunk:
    """Document chunk with embedding"""

    content: str
    chunk_index: int
    document_id: UUID
    chunk_id: UUID = field(default_factory=uuid4)
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    token_count: Optional[int] = None
    embedding: Optional[List[float]] = None
    embedding_model: str = "bge-m3"
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "chunk_id": str(self.chunk_id),
            "document_id": str(self.document_id),
            "chunk_index": self.chunk_index,
            "content": self.content,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "token_count": self.token_count,
            "embedding_model": self.embedding_model,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Document:
    """Document domain entity with validation"""

    filename: str
    original_filename: str
    file_type: FileType
    document_id: UUID = field(default_factory=uuid4)
    uploaded_by: Optional[UUID] = None
    file_size_bytes: Optional[int] = None
    file_path: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    page_count: Optional[int] = None
    language: str = "th"
    tags: List[str] = field(default_factory=list)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_step: ProcessingStep = ProcessingStep.PENDING
    processing_progress: int = 0
    processing_error: Optional[str] = None
    total_chunks: int = 0
    is_deleted: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None

    # Chunks (not stored in main table, loaded separately)
    chunks: List[DocumentChunk] = field(default_factory=list)

    def __post_init__(self):
        """Validate entity after initialization"""
        self._validate()

    def _validate(self):
        """Validate document data"""
        if not self.filename:
            raise ValueError("Filename is required")
        if not self.original_filename:
            raise ValueError("Original filename is required")

    def start_processing(self) -> None:
        """Mark document as processing"""
        self.processing_status = ProcessingStatus.PROCESSING
        self.processing_error = None

    def complete_processing(self, chunk_count: int) -> None:
        """Mark document as completed"""
        self.processing_status = ProcessingStatus.COMPLETED
        self.total_chunks = chunk_count
        self.processed_at = datetime.now()

    def fail_processing(self, error: str) -> None:
        """Mark document as failed"""
        self.processing_status = ProcessingStatus.FAILED
        self.processing_error = error

    def soft_delete(self) -> None:
        """Soft delete document"""
        self.is_deleted = True

    def add_tag(self, tag: str) -> None:
        """Add a tag to document"""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from document"""
        if tag in self.tags:
            self.tags.remove(tag)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "document_id": str(self.document_id),
            "uploaded_by": str(self.uploaded_by) if self.uploaded_by else None,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type.value,
            "file_size_bytes": self.file_size_bytes,
            "file_path": self.file_path,
            "title": self.title,
            "description": self.description,
            "page_count": self.page_count,
            "language": self.language,
            "tags": self.tags,
            "processing_status": self.processing_status.value,
            "processing_step": self.processing_step.value if self.processing_step else "pending",
            "processing_progress": self.processing_progress,
            "processing_error": self.processing_error,
            "total_chunks": self.total_chunks,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        """Create Document from dictionary"""
        return cls(
            document_id=UUID(data["document_id"]) if isinstance(data.get("document_id"), str) else data.get("document_id", uuid4()),
            uploaded_by=UUID(data["uploaded_by"]) if data.get("uploaded_by") else None,
            filename=data["filename"],
            original_filename=data["original_filename"],
            file_type=FileType(data["file_type"]) if isinstance(data.get("file_type"), str) else data.get("file_type"),
            file_size_bytes=data.get("file_size_bytes"),
            file_path=data.get("file_path"),
            title=data.get("title"),
            description=data.get("description"),
            page_count=data.get("page_count"),
            language=data.get("language", "th"),
            tags=data.get("tags", []),
            processing_status=ProcessingStatus(data.get("processing_status", "pending")),
            processing_step=ProcessingStep(data.get("processing_step", "pending")) if data.get("processing_step") else ProcessingStep.PENDING,
            processing_progress=data.get("processing_progress", 0),
            processing_error=data.get("processing_error"),
            total_chunks=data.get("total_chunks", 0),
            is_deleted=data.get("is_deleted", False),
            created_at=data.get("created_at", datetime.now()),
            processed_at=data.get("processed_at"),
        )

    @classmethod
    def create_from_upload(
        cls,
        original_filename: str,
        file_type: str,
        file_size_bytes: int,
        uploaded_by: Optional[UUID] = None
    ) -> "Document":
        """Factory method to create document from upload"""
        import os
        from uuid import uuid4

        doc_id = uuid4()
        ext = os.path.splitext(original_filename)[1].lower().lstrip(".")

        return cls(
            document_id=doc_id,
            uploaded_by=uploaded_by,
            filename=f"{doc_id}.{ext}",
            original_filename=original_filename,
            file_type=FileType(ext),
            file_size_bytes=file_size_bytes,
            title=os.path.splitext(original_filename)[0],
        )
