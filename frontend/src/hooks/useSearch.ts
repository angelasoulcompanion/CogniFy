/**
 * useSearch Hook
 * React Query + Zustand for search state management
 * Created with love by Angela & David - 4 January 2026
 */

import { useMutation, useQuery } from '@tanstack/react-query'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { searchApi } from '@/services/api'
import type {
  SearchConfig,
  SearchResult,
  SearchResponse,
  SearchStats,
} from '@/types'

// =============================================================================
// DEFAULT CONFIG
// =============================================================================

const DEFAULT_CONFIG: SearchConfig = {
  embeddingModel: 'bge-m3',
  searchType: 'hybrid',
  similarityMethod: 'cosine',
  threshold: 0.3,
  maxResults: 10,
  bm25Weight: 0.4,
  vectorWeight: 0.6,
  rrfK: 60,
  documentIds: null,
  includeContent: true,
}

// =============================================================================
// ZUSTAND STORE
// =============================================================================

interface SearchStoreState {
  // Query
  query: string
  recentQueries: string[]

  // Configuration
  config: SearchConfig

  // Results
  results: SearchResult[]
  isLoading: boolean
  error: string | null
  searchTime: number | null
  searchMethod: string | null

  // Actions
  setQuery: (query: string) => void
  setConfig: (config: Partial<SearchConfig>) => void
  setResults: (results: SearchResult[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setSearchTime: (time: number | null) => void
  setSearchMethod: (method: string | null) => void
  clearResults: () => void
  addRecentQuery: (query: string) => void
  resetConfig: () => void
}

export const useSearchStore = create<SearchStoreState>()(
  persist(
    (set) => ({
      // Initial state
      query: '',
      recentQueries: [],
      config: DEFAULT_CONFIG,
      results: [],
      isLoading: false,
      error: null,
      searchTime: null,
      searchMethod: null,

      // Actions
      setQuery: (query) => set({ query }),

      setConfig: (updates) =>
        set((state) => ({
          config: { ...state.config, ...updates },
        })),

      setResults: (results) => set({ results }),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      setSearchTime: (searchTime) => set({ searchTime }),

      setSearchMethod: (searchMethod) => set({ searchMethod }),

      clearResults: () =>
        set({
          results: [],
          error: null,
          searchTime: null,
          searchMethod: null,
        }),

      addRecentQuery: (query) =>
        set((state) => ({
          recentQueries: [
            query,
            ...state.recentQueries.filter((q) => q !== query),
          ].slice(0, 10),
        })),

      resetConfig: () => set({ config: DEFAULT_CONFIG }),
    }),
    {
      name: 'cognify-search',
      partialize: (state) => ({
        config: state.config,
        recentQueries: state.recentQueries,
      }),
    }
  )
)

// =============================================================================
// SEARCH HOOK
// =============================================================================

export function useSearch() {
  const {
    query,
    config,
    setResults,
    setLoading,
    setError,
    setSearchTime,
    setSearchMethod,
    addRecentQuery,
  } = useSearchStore()

  const searchMutation = useMutation({
    mutationFn: async () => {
      if (!query.trim()) return null

      let response: SearchResponse

      switch (config.searchType) {
        case 'vector':
          response = await searchApi.semanticAdvanced({
            query,
            limit: config.maxResults,
            threshold: config.threshold,
            similarityMethod: config.similarityMethod,
            documentIds: config.documentIds ?? undefined,
            includeContent: config.includeContent,
          })
          break

        case 'bm25':
          response = await searchApi.bm25(query, {
            limit: config.maxResults,
            documentIds: config.documentIds ?? undefined,
          })
          break

        case 'hybrid':
        default:
          response = await searchApi.hybridAdvanced({
            query,
            limit: config.maxResults,
            threshold: config.threshold,
            bm25Weight: config.bm25Weight,
            vectorWeight: config.vectorWeight,
            rrfK: config.rrfK,
            documentIds: config.documentIds ?? undefined,
          })
      }

      return response
    },
    onMutate: () => {
      setLoading(true)
      setError(null)
    },
    onSuccess: (data) => {
      if (data) {
        setResults(data.results)
        setSearchTime(data.search_time_ms)
        setSearchMethod(data.search_method)
        addRecentQuery(query)
      }
      setLoading(false)
    },
    onError: (error: Error) => {
      setError(error.message)
      setLoading(false)
    },
  })

  const findSimilarMutation = useMutation({
    mutationFn: (chunkId: string) =>
      searchApi.findSimilar(chunkId, config.maxResults),
    onSuccess: (data) => {
      if (data) {
        setResults(data.results)
        setSearchTime(data.search_time_ms)
        setSearchMethod('similar')
      }
    },
  })

  return {
    // State (from store for reactivity)
    query: useSearchStore((s) => s.query),
    config: useSearchStore((s) => s.config),
    results: useSearchStore((s) => s.results),
    isLoading: useSearchStore((s) => s.isLoading),
    error: useSearchStore((s) => s.error),
    searchTime: useSearchStore((s) => s.searchTime),
    searchMethod: useSearchStore((s) => s.searchMethod),

    // Actions
    search: searchMutation.mutate,
    findSimilar: findSimilarMutation.mutate,
    isLoadingSimilar: findSimilarMutation.isPending,
  }
}

// =============================================================================
// SEARCH STATS HOOK
// =============================================================================

export function useSearchStats() {
  return useQuery<SearchStats>({
    queryKey: ['searchStats'],
    queryFn: searchApi.getStats,
    staleTime: 60000, // 1 minute
    refetchOnWindowFocus: false,
  })
}

// =============================================================================
// ASK AI HOOK (LLM summarization)
// =============================================================================

interface AskAIState {
  answer: string | null
  isAskingAI: boolean
  aiError: string | null
  setAnswer: (answer: string | null) => void
  setAskingAI: (loading: boolean) => void
  setAIError: (error: string | null) => void
  clearAIAnswer: () => void
}

export const useAskAIStore = create<AskAIState>()((set) => ({
  answer: null,
  isAskingAI: false,
  aiError: null,
  setAnswer: (answer) => set({ answer }),
  setAskingAI: (isAskingAI) => set({ isAskingAI }),
  setAIError: (aiError) => set({ aiError }),
  clearAIAnswer: () => set({ answer: null, aiError: null }),
}))

// Expert system prompts
const EXPERT_PROMPTS: Record<string, string> = {
  general: 'คุณเป็นผู้ช่วย AI ทั่วไปที่ตอบคำถามจากเอกสาร',
  financial_analyst: 'คุณเป็นนักวิเคราะห์การเงินผู้เชี่ยวชาญ ตอบคำถามเกี่ยวกับการเงิน งบการเงิน และการวิเคราะห์ธุรกิจ',
  legal_expert: 'คุณเป็นผู้เชี่ยวชาญด้านกฎหมาย ตอบคำถามเกี่ยวกับสัญญา กฎระเบียบ และการปฏิบัติตามกฎหมาย',
  technical_writer: 'คุณเป็นนักเขียนเทคนิคผู้เชี่ยวชาญ ตอบคำถามเกี่ยวกับเอกสารทางเทคนิค และ specifications',
  data_analyst: 'คุณเป็นนักวิเคราะห์ข้อมูลผู้เชี่ยวชาญ ตอบคำถามเกี่ยวกับข้อมูล สถิติ และ patterns',
  business_consultant: 'คุณเป็นที่ปรึกษาธุรกิจผู้เชี่ยวชาญ ตอบคำถามเกี่ยวกับกลยุทธ์ การดำเนินงาน และการบริหาร',
  researcher: 'คุณเป็นนักวิจัยผู้เชี่ยวชาญ ตอบคำถามอย่างเป็นวิชาการ พร้อมอ้างอิงข้อมูลจากเอกสาร',
  ai_engineer: 'คุณเป็นวิศวกร AI ผู้เชี่ยวชาญ ตอบคำถามเกี่ยวกับ Machine Learning, Deep Learning, LLMs และระบบ AI',
}

export interface AskAIParams {
  provider: string
  model: string
  expert: string
}

export function useAskAI() {
  const { setAnswer, setAskingAI, setAIError } = useAskAIStore()
  const { query, results } = useSearchStore()

  const askAIMutation = useMutation({
    mutationFn: async (params: AskAIParams) => {
      const { provider, model, expert } = params

      if (!query.trim() || results.length === 0) return null

      // Build context from search results
      const context = results
        .slice(0, 5) // Top 5 results
        .map((r, i) => `[${i + 1}] ${r.document_name}${r.page_number ? ` (p.${r.page_number})` : ''}:\n${r.content}`)
        .join('\n\n')

      // Get expert-specific intro
      const expertIntro = EXPERT_PROMPTS[expert] || EXPERT_PROMPTS.general

      // Create structured prompt with expert role
      const systemPrompt = `${expertIntro}

## กฎสำคัญ (CRITICAL RULES):
- ตอบจาก "ข้อมูลจากเอกสาร" ที่ให้มาด้านล่าง **เท่านั้น**
- **ห้าม** ใช้ความรู้ภายนอกหรือ training data ของคุณ
- **ห้าม** สมมติหรือเดาข้อมูลที่ไม่มีในเอกสาร
- **ห้าม** ตอบซ้ำหรือพูดเรื่องเดิมหลายครั้ง
- ถ้าไม่พบข้อมูลในเอกสาร ให้ตอบว่า "ไม่พบข้อมูลในเอกสารที่ให้"

## รูปแบบการตอบ:
ตอบเป็นย่อหน้า 2-3 ย่อหน้า แต่ละย่อหน้าพูดเรื่องต่างกัน อ้างอิง source [1], [2] ท้ายประโยค

## สรุป
สรุปสั้นๆ 1-2 ประโยค`

      const userMessage = `คำถาม: ${query}

ข้อมูลจากเอกสาร:
${context}

กรุณาตอบคำถามโดยใช้ข้อมูลข้างต้น จัดรูปแบบเป็นหัวข้อและ bullet points`

      console.log('[Ask AI] Using model:', model, 'provider:', provider, 'expert:', expert)

      // Call AI API (simple completion without conversation)
      const response = await fetch('/api/v1/ai/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${sessionStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          message: userMessage,
          system_prompt: systemPrompt,
          provider: provider,
          model: model,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to get AI answer')
      }

      const data = await response.json()
      return data.content || data.message || 'No response'
    },
    onMutate: () => {
      setAskingAI(true)
      setAIError(null)
    },
    onSuccess: (data) => {
      if (data) {
        setAnswer(data)
      }
      setAskingAI(false)
    },
    onError: (error: Error) => {
      setAIError(error.message)
      setAskingAI(false)
    },
  })

  return {
    answer: useAskAIStore((s) => s.answer),
    isAskingAI: useAskAIStore((s) => s.isAskingAI),
    aiError: useAskAIStore((s) => s.aiError),
    askAI: askAIMutation.mutate,
    clearAIAnswer: useAskAIStore((s) => s.clearAIAnswer),
  }
}
