"""
User Entity
Domain model for user management
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    EDITOR = "editor"
    USER = "user"


@dataclass
class User:
    """User domain entity"""

    email: str
    password_hash: str
    user_id: UUID = field(default_factory=uuid4)
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    last_login_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate entity after initialization"""
        self._validate()

    def _validate(self):
        """Validate user data"""
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email address")
        if not self.password_hash:
            raise ValueError("Password hash is required")

    def update_login(self) -> None:
        """Update last login timestamp"""
        self.last_login_at = datetime.now()
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Deactivate user account"""
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activate user account"""
        self.is_active = True
        self.updated_at = datetime.now()

    def change_role(self, new_role: UserRole) -> None:
        """Change user role"""
        self.role = new_role
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary (excluding password)"""
        return {
            "user_id": str(self.user_id),
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create User from dictionary"""
        return cls(
            user_id=UUID(data["user_id"]) if isinstance(data.get("user_id"), str) else data.get("user_id", uuid4()),
            email=data["email"],
            password_hash=data["password_hash"],
            full_name=data.get("full_name"),
            role=UserRole(data.get("role", "user")),
            is_active=data.get("is_active", True),
            last_login_at=data.get("last_login_at"),
            created_at=data.get("created_at", datetime.now()),
            updated_at=data.get("updated_at", datetime.now()),
        )
