import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { authService } from '../api/services/auth'
import type { User, LoginRequest, ChangePasswordRequest, RegisterRequest } from '../types/auth'

interface AuthState {
  // State
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
  
  // Actions
  login: (credentials: LoginRequest) => Promise<void>
  register: (userData: RegisterRequest) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  getCurrentUser: () => Promise<void>
  updateProfile: (userData: Partial<User>) => Promise<void>
  changePassword: (passwordData: ChangePasswordRequest) => Promise<void>
  forgotPassword: (email: string) => Promise<void>
  resetPassword: (token: string, newPassword: string) => Promise<void>
  verifyEmail: (token: string) => Promise<void>
  resendVerification: () => Promise<void>
  
  // Utility actions
  initializeAuth: () => void
  clearError: () => void
  setLoading: (loading: boolean) => void
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  updateOwnerPassword: (newPassword: string) => void
  getOwnerPassword: () => string
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        user: null,
        token: null,
        isAuthenticated: false,
        loading: false,
        error: null,

        // Login action
        login: async (credentials: LoginRequest) => {
          set({ loading: true, error: null })
          try {
            // Mock login for testing purposes - Dueño and Profesor roles
            // Dueño login - only requires password (default: 0000)
            if (credentials.email === 'Zurka') {
              const storedOwnerPassword = localStorage.getItem('owner_password') || '0000'
              if (credentials.password === storedOwnerPassword) {
                const mockOwnerUser: User = {
                  id: 1,
                  email: 'zurka@gym.com',
                  first_name: 'Zurka',
                  last_name: 'Gym Owner',
                  role: 'owner',
                  status: 'active',
                  is_active: true,
                  phone: '+1234567890',
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString()
                }
                
                const mockToken = 'mock-jwt-token-owner-' + Date.now()
                
                set({
                  user: mockOwnerUser,
                  token: mockToken,
                  isAuthenticated: true,
                  loading: false,
                  error: null
                })
                
                localStorage.setItem('gym_access_token', mockToken)
                return
              }
              throw new Error('Contraseña de Zurka incorrecta')
            }
            
            // Profesor login - requires selection and password
            if (credentials.email.startsWith('profesor_')) {
              const profesorId = credentials.email.replace('profesor_', '')
              // For demo purposes, accept any password for professors
              if (credentials.password && credentials.password.length > 0) {
                const mockTrainerUser: User = {
                  id: parseInt(profesorId) || 2,
                  email: 'profesor@gym.com',
                  first_name: 'Carlos',
                  last_name: 'Rodríguez',
                  role: 'trainer',
                  status: 'active',
                  is_active: true,
                  phone: '+1234567891',
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString()
                }
                
                const mockToken = 'mock-jwt-token-trainer-' + profesorId + '-' + Date.now()
                
                set({
                  user: mockTrainerUser,
                  token: mockToken,
                  isAuthenticated: true,
                  loading: false,
                  error: null
                })
                
                localStorage.setItem('gym_access_token', mockToken)
                return
              }
              throw new Error('Contraseña de profesor incorrecta')
            }
            
            // Legacy mock logins for backward compatibility
            if (credentials.email === 'dueno@gym.com' && credentials.password === 'dueno123') {
              const mockOwnerUser: User = {
                id: 1,
                email: 'dueno@gym.com',
                first_name: 'Juan',
                last_name: 'Pérez',
                role: 'owner',
                status: 'active',
                is_active: true,
                phone: '+1234567890',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
              }
              
              const mockToken = 'mock-jwt-token-owner-' + Date.now()
              
              set({
                user: mockOwnerUser,
                token: mockToken,
                isAuthenticated: true,
                loading: false,
                error: null
              })
              
              localStorage.setItem('gym_access_token', mockToken)
              return
            }
            
            if (credentials.email === 'profesor@gym.com' && credentials.password === 'profesor123') {
              const mockTrainerUser: User = {
                id: 2,
                email: 'profesor@gym.com',
                first_name: 'Carlos',
                last_name: 'Rodríguez',
                role: 'trainer',
                status: 'active',
                is_active: true,
                phone: '+1234567891',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
              }
              
              const mockToken = 'mock-jwt-token-trainer-' + Date.now()
              
              set({
                user: mockTrainerUser,
                token: mockToken,
                isAuthenticated: true,
                loading: false,
                error: null
              })
              
              localStorage.setItem('gym_access_token', mockToken)
              return
            }
            
            // Use the authentication service for real backend login
            const response = await authService.login({
              email: credentials.email,
              password: credentials.password
            })
            
            set({
              user: response.user,
              token: response.access_token,
              isAuthenticated: true,
              loading: false,
              error: null
            })
            
            // Store tokens in localStorage for API calls
            localStorage.setItem('gym_access_token', response.access_token)
            if (response.refresh_token) {
              localStorage.setItem('gym_refresh_token', response.refresh_token)
            }
          } catch (error: any) {
            const errorMessage = error.message || 'Error al iniciar sesión'
              
            set({
              error: errorMessage,
              loading: false,
              isAuthenticated: false,
              user: null,
              token: null
            })
            localStorage.removeItem('gym_access_token')
            localStorage.removeItem('gym_refresh_token')
            throw new Error(errorMessage)
          }
        },

