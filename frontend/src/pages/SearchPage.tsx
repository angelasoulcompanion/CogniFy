/**
 * CogniFy Search Page
 * RAG Search interface with model, similarity, and search type selection
 * Created with love by Angela & David - 4 January 2026
 */

import { useState, FormEvent } from 'react'
import { cn } from '@/lib/utils'
import {
  Search,
  Settings2,
  Brain,
  Type,
  Sparkles,
  Loader2,
  FileText,
  Clock,
  X,
  Wand2,
  Cpu,
  Cloud,
  Bot,
  LineChart,
  Scale,
  FileCode,
  BrainCircuit,
  Briefcase,
  GraduationCap,
  type LucideIcon,
} from 'lucide-react'
import { useSearchStore, useSearch, useSearchStats, useAskAI } from '@/hooks/useSearch'

// Model options for Ask AI
const MODEL_OPTIONS = {
  local: [
    { value: 'qwen2.5:7b', label: 'Qwen 2.5 (7B)', provider: 'ollama' },
    { value: 'qwen2.5:14b', label: 'Qwen 2.5 (14B)', provider: 'ollama' },
    { value: 'supachai/llama-3-typhoon-v1.5:latest', label: 'Typhoon 1.5 (8B)', provider: 'ollama' },
    { value: 'llama3.1:8b', label: 'Llama 3.1 (8B)', provider: 'ollama' },
  ],
  api: [
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini', provider: 'openai' },
    { value: 'gpt-4o', label: 'GPT-4o', provider: 'openai' },
  ],
}

// Expert options for role-based prompting
interface ExpertOption {
  value: string
  label: string
  icon: LucideIcon
  color: string
  description: string
}

const EXPERT_OPTIONS: ExpertOption[] = [
  {
    value: 'general',
    label: 'General Assistant',
    icon: Bot,
    color: 'text-primary-400',
    description: 'All-purpose helpful assistant',
  },
  {
    value: 'financial_analyst',
    label: 'Financial Analyst',
    icon: LineChart,
    color: 'text-green-400',
    description: 'Financial data, reports, and analysis',
  },
  {
    value: 'legal_expert',
    label: 'Legal Expert',
    icon: Scale,
    color: 'text-yellow-400',
    description: 'Contracts, legal documents, compliance',
  },
  {
    value: 'technical_writer',
    label: 'Technical Writer',
    icon: FileCode,
    color: 'text-blue-400',
    description: 'Documentation, specs, technical content',
  },
  {
    value: 'data_analyst',
    label: 'Data Analyst',
    icon: BrainCircuit,
    color: 'text-cyan-400',
    description: 'Data patterns, statistics, insights',
  },
  {
    value: 'business_consultant',
    label: 'Business Consultant',
    icon: Briefcase,
    color: 'text-orange-400',
    description: 'Strategy, operations, management',
  },
  {
    value: 'researcher',
    label: 'Researcher',
    icon: GraduationCap,
    color: 'text-purple-400',
    description: 'Academic research, literature review',
  },
  {
    value: 'ai_engineer',
    label: 'AI Engineer',
    icon: Cpu,
    color: 'text-pink-400',
    description: 'ML, Deep Learning, LLMs, AI systems',
  },
]
import {
  SearchConfigPanel,
  SearchResults,
  AIAnswerCard,
} from '@/components/search'

