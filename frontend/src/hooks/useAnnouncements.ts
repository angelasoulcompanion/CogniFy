/**
 * CogniFy Announcement Hooks
 * React Query hooks for announcement/news management
 * Created with love by Angela & David - 4 January 2026
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { announcementsApi } from '@/services/api'
import type {
  CreateAnnouncementRequest,
  UpdateAnnouncementRequest,
} from '@/types'
import toast from 'react-hot-toast'

// =============================================================================
// QUERY KEYS
// =============================================================================

export const announcementKeys = {
  all: ['announcements'] as const,
  lists: () => [...announcementKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...announcementKeys.lists(), filters] as const,
  pinned: () => [...announcementKeys.all, 'pinned'] as const,
  details: () => [...announcementKeys.all, 'detail'] as const,
  detail: (id: string) => [...announcementKeys.details(), id] as const,
  admin: () => [...announcementKeys.all, 'admin'] as const,
  adminList: (filters: Record<string, unknown>) => [...announcementKeys.admin(), filters] as const,
}

// =============================================================================
// QUERY HOOKS (for users)
// =============================================================================

/**
 * Get published announcements
 */
export function useAnnouncements(filters?: {
  skip?: number
  limit?: number
  category?: string
}) {
  return useQuery({
    queryKey: announcementKeys.list(filters || {}),
    queryFn: () => announcementsApi.list(filters),
    staleTime: 60 * 1000, // 1 minute
  })
}

/**
 * Get pinned announcements (for homepage highlight)
 */
export function usePinnedAnnouncements(limit = 5) {
  return useQuery({
    queryKey: announcementKeys.pinned(),
    queryFn: () => announcementsApi.getPinned(limit),
    staleTime: 60 * 1000, // 1 minute
  })
}

/**
 * Get single announcement by ID
 */
export function useAnnouncement(announcementId: string) {
  return useQuery({
    queryKey: announcementKeys.detail(announcementId),
    queryFn: () => announcementsApi.get(announcementId),
    enabled: !!announcementId,
  })
}

// =============================================================================
// ADMIN QUERY HOOKS
// =============================================================================

/**
 * Get all announcements including drafts (admin only)
 */
export function useAdminAnnouncements(filters?: {
  skip?: number
  limit?: number
}) {
  return useQuery({
    queryKey: announcementKeys.adminList(filters || {}),
    queryFn: () => announcementsApi.listAll(filters),
    staleTime: 30 * 1000, // 30 seconds
  })
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

/**
 * Create new announcement (admin only)
 */
export function useCreateAnnouncement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateAnnouncementRequest) => announcementsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: announcementKeys.all })
      toast.success('Announcement created successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to create announcement: ${error.message}`)
    },
  })
}

/**
 * Update announcement (admin only)
 */
export function useUpdateAnnouncement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ announcementId, data }: { announcementId: string; data: UpdateAnnouncementRequest }) =>
      announcementsApi.update(announcementId, data),
    onSuccess: (_, { announcementId }) => {
      queryClient.invalidateQueries({ queryKey: announcementKeys.all })
      queryClient.invalidateQueries({ queryKey: announcementKeys.detail(announcementId) })
      toast.success('Announcement updated successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to update announcement: ${error.message}`)
    },
  })
}

/**
 * Delete announcement (admin only)
 */
export function useDeleteAnnouncement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (announcementId: string) => announcementsApi.delete(announcementId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: announcementKeys.all })
      toast.success('Announcement deleted successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete announcement: ${error.message}`)
    },
  })
}

/**
 * Publish announcement (admin only)
 */
export function usePublishAnnouncement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (announcementId: string) => announcementsApi.publish(announcementId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: announcementKeys.all })
      toast.success('Announcement published')
    },
    onError: (error: Error) => {
      toast.error(`Failed to publish announcement: ${error.message}`)
    },
  })
}

/**
 * Unpublish announcement (admin only)
 */
export function useUnpublishAnnouncement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (announcementId: string) => announcementsApi.unpublish(announcementId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: announcementKeys.all })
      toast.success('Announcement unpublished')
    },
    onError: (error: Error) => {
      toast.error(`Failed to unpublish announcement: ${error.message}`)
    },
  })
}

/**
 * Pin announcement to top (admin only)
 */
export function usePinAnnouncement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (announcementId: string) => announcementsApi.pin(announcementId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: announcementKeys.all })
      toast.success('Announcement pinned')
    },
    onError: (error: Error) => {
      toast.error(`Failed to pin announcement: ${error.message}`)
    },
  })
}

/**
 * Unpin announcement (admin only)
 */
export function useUnpinAnnouncement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (announcementId: string) => announcementsApi.unpin(announcementId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: announcementKeys.all })
      toast.success('Announcement unpinned')
    },
    onError: (error: Error) => {
      toast.error(`Failed to unpin announcement: ${error.message}`)
    },
  })
}
