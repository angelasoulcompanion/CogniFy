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
  useAdminAnnouncements,
  useCreateAnnouncement,
  useUpdateAnnouncement,
  useDeleteAnnouncement,
  usePublishAnnouncement,
  useUnpublishAnnouncement,
  usePinAnnouncement,
  useUnpinAnnouncement,
} from '@/hooks'
import { useAuth } from '@/hooks/useAuth'
import type { UserStats, Announcement, CreateAnnouncementRequest, AnnouncementCategory } from '@/types'
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
  Newspaper,
  Plus,
  Edit2,
  Trash2,
  Eye,
  EyeOff,
  Pin,
  PinOff,
  X,
  AlertCircle,
  Info,
  PartyPopper,
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
// NEWS MANAGEMENT COMPONENT
// =============================================================================

const CATEGORY_OPTIONS: { value: AnnouncementCategory; label: string; icon: React.ElementType; color: string }[] = [
  { value: 'general', label: 'General', icon: Info, color: 'text-blue-400' },
  { value: 'important', label: 'Important', icon: AlertCircle, color: 'text-red-400' },
  { value: 'update', label: 'Update', icon: RefreshCw, color: 'text-green-400' },
  { value: 'event', label: 'Event', icon: PartyPopper, color: 'text-yellow-400' },
]

