/**
 * CogniFy Utils Tests
 * Created with love by Angela & David - 1 January 2026
 */

import { describe, it, expect } from 'vitest'
import { cn } from './utils'

describe('cn utility function', () => {
  it('should merge class names', () => {
    const result = cn('class1', 'class2')
    expect(result).toBe('class1 class2')
  })

  it('should handle conditional classes', () => {
    const result = cn('base', true && 'included', false && 'excluded')
    expect(result).toContain('base')
    expect(result).toContain('included')
    expect(result).not.toContain('excluded')
  })

  it('should handle undefined values', () => {
    const result = cn('base', undefined, 'other')
    expect(result).toBe('base other')
  })

  it('should handle empty strings', () => {
    const result = cn('base', '', 'other')
    expect(result).toBe('base other')
  })

  it('should merge tailwind classes correctly', () => {
    const result = cn('p-4', 'p-2')
    expect(result).toBe('p-2')
  })

  it('should handle arrays of classes', () => {
    const result = cn(['class1', 'class2'], 'class3')
    expect(result).toContain('class1')
    expect(result).toContain('class2')
    expect(result).toContain('class3')
  })
})
