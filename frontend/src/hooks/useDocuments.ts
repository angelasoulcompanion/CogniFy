/**
 * CogniFy Documents Hook
 * Created with love by Angela & David - 1 January 2026
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi } from '@/services/api'
import toast from 'react-hot-toast'

// =============================================================================
// DOCUMENTS QUERY HOOKS
// =============================================================================

export function useDocuments(limit = 20, offset = 0, enablePolling = false) {
  return useQuery({
    queryKey: ['documents', limit, offset],
    queryFn: () => documentsApi.list(limit, offset),
    select: (data) => data.documents || [],
    // Auto-poll every 2 seconds when enabled (for tracking processing status)
    refetchInterval: enablePolling ? 2000 : false,
  })
}

export function useDocument(documentId: string) {
  return useQuery({
    queryKey: ['document', documentId],
    queryFn: () => documentsApi.get(documentId),
    enabled: !!documentId,
  })
}

export function useDocumentChunks(documentId: string, limit = 50) {
  return useQuery({
    queryKey: ['documentChunks', documentId, limit],
    queryFn: () => documentsApi.getChunks(documentId, limit),
    enabled: !!documentId,
  })
}

export function useDocumentStats(documentId: string) {
  return useQuery({
    queryKey: ['documentStats', documentId],
    queryFn: () => documentsApi.getStats(documentId),
    enabled: !!documentId,
  })
}

// =============================================================================
// DOCUMENTS MUTATION HOOKS
// =============================================================================

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      file,
      onProgress,
    }: {
      file: File
      onProgress?: (progress: number) => void
    }) => {
      return documentsApi.upload(file, onProgress)
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      const filename = data.original_filename || data.document?.original_filename || 'Document'
      toast.success(`Document "${filename}" uploaded successfully`)
    },
    onError: (error: Error) => {
      toast.error(`Upload failed: ${error.message}`)
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (documentId: string) => documentsApi.delete(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document deleted')
    },
    onError: (error: Error) => {
      toast.error(`Delete failed: ${error.message}`)
    },
  })
}

export function useProcessDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (documentId: string) => documentsApi.process(documentId),
    onSuccess: (_, documentId) => {
      queryClient.invalidateQueries({ queryKey: ['document', documentId] })
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document processing started')
    },
    onError: (error: Error) => {
      toast.error(`Processing failed: ${error.message}`)
    },
  })
}

export function useReprocessDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (documentId: string) => documentsApi.reprocess(documentId),
    onSuccess: (_, documentId) => {
      queryClient.invalidateQueries({ queryKey: ['document', documentId] })
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document reprocessing started')
    },
    onError: (error: Error) => {
      toast.error(`Reprocessing failed: ${error.message}`)
    },
  })
}

// =============================================================================
// DOCUMENT UTILS - Re-export from centralized statusColors
// =============================================================================

export { getDocumentStatusColor, getDocumentStatusLabel } from '@/lib/statusColors'
