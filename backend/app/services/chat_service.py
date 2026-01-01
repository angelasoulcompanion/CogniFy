"""
CogniFy Chat Service

Orchestrates:
- RAG retrieval
- LLM generation
- Conversation management
- Source citation

Created with love by Angela & David - 1 January 2026
"""

import json
from typing import Optional, List, Dict, Any, AsyncGenerator, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.services.llm_service import (
    get_llm_service,
    LLMService,
    LLMConfig,
    LLMProvider,
    Message,
    MessageRole,
    StreamChunk,
    LLMResponse,
)
from app.services.rag_service import (
    get_rag_service,
    RAGService,
    RAGSettings,
    SearchMethod,
    SearchResult,
)


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

class PromptTemplates:
    """RAG prompt templates"""

    SYSTEM_DEFAULT = """You are CogniFy, an intelligent assistant that helps users understand their documents and data.

You have access to relevant context from the user's documents. Use this context to answer questions accurately.

Guidelines:
- Be helpful, accurate, and concise
- If the context doesn't contain enough information to answer, say so
- Cite sources when referencing specific information using [Source N] format
- For Thai documents, respond in Thai; for English documents, respond in English
- If uncertain, acknowledge the uncertainty"""

    SYSTEM_RAG = """You are CogniFy, an intelligent assistant with access to the user's documents.

Below is relevant context retrieved from the user's documents. Use this context to answer the question.

--- CONTEXT ---
{context}
--- END CONTEXT ---

Guidelines:
- Answer based on the provided context
- Cite sources using [1], [2], etc. matching the source numbers in context
- If the context doesn't contain enough information, say "I don't have enough information in the documents to answer that."
- Be accurate and concise
- Respond in the same language as the question"""

    SYSTEM_RAG_THAI = """คุณคือ CogniFy ผู้ช่วยอัจฉริยะที่สามารถเข้าถึงเอกสารของผู้ใช้

ด้านล่างนี้คือบริบทที่เกี่ยวข้องจากเอกสารของผู้ใช้ ใช้บริบทนี้เพื่อตอบคำถาม

--- บริบท ---
{context}
--- จบบริบท ---

หลักการ:
- ตอบโดยอิงจากบริบทที่ให้มา
- อ้างอิงแหล่งที่มาโดยใช้ [1], [2] ฯลฯ ตามหมายเลขแหล่งที่มาในบริบท
- หากบริบทไม่มีข้อมูลเพียงพอ ให้ตอบว่า "ไม่มีข้อมูลเพียงพอในเอกสารที่จะตอบคำถามนี้"
- ตอบให้ถูกต้องและกระชับ"""

    SYSTEM_NO_CONTEXT = """You are CogniFy, an intelligent assistant.

The user's question doesn't seem to require document context. Answer based on your general knowledge.

Be helpful, accurate, and concise."""

    @classmethod
    def get_rag_prompt(cls, context: str, language: str = "auto") -> str:
        """Get RAG system prompt with context"""
        if language == "th" or cls._detect_thai(context):
            return cls.SYSTEM_RAG_THAI.format(context=context)
        return cls.SYSTEM_RAG.format(context=context)

    @classmethod
    def _detect_thai(cls, text: str) -> bool:
        """Simple Thai language detection"""
        thai_chars = sum(1 for c in text if '\u0e00' <= c <= '\u0e7f')
        return thai_chars > len(text) * 0.1


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ChatMessage:
    """Chat message with metadata"""
    message_id: UUID
    role: MessageRole
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: Optional[int] = None

    def to_message(self) -> Message:
        """Convert to LLM Message"""
        return Message(role=self.role, content=self.content)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": str(self.message_id),
            "role": self.role.value,
            "content": self.content,
            "sources": self.sources,
            "created_at": self.created_at.isoformat(),
            "response_time_ms": self.response_time_ms,
        }


@dataclass
class Conversation:
    """Conversation with messages"""
    conversation_id: UUID
    user_id: Optional[UUID] = None
    title: Optional[str] = None
    messages: List[ChatMessage] = field(default_factory=list)
    rag_enabled: bool = True
    rag_settings: Optional[RAGSettings] = None
    model_provider: str = "ollama"
    model_name: str = "llama3.2:1b"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: MessageRole, content: str, sources: Optional[List] = None) -> ChatMessage:
        """Add message to conversation"""
        msg = ChatMessage(
            message_id=uuid4(),
            role=role,
            content=content,
            sources=sources,
        )
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
        return msg

    def get_history(self, max_messages: int = 10) -> List[Message]:
        """Get conversation history as Messages"""
        recent = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        return [msg.to_message() for msg in recent]


