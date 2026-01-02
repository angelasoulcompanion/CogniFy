/**
 * CogniFy AI Wizard Modal
 * AI-assisted prompt template builder
 * Created with love by Angela & David - 2 January 2026
 */

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { useAIGeneratePrompt } from '@/hooks/usePrompts'
import type { PromptCategory, ExpertRole, PromptVariable } from '@/types/prompt'
import {
  CATEGORY_LABELS,
  CATEGORY_DESCRIPTIONS,
  EXPERT_ROLE_LABELS,
  LANGUAGE_OPTIONS,
} from '@/types/prompt'
import {
  X,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Loader2,
  Wand2,
  Check,
  Edit3,
  Copy,
} from 'lucide-react'
import toast from 'react-hot-toast'

// =============================================================================
// TYPES
// =============================================================================

interface AIWizardModalProps {
  category: PromptCategory
  onClose: () => void
  onGenerated: (result: {
    name: string
    template_content: string
    variables: PromptVariable[]
    example_output: string | null
  }) => void
}

// =============================================================================
// STEP INDICATOR
// =============================================================================

function StepIndicator({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }) {
  return (
    <div className="flex items-center justify-center gap-2">
      {Array.from({ length: totalSteps }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'w-2 h-2 rounded-full transition-colors',
            i < currentStep
              ? 'bg-primary-500'
              : i === currentStep
              ? 'bg-primary-400'
              : 'bg-secondary-600'
          )}
        />
      ))}
    </div>
  )
}

// =============================================================================
// STEP 1: CATEGORY SELECTION
// =============================================================================

function Step1Category({
  value,
  onChange,
}: {
  value: PromptCategory
  onChange: (cat: PromptCategory) => void
}) {
  const categories: PromptCategory[] = ['rag', 'system', 'summarization', 'analysis', 'custom']

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-white mb-2">Step 1: Choose Category</h3>
        <p className="text-sm text-secondary-400">
          What type of prompt do you want to create?
        </p>
      </div>

      <div className="space-y-2">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => onChange(cat)}
            className={cn(
              'w-full p-4 rounded-lg border text-left transition-all',
              value === cat
                ? 'bg-primary-500/20 border-primary-500 text-white'
                : 'bg-secondary-800/50 border-secondary-700 text-secondary-300 hover:border-secondary-500'
            )}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">{CATEGORY_LABELS[cat]}</p>
                <p className="text-sm text-secondary-400">{CATEGORY_DESCRIPTIONS[cat]}</p>
              </div>
              {value === cat && <Check className="h-5 w-5 text-primary-400" />}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

// =============================================================================
// STEP 2: DESCRIPTION
// =============================================================================

function Step2Description({
  value,
  onChange,
}: {
  value: string
  onChange: (desc: string) => void
}) {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-white mb-2">Step 2: Describe Your Prompt</h3>
        <p className="text-sm text-secondary-400">
          Tell us what you want the AI to do. Be specific!
        </p>
      </div>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={6}
        className="w-full px-4 py-3 bg-secondary-800 border border-secondary-700 rounded-lg text-white placeholder-secondary-500 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
        placeholder="Example: I want a prompt that analyzes financial data, compares year-over-year performance, and presents results in a table format with key insights highlighted."
      />

      <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
        <p className="text-sm text-secondary-400 font-medium mb-2">Tips for better results:</p>
        <ul className="space-y-1 text-sm text-secondary-400">
          <li>- Describe the specific task or goal</li>
          <li>- Mention the format you want (table, bullets, paragraphs)</li>
          <li>- Include any special requirements (language, tone, length)</li>
          <li>- Specify what data or context will be provided</li>
        </ul>
      </div>
    </div>
  )
}

// =============================================================================
// STEP 3: EXPERT ROLE & LANGUAGE
// =============================================================================

