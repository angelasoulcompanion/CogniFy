/**
 * CogniFy Button Component
 * Reusable button with variants following Angela Purple Theme
 * Created with love by Angela & David - 1 January 2026
 */

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'
export type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  icon?: ReactNode
  iconPosition?: 'left' | 'right'
  isLoading?: boolean
  loadingText?: string
  fullWidth?: boolean
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-gradient-to-r from-primary-600 to-violet-600 text-white hover:from-primary-500 hover:to-violet-500 shadow-lg shadow-primary-500/25',
  secondary: 'border border-secondary-700 text-secondary-300 hover:bg-secondary-800 hover:text-white',
  danger: 'border border-red-500/30 text-red-400 hover:bg-red-500/20',
  ghost: 'text-secondary-400 hover:bg-secondary-700 hover:text-white',
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs rounded-lg gap-1.5',
  md: 'px-4 py-2 text-sm rounded-xl gap-2',
  lg: 'px-6 py-3 text-base rounded-xl gap-2',
}

const iconSizes: Record<ButtonSize, string> = {
  sm: 'h-3.5 w-3.5',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      icon,
      iconPosition = 'left',
      isLoading = false,
      loadingText,
      fullWidth = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading

    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center font-medium transition-all',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          variantStyles[variant],
          sizeStyles[size],
          fullWidth && 'w-full',
          className
        )}
        disabled={isDisabled}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2 className={cn('animate-spin', iconSizes[size])} />
            {loadingText || children}
          </>
        ) : (
          <>
            {icon && iconPosition === 'left' && (
              <span className={iconSizes[size]}>{icon}</span>
            )}
            {children}
            {icon && iconPosition === 'right' && (
              <span className={iconSizes[size]}>{icon}</span>
            )}
          </>
        )}
      </button>
    )
  }
)

Button.displayName = 'Button'

export default Button
