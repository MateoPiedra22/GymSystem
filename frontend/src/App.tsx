import { Routes, Route, Navigate } from 'react-router-dom'
import React, { useEffect } from 'react'
import { useAuthStore } from './store/authStore'
import { ThemeProvider } from './components/theme-provider'
import { LoadingSpinner } from './components/ui/loading-spinner'
import { DashboardLayout } from './components/layout/DashboardLayout'
import { PageErrorBoundary } from './components/PageErrorBoundary'

// Direct imports - no lazy loading for administrative system
import LoginPage from './pages/auth/LoginPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import ReportsPage from './pages/ReportsPage'
import UsersPage from './pages/users/UsersPage'
import PaymentsPage from './pages/payments/PaymentsPage'
import RoutinesPage from './pages/routines/RoutinesPage'
import ClassesPage from './pages/classes/ClassesPage'
import ExercisesPage from './pages/exercises/ExercisesPage'
import EmployeesPage from './pages/employees/EmployeesPage'
import CommunityPage from './pages/community/CommunityPage'
import ConfigurationPage from './pages/configuration/ConfigurationPage'
import ConnectionTest from './pages/ConnectionTest'
import NotFoundPage from './pages/NotFoundPage'

// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRoles?: string[]
}

function ProtectedRoute({ children, requiredRoles = [] }: ProtectedRouteProps) {
  const { user, isAuthenticated, loading, token } = useAuthStore()

  // Show loading only when explicitly loading and no user data
  if (loading && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated || !token) {
    return <Navigate to="/login" replace />
  }

  // If we have token but no user data, allow render but getCurrentUser will fetch it
  if (isAuthenticated && token && !user) {
    // Don't show loading spinner, let the app render and fetch user data in background
    return <>{children}</>
  }

  // Check role permissions only if we have user data
  // Only 'owner' (Dueño) and 'trainer' (Profesor) roles are allowed
  if (user && requiredRoles.length > 0 && !requiredRoles.includes(user.role)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Acceso Denegado
          </h2>
          <p className="text-gray-600">
            No tienes permisos para acceder a esta página.
          </p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

// Public Route Component (redirects to dashboard if authenticated)
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuthStore()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}

function App() {
  const { initializeAuth, getCurrentUser, isAuthenticated, token } = useAuthStore()
  const [isInitialized, setIsInitialized] = React.useState(false)

  useEffect(() => {
    // Initialize authentication state from localStorage
    initializeAuth()
    setIsInitialized(true)
  }, [])

  useEffect(() => {
    // Get current user data if authenticated and token exists
    // Only after initialization is complete
    if (isInitialized && isAuthenticated && token) {
      const timeoutId = setTimeout(() => {
        getCurrentUser().catch((error) => {
          console.error('Failed to get current user:', error)
        })
      }, 100) // Small delay to ensure localStorage is updated
      
      return () => clearTimeout(timeoutId)
    }
  }, [isInitialized, isAuthenticated, token])

  // Show loading until initialization is complete
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <ThemeProvider defaultTheme="light" storageKey="gymsystem-ui-theme">
      <div className="min-h-screen bg-background">
        <Routes>
          {/* Public Routes */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <PageErrorBoundary>
                  <LoginPage />
                </PageErrorBoundary>
              </PublicRoute>
            }
          />
          
          {/* Connection Test Route - Public for testing */}
          <Route
            path="/connection-test"
            element={
              <PageErrorBoundary>
                <ConnectionTest />
              </PageErrorBoundary>
            }
          />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            {/* Dashboard */}
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={
              <PageErrorBoundary>
                <DashboardPage />
              </PageErrorBoundary>
            } />

            {/* Reports */}
            <Route
              path="reports"
              element={
                <ProtectedRoute requiredRoles={['owner', 'trainer']}>
                  <PageErrorBoundary>
                    <ReportsPage />
                  </PageErrorBoundary>
                </ProtectedRoute>
              }
            />

            {/* Users Management */}
            <Route
              path="users"
              element={
                <ProtectedRoute requiredRoles={['owner', 'trainer']}>
                  <PageErrorBoundary>
                    <UsersPage />
                  </PageErrorBoundary>
                </ProtectedRoute>
              }
            />

            {/* Payments */}
            <Route
              path="payments"
              element={
                <ProtectedRoute requiredRoles={['owner', 'trainer']}>
                  <PageErrorBoundary>
                    <PaymentsPage />
                  </PageErrorBoundary>
                </ProtectedRoute>
              }
            />

            {/* Routines */}
            <Route path="routines" element={
              <PageErrorBoundary>
                <RoutinesPage />
              </PageErrorBoundary>
            } />

            {/* Classes */}
            <Route path="classes" element={
              <PageErrorBoundary>
                <ClassesPage />
              </PageErrorBoundary>
            } />

            {/* Exercises */}
            <Route path="exercises" element={
              <PageErrorBoundary>
                <ExercisesPage />
              </PageErrorBoundary>
            } />

            {/* Employees */}
            <Route
              path="employees"
              element={
                <ProtectedRoute requiredRoles={['owner']}>
                  <PageErrorBoundary>
                    <EmployeesPage />
                  </PageErrorBoundary>
                </ProtectedRoute>
              }
            />

            {/* Community */}
            <Route path="community" element={
              <PageErrorBoundary>
                <CommunityPage />
              </PageErrorBoundary>
            } />

            {/* Configuration */}
            <Route
              path="configuration"
              element={
                <ProtectedRoute requiredRoles={['owner']}>
                  <PageErrorBoundary>
                    <ConfigurationPage />
                  </PageErrorBoundary>
                </ProtectedRoute>
              }
            />
          </Route>

          {/* 404 Page */}
          <Route path="*" element={
            <PageErrorBoundary>
              <NotFoundPage />
            </PageErrorBoundary>
          } />
        </Routes>
      </div>
    </ThemeProvider>
  )
}

export default App