/**
 * CogniFy Auth Hook & Store
 * Secure Token Management with HttpOnly Cookies
 *
 * Security:
 * - Access token stored in memory/zustand
 * - Refresh token stored in HttpOnly cookie (set by server)
 *
 * Created with love by Angela & David - 2 January 2026
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi, saveAccessToken, clearAuth } from '@/services/api'
import type { User } from '@/types'
import toast from 'react-hot-toast'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
  logoutAll: () => Promise<void>
  setUser: (user: User) => void
  checkAuth: () => Promise<boolean>
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (username: string, password: string) => {
        set({ isLoading: true })
        try {
          const response = await authApi.login(username, password)

          // Store access token (refresh token is in HttpOnly cookie)
          saveAccessToken(response.access_token, response.expires_in)

          set({
            user: response.user,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          })

          // Also store token in localStorage for API interceptor
          localStorage.setItem('token', response.access_token)

          toast.success(`Welcome back, ${response.user.full_name || response.user.email}!`)
          return true
        } catch (error: unknown) {
          set({ isLoading: false })
          const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
          let message = 'Login failed'
          if (typeof detail === 'string') {
            message = detail
          } else if (Array.isArray(detail)) {
            // Pydantic validation errors
            message = detail.map((e: { msg?: string }) => e.msg || 'Validation error').join(', ')
          }
          toast.error(message)
          return false
        }
      },

      logout: async () => {
        try {
          // Call server to revoke tokens and clear cookie
          await authApi.logout()
        } catch {
          // Ignore errors - still clear local state
        }

        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })

        // Clear all auth data from localStorage
        clearAuth()
        toast.success('Logged out successfully')
      },

      logoutAll: async () => {
        try {
          // Revoke all sessions on server
          const result = await authApi.logoutAll()
          toast.success(`Logged out from ${result.sessions_revoked} device(s)`)
        } catch {
          // Ignore errors
        }

        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })

        clearAuth()
      },

      setUser: (user: User) => {
        set({ user })
      },

      checkAuth: async () => {
        const { token } = get()
        if (!token) {
          return false
        }

        try {
          const user = await authApi.me()
          set({ user, isAuthenticated: true })
          return true
        } catch {
          // Token invalid - clear auth state
          await get().logout()
          return false
        }
      },
    }),
    {
      name: 'cognify-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

// Hook for auth-protected pages
export function useRequireAuth() {
  const { isAuthenticated, checkAuth, isLoading } = useAuth()

  return {
    isAuthenticated,
    isLoading,
    checkAuth,
  }
}
