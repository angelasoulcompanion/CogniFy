/**
 * Advanced Settings Component
 * Threshold, max results, RRF-K, and hybrid weights
 * Created with love by Angela & David - 4 January 2026
 */

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown, RotateCcw } from 'lucide-react'
import { useSearchStore } from '@/hooks/useSearch'

const DEFAULT_CONFIG = {
  threshold: 0.3,
  maxResults: 10,
  bm25Weight: 0.4,
  vectorWeight: 0.6,
  rrfK: 60,
}

export function AdvancedSettings() {
  const [isOpen, setIsOpen] = useState(false)
  const { config, setConfig } = useSearchStore()

  const handleReset = () => {
    setConfig({
      threshold: DEFAULT_CONFIG.threshold,
      maxResults: DEFAULT_CONFIG.maxResults,
      bm25Weight: DEFAULT_CONFIG.bm25Weight,
      vectorWeight: DEFAULT_CONFIG.vectorWeight,
      rrfK: DEFAULT_CONFIG.rrfK,
    })
  }

  const isModified =
    config.threshold !== DEFAULT_CONFIG.threshold ||
    config.maxResults !== DEFAULT_CONFIG.maxResults ||
    config.bm25Weight !== DEFAULT_CONFIG.bm25Weight ||
    config.vectorWeight !== DEFAULT_CONFIG.vectorWeight ||
    config.rrfK !== DEFAULT_CONFIG.rrfK

  return (
    <div className="border border-secondary-700 rounded-xl overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-4 py-3 text-sm font-medium text-secondary-300 hover:bg-secondary-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span>Advanced Settings</span>
          {isModified && (
            <span className="h-2 w-2 rounded-full bg-primary-500"></span>
          )}
        </div>
        <ChevronDown
          className={cn('h-4 w-4 transition-transform', isOpen && 'rotate-180')}
        />
      </button>

      {/* Content */}
      {isOpen && (
        <div className="px-4 pb-4 space-y-5 border-t border-secondary-700 pt-4">
          {/* Threshold Slider */}
          <div>
            <label className="flex items-center justify-between text-xs text-secondary-400 mb-2">
              <span>Similarity Threshold</span>
              <span className="font-mono text-primary-400">
                {config.threshold.toFixed(2)}
              </span>
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={config.threshold}
              onChange={(e) => setConfig({ threshold: parseFloat(e.target.value) })}
              className="w-full h-2 bg-secondary-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
            />
            <div className="flex justify-between text-[10px] text-secondary-500 mt-1">
              <span>More results (lower quality)</span>
              <span>Higher quality</span>
            </div>
          </div>

          {/* Max Results Slider */}
          <div>
            <label className="flex items-center justify-between text-xs text-secondary-400 mb-2">
              <span>Max Results</span>
              <span className="font-mono text-primary-400">{config.maxResults}</span>
            </label>
            <input
              type="range"
              min="1"
              max="50"
              value={config.maxResults}
              onChange={(e) => setConfig({ maxResults: parseInt(e.target.value) })}
              className="w-full h-2 bg-secondary-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
            />
            <div className="flex justify-between text-[10px] text-secondary-500 mt-1">
              <span>1</span>
              <span>50</span>
            </div>
          </div>

          {/* Hybrid-specific settings */}
          {config.searchType === 'hybrid' && (
            <>
              {/* Weight Slider */}
              <div>
                <label className="text-xs text-secondary-400 mb-2 block">
                  Search Weights
                </label>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-blue-400 font-medium w-12">
                    BM25
                  </span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={config.vectorWeight}
                    onChange={(e) => {
                      const vw = parseFloat(e.target.value)
                      setConfig({ vectorWeight: vw, bm25Weight: 1 - vw })
                    }}
                    className="flex-1 h-2 bg-secondary-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
                  />
                  <span className="text-xs text-primary-400 font-medium w-12 text-right">
                    Vector
                  </span>
                </div>
                <div className="text-center text-xs text-secondary-400 mt-2">
                  <span className="text-blue-400">
                    {Math.round(config.bm25Weight * 100)}%
                  </span>
                  <span className="text-secondary-500 mx-2">/</span>
                  <span className="text-primary-400">
                    {Math.round(config.vectorWeight * 100)}%
                  </span>
                </div>
              </div>

              {/* RRF K Constant */}
              <div>
                <label className="flex items-center justify-between text-xs text-secondary-400 mb-2">
                  <span>RRF K Constant</span>
                  <span className="font-mono text-primary-400">{config.rrfK}</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={config.rrfK}
                  onChange={(e) => setConfig({ rrfK: parseInt(e.target.value) })}
                  className="w-full h-2 bg-secondary-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
                />
                <p className="text-[10px] text-secondary-500 mt-1">
                  Higher values give more emphasis to top-ranked results
                </p>
              </div>
            </>
          )}

          {/* Reset Button */}
          {isModified && (
            <button
              onClick={handleReset}
              className="flex items-center justify-center gap-2 w-full py-2 rounded-lg border border-secondary-700 text-sm text-secondary-400 hover:bg-secondary-800 hover:text-white transition-colors"
            >
              <RotateCcw className="h-4 w-4" />
              Reset to defaults
            </button>
          )}
        </div>
      )}
    </div>
  )
}
