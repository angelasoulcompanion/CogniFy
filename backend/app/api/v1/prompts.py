"""
CogniFy Prompt Templates API

REST API for prompt template management.
Created with love by Angela & David - 2 January 2026
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.security import get_current_user, require_admin, TokenPayload
from app.services.prompt_service import get_prompt_service, PromptService
from app.domain.entities.prompt import PromptCategory, ExpertRole


router = APIRouter(prefix="/prompts", tags=["prompts"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class VariableSchema(BaseModel):
    """Variable definition"""
    name: str
    required: bool = True
    description: str = ""


class CreatePromptRequest(BaseModel):
    """Create prompt request"""
    name: str = Field(..., min_length=1, max_length=255)
    template_content: str = Field(..., min_length=1)
    category: str = Field(..., description="rag, system, summarization, analysis, custom")
    description: Optional[str] = None
    expert_role: Optional[str] = None
    variables: Optional[List[VariableSchema]] = None
    example_input: Optional[Dict[str, Any]] = None
    example_output: Optional[str] = None
    language: str = "th"
    is_default: bool = False


class UpdatePromptRequest(BaseModel):
    """Update prompt request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_content: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    expert_role: Optional[str] = None
    variables: Optional[List[VariableSchema]] = None
    example_input: Optional[Dict[str, Any]] = None
    example_output: Optional[str] = None
    language: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class AIGenerateRequest(BaseModel):
    """AI generate prompt request"""
    category: str = Field(..., description="Prompt category")
    description: str = Field(..., min_length=10, description="Description of what the prompt should do")
    expert_role: str = "general"
    language: str = "th"


class PromptResponse(BaseModel):
    """Prompt response"""
    template_id: str
    name: str
    description: Optional[str]
    category: str
    expert_role: Optional[str]
    template_content: str
    variables: List[Dict[str, Any]]
    example_input: Dict[str, Any]
    example_output: Optional[str]
    language: str
    is_default: bool
    is_active: bool
    usage_count: int
    version: int
    created_at: str
    updated_at: str


class PromptListResponse(BaseModel):
    """List prompts response"""
    prompts: List[PromptResponse]
    total: int
    limit: int
    offset: int


class TemplateGuideResponse(BaseModel):
    """Template guide response"""
    guides: Dict[str, Any]


class StatsResponse(BaseModel):
    """Stats response"""
    by_category: Dict[str, Any]
    total: int
    total_usage: int


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def prompt_to_response(prompt) -> PromptResponse:
    """Convert PromptTemplate to response model"""
    data = prompt.to_dict()
    return PromptResponse(**data)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=PromptListResponse)
