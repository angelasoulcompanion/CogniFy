/**
 * CogniFy App
 * Enterprise RAG Platform
 * Created with love by Angela & David - 1 January 2026
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Layout } from '@/components/layout/Layout'
import { LoginPage } from '@/pages/LoginPage'
import { HomePage } from '@/pages'
import { SearchPage } from '@/pages/SearchPage'
import { DocumentsPage } from '@/pages/DocumentsPage'
import { ConnectorsPage } from '@/pages/ConnectorsPage'
import { AdminPage } from '@/pages/AdminPage'
import { PromptsPage } from '@/pages/PromptsPage'

// Protected Route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, _hasHydrated } = useAuth()

  // Wait for hydration before checking auth
  if (!_hasHydrated) {
    return (
      <div className="flex h-screen items-center justify-center bg-secondary-950">
        <div className="text-primary-400">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/home" replace />} />
        <Route path="home" element={<HomePage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="connectors" element={<ConnectorsPage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="prompts" element={<PromptsPage />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
