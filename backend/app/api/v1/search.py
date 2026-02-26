"""
Search API Endpoints
Semantic and hybrid search for documents

Created with love by Angela & David - 1 January 2026
"""

import time
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_user, get_current_user_optional, TokenPayload
from app.core.exceptions import NotFoundError, ValidationError
from app.services.rag_service import (
    get_rag_service,
    RAGSettings,
    SearchMethod,
    SimilarityMethod,
)
from app.infrastructure.repositories.embedding_repository import get_embedding_repository
from app.api.helpers import rag_result_to_dict


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")
    threshold: float = Field(0.3, ge=0.0, le=1.0, description="Minimum similarity")
    similarity_method: str = Field("cosine", description="cosine, euclidean, dot")
    document_ids: Optional[List[str]] = Field(None, description="Filter by documents")
    include_content: bool = Field(True, description="Include chunk content")


class SearchResult(BaseModel):
    """Single search result"""
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    similarity: float
    highlight: Optional[str] = None
    # Hybrid search info
    vector_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    rrf_score: Optional[float] = None


class SearchResponse(BaseModel):
    """Search response"""
    query: str
    results: List[SearchResult]
    total: int
    search_time_ms: int
    search_method: str


class HybridSearchRequest(BaseModel):
    """Hybrid search request (BM25 + Vector)"""
    query: str = Field(..., min_length=1)
    limit: int = Field(10, ge=1, le=100)
    threshold: float = Field(0.3, ge=0.0, le=1.0)
    bm25_weight: float = Field(0.4, ge=0.0, le=1.0)
    vector_weight: float = Field(0.6, ge=0.0, le=1.0)
    document_ids: Optional[List[str]] = None
    rrf_k: int = Field(60, ge=1, le=100, description="RRF constant")


class BM25SearchRequest(BaseModel):
    """BM25 keyword search request"""
    query: str = Field(..., min_length=1)
    limit: int = Field(10, ge=1, le=100)
    document_ids: Optional[List[str]] = None


class ContextRequest(BaseModel):
    """Request to build RAG context"""
    query: str = Field(..., min_length=1)
    max_chunks: int = Field(10, ge=1, le=50)
    max_context_length: int = Field(8000, ge=1000, le=32000)
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0)
    search_method: str = Field("hybrid", description="vector, bm25, hybrid")
    document_ids: Optional[List[str]] = None


class ContextResponse(BaseModel):
    """RAG context response"""
    query: str
    context: str
    sources: List[SearchResult]
    total_sources: int
    context_length: int


# =============================================================================
# HELPERS
# =============================================================================

def _parse_search_params(body) -> tuple:
    """Extract common search parameters: doc_ids, user_id from request body + user."""
    doc_ids = [UUID(d) for d in body.document_ids] if body.document_ids else None
    return doc_ids


def _build_search_response(
    query: str,
    results: list,
    start_time: float,
    method: str,
    *,
    include_content: bool = True,
    content_truncate: Optional[int] = None,
) -> SearchResponse:
    """Build a SearchResponse from RAG results, eliminating repeated boilerplate."""
    search_time_ms = int((time.time() - start_time) * 1000)
    return SearchResponse(
        query=query,
        results=[
            SearchResult(**rag_result_to_dict(
                r,
                include_content=include_content,
                content_truncate=content_truncate,
            ))
            for r in results
        ],
        total=len(results),
        search_time_ms=search_time_ms,
        search_method=method,
    )


def _get_user_id(current_user: Optional[TokenPayload]) -> Optional[UUID]:
    return UUID(current_user.sub) if current_user else None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("", response_model=SearchResponse)
