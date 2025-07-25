import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { usersService, UsersListParams } from '../api/services/users'
import { UserProfile, UserStatistics, CreateUserRequest, UpdateUserRequest, UserSearchParams } from '../types/user'

interface UserState {
  // State
  users: UserProfile[]
  currentUser: UserProfile | null
  userStats: UserStatistics | null
  loading: boolean
  error: string | null
  currentPage: number
  totalPages: number
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  filters: UserSearchParams
  
  // Actions
  getUsers: (params?: UsersListParams) => Promise<void>
  getUser: (id: string) => Promise<void>
  createUser: (userData: CreateUserRequest) => Promise<UserProfile | null>
  updateUser: (id: string, userData: UpdateUserRequest) => Promise<UserProfile | null>
  deleteUser: (id: string) => Promise<boolean>
  searchUsers: (params: UserSearchParams) => Promise<void>
  getUserStats: () => Promise<void>
  activateUser: (id: string) => Promise<boolean>
  deactivateUser: (id: string) => Promise<boolean>
  resetUserPassword: (id: string) => Promise<string | null>
  sendWelcomeEmail: (id: string) => Promise<boolean>
  bulkImportUsers: (file: File, onProgress?: (progress: number) => void) => Promise<boolean>
  exportUsers: () => Promise<boolean>
  
  // Utility actions
  setFilters: (filters: Partial<UserSearchParams>) => void
  clearFilters: () => void
  setCurrentUser: (user: UserProfile | null) => void
  setCurrentPage: (page: number) => void
  clearError: () => void
  setLoading: (loading: boolean) => void
}

const initialFilters: UserSearchParams = {
  page: 1,
  limit: 10
}

export const useUserStore = create<UserState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        users: [],
        currentUser: null,
        userStats: null,
        loading: false,
        error: null,
        currentPage: 1,
        totalPages: 0,
        pagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        filters: initialFilters,

        // Actions
        getUsers: async (params?: UsersListParams) => {
          set({ loading: true, error: null })
          try {
            const response = await usersService.getUsers(params)
            set({
              users: response.items,
              totalPages: response.pages,
              pagination: {
                page: response.page,
                limit: response.limit,
                total: response.total,
                totalPages: response.pages
              },
              loading: false
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar usuarios',
              loading: false 
            })
          }
        },

        getUser: async (id: string) => {
          set({ loading: true, error: null })
          try {
            const user = await usersService.getUser(id)
            set({ currentUser: user, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar usuario',
              loading: false 
            })
          }
        },

        createUser: async (userData: CreateUserRequest) => {
          set({ loading: true, error: null })
          try {
            const newUser = await usersService.createUser(userData)
            const { users } = get()
            set({ 
              users: [newUser, ...users],
              loading: false 
            })
            return newUser
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear usuario',
              loading: false 
            })
            return null
          }
        },

        updateUser: async (id: string, userData: UpdateUserRequest) => {
          set({ loading: true, error: null })
          try {
            const updatedUser = await usersService.updateUser(id, userData)
            const { users, currentUser } = get()
            set({ 
              users: users.map(user => user.id === parseInt(id) ? updatedUser : user),
              currentUser: currentUser?.id === parseInt(id) ? updatedUser : currentUser,
              loading: false 
            })
            return updatedUser
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar usuario',
              loading: false 
            })
            return null
          }
        },

        deleteUser: async (id: string) => {
          set({ loading: true, error: null })
          try {
            await usersService.deleteUser(id)
            const { users } = get()
            set({ 
              users: users.filter(user => user.id !== parseInt(id)),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar usuario',
              loading: false 
            })
            return false
          }
        },

        searchUsers: async (params: UserSearchParams) => {
          set({ loading: true, error: null })
          try {
            const query = params.query || ''
            const users = await usersService.searchUsers(query, params)
            set({ users, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al buscar usuarios',
              loading: false 
            })
          }
        },

        getUserStats: async () => {
          set({ loading: true, error: null })
          try {
            const stats = await usersService.getUserStats()
            // Transform the response to match UserStatistics interface
            const userStats: UserStatistics = {
              total_users: stats.total,
              active_users: stats.active,
              new_users_this_month: stats.recent_registrations,
              users_by_role: {
                admin: stats.by_role?.admin || 0,
                owner: stats.by_role?.owner || 0,
                trainer: stats.by_role?.trainer || 0,
                member: stats.by_role?.member || 0
              },
              users_by_status: {
                active: stats.active,
                inactive: stats.inactive,
                suspended: 0 // Default value
              },
              growth_metrics: {
                monthly_growth: 0, // Default value
                yearly_growth: 0 // Default value
              }
            }
            set({ userStats, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar estadísticas',
              loading: false 
            })
          }
        },

        activateUser: async (id: string) => {
          set({ loading: true, error: null })
          try {
            const updatedUser = await usersService.activateUser(id)
            const { users } = get()
            set({ 
              users: users.map(user => user.id === parseInt(id) ? updatedUser : user),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al activar usuario',
              loading: false 
            })
            return false
          }
        },

        deactivateUser: async (id: string) => {
          set({ loading: true, error: null })
          try {
            const updatedUser = await usersService.deactivateUser(id)
            const { users } = get()
            set({ 
              users: users.map(user => user.id === parseInt(id) ? updatedUser : user),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al desactivar usuario',
              loading: false 
            })
            return false
          }
        },

        resetUserPassword: async (id: string) => {
          set({ loading: true, error: null })
          try {
            const result = await usersService.resetUserPassword(id)
            set({ loading: false })
            return result.temporary_password
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al resetear contraseña',
              loading: false 
            })
            return null
          }
        },

        sendWelcomeEmail: async (id: string) => {
          set({ loading: true, error: null })
          try {
            await usersService.sendWelcomeEmail(id)
            set({ loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al enviar email de bienvenida',
              loading: false 
            })
            return false
          }
        },

        bulkImportUsers: async (file: File, onProgress?: (progress: number) => void) => {
          set({ loading: true, error: null })
          try {
            await usersService.bulkImportUsers(file, onProgress)
            // Refresh users list after import
            await get().getUsers()
            set({ loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al importar usuarios',
              loading: false 
            })
            return false
          }
        },

        exportUsers: async () => {
          set({ loading: true, error: null })
          try {
            await usersService.exportUsers()
            set({ loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al exportar usuarios',
              loading: false 
            })
            return false
          }
        },

        // Utility actions
        setFilters: (filters: Partial<UserSearchParams>) => {
          set((state: UserState) => ({ 
            filters: { ...state.filters, ...filters } 
          }))
        },

        clearFilters: () => {
          set({ filters: initialFilters })
        },

        setCurrentUser: (user: UserProfile | null) => {
          set({ currentUser: user })
        },

        setCurrentPage: (page: number) => {
          set({ currentPage: page })
        },

        clearError: () => {
          set({ error: null })
        },

        setLoading: (loading: boolean) => {
          set({ loading })
        }
      }),
      {
        name: 'user-store',
        partialize: (state: UserState) => ({
          filters: state.filters
        }),
        onRehydrateStorage: () => (state: UserState | undefined) => {
          // Reload users when store is rehydrated
          if (state) {
            state.getUsers()
          }
        }
      }
    ),
    {
      name: 'user-store'
    }
  )
)

export default useUserStore