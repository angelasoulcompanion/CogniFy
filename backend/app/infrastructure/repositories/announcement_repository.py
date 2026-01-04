"""
Announcement Repository
Database operations for announcements
Created with love by Angela & David - 4 January 2026
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import asyncpg

from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.database import Database
from app.domain.entities.announcement import Announcement, AnnouncementCategory


class AnnouncementRepository(BaseRepository[Announcement]):
    """Repository for announcement database operations"""

    def __init__(self):
        super().__init__("announcements", "announcement_id")

    def _row_to_entity(self, row: asyncpg.Record) -> Announcement:
        """Convert database row to Announcement entity"""
        return Announcement.from_db_row(row)

    def _entity_to_dict(self, entity: Announcement) -> Dict[str, Any]:
        """Convert Announcement entity to dictionary for database"""
        return {
            "announcement_id": entity.announcement_id,
            "title": entity.title,
            "content": entity.content,
            "cover_image_url": entity.cover_image_url,
            "category": entity.category.value,
            "is_pinned": entity.is_pinned,
            "is_published": entity.is_published,
            "published_at": entity.published_at,
            "created_by": entity.created_by,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    async def create(self, announcement: Announcement) -> Announcement:
        """Create a new announcement"""
        query = """
            INSERT INTO announcements (
                announcement_id, title, content, cover_image_url, category,
                is_pinned, is_published, published_at, created_by,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
        """
        row = await Database.fetchrow(
            query,
            announcement.announcement_id,
            announcement.title,
            announcement.content,
            announcement.cover_image_url,
            announcement.category.value,
            announcement.is_pinned,
            announcement.is_published,
            announcement.published_at,
            announcement.created_by,
            announcement.created_at,
            announcement.updated_at,
        )
        return self._row_to_entity(row)

    async def update(self, announcement: Announcement) -> Announcement:
        """Update an existing announcement"""
        query = """
            UPDATE announcements SET
                title = $2,
                content = $3,
                cover_image_url = $4,
                category = $5,
                is_pinned = $6,
                is_published = $7,
                published_at = $8,
                updated_at = $9
            WHERE announcement_id = $1
            RETURNING *
        """
        row = await Database.fetchrow(
            query,
            announcement.announcement_id,
            announcement.title,
            announcement.content,
            announcement.cover_image_url,
            announcement.category.value,
            announcement.is_pinned,
            announcement.is_published,
            announcement.published_at,
            datetime.now(),
        )
        if row is None:
            raise ValueError(f"Announcement {announcement.announcement_id} not found")
        return self._row_to_entity(row)

    async def get_published(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[AnnouncementCategory] = None,
    ) -> List[Announcement]:
        """
        Get published announcements
        Pinned announcements come first, then by published_at DESC
        """
        if category:
            query = """
                SELECT * FROM announcements
                WHERE is_published = TRUE AND category = $3
                ORDER BY is_pinned DESC, published_at DESC NULLS LAST
                OFFSET $1 LIMIT $2
            """
            rows = await Database.fetch(query, skip, limit, category.value)
        else:
            query = """
                SELECT * FROM announcements
                WHERE is_published = TRUE
                ORDER BY is_pinned DESC, published_at DESC NULLS LAST
                OFFSET $1 LIMIT $2
            """
            rows = await Database.fetch(query, skip, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_pinned(self, limit: int = 5) -> List[Announcement]:
        """Get pinned and published announcements"""
        query = """
            SELECT * FROM announcements
            WHERE is_pinned = TRUE AND is_published = TRUE
            ORDER BY published_at DESC NULLS LAST
            LIMIT $1
        """
        rows = await Database.fetch(query, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_all_admin(
        self,
        skip: int = 0,
        limit: int = 50,
        include_drafts: bool = True,
    ) -> List[Announcement]:
        """
        Get all announcements for admin view
        Includes drafts (unpublished) if requested
        """
        if include_drafts:
            query = """
                SELECT * FROM announcements
                ORDER BY created_at DESC
                OFFSET $1 LIMIT $2
            """
        else:
            query = """
                SELECT * FROM announcements
                WHERE is_published = TRUE
                ORDER BY created_at DESC
                OFFSET $1 LIMIT $2
            """
        rows = await Database.fetch(query, skip, limit)
        return [self._row_to_entity(row) for row in rows]

    async def count_published(self) -> int:
        """Count published announcements"""
        query = "SELECT COUNT(*) FROM announcements WHERE is_published = TRUE"
        return await Database.fetchval(query)

    async def count_all(self) -> int:
        """Count all announcements including drafts"""
        query = "SELECT COUNT(*) FROM announcements"
        return await Database.fetchval(query)

    async def publish(self, announcement_id: UUID) -> Optional[Announcement]:
        """Publish an announcement"""
        query = """
            UPDATE announcements SET
                is_published = TRUE,
                published_at = NOW(),
                updated_at = NOW()
            WHERE announcement_id = $1
            RETURNING *
        """
        row = await Database.fetchrow(query, announcement_id)
        return self._row_to_entity(row) if row else None

    async def unpublish(self, announcement_id: UUID) -> Optional[Announcement]:
        """Unpublish an announcement"""
        query = """
            UPDATE announcements SET
                is_published = FALSE,
                updated_at = NOW()
            WHERE announcement_id = $1
            RETURNING *
        """
        row = await Database.fetchrow(query, announcement_id)
        return self._row_to_entity(row) if row else None

    async def pin(self, announcement_id: UUID) -> Optional[Announcement]:
        """Pin an announcement"""
        query = """
            UPDATE announcements SET
                is_pinned = TRUE,
                updated_at = NOW()
            WHERE announcement_id = $1
            RETURNING *
        """
        row = await Database.fetchrow(query, announcement_id)
        return self._row_to_entity(row) if row else None

    async def unpin(self, announcement_id: UUID) -> Optional[Announcement]:
        """Unpin an announcement"""
        query = """
            UPDATE announcements SET
                is_pinned = FALSE,
                updated_at = NOW()
            WHERE announcement_id = $1
            RETURNING *
        """
        row = await Database.fetchrow(query, announcement_id)
        return self._row_to_entity(row) if row else None

    async def get_by_category(
        self,
        category: AnnouncementCategory,
        skip: int = 0,
        limit: int = 20,
        published_only: bool = True,
    ) -> List[Announcement]:
        """Get announcements by category"""
        if published_only:
            query = """
                SELECT * FROM announcements
                WHERE category = $3 AND is_published = TRUE
                ORDER BY is_pinned DESC, published_at DESC NULLS LAST
                OFFSET $1 LIMIT $2
            """
        else:
            query = """
                SELECT * FROM announcements
                WHERE category = $3
                ORDER BY created_at DESC
                OFFSET $1 LIMIT $2
            """
        rows = await Database.fetch(query, skip, limit, category.value)
        return [self._row_to_entity(row) for row in rows]
