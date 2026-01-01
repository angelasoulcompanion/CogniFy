"""
CogniFy LLM Service

Provides unified interface for:
- Ollama (local LLMs)
- OpenAI API (cloud)

Features:
- Streaming responses (async generators)
- Fallback between providers
- Token counting
- Response caching (optional)

Created with love by Angela & David - 1 January 2026
"""

import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings


class LLMProvider(str, Enum):
    """Available LLM providers"""
    OLLAMA = "ollama"
    OPENAI = "openai"


class MessageRole(str, Enum):
    """Message roles"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Chat message"""
    role: MessageRole
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role.value, "content": self.content}


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "llama3.2"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    stream: bool = True
    # Ollama specific
    ollama_base_url: str = "http://localhost:11434"
    # OpenAI specific
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"

    @classmethod
    def from_settings(cls, provider: Optional[str] = None) -> "LLMConfig":
        """Create config from app settings"""
        return cls(
            provider=LLMProvider(provider or settings.LLM_PROVIDER),
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            ollama_base_url=settings.OLLAMA_BASE_URL,
            openai_api_key=settings.OPENAI_API_KEY,
        )


@dataclass
class LLMResponse:
    """LLM response"""
    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    response_time_ms: int = 0


@dataclass
class StreamChunk:
    """Streaming response chunk"""
    content: str
    is_done: bool = False
    finish_reason: Optional[str] = None


# =============================================================================
# BASE PROVIDER CLASS
# =============================================================================

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """Generate a complete response"""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream response chunks"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health"""
        pass


# =============================================================================
# OLLAMA PROVIDER
# =============================================================================

