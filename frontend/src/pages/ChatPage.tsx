/**
 * CogniFy Chat Page
 * Main chat interface with SSE streaming
 * Created with love by Angela & David - 1 January 2026
 */

import { useState, useRef, useEffect, FormEvent } from 'react'
import { useChat, useChatStore } from '@/hooks/useChat'
import { cn } from '@/lib/utils'
import {
  Send,
  StopCircle,
  FileText,
  ChevronRight,
  Bot,
  User,
  Sparkles,
  Search,
  Loader2,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { ChatMessage, SourceReference } from '@/types'

export function ChatPage() {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const { messages } = useChatStore()
  const {
    isStreaming,
    isLoading,
    sendMessage,
    stopStreaming,
  } = useChat()

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return

    sendMessage(input)
    setInput('')

    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <header className="flex h-16 items-center justify-between border-b border-primary-500/10 bg-secondary-900/50 backdrop-blur-sm px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-500/20">
            <Bot className="h-6 w-6 text-primary-400" />
          </div>
          <div>
            <h1 className="font-semibold text-white">CogniFy Chat</h1>
            <p className="text-sm text-secondary-400">Ask questions about your documents</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-green-500/20 px-3 py-1 text-sm text-green-400">
            <span className="h-2 w-2 rounded-full bg-green-500"></span>
            RAG Enabled
          </span>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="mx-auto max-w-3xl space-y-6">
            {messages.map((message) => (
              <MessageBubble key={message.message_id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-primary-500/10 bg-secondary-900/50 backdrop-blur-sm p-4">
        <form onSubmit={handleSubmit} className="mx-auto max-w-3xl">
          <div className="relative flex items-end gap-2 rounded-2xl border border-secondary-700 bg-secondary-800/50 p-2 focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/20">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              rows={1}
              className="flex-1 resize-none bg-transparent px-3 py-2 text-white placeholder-secondary-500 focus:outline-none"
              disabled={isStreaming}
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={stopStreaming}
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-500 text-white transition-colors hover:bg-red-600"
              >
                <StopCircle className="h-5 w-5" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-primary-600 to-violet-600 text-white transition-colors hover:from-primary-500 hover:to-violet-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="h-5 w-5" />
              </button>
            )}
          </div>
          <p className="mt-2 text-center text-xs text-secondary-500">
            CogniFy uses RAG to search your documents and provide accurate answers
          </p>
        </form>
      </div>
    </div>
  )
}

// =============================================================================
// MESSAGE BUBBLE COMPONENT
// =============================================================================

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.message_type === 'user'
  const isStreaming = message.isStreaming

  return (
    <div
      className={cn(
        'flex gap-4 animate-fade-in-up',
        isUser ? 'flex-row-reverse' : ''
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-primary-500/20' : 'bg-secondary-700'
        )}
      >
        {isUser ? (
          <User className="h-5 w-5 text-primary-400" />
        ) : (
          <Bot className="h-5 w-5 text-secondary-400" />
        )}
      </div>

      {/* Content */}
      <div className={cn('flex-1', isUser ? 'text-right' : '')}>
        <div
          className={cn(
            'inline-block rounded-2xl px-4 py-3 max-w-full',
            isUser
              ? 'bg-gradient-to-r from-primary-600 to-violet-600 text-white'
              : 'bg-secondary-800 text-secondary-200'
          )}
        >
          {isStreaming && !message.content ? (
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Thinking...</span>
            </div>
          ) : (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Streaming indicator */}
        {isStreaming && message.content && (
          <div className="mt-2 flex items-center gap-2 text-sm text-secondary-500">
            <span className="flex gap-1">
              <span className="h-2 w-2 rounded-full bg-primary-500 animate-pulse-dot"></span>
              <span className="h-2 w-2 rounded-full bg-primary-500 animate-pulse-dot" style={{ animationDelay: '0.2s' }}></span>
              <span className="h-2 w-2 rounded-full bg-primary-500 animate-pulse-dot" style={{ animationDelay: '0.4s' }}></span>
            </span>
            <span>Generating...</span>
          </div>
        )}

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <SourcesList sources={message.sources} />
        )}

        {/* Meta info */}
        {!isUser && message.response_time_ms && (
          <p className="mt-2 text-xs text-secondary-400">
            Response time: {message.response_time_ms}ms
          </p>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// SOURCES LIST COMPONENT
// =============================================================================

function SourcesList({ sources }: { sources: SourceReference[] }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="mt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm text-secondary-400 hover:text-secondary-200 transition-colors"
      >
        <FileText className="h-4 w-4" />
        <span>{sources.length} source{sources.length !== 1 ? 's' : ''}</span>
        <ChevronRight
          className={cn(
            'h-4 w-4 transition-transform',
            expanded && 'rotate-90'
          )}
        />
      </button>

      {expanded && (
        <div className="mt-2 space-y-2">
          {sources.map((source) => (
            <div
              key={source.index}
              className="rounded-lg bg-secondary-800/50 border border-secondary-700 p-3 text-sm"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary-500/20 text-xs font-medium text-primary-400">
                    {source.index}
                  </span>
                  <span className="font-medium text-white">
                    {source.document_name}
                  </span>
                </div>
                <span className="text-xs text-secondary-500">
                  {(source.score * 100).toFixed(0)}% match
                </span>
              </div>
              {source.page_number && (
                <p className="mt-1 text-xs text-secondary-500">
                  Page {source.page_number}
                  {source.section && ` - ${source.section}`}
                </p>
              )}
              <p className="mt-2 text-secondary-400 line-clamp-2">
                {source.content_preview}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// =============================================================================
// EMPTY STATE COMPONENT
// =============================================================================

function EmptyState() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center max-w-md">
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 to-violet-600">
          <Sparkles className="h-10 w-10 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white">
          Welcome to CogniFy
        </h2>
        <p className="mt-3 text-secondary-400">
          Start a conversation by asking questions about your documents.
          I'll search through your knowledge base and provide accurate answers.
        </p>

        <div className="mt-8 grid gap-3">
          <SuggestionCard
            icon={<Search className="h-5 w-5" />}
            title="Search documents"
            description="Find information across all your files"
          />
          <SuggestionCard
            icon={<FileText className="h-5 w-5" />}
            title="Summarize content"
            description="Get quick summaries of long documents"
          />
          <SuggestionCard
            icon={<Bot className="h-5 w-5" />}
            title="Ask questions"
            description="Get answers with source citations"
          />
        </div>
      </div>
    </div>
  )
}

function SuggestionCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-secondary-700 bg-secondary-800/50 p-4 text-left transition-colors hover:border-primary-500/50 hover:bg-secondary-800">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-500/20 text-primary-400">
        {icon}
      </div>
      <div>
        <h3 className="font-medium text-white">{title}</h3>
        <p className="text-sm text-secondary-400">{description}</p>
      </div>
    </div>
  )
}
