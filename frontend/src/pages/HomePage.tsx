/**
 * CogniFy Home Page
 * Organization news, announcements, and quick actions
 * Created with love by Angela & David - 4 January 2026
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  useAnnouncements,
  usePinnedAnnouncements,
} from '@/hooks/useAnnouncements'
import { useAuth } from '@/hooks/useAuth'
import type { Announcement, AnnouncementCategory } from '@/types'
import ReactMarkdown from 'react-markdown'
import {
  Home,
  Pin,
  Newspaper,
  Zap,
  Search,
  FileText,
  Database,
  ChevronRight,
  Calendar,
  Tag,
  AlertCircle,
  Bell,
  RefreshCw,
  PartyPopper,
  Megaphone,
  Info,
  X,
} from 'lucide-react'

// =============================================================================
// CATEGORY CONFIG
// =============================================================================

const CATEGORY_CONFIG: Record<AnnouncementCategory, {
  icon: React.ElementType
  color: string
  bgColor: string
  label: string
}> = {
  general: {
    icon: Info,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    label: 'General',
  },
  important: {
    icon: AlertCircle,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    label: 'Important',
  },
  update: {
    icon: RefreshCw,
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    label: 'Update',
  },
  event: {
    icon: PartyPopper,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10',
    label: 'Event',
  },
}

// =============================================================================
// ANNOUNCEMENT CARD
// =============================================================================

function AnnouncementCard({
  announcement,
  isPinned = false,
  onClick,
}: {
  announcement: Announcement
  isPinned?: boolean
  onClick: () => void
}) {
  const config = CATEGORY_CONFIG[announcement.category]
  const CategoryIcon = config.icon

  // Format date
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleDateString('th-TH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  // Get preview text from markdown (first 150 chars)
  const getPreview = (content: string) => {
    // Remove markdown syntax for preview
    const plainText = content
      .replace(/#{1,6}\s/g, '')
      .replace(/\*{1,2}([^*]+)\*{1,2}/g, '$1')
      .replace(/`{1,3}[^`]+`{1,3}/g, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/\n/g, ' ')
      .trim()
    return plainText.length > 150 ? plainText.slice(0, 150) + '...' : plainText
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left rounded-xl border transition-all duration-200',
        'hover:border-primary-500/50 hover:bg-secondary-700/30',
        isPinned
          ? 'bg-primary-500/5 border-primary-500/30'
          : 'bg-secondary-800/50 border-secondary-700/50'
      )}
    >
      {/* Cover Image */}
      {announcement.cover_image_url && (
        <div className="relative h-32 w-full overflow-hidden rounded-t-xl">
          <img
            src={announcement.cover_image_url}
            alt={announcement.title}
            className="h-full w-full object-cover"
          />
          {isPinned && (
            <div className="absolute top-2 left-2 flex items-center gap-1 rounded-full bg-primary-500/90 px-2 py-1 text-xs font-medium text-white">
              <Pin className="h-3 w-3" />
              Pinned
            </div>
          )}
        </div>
      )}

      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className={cn('rounded-full p-1.5', config.bgColor)}>
              <CategoryIcon className={cn('h-4 w-4', config.color)} />
            </span>
            <span className={cn('text-xs font-medium', config.color)}>
              {config.label}
            </span>
          </div>
          {isPinned && !announcement.cover_image_url && (
            <Pin className="h-4 w-4 text-primary-400" />
          )}
        </div>

        {/* Title */}
        <h3 className="mt-3 font-semibold text-white line-clamp-2">
          {announcement.title}
        </h3>

        {/* Preview */}
        <p className="mt-2 text-sm text-secondary-400 line-clamp-2">
          {getPreview(announcement.content)}
        </p>

        {/* Footer */}
        <div className="mt-3 flex items-center gap-3 text-xs text-secondary-500">
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {formatDate(announcement.published_at)}
          </span>
        </div>
      </div>
    </button>
  )
}

// =============================================================================
// ANNOUNCEMENT MODAL
// =============================================================================

