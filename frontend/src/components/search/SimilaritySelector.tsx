/**
 * Similarity Method Selector Component
 * Select between Cosine, Euclidean, and Dot Product similarity
 * Created with love by Angela & David - 4 January 2026
 */

import { useState } from 'react'
import { Info } from 'lucide-react'
import { useSearchStore } from '@/hooks/useSearch'
import type { SimilarityMethod } from '@/types'

interface SimilarityOption {
  value: SimilarityMethod
  label: string
  operator: string
  description: string
  bestFor: string
}

const SIMILARITY_METHODS: SimilarityOption[] = [
  {
    value: 'cosine',
    label: 'Cosine',
    operator: '<=>',
    description: 'Direction-based similarity (0-1 normalized)',
    bestFor: 'Most text similarity tasks (default)',
  },
  {
    value: 'euclidean',
    label: 'Euclidean',
    operator: '<->',
    description: 'L2 distance in vector space',
    bestFor: 'When absolute distance matters',
  },
  {
    value: 'dot',
    label: 'Dot Product',
    operator: '<#>',
    description: 'Direction + magnitude combined',
    bestFor: 'Ranking by relevance strength',
  },
]

export function SimilaritySelector() {
  const { config, setConfig } = useSearchStore()
  const [showTooltip, setShowTooltip] = useState(false)

  const selected = SIMILARITY_METHODS.find((m) => m.value === config.similarityMethod)

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 relative">
        <select
          value={config.similarityMethod}
          onChange={(e) => setConfig({ similarityMethod: e.target.value as SimilarityMethod })}
          className="w-full rounded-xl border border-secondary-700 bg-secondary-800/50 px-4 py-2.5 text-white appearance-none cursor-pointer hover:border-primary-500/50 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:outline-none transition-colors"
        >
          {SIMILARITY_METHODS.map((method) => (
            <option key={method.value} value={method.value}>
              {method.label} ({method.operator})
            </option>
          ))}
        </select>
        <button
          type="button"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-secondary-400 hover:bg-secondary-700 hover:text-white transition-colors"
        >
          <Info className="h-4 w-4" />
        </button>

        {/* Tooltip */}
        {showTooltip && (
          <div className="absolute left-0 top-full z-10 mt-2 w-full rounded-xl border border-secondary-700 bg-secondary-800 p-3 shadow-xl">
            <div className="text-xs text-secondary-300 space-y-2">
              <div>
                <strong className="text-white">Cosine</strong>: Best for text embeddings.
                Measures angle between vectors (normalized 0-1).
              </div>
              <div>
                <strong className="text-white">Euclidean</strong>: Actual distance in vector space.
                Good when magnitude matters.
              </div>
              <div>
                <strong className="text-white">Dot Product</strong>: Combines direction and magnitude.
                Good for ranking by relevance strength.
              </div>
            </div>
          </div>
        )}
      </div>

      {selected && (
        <p className="text-xs text-secondary-500 px-1">
          {selected.description}. {selected.bestFor}
        </p>
      )}
    </div>
  )
}
