"""
CogniFy Re-ranker Service

LLM-based re-ranking to improve search result relevance.

Flow:
1. Initial search returns top-N results (e.g., 20)
2. LLM scores each result's relevance to query (1-10)
3. Sort by LLM score
4. Return top-K results (e.g., 5)

Created with love by Angela & David - 4 January 2026
"""

import time
import json
import re
from typing import Optional, List
from dataclasses import dataclass
from uuid import UUID

import httpx

from app.core.config import settings


@dataclass
class RerankScore:
    """Score for a single result"""
    chunk_id: UUID
    relevance_score: float  # 1-10
    reasoning: Optional[str] = None


@dataclass
class RerankResult:
    """Result from re-ranking"""
    scores: List[RerankScore]
    rerank_time_ms: int
    model_used: str


class RerankerService:
    """
    LLM-based Re-ranker Service

    Uses a fast LLM to score relevance of search results.
    """

    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        # Use same model as HyDE for consistency
        self.model = getattr(settings, 'RERANK_MODEL', 'qwen2.5:7b')
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def rerank(
        self,
        query: str,
        results: List[dict],
        top_k: int = 5,
    ) -> List[dict]:
        """
        Re-rank search results using LLM

        Args:
            query: Original search query
            results: List of search results with 'chunk_id' and 'content'
            top_k: Number of top results to return

        Returns:
            Re-ranked list of results (top_k)
        """
        if not results:
            return []

        if len(results) <= top_k:
            # No need to re-rank if we have fewer results than top_k
            return results

        start = time.time()

        # Build prompt for batch scoring
        system_prompt = """You are a relevance scoring expert. Score how relevant each document is to the query.

SCORING RULES:
- Score 1-10 (10 = highly relevant, 1 = not relevant)
- Score 8-10: Directly answers the query or contains exact information needed
- Score 5-7: Related topic but doesn't directly answer
- Score 1-4: Barely related or unrelated

OUTPUT FORMAT:
Return ONLY a JSON array with scores like:
[{"id": 1, "score": 8}, {"id": 2, "score": 3}, ...]

No explanation, just the JSON array."""

        # Build documents list
        docs_text = ""
        for i, result in enumerate(results, 1):
            content = result.get("content", "")[:500]  # Truncate for efficiency
            docs_text += f"\n[Document {i}]\n{content}\n"

        user_prompt = f"""Query: {query}

Documents to score:
{docs_text}

Score each document (1-10) for relevance to the query. Return JSON array:"""

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistency
                        "num_predict": 512,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            llm_response = data.get("message", {}).get("content", "")

            # Parse scores
            scores = self._parse_scores(llm_response, len(results))

            # Apply scores to results
            for result, score in zip(results, scores):
                result["rerank_score"] = score

            # Sort by rerank_score
            sorted_results = sorted(
                results,
                key=lambda x: x.get("rerank_score", 0),
                reverse=True
            )

            elapsed = int((time.time() - start) * 1000)
            print(f"🎯 Re-ranked {len(results)} results in {elapsed}ms")

            return sorted_results[:top_k]

        except Exception as e:
            print(f"⚠️ Re-ranking failed: {e}, returning original order")
            return results[:top_k]

    def _parse_scores(self, llm_response: str, num_results: int) -> List[float]:
        """
        Parse LLM response to extract scores

        Tries multiple parsing strategies for robustness.
        """
        scores = [5.0] * num_results  # Default scores

        try:
            # Try to find JSON array in response
            json_match = re.search(r'\[.*?\]', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)

                for item in parsed:
                    if isinstance(item, dict):
                        idx = item.get("id", 0) - 1  # 1-indexed to 0-indexed
                        score = item.get("score", 5)
                        if 0 <= idx < num_results:
                            scores[idx] = float(score)
                    elif isinstance(item, (int, float)):
                        # Simple array of scores
                        idx = parsed.index(item)
                        if idx < num_results:
                            scores[idx] = float(item)

                return scores

        except json.JSONDecodeError:
            pass

        # Fallback: try to extract numbers
        try:
            numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', llm_response)
            for i, num in enumerate(numbers[:num_results]):
                score = float(num)
                if 1 <= score <= 10:
                    scores[i] = score
        except Exception:
            pass

        return scores

    async def rerank_with_details(
        self,
        query: str,
        results: List[dict],
        top_k: int = 5,
    ) -> tuple[List[dict], RerankResult]:
        """
        Re-rank with detailed scoring information

        Returns:
            Tuple of (reranked_results, RerankResult with details)
        """
        start = time.time()
        reranked = await self.rerank(query, results, top_k)
        elapsed = int((time.time() - start) * 1000)

        scores = [
            RerankScore(
                chunk_id=r.get("chunk_id"),
                relevance_score=r.get("rerank_score", 5.0),
            )
            for r in reranked
        ]

        result = RerankResult(
            scores=scores,
            rerank_time_ms=elapsed,
            model_used=self.model,
        )

        return reranked, result


# =============================================================================
# SINGLETON
# =============================================================================

_reranker_service: Optional[RerankerService] = None


def get_reranker_service() -> RerankerService:
    """Get Re-ranker service singleton"""
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = RerankerService()
    return _reranker_service


async def shutdown_reranker_service() -> None:
    """Shutdown Re-ranker service"""
    global _reranker_service
    if _reranker_service:
        await _reranker_service.close()
        _reranker_service = None