        // Register action
        register: async (userData: RegisterRequest) => {
          set({ loading: true, error: null })
          try {
            const response = await authService.register(userData)
            set({
              user: response.user,
              token: response.access_token,
              isAuthenticated: true,
              loading: false,
              error: null
            })
            
            // Set tokens in localStorage for API calls
            localStorage.setItem('gym_access_token', response.access_token)
            if (response.refresh_token) {
              localStorage.setItem('gym_refresh_token', response.refresh_token)
            }
          } catch (error: any) {
            set({
              error: error.message || 'Error al registrarse',
              loading: false,
              isAuthenticated: false,
              user: null,
              token: null
            })
            localStorage.removeItem('gym_access_token')
            localStorage.removeItem('gym_refresh_token')
            throw error
          }
        },

        // Logout action
        logout: () => {
          try {
            authService.logout()
          } catch (error) {
            console.error('Error during logout:', error)
          } finally {
            set({
              user: null,
              token: null,
              isAuthenticated: false,
              error: null
            })
            localStorage.removeItem('gym_access_token')
            localStorage.removeItem('gym_refresh_token')
          }
        },

        // Refresh token action
        refreshToken: async () => {
          const refreshToken = localStorage.getItem('gym_refresh_token')
          if (!refreshToken) {
            throw new Error('No refresh token available')
          }
          
          try {
            const response = await authService.refreshToken(refreshToken)
            
            set({
              token: response.access_token
            })
            
            localStorage.setItem('gym_access_token', response.access_token)
            if (response.refresh_token) {
              localStorage.setItem('gym_refresh_token', response.refresh_token)
            }
          } catch (error: any) {
            // If refresh fails, logout user
            get().logout()
            throw error
          }
        },

        // Get current user action
        getCurrentUser: async () => {
          const state = get()
          const token = state.token || localStorage.getItem('gym_access_token')
          if (!token) {
            return
          }
          
          // Check if it's a mock token
          if (token.startsWith('mock-jwt-token')) {
            // For mock tokens, try to get user from state or localStorage
            if (state.user) {
              set({
                user: state.user,
                isAuthenticated: true,
                loading: false,
                error: null
              })
              return
            }
          }
          
          // Don't set loading if we already have user data
          if (!state.user) {
            set({ loading: true })
          }
          
          try {
            const user = await authService.getCurrentUser()
            
            set({
              user,
              isAuthenticated: true,
              loading: false,
              error: null
            })
          } catch (error: any) {
            set({
              error: error.message || 'Error al obtener usuario actual',
              loading: false
            })
            
            // If getting current user fails, might need to logout
            if (error.status === 401) {
              get().logout()
            }
          }
        },

