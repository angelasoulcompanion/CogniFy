/**
 * CogniFy SSE Streaming Service
 * Server-Sent Events for real-time chat
 * With secure token refresh support
 *
 * Created with love by Angela & David - 2 January 2026
 */

import type { SSEEvent, RAGSettings } from '@/types'
import { getTokens, saveAccessToken, clearAuth } from './api'
import axios from 'axios'

const API_BASE_URL = '/api'

// Refresh token for SSE requests (uses HttpOnly cookie)
const refreshTokenForSSE = async (): Promise<string | null> => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/v1/auth/refresh`,
      {}, // Empty body - refresh token is in cookie
      { withCredentials: true }
    )
    const { access_token, expires_in } = response.data
    saveAccessToken(access_token, expires_in)
    return access_token
  } catch {
    clearAuth()
    return null
  }
}

// Get valid token (refresh if needed)
const getValidToken = async (): Promise<string | null> => {
  const { accessToken, expiry } = getTokens()

  if (!accessToken) return null

  // Check if token is about to expire (5 min buffer)
  const bufferMs = 5 * 60 * 1000
  if (expiry && Date.now() >= expiry - bufferMs) {
    return await refreshTokenForSSE()
  }

  return accessToken
}

export interface StreamChatOptions {
  message: string
  conversationId?: string
  ragEnabled?: boolean
  ragSettings?: RAGSettings
  documentIds?: string[]
  provider?: string
  model?: string
  expert?: string
  onEvent: (event: SSEEvent) => void
  onError: (error: Error) => void
  onComplete: () => void
}

/**
 * Stream chat using Server-Sent Events
 */
export async function streamChat(options: StreamChatOptions): Promise<() => void> {
  const {
    message,
    conversationId,
    ragEnabled = true,
    ragSettings,
    documentIds,
    provider = 'ollama',
    model,
    expert = 'general',
    onEvent,
    onError,
    onComplete,
  } = options

  // Get valid token (auto refresh if needed)
  const token = await getValidToken()

  const body = JSON.stringify({
    message,
    conversation_id: conversationId,
    rag_enabled: ragEnabled,
    rag_settings: ragSettings,
    document_ids: documentIds,
    provider,
    model,
    expert,
    stream: true,
  })

  let aborted = false

  try {
    const response = await fetch(`${API_BASE_URL}/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body,
      credentials: 'include', // Send cookies for auth
    })

    if (!response.ok) {
      // Handle 401 - session expired (don't hard redirect, let auth interceptor handle)
      if (response.status === 401) {
        throw new Error('Session expired. Please login again.')
      }
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No reader available')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    const processChunk = async () => {
      while (!aborted) {
        const { done, value } = await reader.read()

        if (done) {
          onComplete()
          break
        }

        buffer += decoder.decode(value, { stream: true })

        // Process complete SSE events
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              onEvent(data as SSEEvent)
            } catch {
              // Ignore parse errors for incomplete data
            }
          }
        }
      }
    }

    processChunk().catch(onError)

    // Return abort function
    return () => {
      aborted = true
      reader.cancel()
    }
  } catch (error) {
    onError(error as Error)
    return () => {}
  }
}

/**
 * Stream chat with AbortController support
 */
export class ChatStream {
  private abortController: AbortController | null = null
  private isActive = false

  async start(options: Omit<StreamChatOptions, 'onComplete'> & {
    onComplete?: () => void
  }): Promise<void> {
    if (this.isActive) {
      this.abort()
    }

    this.abortController = new AbortController()
    this.isActive = true

    const abort = await streamChat({
      ...options,
      onComplete: () => {
        this.isActive = false
        options.onComplete?.()
      },
      onError: (error) => {
        this.isActive = false
        options.onError(error)
      },
    })

    // Store abort function
    const originalAbort = this.abort.bind(this)
    this.abort = () => {
      abort()
      originalAbort()
    }
  }

  abort(): void {
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
    this.isActive = false
  }

  get streaming(): boolean {
    return this.isActive
  }
}

// Export singleton instance
export const chatStream = new ChatStream()