async def list_prompts(
    category: Optional[str] = Query(None, description="Filter by category"),
    expert_role: Optional[str] = Query(None, description="Filter by expert role"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: TokenPayload = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    List all prompt templates.
    Admin only.
    """
    prompts = await prompt_service.get_prompts(
        category=category,
        expert_role=expert_role,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    total = await prompt_service.get_prompt_count(category=category, is_active=is_active)

    return PromptListResponse(
        prompts=[prompt_to_response(p) for p in prompts],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/templates", response_model=TemplateGuideResponse)
async def get_template_guides(
    current_user: TokenPayload = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Get template guides for all categories.
    Admin only.
    """
    guides = prompt_service.get_template_guides()
    return TemplateGuideResponse(guides=guides)


@router.get("/stats", response_model=StatsResponse)
async def get_prompt_stats(
    current_user: TokenPayload = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Get prompt usage statistics.
    Admin only.
    """
    stats = await prompt_service.get_stats()
    return StatsResponse(**stats)


@router.get("/categories")
async def get_categories(
    current_user: TokenPayload = Depends(require_admin),
):
    """
    Get available prompt categories and expert roles.
    Admin only.
    """
    return {
        "categories": [
            {"value": c.value, "label": c.name.replace("_", " ").title()}
            for c in PromptCategory
        ],
        "expert_roles": [
            {"value": r.value, "label": r.name.replace("_", " ").title()}
            for r in ExpertRole
        ],
    }


@router.get("/{template_id}", response_model=PromptResponse)
async def get_prompt(
    template_id: UUID,
    current_user: TokenPayload = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Get prompt by ID.
    Admin only.
    """
    prompt = await prompt_service.get_prompt_by_id(template_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return prompt_to_response(prompt)


@router.post("", response_model=PromptResponse, status_code=201)
async def create_prompt(
    request: CreatePromptRequest,
    current_user: TokenPayload = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Create new prompt template.
    Admin only.
    """
    # Validate category
    try:
        PromptCategory(request.category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {request.category}. Valid: {[c.value for c in PromptCategory]}"
        )

    # Validate expert role if provided
    if request.expert_role:
        try:
            ExpertRole(request.expert_role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid expert_role: {request.expert_role}. Valid: {[r.value for r in ExpertRole]}"
            )

    prompt = await prompt_service.create_prompt(
        name=request.name,
        template_content=request.template_content,
        category=request.category,
        created_by=UUID(current_user.sub),
        description=request.description,
        expert_role=request.expert_role,
        variables=[v.dict() for v in request.variables] if request.variables else None,
        example_input=request.example_input,
        example_output=request.example_output,
        language=request.language,
        is_default=request.is_default,
    )

    return prompt_to_response(prompt)


@router.put("/{template_id}", response_model=PromptResponse)
async def update_prompt(
    template_id: UUID,
    request: UpdatePromptRequest,
    current_user: TokenPayload = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Update prompt template.
    Admin only.
    """
    # Validate category if provided
    if request.category:
        try:
            PromptCategory(request.category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {request.category}"
            )

    # Validate expert role if provided
    if request.expert_role:
        try:
            ExpertRole(request.expert_role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid expert_role: {request.expert_role}"
            )

    # Build updates dict
    updates = {}
    for field, value in request.dict(exclude_unset=True).items():
        if value is not None:
            if field == "variables":
                updates[field] = [v.dict() if hasattr(v, 'dict') else v for v in value]
            else:
                updates[field] = value

    prompt = await prompt_service.update_prompt(template_id, **updates)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return prompt_to_response(prompt)


@router.delete("/{template_id}")
async def delete_prompt(
    template_id: UUID,
    current_user: TokenPayload = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Delete prompt template (soft delete).
    Admin only.
    """
    success = await prompt_service.delete_prompt(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return {"message": "Prompt deleted successfully"}


@router.post("/{template_id}/set-default")
async def set_default_prompt(
    template_id: UUID,
    current_user: TokenPayload = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Set prompt as default for its category.
    Admin only.
    """
    prompt = await prompt_service.get_prompt_by_id(template_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    success = await prompt_service.set_default(
        template_id,
        prompt.category.value if hasattr(prompt.category, 'value') else prompt.category,
        prompt.expert_role.value if prompt.expert_role and hasattr(prompt.expert_role, 'value') else prompt.expert_role,
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to set default")

    return {"message": "Prompt set as default successfully"}


@router.post("/ai-generate")
async def ai_generate_prompt(
    request: AIGenerateRequest,
    current_user: TokenPayload = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Use AI to generate a prompt template based on description.
    Admin only.
    """
    # Validate category
    try:
        PromptCategory(request.category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {request.category}"
        )

    result = await prompt_service.ai_generate_prompt(
        category=request.category,
        description=request.description,
        expert_role=request.expert_role,
        language=request.language,
    )

    return result


@router.post("/{template_id}/render")
async def render_prompt(
    template_id: UUID,
    variables: Dict[str, str],
    current_user: TokenPayload = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Render prompt with variables.
    Any authenticated user.
    """
    try:
        rendered = await prompt_service.render_prompt(template_id, variables)
        return {"rendered": rendered}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
