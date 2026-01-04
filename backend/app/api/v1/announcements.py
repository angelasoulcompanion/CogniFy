"""
Announcements API Endpoints
CRUD operations for organization news and announcements
Created with love by Angela & David - 4 January 2026
"""

from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.security import get_current_user, get_current_user_optional, TokenPayload, require_admin
from app.infrastructure.repositories.announcement_repository import AnnouncementRepository
from app.domain.entities.announcement import Announcement, AnnouncementCategory


router = APIRouter()

# Initialize repository
announcement_repo = AnnouncementRepository()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class AnnouncementResponse(BaseModel):
    """Announcement response model"""
    announcement_id: str
    title: str
    content: str
    cover_image_url: Optional[str]
    category: str
    is_pinned: bool
    is_published: bool
    published_at: Optional[str]
    created_by: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class AnnouncementListResponse(BaseModel):
    """Paginated announcement list response"""
    announcements: List[AnnouncementResponse]
    total: int
    skip: int
    limit: int


class CreateAnnouncementRequest(BaseModel):
    """Request model for creating announcement"""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    cover_image_url: Optional[str] = Field(None, max_length=1000)
    category: str = Field(default="general")
    is_published: bool = Field(default=False)
    is_pinned: bool = Field(default=False)


class UpdateAnnouncementRequest(BaseModel):
    """Request model for updating announcement"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    cover_image_url: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _announcement_to_response(announcement: Announcement) -> AnnouncementResponse:
    """Convert Announcement entity to response model"""
    return AnnouncementResponse(
        announcement_id=str(announcement.announcement_id),
        title=announcement.title,
        content=announcement.content,
        cover_image_url=announcement.cover_image_url,
        category=announcement.category.value,
        is_pinned=announcement.is_pinned,
        is_published=announcement.is_published,
        published_at=announcement.published_at.isoformat() if announcement.published_at else None,
        created_by=str(announcement.created_by) if announcement.created_by else None,
        created_at=announcement.created_at.isoformat() if announcement.created_at else None,
        updated_at=announcement.updated_at.isoformat() if announcement.updated_at else None,
    )


# =============================================================================
# PUBLIC ENDPOINTS (Authenticated users)
# =============================================================================

@router.get("", response_model=AnnouncementListResponse)
async def list_published_announcements(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
):
    """
    Get published announcements for all users.
    Pinned announcements appear first.
    """
    cat_enum = AnnouncementCategory(category) if category else None
    announcements = await announcement_repo.get_published(
        skip=skip,
        limit=limit,
        category=cat_enum,
    )
    total = await announcement_repo.count_published()

    return AnnouncementListResponse(
        announcements=[_announcement_to_response(a) for a in announcements],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/pinned", response_model=List[AnnouncementResponse])
async def get_pinned_announcements(
    limit: int = Query(5, ge=1, le=10),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
):
    """Get pinned announcements (for homepage highlight)"""
    announcements = await announcement_repo.get_pinned(limit=limit)
    return [_announcement_to_response(a) for a in announcements]


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: UUID,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
):
    """Get a specific announcement by ID"""
    announcement = await announcement_repo.get_by_id(announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )

    # Only return published announcements for non-admin users
    if not announcement.is_published:
        if not current_user or current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )

    return _announcement_to_response(announcement)


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.get("/admin/all", response_model=AnnouncementListResponse)
async def list_all_announcements_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: TokenPayload = Depends(require_admin),
):
    """
    Get all announcements including drafts (Admin only).
    """
    announcements = await announcement_repo.get_all_admin(
        skip=skip,
        limit=limit,
        include_drafts=True,
    )
    total = await announcement_repo.count_all()

    return AnnouncementListResponse(
        announcements=[_announcement_to_response(a) for a in announcements],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    request: CreateAnnouncementRequest,
    current_user: TokenPayload = Depends(require_admin),
):
    """Create a new announcement (Admin only)"""
    try:
        category_enum = AnnouncementCategory(request.category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {request.category}. Valid values: general, important, update, event"
        )

    announcement = Announcement.create(
        title=request.title,
        content=request.content,
        category=category_enum,
        cover_image_url=request.cover_image_url,
        created_by=UUID(current_user.sub),
    )

    # Set initial states
    announcement.is_pinned = request.is_pinned
    if request.is_published:
        announcement.publish()

    created = await announcement_repo.create(announcement)
    return _announcement_to_response(created)


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: UUID,
    request: UpdateAnnouncementRequest,
    current_user: TokenPayload = Depends(require_admin),
):
    """Update an existing announcement (Admin only)"""
    announcement = await announcement_repo.get_by_id(announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )

    category_enum = None
    if request.category:
        try:
            category_enum = AnnouncementCategory(request.category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {request.category}"
            )

    announcement.update(
        title=request.title,
        content=request.content,
        cover_image_url=request.cover_image_url,
        category=category_enum,
    )

    updated = await announcement_repo.update(announcement)
    return _announcement_to_response(updated)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: UUID,
    current_user: TokenPayload = Depends(require_admin),
):
    """Delete an announcement (Admin only)"""
    deleted = await announcement_repo.delete(announcement_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )


@router.post("/{announcement_id}/publish", response_model=AnnouncementResponse)
async def publish_announcement(
    announcement_id: UUID,
    current_user: TokenPayload = Depends(require_admin),
):
    """Publish an announcement (Admin only)"""
    announcement = await announcement_repo.publish(announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    return _announcement_to_response(announcement)


@router.post("/{announcement_id}/unpublish", response_model=AnnouncementResponse)
async def unpublish_announcement(
    announcement_id: UUID,
    current_user: TokenPayload = Depends(require_admin),
):
    """Unpublish an announcement (Admin only)"""
    announcement = await announcement_repo.unpublish(announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    return _announcement_to_response(announcement)


@router.post("/{announcement_id}/pin", response_model=AnnouncementResponse)
async def pin_announcement(
    announcement_id: UUID,
    current_user: TokenPayload = Depends(require_admin),
):
    """Pin an announcement to top (Admin only)"""
    announcement = await announcement_repo.pin(announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    return _announcement_to_response(announcement)


@router.post("/{announcement_id}/unpin", response_model=AnnouncementResponse)
async def unpin_announcement(
    announcement_id: UUID,
    current_user: TokenPayload = Depends(require_admin),
):
    """Unpin an announcement (Admin only)"""
    announcement = await announcement_repo.unpin(announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    return _announcement_to_response(announcement)
