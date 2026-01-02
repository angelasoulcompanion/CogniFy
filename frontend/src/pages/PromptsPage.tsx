/**
 * CogniFy Prompts Management Page
 * Admin page for managing prompt templates
 * Created with love by Angela & David - 2 January 2026
 */

import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import {
  usePrompts,
  useCreatePrompt,
  useUpdatePrompt,
  useDeletePrompt,
  useSetDefaultPrompt,
  useTemplateGuides,
  usePromptStats,
  useCategories,
} from '@/hooks/usePrompts'
import type {
  PromptTemplate,
  PromptCategory,
  ExpertRole,
  PromptVariable,
  CreatePromptRequest,
  UpdatePromptRequest,
  TemplateGuide,
} from '@/types/prompt'
import {
  CATEGORY_LABELS,
  CATEGORY_DESCRIPTIONS,
  EXPERT_ROLE_LABELS,
  LANGUAGE_OPTIONS,
} from '@/types/prompt'
import {
  Plus,
  Trash2,
  Star,
  Save,
  X,
  Sparkles,
  FileText,
  Settings,
  BarChart3,
  Wand2,
  ChevronRight,
  Check,
  Code2,
  Eye,
  Lightbulb,
  RefreshCw,
  AlertCircle,
} from 'lucide-react'
import { AIWizardModal } from '@/components/prompts/AIWizardModal'

// =============================================================================
// CATEGORY TABS
// =============================================================================

const CATEGORY_TABS: { value: PromptCategory; icon: React.ElementType }[] = [
  { value: 'rag', icon: FileText },
  { value: 'system', icon: Settings },
  { value: 'summarization', icon: BarChart3 },
  { value: 'analysis', icon: BarChart3 },
  { value: 'custom', icon: Code2 },
]

// =============================================================================
// PROMPT LIST ITEM
// =============================================================================

function PromptListItem({
  prompt,
  isSelected,
  onClick,
}: {
  prompt: PromptTemplate
  isSelected: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left p-4 border-b border-secondary-700/50 transition-colors',
        isSelected
          ? 'bg-primary-500/20 border-l-2 border-l-primary-500'
          : 'hover:bg-secondary-700/30'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {prompt.is_default && (
              <Star className="h-4 w-4 text-yellow-400 flex-shrink-0" fill="currentColor" />
            )}
            <span className="font-medium text-white truncate">{prompt.name}</span>
          </div>
          {prompt.description && (
            <p className="mt-1 text-sm text-secondary-400 line-clamp-2">
              {prompt.description}
            </p>
          )}
          <div className="mt-2 flex items-center gap-3 text-xs text-secondary-500">
            {prompt.expert_role && (
              <span className="px-2 py-0.5 bg-secondary-700 rounded">
                {EXPERT_ROLE_LABELS[prompt.expert_role as ExpertRole] || prompt.expert_role}
              </span>
            )}
            <span>{prompt.language.toUpperCase()}</span>
            <span>{prompt.usage_count.toLocaleString()} uses</span>
          </div>
        </div>
        <ChevronRight className="h-4 w-4 text-secondary-500 flex-shrink-0" />
      </div>
    </button>
  )
}

// =============================================================================
// TEMPLATE GUIDE PANEL
// =============================================================================