function AnnouncementModal({
  announcement,
  onClose,
}: {
  announcement: Announcement
  onClose: () => void
}) {
  const config = CATEGORY_CONFIG[announcement.category]
  const CategoryIcon = config.icon

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleDateString('th-TH', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 max-h-[85vh] w-full max-w-2xl overflow-hidden rounded-2xl bg-secondary-800 border border-secondary-700 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-secondary-700 p-4">
          <div className="flex items-center gap-3">
            <span className={cn('rounded-full p-2', config.bgColor)}>
              <CategoryIcon className={cn('h-5 w-5', config.color)} />
            </span>
            <div>
              <span className={cn('text-sm font-medium', config.color)}>
                {config.label}
              </span>
              <p className="text-xs text-secondary-500">
                {formatDate(announcement.published_at)}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-secondary-400 hover:bg-secondary-700 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Cover Image */}
        {announcement.cover_image_url && (
          <div className="w-full h-48 overflow-hidden">
            <img
              src={announcement.cover_image_url}
              alt={announcement.title}
              className="h-full w-full object-cover"
            />
          </div>
        )}

        {/* Content */}
        <div className="max-h-[50vh] overflow-y-auto p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            {announcement.title}
          </h2>
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown>{announcement.content}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// QUICK ACTION CARD
// =============================================================================

function QuickActionCard({
  to,
  icon: Icon,
  title,
  description,
  color,
}: {
  to: string
  icon: React.ElementType
  title: string
  description: string
  color: string
}) {
  return (
    <Link
      to={to}
      className={cn(
        'group flex flex-col rounded-xl border p-5 transition-all duration-200',
        'bg-secondary-800/50 border-secondary-700/50',
        'hover:border-primary-500/50 hover:bg-secondary-700/30'
      )}
    >
      <div className={cn('rounded-lg p-3 w-fit', color)}>
        <Icon className="h-6 w-6 text-white" />
      </div>
      <h3 className="mt-3 font-semibold text-white group-hover:text-primary-400 transition-colors">
        {title}
      </h3>
      <p className="mt-1 text-sm text-secondary-400">{description}</p>
      <div className="mt-auto pt-3 flex items-center gap-1 text-sm text-primary-400 opacity-0 group-hover:opacity-100 transition-opacity">
        Go to {title.toLowerCase()}
        <ChevronRight className="h-4 w-4" />
      </div>
    </Link>
  )
}

// =============================================================================
// MAIN PAGE
// =============================================================================

export default function HomePage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [selectedAnnouncement, setSelectedAnnouncement] = useState<Announcement | null>(null)

  // Fetch data
  const { data: pinnedData, isLoading: pinnedLoading } = usePinnedAnnouncements(3)
  const { data: recentData, isLoading: recentLoading } = useAnnouncements({ limit: 6 })

  // Get recent announcements (exclude pinned ones)
  const pinnedIds = new Set(pinnedData?.map(a => a.announcement_id) || [])
  const recentAnnouncements = recentData?.announcements.filter(
    a => !pinnedIds.has(a.announcement_id)
  ).slice(0, 4) || []

  // Get greeting based on time
  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good Morning'
    if (hour < 17) return 'Good Afternoon'
    return 'Good Evening'
  }

  return (
    <div className="min-h-full p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="rounded-lg bg-primary-500/10 p-2">
            <Home className="h-6 w-6 text-primary-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">
              {getGreeting()}, {user?.full_name?.split(' ')[0] || user?.email?.split('@')[0]}!
            </h1>
            <p className="text-secondary-400">
              Welcome to CogniFy - Your Enterprise RAG Platform
            </p>
          </div>
        </div>
      </div>

      {/* Pinned Announcements */}
      {pinnedData && pinnedData.length > 0 && (
        <section className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Pin className="h-5 w-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">Pinned Announcements</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {pinnedData.map((announcement) => (
              <AnnouncementCard
                key={announcement.announcement_id}
                announcement={announcement}
                isPinned
                onClick={() => setSelectedAnnouncement(announcement)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Recent News */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Newspaper className="h-5 w-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">Recent News</h2>
          </div>
          {recentData && recentData.total > 4 && (
            <button
              onClick={() => navigate('/announcements')}
              className="flex items-center gap-1 text-sm text-primary-400 hover:text-primary-300 transition-colors"
            >
              View all
              <ChevronRight className="h-4 w-4" />
            </button>
          )}
        </div>

        {recentLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="h-48 rounded-xl bg-secondary-800/50 border border-secondary-700/50 animate-pulse"
              />
            ))}
          </div>
        ) : recentAnnouncements.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {recentAnnouncements.map((announcement) => (
              <AnnouncementCard
                key={announcement.announcement_id}
                announcement={announcement}
                onClick={() => setSelectedAnnouncement(announcement)}
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="rounded-full bg-secondary-700/50 p-4 mb-4">
              <Bell className="h-8 w-8 text-secondary-500" />
            </div>
            <p className="text-secondary-400">No announcements yet</p>
            <p className="text-sm text-secondary-500 mt-1">
              Check back later for news and updates
            </p>
          </div>
        )}
      </section>

      {/* Quick Actions */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Zap className="h-5 w-5 text-primary-400" />
          <h2 className="text-lg font-semibold text-white">Quick Actions</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <QuickActionCard
            to="/search"
            icon={Search}
            title="Search"
            description="Search your documents with AI-powered semantic search"
            color="bg-blue-500"
          />
          <QuickActionCard
            to="/documents"
            icon={FileText}
            title="Documents"
            description="Upload and manage your document library"
            color="bg-purple-500"
          />
          <QuickActionCard
            to="/connectors"
            icon={Database}
            title="Connectors"
            description="Connect to external databases and data sources"
            color="bg-orange-500"
          />
        </div>
      </section>

      {/* Modal */}
      {selectedAnnouncement && (
        <AnnouncementModal
          announcement={selectedAnnouncement}
          onClose={() => setSelectedAnnouncement(null)}
        />
      )}
    </div>
  )
}
