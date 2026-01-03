"""
Documents API Endpoints
Upload, list, delete, and manage documents
"""

from typing import Optional, List
from uuid import UUID
import os
import aiofiles
from datetime import datetime

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, BackgroundTasks

from app.core.config import settings
from app.core.security import get_current_user, get_current_user_optional, TokenPayload
from app.infrastructure.repositories.document_repository import DocumentRepository, DocumentChunkRepository
from app.domain.entities.document import Document, ProcessingStatus
from app.services.document_service import process_document_background, get_document_service


router = APIRouter()

# Initialize repositories
document_repo = DocumentRepository()
chunk_repo = DocumentChunkRepository()
document_service = get_document_service()


# Response Models
class DocumentResponse(BaseModel):
    """Document response model"""
    document_id: str
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: Optional[int]
    title: Optional[str]
    description: Optional[str]
    page_count: Optional[int]
    language: str
    tags: List[str]
    processing_status: str
    processing_step: Optional[str]
    processing_progress: Optional[int]
    processing_error: Optional[str]
    total_chunks: int
    created_at: str
    processed_at: Optional[str]


class DocumentListResponse(BaseModel):
    """Paginated document list response"""
    documents: List[DocumentResponse]
    total: int
    skip: int
    limit: int


class ChunkResponse(BaseModel):
    """Document chunk response"""
    chunk_id: str
    chunk_index: int
    content: str
    page_number: Optional[int]
    section_title: Optional[str]
    token_count: Optional[int]


class UploadResponse(BaseModel):
    """Upload response"""
    document_id: str
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    processing_status: str
    message: str


def _document_to_response(doc: Document) -> DocumentResponse:
    """Convert Document entity to response model"""
    return DocumentResponse(
        document_id=str(doc.document_id),
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_type=doc.file_type.value,
        file_size_bytes=doc.file_size_bytes,
        title=doc.title,
        description=doc.description,
        page_count=doc.page_count,
        language=doc.language,
        tags=doc.tags,
        processing_status=doc.processing_status.value,
        processing_step=doc.processing_step.value if doc.processing_step else None,
        processing_progress=doc.processing_progress,
        processing_error=doc.processing_error,
        total_chunks=doc.total_chunks,
        created_at=doc.created_at.isoformat(),
        processed_at=doc.processed_at.isoformat() if doc.processed_at else None,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    List all documents with pagination.
    """
    documents = await document_repo.get_all_active(skip=skip, limit=limit)
    total = await document_repo.count()

    return DocumentListResponse(
        documents=[_document_to_response(doc) for doc in documents],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Get document by ID.
    """
    document = await document_repo.get_by_id(document_id)

    if document is None or document.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return _document_to_response(document)


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Upload a new document.
    Document will be processed in background.
    """
    # Validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {ext} not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Check file size
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    # Create document entity
    user_id = UUID(current_user.sub) if current_user else None
    document = Document.create_from_upload(
        original_filename=file.filename,
        file_type=ext.lstrip("."),
        file_size_bytes=file_size,
        uploaded_by=user_id,
    )

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Save file to disk
    file_path = os.path.join(settings.UPLOAD_DIR, document.filename)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    document.file_path = file_path

    # Save to database
    document = await document_repo.create(document)

    # Add background task for document processing
    background_tasks.add_task(process_document_background, document.document_id)

    return UploadResponse(
        document_id=str(document.document_id),
        filename=document.filename,
        original_filename=document.original_filename,
        file_type=document.file_type.value,
        file_size_bytes=document.file_size_bytes,
        processing_status=document.processing_status.value,
        message="Document uploaded successfully. Processing will start shortly.",
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Delete a document (soft delete).
    """
    document = await document_repo.get_by_id(document_id)

    if document is None or document.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Soft delete
    await document_repo.soft_delete(document_id)

    return None


@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
async def get_document_chunks(
    document_id: UUID,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Get all chunks for a document.
    """
    document = await document_repo.get_by_id(document_id)

    if document is None or document.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    chunks = await chunk_repo.get_by_document(document_id)

    return [
        ChunkResponse(
            chunk_id=str(chunk.chunk_id),
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            page_number=chunk.page_number,
            section_title=chunk.section_title,
            token_count=chunk.token_count,
        )
        for chunk in chunks
    ]


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Reprocess a document (delete chunks and re-extract).
    """
    document = await document_repo.get_by_id(document_id)

    if document is None or document.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete existing chunks
    await chunk_repo.delete_by_document(document_id)

    # Reset status
    await document_repo.update_status(document_id, ProcessingStatus.PENDING)

    # Add background task for document processing
    background_tasks.add_task(process_document_background, document_id)

    # Get updated document
    document = await document_repo.get_by_id(document_id)

    return _document_to_response(document)


@router.patch("/{document_id}")
async def update_document(
    document_id: UUID,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Update document metadata.
    """
    document = await document_repo.get_by_id(document_id)

    if document is None or document.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if title is not None:
        document.title = title
    if description is not None:
        document.description = description
    if tags is not None:
        document.tags = tags

    document = await document_repo.update(document)

    return _document_to_response(document)


@router.get("/{document_id}/stats")
async def get_document_stats(
    document_id: UUID,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Get document processing statistics.
    """
    document = await document_repo.get_by_id(document_id)

    if document is None or document.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    try:
        stats = await document_service.get_document_stats(document_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{document_id}/process")
async def process_document_now(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Trigger document processing immediately.
    """
    document = await document_repo.get_by_id(document_id)

    if document is None or document.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document.processing_status == ProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already being processed"
        )

    # Add background task
    background_tasks.add_task(process_document_background, document_id)

    return {
        "message": "Processing started",
        "document_id": str(document_id),
        "status": "processing"
    }