function TemplateGuidePanel({ category }: { category: PromptCategory }) {
  const { data: guides } = useTemplateGuides()
  const guide = guides?.guides?.[category] as TemplateGuide | undefined

  if (!guide) return null

  return (
    <div className="bg-secondary-800/30 rounded-lg p-4 border border-secondary-700/50">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb className="h-4 w-4 text-yellow-400" />
        <h4 className="font-medium text-white">Template Guide</h4>
      </div>

      <div className="space-y-4 text-sm">
        <p className="text-secondary-300">{guide.description}</p>

        {guide.required_variables && guide.required_variables.length > 0 && (
          <div>
            <p className="text-secondary-400 font-medium mb-2">Required Variables:</p>
            <ul className="space-y-1">
              {guide.required_variables.map((v) => (
                <li key={v.name} className="flex items-center gap-2 text-secondary-300">
                  <code className="px-1.5 py-0.5 bg-primary-500/20 text-primary-300 rounded text-xs">
                    {'{' + v.name + '}'}
                  </code>
                  <span className="text-secondary-400">{v.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {guide.optional_variables && guide.optional_variables.length > 0 && (
          <div>
            <p className="text-secondary-400 font-medium mb-2">Optional Variables:</p>
            <ul className="space-y-1">
              {guide.optional_variables.map((v) => (
                <li key={v.name} className="flex items-center gap-2 text-secondary-300">
                  <code className="px-1.5 py-0.5 bg-secondary-700 text-secondary-300 rounded text-xs">
                    {'{' + v.name + '}'}
                  </code>
                  <span className="text-secondary-400">{v.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div>
          <p className="text-secondary-400 font-medium mb-2">Best Practices:</p>
          <ul className="space-y-1">
            {guide.best_practices?.map((tip, i) => (
              <li key={i} className="flex items-start gap-2 text-secondary-300">
                <Check className="h-3 w-3 text-green-400 mt-1 flex-shrink-0" />
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// VARIABLES EDITOR
// =============================================================================

function VariablesEditor({
  variables,
  onChange,
}: {
  variables: PromptVariable[]
  onChange: (vars: PromptVariable[]) => void
}) {
  const addVariable = () => {
    onChange([...variables, { name: '', required: true, description: '' }])
  }

  const updateVariable = (index: number, field: keyof PromptVariable, value: string | boolean) => {
    const updated = [...variables]
    updated[index] = { ...updated[index], [field]: value }
    onChange(updated)
  }

  const removeVariable = (index: number) => {
    onChange(variables.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-secondary-300">Variables</label>
        <button
          type="button"
          onClick={addVariable}
          className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1"
        >
          <Plus className="h-3 w-3" />
          Add
        </button>
      </div>

      {variables.length === 0 ? (
        <p className="text-sm text-secondary-500">No variables defined</p>
      ) : (
        <div className="space-y-2">
          {variables.map((v, index) => (
            <div
              key={index}
              className="flex items-center gap-2 p-2 bg-secondary-800/50 rounded-lg"
            >
              <input
                type="text"
                value={v.name}
                onChange={(e) => updateVariable(index, 'name', e.target.value)}
                placeholder="name"
                className="flex-1 px-2 py-1 text-sm bg-secondary-700 border border-secondary-600 rounded text-white placeholder-secondary-500"
              />
              <input
                type="text"
                value={v.description}
                onChange={(e) => updateVariable(index, 'description', e.target.value)}
                placeholder="description"
                className="flex-[2] px-2 py-1 text-sm bg-secondary-700 border border-secondary-600 rounded text-white placeholder-secondary-500"
              />
              <label className="flex items-center gap-1 text-xs text-secondary-400">
                <input
                  type="checkbox"
                  checked={v.required}
                  onChange={(e) => updateVariable(index, 'required', e.target.checked)}
                  className="rounded border-secondary-600 bg-secondary-700 text-primary-500"
                />
                Required
              </label>
              <button
                type="button"
                onClick={() => removeVariable(index)}
                className="p-1 text-red-400 hover:text-red-300"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// =============================================================================
// PROMPT EDITOR
// =============================================================================

function PromptEditor({
  prompt,
  category,
  onSave,
  onCancel,
  onDelete,
  onSetDefault,
  isNew,
}: {
  prompt: Partial<PromptTemplate> | null
  category: PromptCategory
  onSave: (data: CreatePromptRequest | UpdatePromptRequest) => void
  onCancel: () => void
  onDelete?: () => void
  onSetDefault?: () => void
  isNew: boolean
}) {
  const { data: categoriesData } = useCategories()
  const [formData, setFormData] = useState<{
    name: string
    description: string
    template_content: string
    category: PromptCategory
    expert_role: ExpertRole | ''
    variables: PromptVariable[]
    example_input: Record<string, unknown>
    example_output: string
    language: string
    is_default: boolean
  }>({
    name: '',
    description: '',
    template_content: '',
    category: category,
    expert_role: '',
    variables: [],
    example_input: {},
    example_output: '',
    language: 'th',
    is_default: false,
  })

  const [activeTab, setActiveTab] = useState<'edit' | 'preview'>('edit')
  const [showAIWizard, setShowAIWizard] = useState(false)

  useEffect(() => {
    if (prompt) {
      setFormData({
        name: prompt.name || '',
        description: prompt.description || '',
        template_content: prompt.template_content || '',
        category: (prompt.category as PromptCategory) || category,
        expert_role: (prompt.expert_role as ExpertRole) || '',
        variables: prompt.variables || [],
        example_input: prompt.example_input || {},
        example_output: prompt.example_output || '',
        language: prompt.language || 'th',
        is_default: prompt.is_default || false,
      })
    } else {
      setFormData({
        name: '',
        description: '',
        template_content: '',
        category: category,
        expert_role: '',
        variables: [],
        example_input: {},
        example_output: '',
        language: 'th',
        is_default: false,
      })
    }
  }, [prompt, category])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data: CreatePromptRequest = {
      name: formData.name,
      template_content: formData.template_content,
      category: formData.category,
      description: formData.description || undefined,
      expert_role: formData.expert_role || undefined,
      variables: formData.variables.length > 0 ? formData.variables : undefined,
      example_input: Object.keys(formData.example_input).length > 0 ? formData.example_input : undefined,
      example_output: formData.example_output || undefined,
      language: formData.language,
      is_default: formData.is_default,
    }
    onSave(data)
  }

  const handleAIGenerated = (generated: {
    name: string
    template_content: string
    variables: PromptVariable[]
    example_output: string | null
  }) => {
    setFormData((prev) => ({
      ...prev,
      name: generated.name,
      template_content: generated.template_content,
      variables: generated.variables,
      example_output: generated.example_output || '',
    }))
    setShowAIWizard(false)
  }

  // Extract variables from template content
  const extractedVariables = formData.template_content.match(/\{(\w+)\}/g)?.map((v) => v.slice(1, -1)) || []
  const undefinedVariables = extractedVariables.filter(
    (v) => !formData.variables.some((fv) => fv.name === v)
  )

  return (
    <form onSubmit={handleSubmit} className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-secondary-700">
        <h3 className="font-semibold text-white">
          {isNew ? 'New Prompt' : 'Edit Prompt'}
        </h3>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowAIWizard(true)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg text-white hover:from-purple-500 hover:to-pink-500"
          >
            <Sparkles className="h-4 w-4" />
            AI Wizard
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-secondary-700">
        <button
          type="button"
          onClick={() => setActiveTab('edit')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'edit'
              ? 'border-primary-500 text-primary-400'
              : 'border-transparent text-secondary-400 hover:text-secondary-200'
          )}
        >
          <Code2 className="h-4 w-4" />
          Edit
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('preview')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'preview'
              ? 'border-primary-500 text-primary-400'
              : 'border-transparent text-secondary-400 hover:text-secondary-200'
          )}
        >
          <Eye className="h-4 w-4" />
          Preview
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'edit' ? (
          <>
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary-300 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-white placeholder-secondary-500 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                  placeholder="e.g., Financial Analyst RAG"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-300 mb-1">
                  Language
                </label>
                <select
                  value={formData.language}
                  onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                  className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-white focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                >
                  {LANGUAGE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary-300 mb-1">
                  Category
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value as PromptCategory })}
                  className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-white focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                >
                  {categoriesData?.categories.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-300 mb-1">
                  Expert Role
                </label>
                <select
                  value={formData.expert_role}
                  onChange={(e) => setFormData({ ...formData, expert_role: e.target.value as ExpertRole })}
                  className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-white focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                >
                  <option value="">None</option>
                  {categoriesData?.expert_roles.map((role) => (
                    <option key={role.value} value={role.value}>
                      {role.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-secondary-300 mb-1">
                Description
              </label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-white placeholder-secondary-500 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                placeholder="Brief description of this prompt"
              />
            </div>

            {/* Template Content */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-secondary-300">
                  Template Content *
                </label>
                {undefinedVariables.length > 0 && (
                  <span className="text-xs text-yellow-400 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {undefinedVariables.length} undefined variable(s)
                  </span>
                )}
              </div>
              <textarea
                value={formData.template_content}
                onChange={(e) => setFormData({ ...formData, template_content: e.target.value })}
                required
                rows={10}
                className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-white placeholder-secondary-500 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 font-mono text-sm"
                placeholder="You are a helpful assistant...&#10;&#10;Use {variable_name} for template variables"
              />
              <p className="mt-1 text-xs text-secondary-500">
                Use {'{variable}'} syntax for dynamic values. Example: {'{query}'}, {'{context}'}
              </p>
            </div>

            {/* Variables */}
            <VariablesEditor
              variables={formData.variables}
              onChange={(vars) => setFormData({ ...formData, variables: vars })}
            />

            {/* Example Output */}
            <div>
              <label className="block text-sm font-medium text-secondary-300 mb-1">
                Example Output
              </label>
              <textarea
                value={formData.example_output}
                onChange={(e) => setFormData({ ...formData, example_output: e.target.value })}
                rows={4}
                className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-white placeholder-secondary-500 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 text-sm"
                placeholder="Example of what the AI should output..."
              />
            </div>

            {/* Template Guide */}
            <TemplateGuidePanel category={formData.category} />
          </>
        ) : (
          /* Preview Tab */
          <div className="space-y-4">
            <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
              <h4 className="text-sm font-medium text-secondary-400 mb-2">Template Preview</h4>
              <pre className="whitespace-pre-wrap text-white font-mono text-sm">
                {formData.template_content || 'No content yet...'}
              </pre>
            </div>

            {formData.variables.length > 0 && (
              <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
                <h4 className="text-sm font-medium text-secondary-400 mb-2">Variables</h4>
                <div className="flex flex-wrap gap-2">
                  {formData.variables.map((v) => (
                    <span
                      key={v.name}
                      className={cn(
                        'px-2 py-1 rounded text-xs',
                        v.required
                          ? 'bg-primary-500/20 text-primary-300'
                          : 'bg-secondary-700 text-secondary-300'
                      )}
                    >
                      {'{' + v.name + '}'}
                      {v.required && ' *'}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {formData.example_output && (
              <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
                <h4 className="text-sm font-medium text-secondary-400 mb-2">Example Output</h4>
                <p className="text-white text-sm whitespace-pre-wrap">{formData.example_output}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between p-4 border-t border-secondary-700 bg-secondary-800/50">
        <div className="flex items-center gap-2">
          {!isNew && onDelete && (
            <button
              type="button"
              onClick={onDelete}
              className="flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </button>
          )}
          {!isNew && onSetDefault && !prompt?.is_default && (
            <button
              type="button"
              onClick={onSetDefault}
              className="flex items-center gap-2 px-3 py-2 text-sm text-yellow-400 hover:text-yellow-300 hover:bg-yellow-500/10 rounded-lg"
            >
              <Star className="h-4 w-4" />
              Set Default
            </button>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm text-secondary-300 hover:text-white hover:bg-secondary-700 rounded-lg"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="flex items-center gap-2 px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-500"
          >
            <Save className="h-4 w-4" />
            {isNew ? 'Create' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* AI Wizard Modal */}
      {showAIWizard && (
        <AIWizardModal
          category={formData.category}
          onClose={() => setShowAIWizard(false)}
          onGenerated={handleAIGenerated}
        />
      )}
    </form>
  )
}

// =============================================================================
// STATS HEADER
// =============================================================================

function StatsHeader() {
  const { data: stats } = usePromptStats()

  if (!stats) return null

  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
        <p className="text-sm text-secondary-400">Total Prompts</p>
        <p className="text-2xl font-semibold text-white">{stats.total}</p>
      </div>
      <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
        <p className="text-sm text-secondary-400">Total Usage</p>
        <p className="text-2xl font-semibold text-white">{stats.total_usage.toLocaleString()}</p>
      </div>
      <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
        <p className="text-sm text-secondary-400">RAG Prompts</p>
        <p className="text-2xl font-semibold text-white">{stats.by_category.rag?.count || 0}</p>
      </div>
      <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
        <p className="text-sm text-secondary-400">Custom Prompts</p>
        <p className="text-2xl font-semibold text-white">{stats.by_category.custom?.count || 0}</p>
      </div>
    </div>
  )
}

// =============================================================================
// MAIN PAGE
// =============================================================================

export function PromptsPage() {
  const [activeCategory, setActiveCategory] = useState<PromptCategory>('rag')
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  // Data hooks
  const { data: promptsData, isLoading, refetch } = usePrompts({ category: activeCategory })
  const createPrompt = useCreatePrompt()
  const updatePrompt = useUpdatePrompt()
  const deletePrompt = useDeletePrompt()
  const setDefault = useSetDefaultPrompt()

  const prompts = promptsData?.prompts || []
  const selectedPrompt = prompts.find((p) => p.template_id === selectedPromptId)

  // Reset selection when category changes
  useEffect(() => {
    setSelectedPromptId(null)
    setIsCreating(false)
  }, [activeCategory])

  const handleCreate = (data: CreatePromptRequest) => {
    createPrompt.mutate(data, {
      onSuccess: () => {
        setIsCreating(false)
        refetch()
      },
    })
  }

  const handleUpdate = (data: UpdatePromptRequest) => {
    if (!selectedPromptId) return
    updatePrompt.mutate(
      { templateId: selectedPromptId, data },
      {
        onSuccess: () => {
          refetch()
        },
      }
    )
  }

  const handleDelete = () => {
    if (!selectedPromptId) return
    if (!confirm('Are you sure you want to delete this prompt?')) return
    deletePrompt.mutate(selectedPromptId, {
      onSuccess: () => {
        setSelectedPromptId(null)
        refetch()
      },
    })
  }

  const handleSetDefault = () => {
    if (!selectedPromptId) return
    setDefault.mutate(selectedPromptId, {
      onSuccess: () => {
        refetch()
      },
    })
  }

  return (
    <div className="min-h-screen bg-secondary-950 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Prompt Management</h1>
            <p className="text-secondary-400">Create and manage prompt templates</p>
          </div>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-secondary-800 border border-secondary-700 rounded-xl text-secondary-300 hover:bg-secondary-700"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>

        {/* Stats */}
        <StatsHeader />

        {/* Category Tabs */}
        <div className="mb-6 border-b border-secondary-700">
          <div className="flex gap-1">
            {CATEGORY_TABS.map(({ value, icon: Icon }) => (
              <button
                key={value}
                onClick={() => setActiveCategory(value)}
                className={cn(
                  'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                  activeCategory === value
                    ? 'border-primary-500 text-primary-400'
                    : 'border-transparent text-secondary-400 hover:text-secondary-200'
                )}
              >
                <Icon className="h-4 w-4" />
                {CATEGORY_LABELS[value]}
              </button>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Panel - Prompt List */}
          <div className="col-span-4 bg-secondary-800/50 rounded-xl border border-secondary-700/50 overflow-hidden">
            {/* List Header */}
            <div className="flex items-center justify-between p-4 border-b border-secondary-700">
              <div>
                <h3 className="font-semibold text-white">{CATEGORY_LABELS[activeCategory]}</h3>
                <p className="text-xs text-secondary-400">{CATEGORY_DESCRIPTIONS[activeCategory]}</p>
              </div>
              <button
                onClick={() => {
                  setSelectedPromptId(null)
                  setIsCreating(true)
                }}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-500"
              >
                <Plus className="h-4 w-4" />
                New
              </button>
            </div>

            {/* List */}
            <div className="max-h-[calc(100vh-400px)] overflow-y-auto">
              {isLoading ? (
                <div className="p-4 text-center text-secondary-400">Loading...</div>
              ) : prompts.length === 0 ? (
                <div className="p-8 text-center">
                  <FileText className="h-12 w-12 mx-auto text-secondary-600 mb-3" />
                  <p className="text-secondary-400">No prompts in this category</p>
                  <button
                    onClick={() => setIsCreating(true)}
                    className="mt-3 text-sm text-primary-400 hover:text-primary-300"
                  >
                    Create your first prompt
                  </button>
                </div>
              ) : (
                prompts.map((prompt) => (
                  <PromptListItem
                    key={prompt.template_id}
                    prompt={prompt}
                    isSelected={selectedPromptId === prompt.template_id}
                    onClick={() => {
                      setSelectedPromptId(prompt.template_id)
                      setIsCreating(false)
                    }}
                  />
                ))
              )}
            </div>
          </div>

          {/* Right Panel - Editor */}
          <div className="col-span-8 bg-secondary-800/50 rounded-xl border border-secondary-700/50 overflow-hidden">
            {isCreating || selectedPrompt ? (
              <PromptEditor
                prompt={isCreating ? null : (selectedPrompt ?? null)}
                category={activeCategory}
                onSave={(data) => {
                  if (isCreating) {
                    handleCreate(data as CreatePromptRequest)
                  } else {
                    handleUpdate(data as UpdatePromptRequest)
                  }
                }}
                onCancel={() => {
                  setIsCreating(false)
                  setSelectedPromptId(null)
                }}
                onDelete={isCreating ? undefined : handleDelete}
                onSetDefault={isCreating ? undefined : handleSetDefault}
                isNew={isCreating}
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-96 text-center p-8">
                <Wand2 className="h-16 w-16 text-secondary-600 mb-4" />
                <h3 className="text-lg font-medium text-secondary-300 mb-2">
                  Select or Create a Prompt
                </h3>
                <p className="text-secondary-500 mb-4 max-w-md">
                  Choose a prompt from the list to edit, or create a new one to get started.
                </p>
                <button
                  onClick={() => setIsCreating(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500"
                >
                  <Plus className="h-4 w-4" />
                  Create New Prompt
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
