/**
 * CogniFy Documents Page
 * Document management interface
 * Created with love by Angela & David - 1 January 2026
 */

import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import {
  useDocuments,
  useUploadDocument,
  useDeleteDocument,
  getDocumentStatusColor,
  getDocumentStatusLabel,
} from '@/hooks/useDocuments'
import { formatFileSize, formatRelativeTime, getFileIcon } from '@/lib/utils'
import { cn } from '@/lib/utils'
import type { Document } from '@/types'
import toast from 'react-hot-toast'
import {
  Upload,
  Trash2,
  RefreshCw,
  Search,
  MoreVertical,
  Loader2,
  FolderOpen,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { PageHeader } from '@/components/ui/PageHeader'
import { EmptyState as SharedEmptyState } from '@/components/ui/EmptyState'
import { DropdownMenu, DropdownItem } from '@/components/ui/DropdownMenu'

export function DocumentsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)
  const [previousStatuses, setPreviousStatuses] = useState<Record<string, string>>({})

  // Check if any document is processing to enable auto-polling
  const { data: documents, isLoading, refetch } = useDocuments(20, 0, false)

  // Track processing documents for auto-polling
  const hasProcessingDocs = useMemo(() =>
    documents?.some((doc: Document) =>
      doc.processing_status === 'processing' || doc.processing_status === 'pending'
    ) ?? false,
    [documents]
  )

  // Use separate hook with polling when there are processing documents
  const { data: polledDocuments } = useDocuments(20, 0, hasProcessingDocs)
  const activeDocuments = hasProcessingDocs ? polledDocuments : documents

  // Detect when processing completes and show notification
  useEffect(() => {
    if (!activeDocuments) return

    activeDocuments.forEach((doc: Document) => {
      const prevStatus = previousStatuses[doc.document_id]

      // Notify when status changes from processing/pending to completed
      if (prevStatus &&
          (prevStatus === 'processing' || prevStatus === 'pending') &&
          doc.processing_status === 'completed') {
        toast.success(
          `"${doc.title || doc.original_filename}" processed successfully! 🎉`,
          { duration: 5000, icon: '✅' }
        )
      }

      // Notify when processing fails
      if (prevStatus &&
          (prevStatus === 'processing' || prevStatus === 'pending') &&
          doc.processing_status === 'failed') {
        toast.error(
          `"${doc.title || doc.original_filename}" processing failed`,
          { duration: 5000 }
        )
      }
    })

    // Update previous statuses
    const newStatuses: Record<string, string> = {}
    activeDocuments.forEach((doc: Document) => {
      newStatuses[doc.document_id] = doc.processing_status
    })
    setPreviousStatuses(newStatuses)
  }, [activeDocuments])

  const uploadMutation = useUploadDocument()
  const deleteMutation = useDeleteDocument()

  // Filter documents by search (use activeDocuments for real-time updates)
  const filteredDocuments = activeDocuments?.filter((doc: Document) =>
    doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.title?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  // Handle file upload
  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploadProgress(0)
    await uploadMutation.mutateAsync({
      file,
      onProgress: setUploadProgress,
    })
    setUploadProgress(null)

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [uploadMutation])

  // Handle drag and drop
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (!file) return

    setUploadProgress(0)
    await uploadMutation.mutateAsync({
      file,
      onProgress: setUploadProgress,
    })
    setUploadProgress(null)
  }, [uploadMutation])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Documents"
        subtitle={<>
          {activeDocuments?.length || 0} document{activeDocuments?.length !== 1 ? 's' : ''} uploaded
          {hasProcessingDocs && (
            <span className="ml-2 inline-flex items-center gap-1 text-primary-400">
              <Loader2 className="h-3 w-3 animate-spin" />
              Processing...
            </span>
          )}
        </>}
      >
        <Button variant="secondary" onClick={() => refetch()} icon={<RefreshCw className="h-4 w-4" />}>
          Refresh
        </Button>
        <Button onClick={() => fileInputRef.current?.click()} icon={<Upload className="h-4 w-4" />}>
          Upload
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept=".pdf,.docx,.doc,.txt,.xlsx,.xls"
          className="hidden"
        />
      </PageHeader>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-5xl">
          {/* Search */}
          <div className="mb-6 flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-secondary-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search documents..."
                className="w-full rounded-xl border border-secondary-700 bg-secondary-800/50 py-2.5 pl-10 pr-4 text-white placeholder-secondary-500 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
              />
            </div>
          </div>

          {/* Upload Zone */}
          {uploadProgress !== null && (
            <div className="mb-6 rounded-xl border border-primary-500/30 bg-primary-900/30 p-4">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-primary-400" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-primary-200">
                    Uploading document...
                  </p>
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-primary-800">
                    <div
                      className="h-full bg-gradient-to-r from-primary-500 to-violet-500 transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
                <span className="text-sm font-medium text-primary-400">
                  {uploadProgress}%
                </span>
              </div>
            </div>
          )}

          {/* Drop Zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={cn(
              'mb-6 rounded-xl border-2 border-dashed p-8 text-center transition-colors',
              isDragging
                ? 'border-primary-500 bg-primary-900/30'
                : 'border-secondary-700 hover:border-primary-500/50 hover:bg-secondary-800/30'
            )}
          >
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-secondary-800">
              <Upload className="h-6 w-6 text-primary-400" />
            </div>
            <p className="mt-3 text-sm font-medium text-secondary-200">
              Drag and drop files here
            </p>
            <p className="mt-1 text-sm text-secondary-500">
              or click Upload button • PDF, DOCX, TXT, Excel
            </p>
          </div>

          {/* Documents List */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-secondary-400" />
            </div>
          ) : filteredDocuments.length === 0 ? (
            <EmptyState hasDocuments={documents?.length > 0} />
          ) : (
            <div className="space-y-3">
              {filteredDocuments.map((doc: Document) => (
                <DocumentCard
                  key={doc.document_id}
                  document={doc}
                  onDelete={() => deleteMutation.mutate(doc.document_id)}
                  isDeleting={deleteMutation.isPending}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// DOCUMENT CARD COMPONENT
// =============================================================================

function DocumentCard({
  document,
  onDelete,
  isDeleting,
}: {
  document: Document
  onDelete: () => void
  isDeleting: boolean
}) {
  const isProcessing = document.processing_status === 'processing' || document.processing_status === 'pending'
  const isCompleted = document.processing_status === 'completed'

  return (
    <div className={cn(
      'group rounded-xl border bg-secondary-800/50 p-4 transition-all',
      isProcessing
        ? 'border-primary-500/50 bg-primary-900/20'
        : isCompleted
          ? 'border-secondary-700/50 hover:border-green-500/30 hover:bg-secondary-800'
          : 'border-secondary-700/50 hover:border-primary-500/30 hover:bg-secondary-800'
    )}>
      <div className="flex items-center gap-4">
        {/* Icon */}
        <div className={cn(
          'flex h-12 w-12 items-center justify-center rounded-lg text-2xl',
          isProcessing ? 'bg-primary-800/50' : 'bg-secondary-700/50'
        )}>
          {isProcessing ? (
            <Loader2 className="h-6 w-6 animate-spin text-primary-400" />
          ) : isCompleted ? (
            <span>{getFileIcon(document.file_type)}</span>
          ) : (
            <span>{getFileIcon(document.file_type)}</span>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-white truncate">
              {document.title || document.original_filename}
            </h3>
            <span
              className={cn(
                'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
                getDocumentStatusColor(document.processing_status)
              )}
            >
              {isProcessing && <Loader2 className="h-3 w-3 animate-spin" />}
              {isCompleted && <CheckCircle2 className="h-3 w-3" />}
              {getDocumentStatusLabel(document.processing_status)}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-3 text-sm text-secondary-400">
            <span>{formatFileSize(document.file_size_bytes)}</span>
            <span>•</span>
            <span>{document.total_chunks} chunks</span>
            <span>•</span>
            <span>{formatRelativeTime(document.created_at)}</span>
          </div>
          {document.processing_error && (
            <p className="mt-1 flex items-center gap-1 text-sm text-red-400">
              <AlertCircle className="h-4 w-4" />
              {document.processing_error}
            </p>
          )}
        </div>

        <DropdownMenu trigger={<MoreVertical className="h-5 w-5" />} width="w-48">
          <DropdownItem
            onClick={onDelete}
            disabled={isDeleting}
            variant="danger"
            icon={isDeleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          >
            Delete
          </DropdownItem>
        </DropdownMenu>
      </div>

      {/* Processing Progress Bar */}
      {isProcessing && (
        <ProcessingProgressBar
          step={document.processing_step}
          progress={document.processing_progress ?? 0}
        />
      )}
    </div>
  )
}

// =============================================================================
// PROCESSING PROGRESS BAR COMPONENT
// =============================================================================

const PROCESSING_STEPS = [
  { key: 'extracting', label: 'Extracting', icon: '📄', description: 'Reading document content...' },
  { key: 'chunking', label: 'Chunking', icon: '✂️', description: 'Splitting into segments...' },
  { key: 'embedding', label: 'Embedding', icon: '🧠', description: 'Generating AI embeddings...' },
  { key: 'storing', label: 'Storing', icon: '💾', description: 'Saving to database...' },
] as const

function ProcessingProgressBar({
  step,
  progress,
}: {
  step: string | null
  progress: number
}) {
  const currentStepIndex = PROCESSING_STEPS.findIndex(s => s.key === step)
  const currentStepInfo = PROCESSING_STEPS[currentStepIndex] || PROCESSING_STEPS[0]

  return (
    <div className="mt-3 pt-3 border-t border-primary-500/20">
      {/* Current step info */}
      <div className="flex items-center justify-between text-xs mb-2">
        <span className="text-primary-200 font-medium flex items-center gap-1.5">
          <span className="text-base">{currentStepInfo.icon}</span>
          {currentStepInfo.description}
        </span>
        <span className="text-primary-400 font-mono">
          {progress}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-primary-800/50">
        <div
          className="h-full bg-gradient-to-r from-primary-500 via-violet-500 to-primary-400 transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Step indicators */}
      <div className="mt-2 flex justify-between">
        {PROCESSING_STEPS.map((s, i) => {
          const isActive = s.key === step
          const isCompleted = currentStepIndex > i
          return (
            <div
              key={s.key}
              className={cn(
                'flex items-center gap-1 text-[10px] transition-all',
                isActive && 'text-primary-300 font-medium scale-105',
                isCompleted && 'text-green-400',
                !isActive && !isCompleted && 'text-primary-600'
              )}
            >
              {isCompleted ? (
                <CheckCircle2 className="h-3 w-3" />
              ) : isActive ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <span className="h-3 w-3 rounded-full border border-current flex items-center justify-center text-[8px]">
                  {i + 1}
                </span>
              )}
              <span>{s.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// =============================================================================
// EMPTY STATE COMPONENT
// =============================================================================

function EmptyState({ hasDocuments }: { hasDocuments: boolean }) {
  return (
    <SharedEmptyState
      icon={<FolderOpen className="h-8 w-8 text-secondary-500" />}
      title={hasDocuments ? 'No documents found' : 'No documents yet'}
      description={hasDocuments
        ? 'Try adjusting your search query'
        : 'Upload your first document to get started with CogniFy'}
    />
  )
}
