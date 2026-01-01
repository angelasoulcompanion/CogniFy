"""
CogniFy RAG Service

Provides:
- Vector similarity search (pgvector)
- BM25 keyword search (full-text)
- Hybrid search with RRF fusion
- Reranking support

Created with love by Angela & David - 1 January 2026
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from dataclasses import dataclass
from enum import Enum

from app.services.embedding_service import get_embedding_service
from app.infrastructure.database import Database


class SearchMethod(str, Enum):
    """Available search methods"""
    VECTOR = "vector"          # Pure vector similarity
    BM25 = "bm25"              # Pure keyword search
    HYBRID = "hybrid"          # Combined with RRF


class SimilarityMethod(str, Enum):
    """Similarity calculation methods for pgvector"""
    COSINE = "cosine"          # <=> operator - normalized, good for text
    EUCLIDEAN = "euclidean"    # <-> operator - L2 distance
    DOT_PRODUCT = "dot"        # <#> operator - for normalized vectors


@dataclass
class SearchResult:
    """Single search result with metadata"""
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    page_number: Optional[int]
    section_title: Optional[str]
    document_title: Optional[str]
    document_filename: Optional[str]

    # For hybrid search
    vector_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    rrf_score: Optional[float] = None


@dataclass
class RAGSettings:
    """RAG configuration settings"""
    search_method: SearchMethod = SearchMethod.HYBRID
    similarity_method: SimilarityMethod = SimilarityMethod.COSINE
    similarity_threshold: float = 0.3      # Minimum similarity score
    max_chunks: int = 10                   # Max results to return
    bm25_weight: float = 0.4               # Weight for BM25 in hybrid
    vector_weight: float = 0.6             # Weight for vector in hybrid
    rrf_k: int = 60                        # RRF constant (default 60)
    include_metadata: bool = True          # Include document metadata

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RAGSettings":
        """Create settings from dictionary"""
        return cls(
            search_method=SearchMethod(data.get("search_method", "hybrid")),
            similarity_method=SimilarityMethod(data.get("similarity_method", "cosine")),
            similarity_threshold=data.get("similarity_threshold", 0.3),
            max_chunks=data.get("max_chunks", 10),
            bm25_weight=data.get("bm25_weight", 0.4),
            vector_weight=data.get("vector_weight", 0.6),
            rrf_k=data.get("rrf_k", 60),
            include_metadata=data.get("include_metadata", True),
        )


class RAGService:
    """
    RAG (Retrieval Augmented Generation) Service

    Supports:
    - Vector search using pgvector
    - BM25 keyword search using PostgreSQL full-text
    - Hybrid search combining both with RRF fusion
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()

    # =========================================================================
    # MAIN SEARCH API
    # =========================================================================

    async def search(
        self,
        query: str,
        settings: Optional[RAGSettings] = None,
        user_id: Optional[UUID] = None,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[SearchResult]:
        """
        Main search API - routes to appropriate search method

        Args:
            query: Search query text
            settings: RAG settings (uses defaults if not provided)
            user_id: Filter by user's documents
            document_ids: Filter by specific document IDs

        Returns:
            List of SearchResult ordered by relevance
        """
        settings = settings or RAGSettings()

        if settings.search_method == SearchMethod.VECTOR:
            return await self.vector_search(
                query=query,
                settings=settings,
                user_id=user_id,
                document_ids=document_ids,
            )
        elif settings.search_method == SearchMethod.BM25:
            return await self.bm25_search(
                query=query,
                settings=settings,
                user_id=user_id,
                document_ids=document_ids,
            )
        else:  # HYBRID
            return await self.hybrid_search(
                query=query,
                settings=settings,
                user_id=user_id,
                document_ids=document_ids,
            )

    # =========================================================================
    # VECTOR SEARCH (pgvector)
    # =========================================================================

    async def vector_search(
        self,
        query: str,
        settings: Optional[RAGSettings] = None,
        user_id: Optional[UUID] = None,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[SearchResult]:
        """
        Pure vector similarity search using pgvector

        Uses embedding to find semantically similar chunks
        """
        settings = settings or RAGSettings()

        # Get query embedding
        query_embedding = await self.embedding_service.get_embedding(query)
        if not query_embedding:
            return []

        # Build similarity operator based on method
        similarity_op = self._get_similarity_operator(settings.similarity_method)

        # Build query
        sql = f"""
            WITH ranked_chunks AS (
                SELECT
                    c.chunk_id,
                    c.document_id,
                    c.content,
                    c.page_number,
                    c.section_title,
                    d.title as document_title,
                    d.original_filename as document_filename,
                    1 - (c.embedding {similarity_op} $1::vector) as similarity_score,
                    ROW_NUMBER() OVER (ORDER BY c.embedding {similarity_op} $1::vector) as rank
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.document_id
                WHERE d.is_deleted = false
                  AND d.processing_status = 'completed'
                  AND c.embedding IS NOT NULL
                  {"AND d.uploaded_by = $2" if user_id else ""}
                  {"AND d.document_id = ANY($3)" if document_ids else ""}
            )
            SELECT *
            FROM ranked_chunks
            WHERE similarity_score >= ${"3" if user_id else ("2" if not document_ids else "4")}
            ORDER BY similarity_score DESC
            LIMIT ${"4" if user_id else ("3" if not document_ids else "5")}
        """

        # Build parameters
        params: List[Any] = [query_embedding]
        param_idx = 2

        if user_id:
            params.append(str(user_id))
            param_idx += 1

        if document_ids:
            params.append([str(d) for d in document_ids])
            param_idx += 1

        params.append(settings.similarity_threshold)
        params.append(settings.max_chunks)

        # Execute
        pool = await Database.get_pool()
        rows = await pool.fetch(sql, *params)

        return [
            SearchResult(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                content=row["content"],
                score=float(row["similarity_score"]),
                page_number=row["page_number"],
                section_title=row["section_title"],
                document_title=row["document_title"],
                document_filename=row["document_filename"],
                vector_rank=row["rank"],
            )
            for row in rows
        ]

    # =========================================================================
    # BM25 SEARCH (Full-Text)
    # =========================================================================

    async def bm25_search(
        self,
        query: str,
        settings: Optional[RAGSettings] = None,
        user_id: Optional[UUID] = None,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[SearchResult]:
        """
        BM25-style keyword search using PostgreSQL full-text search

        Uses ts_rank for scoring (approximates BM25)
        """
        settings = settings or RAGSettings()

        # Convert query to tsquery format
        # Split query into words and join with &
        query_words = query.strip().split()
        if not query_words:
            return []

        # Create tsquery - each word with prefix matching
        tsquery_parts = [f"{word}:*" for word in query_words if word]
        tsquery = " & ".join(tsquery_parts)

        # Build query
        sql = """
            WITH ranked_chunks AS (
                SELECT
                    c.chunk_id,
                    c.document_id,
                    c.content,
                    c.page_number,
                    c.section_title,
                    d.title as document_title,
                    d.original_filename as document_filename,
                    ts_rank_cd(
                        to_tsvector('simple', c.content),
                        to_tsquery('simple', $1),
                        32  -- Normalize by document length
                    ) as bm25_score,
                    ROW_NUMBER() OVER (
                        ORDER BY ts_rank_cd(
                            to_tsvector('simple', c.content),
                            to_tsquery('simple', $1),
                            32
                        ) DESC
                    ) as rank
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.document_id
                WHERE d.is_deleted = false
                  AND d.processing_status = 'completed'
                  AND to_tsvector('simple', c.content) @@ to_tsquery('simple', $1)
        """

        params: List[Any] = [tsquery]
        param_idx = 2

        if user_id:
            sql += f" AND d.uploaded_by = ${param_idx}"
            params.append(str(user_id))
            param_idx += 1

        if document_ids:
            sql += f" AND d.document_id = ANY(${param_idx})"
            params.append([str(d) for d in document_ids])
            param_idx += 1

        sql += f"""
            )
            SELECT *
            FROM ranked_chunks
            ORDER BY bm25_score DESC
            LIMIT ${param_idx}
        """
        params.append(settings.max_chunks)

        # Execute
        pool = await Database.get_pool()
        rows = await pool.fetch(sql, *params)

        return [
            SearchResult(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                content=row["content"],
                score=float(row["bm25_score"]),
                page_number=row["page_number"],
                section_title=row["section_title"],
                document_title=row["document_title"],
                document_filename=row["document_filename"],
                bm25_rank=row["rank"],
            )
            for row in rows
        ]

    # =========================================================================
    # HYBRID SEARCH (RRF Fusion)
    # =========================================================================

    async def hybrid_search(
        self,
        query: str,
        settings: Optional[RAGSettings] = None,
        user_id: Optional[UUID] = None,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[SearchResult]:
        """
        Hybrid search combining vector and BM25 with RRF fusion

        RRF (Reciprocal Rank Fusion) formula:
        score = sum(1 / (k + rank)) for each ranker

        With weights:
        score = vector_weight * (1 / (k + vector_rank)) + bm25_weight * (1 / (k + bm25_rank))
        """
        settings = settings or RAGSettings()

        # Get results from both methods
        vector_results = await self.vector_search(
            query=query,
            settings=RAGSettings(
                similarity_method=settings.similarity_method,
                similarity_threshold=settings.similarity_threshold,
                max_chunks=settings.max_chunks * 2,  # Get more for merging
            ),
            user_id=user_id,
            document_ids=document_ids,
        )

        bm25_results = await self.bm25_search(
            query=query,
            settings=RAGSettings(max_chunks=settings.max_chunks * 2),
            user_id=user_id,
            document_ids=document_ids,
        )

        # Build rank maps
        vector_ranks: Dict[UUID, int] = {
            r.chunk_id: i + 1 for i, r in enumerate(vector_results)
        }
        bm25_ranks: Dict[UUID, int] = {
            r.chunk_id: i + 1 for i, r in enumerate(bm25_results)
        }

        # Collect all unique chunks
        all_chunks: Dict[UUID, SearchResult] = {}
        for r in vector_results:
            all_chunks[r.chunk_id] = r
        for r in bm25_results:
            if r.chunk_id not in all_chunks:
                all_chunks[r.chunk_id] = r

        # Calculate RRF scores
        k = settings.rrf_k
        results_with_rrf: List[SearchResult] = []

        for chunk_id, result in all_chunks.items():
            v_rank = vector_ranks.get(chunk_id)
            b_rank = bm25_ranks.get(chunk_id)

            # RRF score calculation
            rrf_score = 0.0
            if v_rank:
                rrf_score += settings.vector_weight * (1.0 / (k + v_rank))
            if b_rank:
                rrf_score += settings.bm25_weight * (1.0 / (k + b_rank))

            # Update result with RRF info
            result.vector_rank = v_rank
            result.bm25_rank = b_rank
            result.rrf_score = rrf_score
            result.score = rrf_score  # Use RRF as main score

            results_with_rrf.append(result)

        # Sort by RRF score and limit
        results_with_rrf.sort(key=lambda x: x.rrf_score or 0, reverse=True)

        return results_with_rrf[:settings.max_chunks]

    # =========================================================================
    # CONTEXT BUILDING FOR LLM
    # =========================================================================

    async def build_context(
        self,
        query: str,
        settings: Optional[RAGSettings] = None,
        user_id: Optional[UUID] = None,
        document_ids: Optional[List[UUID]] = None,
        max_context_length: int = 8000,
    ) -> Tuple[str, List[SearchResult]]:
        """
        Search and build context string for LLM

        Returns:
            Tuple of (context_string, search_results)
        """
        results = await self.search(
            query=query,
            settings=settings,
            user_id=user_id,
            document_ids=document_ids,
        )

        if not results:
            return "", []

        # Build context with source citations
        context_parts = []
        current_length = 0
        used_results = []

        for i, result in enumerate(results, 1):
            # Format source reference
            source = f"[{i}]"
            if result.document_title:
                source = f"[{i}: {result.document_title}"
                if result.page_number:
                    source += f", p.{result.page_number}"
                source += "]"

            chunk_text = f"{source}\n{result.content}\n"
            chunk_length = len(chunk_text)

            if current_length + chunk_length > max_context_length:
                break

            context_parts.append(chunk_text)
            current_length += chunk_length
            used_results.append(result)

        context = "\n---\n".join(context_parts)

        return context, used_results

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_similarity_operator(self, method: SimilarityMethod) -> str:
        """Get pgvector operator for similarity method"""
        operators = {
            SimilarityMethod.COSINE: "<=>",
            SimilarityMethod.EUCLIDEAN: "<->",
            SimilarityMethod.DOT_PRODUCT: "<#>",
        }
        return operators.get(method, "<=>")


# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAGService singleton"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
