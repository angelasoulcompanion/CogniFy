"""
CogniFy API Dependencies
Re-export common dependencies for API endpoints
Created with love by Angela & David - 1 January 2026
"""

from app.core.security import (
    get_current_user,
    get_current_user_optional,
    require_admin,
    require_editor,
    require_role,
    TokenPayload,
)
from app.domain.entities.user import User, UserRole
from app.infrastructure.repositories.user_repository import UserRepository


# User repository instance
user_repo = UserRepository()


__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "require_admin",
    "require_editor",
    "require_role",
    "TokenPayload",
    "User",
    "UserRole",
    "user_repo",
]