function Step3Settings({
  expertRole,
  onExpertRoleChange,
  language,
  onLanguageChange,
}: {
  expertRole: ExpertRole
  onExpertRoleChange: (role: ExpertRole) => void
  language: string
  onLanguageChange: (lang: string) => void
}) {
  const roles: ExpertRole[] = ['general', 'financial', 'legal', 'technical', 'data', 'business', 'researcher']

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-white mb-2">Step 3: Expert Settings</h3>
        <p className="text-sm text-secondary-400">
          Choose the AI's expertise and language
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-secondary-300 mb-3">Expert Role</label>
        <div className="grid grid-cols-2 gap-2">
          {roles.map((role) => (
            <button
              key={role}
              onClick={() => onExpertRoleChange(role)}
              className={cn(
                'p-3 rounded-lg border text-left transition-all',
                expertRole === role
                  ? 'bg-primary-500/20 border-primary-500 text-white'
                  : 'bg-secondary-800/50 border-secondary-700 text-secondary-300 hover:border-secondary-500'
              )}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm">{EXPERT_ROLE_LABELS[role]}</span>
                {expertRole === role && <Check className="h-4 w-4 text-primary-400" />}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-secondary-300 mb-3">Output Language</label>
        <div className="flex gap-2">
          {LANGUAGE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onLanguageChange(opt.value)}
              className={cn(
                'flex-1 p-3 rounded-lg border text-center transition-all',
                language === opt.value
                  ? 'bg-primary-500/20 border-primary-500 text-white'
                  : 'bg-secondary-800/50 border-secondary-700 text-secondary-300 hover:border-secondary-500'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// STEP 4: RESULT
// =============================================================================

function Step4Result({
  result,
  isLoading,
  error,
  onRegenerate,
  onEdit,
  onUse,
}: {
  result: {
    name: string
    template_content: string
    variables: PromptVariable[]
    example_output: string | null
  } | null
  isLoading: boolean
  error: string | null
  onRegenerate: () => void
  onEdit: () => void
  onUse: () => void
}) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="h-12 w-12 text-primary-400 animate-spin mb-4" />
        <p className="text-secondary-300">AI is generating your prompt...</p>
        <p className="text-sm text-secondary-500 mt-1">This may take a few seconds</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
          <X className="h-8 w-8 text-red-400" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">Generation Failed</h3>
        <p className="text-sm text-red-400 mb-4">{error}</p>
        <button
          onClick={onRegenerate}
          className="px-4 py-2 bg-secondary-700 text-white rounded-lg hover:bg-secondary-600"
        >
          Try Again
        </button>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="text-center py-8">
        <Wand2 className="h-12 w-12 text-secondary-600 mx-auto mb-4" />
        <p className="text-secondary-400">Click Generate to create your prompt</p>
      </div>
    )
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(result.template_content)
    toast.success('Copied to clipboard!')
  }

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-white mb-2">Generated Prompt</h3>
        <p className="text-sm text-secondary-400">
          Review and customize your AI-generated prompt
        </p>
      </div>

      <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-secondary-300">Name</span>
        </div>
        <p className="text-white">{result.name}</p>
      </div>

      <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-secondary-300">Template</span>
          <button
            onClick={copyToClipboard}
            className="text-secondary-400 hover:text-white p-1"
          >
            <Copy className="h-4 w-4" />
          </button>
        </div>
        <pre className="text-sm text-white whitespace-pre-wrap font-mono max-h-48 overflow-y-auto">
          {result.template_content}
        </pre>
      </div>

      {result.variables.length > 0 && (
        <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
          <span className="text-sm font-medium text-secondary-300 block mb-2">Variables</span>
          <div className="flex flex-wrap gap-2">
            {result.variables.map((v) => (
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

      {result.example_output && (
        <div className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50">
          <span className="text-sm font-medium text-secondary-300 block mb-2">Example Output</span>
          <p className="text-sm text-white whitespace-pre-wrap">{result.example_output}</p>
        </div>
      )}

      <div className="flex gap-3 pt-4">
        <button
          onClick={onRegenerate}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-secondary-700 text-white rounded-lg hover:bg-secondary-600"
        >
          <Sparkles className="h-4 w-4" />
          Regenerate
        </button>
        <button
          onClick={onEdit}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-secondary-700 text-white rounded-lg hover:bg-secondary-600"
        >
          <Edit3 className="h-4 w-4" />
          Edit First
        </button>
        <button
          onClick={onUse}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500"
        >
          <Check className="h-4 w-4" />
          Use This
        </button>
      </div>
    </div>
  )
}

// =============================================================================
// MAIN MODAL
// =============================================================================

export function AIWizardModal({ category, onClose, onGenerated }: AIWizardModalProps) {
  const [step, setStep] = useState(0)
  const [formData, setFormData] = useState({
    category: category,
    description: '',
    expertRole: 'general' as ExpertRole,
    language: 'th',
  })
  const [result, setResult] = useState<{
    name: string
    template_content: string
    variables: PromptVariable[]
    example_output: string | null
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const generateMutation = useAIGeneratePrompt()

  const canProceed = () => {
    switch (step) {
      case 0:
        return true
      case 1:
        return formData.description.length >= 10
      case 2:
        return true
      case 3:
        return result !== null
      default:
        return false
    }
  }

  const handleNext = () => {
    if (step === 2) {
      // Generate prompt
      handleGenerate()
    }
    if (step < 3) {
      setStep(step + 1)
    }
  }

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1)
      if (step === 3) {
        setResult(null)
        setError(null)
      }
    }
  }

  const handleGenerate = () => {
    setError(null)
    generateMutation.mutate(
      {
        category: formData.category,
        description: formData.description,
        expert_role: formData.expertRole,
        language: formData.language,
      },
      {
        onSuccess: (data) => {
          setResult(data)
        },
        onError: (err: Error) => {
          setError(err.message)
        },
      }
    )
  }

  const handleUse = () => {
    if (result) {
      onGenerated(result)
    }
  }

  const handleEdit = () => {
    if (result) {
      onGenerated(result)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[90vh] bg-secondary-900 rounded-2xl shadow-2xl border border-secondary-700 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-secondary-700 bg-gradient-to-r from-purple-600/20 to-pink-600/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">AI Prompt Wizard</h2>
              <p className="text-sm text-secondary-400">Let AI help create your prompt</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-secondary-400 hover:text-white hover:bg-secondary-700 rounded-lg"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Step Indicator */}
        <div className="py-3 border-b border-secondary-700/50">
          <StepIndicator currentStep={step} totalSteps={4} />
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          {step === 0 && (
            <Step1Category
              value={formData.category}
              onChange={(cat) => setFormData({ ...formData, category: cat })}
            />
          )}
          {step === 1 && (
            <Step2Description
              value={formData.description}
              onChange={(desc) => setFormData({ ...formData, description: desc })}
            />
          )}
          {step === 2 && (
            <Step3Settings
              expertRole={formData.expertRole}
              onExpertRoleChange={(role) => setFormData({ ...formData, expertRole: role })}
              language={formData.language}
              onLanguageChange={(lang) => setFormData({ ...formData, language: lang })}
            />
          )}
          {step === 3 && (
            <Step4Result
              result={result}
              isLoading={generateMutation.isPending}
              error={error}
              onRegenerate={handleGenerate}
              onEdit={handleEdit}
              onUse={handleUse}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-secondary-700 bg-secondary-800/50">
          <button
            onClick={handleBack}
            disabled={step === 0}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
              step === 0
                ? 'text-secondary-500 cursor-not-allowed'
                : 'text-secondary-300 hover:text-white hover:bg-secondary-700'
            )}
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>

          <span className="text-sm text-secondary-500">
            Step {step + 1} of 4
          </span>

          {step < 3 && (
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
                canProceed()
                  ? 'bg-primary-600 text-white hover:bg-primary-500'
                  : 'bg-secondary-700 text-secondary-500 cursor-not-allowed'
              )}
            >
              {step === 2 ? (
                <>
                  <Sparkles className="h-4 w-4" />
                  Generate
                </>
              ) : (
                <>
                  Next
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          )}

          {step === 3 && !result && (
            <button
              onClick={handleGenerate}
              disabled={generateMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500"
            >
              <Sparkles className="h-4 w-4" />
              Generate
            </button>
          )}

          {step === 3 && result && (
            <div className="w-24" /> // Spacer for layout balance
          )}
        </div>
      </div>
    </div>
  )
}
