"""
CogniFy API Helpers
Shared utilities to eliminate duplication across API endpoints
"""

from typing import Any, Awaitable, Callable, Optional, TypeVar
from uuid import UUID

from fastapi import Depends, Query

from app.core.exceptions import NotFoundError, AuthorizationError
from app.core.security import TokenPayload


T = TypeVar("T")


# =============================================================================
# RESOURCE LOOKUP
# =============================================================================

async def get_or_404(
    fetch: Callable[..., Awaitable[Optional[T]]],
    resource_id: Any,
    name: str = "Resource",
) -> T:
    """
    Fetch a resource or raise NotFoundError (→ 404 via global handler).

    Usage:
        document = await get_or_404(repo.get_by_id, document_id, "Document")
    """
    result = await fetch(resource_id)
    if result is None:
        raise NotFoundError(f"{name} not found")
    return result


async def get_active_or_404(
    fetch: Callable[..., Awaitable[Optional[T]]],
    resource_id: Any,
    name: str = "Document",
) -> T:
    """
    Fetch a resource and verify it's not soft-deleted.
    Expects the entity to have an `is_deleted` attribute.

    Usage:
        document = await get_active_or_404(repo.get_by_id, document_id, "Document")
    """
    result = await fetch(resource_id)
    if result is None or getattr(result, "is_deleted", False):
        raise NotFoundError(f"{name} not found")
    return result


# =============================================================================
# AUTHORIZATION
# =============================================================================

def check_owner_or_admin(
    resource_created_by: UUID,
    current_user: TokenPayload,
) -> None:
    """
    Verify the current user is the resource owner or an admin.
    Raises AuthorizationError (→ 403) if not.
    """
    if current_user.role != "admin" and str(resource_created_by) != current_user.sub:
        raise AuthorizationError("Not authorized")


# =============================================================================
# PAGINATION
# =============================================================================

class PaginationParams:
    """
    Reusable pagination dependency.

    Usage:
        async def list_items(pagination: PaginationParams = Depends()):
            items = await repo.get_all(skip=pagination.skip, limit=pagination.limit)
    """

    def __init__(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
    ):
        self.skip = skip
        self.limit = limit


# =============================================================================
# SEARCH RESULT BUILDER
# =============================================================================

def rag_result_to_dict(
    r: Any,
    *,
    include_content: bool = True,
    content_truncate: Optional[int] = None,
) -> dict:
    """
    Convert a RAG search result object to a dict matching SearchResult fields.
    Eliminates the repeated SearchResult(...) construction across search endpoints.
    """
    content = r.content if include_content else ""
    if content_truncate and len(content) > content_truncate:
        content = content[:content_truncate] + "..."

    return dict(
        chunk_id=str(r.chunk_id),
        document_id=str(r.document_id),
        document_name=r.document_title or r.document_filename or "Untitled",
        content=content,
        page_number=r.page_number,
        section_title=r.section_title,
        similarity=r.score,
        vector_rank=getattr(r, "vector_rank", None),
        bm25_rank=getattr(r, "bm25_rank", None),
        rrf_score=getattr(r, "rrf_score", None),
    )


# =============================================================================
# ENUM VALIDATION
# =============================================================================

def validate_enum(value: str, enum_class: type, label: str = "value") -> Any:
    """
    Validate a string against an enum, raising a descriptive 400 error.

    Usage:
        category = validate_enum(request.category, PromptCategory, "category")
    """
    from app.core.exceptions import ValidationError
    try:
        return enum_class(value)
    except ValueError:
        valid = [e.value for e in enum_class]
        raise ValidationError(
            f"Invalid {label}: {value}. Valid values: {', '.join(valid)}"
        )
