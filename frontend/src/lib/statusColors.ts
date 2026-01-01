/**
 * CogniFy Status Colors Utility
 * Centralized status color management following Angela Purple Theme
 * Created with love by Angela & David - 1 January 2026
 */

// =============================================================================
// STATUS TYPES
// =============================================================================

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type SyncStatus = 'completed' | 'syncing' | 'pending' | 'failed' | null
export type UserStatus = 'active' | 'inactive'
export type UserRole = 'admin' | 'editor' | 'user'

// =============================================================================
// BADGE CLASS HELPERS (Tailwind classes for dark theme)
// =============================================================================

/**
 * Get badge class for document processing status
 */
export function getDocumentStatusColor(status: ProcessingStatus): string {
  const colors: Record<ProcessingStatus, string> = {
    pending: 'bg-yellow-500/20 text-yellow-400',
    processing: 'bg-blue-500/20 text-blue-400',
    completed: 'bg-green-500/20 text-green-400',
    failed: 'bg-red-500/20 text-red-400',
  }
  return colors[status] || 'bg-gray-500/20 text-gray-400'
}

/**
 * Get badge class for connector sync status
 */
export function getConnectionStatusColor(status: SyncStatus): string {
  if (status === 'completed') return 'bg-green-500/20 text-green-400'
  if (status === 'syncing') return 'bg-blue-500/20 text-blue-400'
  if (status === 'failed') return 'bg-red-500/20 text-red-400'
  if (status === 'pending') return 'bg-yellow-500/20 text-yellow-400'
  return 'bg-gray-500/20 text-gray-400'
}

/**
 * Get badge class for user role
 */
export function getRoleBadgeColor(role: UserRole | string): string {
  switch (role) {
    case 'admin':
      return 'bg-red-500/20 text-red-400'
    case 'editor':
      return 'bg-blue-500/20 text-blue-400'
    default:
      return 'bg-gray-500/20 text-gray-400'
  }
}

/**
 * Get badge class for user active status
 */
export function getUserStatusColor(isActive: boolean): string {
  return isActive
    ? 'bg-green-500/20 text-green-400'
    : 'bg-red-500/20 text-red-400'
}

// =============================================================================
// TEXT COLOR HELPERS (Just the text color for icons, dots, etc.)
// =============================================================================

/**
 * Get text color class for status
 */
export function getStatusTextColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'text-yellow-400',
    processing: 'text-blue-400',
    syncing: 'text-blue-400',
    completed: 'text-green-400',
    success: 'text-green-400',
    active: 'text-green-400',
    failed: 'text-red-400',
    error: 'text-red-400',
    inactive: 'text-gray-400',
  }
  return colors[status.toLowerCase()] || 'text-gray-400'
}

// =============================================================================
// STATUS LABELS
// =============================================================================

/**
 * Get human-readable label for document status
 */
export function getDocumentStatusLabel(status: ProcessingStatus): string {
  const labels: Record<ProcessingStatus, string> = {
    pending: 'Pending',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
  }
  return labels[status] || status
}

/**
 * Get human-readable label for sync status
 */
export function getSyncStatusLabel(status: SyncStatus): string {
  if (!status) return 'Not synced'
  const labels: Record<string, string> = {
    completed: 'Synced',
    syncing: 'Syncing',
    pending: 'Pending',
    failed: 'Failed',
  }
  return labels[status] || status
}

// =============================================================================
// ACTIVITY TYPE HELPERS (for AdminPage)
// =============================================================================

export type ActivityType = 'document' | 'query' | 'login' | 'upload'

/**
 * Get background color for activity type
 */
export function getActivityTypeColor(type: ActivityType | string): string {
  const colors: Record<string, string> = {
    document: 'bg-blue-500/20',
    query: 'bg-purple-500/20',
    login: 'bg-green-500/20',
    upload: 'bg-yellow-500/20',
  }
  return colors[type] || 'bg-gray-500/20'
}

// =============================================================================
// GENERIC STATUS COLOR MAP (for dynamic usage)
// =============================================================================

export const statusColorMap = {
  // Success states
  success: 'bg-green-500/20 text-green-400',
  completed: 'bg-green-500/20 text-green-400',
  active: 'bg-green-500/20 text-green-400',

  // Warning states
  warning: 'bg-yellow-500/20 text-yellow-400',
  pending: 'bg-yellow-500/20 text-yellow-400',

  // Info states
  info: 'bg-blue-500/20 text-blue-400',
  processing: 'bg-blue-500/20 text-blue-400',
  syncing: 'bg-blue-500/20 text-blue-400',

  // Error states
  error: 'bg-red-500/20 text-red-400',
  failed: 'bg-red-500/20 text-red-400',
  inactive: 'bg-red-500/20 text-red-400',

  // Neutral
  default: 'bg-gray-500/20 text-gray-400',
} as const

/**
 * Get status color from the generic map
 */
export function getStatusColor(status: string): string {
  return (
    statusColorMap[status.toLowerCase() as keyof typeof statusColorMap] ||
    statusColorMap.default
  )
}
