import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { RoutinesService } from '../api/services/routines'
import {
  Routine,
  RoutineCategory,
  CreateRoutineRequest,
  UpdateRoutineRequest,
  RoutineSearchParams,
  UserRoutine,
  RoutineSession,
  AssignRoutineRequest,
  RoutineProgress,
  RoutineStatistics
} from '../types/routine'

interface RoutineState {
  // State
  routines: Routine[]
  categories: RoutineCategory[]
  userRoutines: UserRoutine[]
  sessions: RoutineSession[]
  currentRoutine: Routine | null
  currentUserRoutine: UserRoutine | null
  currentSession: RoutineSession | null
  routineProgress: RoutineProgress | null
  routineStats: RoutineStatistics | null
  stats: RoutineStatistics | null
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
  userRoutinePagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  sessionPagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  filters: RoutineSearchParams
  
  // Actions
  getRoutines: (params?: RoutineSearchParams) => Promise<void>
  getRoutine: (id: number) => Promise<void>
  searchRoutines: (params: RoutineSearchParams) => Promise<void>
  createRoutine: (routineData: CreateRoutineRequest) => Promise<Routine | null>
  updateRoutine: (id: number, routineData: UpdateRoutineRequest) => Promise<Routine | null>
  deleteRoutine: (id: number) => Promise<boolean>
  toggleRoutineStatus: (id: number) => Promise<boolean>
  duplicateRoutine: (id: number, data: { name: string; description?: string }) => Promise<Routine | null>
  
  // Categories
  getCategories: () => Promise<void>
  createCategory: (data: { name: string; description: string; icon?: string; color?: string }) => Promise<RoutineCategory | null>
  updateCategory: (id: number, data: any) => Promise<RoutineCategory | null>
  deleteCategory: (id: number) => Promise<boolean>
  
  // User Routines
  getUserRoutines: (params?: any) => Promise<void>
  getUserRoutine: (id: number) => Promise<void>
  assignRoutine: (data: AssignRoutineRequest) => Promise<UserRoutine | null>
  unassignRoutine: (userRoutineId: number) => Promise<boolean>
  updateUserRoutine: (id: number, data: any) => Promise<UserRoutine | null>
  pauseUserRoutine: (id: number, reason?: string) => Promise<boolean>
  resumeUserRoutine: (id: number) => Promise<boolean>
  completeUserRoutine: (id: number, data?: any) => Promise<boolean>
  
  // Sessions
  getRoutineSessions: (params?: any) => Promise<void>
  getRoutineSession: (id: number) => Promise<void>
  startRoutineSession: (userRoutineId: number, data?: any) => Promise<RoutineSession | null>
  updateRoutineSession: (id: number, data: any) => Promise<RoutineSession | null>
  completeRoutineSession: (id: number, data?: any) => Promise<boolean>
  cancelRoutineSession: (id: number, reason?: string) => Promise<boolean>
  
  // Progress
  getRoutineProgress: (userRoutineId: number) => Promise<void>
  getUserRoutineProgress: (userId: number, params?: any) => Promise<void>
  
  // Statistics
  getRoutineStatistics: () => Promise<void>
  
  // Utility actions
  setFilters: (filters: Partial<RoutineSearchParams>) => void
  clearFilters: () => void
  setCurrentRoutine: (routine: Routine | null) => void
  setCurrentUserRoutine: (userRoutine: UserRoutine | null) => void
  setCurrentSession: (session: RoutineSession | null) => void
  setCurrentPage: (page: number) => void
  clearError: () => void
  setLoading: (loading: boolean) => void
}

const initialFilters: RoutineSearchParams = {
  page: 1,
  limit: 10
}

