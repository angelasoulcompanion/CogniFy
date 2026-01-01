"""
CogniFy Admin API
System administration and analytics endpoints
Created with love by Angela & David - 1 January 2026
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.security import get_current_user, require_admin, TokenPayload
from app.services.admin_service import get_admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class SystemStatsResponse(BaseModel):
    """System statistics response"""
    total_users: int
    active_users_7d: int
    total_documents: int
    total_chunks: int
    total_conversations: int
    total_messages: int
    total_embeddings: int
    storage_used_mb: float
    avg_response_time_ms: float


class UserStatsResponse(BaseModel):
    """User statistics response"""
    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    document_count: int
    conversation_count: int
    message_count: int
    last_active: Optional[datetime]
    created_at: datetime


class UserListResponse(BaseModel):
    """Paginated user list response"""
    users: List[UserStatsResponse]
    total: int
    skip: int
    limit: int


class UsageMetricsResponse(BaseModel):
    """Usage metrics response"""
    date: datetime
    documents_uploaded: int
    messages_sent: int
    embeddings_created: int
    unique_users: int


class DocumentTypeStatsResponse(BaseModel):
    """Document type statistics response"""
    file_type: str
    count: int
    total_size_mb: float
    total_chunks: int


class TopUserResponse(BaseModel):
    """Top user response"""
    user_id: str
    email: str
    full_name: Optional[str]
    conversations: int
    messages: int
    documents: int


class ActivityResponse(BaseModel):
    """Activity item response"""
    type: str
    id: str
    title: str
    user_email: str
    timestamp: str


class RoleUpdateRequest(BaseModel):
    """Role update request"""
    role: str = Field(..., description="New role: admin, editor, or user")


class MessageResponse(BaseModel):
    """Simple message response"""
    success: bool
    message: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/stats",
    response_model=SystemStatsResponse,
    summary="Get system statistics",
)
async def get_system_stats(
    current_user: TokenPayload = Depends(require_admin),
):
    """
    Get system-wide statistics.

    **Requires admin role.**

    Returns:
    - User counts (total, active)
    - Document and chunk counts
    - Conversation and message counts
    - Storage usage
    - Average response time
    """
    admin_service = get_admin_service()
    stats = await admin_service.get_system_stats()

    return SystemStatsResponse(
        total_users=stats.total_users,
        active_users_7d=stats.active_users_7d,
        total_documents=stats.total_documents,
        total_chunks=stats.total_chunks,
        total_conversations=stats.total_conversations,
        total_messages=stats.total_messages,
        total_embeddings=stats.total_embeddings,
        storage_used_mb=stats.storage_used_mb,
        avg_response_time_ms=stats.avg_response_time_ms,
    )


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all users",
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: TokenPayload = Depends(require_admin),
):
    """
    Get all users with their statistics.

    **Requires admin role.**

    Returns paginated list of users with:
    - Document, conversation, message counts
    - Last active timestamp
    - Account status
    """
    admin_service = get_admin_service()

    users = await admin_service.get_all_users(
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
    )
    total = await admin_service.get_user_count(include_inactive=include_inactive)

    return UserListResponse(
        users=[
            UserStatsResponse(
                user_id=str(u.user_id),
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                is_active=u.is_active,
                document_count=u.document_count,
                conversation_count=u.conversation_count,
                message_count=u.message_count,
                last_active=u.last_active,
                created_at=u.created_at,
            )
            for u in users
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/usage",
    response_model=List[UsageMetricsResponse],
    summary="Get usage metrics",
)
async def get_usage_metrics(
    days: int = Query(30, ge=1, le=365),
    interval: str = Query("day", regex="^(day|week|month)$"),
    current_user: TokenPayload = Depends(require_admin),
):
    """
    Get usage metrics over time.

    **Requires admin role.**

    Args:
    - days: Number of days to look back (1-365)
    - interval: Grouping interval (day, week, month)

    Returns metrics per interval:
    - Documents uploaded
    - Messages sent
    - Embeddings created
    - Unique active users
    """
    admin_service = get_admin_service()
    metrics = await admin_service.get_usage_metrics(days=days, interval=interval)

    return [
        UsageMetricsResponse(
            date=m.date,
            documents_uploaded=m.documents_uploaded,
            messages_sent=m.messages_sent,
            embeddings_created=m.embeddings_created,
            unique_users=m.unique_users,
        )
        for m in metrics
    ]


@router.get(
    "/documents/stats",
    response_model=List[DocumentTypeStatsResponse],
    summary="Get document type statistics",
)
async def get_document_type_stats(
    current_user: TokenPayload = Depends(require_admin),
):
    """
    Get statistics grouped by document type.

    **Requires admin role.**

    Returns for each file type:
    - Document count
    - Total size in MB
    - Total chunks
    """
    admin_service = get_admin_service()
    stats = await admin_service.get_document_type_stats()

    return [
        DocumentTypeStatsResponse(
            file_type=s.file_type,
            count=s.count,
            total_size_mb=s.total_size_mb,
            total_chunks=s.total_chunks,
        )
        for s in stats
    ]


@router.get(
    "/users/top",
    response_model=List[TopUserResponse],
    summary="Get top users",
)
async def get_top_users(
    limit: int = Query(10, ge=1, le=50),
    current_user: TokenPayload = Depends(require_admin),
):
    """
    Get top users by activity.

    **Requires admin role.**

    Returns users sorted by message count with:
    - Conversation count
    - Message count
    - Document count
    """
    admin_service = get_admin_service()
    users = await admin_service.get_top_users(limit=limit)

    return [
        TopUserResponse(
            user_id=u['user_id'],
            email=u['email'],
            full_name=u['full_name'],
            conversations=u['conversations'],
            messages=u['messages'],
            documents=u['documents'],
        )
        for u in users
    ]


@router.get(
    "/activity",
    response_model=List[ActivityResponse],
    summary="Get recent activity",
)
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(require_admin),
):
    """
    Get recent system activity.

    **Requires admin role.**

    Returns recent documents and conversations.
    """
    admin_service = get_admin_service()
    activity = await admin_service.get_recent_activity(limit=limit)

    return [
        ActivityResponse(
            type=a['type'],
            id=a['id'],
            title=a['title'],
            user_email=a['user_email'],
            timestamp=a['timestamp'],
        )
        for a in activity
    ]


@router.put(
    "/users/{user_id}/role",
    response_model=MessageResponse,
    summary="Update user role",
)
async def update_user_role(
    user_id: UUID,
    request: RoleUpdateRequest,
    current_user: TokenPayload = Depends(require_admin),
):
    """
    Update a user's role.

    **Requires admin role.**

    Valid roles: admin, editor, user
    """
    if str(user_id) == current_user.sub:
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own role",
        )

    admin_service = get_admin_service()

    try:
        success = await admin_service.update_user_role(user_id, request.role)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MessageResponse(
        success=True,
        message=f"User role updated to {request.role}",
    )


@router.put(
    "/users/{user_id}/toggle-status",
    response_model=MessageResponse,
    summary="Toggle user active status",
)
async def toggle_user_status(
    user_id: UUID,
    current_user: TokenPayload = Depends(require_admin),
):
    """
    Toggle a user's active status.

    **Requires admin role.**

    Cannot deactivate yourself.
    """
    if str(user_id) == current_user.sub:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own account",
        )

    admin_service = get_admin_service()
    success = await admin_service.toggle_user_status(user_id)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return MessageResponse(
        success=True,
        message="User status toggled",
    )
