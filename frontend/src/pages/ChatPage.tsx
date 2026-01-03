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
  Settings2,
  Cpu,
  Cloud,
  Trash2,
  GraduationCap,
  BrainCircuit,
  LineChart,
  Scale,
  FileCode,
  Briefcase,
  type LucideIcon,
} from 'lucide-react'
import { Streamdown } from 'streamdown'
import type { ChatMessage, SourceReference } from '@/types'

// Model options - match actual installed Ollama models
const MODEL_OPTIONS = {
  local: [
    { value: 'llama3.2:1b', label: 'Llama 3.2 (1B)', provider: 'ollama' },
    { value: 'llama3.1:8b', label: 'Llama 3.1 (8B)', provider: 'ollama' },
    { value: 'qwen2.5:7b', label: 'Qwen 2.5 (7B)', provider: 'ollama' },
    { value: 'qwen2.5:3b', label: 'Qwen 2.5 (3B)', provider: 'ollama' },
    { value: 'phi3:mini', label: 'Phi-3 Mini', provider: 'ollama' },
  ],
  api: [
    { value: 'gpt-4o', label: 'GPT-4o', provider: 'openai' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini', provider: 'openai' },
  ],
}

// Expert options for role-based prompting
interface ExpertOption {
  value: string
  label: string
  labelTh: string
  icon: LucideIcon
  color: string
  description: string
}

const EXPERT_OPTIONS: ExpertOption[] = [
  {
    value: 'general',
    label: 'General Assistant',
    labelTh: 'ผู้ช่วยทั่วไป',
    icon: Bot,
    color: 'text-primary-400',
    description: 'All-purpose helpful assistant',
  },
  {
    value: 'financial_analyst',
    label: 'Financial Analyst',
    labelTh: 'นักวิเคราะห์การเงิน',
    icon: LineChart,
    color: 'text-green-400',
    description: 'Financial data, reports, and analysis',
  },
  {
    value: 'legal_expert',
    label: 'Legal Expert',
    labelTh: 'ผู้เชี่ยวชาญกฎหมาย',
    icon: Scale,
    color: 'text-yellow-400',
    description: 'Contracts, legal documents, compliance',
  },
  {
    value: 'technical_writer',
    label: 'Technical Writer',
    labelTh: 'นักเขียนเทคนิค',
    icon: FileCode,
    color: 'text-blue-400',
    description: 'Documentation, specs, technical content',
  },
  {
    value: 'data_analyst',
    label: 'Data Analyst',
    labelTh: 'นักวิเคราะห์ข้อมูล',
    icon: BrainCircuit,
    color: 'text-cyan-400',
    description: 'Data patterns, statistics, insights',
  },
  {
    value: 'business_consultant',
    label: 'Business Consultant',
    labelTh: 'ที่ปรึกษาธุรกิจ',
    icon: Briefcase,
    color: 'text-orange-400',
    description: 'Strategy, operations, management',
  },
  {
    value: 'researcher',
    label: 'Researcher',
    labelTh: 'นักวิจัย',
    icon: GraduationCap,
    color: 'text-purple-400',
    description: 'Academic research, literature review',
  },
  {
    value: 'ai_engineer',
    label: 'AI Engineer',
    labelTh: 'วิศวกร AI',
    icon: Cpu,
    color: 'text-pink-400',
    description: 'ML, Deep Learning, LLMs, AI systems',
  },
]

export function ChatPage() {
  const [input, setInput] = useState('')
  const [modelType, setModelType] = useState<'local' | 'api'>('local')
  const [selectedModel, setSelectedModel] = useState(MODEL_OPTIONS.local[0])
  const [selectedExpert, setSelectedExpert] = useState(EXPERT_OPTIONS[0])
  const [showModelSelector, setShowModelSelector] = useState(false)
  const [showExpertSelector, setShowExpertSelector] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const { messages, clearMessages } = useChatStore()
  const {
    isStreaming,
    isLoading,
    sendMessage,
    stopStreaming,
  } = useChat({
    provider: selectedModel.provider,
    model: selectedModel.value,
    expert: selectedExpert.value,
  })

  // Cleanup: abort streaming when navigating away
  useEffect(() => {
    return () => {
      if (isStreaming) {
        stopStreaming()
      }
    }
  }, [isStreaming, stopStreaming])

  // Clear chat handler
  const handleClearChat = () => {
    if (messages.length > 0 && !isStreaming) {
      clearMessages()
    }
  }

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
        <div className="flex items-center gap-3">
          {/* Expert Selector */}
          <div className="relative">
            <button
              onClick={() => setShowExpertSelector(!showExpertSelector)}
              className="flex items-center gap-2 rounded-lg border border-secondary-700 bg-secondary-800/50 px-3 py-1.5 text-sm text-secondary-200 hover:bg-secondary-800 transition-colors"
            >
              <selectedExpert.icon className={cn('h-4 w-4', selectedExpert.color)} />
              <span>{selectedExpert.label}</span>
              <GraduationCap className="h-3.5 w-3.5 text-secondary-500" />
            </button>

            {showExpertSelector && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowExpertSelector(false)}
                />
                <div className="absolute right-0 top-full z-20 mt-2 w-72 rounded-xl border border-secondary-700 bg-secondary-800 p-2 shadow-xl">
                  <div className="mb-2 px-2 py-1 text-xs font-medium text-secondary-400 uppercase tracking-wide">
                    Select Expert Role
                  </div>
                  <div className="space-y-1">
                    {EXPERT_OPTIONS.map((expert) => {
                      const IconComponent = expert.icon
                      return (
                        <button
                          key={expert.value}
                          onClick={() => {
                            setSelectedExpert(expert)
                            setShowExpertSelector(false)
                          }}
                          className={cn(
                            'w-full flex items-start gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                            selectedExpert.value === expert.value
                              ? 'bg-primary-500/20'
                              : 'hover:bg-secondary-700'
                          )}
                        >
                          <IconComponent className={cn('h-5 w-5 mt-0.5 flex-shrink-0', expert.color)} />
                          <div className="text-left">
                            <div className={cn(
                              'font-medium',
                              selectedExpert.value === expert.value
                                ? 'text-primary-300'
                                : 'text-secondary-200'
                            )}>
                              {expert.label}
                            </div>
                            <div className="text-xs text-secondary-500">
                              {expert.description}
                            </div>
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Model Selector */}
          <div className="relative">
            <button
              onClick={() => setShowModelSelector(!showModelSelector)}
              className="flex items-center gap-2 rounded-lg border border-secondary-700 bg-secondary-800/50 px-3 py-1.5 text-sm text-secondary-200 hover:bg-secondary-800 transition-colors"
            >
              {modelType === 'local' ? (
                <Cpu className="h-4 w-4 text-green-400" />
              ) : (
                <Cloud className="h-4 w-4 text-blue-400" />
              )}
              <span>{selectedModel.label}</span>
              <Settings2 className="h-3.5 w-3.5 text-secondary-500" />
            </button>

            {showModelSelector && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowModelSelector(false)}
                />
                <div className="absolute right-0 top-full z-20 mt-2 w-64 rounded-xl border border-secondary-700 bg-secondary-800 p-2 shadow-xl">
                  {/* Type Toggle */}
                  <div className="flex gap-1 rounded-lg bg-secondary-900 p-1 mb-2">
                    <button
                      onClick={() => {
                        setModelType('local')
                        setSelectedModel(MODEL_OPTIONS.local[0])
                      }}
                      className={cn(
                        'flex-1 flex items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                        modelType === 'local'
                          ? 'bg-green-500/20 text-green-400'
                          : 'text-secondary-400 hover:text-white'
                      )}
                    >
                      <Cpu className="h-4 w-4" />
                      Local
                    </button>
                    <button
                      onClick={() => {
                        setModelType('api')
                        setSelectedModel(MODEL_OPTIONS.api[0])
                      }}
                      className={cn(
                        'flex-1 flex items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                        modelType === 'api'
                          ? 'bg-blue-500/20 text-blue-400'
                          : 'text-secondary-400 hover:text-white'
                      )}
                    >
                      <Cloud className="h-4 w-4" />
                      API
                    </button>
                  </div>

                  {/* Model Options */}
                  <div className="space-y-1">
                    {MODEL_OPTIONS[modelType].map((model) => (
                      <button
                        key={model.value}
                        onClick={() => {
                          setSelectedModel(model)
                          setShowModelSelector(false)
                        }}
                        className={cn(
                          'w-full flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors',
                          selectedModel.value === model.value
                            ? 'bg-primary-500/20 text-primary-300'
                            : 'text-secondary-300 hover:bg-secondary-700'
                        )}
                      >
                        <span>{model.label}</span>
                        <span className="text-xs text-secondary-500">{model.provider}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Clear Chat Button */}
          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              disabled={isStreaming}
              className="flex items-center gap-2 rounded-lg border border-secondary-700 bg-secondary-800/50 px-3 py-1.5 text-sm text-secondary-300 hover:bg-red-500/20 hover:border-red-500/50 hover:text-red-400 transition-colors disabled:opacity-50"
              title="Clear chat"
            >
              <Trash2 className="h-4 w-4" />
              Clear
            </button>
          )}

          {/* RAG Badge */}
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
// MESSAGE CONTENT COMPONENT
// =============================================================================

// Pre-process markdown to fix common LLM formatting issues
function preprocessMarkdown(text: string): string {
  let processed = text

  // Step 1: Fix numbered list items stuck together
  // Pattern: word1.word or word2.word -> word\n1. word (add newline before number)
  processed = processed.replace(/([ก-๙a-zA-Z\]\)\*])(\d{1,2})\.([ก-๙a-zA-Z_\*])/g, '$1\n$2. $3')

  // Also fix **number.** pattern
  processed = processed.replace(/\*\*(\d+)\.\*\*/g, '**\n$1. **')

  // Step 2: Fix bold with spaces - remove space after ** opening
  let boldFixed = processed
  do {
    processed = boldFixed
    boldFixed = processed.replace(/\*\*\s+([^\s*])/g, '**$1')
  } while (boldFixed !== processed)
  processed = boldFixed

  // Fix space before closing **: word ** -> word**
  processed = processed.replace(/(\S)\s+\*\*([^*]|$)/g, '$1**$2')

  // Step 2: Fix headers - add space after # and newlines before
  processed = processed.replace(/(?<=[^#\n]|^)(#{2,4})(?=[^\s#])/g, '\n\n$1 ')

  // Step 3: Add newline before bullet points (-**)
  // Pattern: any char (not newline) + optional spaces + -** -> char + newline + - **
  processed = processed.replace(/([^\n])\s*-\*\*/g, '$1\n- **')

  // Step 4: Add space after **bold**: patterns
  processed = processed.replace(/(\*\*[^*]+\*\*):(?=\S)/g, '$1: ')

  // Step 5: Add space after bold text followed by Thai/text (no punctuation)
  processed = processed.replace(/(\*\*[^*]+\*\*)(?=[\u0E00-\u0E7Fa-zA-Z])/g, '$1 ')

  // Step 6: Clean up multiple newlines
  processed = processed.replace(/\n{3,}/g, '\n\n')

  // Step 7: Clean up multiple spaces (but not in bold)
  processed = processed.replace(/([^*])  +([^*])/g, '$1 $2')

  return processed.trim()
}

// =============================================================================
// MESSAGE CONTENT COMPONENT with Streamdown
// =============================================================================

function MessageContent({ content, isUser }: { content: string; isUser: boolean }) {
  // User messages are always plain text
  if (isUser) {
    return <span className="whitespace-pre-wrap">{content}</span>
  }

  // Pre-process markdown for better formatting
  const processedContent = preprocessMarkdown(content)

  // Assistant messages use Streamdown for AI-optimized markdown rendering
  // Streamdown handles incomplete markdown during streaming and provides
  // beautiful syntax highlighting with Shiki
  return (
    <div className="markdown-content text-left break-words prose prose-invert prose-purple max-w-none">
      <Streamdown>{processedContent}</Streamdown>
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
            // Show loading while waiting for first content
            <div className="flex items-center gap-3">
              <Loader2 className="h-4 w-4 animate-spin text-purple-400" />
              <span className="text-purple-300">กำลังค้นหาข้อมูล...</span>
            </div>
          ) : (
            <MessageContent content={message.content} isUser={isUser} />
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
