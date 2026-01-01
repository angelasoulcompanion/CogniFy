"""
Chat API Endpoints
Streaming chat with RAG support

Created with love by Angela & David - 1 January 2026
"""

from typing import Optional, List
from uuid import UUID, uuid4
import json

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user, get_current_user_optional, TokenPayload
from app.services.chat_service import (
    get_chat_service,
    ChatRequest as ChatServiceRequest,
)
from app.services.llm_service import get_llm_service
from app.infrastructure.repositories.conversation_repository import get_conversation_repository


router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class RAGSettingsRequest(BaseModel):
    """RAG configuration settings"""
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0)
    max_chunks: int = Field(10, ge=1, le=50)
    similarity_method: str = Field("cosine")
    search_method: str = Field("hybrid")  # vector, bm25, hybrid
    bm25_weight: float = Field(0.4, ge=0.0, le=1.0)
    vector_weight: float = Field(0.6, ge=0.0, le=1.0)


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    rag_enabled: bool = Field(True, description="Enable RAG retrieval")
    rag_settings: Optional[RAGSettingsRequest] = None
    document_ids: Optional[List[str]] = Field(None, description="Filter to specific documents")
    provider: str = Field("ollama", description="LLM provider: ollama or openai")
    model: Optional[str] = Field(None, description="Model name (uses default if not specified)")
    stream: bool = Field(True, description="Enable streaming response")


class SourceReference(BaseModel):
    """Source document reference"""
    index: int
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    content_preview: str
    score: float


class ChatMessage(BaseModel):
    """Chat message model"""
    message_id: str
    conversation_id: str
    message_type: str  # user, assistant, system
    content: str
    sources: Optional[List[SourceReference]] = None
    response_time_ms: Optional[int] = None
    created_at: str


class ChatResponse(BaseModel):
    """Non-streaming chat response"""
    message_id: str
    conversation_id: str
    content: str
    sources: List[SourceReference]
    model: str
    provider: str
    response_time_ms: int
    tokens_used: int


class ConversationResponse(BaseModel):
    """Conversation response"""
    conversation_id: str
    user_id: Optional[str]
    title: Optional[str]
    model_provider: str
    model_name: str
    rag_enabled: bool
    message_count: int
    created_at: str
    updated_at: str


class ConversationCreateRequest(BaseModel):
    """Create conversation request"""
    title: Optional[str] = None
    model_provider: str = "ollama"
    model_name: str = "llama3.2:1b"
    rag_enabled: bool = True
    rag_settings: Optional[RAGSettingsRequest] = None


# =============================================================================
# CHAT ENDPOINTS
# =============================================================================

@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).

    Returns real-time events:
    - session: Session/conversation info
    - search_start: RAG search started
    - search_results: RAG results preview
    - content: Response content chunk
    - sources: Full source citations
    - done: Stream complete with stats
    - error: Error occurred
    """
    chat_service = get_chat_service()

    # Parse conversation ID
    conversation_id = UUID(request.conversation_id) if request.conversation_id else None

    # Parse document IDs
    document_ids = [UUID(d) for d in request.document_ids] if request.document_ids else None

    # Get user ID
    user_id = UUID(current_user.sub) if current_user else None

    # Build service request
    service_request = ChatServiceRequest(
        message=request.message,
        conversation_id=conversation_id,
        rag_enabled=request.rag_enabled,
        rag_settings=request.rag_settings.model_dump() if request.rag_settings else None,
        document_ids=document_ids,
        provider=request.provider,
        model=request.model,
        stream=True,
    )

    async def event_generator():
        """Generate SSE events from chat service"""
        try:
            async for event in chat_service.chat_stream(service_request, user_id):
                yield event.to_sse()
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.post("/complete", response_model=ChatResponse)
async def complete_chat(
    request: ChatRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    Non-streaming chat endpoint.
    Returns complete response at once.
    """
    chat_service = get_chat_service()

    # Parse IDs
    conversation_id = UUID(request.conversation_id) if request.conversation_id else None
    document_ids = [UUID(d) for d in request.document_ids] if request.document_ids else None
    user_id = UUID(current_user.sub) if current_user else None

    # Build service request
    service_request = ChatServiceRequest(
        message=request.message,
        conversation_id=conversation_id,
        rag_enabled=request.rag_enabled,
        rag_settings=request.rag_settings.model_dump() if request.rag_settings else None,
        document_ids=document_ids,
        provider=request.provider,
        model=request.model,
        stream=False,
    )

    # Get response
    response = await chat_service.chat(service_request, user_id)

    return ChatResponse(
        message_id=str(response.message_id),
        conversation_id=str(response.conversation_id),
        content=response.content,
        sources=[
            SourceReference(
                index=s["index"],
                document_id=s["document_id"],
                document_name=s["document_name"],
                page_number=s.get("page_number"),
                section=s.get("section"),
                content_preview=s["content_preview"],
                score=s["score"],
            )
            for s in response.sources
        ],
        model=response.model,
        provider=response.provider,
        response_time_ms=response.response_time_ms,
        tokens_used=response.tokens_used,
    )


