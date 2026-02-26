/**
 * CogniFy Announcement Category Configuration
 * Shared category config used by HomePage and AdminPage
 * Created with love by Angela & David
 */

import { Info, AlertCircle, RefreshCw, PartyPopper } from 'lucide-react'
import type { AnnouncementCategory } from '@/types'

export interface CategoryConfig {
  icon: React.ElementType
  color: string
  bgColor: string
  label: string
}

export const CATEGORY_CONFIG: Record<AnnouncementCategory, CategoryConfig> = {
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

export const CATEGORY_OPTIONS = Object.entries(CATEGORY_CONFIG).map(
  ([value, config]) => ({
    value: value as AnnouncementCategory,
    ...config,
  })
)
