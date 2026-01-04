"""
CogniFy Services Module

Services:
- EmbeddingService: Singleton, cached, fallback embedding generation
- ChunkingService: Semantic text chunking with overlap
- DocumentService: Document processing pipeline
- RAGService: Vector, BM25, and Hybrid search with RRF
- LLMService: Ollama + OpenAI with streaming
- ChatService: RAG + LLM orchestration
- HyDEService: Hypothetical Document Embedding for better retrieval
- RerankerService: LLM-based result re-ranking

Created with love by Angela & David - 4 January 2026
"""

from app.services.embedding_service import (
    EmbeddingService,
    get_embedding_service,
    shutdown_embedding_service,
    build_embedding_text,
)
from app.services.hyde_service import (
    HyDEService,
    get_hyde_service,
    shutdown_hyde_service,
    HyDEResult,
)
from app.services.reranker_service import (
    RerankerService,
    get_reranker_service,
    shutdown_reranker_service,
    RerankResult,
    RerankScore,
)
from app.services.chunking_service import (
    ChunkingService,
    get_chunking_service,
    Chunk,
)
from app.services.document_service import (
    DocumentService,
    get_document_service,
    process_document_background,
    TextExtractor,
)
from app.services.rag_service import (
    RAGService,
    get_rag_service,
    RAGSettings,
    SearchMethod,
    SimilarityMethod,
    SearchResult,
)
from app.services.llm_service import (
    LLMService,
    get_llm_service,
    shutdown_llm_service,
    LLMConfig,
    LLMProvider,
    Message,
    MessageRole,
    LLMResponse,
    StreamChunk,
)
from app.services.chat_service import (
    ChatService,
    get_chat_service,
    ChatRequest,
    ChatResponse,
    Conversation,
    ChatMessage,
    PromptTemplates,
)

__all__ = [
    # Embedding
    "EmbeddingService",
    "get_embedding_service",
    "shutdown_embedding_service",
    "build_embedding_text",
    # HyDE
    "HyDEService",
    "get_hyde_service",
    "shutdown_hyde_service",
    "HyDEResult",
    # Reranker
    "RerankerService",
    "get_reranker_service",
    "shutdown_reranker_service",
    "RerankResult",
    "RerankScore",
    # Chunking
    "ChunkingService",
    "get_chunking_service",
    "Chunk",
    # Document
    "DocumentService",
    "get_document_service",
    "process_document_background",
    "TextExtractor",
    # RAG
    "RAGService",
    "get_rag_service",
    "RAGSettings",
    "SearchMethod",
    "SimilarityMethod",
    "SearchResult",
    # LLM
    "LLMService",
    "get_llm_service",
    "shutdown_llm_service",
    "LLMConfig",
    "LLMProvider",
    "Message",
    "MessageRole",
    "LLMResponse",
    "StreamChunk",
    # Chat
    "ChatService",
    "get_chat_service",
    "ChatRequest",
    "ChatResponse",
    "Conversation",
    "ChatMessage",
    "PromptTemplates",
]