@dataclass
class ChatRequest:
    """Chat request"""
    message: str
    conversation_id: Optional[UUID] = None
    rag_enabled: bool = True
    rag_settings: Optional[Dict[str, Any]] = None
    document_ids: Optional[List[UUID]] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    stream: bool = True


@dataclass
class ChatResponse:
    """Chat response"""
    message_id: UUID
    conversation_id: UUID
    content: str
    sources: List[Dict[str, Any]]
    model: str
    provider: str
    response_time_ms: int
    tokens_used: int


@dataclass
class StreamEvent:
    """SSE stream event"""
    event_type: str  # session, search_start, search_results, content, sources, done, error
    data: Dict[str, Any]

    def to_sse(self) -> str:
        """Format as SSE event"""
        return f"data: {json.dumps({'type': self.event_type, **self.data})}\n\n"


# =============================================================================
# CHAT SERVICE
# =============================================================================

class ChatService:
    """
    Chat Service - Orchestrates RAG + LLM

    Features:
    - RAG context retrieval
    - Streaming responses with SSE
    - Source citation
    - Conversation management
    """

    def __init__(self):
        self.llm_service = get_llm_service()
        self.rag_service = get_rag_service()
        self._conversations: Dict[UUID, Conversation] = {}  # In-memory for now

    # =========================================================================
    # MAIN CHAT API
    # =========================================================================

    async def chat(
        self,
        request: ChatRequest,
        user_id: Optional[UUID] = None,
    ) -> ChatResponse:
        """
        Process chat request (non-streaming)

        Returns complete response with sources
        """
        import time
        start_time = time.time()

        # Get or create conversation
        conversation = self._get_or_create_conversation(
            request.conversation_id,
            user_id,
            request.provider,
            request.model,
        )

        # Add user message
        conversation.add_message(MessageRole.USER, request.message)

        # Get RAG context if enabled
        context = ""
        sources: List[SearchResult] = []

        if request.rag_enabled:
            rag_settings = RAGSettings.from_dict(request.rag_settings) if request.rag_settings else None
            context, sources = await self.rag_service.build_context(
                query=request.message,
                settings=rag_settings,
                user_id=user_id,
                document_ids=request.document_ids,
            )

        # Build messages
        messages = self._build_messages(conversation, context)

        # Get LLM config
        config = self._get_llm_config(request.provider, request.model)

        # Generate response
        llm_response = await self.llm_service.generate(messages, config)

        # Add assistant message
        source_dicts = self._format_sources(sources)
        assistant_msg = conversation.add_message(
            MessageRole.ASSISTANT,
            llm_response.content,
            sources=source_dicts,
        )
        assistant_msg.response_time_ms = llm_response.response_time_ms

        response_time = int((time.time() - start_time) * 1000)

        return ChatResponse(
            message_id=assistant_msg.message_id,
            conversation_id=conversation.conversation_id,
            content=llm_response.content,
            sources=source_dicts,
            model=llm_response.model,
            provider=llm_response.provider,
            response_time_ms=response_time,
            tokens_used=llm_response.total_tokens,
        )

    async def chat_stream(
        self,
        request: ChatRequest,
        user_id: Optional[UUID] = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Process chat request with streaming

        Yields SSE events:
        - session: Session info
        - search_start: RAG search started
        - search_results: RAG results found
        - content: Response content chunk
        - sources: Source citations
        - done: Stream complete
        - error: Error occurred
        """
        import time
        start_time = time.time()

        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation(
                request.conversation_id,
                user_id,
                request.provider,
                request.model,
            )

            # Send session event
            yield StreamEvent(
                event_type="session",
                data={
                    "conversation_id": str(conversation.conversation_id),
                    "model": conversation.model_name,
                    "provider": conversation.model_provider,
                }
            )

            # Add user message
            conversation.add_message(MessageRole.USER, request.message)

            # Get RAG context if enabled
            context = ""
            sources: List[SearchResult] = []

            if request.rag_enabled:
                yield StreamEvent(event_type="search_start", data={"query": request.message})

                rag_settings = RAGSettings.from_dict(request.rag_settings) if request.rag_settings else None
                context, sources = await self.rag_service.build_context(
                    query=request.message,
                    settings=rag_settings,
                    user_id=user_id,
                    document_ids=request.document_ids,
                )

                yield StreamEvent(
                    event_type="search_results",
                    data={
                        "count": len(sources),
                        "sources": [
                            {
                                "document": s.document_title or s.document_filename,
                                "page": s.page_number,
                                "score": round(s.score, 3),
                            }
                            for s in sources[:5]  # Preview first 5
                        ]
                    }
                )

            # Build messages
            messages = self._build_messages(conversation, context)

            # Get LLM config
            config = self._get_llm_config(request.provider, request.model)

            # Stream response
            full_content = ""
            async for chunk in self.llm_service.stream(messages, config):
                if chunk.content:
                    full_content += chunk.content
                    yield StreamEvent(
                        event_type="content",
                        data={"content": chunk.content}
                    )

                if chunk.is_done:
                    break

            # Format and send sources
            source_dicts = self._format_sources(sources)
            if source_dicts:
                yield StreamEvent(
                    event_type="sources",
                    data={"sources": source_dicts}
                )

            # Add assistant message
            assistant_msg = conversation.add_message(
                MessageRole.ASSISTANT,
                full_content,
                sources=source_dicts,
            )

            response_time = int((time.time() - start_time) * 1000)
            assistant_msg.response_time_ms = response_time

            # Send done event
            yield StreamEvent(
                event_type="done",
                data={
                    "message_id": str(assistant_msg.message_id),
                    "response_time_ms": response_time,
                }
            )

        except Exception as e:
            yield StreamEvent(
                event_type="error",
                data={"error": str(e)}
            )

    # =========================================================================
    # CONVERSATION MANAGEMENT
    # =========================================================================

    def _get_or_create_conversation(
        self,
        conversation_id: Optional[UUID],
        user_id: Optional[UUID],
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Conversation:
        """Get existing or create new conversation"""
        if conversation_id and conversation_id in self._conversations:
            return self._conversations[conversation_id]

        # Create new conversation
        conv_id = conversation_id or uuid4()
        conversation = Conversation(
            conversation_id=conv_id,
            user_id=user_id,
            model_provider=provider or "ollama",
            model_name=model or "llama3.2:1b",
        )
        self._conversations[conv_id] = conversation
        return conversation

    def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self._conversations.get(conversation_id)

    def list_conversations(self, user_id: Optional[UUID] = None) -> List[Conversation]:
        """List conversations, optionally filtered by user"""
        conversations = list(self._conversations.values())
        if user_id:
            conversations = [c for c in conversations if c.user_id == user_id]
        return sorted(conversations, key=lambda c: c.updated_at, reverse=True)

    def delete_conversation(self, conversation_id: UUID) -> bool:
        """Delete conversation"""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _build_messages(
        self,
        conversation: Conversation,
        context: str,
        max_history: int = 10,
    ) -> List[Message]:
        """Build message list for LLM"""
        messages = []

        # Add system prompt
        if context:
            system_prompt = PromptTemplates.get_rag_prompt(context)
        else:
            system_prompt = PromptTemplates.SYSTEM_DEFAULT

        messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))

        # Add conversation history (excluding current user message which is already in context)
        history = conversation.get_history(max_history)
        messages.extend(history)

        return messages

    def _get_llm_config(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> LLMConfig:
        """Get LLM configuration"""
        config = LLMConfig.from_settings()
        if provider:
            config.provider = LLMProvider(provider)
        if model:
            config.model = model
        return config

    def _format_sources(self, sources: List[SearchResult]) -> List[Dict[str, Any]]:
        """Format search results as source citations"""
        return [
            {
                "index": i + 1,
                "document_id": str(s.document_id),
                "document_name": s.document_title or s.document_filename or "Untitled",
                "page_number": s.page_number,
                "section": s.section_title,
                "content_preview": s.content[:200] + "..." if len(s.content) > 200 else s.content,
                "score": round(s.score, 3),
            }
            for i, s in enumerate(sources)
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Check chat service health"""
        llm_health = await self.llm_service.health_check()
        return {
            "status": llm_health.get("status", "unknown"),
            "conversations_in_memory": len(self._conversations),
            "llm": llm_health,
        }


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get or create ChatService singleton"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
