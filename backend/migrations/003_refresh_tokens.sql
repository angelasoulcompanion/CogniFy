-- Migration: 003_refresh_tokens.sql
-- Secure Token Management System
-- Created with love by Angela & David - 2 January 2026

-- =============================================================================
-- REFRESH TOKENS TABLE
-- Stores refresh tokens with rotation support and reuse detection
-- =============================================================================

CREATE TABLE IF NOT EXISTS refresh_tokens (
    -- Primary key
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User reference
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Token data (hashed for security)
    token_hash VARCHAR(255) NOT NULL,

    -- Token family for rotation tracking
    -- All tokens in same rotation chain share family_id
    family_id UUID NOT NULL,

    -- Token state
    is_revoked BOOLEAN DEFAULT FALSE,
    is_used BOOLEAN DEFAULT FALSE,  -- Marked true after rotation

    -- Expiration
    expires_at TIMESTAMPTZ NOT NULL,

    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    rotated_at TIMESTAMPTZ,  -- When this token was rotated to a new one

    -- Security metadata
    user_agent TEXT,
    ip_address INET,
    device_info TEXT  -- Optional device fingerprint
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Fast lookup by user (for listing active sessions)
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);

-- Fast lookup by family (for rotation and revocation)
CREATE INDEX idx_refresh_tokens_family_id ON refresh_tokens(family_id);

-- Cleanup expired tokens
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- Find active (non-revoked, non-used) tokens
CREATE INDEX idx_refresh_tokens_active ON refresh_tokens(user_id, is_revoked, is_used)
    WHERE is_revoked = FALSE AND is_used = FALSE;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE refresh_tokens IS 'Secure refresh token storage with rotation support';
COMMENT ON COLUMN refresh_tokens.token_hash IS 'Bcrypt hash of the refresh token - never store plain tokens';
COMMENT ON COLUMN refresh_tokens.family_id IS 'Groups tokens in same rotation chain for reuse detection';
COMMENT ON COLUMN refresh_tokens.is_used IS 'True after token has been rotated - prevents reuse';
COMMENT ON COLUMN refresh_tokens.is_revoked IS 'True if token family was compromised or user logged out';

-- =============================================================================
-- CLEANUP FUNCTION
-- Automatically removes expired tokens (run periodically via cron)
-- =============================================================================

CREATE OR REPLACE FUNCTION cleanup_expired_refresh_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM refresh_tokens
    WHERE expires_at < NOW()
    RETURNING 1 INTO deleted_count;

    RETURN COALESCE(deleted_count, 0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_refresh_tokens IS 'Removes expired refresh tokens - call via scheduled job';
