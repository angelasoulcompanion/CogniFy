/**
 * CogniFy Documents Page
 * Document management interface
 * Created with love by Angela & David - 1 January 2026
 */

import { useState, useCallback, useRef } from 'react'
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
import {
  Upload,
  Trash2,
  RefreshCw,
  Search,
  MoreVertical,
  Loader2,
  FolderOpen,
  AlertCircle,
} from 'lucide-react'

export function DocumentsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)

  const { data: documents, isLoading, refetch } = useDocuments()
  const uploadMutation = useUploadDocument()
  const deleteMutation = useDeleteDocument()

  // Filter documents by search
  const filteredDocuments = documents?.filter((doc: Document) =>
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
      {/* Header */}
      <header className="flex h-16 items-center justify-between border-b border-primary-500/10 bg-secondary-900/50 backdrop-blur-sm px-6">
        <div>
          <h1 className="text-xl font-semibold text-white">Documents</h1>
          <p className="text-sm text-secondary-400">
            {documents?.length || 0} document{documents?.length !== 1 ? 's' : ''} uploaded
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 rounded-xl border border-secondary-700 px-3 py-2 text-sm text-secondary-300 hover:bg-secondary-800 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary-600 to-violet-600 px-4 py-2 text-sm font-medium text-white hover:from-primary-500 hover:to-violet-500 transition-all shadow-lg shadow-primary-500/25"
          >
            <Upload className="h-4 w-4" />
            Upload
          </button>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            accept=".pdf,.docx,.doc,.txt,.xlsx,.xls"
            className="hidden"
          />
        </div>
      </header>

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
  const [showMenu, setShowMenu] = useState(false)

  return (
    <div className="group flex items-center gap-4 rounded-xl border border-secondary-700/50 bg-secondary-800/50 p-4 transition-colors hover:border-primary-500/30 hover:bg-secondary-800">
      {/* Icon */}
      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-secondary-700/50 text-2xl">
        {getFileIcon(document.file_type)}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-white truncate">
            {document.title || document.original_filename}
          </h3>
          <span
            className={cn(
              'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
              getDocumentStatusColor(document.processing_status)
            )}
          >
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

      {/* Actions */}
      <div className="relative">
        <button
          onClick={() => setShowMenu(!showMenu)}
          className="rounded-lg p-2 text-secondary-400 hover:bg-secondary-700 hover:text-white"
        >
          <MoreVertical className="h-5 w-5" />
        </button>

        {showMenu && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setShowMenu(false)}
            />
            <div className="absolute right-0 top-full z-20 mt-1 w-48 rounded-lg border border-secondary-700 bg-secondary-800 py-1 shadow-lg">
              <button
                onClick={() => {
                  setShowMenu(false)
                  onDelete()
                }}
                disabled={isDeleting}
                className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-red-400 hover:bg-red-500/20 disabled:opacity-50"
              >
                {isDeleting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                Delete
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// EMPTY STATE COMPONENT
// =============================================================================

function EmptyState({ hasDocuments }: { hasDocuments: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary-800">
        <FolderOpen className="h-8 w-8 text-secondary-500" />
      </div>
      <h3 className="mt-4 text-lg font-medium text-white">
        {hasDocuments ? 'No documents found' : 'No documents yet'}
      </h3>
      <p className="mt-2 text-sm text-secondary-400 max-w-sm">
        {hasDocuments
          ? 'Try adjusting your search query'
          : 'Upload your first document to get started with CogniFy'}
      </p>
    </div>
  )
}
