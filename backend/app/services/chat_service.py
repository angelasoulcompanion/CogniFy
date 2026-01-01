"""
CogniFy Chat Service

Orchestrates:
- RAG retrieval
- LLM generation with Structured JSON Output
- Conversation management
- Source citation

Created with love by Angela & David - 2 January 2026
"""

import json
import re
from typing import Optional, List, Dict, Any, AsyncGenerator, Tuple, Union
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

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
from app.infrastructure.repositories.conversation_repository import (
    get_conversation_repository,
    ConversationRepository,
)


# =============================================================================
# STRUCTURED RESPONSE SCHEMA (Pydantic)
# =============================================================================

class ContentItem(BaseModel):
    """A single content item - can be text or a key-value fact"""
    type: str = Field(description="Type: 'text', 'fact', or 'list_item'")
    text: Optional[str] = Field(default=None, description="Text content")
    label: Optional[str] = Field(default=None, description="Label for fact type")
    value: Optional[str] = Field(default=None, description="Value for fact type")


class Section(BaseModel):
    """A section with heading and content items"""
    heading: str = Field(description="Section heading")
    items: List[ContentItem] = Field(description="Content items in this section")


class StructuredRAGResponse(BaseModel):
    """Structured response format for RAG queries"""
    title: str = Field(description="Main title/summary of the response")
    sections: List[Section] = Field(description="Content sections")
    sources_used: List[int] = Field(description="List of source numbers used [1], [2], etc.")


# JSON Schema for LLM prompt
STRUCTURED_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Main title/summary"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["text", "fact", "list_item"]},
                                "text": {"type": "string"},
                                "label": {"type": "string"},
                                "value": {"type": "string"}
                            },
                            "required": ["type"]
                        }
                    }
                },
                "required": ["heading", "items"]
            }
        },
        "sources_used": {"type": "array", "items": {"type": "integer"}}
    },
    "required": ["title", "sections", "sources_used"]
}


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