function AnnouncementModal({
  announcement,
  onClose,
  onSave,
  isSaving,
}: {
  announcement?: Announcement | null
  onClose: () => void
  onSave: (data: CreateAnnouncementRequest) => void
  isSaving: boolean
}) {
  const [title, setTitle] = useState(announcement?.title || '')
  const [content, setContent] = useState(announcement?.content || '')
  const [category, setCategory] = useState<AnnouncementCategory>(announcement?.category || 'general')
  const [coverImageUrl, setCoverImageUrl] = useState(announcement?.cover_image_url || '')
  const [isPublished, setIsPublished] = useState(announcement?.is_published || false)
  const [isPinned, setIsPinned] = useState(announcement?.is_pinned || false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      title,
      content,
      category,
      cover_image_url: coverImageUrl || null,
      is_published: isPublished,
      is_pinned: isPinned,
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-2xl bg-secondary-800 rounded-2xl border border-secondary-700 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-secondary-700">
          <h2 className="text-lg font-semibold text-white">
            {announcement ? 'Edit Announcement' : 'Create Announcement'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-secondary-400 hover:bg-secondary-700 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-secondary-300 mb-2">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="w-full px-4 py-2 rounded-lg bg-secondary-700 border border-secondary-600 text-white placeholder-secondary-400 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
              placeholder="Announcement title..."
            />
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-secondary-300 mb-2">Category</label>
            <div className="grid grid-cols-4 gap-2">
              {CATEGORY_OPTIONS.map((opt) => {
                const Icon = opt.icon
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setCategory(opt.value)}
                    className={cn(
                      'flex flex-col items-center gap-1 p-3 rounded-lg border transition-colors',
                      category === opt.value
                        ? 'border-primary-500 bg-primary-500/10'
                        : 'border-secondary-600 bg-secondary-700 hover:border-secondary-500'
                    )}
                  >
                    <Icon className={cn('h-5 w-5', opt.color)} />
                    <span className="text-xs text-secondary-300">{opt.label}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Cover Image URL */}
          <div>
            <label className="block text-sm font-medium text-secondary-300 mb-2">
              Cover Image URL <span className="text-secondary-500">(optional)</span>
            </label>
            <input
              type="url"
              value={coverImageUrl}
              onChange={(e) => setCoverImageUrl(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-secondary-700 border border-secondary-600 text-white placeholder-secondary-400 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
              placeholder="https://example.com/image.jpg"
            />
          </div>

          {/* Content */}
          <div>
            <label className="block text-sm font-medium text-secondary-300 mb-2">
              Content <span className="text-secondary-500">(Markdown supported)</span>
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
              rows={8}
              className="w-full px-4 py-2 rounded-lg bg-secondary-700 border border-secondary-600 text-white placeholder-secondary-400 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none resize-none font-mono text-sm"
              placeholder="# Title&#10;&#10;Write your announcement content in **Markdown**..."
            />
          </div>

          {/* Options */}
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-sm text-secondary-300">
              <input
                type="checkbox"
                checked={isPublished}
                onChange={(e) => setIsPublished(e.target.checked)}
                className="rounded border-secondary-600 bg-secondary-700 text-primary-500"
              />
              Publish immediately
            </label>
            <label className="flex items-center gap-2 text-sm text-secondary-300">
              <input
                type="checkbox"
                checked={isPinned}
                onChange={(e) => setIsPinned(e.target.checked)}
                className="rounded border-secondary-600 bg-secondary-700 text-primary-500"
              />
              Pin to top
            </label>
          </div>
        </form>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-4 border-t border-secondary-700">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-secondary-300 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSaving || !title || !content}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? 'Saving...' : announcement ? 'Update' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}

function NewsManagement() {
  const [showModal, setShowModal] = useState(false)
  const [editingAnnouncement, setEditingAnnouncement] = useState<Announcement | null>(null)

  const { data, isLoading, refetch } = useAdminAnnouncements({ limit: 50 })
  const createAnnouncement = useCreateAnnouncement()
  const updateAnnouncement = useUpdateAnnouncement()
  const deleteAnnouncement = useDeleteAnnouncement()
  const publishAnnouncement = usePublishAnnouncement()
  const unpublishAnnouncement = useUnpublishAnnouncement()
  const pinAnnouncement = usePinAnnouncement()
  const unpinAnnouncement = useUnpinAnnouncement()

  const handleCreate = () => {
    setEditingAnnouncement(null)
    setShowModal(true)
  }

  const handleEdit = (announcement: Announcement) => {
    setEditingAnnouncement(announcement)
    setShowModal(true)
  }

  const handleSave = (formData: CreateAnnouncementRequest) => {
    if (editingAnnouncement) {
      updateAnnouncement.mutate(
        { announcementId: editingAnnouncement.announcement_id, data: formData },
        { onSuccess: () => { setShowModal(false); refetch() } }
      )
    } else {
      createAnnouncement.mutate(formData, {
        onSuccess: () => { setShowModal(false); refetch() }
      })
    }
  }

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this announcement?')) {
      deleteAnnouncement.mutate(id)
    }
  }

  const handleTogglePublish = (announcement: Announcement) => {
    if (announcement.is_published) {
      unpublishAnnouncement.mutate(announcement.announcement_id)
    } else {
      publishAnnouncement.mutate(announcement.announcement_id)
    }
  }

  const handleTogglePin = (announcement: Announcement) => {
    if (announcement.is_pinned) {
      unpinAnnouncement.mutate(announcement.announcement_id)
    } else {
      pinAnnouncement.mutate(announcement.announcement_id)
    }
  }

  const getCategoryBadge = (category: AnnouncementCategory) => {
    const opt = CATEGORY_OPTIONS.find(o => o.value === category)
    if (!opt) return null
    const Icon = opt.icon
    return (
      <span className={cn('inline-flex items-center gap-1 text-xs font-medium', opt.color)}>
        <Icon className="h-3 w-3" />
        {opt.label}
      </span>
    )
  }

  return (
    <div className="bg-secondary-800/50 rounded-xl border border-secondary-700/50">
      <div className="p-4 border-b border-secondary-700 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Newspaper className="h-5 w-5 text-primary-400" />
          <h3 className="font-semibold text-white">News Management</h3>
          <span className="text-sm text-secondary-400">{data?.total || 0} announcements</span>
        </div>
        <button
          onClick={handleCreate}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-500"
        >
          <Plus className="h-4 w-4" />
          New Announcement
        </button>
      </div>

      {isLoading ? (
        <div className="p-8 text-center text-secondary-400">Loading announcements...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-secondary-700">
                <th className="py-3 px-4 text-left text-xs font-medium text-secondary-400 uppercase tracking-wider">Title</th>
                <th className="py-3 px-4 text-left text-xs font-medium text-secondary-400 uppercase tracking-wider">Category</th>
                <th className="py-3 px-4 text-center text-xs font-medium text-secondary-400 uppercase tracking-wider">Status</th>
                <th className="py-3 px-4 text-center text-xs font-medium text-secondary-400 uppercase tracking-wider">Pinned</th>
                <th className="py-3 px-4 text-left text-xs font-medium text-secondary-400 uppercase tracking-wider">Created</th>
                <th className="py-3 px-4 text-right text-xs font-medium text-secondary-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-secondary-700/50">
              {data?.announcements.map((announcement) => (
                <tr key={announcement.announcement_id} className="hover:bg-secondary-700/30">
                  <td className="py-3 px-4">
                    <p className="font-medium text-white truncate max-w-xs">{announcement.title}</p>
                  </td>
                  <td className="py-3 px-4">{getCategoryBadge(announcement.category)}</td>
                  <td className="py-3 px-4 text-center">
                    <span className={cn(
                      'inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium',
                      announcement.is_published
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    )}>
                      {announcement.is_published ? (
                        <><Eye className="h-3 w-3" /> Published</>
                      ) : (
                        <><EyeOff className="h-3 w-3" /> Draft</>
                      )}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    {announcement.is_pinned && <Pin className="h-4 w-4 text-primary-400 mx-auto" />}
                  </td>
                  <td className="py-3 px-4 text-sm text-secondary-400">
                    {announcement.created_at
                      ? new Date(announcement.created_at).toLocaleDateString()
                      : '-'}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleTogglePublish(announcement)}
                        className={cn(
                          'p-1.5 rounded-lg transition-colors',
                          announcement.is_published
                            ? 'text-yellow-400 hover:bg-yellow-500/20'
                            : 'text-green-400 hover:bg-green-500/20'
                        )}
                        title={announcement.is_published ? 'Unpublish' : 'Publish'}
                      >
                        {announcement.is_published ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                      <button
                        onClick={() => handleTogglePin(announcement)}
                        className={cn(
                          'p-1.5 rounded-lg transition-colors',
                          announcement.is_pinned
                            ? 'text-primary-400 hover:bg-primary-500/20'
                            : 'text-secondary-400 hover:bg-secondary-600'
                        )}
                        title={announcement.is_pinned ? 'Unpin' : 'Pin'}
                      >
                        {announcement.is_pinned ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}
                      </button>
                      <button
                        onClick={() => handleEdit(announcement)}
                        className="p-1.5 rounded-lg text-blue-400 hover:bg-blue-500/20 transition-colors"
                        title="Edit"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(announcement.announcement_id)}
                        className="p-1.5 rounded-lg text-red-400 hover:bg-red-500/20 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {(!data?.announcements || data.announcements.length === 0) && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-secondary-400">
                    No announcements yet. Click "New Announcement" to create one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <AnnouncementModal
          announcement={editingAnnouncement}
          onClose={() => setShowModal(false)}
          onSave={handleSave}
          isSaving={createAnnouncement.isPending || updateAnnouncement.isPending}
        />
      )}
    </div>
  )
}

// =============================================================================
// MAIN ADMIN PAGE
// =============================================================================

export function AdminPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'news'>('overview')
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
            <button
              onClick={() => setActiveTab('news')}
              className={cn(
                'pb-3 px-1 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'news'
                  ? 'border-primary-500 text-primary-400'
                  : 'border-transparent text-secondary-400 hover:text-secondary-200'
              )}
            >
              <Newspaper className="inline h-4 w-4 mr-2" />
              News
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

        {/* News Tab */}
        {activeTab === 'news' && <NewsManagement />}
      </div>
    </div>
  )
}
