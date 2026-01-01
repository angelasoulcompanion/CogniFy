/**
 * CogniFy API Service
 * Created with love by Angela & David - 1 January 2026
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = '/api'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    } else if (error.response?.status === 403) {
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

  refresh: async (refreshToken: string) => {
    const response = await api.post('/v1/auth/refresh', {
      refresh_token: refreshToken,
    })
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
// CHAT API
// =============================================================================

export const chatApi = {
  // Non-streaming chat
  complete: async (request: {
    message: string;
    conversationId?: string;
    ragEnabled?: boolean;
    provider?: string;
    model?: string;
  }) => {
    const response = await api.post('/v1/chat/complete', {
      message: request.message,
      conversation_id: request.conversationId,
      rag_enabled: request.ragEnabled ?? true,
      provider: request.provider || 'ollama',
      model: request.model,
    })
    return response.data
  },

  // List conversations
  listConversations: async (limit = 20, offset = 0) => {
    const response = await api.get('/v1/chat/conversations', {
      params: { limit, offset },
    })
    return response.data
  },

  // Get conversation
  getConversation: async (conversationId: string) => {
    const response = await api.get(`/v1/chat/conversations/${conversationId}`)
    return response.data
  },

  // Get messages
  getMessages: async (conversationId: string, limit = 50) => {
    const response = await api.get(`/v1/chat/conversations/${conversationId}/messages`, {
      params: { limit },
    })
    return response.data
  },

  // Delete conversation
  deleteConversation: async (conversationId: string) => {
    const response = await api.delete(`/v1/chat/conversations/${conversationId}`)
    return response.data
  },

  // Get available models
  getModels: async () => {
    const response = await api.get('/v1/chat/models')
    return response.data
  },

  // Health check
  health: async () => {
    const response = await api.get('/v1/chat/health')
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
