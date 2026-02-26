/**
 * CogniFy Dropdown Menu Component
 * Shared floating context menu triggered by a button
 * Created with love by Angela & David
 */

import { useState, type ReactNode } from 'react'
import { MoreVertical } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DropdownMenuProps {
  trigger?: ReactNode
  children: ReactNode
  width?: string
}

export function DropdownMenu({ trigger, children, width = 'w-40' }: DropdownMenuProps) {
  const [open, setOpen] = useState(false)

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="rounded-lg p-2 text-secondary-400 hover:bg-secondary-700 hover:text-white"
      >
        {trigger || <MoreVertical className="h-4 w-4" />}
      </button>
      {open && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setOpen(false)}
          />
          <div className={cn(
            'absolute right-0 top-full z-20 mt-1 rounded-lg border border-secondary-700 bg-secondary-800 py-1 shadow-lg',
            width
          )}>
            {typeof children === 'function'
              ? (children as (close: () => void) => ReactNode)(() => setOpen(false))
              : children}
          </div>
        </>
      )}
    </div>
  )
}

interface DropdownItemProps {
  onClick: () => void
  disabled?: boolean
  variant?: 'default' | 'danger'
  icon?: ReactNode
  children: ReactNode
}

export function DropdownItem({ onClick, disabled, variant = 'default', icon, children }: DropdownItemProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'flex w-full items-center gap-2 px-4 py-2 text-left text-sm disabled:opacity-50',
        variant === 'danger'
          ? 'text-red-400 hover:bg-red-500/20'
          : 'text-secondary-300 hover:bg-secondary-700'
      )}
    >
      {icon}
      {children}
    </button>
  )
}
