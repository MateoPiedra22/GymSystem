import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { ExercisesService } from '../api/services/exercises'
import {
  Exercise,
  ExerciseCategory,
  MuscleGroup,
  Equipment,
  CreateExerciseRequest,
  UpdateExerciseRequest,
  ExerciseSearchParams,
  Workout,
  CreateWorkoutRequest,
  WorkoutTemplate,
  ExerciseStatistics
} from '../types/exercise'

interface ExerciseState {
  // State
  exercises: Exercise[]
  categories: ExerciseCategory[]
  muscleGroups: MuscleGroup[]
  equipment: Equipment[]
  workouts: Workout[]
  templates: WorkoutTemplate[]
  currentExercise: Exercise | null
  currentWorkout: Workout | null
  exerciseStats: ExerciseStatistics | null
  loading: boolean
  error: string | null
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  filters: ExerciseSearchParams
  
  // Actions
  getExercises: (params?: ExerciseSearchParams) => Promise<void>
  getExercise: (id: number) => Promise<void>
  createExercise: (exerciseData: CreateExerciseRequest) => Promise<Exercise | null>
  updateExercise: (id: number, exerciseData: UpdateExerciseRequest) => Promise<Exercise | null>
  deleteExercise: (id: number) => Promise<boolean>
  toggleExerciseStatus: (id: number) => Promise<boolean>
  
  // Categories
  getCategories: () => Promise<void>
  createCategory: (data: { name: string; description: string; icon?: string; color?: string }) => Promise<ExerciseCategory | null>
  updateCategory: (id: number, data: any) => Promise<ExerciseCategory | null>
  deleteCategory: (id: number) => Promise<boolean>
  
  // Muscle Groups
  getMuscleGroups: () => Promise<void>
  createMuscleGroup: (data: { name: string; description: string; body_part: 'upper' | 'lower' | 'core' | 'full_body' }) => Promise<MuscleGroup | null>
  updateMuscleGroup: (id: number, data: any) => Promise<MuscleGroup | null>
  deleteMuscleGroup: (id: number) => Promise<boolean>
  
  // Equipment
  getEquipment: () => Promise<void>
  createEquipment: (data: any) => Promise<Equipment | null>
  updateEquipment: (id: number, data: any) => Promise<Equipment | null>
  deleteEquipment: (id: number) => Promise<boolean>
  
  // Workouts
  getWorkouts: (params?: any) => Promise<void>
  getWorkout: (id: number) => Promise<void>
  createWorkout: (workoutData: CreateWorkoutRequest) => Promise<Workout | null>
  updateWorkout: (id: number, workoutData: Partial<CreateWorkoutRequest>) => Promise<Workout | null>
  deleteWorkout: (id: number) => Promise<boolean>
  startWorkout: (id: number) => Promise<boolean>
  completeWorkout: (id: number, data?: any) => Promise<boolean>
  
  // Utility actions
  setFilters: (filters: Partial<ExerciseSearchParams>) => void
  clearFilters: () => void
  setCurrentExercise: (exercise: Exercise | null) => void
  setCurrentWorkout: (workout: Workout | null) => void
  clearError: () => void
  setLoading: (loading: boolean) => void
}

const initialFilters: ExerciseSearchParams = {
  page: 1,
  limit: 10
}

