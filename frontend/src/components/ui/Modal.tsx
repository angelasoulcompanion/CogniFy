/**
 * CogniFy Modal Component
 * Reusable modal with compound components following Angela Purple Theme
 * Created with love by Angela & David - 1 January 2026
 */

import { createContext, useContext, type ReactNode, type HTMLAttributes } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

// =============================================================================
// MODAL CONTEXT
// =============================================================================

interface ModalContextValue {
  onClose: () => void
}

const ModalContext = createContext<ModalContextValue | undefined>(undefined)

function useModalContext() {
  const context = useContext(ModalContext)
  if (!context) {
    throw new Error('Modal compound components must be used within Modal')
  }
  return context
}

// =============================================================================
// MODAL ROOT
// =============================================================================

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  size?: ModalSize
  children: ReactNode
  closeOnOverlayClick?: boolean
}

const sizeStyles: Record<ModalSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-3xl',
  xl: 'max-w-5xl',
  full: 'max-w-[90vw]',
}

export function Modal({
  isOpen,
  onClose,
  size = 'md',
  children,
  closeOnOverlayClick = true,
}: ModalProps) {
  if (!isOpen) return null

  return (
    <ModalContext.Provider value={{ onClose }}>
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        {/* Overlay */}
        <div
          className="absolute inset-0 bg-black/70"
          onClick={closeOnOverlayClick ? onClose : undefined}
        />
        {/* Modal Container */}
        <div
          className={cn(
            'relative w-full rounded-xl bg-secondary-900 border border-secondary-700 shadow-xl',
            sizeStyles[size]
          )}
        >
          {children}
        </div>
      </div>
    </ModalContext.Provider>
  )
}

// =============================================================================
// MODAL HEADER
// =============================================================================

export interface ModalHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title: string
  subtitle?: string
  showCloseButton?: boolean
}

export function ModalHeader({
  title,
  subtitle,
  showCloseButton = true,
  className,
  children,
  ...props
}: ModalHeaderProps) {
  const { onClose } = useModalContext()

  return (
    <div
      className={cn(
        'flex items-center justify-between p-6 border-b border-secondary-700',
        className
      )}
      {...props}
    >
      <div>
        <h2 className="text-xl font-semibold text-white">{title}</h2>
        {subtitle && (
          <p className="text-sm text-secondary-400 mt-1">{subtitle}</p>
        )}
      </div>
      <div className="flex items-center gap-2">
        {children}
        {showCloseButton && (
          <button
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-secondary-800 transition-colors"
          >
            <X className="h-5 w-5 text-secondary-400" />
          </button>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// MODAL CONTENT
// =============================================================================

export interface ModalContentProps extends HTMLAttributes<HTMLDivElement> {
  noPadding?: boolean
  scrollable?: boolean
  maxHeight?: string
}

export function ModalContent({
  noPadding = false,
  scrollable = false,
  maxHeight = 'max-h-[60vh]',
  className,
  children,
  ...props
}: ModalContentProps) {
  return (
    <div
      className={cn(
        !noPadding && 'p-6',
        scrollable && `overflow-y-auto ${maxHeight}`,
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

// =============================================================================
// MODAL FOOTER
// =============================================================================

export interface ModalFooterProps extends HTMLAttributes<HTMLDivElement> {
  align?: 'left' | 'center' | 'right' | 'between'
}

const alignStyles: Record<string, string> = {
  left: 'justify-start',
  center: 'justify-center',
  right: 'justify-end',
  between: 'justify-between',
}

export function ModalFooter({
  align = 'right',
  className,
  children,
  ...props
}: ModalFooterProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 p-6 border-t border-secondary-700',
        alignStyles[align],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

// =============================================================================
// EXPORTS
// =============================================================================

Modal.Header = ModalHeader
Modal.Content = ModalContent
Modal.Footer = ModalFooter

export default Modal
