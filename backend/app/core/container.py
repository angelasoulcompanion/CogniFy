"""
CogniFy Service Container
Centralized dependency management — replaces module-level singletons
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.core.logging import logger

if TYPE_CHECKING:
    from app.services.admin_service import AdminService
    from app.services.chat_service import ChatService
    from app.services.chunking_service import ChunkingService
    from app.services.connector_service import ConnectorService
    from app.services.document_service import DocumentService
    from app.services.embedding_service import EmbeddingService
    from app.services.hyde_service import HyDEService
    from app.services.llm_service import LLMService
    from app.services.ocr_service import OCRService
    from app.services.prompt_service import PromptService
    from app.services.rag_service import RAGService
    from app.services.reranker_service import RerankerService
    from app.services.token_service import TokenService


class ServiceContainer:
    """
    Lazy-initializing service container.

    Usage in FastAPI routes:
        container = Depends(get_container)
        container.embedding  # lazy-creates EmbeddingService once
    """

    def __init__(self) -> None:
        self._embedding: Optional["EmbeddingService"] = None
        self._llm: Optional["LLMService"] = None
        self._rag: Optional["RAGService"] = None
        self._hyde: Optional["HyDEService"] = None
        self._reranker: Optional["RerankerService"] = None
        self._document: Optional["DocumentService"] = None
        self._chat: Optional["ChatService"] = None
        self._ocr: Optional["OCRService"] = None
        self._chunking: Optional["ChunkingService"] = None
        self._admin: Optional["AdminService"] = None
        self._prompt: Optional["PromptService"] = None
        self._connector: Optional["ConnectorService"] = None
        self._token: Optional["TokenService"] = None

    # ----- Core services -----

    @property
    def embedding(self) -> "EmbeddingService":
        if self._embedding is None:
            from app.services.embedding_service import EmbeddingService
            self._embedding = EmbeddingService()
        return self._embedding

    @property
    def llm(self) -> "LLMService":
        if self._llm is None:
            from app.services.llm_service import LLMService
            self._llm = LLMService()
        return self._llm

    @property
    def rag(self) -> "RAGService":
        if self._rag is None:
            from app.services.rag_service import RAGService
            self._rag = RAGService()
        return self._rag

    @property
    def hyde(self) -> "HyDEService":
        if self._hyde is None:
            from app.services.hyde_service import HyDEService
            self._hyde = HyDEService()
        return self._hyde

    @property
    def reranker(self) -> "RerankerService":
        if self._reranker is None:
            from app.services.reranker_service import RerankerService
            self._reranker = RerankerService()
        return self._reranker

    @property
    def document(self) -> "DocumentService":
        if self._document is None:
            from app.services.document_service import DocumentService
            self._document = DocumentService()
        return self._document

    @property
    def chat(self) -> "ChatService":
        if self._chat is None:
            from app.services.chat_service import ChatService
            self._chat = ChatService()
        return self._chat

    @property
    def ocr(self) -> "OCRService":
        if self._ocr is None:
            from app.services.ocr_service import OCRService
            self._ocr = OCRService()
        return self._ocr

    @property
    def chunking(self) -> "ChunkingService":
        if self._chunking is None:
            from app.services.chunking_service import ChunkingService
            self._chunking = ChunkingService()
        return self._chunking

    @property
    def admin(self) -> "AdminService":
        if self._admin is None:
            from app.services.admin_service import AdminService
            self._admin = AdminService()
        return self._admin

    @property
    def prompt(self) -> "PromptService":
        if self._prompt is None:
            from app.services.prompt_service import PromptService
            self._prompt = PromptService()
        return self._prompt

    @property
    def connector(self) -> "ConnectorService":
        if self._connector is None:
            from app.services.connector_service import ConnectorService
            self._connector = ConnectorService()
        return self._connector

    @property
    def token(self) -> "TokenService":
        if self._token is None:
            from app.services.token_service import TokenService
            self._token = TokenService()
        return self._token

    # ----- Lifecycle -----

    async def shutdown(self) -> None:
        """Close all initialized services"""
        if self._embedding:
            await self._embedding.close()
        if self._llm:
            for provider in self._llm._providers.values():
                if hasattr(provider, "client"):
                    await provider.client.aclose()
        if self._hyde:
            await self._hyde.close()
        if self._reranker:
            await self._reranker.close()
        logger.info("Service container shut down")


# ---- Module-level singleton (the ONE singleton we allow) ----

_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """FastAPI dependency — returns the global ServiceContainer"""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


async def shutdown_container() -> None:
    """Shutdown the global container (called from app lifespan)"""
    global _container
    if _container:
        await _container.shutdown()
        _container = None
