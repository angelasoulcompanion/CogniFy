/**
 * CogniFy Chat Hook
 * Manages chat state and SSE streaming
 * Created with love by Angela & David - 1 January 2026
 */

import { useState, useCallback, useRef } from 'react'
import { create } from 'zustand'
import { chatApi } from '@/services/api'
import { streamChat } from '@/services/sse'
import type {
  ChatMessage,
  Conversation,
  SourceReference,
  RAGSettings,
  SSEEvent,
} from '@/types'
import toast from 'react-hot-toast'

// =============================================================================
// CHAT STORE
// =============================================================================

interface ChatStore {
  conversations: Conversation[]
  currentConversation: Conversation | null
  messages: ChatMessage[]
  isLoading: boolean
  setConversations: (conversations: Conversation[]) => void
  setCurrentConversation: (conversation: Conversation | null) => void
  setMessages: (messages: ChatMessage[]) => void
  addMessage: (message: ChatMessage) => void
  updateMessage: (messageId: string, updates: Partial<ChatMessage>) => void
  setLoading: (loading: boolean) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatStore>((set) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,

  setConversations: (conversations) => set({ conversations }),
  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),
  updateMessage: (messageId, updates) => set((state) => ({
    messages: state.messages.map((m) =>
      m.message_id === messageId ? { ...m, ...updates } : m
    ),
  })),
  setLoading: (isLoading) => set({ isLoading }),
  clearMessages: () => set({ messages: [] }),
}))

// =============================================================================
// CHAT HOOK
// =============================================================================

interface UseChatOptions {
  ragEnabled?: boolean
  ragSettings?: RAGSettings
  documentIds?: string[]
  provider?: string
  model?: string
}

export function useChat(options: UseChatOptions = {}) {
  const {
    ragEnabled = true,
    ragSettings,
    documentIds,
    provider = 'ollama',
    model,
  } = options

  const {
    messages,
    currentConversation,
    addMessage,
    updateMessage,
    setLoading,
    isLoading,
  } = useChatStore()

  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [sources, setSources] = useState<SourceReference[]>([])
  const abortRef = useRef<(() => void) | null>(null)

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isStreaming) return

    // Add user message
    const userMessage: ChatMessage = {
      message_id: `temp-${Date.now()}`,
      conversation_id: currentConversation?.conversation_id || '',
      message_type: 'user',
      content: content.trim(),
      sources: null,
      response_time_ms: null,
      created_at: new Date().toISOString(),
    }
    addMessage(userMessage)

    // Add placeholder assistant message
    const assistantMessageId = `streaming-${Date.now()}`
    const assistantMessage: ChatMessage = {
      message_id: assistantMessageId,
      conversation_id: currentConversation?.conversation_id || '',
      message_type: 'assistant',
      content: '',
      sources: null,
      response_time_ms: null,
      created_at: new Date().toISOString(),
      isStreaming: true,
    }
    addMessage(assistantMessage)

    setIsStreaming(true)
    setStreamingContent('')
    setSources([])
    setLoading(true)

    let fullContent = ''
    let conversationId = currentConversation?.conversation_id

    try {
      const abort = await streamChat({
        message: content,
        conversationId,
        ragEnabled,
        ragSettings,
        documentIds,
        provider,
        model,
        onEvent: (event: SSEEvent) => {
          switch (event.type) {
            case 'session':
              conversationId = event.conversation_id
              break

            case 'search_start':
              // Could show search indicator
              break

            case 'search_results':
              // Preview of search results
              break

            case 'content':
              fullContent += event.content
              setStreamingContent(fullContent)
              updateMessage(assistantMessageId, {
                content: fullContent,
              })
              break

            case 'sources':
              setSources(event.sources)
              updateMessage(assistantMessageId, {
                sources: event.sources,
              })
              break

            case 'done':
              updateMessage(assistantMessageId, {
                message_id: event.message_id,
                content: fullContent,
                response_time_ms: event.response_time_ms,
                isStreaming: false,
              })
              break

            case 'error':
              toast.error(event.error)
              updateMessage(assistantMessageId, {
                content: `Error: ${event.error}`,
                isStreaming: false,
              })
              break
          }
        },
        onError: (error) => {
          console.error('Stream error:', error)
          toast.error('Failed to send message')
          updateMessage(assistantMessageId, {
            content: 'Failed to get response. Please try again.',
            isStreaming: false,
          })
        },
        onComplete: () => {
          setIsStreaming(false)
          setLoading(false)
        },
      })

      abortRef.current = abort
    } catch (error) {
      console.error('Chat error:', error)
      setIsStreaming(false)
      setLoading(false)
      toast.error('Failed to send message')
    }
  }, [
    isStreaming,
    currentConversation,
    ragEnabled,
    ragSettings,
    documentIds,
    provider,
    model,
    addMessage,
    updateMessage,
    setLoading,
  ])

  const stopStreaming = useCallback(() => {
    if (abortRef.current) {
      abortRef.current()
      abortRef.current = null
    }
    setIsStreaming(false)
    setLoading(false)
  }, [setLoading])

  const loadConversations = useCallback(async () => {
    try {
      const conversations = await chatApi.listConversations()
      useChatStore.getState().setConversations(conversations)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }, [])

  const loadMessages = useCallback(async (conversationId: string) => {
    try {
      const messages = await chatApi.getMessages(conversationId)
      useChatStore.getState().setMessages(messages)
    } catch (error) {
      console.error('Failed to load messages:', error)
    }
  }, [])

  const deleteConversation = useCallback(async (conversationId: string) => {
    try {
      await chatApi.deleteConversation(conversationId)
      await loadConversations()
      if (currentConversation?.conversation_id === conversationId) {
        useChatStore.getState().setCurrentConversation(null)
        useChatStore.getState().clearMessages()
      }
      toast.success('Conversation deleted')
    } catch (error) {
      console.error('Failed to delete conversation:', error)
      toast.error('Failed to delete conversation')
    }
  }, [currentConversation, loadConversations])

  return {
    messages,
    isStreaming,
    isLoading,
    streamingContent,
    sources,
    sendMessage,
    stopStreaming,
    loadConversations,
    loadMessages,
    deleteConversation,
  }
}
