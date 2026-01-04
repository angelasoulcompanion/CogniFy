/**
 * CogniFy API Service
 * Secure Token Management with HttpOnly Cookies
 *
 * Security Features:
 * - Access token in memory/sessionStorage (short-lived, cleared on browser close)
 * - Refresh token in HttpOnly cookie (XSS protected)
 * - Auto token refresh before expiry
 * - Automatic retry on 401
 *
 * Created with love by Angela & David - 2 January 2026
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = '/api'

// Token storage keys (only access token in sessionStorage now)
const TOKEN_KEY = 'token'
const TOKEN_EXPIRY_KEY = 'tokenExpiry'
const USER_KEY = 'user'

// Token refresh state
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (error: Error) => void
}> = []

// Process queued requests after token refresh
const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else if (token) {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Helper: Check if token is expired or about to expire (5 min buffer)
const isTokenExpired = (expiry: number | null): boolean => {
  if (!expiry) return true
  const bufferMs = 5 * 60 * 1000 // 5 minutes buffer
  return Date.now() >= expiry - bufferMs
}

// Helper: Save access token to sessionStorage
export const saveAccessToken = (accessToken: string, expiresIn: number) => {
  sessionStorage.setItem(TOKEN_KEY, accessToken)
  const expiry = Date.now() + expiresIn * 1000
  sessionStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toString())
}

// Helper: Clear all auth data
export const clearAuth = () => {
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(TOKEN_EXPIRY_KEY)
  sessionStorage.removeItem(USER_KEY)
  // IMPORTANT: Clear zustand persisted auth state to prevent auto-redirect to home
  sessionStorage.removeItem('cognify-auth')
}

// Helper: Get stored tokens
export const getTokens = () => ({
  accessToken: sessionStorage.getItem(TOKEN_KEY),
  expiry: sessionStorage.getItem(TOKEN_EXPIRY_KEY)
    ? parseInt(sessionStorage.getItem(TOKEN_EXPIRY_KEY)!)
    : null,
})

// Create axios instance with credentials for cookies
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable cookies for all requests
})

// Refresh token function (uses HttpOnly cookie automatically)
const refreshAccessToken = async (): Promise<string> => {
  // Cookie is sent automatically due to withCredentials
  const response = await axios.post(
    `${API_BASE_URL}/v1/auth/refresh`,
    {}, // Empty body - refresh token is in cookie
    { withCredentials: true }
  )

  const { access_token, expires_in } = response.data
  saveAccessToken(access_token, expires_in)

  return access_token
}

// Request interceptor - add auth token and check expiry
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Skip auth for login/register endpoints
    const skipAuthUrls = ['/v1/auth/login', '/v1/auth/register']
    if (skipAuthUrls.some((url) => config.url?.includes(url))) {
      return config
    }

    let { accessToken, expiry } = getTokens()

    // If token exists and is about to expire, try to refresh proactively
    if (accessToken && isTokenExpired(expiry)) {
      if (!isRefreshing) {
        isRefreshing = true
        try {
          accessToken = await refreshAccessToken()
          processQueue(null, accessToken)
        } catch (error) {
          processQueue(error as Error, null)
          clearAuth()
          window.location.href = '/login'
          return Promise.reject(error)
        } finally {
          isRefreshing = false
        }
      } else {
        // Wait for ongoing refresh
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              config.headers.Authorization = `Bearer ${token}`
              resolve(config)
            },
            reject: (err: Error) => {
              reject(err)
            },
          })
        })
      }
    }

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle 401 and retry with refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Skip retry for auth endpoints
      if (originalRequest.url?.includes('/v1/auth/')) {
        clearAuth()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        // Wait for ongoing refresh
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`
              resolve(api(originalRequest))
            },
            reject: (err: Error) => {
              reject(err)
            },
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const newToken = await refreshAccessToken()
        processQueue(null, newToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError as Error, null)
        clearAuth()
        toast.error('Session expired. Please login again.')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // Handle other errors
    if (error.response?.status === 403) {
      toast.error('You do not have permission to perform this action')
    } else if (error.response?.status === 500) {
      toast.error('Server error. Please try again later.')
    }

    return Promise.reject(error)
  }
)

export default api

// =============================================================================
// AUTH API
// =============================================================================

export const authApi = {
  login: async (username: string, password: string) => {
    const response = await api.post('/v1/auth/login', {
      username,
      password,
    })
    return response.data
  },

  register: async (email: string, password: string, fullName?: string) => {
    const response = await api.post('/v1/auth/register', {
      email,
      password,
      full_name: fullName,
    })
    return response.data
  },

  me: async () => {
    const response = await api.get('/v1/auth/me')
    return response.data
  },

  refresh: async () => {
    // Cookie is sent automatically
    const response = await api.post('/v1/auth/refresh', {})
    return response.data
  },

  logout: async () => {
    const response = await api.post('/v1/auth/logout')
    return response.data
  },

  logoutAll: async () => {
    const response = await api.post('/v1/auth/logout-all')
    return response.data
  },

  getSessions: async () => {
    const response = await api.get('/v1/auth/sessions')
    return response.data
  },

  revokeSession: async (sessionId: string) => {
    const response = await api.delete(`/v1/auth/sessions/${sessionId}`)
    return response.data
  },
}

// =============================================================================
// DOCUMENTS API
// =============================================================================

export const documentsApi = {
  list: async (limit = 20, offset = 0) => {
    const response = await api.get('/v1/documents', {
      params: { limit, offset },
    })
    return response.data
  },

  get: async (documentId: string) => {
    const response = await api.get(`/v1/documents/${documentId}`)
    return response.data
  },

  upload: async (file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
    return response.data
  },

  delete: async (documentId: string) => {
    const response = await api.delete(`/v1/documents/${documentId}`)
    return response.data
  },

  getChunks: async (documentId: string, limit = 50) => {
    const response = await api.get(`/v1/documents/${documentId}/chunks`, {
      params: { limit },
    })
    return response.data
  },

  getStats: async (documentId: string) => {
    const response = await api.get(`/v1/documents/${documentId}/stats`)
    return response.data
  },

  process: async (documentId: string) => {
    const response = await api.post(`/v1/documents/${documentId}/process`)
    return response.data
  },

  reprocess: async (documentId: string) => {
    const response = await api.post(`/v1/documents/${documentId}/reprocess`)
    return response.data
  },
}

// =============================================================================
// SEARCH API
// =============================================================================

export const searchApi = {
  // Basic semantic search
  semantic: async (query: string, options?: {
    limit?: number;
    threshold?: number;
    documentIds?: string[];
  }) => {
    const response = await api.post('/v1/search', {
      query,
      limit: options?.limit || 10,
      threshold: options?.threshold || 0.3,
      document_ids: options?.documentIds,
    })
    return response.data
  },

  // Enhanced semantic search with similarity method
  semanticAdvanced: async (options: {
    query: string;
    limit?: number;
    threshold?: number;
    similarityMethod?: 'cosine' | 'euclidean' | 'dot';
    documentIds?: string[];
    includeContent?: boolean;
  }) => {
    const response = await api.post('/v1/search', {
      query: options.query,
      limit: options.limit ?? 10,
      threshold: options.threshold ?? 0.3,
      similarity_method: options.similarityMethod ?? 'cosine',
      document_ids: options.documentIds,
      include_content: options.includeContent ?? true,
    })
    return response.data
  },

  // Basic hybrid search
  hybrid: async (query: string, options?: {
    limit?: number;
    threshold?: number;
    bm25Weight?: number;
    vectorWeight?: number;
    documentIds?: string[];
  }) => {
    const response = await api.post('/v1/search/hybrid', {
      query,
      limit: options?.limit || 10,
      threshold: options?.threshold || 0.3,
      bm25_weight: options?.bm25Weight || 0.4,
      vector_weight: options?.vectorWeight || 0.6,
      document_ids: options?.documentIds,
    })
    return response.data
  },

  // Enhanced hybrid search with RRF-K
  hybridAdvanced: async (options: {
    query: string;
    limit?: number;
    threshold?: number;
    bm25Weight?: number;
    vectorWeight?: number;
    rrfK?: number;
    documentIds?: string[];
  }) => {
    const response = await api.post('/v1/search/hybrid', {
      query: options.query,
      limit: options.limit ?? 10,
      threshold: options.threshold ?? 0.3,
      bm25_weight: options.bm25Weight ?? 0.4,
      vector_weight: options.vectorWeight ?? 0.6,
      rrf_k: options.rrfK ?? 60,
      document_ids: options.documentIds,
    })
    return response.data
  },

  // BM25 keyword search
  bm25: async (query: string, options?: {
    limit?: number;
    documentIds?: string[];
  }) => {
    const response = await api.post('/v1/search/bm25', {
      query,
      limit: options?.limit || 10,
      document_ids: options?.documentIds,
    })
    return response.data
  },

  // Find similar chunks
  findSimilar: async (chunkId: string, limit?: number) => {
    const response = await api.post(`/v1/search/similar/${chunkId}`, null, {
      params: { limit: limit ?? 5 },
    })
    return response.data
  },

  // Get search stats
  getStats: async () => {
    const response = await api.get('/v1/search/stats')
    return response.data
  },

  // Build RAG context
  context: async (query: string, options?: {
    maxChunks?: number;
    maxContextLength?: number;
    searchMethod?: string;
    documentIds?: string[];
  }) => {
    const response = await api.post('/v1/search/context', {
      query,
      max_chunks: options?.maxChunks || 10,
      max_context_length: options?.maxContextLength || 8000,
      search_method: options?.searchMethod || 'hybrid',
      document_ids: options?.documentIds,
    })
    return response.data
  },
}

// =============================================================================
// HEALTH API
// =============================================================================

export const healthApi = {
  check: async () => {
    const response = await api.get('/health')
    return response.data
  },

  embedding: async () => {
    const response = await api.get('/health/embedding')
    return response.data
  },
}

// =============================================================================
// CONNECTORS API
// =============================================================================

export const connectorsApi = {
  // List all connections
  list: async (skip = 0, limit = 100) => {
    const response = await api.get('/v1/connectors', {
      params: { skip, limit },
    })
    return response.data
  },

  // Get a connection
  get: async (connectionId: string) => {
    const response = await api.get(`/v1/connectors/${connectionId}`)
    return response.data
  },

  // Create a connection
  create: async (data: {
    name: string;
    db_type: string;
    host: string;
    port: number;
    database_name: string;
    username: string;
    password: string;
  }) => {
    const response = await api.post('/v1/connectors', data)
    return response.data
  },

  // Update a connection
  update: async (connectionId: string, data: {
    name?: string;
    host?: string;
    port?: number;
    database_name?: string;
    username?: string;
    password?: string;
    sync_enabled?: boolean;
  }) => {
    const response = await api.put(`/v1/connectors/${connectionId}`, data)
    return response.data
  },

  // Delete a connection
  delete: async (connectionId: string) => {
    const response = await api.delete(`/v1/connectors/${connectionId}`)
    return response.data
  },

  // Test a new connection
  testNew: async (data: {
    db_type: string;
    host: string;
    port: number;
    database_name: string;
    username: string;
    password: string;
  }) => {
    const response = await api.post('/v1/connectors/test', data)
    return response.data
  },

  // Test an existing connection
  test: async (connectionId: string) => {
    const response = await api.post(`/v1/connectors/${connectionId}/test`)
    return response.data
  },

  // Discover schema
  discoverSchema: async (connectionId: string) => {
    const response = await api.get(`/v1/connectors/${connectionId}/schema`)
    return response.data
  },

  // Sync connection to chunks
  sync: async (connectionId: string, options?: {
    tables?: string[];
    max_rows?: number;
    chunk_size?: number;
  }) => {
    const response = await api.post(`/v1/connectors/${connectionId}/sync`, {
      tables: options?.tables,
      max_rows: options?.max_rows || 1000,
      chunk_size: options?.chunk_size || 500,
    })
    return response.data
  },

  // Preview table data
  preview: async (connectionId: string, tableName: string, limit = 10) => {
    const response = await api.get(`/v1/connectors/${connectionId}/preview/${tableName}`, {
      params: { limit },
    })
    return response.data
  },

  // Execute custom query
  query: async (connectionId: string, query: string) => {
    const response = await api.post(`/v1/connectors/${connectionId}/query`, { query })
    return response.data
  },
}

// =============================================================================
// ADMIN API
// =============================================================================

export const adminApi = {
  // Get system statistics
  getStats: async () => {
    const response = await api.get('/v1/admin/stats')
    return response.data
  },

  // List all users
  listUsers: async (skip = 0, limit = 50, includeInactive = false) => {
    const response = await api.get('/v1/admin/users', {
      params: { skip, limit, include_inactive: includeInactive },
    })
    return response.data
  },

  // Get usage metrics
  getUsageMetrics: async (days = 30, interval = 'day') => {
    const response = await api.get('/v1/admin/usage', {
      params: { days, interval },
    })
    return response.data
  },

  // Get document type stats
  getDocumentTypeStats: async () => {
    const response = await api.get('/v1/admin/documents/stats')
    return response.data
  },

  // Get top users
  getTopUsers: async (limit = 10) => {
    const response = await api.get('/v1/admin/users/top', {
      params: { limit },
    })
    return response.data
  },

  // Get recent activity
  getRecentActivity: async (limit = 20) => {
    const response = await api.get('/v1/admin/activity', {
      params: { limit },
    })
    return response.data
  },

  // Update user role
  updateUserRole: async (userId: string, role: string) => {
    const response = await api.put(`/v1/admin/users/${userId}/role`, { role })
    return response.data
  },

  // Toggle user status
  toggleUserStatus: async (userId: string) => {
    const response = await api.put(`/v1/admin/users/${userId}/toggle-status`)
    return response.data
  },
}

// =============================================================================
// PROMPTS API
// =============================================================================

import type {
  PromptTemplate,
  PromptListResponse,
  CreatePromptRequest,
  UpdatePromptRequest,
  AIGenerateRequest,
  AIGenerateResponse,
  TemplateGuidesResponse,
  PromptStatsResponse,
  CategoriesResponse,
} from '@/types/prompt'

export const promptsApi = {
  // List all prompts
  list: async (params?: {
    category?: string
    expert_role?: string
    is_active?: boolean
    limit?: number
    offset?: number
  }): Promise<PromptListResponse> => {
    const response = await api.get('/v1/prompts', { params })
    return response.data
  },

  // Get prompt by ID
  get: async (templateId: string): Promise<PromptTemplate> => {
    const response = await api.get(`/v1/prompts/${templateId}`)
    return response.data
  },

  // Create new prompt
  create: async (data: CreatePromptRequest): Promise<PromptTemplate> => {
    const response = await api.post('/v1/prompts', data)
    return response.data
  },

  // Update prompt
  update: async (templateId: string, data: UpdatePromptRequest): Promise<PromptTemplate> => {
    const response = await api.put(`/v1/prompts/${templateId}`, data)
    return response.data
  },

  // Delete prompt
  delete: async (templateId: string): Promise<void> => {
    await api.delete(`/v1/prompts/${templateId}`)
  },

  // Set as default
  setDefault: async (templateId: string): Promise<void> => {
    await api.post(`/v1/prompts/${templateId}/set-default`)
  },

  // Get template guides
  getTemplateGuides: async (): Promise<TemplateGuidesResponse> => {
    const response = await api.get('/v1/prompts/templates')
    return response.data
  },

  // Get stats
  getStats: async (): Promise<PromptStatsResponse> => {
    const response = await api.get('/v1/prompts/stats')
    return response.data
  },

  // Get categories and roles
  getCategories: async (): Promise<CategoriesResponse> => {
    const response = await api.get('/v1/prompts/categories')
    return response.data
  },

  // AI generate prompt
  aiGenerate: async (data: AIGenerateRequest): Promise<AIGenerateResponse> => {
    const response = await api.post('/v1/prompts/ai-generate', data)
    return response.data
  },

  // Render prompt with variables
  render: async (templateId: string, variables: Record<string, string>): Promise<{ rendered: string }> => {
    const response = await api.post(`/v1/prompts/${templateId}/render`, variables)
    return response.data
  },
}

// =============================================================================
// ANNOUNCEMENTS API
// =============================================================================

import type {
  Announcement,
  AnnouncementListResponse,
  CreateAnnouncementRequest,
  UpdateAnnouncementRequest,
} from '@/types'

export const announcementsApi = {
  // List published announcements (for users)
  list: async (params?: {
    skip?: number
    limit?: number
    category?: string
  }): Promise<AnnouncementListResponse> => {
    const response = await api.get('/v1/announcements', { params })
    return response.data
  },

  // Get pinned announcements
  getPinned: async (limit = 5): Promise<Announcement[]> => {
    const response = await api.get('/v1/announcements/pinned', {
      params: { limit },
    })
    return response.data
  },

  // Get single announcement
  get: async (announcementId: string): Promise<Announcement> => {
    const response = await api.get(`/v1/announcements/${announcementId}`)
    return response.data
  },

  // Admin: List all announcements (including drafts)
  listAll: async (params?: {
    skip?: number
    limit?: number
  }): Promise<AnnouncementListResponse> => {
    const response = await api.get('/v1/announcements/admin/all', { params })
    return response.data
  },

  // Admin: Create announcement
  create: async (data: CreateAnnouncementRequest): Promise<Announcement> => {
    const response = await api.post('/v1/announcements', data)
    return response.data
  },

  // Admin: Update announcement
  update: async (announcementId: string, data: UpdateAnnouncementRequest): Promise<Announcement> => {
    const response = await api.put(`/v1/announcements/${announcementId}`, data)
    return response.data
  },

  // Admin: Delete announcement
  delete: async (announcementId: string): Promise<void> => {
    await api.delete(`/v1/announcements/${announcementId}`)
  },

  // Admin: Publish announcement
  publish: async (announcementId: string): Promise<Announcement> => {
    const response = await api.post(`/v1/announcements/${announcementId}/publish`)
    return response.data
  },

  // Admin: Unpublish announcement
  unpublish: async (announcementId: string): Promise<Announcement> => {
    const response = await api.post(`/v1/announcements/${announcementId}/unpublish`)
    return response.data
  },

  // Admin: Pin announcement
  pin: async (announcementId: string): Promise<Announcement> => {
    const response = await api.post(`/v1/announcements/${announcementId}/pin`)
    return response.data
  },

  // Admin: Unpin announcement
  unpin: async (announcementId: string): Promise<Announcement> => {
    const response = await api.post(`/v1/announcements/${announcementId}/unpin`)
    return response.data
  },
}