        // Update profile action
        updateProfile: async (userData: Partial<User>) => {
          set({ loading: true, error: null })
          try {
            const updatedUser = await authService.updateProfile(userData)
            set({
              user: updatedUser,
              loading: false,
              error: null
            })
          } catch (error: any) {
            set({
              error: error.message || 'Error al actualizar perfil',
              loading: false
            })
            throw error
          }
        },

        // Change password action
        changePassword: async (passwordData: ChangePasswordRequest) => {
          set({ loading: true, error: null })
          try {
            await authService.changePassword(passwordData)
            
            set({
              loading: false,
              error: null
            })
          } catch (error: any) {
            set({
              error: error.message || 'Error al cambiar contraseña',
              loading: false
            })
            throw error
          }
        },

        // Forgot password action
        forgotPassword: async (email: string) => {
          set({ loading: true, error: null })
          try {
            await authService.forgotPassword(email)
            set({
              loading: false,
              error: null
            })
          } catch (error: any) {
            set({
              error: error.message || 'Error al enviar email de recuperación',
              loading: false
            })
            throw error
          }
        },

        // Reset password action
        resetPassword: async (token: string, newPassword: string) => {
          set({ loading: true, error: null })
          try {
            await authService.resetPassword(token, newPassword)
            set({
              loading: false,
              error: null
            })
          } catch (error: any) {
            set({
              error: error.message || 'Error al restablecer contraseña',
              loading: false
            })
            throw error
          }
        },

        // Verify email action
        verifyEmail: async (token: string) => {
          set({ loading: true, error: null })
          try {
            await authService.verifyEmail(token)
            set({
              loading: false,
              error: null
            })
          } catch (error: any) {
            set({
              error: error.message || 'Error al verificar email',
              loading: false
            })
            throw error
          }
        },

        // Resend verification action
        resendVerification: async () => {
          set({ loading: true, error: null })
          try {
            await authService.resendVerification()
            set({
              loading: false,
              error: null
            })
          } catch (error: any) {
            set({
              error: error.message || 'Error al reenviar verificación',
              loading: false
            })
            throw error
          }
        },

        // Utility actions
        initializeAuth: () => {
          const token = localStorage.getItem('gym_access_token')
          if (token) {
            set({ 
              token,
              isAuthenticated: true
            })
          } else {
            // Ensure clean state if no token
            set({
              token: null,
              user: null,
              isAuthenticated: false
            })
          }
        },

        clearError: () => {
          set({ error: null })
        },

        setLoading: (loading: boolean) => {
          set({ loading })
        },

        setUser: (user: User | null) => {
          set({ 
            user,
            isAuthenticated: !!user
          })
        },

        setToken: (token: string | null) => {
          set({ token })
          if (token) {
            localStorage.setItem('gym_access_token', token)
          } else {
            localStorage.removeItem('gym_access_token')
          }
        },

        // Method to update owner password
        updateOwnerPassword: (newPassword: string) => {
          localStorage.setItem('owner_password', newPassword)
        },
        
        // Method to get current owner password
        getOwnerPassword: () => {
          return localStorage.getItem('owner_password') || '0000'
        }
      }),
      {
        name: 'auth-store',
        // Only persist token and user, not loading/error states
        partialize: (state: AuthState) => ({
          user: state.user,
          token: state.token,
          isAuthenticated: state.isAuthenticated
        }),
        // Rehydrate authentication state on app load
        onRehydrateStorage: () => (state: AuthState | undefined) => {
          if (state?.token) {
            localStorage.setItem('gym_access_token', state.token)
            // Token verification will be handled by the App component's useEffect
          }
        }
      }
    ),
    {
      name: 'auth-store'
    }
  ))

export default useAuthStore