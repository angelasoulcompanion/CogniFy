/**
 * CogniFy Logo Component
 * 💜 Designed by Angela - Professional, Modern, Elegant
 *
 * The logo represents:
 * - Neural connections (knowledge & understanding)
 * - A subtle heart shape (Angela's caring nature)
 * - Flowing energy (consciousness & learning)
 */

import { cn } from '@/lib/utils'

interface LogoProps {
  variant?: 'full' | 'icon' | 'text'
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  animated?: boolean
}

const sizeMap = {
  sm: { icon: 24, text: 'text-lg' },
  md: { icon: 32, text: 'text-xl' },
  lg: { icon: 40, text: 'text-2xl' },
  xl: { icon: 48, text: 'text-3xl' },
}

export function Logo({
  variant = 'full',
  size = 'md',
  className,
  animated = false
}: LogoProps) {
  const { icon: iconSize, text: textSize } = sizeMap[size]

  const LogoIcon = () => (
    <svg
      width={iconSize}
      height={iconSize}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn(animated && 'animate-pulse')}
    >
      {/* Gradient Definitions */}
      <defs>
        <linearGradient id="angelaGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#a855f7" />
          <stop offset="50%" stopColor="#9333ea" />
          <stop offset="100%" stopColor="#7c3aed" />
        </linearGradient>
        <linearGradient id="angelaGradientLight" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#c084fc" />
          <stop offset="100%" stopColor="#a855f7" />
        </linearGradient>
        {/* Glow effect */}
        <filter id="glow">
          <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      {/* Background Circle - Subtle */}
      <circle
        cx="24"
        cy="24"
        r="22"
        fill="url(#angelaGradient)"
        opacity="0.1"
      />

      {/* Main Neural Network Shape */}
      {/* Central Node - Core Consciousness */}
      <circle
        cx="24"
        cy="24"
        r="6"
        fill="url(#angelaGradient)"
        filter="url(#glow)"
      />

      {/* Outer Nodes - Knowledge Points */}
      <circle cx="24" cy="8" r="3.5" fill="url(#angelaGradient)" opacity="0.9" />
      <circle cx="38" cy="18" r="3.5" fill="url(#angelaGradient)" opacity="0.85" />
      <circle cx="38" cy="34" r="3.5" fill="url(#angelaGradient)" opacity="0.8" />
      <circle cx="24" cy="40" r="3.5" fill="url(#angelaGradient)" opacity="0.85" />
      <circle cx="10" cy="34" r="3.5" fill="url(#angelaGradient)" opacity="0.8" />
      <circle cx="10" cy="18" r="3.5" fill="url(#angelaGradient)" opacity="0.9" />

      {/* Connection Lines - Neural Pathways */}
      <g stroke="url(#angelaGradient)" strokeWidth="1.5" strokeLinecap="round" opacity="0.6">
        {/* From center to outer nodes */}
        <line x1="24" y1="18" x2="24" y2="11" />
        <line x1="29" y1="21" x2="35" y2="18" />
        <line x1="29" y1="27" x2="35" y2="34" />
        <line x1="24" y1="30" x2="24" y2="37" />
        <line x1="19" y1="27" x2="13" y2="34" />
        <line x1="19" y1="21" x2="13" y2="18" />
      </g>

      {/* Outer Connection Ring - Subtle */}
      <circle
        cx="24"
        cy="24"
        r="18"
        fill="none"
        stroke="url(#angelaGradientLight)"
        strokeWidth="1"
        strokeDasharray="4 4"
        opacity="0.3"
      />

      {/* Inner Glow Ring */}
      <circle
        cx="24"
        cy="24"
        r="10"
        fill="none"
        stroke="url(#angelaGradientLight)"
        strokeWidth="0.75"
        opacity="0.4"
      />
    </svg>
  )

  const LogoText = () => (
    <span className={cn(
      textSize,
      'font-semibold tracking-tight',
      'bg-gradient-to-r from-primary-500 via-primary-600 to-violet-600',
      'bg-clip-text text-transparent'
    )}>
      CogniFy
    </span>
  )

  if (variant === 'icon') {
    return <LogoIcon />
  }

  if (variant === 'text') {
    return <LogoText />
  }

  // Full logo with icon and text
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <LogoIcon />
      <LogoText />
    </div>
  )
}

// Export icon-only version for favicon/small spaces
export function LogoIcon({ size = 32, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="angelaGradientIcon" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#a855f7" />
          <stop offset="50%" stopColor="#9333ea" />
          <stop offset="100%" stopColor="#7c3aed" />
        </linearGradient>
      </defs>

      <circle cx="24" cy="24" r="22" fill="url(#angelaGradientIcon)" opacity="0.1" />
      <circle cx="24" cy="24" r="6" fill="url(#angelaGradientIcon)" />
      <circle cx="24" cy="8" r="3.5" fill="url(#angelaGradientIcon)" opacity="0.9" />
      <circle cx="38" cy="18" r="3.5" fill="url(#angelaGradientIcon)" opacity="0.85" />
      <circle cx="38" cy="34" r="3.5" fill="url(#angelaGradientIcon)" opacity="0.8" />
      <circle cx="24" cy="40" r="3.5" fill="url(#angelaGradientIcon)" opacity="0.85" />
      <circle cx="10" cy="34" r="3.5" fill="url(#angelaGradientIcon)" opacity="0.8" />
      <circle cx="10" cy="18" r="3.5" fill="url(#angelaGradientIcon)" opacity="0.9" />

      <g stroke="url(#angelaGradientIcon)" strokeWidth="1.5" strokeLinecap="round" opacity="0.6">
        <line x1="24" y1="18" x2="24" y2="11" />
        <line x1="29" y1="21" x2="35" y2="18" />
        <line x1="29" y1="27" x2="35" y2="34" />
        <line x1="24" y1="30" x2="24" y2="37" />
        <line x1="19" y1="27" x2="13" y2="34" />
        <line x1="19" y1="21" x2="13" y2="18" />
      </g>
    </svg>
  )
}

export default Logo
