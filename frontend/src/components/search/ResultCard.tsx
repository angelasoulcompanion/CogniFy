/**
 * Result Card Component
 * Displays a single search result with score, content, and actions
 * Created with love by Angela & David - 4 January 2026
 */

import { useState } from 'react'
import { cn } from '@/lib/utils'
import {
  FileText,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Hash,
  BookOpen,
} from 'lucide-react'
import type { SearchResult, SearchType } from '@/types'

interface ResultCardProps {
  result: SearchResult
  rank: number
  searchType: SearchType
  onFindSimilar?: (chunkId: string) => void
  isLoadingSimilar?: boolean
}

export function ResultCard({
  result,
  rank,
  searchType,
  onFindSimilar,
  isLoadingSimilar,
}: ResultCardProps) {
  const [expanded, setExpanded] = useState(false)

  // Score color based on value
  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'text-green-400 bg-green-500/20 border-green-500/30'
    if (score >= 0.5) return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30'
    return 'text-secondary-400 bg-secondary-700 border-secondary-600'
  }

  const scoreColor = getScoreColor(result.similarity)
  const scorePercent = (result.similarity * 100).toFixed(1)

  return (
    <div className="rounded-xl border border-secondary-700 bg-secondary-800/50 p-4 hover:border-primary-500/30 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          {/* Rank Badge */}
          <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-500/20 text-sm font-bold text-primary-400">
            {rank}
          </span>

          <div className="min-w-0">
            {/* Document Name */}
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-secondary-400 flex-shrink-0" />
              <h4 className="font-medium text-white truncate">
                {result.document_name}
              </h4>
            </div>

            {/* Meta Info */}
            <div className="flex items-center gap-2 mt-1 text-xs text-secondary-400">
              {result.page_number && (
                <span className="flex items-center gap-1">
                  <BookOpen className="h-3 w-3" />
                  Page {result.page_number}
                </span>
              )}
              {result.section_title && (
                <>
                  <span>•</span>
                  <span className="truncate max-w-[200px]">
                    {result.section_title}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Score Badge */}
        <div
          className={cn(
            'px-2.5 py-1 rounded-lg text-xs font-mono border flex-shrink-0',
            scoreColor
          )}
        >
          {scorePercent}%
        </div>
      </div>

      {/* Hybrid Rank Info */}
      {searchType === 'hybrid' && (result.vector_rank || result.bm25_rank) && (
        <div className="flex items-center gap-3 mt-3 text-xs">
          {result.vector_rank && (
            <span className="flex items-center gap-1 text-primary-400">
              <Hash className="h-3 w-3" />
              Vector: #{result.vector_rank}
            </span>
          )}
          {result.bm25_rank && (
            <span className="flex items-center gap-1 text-blue-400">
              <Hash className="h-3 w-3" />
              BM25: #{result.bm25_rank}
            </span>
          )}
          {result.rrf_score && (
            <span className="text-secondary-500">
              RRF: {result.rrf_score.toFixed(4)}
            </span>
          )}
        </div>
      )}

      {/* Content Preview */}
      <div className="mt-3">
        <p
          className={cn(
            'text-sm text-secondary-300 whitespace-pre-wrap leading-relaxed',
            !expanded && 'line-clamp-3'
          )}
        >
          {result.content}
        </p>

        {result.content.length > 200 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-2 flex items-center gap-1 text-xs text-primary-400 hover:text-primary-300 transition-colors"
          >
            {expanded ? (
              <>
                <ChevronUp className="h-3.5 w-3.5" />
                Show less
              </>
            ) : (
              <>
                <ChevronDown className="h-3.5 w-3.5" />
                Show more
              </>
            )}
          </button>
        )}
      </div>

      {/* Actions */}
      {onFindSimilar && (
        <div className="flex items-center justify-end gap-2 mt-3 pt-3 border-t border-secondary-700">
          <button
            onClick={() => onFindSimilar(result.chunk_id)}
            disabled={isLoadingSimilar}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-secondary-400 hover:text-primary-400 hover:bg-primary-500/10 rounded-lg transition-colors disabled:opacity-50"
          >
            <Sparkles className="h-3.5 w-3.5" />
            Find similar
          </button>
        </div>
      )}
    </div>
  )
}
