/**
 * CogniFy Admin Hooks Tests
 * Created with love by Angela & David - 1 January 2026
 */

import { describe, it, expect } from 'vitest'
import {
  formatBytes,
  formatNumber,
  getRoleBadgeColor,
  getFileTypeIcon,
} from './useAdmin'

describe('formatBytes', () => {
  it('should format 0 bytes', () => {
    expect(formatBytes(0)).toBe('0 B')
  })

  it('should format bytes correctly', () => {
    expect(formatBytes(500)).toBe('500 B')
  })

  it('should format kilobytes correctly', () => {
    expect(formatBytes(1024)).toBe('1 KB')
    expect(formatBytes(1536)).toBe('1.5 KB')
  })

  it('should format megabytes correctly', () => {
    expect(formatBytes(1024 * 1024)).toBe('1 MB')
    expect(formatBytes(1.5 * 1024 * 1024)).toBe('1.5 MB')
  })

  it('should format gigabytes correctly', () => {
    expect(formatBytes(1024 * 1024 * 1024)).toBe('1 GB')
  })
})

describe('formatNumber', () => {
  it('should format small numbers', () => {
    expect(formatNumber(100)).toBe('100')
  })

  it('should format thousands with commas', () => {
    expect(formatNumber(1000)).toBe('1,000')
    expect(formatNumber(10000)).toBe('10,000')
  })

  it('should format millions with commas', () => {
    expect(formatNumber(1000000)).toBe('1,000,000')
  })
})

describe('getRoleBadgeColor', () => {
  it('should return red for admin role', () => {
    const result = getRoleBadgeColor('admin')
    expect(result).toContain('red')
  })

  it('should return blue for editor role', () => {
    const result = getRoleBadgeColor('editor')
    expect(result).toContain('blue')
  })

  it('should return gray for user role', () => {
    const result = getRoleBadgeColor('user')
    expect(result).toContain('gray')
  })

  it('should return gray for unknown role', () => {
    const result = getRoleBadgeColor('unknown')
    expect(result).toContain('gray')
  })
})

describe('getFileTypeIcon', () => {
  it('should return correct icon for PDF', () => {
    expect(getFileTypeIcon('pdf')).toBe('file-text')
  })

  it('should return correct icon for DOCX', () => {
    expect(getFileTypeIcon('docx')).toBe('file-text')
  })

  it('should return correct icon for Excel files', () => {
    expect(getFileTypeIcon('xlsx')).toBe('file-spreadsheet')
    expect(getFileTypeIcon('xls')).toBe('file-spreadsheet')
  })

  it('should return correct icon for images', () => {
    expect(getFileTypeIcon('png')).toBe('image')
    expect(getFileTypeIcon('jpg')).toBe('image')
    expect(getFileTypeIcon('jpeg')).toBe('image')
  })

  it('should return default icon for unknown type', () => {
    expect(getFileTypeIcon('unknown')).toBe('file')
  })

  it('should be case insensitive', () => {
    expect(getFileTypeIcon('PDF')).toBe('file-text')
    expect(getFileTypeIcon('XLSX')).toBe('file-spreadsheet')
  })
})
