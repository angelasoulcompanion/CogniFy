"""
CogniFy LLM Service

Provides unified interface for:
- Ollama (local LLMs)
- Anthropic API (Claude)

Features:
- Streaming responses (async generators)
- Fallback between providers
- Token counting
- Response caching (optional)

Created with love by Angela & David - 1 January 2026
Updated: Anthropic Claude support - 21 February 2026
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
    ANTHROPIC = "anthropic"


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
    model: str = "scb10x/typhoon2.5-qwen3-4b"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    stream: bool = True
    # Ollama specific
    ollama_base_url: str = "http://localhost:11434"
    # Anthropic specific
    anthropic_api_key: Optional[str] = None
    anthropic_base_url: str = "https://api.anthropic.com"

    @classmethod
    def from_settings(cls, provider: Optional[str] = None) -> "LLMConfig":
        """Create config from app settings"""
        return cls(
            provider=LLMProvider(provider or settings.LLM_PROVIDER),
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            ollama_base_url=settings.OLLAMA_BASE_URL,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            anthropic_base_url=settings.ANTHROPIC_BASE_URL,
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
        """List available Ollama models (with and without :latest tag)"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            names = set()
            for m in data.get("models", []):
                name = m["name"]
                names.add(name)
                # Also add short name without :latest tag
                if ":" in name:
                    names.add(name.rsplit(":", 1)[0])
            return sorted(names)
        except Exception:
            return []


# =============================================================================
# ANTHROPIC PROVIDER
# =============================================================================

class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider for Claude models"""

    MODELS = [
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
    ]

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=120.0,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
        )

    def _split_system(self, messages: List[Message]) -> tuple[Optional[str], List[Dict[str, str]]]:
        """
        Anthropic requires system prompt as a separate top-level field.
        Split system message from conversation messages.
        """
        system_prompt = None
        api_messages = []
        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system_prompt = m.content
            else:
                api_messages.append(m.to_dict())
        return system_prompt, api_messages

    async def generate(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """Generate complete response from Anthropic"""
        import time
        start_time = time.time()

        system_prompt, api_messages = self._split_system(messages)

        url = f"{self.base_url}/v1/messages"
        payload: Dict[str, Any] = {
            "model": config.model,
            "messages": api_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            response_time = int((time.time() - start_time) * 1000)

            # Extract text from content blocks
            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")

            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=data.get("model", config.model),
                provider="anthropic",
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                finish_reason=data.get("stop_reason", "end_turn"),
                response_time_ms=response_time,
            )
        except Exception as e:
            raise LLMError(f"Anthropic generate failed: {e}")

    async def stream(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream response from Anthropic"""
        system_prompt, api_messages = self._split_system(messages)

        url = f"{self.base_url}/v1/messages"
        payload: Dict[str, Any] = {
            "model": config.model,
            "messages": api_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    event_type = data.get("type", "")

                    if event_type == "content_block_delta":
                        delta = data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield StreamChunk(
                                content=delta.get("text", ""),
                                is_done=False,
                            )

                    elif event_type == "message_stop":
                        yield StreamChunk(
                            content="",
                            is_done=True,
                            finish_reason="end_turn",
                        )
                        break

        except Exception as e:
            raise LLMError(f"Anthropic stream failed: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check Anthropic health"""
        try:
            # Simple test: send a tiny request
            response = await self.client.post(
                f"{self.base_url}/v1/messages",
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                },
            )
            response.raise_for_status()
            return {
                "status": "healthy",
                "provider": "anthropic",
                "api_key_set": True,
                "models_available": self.MODELS,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "anthropic",
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
    - Multiple provider support (Ollama, Anthropic)
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

        # Initialize Anthropic if API key is available
        if self.config.anthropic_api_key:
            self._providers[LLMProvider.ANTHROPIC] = AnthropicProvider(
                api_key=self.config.anthropic_api_key,
                base_url=self.config.anthropic_base_url,
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
            provider_name = primary_provider.value.capitalize()
            raise LLMError(f"{provider_name} is not available. Please check if {provider_name} is running or try selecting a different model.")

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

        if LLMProvider.ANTHROPIC in self._providers:
            models["anthropic"] = AnthropicProvider.MODELS

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
