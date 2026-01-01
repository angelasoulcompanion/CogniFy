/**
 * CogniFy Admin Hooks
 * React Query hooks for admin dashboard
 * Created with love by Angela & David - 1 January 2026
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/services/api'
import type {
  SystemStats,
  UserListResponse,
  UsageMetrics,
  DocumentTypeStats,
  TopUser,
  ActivityItem,
} from '@/types'
import toast from 'react-hot-toast'

// =============================================================================
// QUERY KEYS
// =============================================================================

const adminKeys = {
  all: ['admin'] as const,
  stats: () => [...adminKeys.all, 'stats'] as const,
  users: (params?: { skip?: number; limit?: number; includeInactive?: boolean }) =>
    [...adminKeys.all, 'users', params] as const,
  usage: (params?: { days?: number; interval?: string }) =>
    [...adminKeys.all, 'usage', params] as const,
  documentStats: () => [...adminKeys.all, 'documentStats'] as const,
  topUsers: (limit?: number) => [...adminKeys.all, 'topUsers', limit] as const,
  activity: (limit?: number) => [...adminKeys.all, 'activity', limit] as const,
}

// =============================================================================
// QUERIES
// =============================================================================

/**
 * Get system statistics
 */
export function useSystemStats() {
  return useQuery<SystemStats>({
    queryKey: adminKeys.stats(),
    queryFn: () => adminApi.getStats(),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // 1 minute
  })
}

/**
 * Get all users with stats
 */
export function useUsers(skip = 0, limit = 50, includeInactive = false) {
  return useQuery<UserListResponse>({
    queryKey: adminKeys.users({ skip, limit, includeInactive }),
    queryFn: () => adminApi.listUsers(skip, limit, includeInactive),
    staleTime: 30 * 1000,
  })
}

/**
 * Get usage metrics over time
 */
export function useUsageMetrics(days = 30, interval = 'day') {
  return useQuery<UsageMetrics[]>({
    queryKey: adminKeys.usage({ days, interval }),
    queryFn: () => adminApi.getUsageMetrics(days, interval),
    staleTime: 60 * 1000,
  })
}

/**
 * Get document type statistics
 */
export function useDocumentTypeStats() {
  return useQuery<DocumentTypeStats[]>({
    queryKey: adminKeys.documentStats(),
    queryFn: () => adminApi.getDocumentTypeStats(),
    staleTime: 60 * 1000,
  })
}

/**
 * Get top users by activity
 */
export function useTopUsers(limit = 10) {
  return useQuery<TopUser[]>({
    queryKey: adminKeys.topUsers(limit),
    queryFn: () => adminApi.getTopUsers(limit),
    staleTime: 60 * 1000,
  })
}

/**
 * Get recent activity
 */
export function useRecentActivity(limit = 20) {
  return useQuery<ActivityItem[]>({
    queryKey: adminKeys.activity(limit),
    queryFn: () => adminApi.getRecentActivity(limit),
    staleTime: 30 * 1000,
  })
}

// =============================================================================
// MUTATIONS
// =============================================================================

/**
 * Update user role
 */
export function useUpdateUserRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      adminApi.updateUserRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminKeys.all })
      toast.success('User role updated')
    },
    onError: (error: Error) => {
      toast.error(`Failed to update role: ${error.message}`)
    },
  })
}

/**
 * Toggle user active status
 */
export function useToggleUserStatus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (userId: string) => adminApi.toggleUserStatus(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminKeys.all })
      toast.success('User status updated')
    },
    onError: (error: Error) => {
      toast.error(`Failed to update status: ${error.message}`)
    },
  })
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Format bytes to human readable size
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

/**
 * Format number with commas
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('en-US')
}

/**
 * Get role badge color - Re-export from centralized statusColors
 */
export { getRoleBadgeColor } from '@/lib/statusColors'

/**
 * Get file type icon
 */
export function getFileTypeIcon(fileType: string): string {
  switch (fileType.toLowerCase()) {
    case 'pdf':
      return 'file-text'
    case 'docx':
    case 'doc':
      return 'file-text'
    case 'xlsx':
    case 'xls':
      return 'file-spreadsheet'
    case 'txt':
      return 'file'
    case 'png':
    case 'jpg':
    case 'jpeg':
      return 'image'
    default:
      return 'file'
  }
}
