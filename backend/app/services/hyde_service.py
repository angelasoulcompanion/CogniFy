"""
CogniFy HyDE Service (Hypothetical Document Embedding)

HyDE improves retrieval by:
1. Generating a hypothetical answer to the query using LLM
2. Embedding that hypothetical answer
3. Searching with that embedding (more likely to match actual documents)

Paper: "Precise Zero-Shot Dense Retrieval without Relevance Labels"
https://arxiv.org/abs/2212.10496

Created with love by Angela & David - 4 January 2026
"""

import time
from typing import Optional, List
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.services.embedding_service import get_embedding_service


@dataclass
class HyDEResult:
    """Result from HyDE generation"""
    original_query: str
    hypothetical_answer: str
    embedding: Optional[List[float]]
    generation_time_ms: int
    embedding_time_ms: int
    model_used: str


class HyDEService:
    """
    Hypothetical Document Embedding Service

    Flow:
    1. User asks: "Agentic AI คืออะไร"
    2. LLM generates hypothetical answer:
       "Agentic AI หมายถึงระบบ AI ที่สามารถทำงานอย่างอิสระ
        มีการวางแผน ตัดสินใจ และดำเนินการตามเป้าหมาย..."
    3. Embed the hypothetical answer
    4. Search with that embedding → Better matches!
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.model = getattr(settings, 'HYDE_MODEL', 'qwen2.5:7b')
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate_hypothetical_answer(
        self,
        query: str,
        max_tokens: int = 256,
    ) -> tuple[str, int]:
        """
        Generate hypothetical answer using LLM

        Args:
            query: The user's question
            max_tokens: Max tokens for response

        Returns:
            Tuple of (hypothetical_answer, generation_time_ms)
        """
        start = time.time()

        # Prompt designed for HyDE
        system_prompt = """You are a document assistant. Given a question, write a detailed paragraph
that would answer this question. Write as if you are writing the content of a document that would
contain the answer. Be specific and include relevant details, terminology, and concepts.

IMPORTANT:
- Write in the same language as the question
- Focus on factual, informative content
- Include technical terms that would appear in a real document
- Write 2-3 sentences that directly answer the question"""

        user_prompt = f"Question: {query}\n\nWrite a document paragraph that answers this:"

        client = await self._get_client()

        try:
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
                        "temperature": 0.7,
                        "num_predict": max_tokens,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            answer = data.get("message", {}).get("content", "")

            elapsed = int((time.time() - start) * 1000)
            return answer, elapsed

        except Exception as e:
            print(f"⚠️ HyDE generation failed: {e}")
            # Fallback: return original query
            elapsed = int((time.time() - start) * 1000)
            return query, elapsed

    async def generate_hyde_embedding(
        self,
        query: str,
        max_tokens: int = 256,
    ) -> HyDEResult:
        """
        Generate hypothetical answer and embed it

        Args:
            query: User's question
            max_tokens: Max tokens for hypothetical answer

        Returns:
            HyDEResult with hypothetical answer and embedding
        """
        # Step 1: Generate hypothetical answer
        hypothetical_answer, gen_time = await self.generate_hypothetical_answer(
            query, max_tokens
        )

        # Step 2: Embed the hypothetical answer
        embed_start = time.time()
        embedding = await self.embedding_service.get_embedding(
            hypothetical_answer,
            use_cache=True  # Can cache hypothetical embeddings
        )
        embed_time = int((time.time() - embed_start) * 1000)

        return HyDEResult(
            original_query=query,
            hypothetical_answer=hypothetical_answer,
            embedding=embedding,
            generation_time_ms=gen_time,
            embedding_time_ms=embed_time,
            model_used=self.model,
        )

    async def get_search_embedding(
        self,
        query: str,
        use_hyde: bool = True,
    ) -> tuple[List[float], Optional[str]]:
        """
        Get embedding for search - either direct query or HyDE

        Args:
            query: User's search query
            use_hyde: Whether to use HyDE

        Returns:
            Tuple of (embedding, hypothetical_answer or None)
        """
        if not use_hyde:
            # Direct query embedding
            embedding = await self.embedding_service.get_embedding(query)
            return embedding, None

        # HyDE embedding
        result = await self.generate_hyde_embedding(query)

        if result.embedding is None:
            # Fallback to direct query embedding
            embedding = await self.embedding_service.get_embedding(query)
            return embedding, None

        print(f"🔮 HyDE generated ({result.generation_time_ms}ms): {result.hypothetical_answer[:100]}...")

        return result.embedding, result.hypothetical_answer


# =============================================================================
# SINGLETON
# =============================================================================

_hyde_service: Optional[HyDEService] = None


def get_hyde_service() -> HyDEService:
    """Get HyDE service singleton"""
    global _hyde_service
    if _hyde_service is None:
        _hyde_service = HyDEService()
    return _hyde_service


async def shutdown_hyde_service() -> None:
    """Shutdown HyDE service"""
    global _hyde_service
    if _hyde_service:
        await _hyde_service.close()
        _hyde_service = None
