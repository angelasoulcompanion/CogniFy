"""
CogniFy Entity Tests
Created with love by Angela & David - 1 January 2026
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.domain.entities.user import User, UserRole
from app.domain.entities.document import Document, DocumentChunk, FileType, ProcessingStatus


class TestUserEntity:
    """Test User entity"""

    @pytest.mark.unit
    def test_create_user(self):
        """Test user creation"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
        )

        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.full_name == "Test User"
        assert user.role == UserRole.USER
        assert user.is_active is True

    @pytest.mark.unit
    def test_user_with_admin_role(self):
        """Test user with admin role"""
        user = User(
            email="admin@example.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
        )

        assert user.role == UserRole.ADMIN

    @pytest.mark.unit
    def test_user_to_dict(self):
        """Test user to_dict method"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
        )

        data = user.to_dict()

        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["role"] == "user"
        assert "password_hash" not in data

    @pytest.mark.unit
    def test_user_validation_empty_email(self):
        """Test user validation with empty email"""
        with pytest.raises((ValueError, Exception)):
            User(email="", password_hash="hashed")

    @pytest.mark.unit
    def test_user_validation_empty_password(self):
        """Test user validation with empty password"""
        with pytest.raises((ValueError, Exception)):
            User(email="test@example.com", password_hash="")


class TestDocumentEntity:
    """Test Document entity"""

    @pytest.mark.unit
    def test_create_document(self):
        """Test document creation"""
        doc = Document(
            filename="doc123.pdf",
            original_filename="test.pdf",
            file_type=FileType.PDF,
        )

        assert doc.filename == "doc123.pdf"
        assert doc.original_filename == "test.pdf"
        assert doc.file_type == FileType.PDF
        assert doc.processing_status == ProcessingStatus.PENDING

    @pytest.mark.unit
    def test_document_start_processing(self):
        """Test starting document processing"""
        doc = Document(
            filename="doc.pdf",
            original_filename="test.pdf",
            file_type=FileType.PDF,
        )

        doc.start_processing()

        assert doc.processing_status == ProcessingStatus.PROCESSING
        assert doc.processing_error is None

    @pytest.mark.unit
    def test_document_complete_processing(self):
        """Test completing document processing"""
        doc = Document(
            filename="doc.pdf",
            original_filename="test.pdf",
            file_type=FileType.PDF,
        )

        doc.complete_processing(chunk_count=10)

        assert doc.processing_status == ProcessingStatus.COMPLETED
        assert doc.total_chunks == 10
        assert doc.processed_at is not None

    @pytest.mark.unit
    def test_document_fail_processing(self):
        """Test failing document processing"""
        doc = Document(
            filename="doc.pdf",
            original_filename="test.pdf",
            file_type=FileType.PDF,
        )

        doc.fail_processing("Test error")

        assert doc.processing_status == ProcessingStatus.FAILED
        assert doc.processing_error == "Test error"

    @pytest.mark.unit
    def test_document_soft_delete(self):
        """Test soft delete"""
        doc = Document(
            filename="doc.pdf",
            original_filename="test.pdf",
            file_type=FileType.PDF,
        )

        doc.soft_delete()

        assert doc.is_deleted is True

    @pytest.mark.unit
    def test_document_tags(self):
        """Test document tags"""
        doc = Document(
            filename="doc.pdf",
            original_filename="test.pdf",
            file_type=FileType.PDF,
        )

        doc.add_tag("important")
        doc.add_tag("finance")

        assert "important" in doc.tags
        assert "finance" in doc.tags

        doc.remove_tag("important")
        assert "important" not in doc.tags

    @pytest.mark.unit
    def test_document_to_dict(self):
        """Test document to_dict method"""
        doc = Document(
            filename="doc.pdf",
            original_filename="test.pdf",
            file_type=FileType.PDF,
            title="Test Document",
        )

        data = doc.to_dict()

        assert data["filename"] == "doc.pdf"
        assert data["original_filename"] == "test.pdf"
        assert data["file_type"] == "pdf"
        assert data["title"] == "Test Document"

    @pytest.mark.unit
    def test_document_create_from_upload(self):
        """Test factory method"""
        doc = Document.create_from_upload(
            original_filename="my_report.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            uploaded_by=uuid4(),
        )

        assert doc.original_filename == "my_report.pdf"
        assert doc.file_type == FileType.PDF
        assert doc.file_size_bytes == 1024
        assert doc.title == "my_report"


class TestDocumentChunkEntity:
    """Test DocumentChunk entity"""

    @pytest.mark.unit
    def test_create_chunk(self):
        """Test chunk creation"""
        doc_id = uuid4()
        chunk = DocumentChunk(
            document_id=doc_id,
            content="This is test content",
            chunk_index=0,
            page_number=1,
        )

        assert chunk.document_id == doc_id
        assert chunk.content == "This is test content"
        assert chunk.chunk_index == 0
        assert chunk.page_number == 1

    @pytest.mark.unit
    def test_chunk_to_dict(self):
        """Test chunk to_dict method"""
        doc_id = uuid4()
        chunk = DocumentChunk(
            document_id=doc_id,
            content="Test content",
            chunk_index=5,
            token_count=10,
        )

        data = chunk.to_dict()

        assert data["content"] == "Test content"
        assert data["chunk_index"] == 5
        assert data["token_count"] == 10


class TestFileType:
    """Test FileType enum"""

    @pytest.mark.unit
    def test_file_types(self):
        """Test all file types"""
        assert FileType.PDF.value == "pdf"
        assert FileType.DOCX.value == "docx"
        assert FileType.TXT.value == "txt"
        assert FileType.XLSX.value == "xlsx"
        assert FileType.PNG.value == "png"
        assert FileType.JPG.value == "jpg"
        assert FileType.JPEG.value == "jpeg"


class TestProcessingStatus:
    """Test ProcessingStatus enum"""

    @pytest.mark.unit
    def test_processing_statuses(self):
        """Test all processing statuses"""
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"
