/**
 * CogniFy Input Component
 * Reusable input with variants following Angela Purple Theme
 * Created with love by Angela & David - 1 January 2026
 */

import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react'
import { Search } from 'lucide-react'
import { cn } from '@/lib/utils'

export type InputVariant = 'default' | 'filled'
export type InputSize = 'sm' | 'md' | 'lg'

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  variant?: InputVariant
  inputSize?: InputSize
  icon?: ReactNode
  iconPosition?: 'left' | 'right'
  error?: string
  fullWidth?: boolean
}

const baseStyles = 'border bg-secondary-800/50 text-white placeholder-secondary-500 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-colors'

const variantStyles: Record<InputVariant, string> = {
  default: 'border-secondary-700',
  filled: 'border-secondary-600 bg-secondary-700/50',
}

const sizeStyles: Record<InputSize, string> = {
  sm: 'px-3 py-1.5 text-sm rounded-lg',
  md: 'px-4 py-2.5 text-sm rounded-xl',
  lg: 'px-5 py-3 text-base rounded-xl',
}

const iconPadding: Record<InputSize, { left: string; right: string }> = {
  sm: { left: 'pl-8', right: 'pr-8' },
  md: { left: 'pl-10', right: 'pr-10' },
  lg: { left: 'pl-12', right: 'pr-12' },
}

const iconPositionStyles: Record<InputSize, string> = {
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant = 'default',
      inputSize = 'md',
      icon,
      iconPosition = 'left',
      error,
      fullWidth = true,
      ...props
    },
    ref
  ) => {
    const hasIcon = !!icon

    return (
      <div className={cn('relative', fullWidth && 'w-full')}>
        {hasIcon && iconPosition === 'left' && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary-500">
            <span className={iconPositionStyles[inputSize]}>{icon}</span>
          </div>
        )}
        <input
          ref={ref}
          className={cn(
            baseStyles,
            variantStyles[variant],
            sizeStyles[inputSize],
            fullWidth && 'w-full',
            hasIcon && iconPosition === 'left' && iconPadding[inputSize].left,
            hasIcon && iconPosition === 'right' && iconPadding[inputSize].right,
            error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
            className
          )}
          {...props}
        />
        {hasIcon && iconPosition === 'right' && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary-500">
            <span className={iconPositionStyles[inputSize]}>{icon}</span>
          </div>
        )}
        {error && (
          <p className="mt-1 text-sm text-red-400">{error}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

// =============================================================================
// SEARCH INPUT - Pre-configured variant
// =============================================================================

export interface SearchInputProps extends Omit<InputProps, 'icon' | 'iconPosition'> {
  onSearch?: (value: string) => void
}

export const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  ({ placeholder = 'Search...', ...props }, ref) => {
    return (
      <Input
        ref={ref}
        icon={<Search className="h-5 w-5" />}
        iconPosition="left"
        placeholder={placeholder}
        {...props}
      />
    )
  }
)

SearchInput.displayName = 'SearchInput'

export default Input
