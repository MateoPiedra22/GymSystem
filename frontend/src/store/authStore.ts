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
            // Handle owner login with master password
            if (credentials.role === 'owner') {
              if (credentials.password === '0000') {
                // Mock owner user data
                const ownerUser = {
                  id: 1,
                  email: 'owner@zurka.gym',
                  first_name: 'Dueño',
                  last_name: 'Zurka',
                  role: 'owner' as const,
                  status: 'active' as const,
                  is_active: true,
                  created_at: new Date().toISOString(),
                  gym_name: 'Zurka'
                }
                
                // Generate mock token
                const mockToken = 'owner_token_' + Date.now()
                
                // Store tokens in localStorage
                localStorage.setItem('gym_access_token', mockToken)
                localStorage.setItem('gym_refresh_token', mockToken + '_refresh')
                
                set({ 
                  user: ownerUser, 
                  token: mockToken,
                  isAuthenticated: true,
                  loading: false 
                })
                return
              } else {
                throw new Error('Contraseña maestra incorrecta')
              }
            }
            
            // Handle trainer login
            if (credentials.role === 'trainer') {
              if (credentials.password === 'password' && credentials.trainer_id) {
                // Mock trainer user data based on trainer_id
                const trainerUser = {
                  id: credentials.trainer_id,
                  email: `trainer${credentials.trainer_id}@zurka.gym`,
                  first_name: credentials.trainer_id === 1 ? 'Carlos' : credentials.trainer_id === 2 ? 'Maria' : 'Diego',
                  last_name: credentials.trainer_id === 1 ? 'Rodriguez' : credentials.trainer_id === 2 ? 'Gonzalez' : 'Martinez',
                  role: 'trainer' as const,
                  status: 'active' as const,
                  is_active: true,
                  created_at: new Date().toISOString()
                }
                
                // Generate mock token
                const mockToken = 'trainer_token_' + Date.now()
                
                // Store tokens in localStorage
                localStorage.setItem('gym_access_token', mockToken)
                localStorage.setItem('gym_refresh_token', mockToken + '_refresh')
                
                set({ 
                  user: trainerUser, 
                  token: mockToken,
                  isAuthenticated: true,
                  loading: false 
                })
                return
              } else {
                throw new Error('Contraseña incorrecta')
              }
            }
            
            throw new Error('Tipo de usuario no válido')
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