/**
 * CogniFy SSE Streaming Service
 * Server-Sent Events for real-time chat
 * Created with love by Angela & David - 1 January 2026
 */

import type { SSEEvent, RAGSettings } from '@/types'

const API_BASE_URL = '/api'

export interface StreamChatOptions {
  message: string
  conversationId?: string
  ragEnabled?: boolean
  ragSettings?: RAGSettings
  documentIds?: string[]
  provider?: string
  model?: string
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
    onEvent,
    onError,
    onComplete,
  } = options

  const token = localStorage.getItem('token')

  const body = JSON.stringify({
    message,
    conversation_id: conversationId,
    rag_enabled: ragEnabled,
    rag_settings: ragSettings,
    document_ids: documentIds,
    provider,
    model,
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
    })

    if (!response.ok) {
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
