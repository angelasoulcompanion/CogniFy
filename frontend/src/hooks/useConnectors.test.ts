/**
 * CogniFy Connectors Hooks Tests
 * Created with love by Angela & David - 1 January 2026
 */

import { describe, it, expect } from 'vitest'
import {
  getConnectionStatusColor,
  getDatabaseIcon,
  getDefaultPort,
} from './useConnectors'

describe('getConnectionStatusColor', () => {
  it('should return green for completed status', () => {
    const result = getConnectionStatusColor('completed')
    expect(result).toContain('green')
  })

  it('should return blue for syncing status', () => {
    const result = getConnectionStatusColor('syncing')
    expect(result).toContain('blue')
  })

  it('should return yellow for pending status', () => {
    const result = getConnectionStatusColor('pending')
    expect(result).toContain('yellow')
  })

  it('should return red for failed status', () => {
    const result = getConnectionStatusColor('failed')
    expect(result).toContain('red')
  })

  it('should return gray for null status', () => {
    const result = getConnectionStatusColor(null)
    expect(result).toContain('gray')
  })
})

describe('getDatabaseIcon', () => {
  it('should return elephant for PostgreSQL', () => {
    expect(getDatabaseIcon('postgresql')).toBe('elephant')
  })

  it('should return dolphin for MySQL', () => {
    expect(getDatabaseIcon('mysql')).toBe('dolphin')
  })

  it('should return server for SQL Server', () => {
    expect(getDatabaseIcon('sqlserver')).toBe('server')
  })

  it('should return database for unknown type', () => {
    expect(getDatabaseIcon('unknown' as any)).toBe('database')
  })
})

describe('getDefaultPort', () => {
  it('should return 5432 for PostgreSQL', () => {
    expect(getDefaultPort('postgresql')).toBe(5432)
  })

  it('should return 3306 for MySQL', () => {
    expect(getDefaultPort('mysql')).toBe(3306)
  })

  it('should return 1433 for SQL Server', () => {
    expect(getDefaultPort('sqlserver')).toBe(1433)
  })

  it('should return 5432 as default for unknown type', () => {
    expect(getDefaultPort('unknown' as any)).toBe(5432)
  })
})