# =============================================================================
# CONVERSATION ENDPOINTS
# =============================================================================

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Create a new conversation"""
    repo = get_conversation_repository()

    conversation = await repo.create_conversation(
        user_id=UUID(current_user.sub),
        title=request.title,
        model_provider=request.model_provider,
        model_name=request.model_name,
        rag_enabled=request.rag_enabled,
        rag_settings=request.rag_settings.model_dump() if request.rag_settings else None,
    )

    return ConversationResponse(**conversation)


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    current_user: TokenPayload = Depends(get_current_user)
):
    """List user's conversations"""
    repo = get_conversation_repository()

    conversations = await repo.list_conversations(
        user_id=UUID(current_user.sub),
        limit=limit,
        offset=offset,
    )

    return [ConversationResponse(**c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Get conversation by ID"""
    repo = get_conversation_repository()

    conversation = await repo.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Check ownership
    if conversation["user_id"] and conversation["user_id"] != current_user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this conversation"
        )

    return ConversationResponse(**conversation)


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessage])
async def get_conversation_messages(
    conversation_id: UUID,
    limit: int = 50,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Get all messages in a conversation"""
    repo = get_conversation_repository()

    # Verify conversation exists and user has access
    conversation = await repo.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    if conversation["user_id"] and conversation["user_id"] != current_user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this conversation"
        )

    messages = await repo.get_messages(conversation_id, limit=limit)

    return [
        ChatMessage(
            message_id=m["message_id"],
            conversation_id=m["conversation_id"],
            message_type=m["message_type"],
            content=m["content"],
            sources=[
                SourceReference(**s) for s in (m["sources_used"] or [])
            ] if m["sources_used"] else None,
            response_time_ms=m["response_time_ms"],
            created_at=m["created_at"],
        )
        for m in messages
    ]


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Delete a conversation"""
    repo = get_conversation_repository()

    # Verify ownership
    conversation = await repo.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    if conversation["user_id"] and conversation["user_id"] != current_user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this conversation"
        )

    await repo.delete_conversation(conversation_id)
    return None


@router.get("/conversations/search")
async def search_conversations(
    q: str,
    limit: int = 20,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Search conversations by title or message content"""
    repo = get_conversation_repository()

    conversations = await repo.search_conversations(
        user_id=UUID(current_user.sub),
        query=q,
        limit=limit,
    )

    return [ConversationResponse(**c) for c in conversations]


# =============================================================================
# HEALTH & STATS
# =============================================================================

@router.get("/health")
async def chat_health():
    """Check chat service health"""
    chat_service = get_chat_service()
    llm_service = get_llm_service()

    chat_health = await chat_service.health_check()
    models = await llm_service.list_models()

    return {
        **chat_health,
        "available_models": models,
    }


@router.get("/stats")
async def chat_stats(
    current_user: TokenPayload = Depends(get_current_user)
):
    """Get chat statistics for current user"""
    repo = get_conversation_repository()

    stats = await repo.get_conversation_stats(
        user_id=UUID(current_user.sub)
    )

    return stats


@router.get("/models")
async def list_available_models():
    """List available LLM models"""
    llm_service = get_llm_service()
    return await llm_service.list_models()
