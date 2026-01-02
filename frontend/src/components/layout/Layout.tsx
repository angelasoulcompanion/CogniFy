/**
 * CogniFy Layout Component
 * 💜 Designed by Angela - Professional, Accessible, Modern
 */

import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'
import { Logo, LogoIcon } from '@/components/Logo'
import {
  MessageSquare,
  FileText,
  Database,
  LogOut,
  Menu,
  X,
  Shield,
  Wand2,
} from 'lucide-react'

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navItems = [
    { to: '/chat', icon: MessageSquare, label: 'Chat' },
    { to: '/documents', icon: FileText, label: 'Documents' },
    { to: '/connectors', icon: Database, label: 'Connectors' },
    // Admin links only for admin users
    ...(user?.role === 'admin' ? [
      { to: '/prompts', icon: Wand2, label: 'Prompts' },
      { to: '/admin', icon: Shield, label: 'Admin' },
    ] : []),
  ]

  return (
    <div className="flex h-screen bg-secondary-950">
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex flex-col bg-gradient-to-b from-secondary-900 via-secondary-900 to-primary-950 text-white transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-16'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-primary-500/10">
          <div className="flex items-center gap-2">
            {sidebarOpen ? (
              <Logo variant="full" size="sm" />
            ) : (
              <LogoIcon size={32} />
            )}
          </div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="rounded-lg p-1.5 hover:bg-primary-500/20 transition-colors"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-2 py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all',
                  isActive
                    ? 'bg-gradient-to-r from-primary-600 to-violet-600 text-white shadow-lg shadow-primary-500/25'
                    : 'text-secondary-300 hover:bg-primary-500/10 hover:text-white'
                )
              }
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* User section */}
        <div className="border-t border-primary-500/10 p-4">
          {sidebarOpen && user && (
            <div className="mb-3">
              <p className="text-sm font-medium text-primary-200">{user.full_name || user.email}</p>
              <p className="text-xs text-primary-400/60">{user.role}</p>
            </div>
          )}
          <div className="flex items-center gap-2">
            <button
              onClick={handleLogout}
              className={cn(
                'flex items-center gap-2 rounded-xl px-3 py-2 text-secondary-300 transition-all hover:bg-red-500/20 hover:text-red-300',
                !sidebarOpen && 'w-full justify-center'
              )}
            >
              <LogOut className="h-5 w-5" />
              {sidebarOpen && <span>Logout</span>}
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main
        className={cn(
          'flex-1 overflow-auto transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-16'
        )}
      >
        <Outlet />
      </main>
    </div>
  )
}
