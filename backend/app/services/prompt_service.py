"""
CogniFy Prompt Service

Business logic for prompt template management.
Created with love by Angela & David - 2 January 2026
"""

import json
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.infrastructure.database import get_db_pool
from app.domain.entities.prompt import (
    PromptTemplate,
    PromptCategory,
    ExpertRole,
    PromptVariable,
    get_template_guide,
    TEMPLATE_GUIDES,
)
from app.services.llm_service import get_llm_service, LLMConfig, Message, MessageRole


class PromptService:
    """
    Prompt Template Service

    Handles CRUD operations for prompt templates and AI-assisted generation.
    """

    def __init__(self):
        self.llm_service = get_llm_service()

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    async def get_prompts(
        self,
        category: Optional[str] = None,
        expert_role: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PromptTemplate]:
        """Get all prompts with optional filters"""
        pool = await get_db_pool()

        conditions = ["is_active = $1"]
        params = [is_active]
        param_idx = 2

        if category:
            conditions.append(f"category = ${param_idx}")
            params.append(category)
            param_idx += 1

        if expert_role:
            conditions.append(f"expert_role = ${param_idx}")
            params.append(expert_role)
            param_idx += 1

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT * FROM prompt_templates
            WHERE {where_clause}
            ORDER BY is_default DESC, usage_count DESC, created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [PromptTemplate.from_db_row(dict(row)) for row in rows]

    async def get_prompt_by_id(self, template_id: UUID) -> Optional[PromptTemplate]:
        """Get prompt by ID"""
        pool = await get_db_pool()

        query = """
            SELECT * FROM prompt_templates
            WHERE template_id = $1
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, template_id)

        if not row:
            return None

        return PromptTemplate.from_db_row(dict(row))

    async def get_default_prompt(
        self,
        category: str,
        expert_role: str = "general",
    ) -> Optional[PromptTemplate]:
        """Get default prompt for category and role"""
        pool = await get_db_pool()

        # Try to find exact match (category + role + is_default)
        query = """
            SELECT * FROM prompt_templates
            WHERE category = $1
                AND (expert_role = $2 OR expert_role IS NULL)
                AND is_default = true
                AND is_active = true
            ORDER BY
                CASE WHEN expert_role = $2 THEN 0 ELSE 1 END,
                usage_count DESC
            LIMIT 1
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, category, expert_role)

        if row:
            return PromptTemplate.from_db_row(dict(row))

        # Fallback: any default for category
        query = """
            SELECT * FROM prompt_templates
            WHERE category = $1
                AND is_default = true
                AND is_active = true
            ORDER BY usage_count DESC
            LIMIT 1
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, category)

        if row:
            return PromptTemplate.from_db_row(dict(row))

        return None

    async def get_prompt_count(
        self,
        category: Optional[str] = None,
        is_active: bool = True,
    ) -> int:
        """Get total count of prompts"""
        pool = await get_db_pool()

        if category:
            query = """
                SELECT COUNT(*) FROM prompt_templates
                WHERE category = $1 AND is_active = $2
            """
            params = [category, is_active]
        else:
            query = """
                SELECT COUNT(*) FROM prompt_templates
                WHERE is_active = $1
            """
            params = [is_active]

        async with pool.acquire() as conn:
            count = await conn.fetchval(query, *params)

        return count or 0

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    async def create_prompt(
        self,
        name: str,
        template_content: str,
        category: str,
        created_by: UUID,
        description: Optional[str] = None,
        expert_role: Optional[str] = None,
        variables: Optional[List[Dict]] = None,
        example_input: Optional[Dict] = None,
        example_output: Optional[str] = None,
        language: str = "th",
        is_default: bool = False,
    ) -> PromptTemplate:
        """Create new prompt template"""
        pool = await get_db_pool()

        # If setting as default, unset other defaults in same category
        if is_default:
            await self._unset_category_defaults(category, expert_role)

        query = """
            INSERT INTO prompt_templates (
                name, description, category, expert_role,
                template_content, variables, example_input, example_output,
                language, is_default, is_active, created_by
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
            )
            RETURNING *
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                name,
                description,
                category,
                expert_role,
                template_content,
                json.dumps(variables or []),
                json.dumps(example_input or {}),
                example_output,
                language,
                is_default,
                True,  # is_active
                created_by,
            )

        return PromptTemplate.from_db_row(dict(row))

    async def update_prompt(
        self,
        template_id: UUID,
        **updates,
    ) -> Optional[PromptTemplate]:
        """Update prompt template"""
        pool = await get_db_pool()

        # Check if prompt exists
        existing = await self.get_prompt_by_id(template_id)
        if not existing:
            return None

        # Handle default setting
        if updates.get("is_default"):
            category = updates.get("category", existing.category)
            expert_role = updates.get("expert_role", existing.expert_role)
            await self._unset_category_defaults(
                category.value if isinstance(category, PromptCategory) else category,
                expert_role.value if isinstance(expert_role, ExpertRole) else expert_role,
            )

        # Build update query dynamically
        allowed_fields = [
            "name", "description", "category", "expert_role",
            "template_content", "variables", "example_input", "example_output",
            "language", "is_default", "is_active",
        ]

        set_clauses = []
        params = []
        param_idx = 1

        for field in allowed_fields:
            if field in updates:
                value = updates[field]
                # Handle JSON fields
                if field in ["variables", "example_input"]:
                    value = json.dumps(value) if value else None
                # Handle enums
                if isinstance(value, (PromptCategory, ExpertRole)):
                    value = value.value
                set_clauses.append(f"{field} = ${param_idx}")
                params.append(value)
                param_idx += 1

        if not set_clauses:
            return existing

        params.append(template_id)
        query = f"""
            UPDATE prompt_templates
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE template_id = ${param_idx}
            RETURNING *
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        return PromptTemplate.from_db_row(dict(row)) if row else None

    async def delete_prompt(self, template_id: UUID) -> bool:
        """Soft delete prompt template"""
        pool = await get_db_pool()

        query = """
            UPDATE prompt_templates
            SET is_active = false, updated_at = NOW()
            WHERE template_id = $1
            RETURNING template_id
        """

        async with pool.acquire() as conn:
            result = await conn.fetchval(query, template_id)

        return result is not None

    async def set_default(
        self,
        template_id: UUID,
        category: str,
        expert_role: Optional[str] = None,
    ) -> bool:
        """Set prompt as default for category"""
        pool = await get_db_pool()

        # Unset other defaults
        await self._unset_category_defaults(category, expert_role)

        # Set this as default
        query = """
            UPDATE prompt_templates
            SET is_default = true, updated_at = NOW()
            WHERE template_id = $1
            RETURNING template_id
        """

        async with pool.acquire() as conn:
            result = await conn.fetchval(query, template_id)

        return result is not None

    async def increment_usage(self, template_id: UUID) -> None:
        """Increment usage count for prompt"""
        pool = await get_db_pool()

        query = """
            UPDATE prompt_templates
            SET usage_count = usage_count + 1, updated_at = NOW()
            WHERE template_id = $1
        """

        async with pool.acquire() as conn:
            await conn.execute(query, template_id)

    async def _unset_category_defaults(
        self,
        category: str,
        expert_role: Optional[str] = None,
    ) -> None:
        """Unset default flag for all prompts in category"""
        pool = await get_db_pool()

        if expert_role:
            query = """
                UPDATE prompt_templates
                SET is_default = false
                WHERE category = $1 AND expert_role = $2 AND is_default = true
            """
            params = [category, expert_role]
        else:
            query = """
                UPDATE prompt_templates
                SET is_default = false
                WHERE category = $1 AND is_default = true
            """
            params = [category]

        async with pool.acquire() as conn:
            await conn.execute(query, *params)

    # =========================================================================
    # RENDERING
    # =========================================================================

    async def render_prompt(
        self,
        template_id: UUID,
        variables: Dict[str, str],
    ) -> str:
        """Render prompt with variables"""
        prompt = await self.get_prompt_by_id(template_id)
        if not prompt:
            raise ValueError(f"Prompt not found: {template_id}")

        # Increment usage
        await self.increment_usage(template_id)

        return prompt.render(variables)

    # =========================================================================
    # AI GENERATION
    # =========================================================================

    async def ai_generate_prompt(
        self,
        category: str,
        description: str,
        expert_role: str = "general",
        language: str = "th",
    ) -> Dict[str, Any]:
        """
        Use AI to generate a prompt template based on description.

        Returns:
            Dict with generated prompt content and suggested variables
        """
        # Get template guide for category
        cat_enum = PromptCategory(category)
        guide = get_template_guide(cat_enum)

        # Build generation prompt
        system_prompt = f"""You are an expert prompt engineer. Generate a high-quality prompt template based on the user's description.

