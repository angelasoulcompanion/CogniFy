-- Migration: 005_announcements.sql
-- Purpose: Create announcements table for organization news
-- Created: 4 January 2026

-- =============================================================================
-- ANNOUNCEMENTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS announcements (
    announcement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,                           -- Markdown content
    cover_image_url VARCHAR(1000),                   -- Optional cover image URL
    category VARCHAR(50) DEFAULT 'general',          -- general, important, update, event
    is_pinned BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Index for fetching published announcements (most common query)
CREATE INDEX IF NOT EXISTS idx_announcements_published
ON announcements(is_published, published_at DESC NULLS LAST);

-- Index for fetching pinned announcements
CREATE INDEX IF NOT EXISTS idx_announcements_pinned
ON announcements(is_pinned, is_published, published_at DESC NULLS LAST);

-- Index for category filtering
CREATE INDEX IF NOT EXISTS idx_announcements_category
ON announcements(category) WHERE is_published = TRUE;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE announcements IS 'Organization news and announcements';
COMMENT ON COLUMN announcements.content IS 'Markdown formatted content';
COMMENT ON COLUMN announcements.cover_image_url IS 'Optional URL for cover/thumbnail image';
COMMENT ON COLUMN announcements.category IS 'Category: general, important, update, event';
COMMENT ON COLUMN announcements.is_pinned IS 'Pinned announcements appear at top';
COMMENT ON COLUMN announcements.is_published IS 'Only published announcements are visible to users';
COMMENT ON COLUMN announcements.published_at IS 'Timestamp when announcement was published';
