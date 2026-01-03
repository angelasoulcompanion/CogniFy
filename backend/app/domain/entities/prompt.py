"""
CogniFy Prompt Template Entity

Domain entity for prompt templates with validation and rendering.
Created with love by Angela & David - 2 January 2026
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import re


class PromptCategory(str, Enum):
    """Prompt category types"""
    RAG = "rag"
    SYSTEM = "system"
    SUMMARIZATION = "summarization"
    ANALYSIS = "analysis"
    CUSTOM = "custom"


class ExpertRole(str, Enum):
    """Expert role types"""
    GENERAL = "general"
    FINANCIAL = "financial"
    LEGAL = "legal"
    TECHNICAL = "technical"
    DATA = "data"
    BUSINESS = "business"
    RESEARCHER = "researcher"
    AI_ENGINEER = "ai_engineer"


@dataclass
class PromptVariable:
    """Variable definition for prompt template"""
    name: str
    required: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "required": self.required,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data) -> "PromptVariable":
        """Create from dict or string (for backwards compatibility)"""
        # Handle string input (legacy format like ["context"])
        if isinstance(data, str):
            return cls(name=data, required=True, description="")
        # Handle dict input (proper format)
        return cls(
            name=data.get("name", ""),
            required=data.get("required", True),
            description=data.get("description", ""),
        )


@dataclass
class PromptTemplate:
    """
    Prompt Template domain entity

    Represents a reusable LLM prompt template with variables,
    categories, and rendering capabilities.
    """

    # Required fields
    name: str
    template_content: str
    category: PromptCategory

    # Identity
    template_id: UUID = field(default_factory=uuid4)
    created_by: Optional[UUID] = None

    # Metadata
    description: Optional[str] = None
    expert_role: Optional[ExpertRole] = None
    language: str = "th"

    # Variables
    variables: List[PromptVariable] = field(default_factory=list)

    # Examples
    example_input: Dict[str, Any] = field(default_factory=dict)
    example_output: Optional[str] = None

    # Settings
    is_default: bool = False
    is_active: bool = True
    usage_count: int = 0
    version: int = 1

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate entity after initialization"""
        self._validate()
        self._extract_variables()

    def _validate(self) -> None:
        """Validate required fields"""
        if not self.name or not self.name.strip():
            raise ValueError("Template name is required")
        if not self.template_content or not self.template_content.strip():
            raise ValueError("Template content is required")
        if not isinstance(self.category, PromptCategory):
            if isinstance(self.category, str):
                self.category = PromptCategory(self.category)
            else:
                raise ValueError(f"Invalid category: {self.category}")
        if self.expert_role and not isinstance(self.expert_role, ExpertRole):
            if isinstance(self.expert_role, str):
                self.expert_role = ExpertRole(self.expert_role)

    def _extract_variables(self) -> None:
        """Extract variables from template content if not provided"""
        if not self.variables:
            # Find all {variable_name} patterns
            pattern = r'\{(\w+)\}'
            matches = re.findall(pattern, self.template_content)
            unique_vars = list(dict.fromkeys(matches))  # Preserve order, remove duplicates
            self.variables = [
                PromptVariable(name=var, required=True)
                for var in unique_vars
            ]

    def render(self, variables: Dict[str, str]) -> str:
        """
        Render template with provided variables.

        Args:
            variables: Dictionary of variable name to value

        Returns:
            Rendered template string

        Raises:
            ValueError: If required variable is missing
        """
        # Check required variables
        for var in self.variables:
            if var.required and var.name not in variables:
                raise ValueError(f"Missing required variable: {var.name}")

        # Replace all variables
        result = self.template_content
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))

        return result

    def get_variable_names(self) -> List[str]:
        """Get list of variable names"""
        return [v.name for v in self.variables]

    def increment_usage(self) -> None:
        """Increment usage count"""
        self.usage_count += 1
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        return {
            "template_id": str(self.template_id),
            "created_by": str(self.created_by) if self.created_by else None,
            "name": self.name,
            "description": self.description,
            "category": self.category.value if isinstance(self.category, PromptCategory) else self.category,
            "expert_role": self.expert_role.value if isinstance(self.expert_role, ExpertRole) else self.expert_role,
            "template_content": self.template_content,
            "variables": [v.to_dict() for v in self.variables],
            "example_input": self.example_input,
            "example_output": self.example_output,
            "language": self.language,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """Create entity from dictionary"""
        variables = []
        if data.get("variables"):
            if isinstance(data["variables"], list):
                variables = [
                    PromptVariable.from_dict(v) if isinstance(v, dict) else v
                    for v in data["variables"]
                ]

        return cls(
            template_id=UUID(data["template_id"]) if data.get("template_id") else uuid4(),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            name=data.get("name", ""),
            description=data.get("description"),
            category=PromptCategory(data["category"]) if data.get("category") else PromptCategory.CUSTOM,
            expert_role=ExpertRole(data["expert_role"]) if data.get("expert_role") else None,
            template_content=data.get("template_content", ""),
            variables=variables,
            example_input=data.get("example_input", {}),
            example_output=data.get("example_output"),
            language=data.get("language", "th"),
            is_default=data.get("is_default", False),
            is_active=data.get("is_active", True),
            usage_count=data.get("usage_count", 0),
            version=data.get("version", 1),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
        )

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> "PromptTemplate":
        """Create entity from database row"""
        import json

        variables = []
        if row.get("variables"):
            var_data = row["variables"]
            if isinstance(var_data, str):
                var_data = json.loads(var_data)
            variables = [PromptVariable.from_dict(v) for v in var_data]

        example_input = row.get("example_input", {})
        if isinstance(example_input, str):
            example_input = json.loads(example_input)

        return cls(
            template_id=row["template_id"] if isinstance(row["template_id"], UUID) else UUID(row["template_id"]),
            created_by=row["created_by"] if row.get("created_by") else None,
            name=row["name"],
            description=row.get("description"),
            category=PromptCategory(row["category"]),
            expert_role=ExpertRole(row["expert_role"]) if row.get("expert_role") else None,
            template_content=row["template_content"],
            variables=variables,
            example_input=example_input,
            example_output=row.get("example_output"),
            language=row.get("language", "th"),
            is_default=row.get("is_default", False),
            is_active=row.get("is_active", True),
            usage_count=row.get("usage_count", 0),
            version=row.get("version", 1),
            created_at=row.get("created_at", datetime.utcnow()),
            updated_at=row.get("updated_at", datetime.utcnow()),
        )


# =============================================================================
# TEMPLATE GUIDES
# =============================================================================

TEMPLATE_GUIDES = {
    PromptCategory.RAG: {
        "title": "RAG Prompt Guidelines",
        "description": "Prompts for retrieval-augmented generation from documents",
        "required_variables": [
            {"name": "context", "description": "Document context from RAG retrieval"},
            {"name": "query", "description": "User's question"},
        ],
        "best_practices": [
            "ระบุ role ที่ชัดเจน (You are a...)",
            "กำหนด format ผลลัพธ์ (bullet points, table, etc.)",
            "บอกให้อ้างอิง source เสมอ [Source X]",
            "กำหนดภาษาตอบ",
            "บอกวิธีจัดการเมื่อไม่พบข้อมูล",
        ],
        "example": """คุณคือผู้ช่วยอัจฉริยะ

--- บริบท ---
{context}
--- จบบริบท ---

ตอบคำถามโดยใช้บริบทด้านบน:
- ตอบเป็นภาษาไทย
- อ้างอิงด้วย [แหล่งที่ X]
- ถ้าไม่พบข้อมูล ให้บอกว่า "ไม่พบข้อมูลในเอกสาร" """,
    },
    PromptCategory.SUMMARIZATION: {
        "title": "Summarization Guidelines",
        "description": "Prompts for summarizing documents or content",
        "required_variables": [
            {"name": "content", "description": "Content to summarize"},
        ],
        "optional_variables": [
            {"name": "length", "description": "Summary length: short, medium, long"},
            {"name": "focus", "description": "Focus area for summary"},
        ],
        "best_practices": [
            "กำหนดความยาวที่ต้องการ",
            "ระบุประเด็นที่ต้องเน้น",
            "บอกให้คงข้อมูลสำคัญ",
            "ใช้ bullet points เพื่อความชัดเจน",
        ],
        "example": """สรุปเนื้อหาต่อไปนี้:

{content}

ความยาว: {length}
- short = 2-3 ประโยค
- medium = 1 ย่อหน้า
- long = หลายย่อหน้า

ใช้ bullet points สำหรับประเด็นสำคัญ""",
    },
    PromptCategory.ANALYSIS: {
        "title": "Analysis Guidelines",
        "description": "Prompts for data analysis and insights",
        "required_variables": [
            {"name": "data", "description": "Data to analyze"},
        ],
        "optional_variables": [
            {"name": "focus", "description": "Analysis focus area"},
            {"name": "compare", "description": "Comparison criteria"},
        ],
        "best_practices": [
            "ระบุประเภทการวิเคราะห์ที่ต้องการ",
            "บอกให้หา patterns และ trends",
            "ขอ actionable insights",
            "ใช้ตารางเมื่อเปรียบเทียบ",
        ],
        "example": """วิเคราะห์ข้อมูลต่อไปนี้:

{data}

จุดเน้น: {focus}

ให้วิเคราะห์:
1. Patterns และ trends
2. ข้อสังเกตสำคัญ
3. คำแนะนำ/Action items""",
    },
    PromptCategory.SYSTEM: {
        "title": "System Prompt Guidelines",
        "description": "Base system prompts for AI behavior",
        "required_variables": [],
        "best_practices": [
            "กำหนด persona ที่ชัดเจน",
            "ระบุขอบเขตความสามารถ",
            "กำหนด tone และ style",
            "บอกวิธีจัดการกรณีไม่แน่ใจ",
        ],
        "example": """คุณคือ CogniFy ผู้ช่วยอัจฉริยะ

หน้าที่:
- ช่วยตอบคำถามทั่วไป
- ใช้ภาษาสุภาพและเป็นมิตร
- ถ้าไม่แน่ใจ ให้บอกตรงๆ

รูปแบบการตอบ:
- ใช้ Markdown
- กระชับ ตรงประเด็น""",
    },
    PromptCategory.CUSTOM: {
        "title": "Custom Prompt Guidelines",
        "description": "Create your own prompt templates",
        "required_variables": [],
        "best_practices": [
            "กำหนด variables ที่ต้องการใช้ {variable_name}",
            "เขียนคำสั่งให้ชัดเจน",
            "ใส่ตัวอย่างผลลัพธ์",
            "ทดสอบก่อนใช้งานจริง",
        ],
        "example": """ใส่คำสั่งของคุณที่นี่...

ใช้ {variable} สำหรับส่วนที่เปลี่ยนแปลงได้""",
    },
}


def get_template_guide(category: PromptCategory) -> Dict[str, Any]:
    """Get template guide for a category"""
    return TEMPLATE_GUIDES.get(category, TEMPLATE_GUIDES[PromptCategory.CUSTOM])