Category: {category}
Expert Role: {expert_role}
Language: {language}

Template Guide:
{json.dumps(guide, ensure_ascii=False, indent=2)}

Requirements:
1. Use {{variable_name}} syntax for dynamic parts
2. Include clear instructions for the AI
3. Specify output format (Markdown, bullet points, etc.)
4. Add source citation instructions if RAG
5. Be specific and clear

Output format (JSON):
{{
  "name": "Suggested name for the template",
  "template_content": "The full prompt template...",
  "variables": [
    {{"name": "variable1", "required": true, "description": "What this variable is for"}},
    ...
  ],
  "example_output": "Example of expected output..."
}}

Respond with valid JSON only."""

        user_message = f"""Create a prompt template for:

{description}

The prompt should be in {language} language and suitable for {expert_role} expert role."""

        messages = [
            Message(role=MessageRole.SYSTEM, content=system_prompt),
            Message(role=MessageRole.USER, content=user_message),
        ]

        config = LLMConfig.from_settings()
        response = await self.llm_service.generate(messages, config)

        # Parse JSON response
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                result = json.loads(json_match.group(0))
                return result
        except json.JSONDecodeError:
            pass

        # Fallback: return raw content
        return {
            "name": "Generated Prompt",
            "template_content": response.content,
            "variables": [],
            "example_output": None,
        }

    # =========================================================================
    # TEMPLATE GUIDES
    # =========================================================================

    def get_template_guides(self) -> Dict[str, Any]:
        """Get all template guides"""
        result = {}
        for cat, guide in TEMPLATE_GUIDES.items():
            result[cat.value] = guide
        return result

    def get_category_guide(self, category: str) -> Dict[str, Any]:
        """Get template guide for specific category"""
        cat_enum = PromptCategory(category)
        return get_template_guide(cat_enum)

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_stats(self) -> Dict[str, Any]:
        """Get prompt statistics"""
        pool = await get_db_pool()

        query = """
            SELECT
                category,
                COUNT(*) as count,
                SUM(usage_count) as total_usage,
                COUNT(*) FILTER (WHERE is_default) as default_count
            FROM prompt_templates
            WHERE is_active = true
            GROUP BY category
        """

        async with pool.acquire() as conn:
            rows = await conn.fetch(query)

        stats = {
            "by_category": {row["category"]: {
                "count": row["count"],
                "total_usage": row["total_usage"] or 0,
                "has_default": row["default_count"] > 0,
            } for row in rows},
            "total": sum(row["count"] for row in rows),
            "total_usage": sum(row["total_usage"] or 0 for row in rows),
        }

        return stats


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_prompt_service: Optional[PromptService] = None


def get_prompt_service() -> PromptService:
    """Get or create PromptService singleton"""
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service
