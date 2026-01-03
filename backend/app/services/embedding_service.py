"""
CogniFy Embedding Service
Singleton pattern with caching and fallback models
Pattern from AngelaAI
"""

import hashlib
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio

import httpx

from app.core.config import settings
from app.infrastructure.database import Database


class EmbeddingCache:
    """In-memory cache for embeddings with TTL"""

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, tuple[List[float], float]] = {}  # {hash: (embedding, timestamp)}
        self._hits = 0
        self._misses = 0

    def _hash_text(self, text: str, model: str) -> str:
        """Create hash key for text + model"""
        content = f"{model}:{text}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, text: str, model: str) -> Optional[List[float]]:
        """Get embedding from cache if exists and not expired"""
        key = self._hash_text(text, model)
        if key in self._cache:
            embedding, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                self._hits += 1
                return embedding
            else:
                # Expired, remove from cache
                del self._cache[key]

        self._misses += 1
        return None

    def set(self, text: str, model: str, embedding: List[float]) -> None:
        """Store embedding in cache"""
        # Evict oldest if at max size
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        key = self._hash_text(text, model)
        self._cache[key] = (embedding, time.time())

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl_seconds": self.ttl,
        }

    def clear(self) -> None:
        """Clear cache"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0


class EmbeddingService:
    """
    Embedding service with:
    - Singleton pattern
    - In-memory caching (TTL 1 hour)
    - Database caching (persistent)
    - Fallback model support
    - Batch processing
    """

    def __init__(self):
        self.primary_model = settings.EMBEDDING_MODEL
        self.fallback_model = settings.EMBEDDING_FALLBACK_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.openai_key = settings.OPENAI_API_KEY

        # In-memory cache
        self.cache = EmbeddingCache(
            ttl_seconds=settings.EMBEDDING_CACHE_TTL,
            max_size=1000
        )

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _generate_ollama_embedding(
        self,
        text: str,
        model: str
    ) -> Optional[List[float]]:
        """Generate embedding using Ollama"""
        try:
            client = await self._get_client()
            # bge-m3 supports 8192 tokens (~32000 chars), truncate as safety margin
            truncated_text = text[:30000] if len(text) > 30000 else text
            response = await client.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": model, "prompt": truncated_text}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding")
        except Exception as e:
            print(f"⚠️ Ollama embedding error ({model}): {e}")
            return None

    async def _generate_openai_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small"
    ) -> Optional[List[float]]:
        """Generate embedding using OpenAI"""
        if not self.openai_key:
            return None

        try:
            client = await self._get_client()
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.openai_key}"},
                json={"model": model, "input": text}
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            print(f"⚠️ OpenAI embedding error: {e}")
            return None

    def _embedding_to_pgvector(self, embedding) -> str:
        """Convert embedding to pgvector string format"""
        # Already a string - return as-is (but validate format)
        if isinstance(embedding, str):
            if embedding.startswith('[') and embedding.endswith(']'):
                return embedding
            return "[" + embedding + "]"

        # Nested list [[...]] - unwrap
        if isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], list):
            embedding = embedding[0]

        # Normal list of floats
        if isinstance(embedding, list):
            return "[" + ",".join(str(float(x)) for x in embedding) + "]"

        raise ValueError(f"Invalid embedding type: {type(embedding)}")

    async def _save_to_db_cache(
        self,
        text: str,
        model: str,
        embedding: List[float]
    ) -> None:
        """Save embedding to database cache"""
        try:
            text_hash = hashlib.md5(f"{model}:{text}".encode()).hexdigest()
            embedding_str = self._embedding_to_pgvector(embedding)
            await Database.execute(
                """
                INSERT INTO embedding_cache (text_hash, embedding, model_name, expires_at)
                VALUES ($1, $2::vector, $3, NOW() + INTERVAL '1 hour')
                ON CONFLICT (text_hash, model_name) DO UPDATE
                SET embedding = $2::vector, expires_at = NOW() + INTERVAL '1 hour'
                """,
                text_hash, embedding_str, model
            )
        except Exception as e:
            print(f"⚠️ Failed to cache embedding in DB: {e}")

    async def _get_from_db_cache(
        self,
        text: str,
        model: str
    ) -> Optional[List[float]]:
        """Get embedding from database cache"""
        try:
            text_hash = hashlib.md5(f"{model}:{text}".encode()).hexdigest()
            row = await Database.fetchrow(
                """
                SELECT embedding FROM embedding_cache
                WHERE text_hash = $1 AND model_name = $2 AND expires_at > NOW()
                """,
                text_hash, model
            )
            if row and row["embedding"]:
                emb = row["embedding"]
                # If pgvector returns as string "[0.1,0.2,...]" - parse it
                if isinstance(emb, str):
                    clean = emb.strip("[]")
                    return [float(x) for x in clean.split(",")] if clean else []
                # If already a list/tuple, convert to list of floats
                return [float(x) for x in emb]
        except Exception as e:
            print(f"⚠️ Failed to get embedding from DB cache: {e}")
        return None

    async def get_embedding(
        self,
        text: str,
        use_cache: bool = True
    ) -> Optional[List[float]]:
        """
        Get embedding for text with caching and fallback.

        Order:
        1. Check in-memory cache
        2. Check database cache
        3. Generate with primary model (Ollama)
        4. Fallback to secondary model
        5. Fallback to OpenAI (if configured)
        """
        if not text or not text.strip():
            return None

        text = text.strip()
        model = self.primary_model

        # 1. Check in-memory cache
        if use_cache:
            cached = self.cache.get(text, model)
            if cached:
                return cached

            # 2. Check database cache
            db_cached = await self._get_from_db_cache(text, model)
            if db_cached:
                self.cache.set(text, model, db_cached)
                return db_cached

        # 3. Generate with primary model (Ollama)
        embedding = await self._generate_ollama_embedding(text, self.primary_model)

        # 4. Fallback to secondary model
        if embedding is None and self.fallback_model:
            print(f"🔄 Trying fallback model: {self.fallback_model}")
            embedding = await self._generate_ollama_embedding(text, self.fallback_model)
            if embedding:
                model = self.fallback_model

        # 5. Fallback to OpenAI
        if embedding is None and self.openai_key:
            print("🔄 Trying OpenAI embedding")
            embedding = await self._generate_openai_embedding(text)
            if embedding:
                model = "text-embedding-3-small"

        if embedding is None:
            print(f"❌ Failed to generate embedding for text: {text[:50]}...")
            return None

        # Cache the result
        if use_cache:
            self.cache.set(text, model, embedding)
            await self._save_to_db_cache(text, model, embedding)

        return embedding

    async def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 10,
        use_cache: bool = True
    ) -> List[Optional[List[float]]]:
        """
        Get embeddings for multiple texts in batches.
        Returns list of embeddings (or None for failed ones).
        """
        results: List[Optional[List[float]]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Process batch concurrently
            tasks = [self.get_embedding(text, use_cache) for text in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # Small delay between batches to avoid overwhelming the server
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)

        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.stats()

    async def cleanup_expired_cache(self) -> int:
        """Clean up expired entries from database cache"""
        try:
            result = await Database.execute(
                "DELETE FROM embedding_cache WHERE expires_at < NOW()"
            )
            # Extract count from "DELETE X"
            count = int(result.split()[-1]) if result else 0
            print(f"🧹 Cleaned up {count} expired cache entries")
            return count
        except Exception as e:
            print(f"⚠️ Cache cleanup error: {e}")
            return 0

    async def health_check(self) -> Dict[str, Any]:
        """Check embedding service health"""
        # Test with a simple text
        test_text = "Hello, this is a test."
        start = time.time()
        embedding = await self.get_embedding(test_text, use_cache=False)
        elapsed = time.time() - start

        return {
            "status": "healthy" if embedding else "unhealthy",
            "primary_model": self.primary_model,
            "fallback_model": self.fallback_model,
            "dimension": self.dimension,
            "latency_ms": int(elapsed * 1000),
            "cache_stats": self.get_cache_stats(),
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get global EmbeddingService instance (singleton pattern)"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def shutdown_embedding_service() -> None:
    """Shutdown embedding service and cleanup"""
    global _embedding_service
    if _embedding_service:
        await _embedding_service.close()
        _embedding_service = None
