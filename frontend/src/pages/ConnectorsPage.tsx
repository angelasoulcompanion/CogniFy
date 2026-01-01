/**
 * CogniFy Connectors Page
 * Database connector management interface
 * Created with love by Angela & David - 1 January 2026
 */

import { useState, FormEvent } from 'react'
import {
  useConnectors,
  useCreateConnector,
  useDeleteConnector,
  useTestConnection,
  useTestNewConnection,
  useSyncConnection,
  useDiscoverSchemaMutation,
  getConnectionStatusColor,
  getDatabaseIcon,
  getDefaultPort,
} from '@/hooks/useConnectors'
import { formatRelativeTime } from '@/lib/utils'
import { cn } from '@/lib/utils'
import type { DatabaseConnection, DatabaseType, TableInfo } from '@/types'
import {
  Database,
  Plus,
  RefreshCw,
  Trash2,
  Eye,
  X,
  Loader2,
  Server,
  Table,
  MoreVertical,
  ChevronDown,
  ChevronRight,
  Zap,
  AlertCircle,
} from 'lucide-react'

export function ConnectorsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedConnection, setSelectedConnection] = useState<DatabaseConnection | null>(null)
  const [showSchemaModal, setShowSchemaModal] = useState(false)

  const { data: connections, isLoading, refetch } = useConnectors()

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <header className="flex h-16 items-center justify-between border-b border-primary-500/10 bg-secondary-900/50 backdrop-blur-sm px-6">
        <div>
          <h1 className="text-xl font-semibold text-white">Database Connectors</h1>
          <p className="text-sm text-secondary-400">
            {connections?.length || 0} connection{connections?.length !== 1 ? 's' : ''} configured
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 rounded-xl border border-secondary-700 px-3 py-2 text-sm text-secondary-300 hover:bg-secondary-800 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary-600 to-violet-600 px-4 py-2 text-sm font-medium text-white hover:from-primary-500 hover:to-violet-500 transition-all shadow-lg shadow-primary-500/25"
          >
            <Plus className="h-4 w-4" />
            Add Connection
          </button>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-5xl">
          {/* Info Banner */}
          <div className="mb-6 rounded-xl border border-primary-500/30 bg-primary-900/30 p-4">
            <div className="flex items-start gap-3">
              <Database className="h-5 w-5 text-primary-400 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-primary-200">
                  Connect to External Databases
                </p>
                <p className="mt-1 text-sm text-primary-300/80">
                  Import data from PostgreSQL, MySQL, or SQL Server databases into CogniFy for RAG-powered search.
                </p>
              </div>
            </div>
          </div>

          {/* Connections List */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-secondary-400" />
            </div>
          ) : connections?.length === 0 ? (
            <EmptyState onAdd={() => setShowCreateModal(true)} />
          ) : (
            <div className="space-y-4">
              {connections?.map((connection) => (
                <ConnectionCard
                  key={connection.connection_id}
                  connection={connection}
                  onViewSchema={() => {
                    setSelectedConnection(connection)
                    setShowSchemaModal(true)
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <CreateConnectionModal onClose={() => setShowCreateModal(false)} />
      )}

      {/* Schema Modal */}
      {showSchemaModal && selectedConnection && (
        <SchemaModal
          connection={selectedConnection}
          onClose={() => {
            setShowSchemaModal(false)
            setSelectedConnection(null)
          }}
        />
      )}
    </div>
  )
}

// =============================================================================
// CONNECTION CARD COMPONENT
// =============================================================================

function ConnectionCard({
  connection,
  onViewSchema,
}: {
  connection: DatabaseConnection
  onViewSchema: () => void
}) {
  const [showMenu, setShowMenu] = useState(false)
  const deleteMutation = useDeleteConnector()
  const testMutation = useTestConnection()
  const syncMutation = useSyncConnection()

  const handleSync = () => {
    syncMutation.mutate({ connectionId: connection.connection_id })
  }

  const handleTest = () => {
    testMutation.mutate(connection.connection_id)
  }

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this connection?')) {
      deleteMutation.mutate(connection.connection_id)
    }
  }

  return (
    <div className="group rounded-xl border border-secondary-700/50 bg-secondary-800/50 p-5 transition-all hover:border-primary-500/30 hover:bg-secondary-800">
      <div className="flex items-start justify-between">
        {/* Left: Icon + Info */}
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-secondary-700/50 text-2xl">
            {getDatabaseIcon(connection.db_type)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-white">{connection.name}</h3>
              <span className="inline-flex items-center rounded-md bg-secondary-700 px-2 py-0.5 text-xs font-medium text-secondary-300 uppercase">
                {connection.db_type}
              </span>
            </div>
            <p className="mt-1 text-sm text-secondary-400">
              {connection.host}:{connection.port} / {connection.database_name}
            </p>
            <div className="mt-2 flex items-center gap-4 text-sm">
              <span className="text-secondary-500">
                User: <span className="text-secondary-300">{connection.username}</span>
              </span>
              {connection.last_sync_at && (
                <span className="text-secondary-500">
                  Last sync: {formatRelativeTime(connection.last_sync_at)}
                </span>
              )}
              {connection.total_chunks_synced > 0 && (
                <span className="text-secondary-500">
                  {connection.total_chunks_synced} chunks
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Right: Status + Actions */}
        <div className="flex items-center gap-3">
          {/* Status Badge */}
          {connection.last_sync_status && (
            <span
              className={cn(
                'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                getConnectionStatusColor(connection.last_sync_status)
              )}
            >
              {connection.last_sync_status}
            </span>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-1">
            <button
              onClick={handleTest}
              disabled={testMutation.isPending}
              className="rounded-lg p-2 text-secondary-400 hover:bg-secondary-700 hover:text-white disabled:opacity-50"
              title="Test connection"
            >
              {testMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Zap className="h-4 w-4" />
              )}
            </button>
            <button
              onClick={onViewSchema}
              className="rounded-lg p-2 text-secondary-400 hover:bg-secondary-700 hover:text-white"
              title="View schema"
            >
              <Eye className="h-4 w-4" />
            </button>
            <button
              onClick={handleSync}
              disabled={syncMutation.isPending}
              className="rounded-lg p-2 text-secondary-400 hover:bg-secondary-700 hover:text-white disabled:opacity-50"
              title="Sync to RAG"
            >
              {syncMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
            </button>

            {/* More Menu */}
            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="rounded-lg p-2 text-secondary-400 hover:bg-secondary-700 hover:text-white"
              >
                <MoreVertical className="h-4 w-4" />
              </button>
              {showMenu && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowMenu(false)}
                  />
                  <div className="absolute right-0 top-full z-20 mt-1 w-40 rounded-lg border border-secondary-700 bg-secondary-800 py-1 shadow-lg">
                    <button
                      onClick={() => {
                        setShowMenu(false)
                        handleDelete()
                      }}
                      disabled={deleteMutation.isPending}
                      className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-red-400 hover:bg-red-500/20"
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {connection.last_sync_error && (
        <div className="mt-3 flex items-center gap-2 rounded-lg bg-red-500/20 p-3 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{connection.last_sync_error}</span>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// CREATE CONNECTION MODAL
// =============================================================================

function CreateConnectionModal({ onClose }: { onClose: () => void }) {
  const [formData, setFormData] = useState({
    name: '',
    db_type: 'postgresql' as DatabaseType,
    host: 'localhost',
    port: 5432,
    database_name: '',
    username: '',
    password: '',
  })

  const createMutation = useCreateConnector()
  const testMutation = useTestNewConnection()

  const handleDbTypeChange = (dbType: DatabaseType) => {
    setFormData({
      ...formData,
      db_type: dbType,
      port: getDefaultPort(dbType),
    })
  }

  const handleTest = () => {
    testMutation.mutate(formData)
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData, {
      onSuccess: () => onClose(),
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="w-full max-w-lg rounded-xl bg-secondary-900 border border-secondary-700 p-6 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Add Database Connection</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-secondary-800"
          >
            <X className="h-5 w-5 text-secondary-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-secondary-300 mb-1">
              Connection Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="My Database"
              required
              className="w-full rounded-lg border border-secondary-700 bg-secondary-800 px-4 py-2.5 text-white placeholder-secondary-500 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
            />
          </div>

          {/* Database Type */}
          <div>
            <label className="block text-sm font-medium text-secondary-300 mb-2">
              Database Type
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(['postgresql', 'mysql', 'sqlserver'] as DatabaseType[]).map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => handleDbTypeChange(type)}
                  className={cn(
                    'flex items-center justify-center gap-2 rounded-lg border p-3 text-sm font-medium transition-colors',
                    formData.db_type === type
                      ? 'border-primary-500 bg-primary-500/20 text-primary-300'
                      : 'border-secondary-700 text-secondary-400 hover:bg-secondary-800'
                  )}
                >
                  <span className="text-lg">{getDatabaseIcon(type)}</span>
                  <span className="capitalize">{type === 'sqlserver' ? 'SQL Server' : type}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Host & Port */}
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-secondary-300 mb-1">
                Host
              </label>
              <input
                type="text"
                value={formData.host}
                onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                required
                className="w-full rounded-lg border border-secondary-700 bg-secondary-800 px-4 py-2.5 text-white focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-300 mb-1">
                Port
              </label>
              <input
                type="number"
                value={formData.port}
                onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) })}
                required
                className="w-full rounded-lg border border-secondary-700 bg-secondary-800 px-4 py-2.5 text-white focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
              />
            </div>
          </div>

          {/* Database Name */}
          <div>
            <label className="block text-sm font-medium text-secondary-300 mb-1">
              Database Name
            </label>
            <input
              type="text"
              value={formData.database_name}
              onChange={(e) => setFormData({ ...formData, database_name: e.target.value })}
              required
              className="w-full rounded-lg border border-secondary-700 bg-secondary-800 px-4 py-2.5 text-white focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
            />
          </div>

          {/* Username & Password */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-secondary-300 mb-1">
                Username
              </label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
                className="w-full rounded-lg border border-secondary-700 bg-secondary-800 px-4 py-2.5 text-white focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-300 mb-1">
                Password
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                className="w-full rounded-lg border border-secondary-700 bg-secondary-800 px-4 py-2.5 text-white focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-between pt-4">
            <button
              type="button"
              onClick={handleTest}
              disabled={testMutation.isPending}
              className="flex items-center gap-2 rounded-lg border border-secondary-700 px-4 py-2 text-sm font-medium text-secondary-300 hover:bg-secondary-800 disabled:opacity-50"
            >
              {testMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Zap className="h-4 w-4" />
              )}
              Test Connection
            </button>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg border border-secondary-700 px-4 py-2 text-sm font-medium text-secondary-300 hover:bg-secondary-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-primary-600 to-violet-600 px-4 py-2 text-sm font-medium text-white hover:from-primary-500 hover:to-violet-500 disabled:opacity-50"
              >
                {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Create Connection
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

// =============================================================================
// SCHEMA MODAL
// =============================================================================

function SchemaModal({
  connection,
  onClose,
}: {
  connection: DatabaseConnection
  onClose: () => void
}) {
  const [tables, setTables] = useState<TableInfo[]>([])
  const [expandedTable, setExpandedTable] = useState<string | null>(null)
  const [selectedTables, setSelectedTables] = useState<string[]>([])

  const schemaMutation = useDiscoverSchemaMutation()
  const syncMutation = useSyncConnection()

  const handleDiscover = () => {
    schemaMutation.mutate(connection.connection_id, {
      onSuccess: (data) => setTables(data),
    })
  }

  const handleSync = () => {
    syncMutation.mutate({
      connectionId: connection.connection_id,
      tables: selectedTables.length > 0 ? selectedTables : undefined,
    }, {
      onSuccess: () => onClose(),
    })
  }

  const toggleTable = (tableName: string) => {
    setSelectedTables(prev =>
      prev.includes(tableName)
        ? prev.filter(t => t !== tableName)
        : [...prev, tableName]
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="w-full max-w-3xl max-h-[80vh] rounded-xl bg-secondary-900 border border-secondary-700 shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-secondary-700">
          <div>
            <h2 className="text-xl font-semibold text-white">
              {connection.name} - Schema
            </h2>
            <p className="text-sm text-secondary-400 mt-1">
              {connection.host}:{connection.port}/{connection.database_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-secondary-800"
          >
            <X className="h-5 w-5 text-secondary-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {tables.length === 0 ? (
            <div className="text-center py-12">
              <Table className="h-12 w-12 text-secondary-600 mx-auto mb-4" />
              <p className="text-secondary-400 mb-4">Click "Discover Schema" to load tables</p>
              <button
                onClick={handleDiscover}
                disabled={schemaMutation.isPending}
                className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-primary-600 to-violet-600 px-4 py-2 text-sm font-medium text-white hover:from-primary-500 hover:to-violet-500 disabled:opacity-50"
              >
                {schemaMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Server className="h-4 w-4" />
                )}
                Discover Schema
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-secondary-400">
                  {tables.length} tables found. Select tables to sync.
                </p>
                <button
                  onClick={() => {
                    if (selectedTables.length === tables.length) {
                      setSelectedTables([])
                    } else {
                      setSelectedTables(tables.map(t => t.table_name))
                    }
                  }}
                  className="text-sm text-primary-400 hover:text-primary-300"
                >
                  {selectedTables.length === tables.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>

              {tables.map((table) => (
                <div
                  key={table.table_name}
                  className="border border-secondary-700 rounded-lg overflow-hidden"
                >
                  <div
                    className="flex items-center justify-between p-3 bg-secondary-800 cursor-pointer hover:bg-secondary-700"
                    onClick={() => setExpandedTable(
                      expandedTable === table.table_name ? null : table.table_name
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={selectedTables.includes(table.table_name)}
                        onChange={() => toggleTable(table.table_name)}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded border-secondary-600 bg-secondary-700 text-primary-500 focus:ring-primary-500"
                      />
                      <Table className="h-4 w-4 text-secondary-400" />
                      <span className="font-medium text-white">{table.table_name}</span>
                      <span className="text-sm text-secondary-400">
                        ({table.column_count} columns
                        {table.row_count !== null && `, ~${table.row_count.toLocaleString()} rows`})
                      </span>
                    </div>
                    {expandedTable === table.table_name ? (
                      <ChevronDown className="h-4 w-4 text-secondary-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-secondary-400" />
                    )}
                  </div>

                  {expandedTable === table.table_name && table.columns.length > 0 && (
                    <div className="p-3 border-t border-secondary-700 bg-secondary-800/50">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-secondary-500">
                            <th className="pb-2">Column</th>
                            <th className="pb-2">Type</th>
                            <th className="pb-2">Nullable</th>
                          </tr>
                        </thead>
                        <tbody>
                          {table.columns.map((col) => (
                            <tr key={col.column_name} className="border-t border-secondary-700">
                              <td className="py-1.5 text-white">
                                {col.column_name}
                                {table.primary_key === col.column_name && (
                                  <span className="ml-2 text-xs text-primary-400">PK</span>
                                )}
                              </td>
                              <td className="py-1.5 text-secondary-400">{col.data_type}</td>
                              <td className="py-1.5 text-secondary-400">
                                {col.is_nullable === 'YES' ? 'Yes' : 'No'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {tables.length > 0 && (
          <div className="flex items-center justify-between p-6 border-t border-secondary-700">
            <p className="text-sm text-secondary-400">
              {selectedTables.length > 0
                ? `${selectedTables.length} table(s) selected`
                : 'All tables will be synced'}
            </p>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="rounded-lg border border-secondary-700 px-4 py-2 text-sm font-medium text-secondary-300 hover:bg-secondary-800"
              >
                Cancel
              </button>
              <button
                onClick={handleSync}
                disabled={syncMutation.isPending}
                className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-primary-600 to-violet-600 px-4 py-2 text-sm font-medium text-white hover:from-primary-500 hover:to-violet-500 disabled:opacity-50"
              >
                {syncMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                Sync to RAG
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// EMPTY STATE COMPONENT
// =============================================================================

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary-800">
        <Database className="h-8 w-8 text-secondary-500" />
      </div>
      <h3 className="mt-4 text-lg font-medium text-white">
        No database connections yet
      </h3>
      <p className="mt-2 text-sm text-secondary-400 max-w-sm">
        Connect to external databases and sync their data for RAG-powered search.
      </p>
      <button
        onClick={onAdd}
        className="mt-6 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary-600 to-violet-600 px-4 py-2 text-sm font-medium text-white hover:from-primary-500 hover:to-violet-500 shadow-lg shadow-primary-500/25"
      >
        <Plus className="h-4 w-4" />
        Add Connection
      </button>
    </div>
  )
}
