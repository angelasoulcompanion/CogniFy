/**
 * CogniFy Badge Component
 * Reusable badge with variants following Angela Purple Theme
 * Created with love by Angela & David - 1 January 2026
 */

import { type HTMLAttributes, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

export type BadgeVariant =
  | 'default'
  | 'success'
  | 'warning'
  | 'error'
  | 'info'
  | 'purple'
  | 'outline'

export type BadgeSize = 'sm' | 'md' | 'lg'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  size?: BadgeSize
  icon?: ReactNode
  dot?: boolean
  pulse?: boolean
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-secondary-700/50 text-secondary-300',
  success: 'bg-green-500/20 text-green-400',
  warning: 'bg-yellow-500/20 text-yellow-400',
  error: 'bg-red-500/20 text-red-400',
  info: 'bg-blue-500/20 text-blue-400',
  purple: 'bg-purple-500/20 text-purple-400',
  outline: 'border border-secondary-600 text-secondary-300 bg-transparent',
}

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
  lg: 'px-3 py-1.5 text-sm',
}

const dotSizes: Record<BadgeSize, string> = {
  sm: 'h-1.5 w-1.5',
  md: 'h-2 w-2',
  lg: 'h-2.5 w-2.5',
}

const dotColors: Record<BadgeVariant, string> = {
  default: 'bg-secondary-400',
  success: 'bg-green-400',
  warning: 'bg-yellow-400',
  error: 'bg-red-400',
  info: 'bg-blue-400',
  purple: 'bg-purple-400',
  outline: 'bg-secondary-400',
}

export function Badge({
  variant = 'default',
  size = 'md',
  icon,
  dot = false,
  pulse = false,
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-medium',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {dot && (
        <span className="relative flex">
          <span
            className={cn('rounded-full', dotSizes[size], dotColors[variant])}
          />
          {pulse && (
            <span
              className={cn(
                'absolute inline-flex h-full w-full animate-ping rounded-full opacity-75',
                dotColors[variant]
              )}
            />
          )}
        </span>
      )}
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </span>
  )
}

// =============================================================================
// STATUS BADGE - Pre-configured for common statuses
// =============================================================================

export type StatusType =
  | 'pending'
  | 'processing'
  | 'syncing'
  | 'completed'
  | 'success'
  | 'failed'
  | 'error'
  | 'active'
  | 'inactive'

const statusToVariant: Record<StatusType, BadgeVariant> = {
  pending: 'warning',
  processing: 'info',
  syncing: 'info',
  completed: 'success',
  success: 'success',
  failed: 'error',
  error: 'error',
  active: 'success',
  inactive: 'default',
}

const statusLabels: Record<StatusType, string> = {
  pending: 'Pending',
  processing: 'Processing',
  syncing: 'Syncing',
  completed: 'Completed',
  success: 'Success',
  failed: 'Failed',
  error: 'Error',
  active: 'Active',
  inactive: 'Inactive',
}

export interface StatusBadgeProps extends Omit<BadgeProps, 'variant'> {
  status: StatusType | string
  showDot?: boolean
  showPulse?: boolean
  customLabel?: string
}

export function StatusBadge({
  status,
  showDot = true,
  showPulse = false,
  customLabel,
  ...props
}: StatusBadgeProps) {
  const normalizedStatus = status.toLowerCase() as StatusType
  const variant = statusToVariant[normalizedStatus] || 'default'
  const label = customLabel || statusLabels[normalizedStatus] || status
  const shouldPulse =
    showPulse || normalizedStatus === 'processing' || normalizedStatus === 'syncing'

  return (
    <Badge variant={variant} dot={showDot} pulse={shouldPulse} {...props}>
      {label}
    </Badge>
  )
}

// =============================================================================
// ROLE BADGE - For user roles
// =============================================================================

export type RoleType = 'admin' | 'editor' | 'user'

const roleToVariant: Record<RoleType, BadgeVariant> = {
  admin: 'error',
  editor: 'info',
  user: 'default',
}

const roleLabels: Record<RoleType, string> = {
  admin: 'Admin',
  editor: 'Editor',
  user: 'User',
}

export interface RoleBadgeProps extends Omit<BadgeProps, 'variant'> {
  role: RoleType | string
}

export function RoleBadge({ role, ...props }: RoleBadgeProps) {
  const normalizedRole = role.toLowerCase() as RoleType
  const variant = roleToVariant[normalizedRole] || 'default'
  const label = roleLabels[normalizedRole] || role

  return (
    <Badge variant={variant} {...props}>
      {label}
    </Badge>
  )
}

// =============================================================================
// EXPORTS
// =============================================================================

Badge.Status = StatusBadge
Badge.Role = RoleBadge

export default Badge
