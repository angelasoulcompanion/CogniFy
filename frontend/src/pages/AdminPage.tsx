/**
 * CogniFy Admin Dashboard
 * System administration and analytics
 * Created with love by Angela & David - 1 January 2026
 */

import { useState } from 'react'
import { cn } from '@/lib/utils'
import {
  useSystemStats,
  useUsers,
  useDocumentTypeStats,
  useTopUsers,
  useRecentActivity,
  useUpdateUserRole,
  useToggleUserStatus,
  formatNumber,
  getRoleBadgeColor,
} from '@/hooks/useAdmin'
import { useAuth } from '@/hooks/useAuth'
import type { UserStats } from '@/types'
import {
  Users,
  FileText,
  MessageSquare,
  Database,
  HardDrive,
  Activity,
  TrendingUp,
  UserCheck,
  RefreshCw,
  Shield,
  UserX,
  FileImage,
  FileSpreadsheet,
  File,
} from 'lucide-react'

// =============================================================================
// STAT CARD COMPONENT
// =============================================================================

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-primary-400',
  trend,
}: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  iconColor?: string
  trend?: { value: number; label: string }
}) {
  return (
    <div className="rounded-xl bg-secondary-800/50 p-6 border border-secondary-700/50">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-secondary-400">{title}</p>
          <p className="mt-1 text-2xl font-semibold text-white">
            {typeof value === 'number' ? formatNumber(value) : value}
          </p>
          {subtitle && (
            <p className="mt-1 text-xs text-secondary-500">{subtitle}</p>
          )}
          {trend && (
            <p className={cn(
              'mt-2 flex items-center gap-1 text-xs',
              trend.value >= 0 ? 'text-green-400' : 'text-red-400'
            )}>
              <TrendingUp className="h-3 w-3" />
              {trend.value >= 0 ? '+' : ''}{trend.value}% {trend.label}
            </p>
          )}
        </div>
        <div className={cn('rounded-lg bg-secondary-700/50 p-3', iconColor)}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// USER TABLE COMPONENT
// =============================================================================

function UserTable({
  users,
  onRoleChange,
  onToggleStatus,
  isUpdating,
}: {
  users: UserStats[]
  onRoleChange: (userId: string, role: string) => void
  onToggleStatus: (userId: string) => void
  isUpdating: boolean
}) {
  const { user: currentUser } = useAuth()

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-secondary-700">
            <th className="py-3 px-4 text-left text-xs font-medium text-secondary-400 uppercase tracking-wider">
              User
            </th>
            <th className="py-3 px-4 text-left text-xs font-medium text-secondary-400 uppercase tracking-wider">
              Role
            </th>
            <th className="py-3 px-4 text-center text-xs font-medium text-secondary-400 uppercase tracking-wider">
              Documents
            </th>
            <th className="py-3 px-4 text-center text-xs font-medium text-secondary-400 uppercase tracking-wider">
              Messages
            </th>
            <th className="py-3 px-4 text-left text-xs font-medium text-secondary-400 uppercase tracking-wider">
              Last Active
            </th>
            <th className="py-3 px-4 text-left text-xs font-medium text-secondary-400 uppercase tracking-wider">
              Status
            </th>
            <th className="py-3 px-4 text-right text-xs font-medium text-secondary-400 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-secondary-700/50">
          {users.map((user) => (
            <tr key={user.user_id} className="hover:bg-secondary-700/30">
              <td className="py-3 px-4">
                <div>
                  <p className="font-medium text-white">
                    {user.full_name || user.email.split('@')[0]}
                  </p>
                  <p className="text-sm text-secondary-400">{user.email}</p>
                </div>
              </td>
              <td className="py-3 px-4">
                <select
                  value={user.role}
                  onChange={(e) => onRoleChange(user.user_id, e.target.value)}
                  disabled={isUpdating || user.user_id === currentUser?.user_id}
                  className={cn(
                    'rounded-md px-2 py-1 text-xs font-medium border-0 bg-secondary-700',
                    getRoleBadgeColor(user.role),
                    user.user_id === currentUser?.user_id && 'opacity-50 cursor-not-allowed'
                  )}
                >
                  <option value="admin">Admin</option>
                  <option value="editor">Editor</option>
                  <option value="user">User</option>
                </select>
              </td>
              <td className="py-3 px-4 text-center text-sm text-secondary-300">
                {formatNumber(user.document_count)}
              </td>
              <td className="py-3 px-4 text-center text-sm text-secondary-300">
                {formatNumber(user.message_count)}
              </td>
              <td className="py-3 px-4 text-sm text-secondary-400">
                {user.last_active
                  ? new Date(user.last_active).toLocaleDateString()
                  : 'Never'}
              </td>
              <td className="py-3 px-4">
                <span className={cn(
                  'inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium',
                  user.is_active
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-red-500/20 text-red-400'
                )}>
                  {user.is_active ? (
                    <>
                      <UserCheck className="h-3 w-3" />
                      Active
                    </>
                  ) : (
                    <>
                      <UserX className="h-3 w-3" />
                      Inactive
                    </>
                  )}
                </span>
              </td>
              <td className="py-3 px-4 text-right">
                {user.user_id !== currentUser?.user_id && (
                  <button
                    onClick={() => onToggleStatus(user.user_id)}
                    disabled={isUpdating}
                    className={cn(
                      'text-sm',
                      user.is_active
                        ? 'text-red-400 hover:text-red-300'
                        : 'text-green-400 hover:text-green-300'
                    )}
                  >
                    {user.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// =============================================================================
// DOCUMENT STATS COMPONENT
// =============================================================================

function DocumentStats() {
  const { data: stats, isLoading } = useDocumentTypeStats()

  if (isLoading) return <div className="animate-pulse h-32 bg-secondary-800 rounded-lg" />

  const getIcon = (fileType: string) => {
    switch (fileType.toLowerCase()) {
      case 'pdf':
        return <FileText className="h-5 w-5 text-red-400" />
      case 'png':
      case 'jpg':
      case 'jpeg':
        return <FileImage className="h-5 w-5 text-purple-400" />
      case 'xlsx':
      case 'xls':
        return <FileSpreadsheet className="h-5 w-5 text-green-400" />
      default:
        return <File className="h-5 w-5 text-secondary-400" />
    }
  }

  return (
    <div className="rounded-xl bg-secondary-800/50 p-6 border border-secondary-700/50">
      <h3 className="font-semibold text-white mb-4">Documents by Type</h3>
      <div className="space-y-4">
        {stats?.map((stat) => (
          <div key={stat.file_type} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getIcon(stat.file_type)}
              <div>
                <p className="font-medium text-white uppercase">{stat.file_type}</p>
                <p className="text-xs text-secondary-400">{stat.total_chunks} chunks</p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-semibold text-white">{stat.count}</p>
              <p className="text-xs text-secondary-400">{stat.total_size_mb.toFixed(1)} MB</p>
            </div>
          </div>
        ))}
        {(!stats || stats.length === 0) && (
          <p className="text-secondary-400 text-sm">No documents yet</p>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// RECENT ACTIVITY COMPONENT
// =============================================================================

function RecentActivity() {
  const { data: activity, isLoading } = useRecentActivity(10)

  if (isLoading) return <div className="animate-pulse h-48 bg-secondary-800 rounded-lg" />

  return (
    <div className="rounded-xl bg-secondary-800/50 p-6 border border-secondary-700/50">
      <h3 className="font-semibold text-white mb-4">Recent Activity</h3>
      <div className="space-y-4">
        {activity?.map((item, index) => (
          <div key={`${item.id}-${index}`} className="flex items-start gap-3">
            <div className={cn(
              'rounded-full p-2',
              item.type === 'document' ? 'bg-blue-500/20' : 'bg-purple-500/20'
            )}>
              {item.type === 'document' ? (
                <FileText className="h-4 w-4 text-blue-400" />
              ) : (
                <MessageSquare className="h-4 w-4 text-purple-400" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white truncate">{item.title}</p>
              <p className="text-xs text-secondary-400">
                {item.user_email} • {new Date(item.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
        ))}
        {(!activity || activity.length === 0) && (
          <p className="text-secondary-400 text-sm">No recent activity</p>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// TOP USERS COMPONENT
// =============================================================================

function TopUsersList() {
  const { data: users, isLoading } = useTopUsers(5)

  if (isLoading) return <div className="animate-pulse h-48 bg-secondary-800 rounded-lg" />

  return (
    <div className="rounded-xl bg-secondary-800/50 p-6 border border-secondary-700/50">
      <h3 className="font-semibold text-white mb-4">Top Users</h3>
      <div className="space-y-4">
        {users?.map((user, index) => (
          <div key={user.user_id} className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-500/20 text-primary-400 font-semibold text-sm">
              {index + 1}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user.full_name || user.email.split('@')[0]}
              </p>
              <p className="text-xs text-secondary-400">{user.email}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-white">{user.messages}</p>
              <p className="text-xs text-secondary-400">messages</p>
            </div>
          </div>
        ))}
        {(!users || users.length === 0) && (
          <p className="text-secondary-400 text-sm">No users yet</p>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// MAIN ADMIN PAGE
// =============================================================================

export function AdminPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'users'>('overview')
  const [showInactive, setShowInactive] = useState(false)

  const { data: stats, refetch: refetchStats } = useSystemStats()
  const { data: usersData, isLoading: usersLoading } = useUsers(0, 50, showInactive)
  const updateRole = useUpdateUserRole()
  const toggleStatus = useToggleUserStatus()

  const handleRoleChange = (userId: string, role: string) => {
    updateRole.mutate({ userId, role })
  }

  const handleToggleStatus = (userId: string) => {
    toggleStatus.mutate(userId)
  }

  return (
    <div className="min-h-screen bg-secondary-950 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
            <p className="text-secondary-400">System overview and user management</p>
          </div>
          <button
            onClick={() => refetchStats()}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-secondary-800 border border-secondary-700 rounded-xl text-secondary-300 hover:bg-secondary-700"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-secondary-700">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('overview')}
              className={cn(
                'pb-3 px-1 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'overview'
                  ? 'border-primary-500 text-primary-400'
                  : 'border-transparent text-secondary-400 hover:text-secondary-200'
              )}
            >
              <Activity className="inline h-4 w-4 mr-2" />
              Overview
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={cn(
                'pb-3 px-1 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'users'
                  ? 'border-primary-500 text-primary-400'
                  : 'border-transparent text-secondary-400 hover:text-secondary-200'
              )}
            >
              <Users className="inline h-4 w-4 mr-2" />
              Users
            </button>
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatCard
                title="Total Users"
                value={stats?.total_users || 0}
                subtitle={`${stats?.active_users_7d || 0} active this week`}
                icon={Users}
                iconColor="text-blue-500"
              />
              <StatCard
                title="Documents"
                value={stats?.total_documents || 0}
                subtitle={`${formatNumber(stats?.total_chunks || 0)} chunks`}
                icon={FileText}
                iconColor="text-green-500"
              />
              <StatCard
                title="Conversations"
                value={stats?.total_conversations || 0}
                subtitle={`${formatNumber(stats?.total_messages || 0)} messages`}
                icon={MessageSquare}
                iconColor="text-purple-500"
              />
              <StatCard
                title="Storage Used"
                value={`${(stats?.storage_used_mb || 0).toFixed(1)} MB`}
                subtitle={`Avg response: ${(stats?.avg_response_time_ms || 0).toFixed(0)}ms`}
                icon={HardDrive}
                iconColor="text-orange-500"
              />
            </div>

            {/* Secondary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <StatCard
                title="Total Embeddings"
                value={stats?.total_embeddings || 0}
                icon={Database}
                iconColor="text-indigo-500"
              />
              <StatCard
                title="Active Users (7 days)"
                value={stats?.active_users_7d || 0}
                icon={UserCheck}
                iconColor="text-teal-500"
              />
            </div>

            {/* Detail Panels */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <DocumentStats />
              <TopUsersList />
              <RecentActivity />
            </div>
          </>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="bg-secondary-800/50 rounded-xl border border-secondary-700/50">
            <div className="p-4 border-b border-secondary-700 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Shield className="h-5 w-5 text-primary-400" />
                <h3 className="font-semibold text-white">User Management</h3>
                <span className="text-sm text-secondary-400">
                  {usersData?.total || 0} users
                </span>
              </div>
              <label className="flex items-center gap-2 text-sm text-secondary-400">
                <input
                  type="checkbox"
                  checked={showInactive}
                  onChange={(e) => setShowInactive(e.target.checked)}
                  className="rounded border-secondary-600 bg-secondary-700 text-primary-500"
                />
                Show inactive
              </label>
            </div>
            {usersLoading ? (
              <div className="p-8 text-center text-secondary-400">Loading users...</div>
            ) : (
              <UserTable
                users={usersData?.users || []}
                onRoleChange={handleRoleChange}
                onToggleStatus={handleToggleStatus}
                isUpdating={updateRole.isPending || toggleStatus.isPending}
              />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
