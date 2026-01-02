/**
 * CogniFy Prompt Types
 * TypeScript types for prompt management
 * Created with love by Angela & David - 2 January 2026
 */

// =============================================================================
// ENUMS
// =============================================================================

export type PromptCategory = 'rag' | 'system' | 'summarization' | 'analysis' | 'custom'

export type ExpertRole = 'general' | 'financial' | 'legal' | 'technical' | 'data' | 'business' | 'researcher'

// =============================================================================
// ENTITIES
// =============================================================================

export interface PromptVariable {
  name: string
  required: boolean
  description: string
}

export interface PromptTemplate {
  template_id: string
  name: string
  description: string | null
  category: PromptCategory
  expert_role: ExpertRole | null
  template_content: string
  variables: PromptVariable[]
  example_input: Record<string, unknown>
  example_output: string | null
  language: string
  is_default: boolean
  is_active: boolean
  usage_count: number
  version: number
  created_at: string
  updated_at: string
}

// =============================================================================
// API REQUESTS
// =============================================================================

export interface CreatePromptRequest {
  name: string
  template_content: string
  category: PromptCategory
  description?: string
  expert_role?: ExpertRole
  variables?: PromptVariable[]
  example_input?: Record<string, unknown>
  example_output?: string
  language?: string
  is_default?: boolean
}

export interface UpdatePromptRequest {
  name?: string
  template_content?: string
  category?: PromptCategory
  description?: string
  expert_role?: ExpertRole
  variables?: PromptVariable[]
  example_input?: Record<string, unknown>
  example_output?: string
  language?: string
  is_default?: boolean
  is_active?: boolean
}

export interface AIGenerateRequest {
  category: PromptCategory
  description: string
  expert_role?: ExpertRole
  language?: string
}

// =============================================================================
// API RESPONSES
// =============================================================================

export interface PromptListResponse {
  prompts: PromptTemplate[]
  total: number
  limit: number
  offset: number
}

export interface TemplateGuide {
  title: string
  description: string
  required_variables?: { name: string; description: string }[]
  optional_variables?: { name: string; description: string }[]
  best_practices: string[]
  example: string
}

export interface TemplateGuidesResponse {
  guides: Record<PromptCategory, TemplateGuide>
}

export interface PromptStatsResponse {
  by_category: Record<string, {
    count: number
    total_usage: number
    has_default: boolean
  }>
  total: number
  total_usage: number
}

export interface CategoriesResponse {
  categories: { value: string; label: string }[]
  expert_roles: { value: string; label: string }[]
}

export interface AIGenerateResponse {
  name: string
  template_content: string
  variables: PromptVariable[]
  example_output: string | null
}

// =============================================================================
// UI CONSTANTS
// =============================================================================

export const CATEGORY_LABELS: Record<PromptCategory, string> = {
  rag: 'RAG',
  system: 'System',
  summarization: 'Summarization',
  analysis: 'Analysis',
  custom: 'Custom',
}

export const CATEGORY_DESCRIPTIONS: Record<PromptCategory, string> = {
  rag: 'ค้นหาและตอบจากเอกสาร',
  system: 'คำสั่งพื้นฐานของ AI',
  summarization: 'สรุปเนื้อหา',
  analysis: 'วิเคราะห์ข้อมูล',
  custom: 'สร้างเอง',
}

export const EXPERT_ROLE_LABELS: Record<ExpertRole, string> = {
  general: 'General',
  financial: 'Financial Analyst',
  legal: 'Legal Expert',
  technical: 'Technical Writer',
  data: 'Data Analyst',
  business: 'Business Consultant',
  researcher: 'Researcher',
}

export const LANGUAGE_OPTIONS = [
  { value: 'th', label: 'Thai' },
  { value: 'en', label: 'English' },
  { value: 'multi', label: 'Multilingual' },
]
