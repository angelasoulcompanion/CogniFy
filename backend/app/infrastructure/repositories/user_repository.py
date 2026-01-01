"""
User Repository
Database operations for User entity
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
import asyncpg

from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.database import Database
from app.domain.entities.user import User, UserRole


class UserRepository(BaseRepository[User]):
    """Repository for User entity"""

    def __init__(self):
        super().__init__("users", "user_id")

    def _row_to_entity(self, row: asyncpg.Record) -> User:
        """Convert database row to User entity"""
        try:
            role = UserRole(row["role"])
        except ValueError:
            role = UserRole.USER

        return User(
            user_id=row["user_id"],
            email=row["email"],
            password_hash=row["password_hash"],
            full_name=row.get("full_name"),
            role=role,
            is_active=row.get("is_active", True),
            last_login_at=row.get("last_login_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _entity_to_dict(self, entity: User) -> Dict[str, Any]:
        """Convert User entity to dictionary"""
        return {
            "user_id": entity.user_id,
            "email": entity.email,
            "password_hash": entity.password_hash,
            "full_name": entity.full_name,
            "role": entity.role.value,
            "is_active": entity.is_active,
            "last_login_at": entity.last_login_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    async def create(self, user: User) -> User:
        """Create a new user"""
        query = """
            INSERT INTO users (
                user_id, email, password_hash, full_name, role,
                is_active, last_login_at, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """
        row = await Database.fetchrow(
            query,
            user.user_id,
            user.email,
            user.password_hash,
            user.full_name,
            user.role.value,
            user.is_active,
            user.last_login_at,
            user.created_at,
            user.updated_at,
        )
        return self._row_to_entity(row)

    async def update(self, user: User) -> User:
        """Update an existing user"""
        query = """
            UPDATE users SET
                email = $2,
                full_name = $3,
                role = $4,
                is_active = $5,
                last_login_at = $6,
                updated_at = NOW()
            WHERE user_id = $1
            RETURNING *
        """
        row = await Database.fetchrow(
            query,
            user.user_id,
            user.email,
            user.full_name,
            user.role.value,
            user.is_active,
            user.last_login_at,
        )
        if row is None:
            raise ValueError(f"User {user.user_id} not found")
        return self._row_to_entity(row)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        query = "SELECT * FROM users WHERE email = $1"
        row = await Database.fetchrow(query, email)
        if row is None:
            return None
        return self._row_to_entity(row)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username (uses full_name field)"""
        query = "SELECT * FROM users WHERE full_name = $1"
        row = await Database.fetchrow(query, username)
        if row is None:
            return None
        return self._row_to_entity(row)

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        query = """
            SELECT * FROM users
            WHERE is_active = true
            ORDER BY created_at DESC
            OFFSET $1 LIMIT $2
        """
        rows = await Database.fetch(query, skip, limit)
        return [self._row_to_entity(row) for row in rows]

    async def get_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        query = """
            SELECT * FROM users
            WHERE role = $1
            ORDER BY created_at DESC
        """
        rows = await Database.fetch(query, role.value)
        return [self._row_to_entity(row) for row in rows]

    async def update_password(self, user_id: UUID, new_password_hash: str) -> bool:
        """Update user password"""
        query = """
            UPDATE users
            SET password_hash = $2, updated_at = NOW()
            WHERE user_id = $1
            RETURNING user_id
        """
        result = await Database.fetchval(query, user_id, new_password_hash)
        return result is not None

    async def update_last_login(self, user_id: UUID) -> bool:
        """Update last login timestamp"""
        query = """
            UPDATE users
            SET last_login_at = NOW(), updated_at = NOW()
            WHERE user_id = $1
            RETURNING user_id
        """
        result = await Database.fetchval(query, user_id)
        return result is not None

    async def deactivate(self, user_id: UUID) -> bool:
        """Deactivate user account"""
        query = """
            UPDATE users
            SET is_active = false, updated_at = NOW()
            WHERE user_id = $1
            RETURNING user_id
        """
        result = await Database.fetchval(query, user_id)
        return result is not None

    async def email_exists(self, email: str, exclude_user_id: Optional[UUID] = None) -> bool:
        """Check if email already exists"""
        if exclude_user_id:
            query = "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1 AND user_id != $2)"
            return await Database.fetchval(query, email, exclude_user_id)
        else:
            query = "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)"
            return await Database.fetchval(query, email)