export const useExerciseStore = create<ExerciseState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        exercises: [],
        categories: [],
        muscleGroups: [],
        equipment: [],
        workouts: [],
        templates: [],
        currentExercise: null,
        currentWorkout: null,
        exerciseStats: null,
        loading: false,
        error: null,
        pagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        filters: initialFilters,

        // Exercise Actions
        getExercises: async (params?: ExerciseSearchParams) => {
          set({ loading: true, error: null })
          try {
            const response = await ExercisesService.getExercises(params)
            set({
              exercises: response.items,
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
              error: error.message || 'Error al cargar ejercicios',
              loading: false 
            })
          }
        },

        getExercise: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const exercise = await ExercisesService.getExercise(id)
            set({ currentExercise: exercise, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar ejercicio',
              loading: false 
            })
          }
        },

        createExercise: async (exerciseData: CreateExerciseRequest) => {
          set({ loading: true, error: null })
          try {
            const newExercise = await ExercisesService.createExercise(exerciseData)
            const { exercises } = get()
            set({ 
              exercises: [newExercise, ...exercises],
              loading: false 
            })
            return newExercise
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear ejercicio',
              loading: false 
            })
            return null
          }
        },

        updateExercise: async (id: number, exerciseData: UpdateExerciseRequest) => {
          set({ loading: true, error: null })
          try {
            const updatedExercise = await ExercisesService.updateExercise(id, exerciseData)
            const { exercises, currentExercise } = get()
            set({ 
              exercises: exercises.map(exercise => exercise.id === id ? updatedExercise : exercise),
              currentExercise: currentExercise?.id === id ? updatedExercise : currentExercise,
              loading: false 
            })
            return updatedExercise
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar ejercicio',
              loading: false 
            })
            return null
          }
        },

        deleteExercise: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await ExercisesService.deleteExercise(id)
            const { exercises } = get()
            set({ 
              exercises: exercises.filter(exercise => exercise.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar ejercicio',
              loading: false 
            })
            return false
          }
        },

        toggleExerciseStatus: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const updatedExercise = await ExercisesService.toggleExerciseStatus(id)
            const { exercises } = get()
            set({ 
              exercises: exercises.map(exercise => exercise.id === id ? updatedExercise : exercise),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cambiar estado del ejercicio',
              loading: false 
            })
            return false
          }
        },

        // Category Actions
        getCategories: async () => {
          set({ loading: true, error: null })
          try {
            const categories = await ExercisesService.getExerciseCategories()
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
            const newCategory = await ExercisesService.createExerciseCategory(data)
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
            const updatedCategory = await ExercisesService.updateExerciseCategory(id, data)
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
            await ExercisesService.deleteExerciseCategory(id)
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

        // Muscle Group Actions
        getMuscleGroups: async () => {
          set({ loading: true, error: null })
          try {
            const muscleGroups = await ExercisesService.getMuscleGroups()
            set({ muscleGroups, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar grupos musculares',
              loading: false 
            })
          }
        },

        createMuscleGroup: async (data) => {
          set({ loading: true, error: null })
          try {
            const newMuscleGroup = await ExercisesService.createMuscleGroup(data)
            const { muscleGroups } = get()
            set({ 
              muscleGroups: [newMuscleGroup, ...muscleGroups],
              loading: false 
            })
            return newMuscleGroup
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear grupo muscular',
              loading: false 
            })
            return null
          }
        },

        updateMuscleGroup: async (id: number, data) => {
          set({ loading: true, error: null })
          try {
            const updatedMuscleGroup = await ExercisesService.updateMuscleGroup(id, data)
            const { muscleGroups } = get()
            set({ 
              muscleGroups: muscleGroups.map(group => group.id === id ? updatedMuscleGroup : group),
              loading: false 
            })
            return updatedMuscleGroup
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar grupo muscular',
              loading: false 
            })
            return null
          }
        },

        deleteMuscleGroup: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await ExercisesService.deleteMuscleGroup(id)
            const { muscleGroups } = get()
            set({ 
              muscleGroups: muscleGroups.filter(group => group.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar grupo muscular',
              loading: false 
            })
            return false
          }
        },

        // Equipment Actions
        getEquipment: async () => {
          set({ loading: true, error: null })
          try {
            const equipment = await ExercisesService.getEquipment()
            set({ equipment, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar equipamiento',
              loading: false 
            })
          }
        },

        createEquipment: async (data) => {
          set({ loading: true, error: null })
          try {
            const newEquipment = await ExercisesService.createEquipment(data)
            const { equipment } = get()
            set({ 
              equipment: [newEquipment, ...equipment],
              loading: false 
            })
            return newEquipment
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear equipamiento',
              loading: false 
            })
            return null
          }
        },

        updateEquipment: async (id: number, data) => {
          set({ loading: true, error: null })
          try {
            const updatedEquipment = await ExercisesService.updateEquipment(id, data)
            const { equipment } = get()
            set({ 
              equipment: equipment.map(item => item.id === id ? updatedEquipment : item),
              loading: false 
            })
            return updatedEquipment
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar equipamiento',
              loading: false 
            })
            return null
          }
        },

        deleteEquipment: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await ExercisesService.deleteEquipment(id)
            const { equipment } = get()
            set({ 
              equipment: equipment.filter(item => item.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar equipamiento',
              loading: false 
            })
            return false
          }
        },

        // Workout Actions
        getWorkouts: async (params?) => {
          set({ loading: true, error: null })
          try {
            const response = await ExercisesService.getWorkouts(params)
            set({ workouts: response.items, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar entrenamientos',
              loading: false 
            })
          }
        },

        getWorkout: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const workout = await ExercisesService.getWorkout(id)
            set({ currentWorkout: workout, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar entrenamiento',
              loading: false 
            })
          }
        },

        createWorkout: async (workoutData: CreateWorkoutRequest) => {
          set({ loading: true, error: null })
          try {
            const newWorkout = await ExercisesService.createWorkout(workoutData)
            const { workouts } = get()
            set({ 
              workouts: [newWorkout, ...workouts],
              loading: false 
            })
            return newWorkout
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear entrenamiento',
              loading: false 
            })
            return null
          }
        },

        updateWorkout: async (id: number, workoutData: Partial<CreateWorkoutRequest>) => {
          set({ loading: true, error: null })
          try {
            const updatedWorkout = await ExercisesService.updateWorkout(id, workoutData)
            const { workouts, currentWorkout } = get()
            set({ 
              workouts: workouts.map(workout => workout.id === id ? updatedWorkout : workout),
              currentWorkout: currentWorkout?.id === id ? updatedWorkout : currentWorkout,
              loading: false 
            })
            return updatedWorkout
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar entrenamiento',
              loading: false 
            })
            return null
          }
        },

        deleteWorkout: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await ExercisesService.deleteWorkout(id)
            const { workouts } = get()
            set({ 
              workouts: workouts.filter(workout => workout.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar entrenamiento',
              loading: false 
            })
            return false
          }
        },

        startWorkout: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const updatedWorkout = await ExercisesService.startWorkout(id)
            const { workouts } = get()
            set({ 
              workouts: workouts.map(workout => workout.id === id ? updatedWorkout : workout),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al iniciar entrenamiento',
              loading: false 
            })
            return false
          }
        },

        completeWorkout: async (id: number, _data?: any) => {
          set({ loading: true, error: null })
          try {
            // Note: This method needs to be implemented in the service
            // const updatedWorkout = await ExercisesService.completeWorkout(id, data)
            // For now, we'll just update the status locally
            const { workouts } = get()
            set({ 
              workouts: workouts.map(workout => 
                workout.id === id ? { ...workout, status: 'completed' as const } : workout
              ),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al completar entrenamiento',
              loading: false 
            })
            return false
          }
        },

        // Utility actions
        setFilters: (filters: Partial<ExerciseSearchParams>) => {
          set((state: ExerciseState) => ({ 
            filters: { ...state.filters, ...filters } 
          }))
        },

        clearFilters: () => {
          set({ filters: initialFilters })
        },

        setCurrentExercise: (exercise: Exercise | null) => {
          set({ currentExercise: exercise })
        },

        setCurrentWorkout: (workout: Workout | null) => {
          set({ currentWorkout: workout })
        },

        clearError: () => {
          set({ error: null })
        },

        setLoading: (loading: boolean) => {
          set({ loading })
        }
      }),
      {
        name: 'exercise-store',
        partialize: (state: ExerciseState) => ({
          filters: state.filters
        }),
        onRehydrateStorage: () => (state: ExerciseState | undefined) => {
          // Reload exercises when store is rehydrated
          if (state) {
            state.getExercises()
            state.getCategories()
            state.getMuscleGroups()
            state.getEquipment()
          }
        }
      }
    ),
    {
      name: 'exercise-store'
    }
  )
)

export default useExerciseStore