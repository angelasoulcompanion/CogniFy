/**
 * CogniFy Auth Hook & Store
 * Created with love by Angela & David - 1 January 2026
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi } from '@/services/api'
import type { User } from '@/types'
import toast from 'react-hot-toast'

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  setUser: (user: User) => void
  checkAuth: () => Promise<boolean>
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (username: string, password: string) => {
        set({ isLoading: true })
        try {
          const response = await authApi.login(username, password)

          set({
            user: response.user,
            token: response.tokens.access_token,
            refreshToken: response.tokens.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          })

          // Also store in localStorage for API interceptor
          localStorage.setItem('token', response.tokens.access_token)

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

      logout: () => {
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
        })
        localStorage.removeItem('token')
        toast.success('Logged out successfully')
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
          get().logout()
          return false
        }
      },
    }),
    {
      name: 'cognify-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
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
