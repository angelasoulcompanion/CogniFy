/**
 * Embedding Model Selector Component
 * Select between bge-m3, mxbai-embed-large, and OpenAI embeddings
 * Created with love by Angela & David - 4 January 2026
 */

import { cn } from '@/lib/utils'
import { Cpu, Cloud, Check } from 'lucide-react'
import { useSearchStore } from '@/hooks/useSearch'
import type { EmbeddingModel } from '@/types'

interface ModelOption {
  value: EmbeddingModel
  label: string
  provider: 'ollama' | 'openai'
  dims: number
  context: string
  languages: string
  description: string
  recommended?: boolean
}

const EMBEDDING_MODELS: ModelOption[] = [
  {
    value: 'bge-m3',
    label: 'BGE-M3',
    provider: 'ollama',
    dims: 1024,
    context: '8192 tokens',
    languages: '100+ languages',
    description: 'Best multilingual model. Recommended for Thai/English.',
    recommended: true,
  },
  {
    value: 'mxbai-embed-large',
    label: 'MxBAI Large',
    provider: 'ollama',
    dims: 1024,
    context: '512 tokens',
    languages: 'English',
    description: 'Fallback model. Good for English-only content.',
  },
  {
    value: 'text-embedding-3-small',
    label: 'OpenAI Ada',
    provider: 'openai',
    dims: 1536,
    context: '8191 tokens',
    languages: '100+ languages',
    description: 'Cloud-based. Requires API key.',
  },
]

export function ModelSelector() {
  const { config, setConfig } = useSearchStore()

  return (
    <div className="space-y-2">
      {EMBEDDING_MODELS.map((model) => {
        const isSelected = config.embeddingModel === model.value
        const isLocal = model.provider === 'ollama'

        return (
          <button
            key={model.value}
            onClick={() => setConfig({ embeddingModel: model.value })}
            className={cn(
              'relative w-full flex items-start gap-3 rounded-xl p-3 border transition-all text-left',
              isSelected
                ? 'border-primary-500 bg-primary-500/10'
                : 'border-secondary-700 hover:border-primary-500/50 hover:bg-secondary-800/50'
            )}
          >
            {/* Provider Icon */}
            <div
              className={cn(
                'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg',
                isLocal ? 'bg-green-500/20' : 'bg-blue-500/20'
              )}
            >
              {isLocal ? (
                <Cpu className="h-5 w-5 text-green-400" />
              ) : (
                <Cloud className="h-5 w-5 text-blue-400" />
              )}
            </div>

            {/* Model Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    'font-medium',
                    isSelected ? 'text-primary-300' : 'text-white'
                  )}
                >
                  {model.label}
                </span>
                <span className="text-xs px-1.5 py-0.5 rounded bg-secondary-700 text-secondary-300">
                  {model.dims}d
                </span>
                {model.recommended && (
                  <span className="text-[10px] bg-primary-500 text-white px-1.5 py-0.5 rounded-full">
                    Recommended
                  </span>
                )}
              </div>
              <p className="text-xs text-secondary-400 mt-0.5">
                {model.description}
              </p>
              <div className="flex items-center gap-2 mt-1 text-xs text-secondary-500">
                <span>{model.context}</span>
                <span>•</span>
                <span>{model.languages}</span>
              </div>
            </div>

            {/* Selected Check */}
            {isSelected && (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary-500 text-white">
                <Check className="h-4 w-4" />
              </div>
            )}
          </button>
        )
      })}
    </div>
  )
}
