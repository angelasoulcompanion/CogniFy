/**
 * CogniFy Documents Hooks Tests
 * Created with love by Angela & David - 1 January 2026
 */

import { describe, it, expect } from 'vitest'
import {
  getDocumentStatusLabel,
  getDocumentStatusColor,
} from './useDocuments'

describe('getDocumentStatusLabel', () => {
  it('should return correct label for pending status', () => {
    expect(getDocumentStatusLabel('pending')).toBe('Pending')
  })

  it('should return correct label for processing status', () => {
    expect(getDocumentStatusLabel('processing')).toBe('Processing')
  })

  it('should return correct label for completed status', () => {
    expect(getDocumentStatusLabel('completed')).toBe('Completed')
  })

  it('should return correct label for failed status', () => {
    expect(getDocumentStatusLabel('failed')).toBe('Failed')
  })

  it('should return Unknown for unknown status', () => {
    expect(getDocumentStatusLabel('unknown' as any)).toBe('Unknown')
  })
})

describe('getDocumentStatusColor', () => {
  it('should return yellow for pending status', () => {
    const result = getDocumentStatusColor('pending')
    expect(result).toContain('yellow')
  })

  it('should return blue for processing status', () => {
    const result = getDocumentStatusColor('processing')
    expect(result).toContain('blue')
  })

  it('should return green for completed status', () => {
    const result = getDocumentStatusColor('completed')
    expect(result).toContain('green')
  })

  it('should return red for failed status', () => {
    const result = getDocumentStatusColor('failed')
    expect(result).toContain('red')
  })

  it('should return gray for unknown status', () => {
    const result = getDocumentStatusColor('unknown' as any)
    expect(result).toContain('gray')
  })
})
