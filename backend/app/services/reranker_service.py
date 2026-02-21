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

import asyncio
import time
import json
import re
from typing import Optional, List
from dataclasses import dataclass
from uuid import UUID

import httpx

from app.core.config import settings
from app.core.logging import logger

# Re-ranking batch config
RERANK_BATCH_SIZE = 5  # Score 5 results per LLM call
RERANK_MAX_CONCURRENT = 4  # Max parallel LLM calls


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
        Re-rank search results using a single fast LLM call.

        Ollama processes requests sequentially, so batching doesn't help.
        Instead we minimize tokens: fewer results + shorter content.
        """
        if not results:
            return []

        if len(results) <= top_k:
            return results

        start = time.time()

        try:
            scores = await self._score_batch(query, results)

            for result, score in zip(results, scores):
                result["rerank_score"] = score

            sorted_results = sorted(
                results,
                key=lambda x: x.get("rerank_score", 0),
                reverse=True,
            )

            elapsed = int((time.time() - start) * 1000)
            logger.info("Re-ranked {} results in {}ms", len(results), elapsed)

            return sorted_results[:top_k]

        except Exception as e:
            logger.warning("Re-ranking failed: {}, returning original order", e)
            return results[:top_k]

    async def _score_batch(self, query: str, batch: List[dict]) -> List[float]:
        """Score results via a single LLM call with minimal tokens"""
        system_prompt = """Score each document's relevance to the query (1-10).
9-10: Directly answers. 5-8: Related. 1-4: Not relevant.
Return ONLY JSON: [{"id":1,"score":8},{"id":2,"score":3},...]"""

        docs_text = ""
        for i, result in enumerate(batch, 1):
            content = result.get("content", "")[:200]
            docs_text += f"\n[{i}] {content}\n"

        user_prompt = f"Query: {query}\n{docs_text}\nJSON scores:"

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
                        "temperature": 0.0,
                        "num_predict": 128,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            llm_response = data.get("message", {}).get("content", "")
            return self._parse_scores(llm_response, len(batch))
        except Exception as e:
            logger.warning("Batch scoring failed: {}", e)
            return [5.0] * len(batch)

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
# SINGLETON ACCESS (delegates to ServiceContainer)
# =============================================================================

def get_reranker_service() -> RerankerService:
    """Get RerankerService via the global ServiceContainer"""
    from app.core.container import get_container
    return get_container().reranker
