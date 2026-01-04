/**
 * AI Answer Card Component
 * Displays structured LLM response with headers, bullets, and sources
 * Created with love by Angela & David - 4 January 2026
 */

import { useState } from 'react'
import { cn } from '@/lib/utils'
import {
  Sparkles,
  ChevronDown,
  ChevronUp,
  FileText,
  BookOpen,
  Loader2,
  Copy,
  Check,
} from 'lucide-react'
import type { SearchResult } from '@/types'

interface AIAnswerCardProps {
  query: string
  answer: string | null
  sources: SearchResult[]
  isLoading: boolean
  searchTime?: number | null
}

export function AIAnswerCard({
  query,
  answer,
  sources,
  isLoading,
  searchTime,
}: AIAnswerCardProps) {
  const [showAllSources, setShowAllSources] = useState(false)
  const [copied, setCopied] = useState(false)

  const displayedSources = showAllSources ? sources : sources.slice(0, 3)

  const handleCopy = async () => {
    if (answer) {
      await navigator.clipboard.writeText(answer)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="rounded-2xl border border-primary-500/30 bg-gradient-to-br from-primary-500/5 via-secondary-800/50 to-violet-500/5 overflow-hidden">
      {/* Header - Question */}
      <div className="px-6 py-4 border-b border-primary-500/20 bg-primary-500/5">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-violet-600">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-semibold text-white leading-tight">
              {query}
            </h2>
            {searchTime && (
              <p className="text-xs text-secondary-400 mt-1">
                Analyzed {sources.length} sources in {searchTime}ms
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Answer Section */}
      <div className="px-6 py-5">
        {isLoading ? (
          <div className="flex items-center gap-3 py-8">
            <Loader2 className="h-6 w-6 animate-spin text-primary-400" />
            <div>
              <p className="text-primary-300">Analyzing sources...</p>
              <p className="text-xs text-secondary-500 mt-0.5">
                AI is synthesizing information from your documents
              </p>
            </div>
          </div>
        ) : answer ? (
          <div className="space-y-4">
            {/* Answer Content - Rendered as structured markdown */}
            <div className="prose prose-invert prose-purple max-w-none">
              <div className="text-secondary-200 leading-relaxed whitespace-pre-wrap">
                {formatAnswer(answer)}
              </div>
            </div>

            {/* Copy Button */}
            <div className="flex justify-end pt-2">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-secondary-400 hover:text-primary-400 hover:bg-primary-500/10 rounded-lg transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    Copy answer
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <p className="text-secondary-400 py-4">
            Click "Ask AI" to get a summarized answer from your documents.
          </p>
        )}
      </div>

      {/* Sources Section */}
      {sources.length > 0 && (
        <div className="px-6 py-4 border-t border-primary-500/20 bg-secondary-900/30">
          <h3 className="text-sm font-medium text-secondary-300 mb-3 flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            Sources ({sources.length})
          </h3>

          <div className="space-y-2">
            {displayedSources.map((source, idx) => (
              <SourceItem key={source.chunk_id} source={source} index={idx + 1} />
            ))}
          </div>

          {sources.length > 3 && (
            <button
              onClick={() => setShowAllSources(!showAllSources)}
              className="mt-3 flex items-center gap-1 text-xs text-primary-400 hover:text-primary-300 transition-colors"
            >
              {showAllSources ? (
                <>
                  <ChevronUp className="h-3.5 w-3.5" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="h-3.5 w-3.5" />
                  Show {sources.length - 3} more sources
                </>
              )}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// Source Item Component
function SourceItem({ source, index }: { source: SearchResult; index: number }) {
  return (
    <div className="flex items-start gap-2 p-2 rounded-lg hover:bg-secondary-800/50 transition-colors group">
      <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-primary-500/20 text-[10px] font-bold text-primary-400">
        {index}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <FileText className="h-3.5 w-3.5 text-secondary-500" />
          <span className="text-xs font-medium text-secondary-200 truncate">
            {source.document_name}
          </span>
          {source.page_number && (
            <span className="text-[10px] text-secondary-500">
              p.{source.page_number}
            </span>
          )}
          <span
            className={cn(
              'text-[10px] px-1.5 py-0.5 rounded',
              source.similarity >= 0.7
                ? 'bg-green-500/20 text-green-400'
                : source.similarity >= 0.5
                ? 'bg-yellow-500/20 text-yellow-400'
                : 'bg-secondary-700 text-secondary-400'
            )}
          >
            {(source.similarity * 100).toFixed(0)}%
          </span>
        </div>
        <p className="text-xs text-secondary-500 mt-0.5 line-clamp-1 group-hover:line-clamp-2 transition-all">
          {source.content.substring(0, 150)}...
        </p>
      </div>
    </div>
  )
}

// Format answer with proper structure
function formatAnswer(answer: string): React.ReactNode {
  // Split by common section patterns
  const lines = answer.split('\n')
  const elements: React.ReactNode[] = []

  lines.forEach((line, idx) => {
    const trimmed = line.trim()

    // Skip empty lines but add spacing
    if (!trimmed) {
      elements.push(<div key={idx} className="h-2" />)
      return
    }

    // Headers (##, ###, or **Header:**)
    if (trimmed.startsWith('## ')) {
      elements.push(
        <h3 key={idx} className="text-lg font-semibold text-white mt-4 mb-2">
          {trimmed.replace('## ', '')}
        </h3>
      )
    } else if (trimmed.startsWith('### ')) {
      elements.push(
        <h4 key={idx} className="text-base font-medium text-primary-300 mt-3 mb-1">
          {trimmed.replace('### ', '')}
        </h4>
      )
    } else if (trimmed.match(/^\*\*[^*]+\*\*:?$/)) {
      // Bold header like **Header:** or **Header**
      const headerText = trimmed.replace(/\*\*/g, '').replace(/:$/, '')
      elements.push(
        <h4 key={idx} className="text-base font-medium text-primary-300 mt-3 mb-1">
          {headerText}
        </h4>
      )
    }
    // Bullet points
    else if (trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
      const bulletText = trimmed.replace(/^[-•]\s*/, '')
      elements.push(
        <div key={idx} className="flex items-start gap-2 ml-2 my-1">
          <span className="text-primary-400 mt-1">•</span>
          <span className="text-secondary-200">{formatInlineMarkdown(bulletText)}</span>
        </div>
      )
    }
    // Numbered items
    else if (trimmed.match(/^\d+\.\s/)) {
      const [num, ...rest] = trimmed.split(/\.\s/)
      elements.push(
        <div key={idx} className="flex items-start gap-2 ml-2 my-1">
          <span className="text-primary-400 font-medium min-w-[1.5rem]">{num}.</span>
          <span className="text-secondary-200">{formatInlineMarkdown(rest.join('. '))}</span>
        </div>
      )
    }
    // Regular paragraph
    else {
      elements.push(
        <p key={idx} className="text-secondary-200 my-1">
          {formatInlineMarkdown(trimmed)}
        </p>
      )
    }
  })

  return elements
}

// Format inline markdown (bold, italic)
function formatInlineMarkdown(text: string): React.ReactNode {
  // Simple bold replacement
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={idx} className="text-white font-medium">
          {part.slice(2, -2)}
        </strong>
      )
    }
    return part
  })
}