class PromptTemplates:
    """RAG prompt templates with strong language enforcement and expert roles"""

    # Expert role definitions
    EXPERT_ROLES = {
        "general": {
            "en": "You are CogniFy, an intelligent assistant that helps users understand their documents and data.",
            "th": "คุณคือ CogniFy ผู้ช่วยอัจฉริยะที่ช่วยผู้ใช้เข้าใจเอกสารและข้อมูลของพวกเขา",
        },
        "financial_analyst": {
            "en": "You are CogniFy acting as an expert Financial Analyst. You specialize in analyzing financial data, reading financial statements, understanding market trends, and providing insights on revenue, costs, profitability, and financial health. Focus on quantitative analysis, ratios, trends, and actionable financial insights.",
            "th": "คุณคือ CogniFy ในบทบาทนักวิเคราะห์การเงินผู้เชี่ยวชาญ คุณเชี่ยวชาญในการวิเคราะห์ข้อมูลทางการเงิน อ่านงบการเงิน เข้าใจแนวโน้มตลาด และให้ข้อมูลเชิงลึกเกี่ยวกับรายได้ ต้นทุน กำไร และสถานะทางการเงิน มุ่งเน้นการวิเคราะห์เชิงปริมาณ อัตราส่วน แนวโน้ม และข้อมูลเชิงลึกที่นำไปปฏิบัติได้",
        },
        "legal_expert": {
            "en": "You are CogniFy acting as an expert Legal Advisor. You specialize in analyzing contracts, legal documents, compliance requirements, and regulatory matters. Focus on identifying key terms, obligations, risks, and legal implications. Always recommend consulting with qualified legal counsel for final decisions.",
            "th": "คุณคือ CogniFy ในบทบาทที่ปรึกษากฎหมายผู้เชี่ยวชาญ คุณเชี่ยวชาญในการวิเคราะห์สัญญา เอกสารกฎหมาย ข้อกำหนดการปฏิบัติตามกฎระเบียบ มุ่งเน้นระบุข้อกำหนดสำคัญ ภาระผูกพัน ความเสี่ยง และผลกระทบทางกฎหมาย แนะนำให้ปรึกษาที่ปรึกษากฎหมายที่มีคุณสมบัติเหมาะสมสำหรับการตัดสินใจขั้นสุดท้าย",
        },
        "technical_writer": {
            "en": "You are CogniFy acting as an expert Technical Writer. You specialize in creating clear, well-structured documentation, technical specifications, and user guides. Focus on clarity, accuracy, logical organization, and making complex information accessible to the target audience.",
            "th": "คุณคือ CogniFy ในบทบาทนักเขียนเทคนิคผู้เชี่ยวชาญ คุณเชี่ยวชาญในการสร้างเอกสารที่ชัดเจน มีโครงสร้างดี ข้อกำหนดทางเทคนิค และคู่มือผู้ใช้ มุ่งเน้นความชัดเจน ความถูกต้อง การจัดระเบียบอย่างเป็นตรรกะ และทำให้ข้อมูลซับซ้อนเข้าถึงได้สำหรับกลุ่มเป้าหมาย",
        },
        "data_analyst": {
            "en": "You are CogniFy acting as an expert Data Analyst. You specialize in identifying patterns, trends, and insights from data. Focus on statistical analysis, data visualization recommendations, correlation discovery, and data-driven conclusions. Present findings clearly with supporting evidence.",
            "th": "คุณคือ CogniFy ในบทบาทนักวิเคราะห์ข้อมูลผู้เชี่ยวชาญ คุณเชี่ยวชาญในการระบุรูปแบบ แนวโน้ม และข้อมูลเชิงลึกจากข้อมูล มุ่งเน้นการวิเคราะห์เชิงสถิติ คำแนะนำการแสดงผลข้อมูล การค้นพบความสัมพันธ์ และข้อสรุปที่ขับเคลื่อนด้วยข้อมูล นำเสนอผลการค้นพบอย่างชัดเจนพร้อมหลักฐานสนับสนุน",
        },
        "business_consultant": {
            "en": "You are CogniFy acting as an expert Business Consultant. You specialize in strategic analysis, operational efficiency, market positioning, and business development. Focus on identifying opportunities, challenges, and actionable recommendations for business improvement.",
            "th": "คุณคือ CogniFy ในบทบาทที่ปรึกษาธุรกิจผู้เชี่ยวชาญ คุณเชี่ยวชาญในการวิเคราะห์เชิงกลยุทธ์ ประสิทธิภาพการดำเนินงาน การวางตำแหน่งตลาด และการพัฒนาธุรกิจ มุ่งเน้นการระบุโอกาส ความท้าทาย และคำแนะนำที่นำไปปฏิบัติได้เพื่อปรับปรุงธุรกิจ",
        },
        "researcher": {
            "en": "You are CogniFy acting as an expert Researcher. You specialize in academic and scientific analysis, literature review, methodology evaluation, and evidence-based conclusions. Focus on rigorous analysis, citing sources accurately, and maintaining academic objectivity.",
            "th": "คุณคือ CogniFy ในบทบาทนักวิจัยผู้เชี่ยวชาญ คุณเชี่ยวชาญในการวิเคราะห์เชิงวิชาการและวิทยาศาสตร์ การทบทวนวรรณกรรม การประเมินวิธีการ และข้อสรุปที่อิงหลักฐาน มุ่งเน้นการวิเคราะห์อย่างเข้มงวด อ้างอิงแหล่งที่มาอย่างถูกต้อง และรักษาความเป็นกลางทางวิชาการ",
        },
    }

    # Structured JSON prompt for RAG (English)
    SYSTEM_RAG = """{{expert_role}}

Below is relevant context from the user's documents. Answer the question using this context.

--- CONTEXT ---
{context}
--- END CONTEXT ---

CRITICAL: You MUST respond in valid JSON format only. No markdown, no plain text.

Response language: {response_language}. DO NOT use Chinese characters.

JSON SCHEMA:
{{
  "title": "Brief summary title",
  "sections": [
    {{
      "heading": "Section heading",
      "items": [
        {{"type": "text", "text": "Paragraph of explanation"}},
        {{"type": "fact", "label": "Key metric", "value": "123,456"}},
        {{"type": "list_item", "text": "A bullet point item"}}
      ]
    }}
  ],
  "sources_used": [1, 2]
}}

ITEM TYPES:
- "text": For paragraphs/explanations
- "fact": For key-value data (label + value)
- "list_item": For bullet points

EXAMPLE:
{{
  "title": "Revenue Summary 2023",
  "sections": [
    {{
      "heading": "Total Revenue",
      "items": [
        {{"type": "fact", "label": "Total Revenue", "value": "$5.2 million"}},
        {{"type": "fact", "label": "Domestic", "value": "85%"}},
        {{"type": "fact", "label": "International", "value": "15%"}}
      ]
    }},
    {{
      "heading": "Growth Analysis",
      "items": [
        {{"type": "text", "text": "Revenue increased by 12% compared to last year."}},
        {{"type": "list_item", "text": "Previous year: $4.6 million"}},
        {{"type": "list_item", "text": "Current year: $5.2 million"}}
      ]
    }}
  ],
  "sources_used": [1, 2]
}}

Respond with ONLY valid JSON. No text before or after."""

    # Structured JSON prompt for RAG (Thai)
    SYSTEM_RAG_THAI = """{{expert_role}}

ด้านล่างนี้คือบริบทจากเอกสาร ใช้ตอบคำถาม

--- บริบท ---
{context}
--- จบบริบท ---

สำคัญมาก: ตอบเป็น JSON เท่านั้น ห้ามตอบเป็น markdown หรือข้อความธรรมดา

กฎภาษา: ตอบเป็นภาษาไทย ห้ามใช้ภาษาจีน

JSON SCHEMA:
{{
  "title": "หัวข้อสรุป",
  "sections": [
    {{
      "heading": "หัวข้อส่วน",
      "items": [
        {{"type": "text", "text": "คำอธิบาย"}},
        {{"type": "fact", "label": "ชื่อข้อมูล", "value": "ค่า"}},
        {{"type": "list_item", "text": "รายการ"}}
      ]
    }}
  ],
  "sources_used": [1, 2]
}}

ประเภท item:
- "text": สำหรับย่อหน้าอธิบาย
- "fact": สำหรับข้อมูลคู่ (label + value)
- "list_item": สำหรับรายการ bullet

ตัวอย่าง:
{{
  "title": "สรุปรายได้ปี 2567",
  "sections": [
    {{
      "heading": "รายได้รวม",
      "items": [
        {{"type": "fact", "label": "รายได้รวม", "value": "539 ล้านบาท"}},
        {{"type": "fact", "label": "รายได้ในประเทศ", "value": "100%"}},
        {{"type": "fact", "label": "รายได้ต่างประเทศ", "value": "ไม่มี"}}
      ]
    }},
    {{
      "heading": "การเติบโต",
      "items": [
        {{"type": "text", "text": "รายได้ลดลง 16.6% เมื่อเทียบกับปีก่อน"}},
        {{"type": "list_item", "text": "ปีก่อน: 646 ล้านบาท"}},
        {{"type": "list_item", "text": "ปีนี้: 539 ล้านบาท"}}
      ]
    }}
  ],
  "sources_used": [1, 2]
}}

ตอบเป็น JSON เท่านั้น ห้ามมีข้อความอื่นก่อนหรือหลัง"""

    SYSTEM_NO_CONTEXT = """{{expert_role}}

The user's question doesn't seem to require document context. Answer based on your general knowledge and expertise.

CRITICAL: You MUST respond in {response_language}. DO NOT respond in Chinese unless asked in Chinese.

FORMATTING:
- Use Markdown format (headers, bullets, bold)
- Structure your response clearly
- Never respond with unformatted wall of text

Be helpful, accurate, and concise."""

    @classmethod
    def get_expert_role(cls, expert: str, is_thai: bool = False) -> str:
        """Get expert role description"""
        role = cls.EXPERT_ROLES.get(expert, cls.EXPERT_ROLES["general"])
        return role["th"] if is_thai else role["en"]

    @classmethod
    def get_rag_prompt(cls, context: str, question: str = "", language: str = "auto", expert: str = "general") -> str:
        """
        Get RAG system prompt with context, language enforcement, and expert role.

        Priority for language detection:
        1. Explicit language parameter
        2. User's question language
        3. Context/document language
        """
        # Detect language from question first, then context
        is_thai_question = cls._detect_thai(question) if question else False
        is_thai_context = cls._detect_thai(context)

        # Get expert role
        expert_role = cls.get_expert_role(expert, is_thai_question)

        # Thai question = Thai response (highest priority)
        if language == "th" or is_thai_question:
            prompt = cls.SYSTEM_RAG_THAI.replace("{{expert_role}}", expert_role)
            return prompt.format(context=context)

        # English or other - use English prompt with explicit language instruction
        response_language = "Thai" if is_thai_context else "the same language as the user's question"
        prompt = cls.SYSTEM_RAG.replace("{{expert_role}}", expert_role)
        return prompt.format(context=context, response_language=response_language)

    @classmethod
    def get_no_context_prompt(cls, question: str = "", expert: str = "general") -> str:
        """Get no-context prompt with language detection and expert role"""
        is_thai = cls._detect_thai(question) if question else False
        expert_role = cls.get_expert_role(expert, is_thai)
        response_language = "Thai (ภาษาไทย)" if is_thai else "the same language as the user's question"
        prompt = cls.SYSTEM_NO_CONTEXT.replace("{{expert_role}}", expert_role)
        return prompt.format(response_language=response_language)

    @classmethod
    def _detect_thai(cls, text: str) -> bool:
        """Detect Thai language in text"""
        if not text:
            return False
        thai_chars = sum(1 for c in text if '\u0e00' <= c <= '\u0e7f')
        return thai_chars > len(text) * 0.05  # Lower threshold for better detection

    # Chinese to Thai replacement map
    CHINESE_REPLACEMENTS = {
        "占比": "คิดเป็น",
        "增长": "เพิ่มขึ้น",
        "下降": "ลดลง",
        "总计": "รวม",
        "分析": "วิเคราะห์",
        "百分比": "เปอร์เซ็นต์",
        "比例": "สัดส่วน",
        "增加": "เพิ่มขึ้น",
        "减少": "ลดลง",
        "总额": "ยอดรวม",
        "收入": "รายได้",
        "支出": "รายจ่าย",
        "利润": "กำไร",
        "亏损": "ขาดทุน",
        "年": "ปี",
        "月": "เดือน",
        "日": "วัน",
    }

    @classmethod
    def filter_chinese(cls, text: str) -> str:
        """
        Post-process text to remove/replace Chinese characters.
        This is the proper way to handle Qwen's tendency to mix Chinese.
        """
        if not text:
            return text

        # First, replace known Chinese phrases with Thai
        for cn, th in cls.CHINESE_REPLACEMENTS.items():
            text = text.replace(cn, th)

        # Then, remove any remaining Chinese characters (CJK Unified Ideographs)
        # Range: \u4e00-\u9fff (CJK), \u3400-\u4dbf (CJK Ext A)
        import re
        text = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf]+', '', text)

        # Clean up any double spaces left behind
        text = re.sub(r'  +', ' ', text)

        return text.strip()

    @classmethod
    def fix_markdown_formatting(cls, text: str) -> str:
        """
        Fix markdown formatting issues from LLM output.
        Small models often forget newlines and spaces around headers.
        """
        if not text:
            return text

        import re

        # Step 1: Add space after ## if missing (##การประกอบ → ## การประกอบ)
        text = re.sub(r'(#{2,4})([^\s#\n])', r'\1 \2', text)

        # Step 2: Add newline BEFORE headers if missing
        # Match: any char (not newline) followed by ##
        text = re.sub(r'([^\n])(#{2,4}\s)', r'\1\n\n\2', text)

        # Step 3: Add newline AFTER header line if missing
        # Match: ## Header text (to end of conceptual header) followed by non-newline
        text = re.sub(r'(#{2,4}\s[^\n]{1,100})([^\n])(#{2,4}\s)', r'\1\2\n\n\3', text)

        # Step 4: Add newline before bullet points if missing
        text = re.sub(r'([^\n\-])([-]\s)', r'\1\n\2', text)

        # Step 5: Fix multiple consecutive newlines (max 2)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Step 6: Clean up spaces before newlines
        text = re.sub(r' +\n', '\n', text)

        return text.strip()

    @classmethod
    def parse_structured_response(cls, text: str) -> Dict[str, Any]:
        """
        Parse LLM response as structured JSON.
        Returns structured data or fallback plain text format.
        """
        if not text:
            return {"title": "Response", "sections": [], "sources_used": [], "raw_text": ""}

        # Filter Chinese first
        text = cls.filter_chinese(text)

        # Try to extract JSON from response
        # LLM might add text before/after JSON, so try to find JSON block
        json_match = re.search(r'\{[\s\S]*\}', text)

        if json_match:
            try:
                json_str = json_match.group(0)
                data = json.loads(json_str)

                # Validate required fields
                if "title" in data and "sections" in data:
                    # Ensure sources_used exists
                    if "sources_used" not in data:
                        data["sources_used"] = []
                    return data

            except json.JSONDecodeError:
                pass

        # Fallback: convert plain text to structured format
        return cls._text_to_structured(text)

    @classmethod
    def _text_to_structured(cls, text: str) -> Dict[str, Any]:
        """Convert plain text/markdown to structured format as fallback"""
        # Fix markdown formatting first
        text = cls.fix_markdown_formatting(text)

        sections = []
        current_section = {"heading": "Response", "items": []}
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for headers
            if line.startswith('## '):
                if current_section["items"]:
                    sections.append(current_section)
                current_section = {"heading": line[3:].strip(), "items": []}
            elif line.startswith('### '):
                if current_section["items"]:
                    sections.append(current_section)
                current_section = {"heading": line[4:].strip(), "items": []}
            elif line.startswith('- ') or line.startswith('* '):
                item_text = line[2:].strip()
                # Check for fact format: **Label**: Value or **Label:** Value
                fact_match = re.match(r'\*\*(.+?)\*\*:\s*(.+)', item_text)
                if fact_match:
                    current_section["items"].append({
                        "type": "fact",
                        "label": fact_match.group(1).strip(),
                        "value": fact_match.group(2).strip()
                    })
                else:
                    current_section["items"].append({
                        "type": "list_item",
                        "text": item_text
                    })
            elif ':' in line and len(line.split(':')[0]) < 30:
                # Looks like a fact (key: value) without bullet
                parts = line.split(':', 1)
                label = parts[0].strip().replace('**', '')  # Remove bold markers
                current_section["items"].append({
                    "type": "fact",
                    "label": label,
                    "value": parts[1].strip()
                })
            else:
                current_section["items"].append({
                    "type": "text",
                    "text": line
                })

        if current_section["items"]:
            sections.append(current_section)

        # If no sections created, create one with the whole text
        if not sections:
            sections = [{"heading": "Response", "items": [{"type": "text", "text": text}]}]

        return {
            "title": sections[0]["heading"] if sections else "Response",
            "sections": sections,
            "sources_used": [],
            "raw_text": text
        }

    @classmethod
    def structured_to_markdown(cls, data: Dict[str, Any]) -> str:
        """Convert structured response back to markdown for storage"""
        lines = []

        if data.get("title"):
            lines.append(f"## {data['title']}")
            lines.append("")

        for section in data.get("sections", []):
            if section.get("heading") and section["heading"] != data.get("title"):
                lines.append(f"### {section['heading']}")
                lines.append("")

            for item in section.get("items", []):
                item_type = item.get("type", "text")
                if item_type == "text":
                    lines.append(item.get("text", ""))
                    lines.append("")
                elif item_type == "fact":
                    lines.append(f"- **{item.get('label', '')}**: {item.get('value', '')}")
                elif item_type == "list_item":
                    lines.append(f"- {item.get('text', '')}")

            lines.append("")

        if data.get("sources_used"):
            lines.append(f"Sources: {data['sources_used']}")

        return "\n".join(lines).strip()


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
    expert: str = "general"
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
        self.conversation_repo = get_conversation_repository()
        self._conversations: Dict[UUID, Conversation] = {}  # In-memory cache

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
        conversation = await self._get_or_create_conversation(
            request.conversation_id,
            user_id,
            request.provider,
            request.model,
        )

        # Add user message
        conversation.add_message(MessageRole.USER, request.message)

        # Persist user message to database
        await self.conversation_repo.add_message(
            conversation_id=conversation.conversation_id,
            message_type="user",
            content=request.message,
        )

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

        # Build messages with question for language detection and expert role
        messages = self._build_messages(conversation, context, question=request.message, expert=request.expert)

        # Get LLM config
        config = self._get_llm_config(request.provider, request.model)

        # Generate response
        llm_response = await self.llm_service.generate(messages, config)

        # Post-process: Filter Chinese + Fix markdown formatting
        filtered_content = PromptTemplates.filter_chinese(llm_response.content)
        filtered_content = PromptTemplates.fix_markdown_formatting(filtered_content)

        # Add assistant message
        source_dicts = self._format_sources(sources)
        assistant_msg = conversation.add_message(
            MessageRole.ASSISTANT,
            filtered_content,
            sources=source_dicts,
        )
        assistant_msg.response_time_ms = llm_response.response_time_ms

        response_time = int((time.time() - start_time) * 1000)

        # Persist assistant message to database
        await self.conversation_repo.add_message(
            conversation_id=conversation.conversation_id,
            message_type="assistant",
            content=filtered_content,
            sources_used=source_dicts if source_dicts else None,
            response_time_ms=response_time,
        )

        # Generate title if first message
        if len(conversation.messages) == 2:  # user + assistant
            await self.conversation_repo.generate_title(conversation.conversation_id)

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
            conversation = await self._get_or_create_conversation(
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

            # Persist user message to database
            await self.conversation_repo.add_message(
                conversation_id=conversation.conversation_id,
                message_type="user",
                content=request.message,
            )

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

            # Build messages with question for language detection and expert role
            messages = self._build_messages(conversation, context, question=request.message, expert=request.expert)

            # Get LLM config
            config = self._get_llm_config(request.provider, request.model)

            # Stream response
            full_content = ""
            async for chunk in self.llm_service.stream(messages, config):
                if chunk.content:
                    # Filter Chinese characters from each chunk
                    filtered_chunk = PromptTemplates.filter_chinese(chunk.content)
                    if filtered_chunk:  # Only send if content remains after filtering
                        full_content += filtered_chunk
                        yield StreamEvent(
                            event_type="content",
                            data={"content": filtered_chunk}
                        )

                if chunk.is_done:
                    break

            # Parse as structured JSON response
            structured_data = PromptTemplates.parse_structured_response(full_content)

            # Convert back to markdown for storage
            markdown_content = PromptTemplates.structured_to_markdown(structured_data)

            # Send structured response for frontend to render
            yield StreamEvent(
                event_type="structured_response",
                data={"structured": structured_data}
            )

            # Format and send sources
            source_dicts = self._format_sources(sources)
            if source_dicts:
                yield StreamEvent(
                    event_type="sources",
                    data={"sources": source_dicts}
                )

            # Add assistant message (store markdown version)
            assistant_msg = conversation.add_message(
                MessageRole.ASSISTANT,
                markdown_content,
                sources=source_dicts,
            )

            response_time = int((time.time() - start_time) * 1000)
            assistant_msg.response_time_ms = response_time

            # Persist assistant message to database (markdown version)
            await self.conversation_repo.add_message(
                conversation_id=conversation.conversation_id,
                message_type="assistant",
                content=markdown_content,
                sources_used=source_dicts if source_dicts else None,
                response_time_ms=response_time,
            )

            # Generate title if first message
            if len(conversation.messages) == 2:  # user + assistant
                await self.conversation_repo.generate_title(conversation.conversation_id)

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

    async def _get_or_create_conversation(
        self,
        conversation_id: Optional[UUID],
        user_id: Optional[UUID],
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Conversation:
        """Get existing or create new conversation (with DB persistence)"""
        # Check in-memory cache first
        if conversation_id and conversation_id in self._conversations:
            return self._conversations[conversation_id]

        # Check database if conversation_id provided
        if conversation_id:
            db_conv = await self.conversation_repo.get_conversation(conversation_id)
            if db_conv:
                # Load messages from database
                messages = await self.conversation_repo.get_last_messages(conversation_id, 20)
                chat_messages = [
                    ChatMessage(
                        message_id=UUID(m["message_id"]),
                        role=MessageRole.USER if m["message_type"] == "user" else MessageRole.ASSISTANT,
                        content=m["content"],
                        sources=m.get("sources_used"),
                        created_at=datetime.fromisoformat(m["created_at"]) if isinstance(m["created_at"], str) else m["created_at"],
                        response_time_ms=m.get("response_time_ms"),
                    )
                    for m in messages
                ]
                conversation = Conversation(
                    conversation_id=UUID(db_conv["conversation_id"]),
                    user_id=UUID(db_conv["user_id"]) if db_conv.get("user_id") else None,
                    title=db_conv.get("title"),
                    messages=chat_messages,
                    rag_enabled=db_conv.get("rag_enabled", True),
                    model_provider=db_conv.get("model_provider", "ollama"),
                    model_name=db_conv.get("model_name", "llama3.2:1b"),
                    created_at=datetime.fromisoformat(db_conv["created_at"]) if isinstance(db_conv["created_at"], str) else db_conv["created_at"],
                    updated_at=datetime.fromisoformat(db_conv["updated_at"]) if isinstance(db_conv["updated_at"], str) else db_conv["updated_at"],
                )
                self._conversations[conversation_id] = conversation
                return conversation

        # Create new conversation in database
        db_conv = await self.conversation_repo.create_conversation(
            user_id=user_id,
            model_provider=provider or "ollama",
            model_name=model or "llama3.2:1b",
        )

        conv_id = UUID(db_conv["conversation_id"])
        conversation = Conversation(
            conversation_id=conv_id,
            user_id=user_id,
            model_provider=provider or "ollama",
            model_name=model or "llama3.2:1b",
        )
        self._conversations[conv_id] = conversation
        return conversation

    async def get_conversation(self, conversation_id: UUID) -> Optional[Dict[str, Any]]:
        """Get conversation by ID from database"""
        # Try cache first
        if conversation_id in self._conversations:
            conv = self._conversations[conversation_id]
            return {
                "conversation_id": str(conv.conversation_id),
                "user_id": str(conv.user_id) if conv.user_id else None,
                "title": conv.title,
                "model_provider": conv.model_provider,
                "model_name": conv.model_name,
                "rag_enabled": conv.rag_enabled,
                "message_count": len(conv.messages),
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
            }

        # Get from database
        return await self.conversation_repo.get_conversation(conversation_id)

    async def list_conversations(
        self,
        user_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List conversations from database"""
        return await self.conversation_repo.list_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """Delete conversation from database"""
        # Remove from cache
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]

        # Delete from database
        return await self.conversation_repo.delete_conversation(conversation_id)

    async def get_conversation_stats(
        self,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get conversation statistics from database"""
        return await self.conversation_repo.get_conversation_stats(user_id)

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _build_messages(
        self,
        conversation: Conversation,
        context: str,
        question: str = "",
        expert: str = "general",
        max_history: int = 10,
    ) -> List[Message]:
        """Build message list for LLM with proper language detection and expert role"""
        messages = []

        # Add system prompt with language detection and expert role
        if context:
            system_prompt = PromptTemplates.get_rag_prompt(context, question=question, expert=expert)
        else:
            system_prompt = PromptTemplates.get_no_context_prompt(question=question, expert=expert)

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
