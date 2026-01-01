-- ============================================================================
-- CogniFy Database Migration - Connector Updates
-- Version: 0.2.0
-- Description: Add connector sync columns
-- ============================================================================

-- Add sync_config column for storing sync settings as JSONB
ALTER TABLE database_connections
ADD COLUMN IF NOT EXISTS sync_config JSONB DEFAULT '{}';

-- Add total_chunks_synced column
ALTER TABLE database_connections
ADD COLUMN IF NOT EXISTS total_chunks_synced INTEGER DEFAULT 0;

-- Add last_sync_error column
ALTER TABLE database_connections
ADD COLUMN IF NOT EXISTS last_sync_error TEXT;

-- Update comment
COMMENT ON COLUMN database_connections.sync_config IS 'Sync configuration (tables, options)';
COMMENT ON COLUMN database_connections.total_chunks_synced IS 'Total document chunks created from sync';
COMMENT ON COLUMN database_connections.last_sync_error IS 'Error message from last sync attempt';
