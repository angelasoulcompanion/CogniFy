/**
 * CogniFy Prompt Hooks
 * React Query hooks for prompt management
 * Created with love by Angela & David - 2 January 2026
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { promptsApi } from '@/services/api'
import type {
  CreatePromptRequest,
  UpdatePromptRequest,
  AIGenerateRequest,
} from '@/types/prompt'
import toast from 'react-hot-toast'

// =============================================================================
// QUERY KEYS
// =============================================================================

export const promptKeys = {
  all: ['prompts'] as const,
  lists: () => [...promptKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...promptKeys.lists(), filters] as const,
  details: () => [...promptKeys.all, 'detail'] as const,
  detail: (id: string) => [...promptKeys.details(), id] as const,
  guides: () => [...promptKeys.all, 'guides'] as const,
  stats: () => [...promptKeys.all, 'stats'] as const,
  categories: () => [...promptKeys.all, 'categories'] as const,
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function usePrompts(filters?: {
  category?: string
  expert_role?: string
  is_active?: boolean
  limit?: number
  offset?: number
}) {
  return useQuery({
    queryKey: promptKeys.list(filters || {}),
    queryFn: () => promptsApi.list(filters),
    staleTime: 30 * 1000, // 30 seconds
  })
}

export function usePrompt(templateId: string) {
  return useQuery({
    queryKey: promptKeys.detail(templateId),
    queryFn: () => promptsApi.get(templateId),
    enabled: !!templateId,
  })
}

export function useTemplateGuides() {
  return useQuery({
    queryKey: promptKeys.guides(),
    queryFn: () => promptsApi.getTemplateGuides(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function usePromptStats() {
  return useQuery({
    queryKey: promptKeys.stats(),
    queryFn: () => promptsApi.getStats(),
    staleTime: 60 * 1000, // 1 minute
  })
}

export function useCategories() {
  return useQuery({
    queryKey: promptKeys.categories(),
    queryFn: () => promptsApi.getCategories(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useCreatePrompt() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreatePromptRequest) => promptsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: promptKeys.all })
      toast.success('Prompt created successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to create prompt: ${error.message}`)
    },
  })
}

export function useUpdatePrompt() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ templateId, data }: { templateId: string; data: UpdatePromptRequest }) =>
      promptsApi.update(templateId, data),
    onSuccess: (_, { templateId }) => {
      queryClient.invalidateQueries({ queryKey: promptKeys.all })
      queryClient.invalidateQueries({ queryKey: promptKeys.detail(templateId) })
      toast.success('Prompt updated successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to update prompt: ${error.message}`)
    },
  })
}

export function useDeletePrompt() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (templateId: string) => promptsApi.delete(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: promptKeys.all })
      toast.success('Prompt deleted successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete prompt: ${error.message}`)
    },
  })
}

export function useSetDefaultPrompt() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (templateId: string) => promptsApi.setDefault(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: promptKeys.all })
      toast.success('Prompt set as default')
    },
    onError: (error: Error) => {
      toast.error(`Failed to set default: ${error.message}`)
    },
  })
}

export function useAIGeneratePrompt() {
  return useMutation({
    mutationFn: (data: AIGenerateRequest) => promptsApi.aiGenerate(data),
    onError: (error: Error) => {
      toast.error(`Failed to generate prompt: ${error.message}`)
    },
  })
}

export function useRenderPrompt() {
  return useMutation({
    mutationFn: ({ templateId, variables }: { templateId: string; variables: Record<string, string> }) =>
      promptsApi.render(templateId, variables),
    onError: (error: Error) => {
      toast.error(`Failed to render prompt: ${error.message}`)
    },
  })
}
