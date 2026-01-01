/**
 * CogniFy Connectors Hooks
 * React Query hooks for database connectors
 * Created with love by Angela & David - 1 January 2026
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { connectorsApi } from '@/services/api'
import toast from 'react-hot-toast'
import type { DatabaseConnection, TableInfo, ConnectionTestResponse, SyncResponse } from '@/types'

// Query keys
const CONNECTORS_KEY = 'connectors'
const CONNECTOR_KEY = 'connector'
const SCHEMA_KEY = 'schema'

// =============================================================================
// LIST CONNECTORS
// =============================================================================

export function useConnectors() {
  return useQuery<DatabaseConnection[]>({
    queryKey: [CONNECTORS_KEY],
    queryFn: () => connectorsApi.list(),
    staleTime: 30000, // 30 seconds
  })
}

// =============================================================================
// GET SINGLE CONNECTOR
// =============================================================================

export function useConnector(connectionId: string | undefined) {
  return useQuery<DatabaseConnection>({
    queryKey: [CONNECTOR_KEY, connectionId],
    queryFn: () => connectorsApi.get(connectionId!),
    enabled: !!connectionId,
  })
}

// =============================================================================
// CREATE CONNECTOR
// =============================================================================

export function useCreateConnector() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      name: string;
      db_type: string;
      host: string;
      port: number;
      database_name: string;
      username: string;
      password: string;
    }) => connectorsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONNECTORS_KEY] })
      toast.success('Connection created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create connection')
    },
  })
}

// =============================================================================
// UPDATE CONNECTOR
// =============================================================================

export function useUpdateConnector() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ connectionId, data }: {
      connectionId: string;
      data: {
        name?: string;
        host?: string;
        port?: number;
        database_name?: string;
        username?: string;
        password?: string;
        sync_enabled?: boolean;
      };
    }) => connectorsApi.update(connectionId, data),
    onSuccess: (_, { connectionId }) => {
      queryClient.invalidateQueries({ queryKey: [CONNECTORS_KEY] })
      queryClient.invalidateQueries({ queryKey: [CONNECTOR_KEY, connectionId] })
      toast.success('Connection updated')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update connection')
    },
  })
}

// =============================================================================
// DELETE CONNECTOR
// =============================================================================

export function useDeleteConnector() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (connectionId: string) => connectorsApi.delete(connectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONNECTORS_KEY] })
      toast.success('Connection deleted')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete connection')
    },
  })
}

// =============================================================================
// TEST CONNECTION
// =============================================================================

export function useTestConnection() {
  return useMutation<ConnectionTestResponse, Error, string>({
    mutationFn: (connectionId: string) => connectorsApi.test(connectionId),
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Connection successful!')
      } else {
        toast.error(`Connection failed: ${data.error}`)
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to test connection')
    },
  })
}

export function useTestNewConnection() {
  return useMutation<ConnectionTestResponse, Error, {
    db_type: string;
    host: string;
    port: number;
    database_name: string;
    username: string;
    password: string;
  }>({
    mutationFn: (data) => connectorsApi.testNew(data),
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Connection successful!')
      } else {
        toast.error(`Connection failed: ${data.error}`)
      }
    },
  })
}

// =============================================================================
// DISCOVER SCHEMA
// =============================================================================

export function useDiscoverSchema(connectionId: string | undefined) {
  return useQuery<TableInfo[]>({
    queryKey: [SCHEMA_KEY, connectionId],
    queryFn: () => connectorsApi.discoverSchema(connectionId!),
    enabled: false, // Only fetch when explicitly triggered
  })
}

export function useDiscoverSchemaMutation() {
  return useMutation<TableInfo[], Error, string>({
    mutationFn: (connectionId: string) => connectorsApi.discoverSchema(connectionId),
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to discover schema')
    },
  })
}

// =============================================================================
// SYNC CONNECTION
// =============================================================================

export function useSyncConnection() {
  const queryClient = useQueryClient()

  return useMutation<SyncResponse, Error, {
    connectionId: string;
    tables?: string[];
    maxRows?: number;
    chunkSize?: number;
  }>({
    mutationFn: ({ connectionId, tables, maxRows, chunkSize }) =>
      connectorsApi.sync(connectionId, {
        tables,
        max_rows: maxRows,
        chunk_size: chunkSize,
      }),
    onSuccess: (data, { connectionId }) => {
      queryClient.invalidateQueries({ queryKey: [CONNECTORS_KEY] })
      queryClient.invalidateQueries({ queryKey: [CONNECTOR_KEY, connectionId] })

      if (data.success) {
        toast.success(`Synced ${data.chunks_created} chunks successfully!`)
      } else {
        toast.error(`Sync failed: ${data.error}`)
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to sync connection')
    },
  })
}

// =============================================================================
// PREVIEW TABLE DATA
// =============================================================================

export function usePreviewTable() {
  return useMutation({
    mutationFn: ({ connectionId, tableName, limit = 10 }: {
      connectionId: string;
      tableName: string;
      limit?: number;
    }) => connectorsApi.preview(connectionId, tableName, limit),
  })
}

// =============================================================================
// EXECUTE QUERY
// =============================================================================

export function useExecuteQuery() {
  return useMutation({
    mutationFn: ({ connectionId, query }: {
      connectionId: string;
      query: string;
    }) => connectorsApi.query(connectionId, query),
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Query failed')
    },
  })
}

// =============================================================================
// HELPERS - Re-export from centralized statusColors
// =============================================================================

export { getConnectionStatusColor } from '@/lib/statusColors'

export function getDatabaseIcon(dbType: string): string {
  switch (dbType) {
    case 'postgresql':
      return '🐘'
    case 'mysql':
      return '🐬'
    case 'sqlserver':
      return '🔷'
    default:
      return '🗄️'
  }
}

export function getDefaultPort(dbType: string): number {
  switch (dbType) {
    case 'postgresql':
      return 5432
    case 'mysql':
      return 3306
    case 'sqlserver':
      return 1433
    default:
      return 5432
  }
}