@limiter.limit("30/minute")
async def semantic_search(
    request: Request,
    body: SearchRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Semantic search using vector similarity (pgvector).

    Uses embeddings to find semantically similar content.
    """
    start_time = time.time()

    rag_service = get_rag_service()

    settings = RAGSettings(
        search_method=SearchMethod.VECTOR,
        similarity_method=SimilarityMethod(body.similarity_method),
        similarity_threshold=body.threshold,
        max_chunks=body.limit,
    )

    results = await rag_service.search(
        query=body.query,
        settings=settings,
        user_id=_get_user_id(current_user),
        document_ids=_parse_search_params(body),
    )

    return _build_search_response(
        body.query, results, start_time, "vector",
        include_content=body.include_content,
    )


@router.post("/hybrid", response_model=SearchResponse)
@limiter.limit("30/minute")
async def hybrid_search(
    request: Request,
    body: HybridSearchRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Hybrid search combining BM25 keyword search and vector similarity.

    Uses Reciprocal Rank Fusion (RRF) to merge results from both methods.
    """
    start_time = time.time()

    rag_service = get_rag_service()

    settings = RAGSettings(
        search_method=SearchMethod.HYBRID,
        similarity_threshold=body.threshold,
        max_chunks=body.limit,
        bm25_weight=body.bm25_weight,
        vector_weight=body.vector_weight,
        rrf_k=body.rrf_k,
    )

    results = await rag_service.search(
        query=body.query,
        settings=settings,
        user_id=_get_user_id(current_user),
        document_ids=_parse_search_params(body),
    )

    return _build_search_response(body.query, results, start_time, "hybrid")


@router.post("/bm25", response_model=SearchResponse)
@limiter.limit("30/minute")
async def bm25_search(
    request: Request,
    body: BM25SearchRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    BM25 keyword search using PostgreSQL full-text search.

    Good for exact keyword matching.
    """
    start_time = time.time()

    rag_service = get_rag_service()

    settings = RAGSettings(
        search_method=SearchMethod.BM25,
        max_chunks=body.limit,
    )

    results = await rag_service.search(
        query=body.query,
        settings=settings,
        user_id=_get_user_id(current_user),
        document_ids=_parse_search_params(body),
    )

    return _build_search_response(body.query, results, start_time, "bm25")


@router.post("/context", response_model=ContextResponse)
@limiter.limit("30/minute")
async def build_rag_context(
    request: Request,
    body: ContextRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Build context for RAG (Retrieval Augmented Generation).

    Returns formatted context string with source citations.
    """
    rag_service = get_rag_service()

    settings = RAGSettings(
        search_method=SearchMethod(body.search_method),
        similarity_threshold=body.similarity_threshold,
        max_chunks=body.max_chunks,
    )

    context, results = await rag_service.build_context(
        query=body.query,
        settings=settings,
        user_id=_get_user_id(current_user),
        document_ids=_parse_search_params(body),
        max_context_length=body.max_context_length,
    )

    return ContextResponse(
        query=body.query,
        context=context,
        sources=[
            SearchResult(**rag_result_to_dict(r, content_truncate=200))
            for r in results
        ],
        total_sources=len(results),
        context_length=len(context),
    )


@router.post("/similar/{chunk_id}", response_model=SearchResponse)
@limiter.limit("30/minute")
async def find_similar_chunks(
    request: Request,
    chunk_id: UUID,
    limit: int = 5,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Find chunks similar to a given chunk.

    Useful for "more like this" functionality.
    """
    start_time = time.time()

    embedding_repo = get_embedding_repository()

    # Get source chunk embedding
    from app.infrastructure.database import Database
    pool = await Database.get_pool()

    row = await pool.fetchrow(
        "SELECT embedding::text, document_id FROM document_chunks WHERE chunk_id = $1",
        str(chunk_id)
    )

    if not row:
        raise NotFoundError("Chunk not found")

    if not row["embedding"]:
        raise ValidationError("Chunk has no embedding")

    # Parse embedding
    embedding_str = row["embedding"].strip("[]")
    embedding = [float(x) for x in embedding_str.split(",")]

    # Find similar chunks (excluding the source)
    similar = await embedding_repo.find_similar_chunks(
        embedding=embedding,
        limit=limit + 1,  # Get one extra to filter out source
        threshold=0.3,
    )

    # Filter out the source chunk
    similar = [s for s in similar if s["chunk_id"] != str(chunk_id)][:limit]

    search_time_ms = int((time.time() - start_time) * 1000)

    return SearchResponse(
        query=f"similar_to:{chunk_id}",
        results=[
            SearchResult(
                chunk_id=s["chunk_id"],
                document_id=s["document_id"],
                document_name=s["document_title"] or s["document_filename"] or "Untitled",
                content=s["content"],
                page_number=s["page_number"],
                section_title=s["section_title"],
                similarity=s["similarity"],
            )
            for s in similar
        ],
        total=len(similar),
        search_time_ms=search_time_ms,
        search_method="vector",
    )


@router.get("/stats")
async def get_search_stats(
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get search/embedding statistics.
    """
    embedding_repo = get_embedding_repository()
    cache_stats = await embedding_repo.get_cache_stats()

    # Get chunk stats
    from app.infrastructure.database import Database
    pool = await Database.get_pool()

    chunk_stats = await pool.fetchrow("""
        SELECT
            COUNT(*) as total_chunks,
            COUNT(c.embedding) as chunks_with_embeddings,
            COUNT(DISTINCT c.document_id) as documents_indexed
        FROM document_chunks c
        JOIN documents d ON c.document_id = d.document_id
        WHERE d.is_deleted = false
          AND d.processing_status = 'completed'
    """)

    return {
        "chunks": {
            "total": chunk_stats["total_chunks"],
            "with_embeddings": chunk_stats["chunks_with_embeddings"],
            "documents_indexed": chunk_stats["documents_indexed"],
        },
        "cache": cache_stats,
    }
