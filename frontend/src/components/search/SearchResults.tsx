/**
 * Search Results Component
 * Container for displaying search results with empty/loading states
 * Created with love by Angela & David - 4 January 2026
 */

import { Search, FileSearch, Loader2 } from 'lucide-react'
import { useSearchStore, useSearch } from '@/hooks/useSearch'
import { ResultCard } from './ResultCard'

export function SearchResults() {
  const { results, isLoading, config, query } = useSearchStore()
  const { findSimilar, isLoadingSimilar } = useSearch()

  // Loading state
  if (isLoading) {
    return (
      <div className="mt-8 flex flex-col items-center justify-center py-12">
        <div className="flex items-center gap-3 text-primary-400">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="text-lg">Searching...</span>
        </div>
        <p className="mt-2 text-sm text-secondary-500">
          {config.searchType === 'hybrid'
            ? 'Combining vector and keyword search...'
            : config.searchType === 'vector'
            ? 'Finding semantically similar content...'
            : 'Matching keywords...'}
        </p>
      </div>
    )
  }

  // Empty state - no query yet
  if (!query.trim() && results.length === 0) {
    return (
      <div className="mt-8 flex flex-col items-center justify-center py-12">
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500/20 to-violet-500/20">
          <Search className="h-10 w-10 text-primary-400" />
        </div>
        <h3 className="mt-4 text-lg font-medium text-white">
          Search your documents
        </h3>
        <p className="mt-2 text-sm text-secondary-400 text-center max-w-sm">
          Enter a query to search through your knowledge base using{' '}
          <span className="text-primary-400">
            {config.searchType === 'hybrid'
              ? 'hybrid (semantic + keyword)'
              : config.searchType === 'vector'
              ? 'semantic'
              : 'keyword'}{' '}
            search
          </span>
        </p>

        {/* Quick tips */}
        <div className="mt-6 grid gap-2 text-xs text-secondary-500">
          <div className="flex items-center gap-2">
            <span className="text-primary-400">Semantic:</span>
            <span>"Find documents about financial planning"</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-blue-400">Keyword:</span>
            <span>"invoice INV-2024-001"</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-green-400">Hybrid:</span>
            <span>"quarterly report revenue growth"</span>
          </div>
        </div>
      </div>
    )
  }

  // Empty state - no results
  if (query.trim() && results.length === 0) {
    return (
      <div className="mt-8 flex flex-col items-center justify-center py-12">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary-700">
          <FileSearch className="h-8 w-8 text-secondary-400" />
        </div>
        <h3 className="mt-4 text-lg font-medium text-white">No results found</h3>
        <p className="mt-2 text-sm text-secondary-400 text-center max-w-sm">
          No documents matched your query "{query}". Try:
        </p>
        <ul className="mt-3 text-sm text-secondary-500 space-y-1">
          <li>• Using different keywords</li>
          <li>• Lowering the similarity threshold</li>
          <li>• Trying a different search type</li>
        </ul>
      </div>
    )
  }

  // Results list
  return (
    <div className="mt-6 space-y-4">
      {results.map((result, index) => (
        <ResultCard
          key={result.chunk_id}
          result={result}
          rank={index + 1}
          searchType={config.searchType}
          onFindSimilar={findSimilar}
          isLoadingSimilar={isLoadingSimilar}
        />
      ))}
    </div>
  )
}