export function SearchPage() {
  const [configOpen, setConfigOpen] = useState(true)
  const [showRecentQueries, setShowRecentQueries] = useState(false)

  // Ask AI model/expert state
  const [modelType, setModelType] = useState<'local' | 'api'>('local')
  const [selectedModel, setSelectedModel] = useState(MODEL_OPTIONS.local[0])
  const [selectedExpert, setSelectedExpert] = useState(EXPERT_OPTIONS[0])
  const [showModelSelector, setShowModelSelector] = useState(false)
  const [showExpertSelector, setShowExpertSelector] = useState(false)

  const { query, setQuery, recentQueries, clearResults, config } = useSearchStore()
  const { search, isLoading, results, searchTime, error } = useSearch()
  const { data: stats } = useSearchStats()
  const { answer, isAskingAI, aiError, askAI, clearAIAnswer } = useAskAI()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isLoading) return
    clearAIAnswer() // Clear previous AI answer
    search()
  }

  const handleAskAI = () => {
    if (results.length === 0 || isAskingAI) return
    // Pass current model/expert selection to askAI
    askAI({
      provider: selectedModel.provider,
      model: selectedModel.value,
      expert: selectedExpert.value,
    })
  }

  const handleRecentQueryClick = (q: string) => {
    setQuery(q)
    setShowRecentQueries(false)
    clearAIAnswer()
    // Auto search after selecting
    setTimeout(() => search(), 100)
  }

  // Get search type label
  const getSearchTypeLabel = () => {
    switch (config.searchType) {
      case 'vector': return 'Semantic'
      case 'bm25': return 'Keyword'
      case 'hybrid': return 'Hybrid'
    }
  }

  const getSearchTypeIcon = () => {
    switch (config.searchType) {
      case 'vector': return Brain
      case 'bm25': return Type
      case 'hybrid': return Sparkles
    }
  }

  const SearchTypeIcon = getSearchTypeIcon()

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <header className="flex h-16 items-center justify-between border-b border-primary-500/10 bg-secondary-900/50 backdrop-blur-sm px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-500/20">
            <Search className="h-6 w-6 text-primary-400" />
          </div>
          <div>
            <h1 className="font-semibold text-white">RAG Search</h1>
            <p className="text-sm text-secondary-400">Search your knowledge base</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Search Type Badge */}
          <span className="inline-flex items-center gap-1.5 rounded-full bg-primary-500/20 px-3 py-1 text-sm text-primary-400">
            <SearchTypeIcon className="h-4 w-4" />
            {getSearchTypeLabel()}
          </span>

          {/* Stats Badge */}
          {stats && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-secondary-700 px-3 py-1 text-sm text-secondary-300">
              <FileText className="h-4 w-4" />
              {stats.chunks?.total?.toLocaleString() || 0} chunks
            </span>
          )}

          {/* Config Toggle */}
          <button
            onClick={() => setConfigOpen(!configOpen)}
            className={cn(
              'flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm transition-colors',
              configOpen
                ? 'border-primary-500 bg-primary-500/20 text-primary-300'
                : 'border-secondary-700 bg-secondary-800/50 text-secondary-200 hover:bg-secondary-800'
            )}
          >
            <Settings2 className="h-4 w-4" />
            Config
          </button>
        </div>
      </header>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Main Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Search Input */}
          <div className="mx-auto max-w-3xl">
            <form onSubmit={handleSubmit} className="relative">
              <div className="relative flex items-center gap-2 rounded-2xl border border-secondary-700 bg-secondary-800/50 p-2 focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/20">
                <div className="flex h-10 w-10 items-center justify-center">
                  <Search className="h-5 w-5 text-secondary-500" />
                </div>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onFocus={() => recentQueries.length > 0 && setShowRecentQueries(true)}
                  placeholder="Search your documents..."
                  className="flex-1 bg-transparent px-2 py-2 text-white placeholder-secondary-500 focus:outline-none"
                  disabled={isLoading}
                />
                {query && (
                  <button
                    type="button"
                    onClick={() => {
                      setQuery('')
                      clearResults()
                      clearAIAnswer()
                    }}
                    className="flex h-8 w-8 items-center justify-center rounded-lg text-secondary-500 hover:bg-secondary-700 hover:text-white transition-colors"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
                <button
                  type="submit"
                  disabled={!query.trim() || isLoading}
                  className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-primary-600 to-violet-600 text-white transition-colors hover:from-primary-500 hover:to-violet-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Search className="h-5 w-5" />
                  )}
                </button>
              </div>

              {/* Recent Queries Dropdown */}
              {showRecentQueries && recentQueries.length > 0 && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowRecentQueries(false)}
                  />
                  <div className="absolute left-0 right-0 top-full z-20 mt-2 rounded-xl border border-secondary-700 bg-secondary-800 p-2 shadow-xl">
                    <div className="mb-2 px-2 py-1 text-xs font-medium text-secondary-400 uppercase tracking-wide flex items-center gap-2">
                      <Clock className="h-3 w-3" />
                      Recent Searches
                    </div>
                    <div className="space-y-1">
                      {recentQueries.map((q, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleRecentQueryClick(q)}
                          className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-secondary-300 hover:bg-secondary-700 transition-colors text-left"
                        >
                          <Search className="h-4 w-4 text-secondary-500" />
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </form>

            {/* Results Info + Ask AI Controls */}
            {results.length > 0 && (
              <div className="mt-4 space-y-3">
                {/* Results Info */}
                <div className="flex items-center gap-2 text-sm text-secondary-400">
                  <span>Found <strong className="text-white">{results.length}</strong> results</span>
                  {searchTime && (
                    <>
                      <span>•</span>
                      <span>{searchTime}ms</span>
                    </>
                  )}
                  <span>•</span>
                  <span className="inline-flex items-center gap-1">
                    <SearchTypeIcon className="h-3.5 w-3.5" />
                    {getSearchTypeLabel()} search
                  </span>
                </div>

                {/* Ask AI Controls Row */}
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-2">
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
                          <div className="absolute left-0 top-full z-20 mt-2 w-72 rounded-xl border border-secondary-700 bg-secondary-800 p-2 shadow-xl">
                            <div className="mb-2 px-2 py-1 text-xs font-medium text-secondary-400 uppercase tracking-wide">
                              Select Expert Role
                            </div>
                            <div className="space-y-1 max-h-64 overflow-y-auto">
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
                          <div className="absolute left-0 top-full z-20 mt-2 w-64 rounded-xl border border-secondary-700 bg-secondary-800 p-2 shadow-xl">
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
                  </div>

                  {/* Ask AI Button */}
                  <button
                    onClick={handleAskAI}
                    disabled={isAskingAI || results.length === 0}
                    className={cn(
                      'flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-all',
                      answer
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                        : 'bg-gradient-to-r from-primary-600 to-violet-600 text-white hover:from-primary-500 hover:to-violet-500 shadow-lg shadow-primary-500/25',
                      isAskingAI && 'opacity-70 cursor-wait'
                    )}
                  >
                    {isAskingAI ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : answer ? (
                      <>
                        <Sparkles className="h-4 w-4" />
                        AI Answered
                      </>
                    ) : (
                      <>
                        <Wand2 className="h-4 w-4" />
                        Ask AI
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="mt-4 rounded-xl border border-red-500/50 bg-red-500/10 p-4 text-red-400">
                {error}
              </div>
            )}

            {/* AI Error */}
            {aiError && (
              <div className="mt-4 rounded-xl border border-red-500/50 bg-red-500/10 p-4 text-red-400">
                AI Error: {aiError}
              </div>
            )}

            {/* AI Answer Card (shown above results when available) */}
            {(answer || isAskingAI) && results.length > 0 && (
              <div className="mt-6">
                <AIAnswerCard
                  query={query}
                  answer={answer}
                  sources={results.slice(0, 5)}
                  isLoading={isAskingAI}
                  searchTime={searchTime}
                />
              </div>
            )}

            {/* Raw Search Results */}
            {!answer && !isAskingAI && <SearchResults />}

            {/* Show results below AI answer */}
            {answer && (
              <div className="mt-8">
                <h3 className="text-sm font-medium text-secondary-400 mb-4 flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  All Search Results ({results.length})
                </h3>
                <SearchResults />
              </div>
            )}
          </div>
        </div>

        {/* Config Sidebar */}
        {configOpen && (
          <aside className="w-80 border-l border-primary-500/10 bg-secondary-900/30 overflow-y-auto">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-white">Search Settings</h2>
                <button
                  onClick={() => setConfigOpen(false)}
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-secondary-400 hover:bg-secondary-700 hover:text-white transition-colors lg:hidden"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <SearchConfigPanel />
            </div>
          </aside>
        )}
      </div>
    </div>
  )
}
