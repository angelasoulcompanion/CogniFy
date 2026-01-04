/**
 * Search Config Panel Component
 * Composes all search configuration components
 * Created with love by Angela & David - 4 January 2026
 */

import { useSearchStore } from '@/hooks/useSearch'
import { SearchTypeSelector } from './SearchTypeSelector'
import { SimilaritySelector } from './SimilaritySelector'
import { ModelSelector } from './ModelSelector'
import { AdvancedSettings } from './AdvancedSettings'

export function SearchConfigPanel() {
  const { config } = useSearchStore()

  return (
    <div className="space-y-6">
      {/* Search Type - Most important */}
      <section>
        <h3 className="text-sm font-medium text-secondary-300 mb-3">
          Search Type
        </h3>
        <SearchTypeSelector />
      </section>

      {/* Similarity Method (only for Vector/Hybrid) */}
      {config.searchType !== 'bm25' && (
        <section>
          <h3 className="text-sm font-medium text-secondary-300 mb-3">
            Similarity Method
          </h3>
          <SimilaritySelector />
        </section>
      )}

      {/* Embedding Model */}
      <section>
        <h3 className="text-sm font-medium text-secondary-300 mb-3">
          Embedding Model
        </h3>
        <ModelSelector />
      </section>

      {/* Advanced Settings */}
      <AdvancedSettings />

      {/* Theory Info */}
      <section className="rounded-xl border border-secondary-700 bg-secondary-800/30 p-4">
        <h4 className="text-xs font-medium text-secondary-300 mb-2 uppercase tracking-wide">
          Quick Guide
        </h4>
        <div className="text-xs text-secondary-500 space-y-2">
          <p>
            <strong className="text-secondary-300">Semantic</strong>: Finds
            meaning-based matches. Best for conceptual queries.
          </p>
          <p>
            <strong className="text-secondary-300">Keyword</strong>: Exact word
            matching (BM25). Best for specific terms, IDs, names.
          </p>
          <p>
            <strong className="text-secondary-300">Hybrid</strong>: Combines both
            using RRF fusion. Recommended for most searches.
          </p>
        </div>
      </section>
    </div>
  )
}
