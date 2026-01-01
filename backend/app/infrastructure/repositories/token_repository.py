"""
Token Repository
Database operations for Refresh Token management with rotation support

Security Features:
- Token hashing (bcrypt)
- Token rotation tracking
- Reuse detection via family_id
- Audit logging (IP, user agent)

Created with love by Angela & David - 2 January 2026
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

from app.infrastructure.database import Database


@dataclass
class RefreshToken:
    """Refresh token entity"""
    token_id: UUID
    user_id: UUID
    token_hash: str
    family_id: UUID
    is_revoked: bool
    is_used: bool
    expires_at: datetime
    created_at: datetime
    last_used_at: Optional[datetime] = None
    rotated_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    device_info: Optional[str] = None


class TokenRepository:
    """Repository for refresh token management"""

    async def create(
        self,
        user_id: UUID,
        token_hash: str,
        family_id: UUID,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> RefreshToken:
        """Create a new refresh token record"""
        query = """
            INSERT INTO refresh_tokens (
                user_id, token_hash, family_id, expires_at,
                user_agent, ip_address, device_info
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """
        row = await Database.fetchrow(
            query,
            user_id,
            token_hash,
            family_id,
            expires_at,
            user_agent,
            ip_address,
            device_info,
        )
        return self._row_to_entity(row)

    async def get_by_id(self, token_id: UUID) -> Optional[RefreshToken]:
        """Get token by ID"""
        query = "SELECT * FROM refresh_tokens WHERE token_id = $1"
        row = await Database.fetchrow(query, token_id)
        if row is None:
            return None
        return self._row_to_entity(row)

    async def get_valid_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get valid (non-revoked, non-used, non-expired) token by hash"""
        query = """
            SELECT * FROM refresh_tokens
            WHERE token_hash = $1
              AND is_revoked = FALSE
              AND is_used = FALSE
              AND expires_at > NOW()
        """
        row = await Database.fetchrow(query, token_hash)
        if row is None:
            return None
        return self._row_to_entity(row)

    async def get_active_by_family(self, family_id: UUID) -> Optional[RefreshToken]:
        """Get the currently active token in a family"""
        query = """
            SELECT * FROM refresh_tokens
            WHERE family_id = $1
              AND is_revoked = FALSE
              AND is_used = FALSE
              AND expires_at > NOW()
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = await Database.fetchrow(query, family_id)
        if row is None:
            return None
        return self._row_to_entity(row)

    async def get_user_active_sessions(self, user_id: UUID) -> List[RefreshToken]:
        """Get all active sessions for a user"""
        query = """
            SELECT * FROM refresh_tokens
            WHERE user_id = $1
              AND is_revoked = FALSE
              AND is_used = FALSE
              AND expires_at > NOW()
            ORDER BY created_at DESC
        """
        rows = await Database.fetch(query, user_id)
        return [self._row_to_entity(row) for row in rows]

    async def mark_as_used(self, token_id: UUID) -> bool:
        """Mark token as used (after rotation)"""
        query = """
            UPDATE refresh_tokens
            SET is_used = TRUE,
                rotated_at = NOW(),
                last_used_at = NOW()
            WHERE token_id = $1
            RETURNING token_id
        """
        result = await Database.fetchval(query, token_id)
        return result is not None

    async def update_last_used(self, token_id: UUID) -> bool:
        """Update last used timestamp"""
        query = """
            UPDATE refresh_tokens
            SET last_used_at = NOW()
            WHERE token_id = $1
            RETURNING token_id
        """
        result = await Database.fetchval(query, token_id)
        return result is not None

    async def revoke_token(self, token_id: UUID) -> bool:
        """Revoke a specific token"""
        query = """
            UPDATE refresh_tokens
            SET is_revoked = TRUE
            WHERE token_id = $1
            RETURNING token_id
        """
        result = await Database.fetchval(query, token_id)
        return result is not None

    async def revoke_family(self, family_id: UUID) -> int:
        """
        Revoke all tokens in a family (used for logout or reuse detection)
        Returns number of revoked tokens
        """
        query = """
            UPDATE refresh_tokens
            SET is_revoked = TRUE
            WHERE family_id = $1
              AND is_revoked = FALSE
            RETURNING token_id
        """
        rows = await Database.fetch(query, family_id)
        return len(rows)

    async def revoke_all_user_tokens(self, user_id: UUID) -> int:
        """
        Revoke all tokens for a user (logout from all devices)
        Returns number of revoked tokens
        """
        query = """
            UPDATE refresh_tokens
            SET is_revoked = TRUE
            WHERE user_id = $1
              AND is_revoked = FALSE
            RETURNING token_id
        """
        rows = await Database.fetch(query, user_id)
        return len(rows)

    async def check_reuse(self, family_id: UUID, token_hash: str) -> bool:
        """
        Check if a used token is being reused (potential attack)
        Returns True if this is a reuse attempt
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM refresh_tokens
                WHERE family_id = $1
                  AND token_hash = $2
                  AND is_used = TRUE
            )
        """
        return await Database.fetchval(query, family_id, token_hash)

    async def get_family_token_count(self, family_id: UUID) -> int:
        """Get total number of tokens in a family (for monitoring)"""
        query = """
            SELECT COUNT(*) FROM refresh_tokens
            WHERE family_id = $1
        """
        return await Database.fetchval(query, family_id)

    async def cleanup_expired(self) -> int:
        """
        Remove expired tokens (should be run periodically)
        Returns number of deleted tokens
        """
        query = """
            DELETE FROM refresh_tokens
            WHERE expires_at < NOW()
            RETURNING token_id
        """
        rows = await Database.fetch(query)
        return len(rows)

    async def cleanup_old_revoked(self, days: int = 7) -> int:
        """
        Remove old revoked tokens (housekeeping)
        Returns number of deleted tokens
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query = """
            DELETE FROM refresh_tokens
            WHERE is_revoked = TRUE
              AND created_at < $1
            RETURNING token_id
        """
        rows = await Database.fetch(query, cutoff)
        return len(rows)

    def _row_to_entity(self, row) -> RefreshToken:
        """Convert database row to RefreshToken entity"""
        return RefreshToken(
            token_id=row["token_id"],
            user_id=row["user_id"],
            token_hash=row["token_hash"],
            family_id=row["family_id"],
            is_revoked=row["is_revoked"],
            is_used=row["is_used"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
            last_used_at=row.get("last_used_at"),
            rotated_at=row.get("rotated_at"),
            user_agent=row.get("user_agent"),
            ip_address=str(row["ip_address"]) if row.get("ip_address") else None,
            device_info=row.get("device_info"),
        )


# Singleton instance
_token_repository: Optional[TokenRepository] = None


def get_token_repository() -> TokenRepository:
    """Get token repository singleton"""
    global _token_repository
    if _token_repository is None:
        _token_repository = TokenRepository()
    return _token_repository
