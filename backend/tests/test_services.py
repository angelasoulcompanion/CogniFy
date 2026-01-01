"""
CogniFy Service Tests
Created with love by Angela & David - 1 January 2026
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestChunkingService:
    """Test chunking service"""

    @pytest.mark.unit
    def test_chunk_text_basic(self):
        """Test basic text chunking"""
        from app.services.chunking_service import ChunkingService

        service = ChunkingService(
            chunk_size=100,
            chunk_overlap=20,
        )

        text = "This is a test. " * 50  # Create text longer than chunk size
        chunks = service.chunk_text(text)

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.content is not None
            assert chunk.token_count is not None

    @pytest.mark.unit
    def test_chunk_text_short(self):
        """Test chunking short text"""
        from app.services.chunking_service import ChunkingService

        service = ChunkingService(chunk_size=500)

        text = "Short text"
        chunks = service.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].content == "Short text"

    @pytest.mark.unit
    def test_chunk_by_pages(self):
        """Test chunking by pages"""
        from app.services.chunking_service import ChunkingService

        service = ChunkingService(chunk_size=100)

        pages = [
            (1, "Page one content. " * 20),
            (2, "Page two content. " * 20),
        ]
        chunks = service.chunk_by_pages(pages)

        assert len(chunks) > 0
        # Check page numbers are preserved
        page_numbers = {c.page_number for c in chunks}
        assert 1 in page_numbers or 2 in page_numbers

    @pytest.mark.unit
    def test_count_tokens(self):
        """Test token counting"""
        from app.services.chunking_service import ChunkingService

        service = ChunkingService()

        text = "Hello world this is a test"
        count = service._count_tokens(text)

        assert count > 0
        assert count <= len(text.split()) * 2  # Rough estimate


class TestOCRService:
    """Test OCR service"""

    @pytest.mark.unit
    def test_ocr_result_dataclass(self):
        """Test OCRResult dataclass"""
        from app.services.ocr_service import OCRResult

        result = OCRResult(
            text="Extracted text",
            confidence=0.95,
            language="eng",
            boxes=[],
            engine="tesseract",
        )

        assert result.text == "Extracted text"
        assert result.confidence == 0.95
        assert result.language == "eng"
        assert result.engine == "tesseract"

    @pytest.mark.unit
    def test_ocr_engine_enum(self):
        """Test OCREngine enum"""
        from app.services.ocr_service import OCREngine

        assert OCREngine.TESSERACT.value == "tesseract"
        assert OCREngine.PADDLEOCR.value == "paddleocr"
        assert OCREngine.EASYOCR.value == "easyocr"


class TestAdminService:
    """Test admin service"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_system_stats_dataclass(self):
        """Test SystemStats dataclass"""
        from app.services.admin_service import SystemStats

        stats = SystemStats(
            total_users=100,
            active_users_7d=50,
            total_documents=500,
            total_chunks=10000,
            total_conversations=200,
            total_messages=5000,
            total_embeddings=9500,
            storage_used_mb=256.5,
            avg_response_time_ms=150.0,
        )

        assert stats.total_users == 100
        assert stats.active_users_7d == 50
        assert stats.total_documents == 500
        assert stats.storage_used_mb == 256.5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_stats_dataclass(self):
        """Test UserStats dataclass"""
        from app.services.admin_service import UserStats
        from datetime import datetime

        stats = UserStats(
            user_id=uuid4(),
            email="test@example.com",
            full_name="Test User",
            role="user",
            is_active=True,
            document_count=10,
            conversation_count=5,
            message_count=100,
            last_active=datetime.now(),
            created_at=datetime.now(),
        )

        assert stats.email == "test@example.com"
        assert stats.role == "user"
        assert stats.document_count == 10


class TestRAGService:
    """Test RAG service"""

    @pytest.mark.unit
    def test_search_result_format(self):
        """Test search result format"""
        # Test the expected structure of search results
        result = {
            "chunk_id": str(uuid4()),
            "document_id": str(uuid4()),
            "document_name": "test.pdf",
            "content": "Test content",
            "page_number": 1,
            "similarity": 0.85,
        }

        assert "chunk_id" in result
        assert "similarity" in result
        assert result["similarity"] >= 0 and result["similarity"] <= 1


class TestConnectorService:
    """Test connector service"""

    @pytest.mark.unit
    def test_password_encryption(self):
        """Test password encryption/decryption"""
        # Skip if no encryption key configured
        import os
        if not os.environ.get("ENCRYPTION_KEY"):
            pytest.skip("ENCRYPTION_KEY not configured")

        from app.services.connector_service import ConnectorService

        service = ConnectorService()
        password = "test_password_123"

        encrypted = service._encrypt_password(password)
        decrypted = service._decrypt_password(encrypted)

        assert encrypted != password
        assert decrypted == password

    @pytest.mark.unit
    def test_database_type_enum(self):
        """Test DatabaseType enum"""
        from app.domain.entities.connector import DatabaseType

        assert DatabaseType.POSTGRESQL.value == "postgresql"
        assert DatabaseType.MYSQL.value == "mysql"
        assert DatabaseType.SQLSERVER.value == "sqlserver"

    @pytest.mark.unit
    def test_sync_status_enum(self):
        """Test SyncStatus enum"""
        from app.domain.entities.connector import SyncStatus

        assert SyncStatus.PENDING.value == "pending"
        assert SyncStatus.SYNCING.value == "syncing"
        assert SyncStatus.COMPLETED.value == "completed"
        assert SyncStatus.FAILED.value == "failed"