export const useRoutineStore = create<RoutineState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        routines: [],
        categories: [],
        userRoutines: [],
        sessions: [],
        currentRoutine: null,
        currentUserRoutine: null,
        currentSession: null,
        routineProgress: null,
        routineStats: null,
        stats: null,
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
        userRoutinePagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        sessionPagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        filters: initialFilters,

        // Routine Actions
        getRoutines: async (params?: RoutineSearchParams) => {
          set({ loading: true, error: null })
          try {
            const response = await RoutinesService.getRoutines(params)
            set({
              routines: response.items,
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
              error: error.message || 'Error al cargar rutinas',
              loading: false 
            })
          }
        },

        getRoutine: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const routine = await RoutinesService.getRoutine(id)
            set({ currentRoutine: routine, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar rutina',
              loading: false 
            })
          }
        },

        searchRoutines: async (params: RoutineSearchParams) => {
          set({ loading: true, error: null })
          try {
            const response = await RoutinesService.getRoutines(params)
            set({
              routines: response.items,
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
              error: error.message || 'Error al buscar rutinas',
              loading: false 
            })
          }
        },

        createRoutine: async (routineData: CreateRoutineRequest) => {
          set({ loading: true, error: null })
          try {
            const newRoutine = await RoutinesService.createRoutine(routineData)
            const { routines } = get()
            set({ 
              routines: [newRoutine, ...routines],
              loading: false 
            })
            return newRoutine
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear rutina',
              loading: false 
            })
            return null
          }
        },

        updateRoutine: async (id: number, routineData: UpdateRoutineRequest) => {
          set({ loading: true, error: null })
          try {
            const updatedRoutine = await RoutinesService.updateRoutine(id, routineData)
            const { routines, currentRoutine } = get()
            set({ 
              routines: routines.map(routine => routine.id === id ? updatedRoutine : routine),
              currentRoutine: currentRoutine?.id === id ? updatedRoutine : currentRoutine,
              loading: false 
            })
            return updatedRoutine
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar rutina',
              loading: false 
            })
            return null
          }
        },

        deleteRoutine: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await RoutinesService.deleteRoutine(id)
            const { routines } = get()
            set({ 
              routines: routines.filter(routine => routine.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar rutina',
              loading: false 
            })
            return false
          }
        },

        toggleRoutineStatus: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const updatedRoutine = await RoutinesService.toggleRoutineStatus(id)
            const { routines } = get()
            set({ 
              routines: routines.map(routine => routine.id === id ? updatedRoutine : routine),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cambiar estado de la rutina',
              loading: false 
            })
            return false
          }
        },

        duplicateRoutine: async (id: number, data: { name: string; description?: string }) => {
          set({ loading: true, error: null })
          try {
            const duplicatedRoutine = await RoutinesService.duplicateRoutine(id, data)
            const { routines } = get()
            set({ 
              routines: [duplicatedRoutine, ...routines],
              loading: false 
            })
            return duplicatedRoutine
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al duplicar rutina',
              loading: false 
            })
            return null
          }
        },

        // Category Actions
        getCategories: async () => {
          set({ loading: true, error: null })
          try {
            const categories = await RoutinesService.getRoutineCategories()
            set({ categories, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar categorías',
              loading: false 
            })
          }
        },

        createCategory: async (data) => {
          set({ loading: true, error: null })
          try {
            const newCategory = await RoutinesService.createRoutineCategory(data)
            const { categories } = get()
            set({ 
              categories: [newCategory, ...categories],
              loading: false 
            })
            return newCategory
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear categoría',
              loading: false 
            })
            return null
          }
        },

        updateCategory: async (id: number, data) => {
          set({ loading: true, error: null })
          try {
            const updatedCategory = await RoutinesService.updateRoutineCategory(id, data)
            const { categories } = get()
            set({ 
              categories: categories.map(category => category.id === id ? updatedCategory : category),
              loading: false 
            })
            return updatedCategory
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar categoría',
              loading: false 
            })
            return null
          }
        },

        deleteCategory: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await RoutinesService.deleteRoutineCategory(id)
            const { categories } = get()
            set({ 
              categories: categories.filter(category => category.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar categoría',
              loading: false 
            })
            return false
          }
        },

        // User Routine Actions
        getUserRoutines: async (params?) => {
          set({ loading: true, error: null })
          try {
            const response = await RoutinesService.getUserRoutines(params)
            set({ 
              userRoutines: response.items,
              userRoutinePagination: {
                page: params?.page || 1,
                limit: params?.limit || 10,
                total: response.total,
                totalPages: Math.ceil(response.total / (params?.limit || 10))
              },
              loading: false 
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar rutinas de usuario',
              loading: false 
            })
          }
        },

        getUserRoutine: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const userRoutine = await RoutinesService.getUserRoutine(id)
            set({ currentUserRoutine: userRoutine, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar rutina de usuario',
              loading: false 
            })
          }
        },

        assignRoutine: async (data: AssignRoutineRequest) => {
          set({ loading: true, error: null })
          try {
            const userRoutine = await RoutinesService.assignRoutine(data)
            const { userRoutines } = get()
            set({ 
              userRoutines: [userRoutine, ...userRoutines],
              loading: false 
            })
            return userRoutine
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al asignar rutina',
              loading: false 
            })
            return null
          }
        },

        unassignRoutine: async (userRoutineId: number) => {
          set({ loading: true, error: null })
          try {
            await RoutinesService.unassignRoutine(userRoutineId)
            const { userRoutines } = get()
            set({ 
              userRoutines: userRoutines.filter(ur => ur.id !== userRoutineId),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al desasignar rutina',
              loading: false 
            })
            return false
          }
        },

        updateUserRoutine: async (id: number, data) => {
          set({ loading: true, error: null })
          try {
            const updatedUserRoutine = await RoutinesService.updateUserRoutine(id, data)
            const { userRoutines, currentUserRoutine } = get()
            set({ 
              userRoutines: userRoutines.map(ur => ur.id === id ? updatedUserRoutine : ur),
              currentUserRoutine: currentUserRoutine?.id === id ? updatedUserRoutine : currentUserRoutine,
              loading: false 
            })
            return updatedUserRoutine
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar rutina de usuario',
              loading: false 
            })
            return null
          }
        },

        pauseUserRoutine: async (id: number, reason?: string) => {
          set({ loading: true, error: null })
          try {
            const updatedUserRoutine = await RoutinesService.pauseUserRoutine(id, reason)
            const { userRoutines } = get()
            set({ 
              userRoutines: userRoutines.map(ur => ur.id === id ? updatedUserRoutine : ur),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al pausar rutina',
              loading: false 
            })
            return false
          }
        },

        resumeUserRoutine: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const updatedUserRoutine = await RoutinesService.resumeUserRoutine(id)
            const { userRoutines } = get()
            set({ 
              userRoutines: userRoutines.map(ur => ur.id === id ? updatedUserRoutine : ur),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al reanudar rutina',
              loading: false 
            })
            return false
          }
        },

        completeUserRoutine: async (id: number, data?) => {
          set({ loading: true, error: null })
          try {
            const updatedUserRoutine = await RoutinesService.completeUserRoutine(id, data)
            const { userRoutines } = get()
            set({ 
              userRoutines: userRoutines.map(ur => ur.id === id ? updatedUserRoutine : ur),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al completar rutina',
              loading: false 
            })
            return false
          }
        },

        // Session Actions
        getRoutineSessions: async (params?) => {
          set({ loading: true, error: null })
          try {
            const response = await RoutinesService.getRoutineSessions(params)
            set({ 
              sessions: response.items,
              sessionPagination: {
                page: params?.page || 1,
                limit: params?.limit || 10,
                total: response.total,
                totalPages: Math.ceil(response.total / (params?.limit || 10))
              },
              loading: false 
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar sesiones',
              loading: false 
            })
          }
        },

        getRoutineSession: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const session = await RoutinesService.getRoutineSession(id)
            set({ currentSession: session, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar sesión',
              loading: false 
            })
          }
        },

        startRoutineSession: async (userRoutineId: number, data?) => {
          set({ loading: true, error: null })
          try {
            const session = await RoutinesService.startRoutineSession(userRoutineId, data)
            const { sessions } = get()
            set({ 
              sessions: [session, ...sessions],
              currentSession: session,
              loading: false 
            })
            return session
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al iniciar sesión',
              loading: false 
            })
            return null
          }
        },

        updateRoutineSession: async (id: number, data) => {
          set({ loading: true, error: null })
          try {
            const updatedSession = await RoutinesService.updateRoutineSession(id, data)
            const { sessions, currentSession } = get()
            set({ 
              sessions: sessions.map(session => session.id === id ? updatedSession : session),
              currentSession: currentSession?.id === id ? updatedSession : currentSession,
              loading: false 
            })
            return updatedSession
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar sesión',
              loading: false 
            })
            return null
          }
        },

        completeRoutineSession: async (id: number, data?) => {
          set({ loading: true, error: null })
          try {
            const updatedSession = await RoutinesService.completeRoutineSession(id, data)
            const { sessions } = get()
            set({ 
              sessions: sessions.map(session => session.id === id ? updatedSession : session),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al completar sesión',
              loading: false 
            })
            return false
          }
        },

        cancelRoutineSession: async (id: number, reason?: string) => {
          set({ loading: true, error: null })
          try {
            const updatedSession = await RoutinesService.cancelRoutineSession(id, reason)
            const { sessions } = get()
            set({ 
              sessions: sessions.map(session => session.id === id ? updatedSession : session),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cancelar sesión',
              loading: false 
            })
            return false
          }
        },

        // Progress Actions
        getRoutineProgress: async (userRoutineId: number) => {
          set({ loading: true, error: null })
          try {
            const progress = await RoutinesService.getRoutineProgress(userRoutineId)
            set({ routineProgress: progress, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar progreso',
              loading: false 
            })
          }
        },

        getUserRoutineProgress: async (userId: number, params?) => {
          set({ loading: true, error: null })
          try {
            await RoutinesService.getUserRoutineProgress(userId, params)
            // Store multiple progress records if needed
            set({ loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar progreso del usuario',
              loading: false 
            })
          }
        },

        // Statistics Actions
        getRoutineStatistics: async () => {
          set({ loading: true, error: null })
          try {
            const stats = await RoutinesService.getRoutineStatistics()
            set({ routineStats: stats, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar estadísticas',
              loading: false 
            })
          }
        },

        // Utility actions
        setFilters: (filters: Partial<RoutineSearchParams>) => {
          set((state: RoutineState) => ({ 
            filters: { ...state.filters, ...filters } 
          }))
        },

        clearFilters: () => {
          set({ filters: initialFilters })
        },

        setCurrentRoutine: (routine: Routine | null) => {
          set({ currentRoutine: routine })
        },

        setCurrentUserRoutine: (userRoutine: UserRoutine | null) => {
          set({ currentUserRoutine: userRoutine })
        },

        setCurrentSession: (session: RoutineSession | null) => {
          set({ currentSession: session })
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
        name: 'routine-store',
        partialize: (state: RoutineState) => ({
          filters: state.filters
        }),
        onRehydrateStorage: () => (state: RoutineState | undefined) => {
          // Reload routines when store is rehydrated
          if (state) {
            state.getRoutines()
            state.getCategories()
          }
        }
      }
    ),
    {
      name: 'routine-store'
    }
  )
)

export default useRoutineStore