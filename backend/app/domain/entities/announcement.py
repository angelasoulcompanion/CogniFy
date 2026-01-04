"""
Announcement Entity
Organization news and announcements
Created with love by Angela & David - 4 January 2026
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
import asyncpg


class AnnouncementCategory(str, Enum):
    """Category types for announcements"""
    GENERAL = "general"
    IMPORTANT = "important"
    UPDATE = "update"
    EVENT = "event"


@dataclass
class Announcement:
    """
    Announcement entity for organization news

    Attributes:
        announcement_id: Unique identifier
        title: Announcement title
        content: Markdown formatted content
        cover_image_url: Optional URL for cover/thumbnail image
        category: Category type (general, important, update, event)
        is_pinned: Whether the announcement is pinned to top
        is_published: Whether the announcement is visible to users
        published_at: When the announcement was published
        created_by: User ID of the creator
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    title: str
    content: str
    announcement_id: UUID = field(default_factory=uuid4)
    cover_image_url: Optional[str] = None
    category: AnnouncementCategory = AnnouncementCategory.GENERAL
    is_pinned: bool = False
    is_published: bool = False
    published_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate announcement data after initialization"""
        self._validate()

    def _validate(self):
        """Validate announcement fields"""
        if not self.title or not self.title.strip():
            raise ValueError("Title is required")
        if not self.content or not self.content.strip():
            raise ValueError("Content is required")
        if len(self.title) > 500:
            raise ValueError("Title must be 500 characters or less")

        # Ensure category is valid enum
        if isinstance(self.category, str):
            self.category = AnnouncementCategory(self.category)

    def publish(self) -> None:
        """Publish the announcement"""
        self.is_published = True
        self.published_at = datetime.now()
        self.updated_at = datetime.now()

    def unpublish(self) -> None:
        """Unpublish the announcement"""
        self.is_published = False
        self.published_at = None
        self.updated_at = datetime.now()

    def pin(self) -> None:
        """Pin the announcement to top"""
        self.is_pinned = True
        self.updated_at = datetime.now()

    def unpin(self) -> None:
        """Unpin the announcement"""
        self.is_pinned = False
        self.updated_at = datetime.now()

    def update(
        self,
        title: Optional[str] = None,
        content: Optional[str] = None,
        cover_image_url: Optional[str] = None,
        category: Optional[AnnouncementCategory] = None,
    ) -> None:
        """Update announcement fields"""
        if title is not None:
            self.title = title
        if content is not None:
            self.content = content
        if cover_image_url is not None:
            self.cover_image_url = cover_image_url if cover_image_url else None
        if category is not None:
            self.category = category

        self.updated_at = datetime.now()
        self._validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "announcement_id": str(self.announcement_id),
            "title": self.title,
            "content": self.content,
            "cover_image_url": self.cover_image_url,
            "category": self.category.value,
            "is_pinned": self.is_pinned,
            "is_published": self.is_published,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Announcement":
        """Create from dictionary"""
        return cls(
            announcement_id=UUID(data["announcement_id"]) if data.get("announcement_id") else uuid4(),
            title=data["title"],
            content=data["content"],
            cover_image_url=data.get("cover_image_url"),
            category=AnnouncementCategory(data.get("category", "general")),
            is_pinned=data.get("is_pinned", False),
            is_published=data.get("is_published", False),
            published_at=datetime.fromisoformat(data["published_at"]) if data.get("published_at") else None,
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
        )

    @classmethod
    def from_db_row(cls, row: asyncpg.Record) -> "Announcement":
        """Create from database row"""
        return cls(
            announcement_id=row["announcement_id"],
            title=row["title"],
            content=row["content"],
            cover_image_url=row["cover_image_url"],
            category=AnnouncementCategory(row["category"]) if row["category"] else AnnouncementCategory.GENERAL,
            is_pinned=row["is_pinned"],
            is_published=row["is_published"],
            published_at=row["published_at"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @classmethod
    def create(
        cls,
        title: str,
        content: str,
        category: AnnouncementCategory = AnnouncementCategory.GENERAL,
        cover_image_url: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> "Announcement":
        """Factory method to create a new announcement"""
        return cls(
            title=title,
            content=content,
            category=category,
            cover_image_url=cover_image_url,
            created_by=created_by,
        )