class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider for local models"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """Generate complete response from Ollama"""
        import time
        start_time = time.time()

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": config.model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
                "top_p": config.top_p,
            }
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            response_time = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=config.model,
                provider="ollama",
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
                total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                finish_reason="stop",
                response_time_ms=response_time,
            )
        except Exception as e:
            raise LLMError(f"Ollama generate failed: {e}")

    async def stream(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream response from Ollama"""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": config.model,
            "messages": [m.to_dict() for m in messages],
            "stream": True,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
                "top_p": config.top_p,
            }
        }

        try:
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            is_done = data.get("done", False)

                            yield StreamChunk(
                                content=content,
                                is_done=is_done,
                                finish_reason="stop" if is_done else None,
                            )

                            if is_done:
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            raise LLMError(f"Ollama stream failed: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama health"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return {
                "status": "healthy",
                "provider": "ollama",
                "base_url": self.base_url,
                "models_available": models,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "ollama",
                "error": str(e),
            }

    async def list_models(self) -> List[str]:
        """List available Ollama models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []


# =============================================================================
# OPENAI PROVIDER
# =============================================================================

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=120.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )

    async def generate(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """Generate complete response from OpenAI"""
        import time
        start_time = time.time()

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": config.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "stream": False,
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            response_time = int((time.time() - start_time) * 1000)
            choice = data.get("choices", [{}])[0]
            usage = data.get("usage", {})

            return LLMResponse(
                content=choice.get("message", {}).get("content", ""),
                model=data.get("model", config.model),
                provider="openai",
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                finish_reason=choice.get("finish_reason", "stop"),
                response_time_ms=response_time,
            )
        except Exception as e:
            raise LLMError(f"OpenAI generate failed: {e}")

    async def stream(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream response from OpenAI"""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": config.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "stream": True,
        }

        try:
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            yield StreamChunk(content="", is_done=True, finish_reason="stop")
                            break

                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            finish_reason = data.get("choices", [{}])[0].get("finish_reason")

                            if content:
                                yield StreamChunk(
                                    content=content,
                                    is_done=False,
                                    finish_reason=finish_reason,
                                )
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            raise LLMError(f"OpenAI stream failed: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI health"""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            return {
                "status": "healthy",
                "provider": "openai",
                "api_key_set": bool(self.api_key),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "openai",
                "error": str(e),
            }


# =============================================================================
# LLM SERVICE (UNIFIED INTERFACE)
# =============================================================================

class LLMError(Exception):
    """LLM operation error"""
    pass


class LLMService:
    """
    Unified LLM Service

    Features:
    - Multiple provider support (Ollama, OpenAI)
    - Automatic fallback
    - Streaming responses
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_settings()
        self._providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available providers"""
        # Always try to initialize Ollama
        self._providers[LLMProvider.OLLAMA] = OllamaProvider(
            base_url=self.config.ollama_base_url
        )

        # Initialize OpenAI if API key is available
        if self.config.openai_api_key:
            self._providers[LLMProvider.OPENAI] = OpenAIProvider(
                api_key=self.config.openai_api_key,
                base_url=self.config.openai_base_url,
            )

    def _get_provider(self, provider: Optional[LLMProvider] = None) -> BaseLLMProvider:
        """Get provider instance"""
        provider = provider or self.config.provider
        if provider not in self._providers:
            raise LLMError(f"Provider {provider} not available")
        return self._providers[provider]

    async def generate(
        self,
        messages: List[Message],
        config: Optional[LLMConfig] = None,
        provider: Optional[LLMProvider] = None,
    ) -> LLMResponse:
        """
        Generate complete response

        Tries primary provider, falls back to secondary if available
        """
        config = config or self.config
        primary_provider = provider or config.provider

        try:
            llm_provider = self._get_provider(primary_provider)
            return await llm_provider.generate(messages, config)
        except LLMError as e:
            # Try fallback
            fallback = self._get_fallback_provider(primary_provider)
            if fallback:
                print(f"Primary provider failed, trying fallback: {fallback}")
                llm_provider = self._get_provider(fallback)
                return await llm_provider.generate(messages, config)
            raise e

    async def stream(
        self,
        messages: List[Message],
        config: Optional[LLMConfig] = None,
        provider: Optional[LLMProvider] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream response chunks

        Yields StreamChunk objects with content
        """
        config = config or self.config
        llm_provider = self._get_provider(provider or config.provider)

        async for chunk in llm_provider.stream(messages, config):
            yield chunk

    async def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Message]] = None,
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """
        Simple chat interface

        Args:
            user_message: User's message
            system_prompt: Optional system prompt
            history: Optional conversation history
            config: Optional LLM config
        """
        messages = []

        if system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))

        if history:
            messages.extend(history)

        messages.append(Message(role=MessageRole.USER, content=user_message))

        return await self.generate(messages, config)

    async def chat_stream(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Message]] = None,
        config: Optional[LLMConfig] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Simple streaming chat interface
        """
        messages = []

        if system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))

        if history:
            messages.extend(history)

        messages.append(Message(role=MessageRole.USER, content=user_message))

        async for chunk in self.stream(messages, config):
            yield chunk

    def _get_fallback_provider(self, primary: LLMProvider) -> Optional[LLMProvider]:
        """Get fallback provider"""
        if primary == LLMProvider.OLLAMA and LLMProvider.OPENAI in self._providers:
            return LLMProvider.OPENAI
        elif primary == LLMProvider.OPENAI and LLMProvider.OLLAMA in self._providers:
            return LLMProvider.OLLAMA
        return None

    async def health_check(self) -> Dict[str, Any]:
        """Check all providers health"""
        results = {}
        for provider_type, provider in self._providers.items():
            results[provider_type.value] = await provider.health_check()

        # Overall status
        any_healthy = any(
            r.get("status") == "healthy" for r in results.values()
        )

        return {
            "status": "healthy" if any_healthy else "unhealthy",
            "default_provider": self.config.provider.value,
            "default_model": self.config.model,
            "providers": results,
        }

    async def list_models(self) -> Dict[str, List[str]]:
        """List available models from all providers"""
        models = {}

        if LLMProvider.OLLAMA in self._providers:
            ollama = self._providers[LLMProvider.OLLAMA]
            if isinstance(ollama, OllamaProvider):
                models["ollama"] = await ollama.list_models()

        if LLMProvider.OPENAI in self._providers:
            models["openai"] = [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
            ]

        return models


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLMService singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


async def shutdown_llm_service():
    """Shutdown LLM service and close connections"""
    global _llm_service
    if _llm_service:
        for provider in _llm_service._providers.values():
            if hasattr(provider, 'client'):
                await provider.client.aclose()
        _llm_service = None
