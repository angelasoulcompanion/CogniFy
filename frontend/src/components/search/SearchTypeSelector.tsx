/**
 * Search Type Selector Component
 * Select between Semantic, Keyword, and Hybrid search
 * Created with love by Angela & David - 4 January 2026
 */

import { cn } from '@/lib/utils'
import { Brain, Type, Sparkles, type LucideIcon } from 'lucide-react'
import { useSearchStore, useSearch } from '@/hooks/useSearch'
import type { SearchType } from '@/types'

interface SearchTypeOption {
  value: SearchType
  label: string
  icon: LucideIcon
  description: string
  example: string
  recommended?: boolean
}

const SEARCH_TYPES: SearchTypeOption[] = [
  {
    value: 'vector',
    label: 'Semantic',
    icon: Brain,
    description: 'Find by meaning, not keywords',
    example: '"financial planning" finds "investment strategy"',
  },
  {
    value: 'bm25',
    label: 'Keyword',
    icon: Type,
    description: 'Exact word matching',
    example: '"invoice 2024" finds exact phrase',
  },
  {
    value: 'hybrid',
    label: 'Hybrid',
    icon: Sparkles,
    description: 'Best of both with RRF fusion',
    example: 'Recommended for most searches',
    recommended: true,
  },
]

export function SearchTypeSelector() {
  const { config, setConfig, query } = useSearchStore()
  const { search } = useSearch()

  const handleSelect = (value: SearchType) => {
    if (config.searchType === value) return // Already selected
    setConfig({ searchType: value })
    // Auto re-search if there's a query
    if (query.trim()) {
      setTimeout(() => search(), 50) // Small delay to ensure config is updated
    }
  }

  return (
    <div className="space-y-2">
      {SEARCH_TYPES.map((type) => {
        const Icon = type.icon
        const isSelected = config.searchType === type.value

        return (
          <button
            key={type.value}
            onClick={() => handleSelect(type.value)}
            className={cn(
              'relative w-full flex items-start gap-3 rounded-xl p-3 border transition-all text-left',
              isSelected
                ? 'border-primary-500 bg-primary-500/10'
                : 'border-secondary-700 hover:border-primary-500/50 hover:bg-secondary-800/50'
            )}
          >
            {type.recommended && (
              <span className="absolute -top-2 -right-2 text-[10px] bg-primary-500 text-white px-1.5 py-0.5 rounded-full">
                Recommended
              </span>
            )}
            <div
              className={cn(
                'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg',
                isSelected ? 'bg-primary-500/20' : 'bg-secondary-700'
              )}
            >
              <Icon
                className={cn(
                  'h-5 w-5',
                  isSelected ? 'text-primary-400' : 'text-secondary-400'
                )}
              />
            </div>
            <div className="flex-1 min-w-0">
              <div
                className={cn(
                  'font-medium',
                  isSelected ? 'text-primary-300' : 'text-white'
                )}
              >
                {type.label}
              </div>
              <p className="text-xs text-secondary-400 mt-0.5">
                {type.description}
              </p>
              <p className="text-xs text-secondary-500 mt-1 italic">
                {type.example}
              </p>
            </div>
          </button>
        )
      })}
    </div>
  )
}
