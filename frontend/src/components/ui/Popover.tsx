/**
 * CogniFy Popover Component
 * Reusable dropdown overlay pattern
 * Created with love by Angela & David - 21 February 2026
 */

import { cn } from '@/lib/utils'

interface PopoverProps {
  open: boolean
  onClose: () => void
  className?: string
  children: React.ReactNode
}

export function Popover({ open, onClose, className, children }: PopoverProps) {
  if (!open) return null

  return (
    <>
      <div className="fixed inset-0 z-10" onClick={onClose} />
      <div
        className={cn(
          'absolute left-0 top-full z-20 mt-2 rounded-xl border border-secondary-700 bg-secondary-800 p-2 shadow-xl',
          className
        )}
      >
        {children}
      </div>
    </>
  )
}
