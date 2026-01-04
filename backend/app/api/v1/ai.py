"""
AI API Endpoints
Simple LLM completion without conversation management
Created with love by Angela & David - 4 January 2026
"""

from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user_optional, TokenPayload
from app.services.llm_service import (
    get_llm_service,
    LLMConfig,
    LLMProvider,
    Message,
    MessageRole,
)


router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class AICompleteRequest(BaseModel):
    """AI completion request"""
    message: str = Field(..., min_length=1, description="User message/query")
    system_prompt: Optional[str] = Field(None, description="System prompt for context")
    provider: str = Field("ollama", description="LLM provider: ollama or openai")
    model: Optional[str] = Field(None, description="Model name")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Response temperature")
    max_tokens: Optional[int] = Field(None, description="Max tokens in response")


class AICompleteResponse(BaseModel):
    """AI completion response"""
    content: str
    model: str
    provider: str
    tokens_used: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/complete", response_model=AICompleteResponse)
async def ai_complete(
    request: AICompleteRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Simple AI completion endpoint.
    Used by Search "Ask AI" feature and other components.
    No conversation history - just single request/response.
    """
    llm_service = get_llm_service()

    # Determine provider
    try:
        provider = LLMProvider(request.provider.lower())
    except ValueError:
        provider = LLMProvider.OLLAMA

    # Build config with defaults for None values
    config = LLMConfig(
        provider=provider,
        model=request.model or ("llama3.2:1b" if provider == LLMProvider.OLLAMA else "gpt-4o-mini"),
        temperature=request.temperature,
        max_tokens=request.max_tokens or 2048,
    )

    # Build messages
    messages = []

    if request.system_prompt:
        messages.append(Message(
            role=MessageRole.SYSTEM,
            content=request.system_prompt
        ))

    messages.append(Message(
        role=MessageRole.USER,
        content=request.message
    ))

    # Generate response
    try:
        response = await llm_service.generate(messages, config)

        return AICompleteResponse(
            content=response.content,
            model=response.model,
            provider=response.provider,  # Already a string
            tokens_used=response.total_tokens,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI generation failed: {str(e)}"
        )


@router.get("/models")
async def list_models():
    """List available AI models"""
    llm_service = get_llm_service()
    return await llm_service.list_models()


@router.get("/health")
async def ai_health():
    """Check AI service health"""
    llm_service = get_llm_service()
    health = await llm_service.health_check()
    models = await llm_service.list_models()

    return {
        **health,
        "available_models": models,
    }
