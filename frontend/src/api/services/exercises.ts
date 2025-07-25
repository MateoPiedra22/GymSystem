import { apiClient } from '../client'
import { API_ENDPOINTS } from '../config'
import {
  Exercise,
  ExerciseCategory,
  MuscleGroup,
  Equipment,
  CreateExerciseRequest,
  UpdateExerciseRequest,
  ExerciseSearchParams,
  ExerciseListResponse,
  Workout,

  CreateWorkoutRequest,
  WorkoutTemplate,
  ExerciseStatistics,
  PersonalRecord,
  PaginationParams
} from '../../types'

export class ExercisesService {
  // Exercises
  async getExercises(params?: ExerciseSearchParams): Promise<ExerciseListResponse> {
    return apiClient.get(API_ENDPOINTS.EXERCISES.EXERCISES, { params })
  }

  async getExercise(id: number): Promise<Exercise> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/${id}`)
  }

  async createExercise(data: CreateExerciseRequest): Promise<Exercise> {
    const formData = new FormData()
    
    // Add text fields
    Object.entries(data).forEach(([key, value]) => {
      if (key !== 'image' && key !== 'video') {
        if (Array.isArray(value)) {
          formData.append(key, JSON.stringify(value))
        } else {
          formData.append(key, String(value))
        }
      }
    })
    
    // Add files
    if (data.image) formData.append('image', data.image)
    if (data.video) formData.append('video', data.video)
    
    const response = await apiClient.postRaw(API_ENDPOINTS.EXERCISES.EXERCISES, formData)
    return response.data.data
  }

  async updateExercise(id: number, data: UpdateExerciseRequest): Promise<Exercise> {
    const formData = new FormData()
    
    // Add text fields
    Object.entries(data).forEach(([key, value]) => {
      if (key !== 'image' && key !== 'video' && value !== undefined) {
        if (Array.isArray(value)) {
          formData.append(key, JSON.stringify(value))
        } else {
          formData.append(key, String(value))
        }
      }
    })
    
    // Add files
    if (data.image) formData.append('image', data.image)
    if (data.video) formData.append('video', data.video)
    
    const response = await apiClient.postRaw(`${API_ENDPOINTS.EXERCISES.EXERCISES}/${id}`, formData)
    return response.data.data
  }

  async deleteExercise(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EXERCISES.EXERCISES}/${id}`)
  }

  async toggleExerciseStatus(id: number): Promise<Exercise> {
    return apiClient.patch(`${API_ENDPOINTS.EXERCISES.EXERCISES}/${id}/toggle-status`)
  }

  // Exercise Categories
  async getExerciseCategories(): Promise<ExerciseCategory[]> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/categories`)
  }

  async createExerciseCategory(data: {
    name: string
    description: string
    icon?: string
    color?: string
  }): Promise<ExerciseCategory> {
    return apiClient.post(`${API_ENDPOINTS.EXERCISES.EXERCISES}/categories`, data)
  }

  async updateExerciseCategory(id: number, data: {
    name?: string
    description?: string
    icon?: string
    color?: string
    is_active?: boolean
  }): Promise<ExerciseCategory> {
    return apiClient.put(`${API_ENDPOINTS.EXERCISES.EXERCISES}/categories/${id}`, data)
  }

  async deleteExerciseCategory(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EXERCISES.EXERCISES}/categories/${id}`)
  }

  // Muscle Groups
  async getMuscleGroups(): Promise<MuscleGroup[]> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/muscle-groups`)
  }

  async createMuscleGroup(data: {
    name: string
    description: string
    body_part: 'upper' | 'lower' | 'core' | 'full_body'
  }): Promise<MuscleGroup> {
    return apiClient.post(`${API_ENDPOINTS.EXERCISES.EXERCISES}/muscle-groups`, data)
  }

  async updateMuscleGroup(id: number, data: {
    name?: string
    description?: string
    body_part?: 'upper' | 'lower' | 'core' | 'full_body'
    is_active?: boolean
  }): Promise<MuscleGroup> {
    return apiClient.put(`${API_ENDPOINTS.EXERCISES.EXERCISES}/muscle-groups/${id}`, data)
  }

  async deleteMuscleGroup(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EXERCISES.EXERCISES}/muscle-groups/${id}`)
  }

  // Equipment
  async getEquipment(): Promise<Equipment[]> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/equipment`)
  }

  async createEquipment(data: {
    name: string
    description: string
    category: string
    quantity?: number
    location?: string
    cost?: number
    purchase_date?: string
  }): Promise<Equipment> {
    return apiClient.post(`${API_ENDPOINTS.EXERCISES.EXERCISES}/equipment`, data)
  }

  async updateEquipment(id: number, data: {
    name?: string
    description?: string
    category?: string
    is_available?: boolean
    quantity?: number
    location?: string
    cost?: number
    maintenance_date?: string
  }): Promise<Equipment> {
    return apiClient.put(`${API_ENDPOINTS.EXERCISES.EXERCISES}/equipment/${id}`, data)
  }

  async deleteEquipment(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EXERCISES.EXERCISES}/equipment/${id}`)
  }

  // Workouts
  async getWorkouts(params?: {
    user_id?: number
    status?: string
    date_from?: string
    date_to?: string
  } & PaginationParams): Promise<{ items: Workout[]; total: number }> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/workouts`, { params })
  }

  async getWorkout(id: number): Promise<Workout> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/workouts/${id}`)
  }

  async createWorkout(data: CreateWorkoutRequest): Promise<Workout> {
    return apiClient.post(`${API_ENDPOINTS.EXERCISES.EXERCISES}/workouts`, data)
  }

  async updateWorkout(id: number, data: Partial<CreateWorkoutRequest>): Promise<Workout> {
    return apiClient.put(`${API_ENDPOINTS.EXERCISES.EXERCISES}/workouts/${id}`, data)
  }

  async deleteWorkout(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EXERCISES.EXERCISES}/workouts/${id}`)
  }

  async startWorkout(id: number): Promise<Workout> {
    return apiClient.patch(`${API_ENDPOINTS.EXERCISES.EXERCISES}/workouts/${id}/start`)
  }

  async completeWorkout(id: number, data?: {
    duration_minutes?: number
    calories_burned?: number
    notes?: string
  }): Promise<Workout> {
    return apiClient.patch(`${API_ENDPOINTS.EXERCISES.EXERCISES}/workouts/${id}/complete`, data)
  }

  async cancelWorkout(id: number, reason?: string): Promise<Workout> {
    return apiClient.patch(`${API_ENDPOINTS.EXERCISES.EXERCISES}/workouts/${id}/cancel`, { reason })
  }

  // Workout Templates
  async getWorkoutTemplates(params?: {
    category?: string
    difficulty_level?: string
    is_public?: boolean
    created_by?: number
  } & PaginationParams): Promise<{ items: WorkoutTemplate[]; total: number }> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/workout-templates`, { params })
  }

  async getWorkoutTemplate(id: number): Promise<WorkoutTemplate> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/workout-templates/${id}`)
  }

  async createWorkoutFromTemplate(templateId: number, data: {
    workout_date: string
    notes?: string
  }): Promise<Workout> {
    return apiClient.post(`${API_ENDPOINTS.EXERCISES.EXERCISES}/workout-templates/${templateId}/create-workout`, data)
  }

  // Personal Records
  async getPersonalRecords(params?: {
    user_id?: number
    exercise_id?: number
    record_type?: string
  }): Promise<PersonalRecord[]> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/personal-records`, { params })
  }

  async createPersonalRecord(data: {
    exercise_id: number
    record_type: 'max_weight' | 'max_reps' | 'max_duration' | 'max_distance'
    value: number
    unit: string
    achieved_date: string
    workout_id?: number
    notes?: string
  }): Promise<PersonalRecord> {
    return apiClient.post(`${API_ENDPOINTS.EXERCISES.EXERCISES}/personal-records`, data)
  }

  async updatePersonalRecord(id: number, data: {
    value?: number
    achieved_date?: string
    notes?: string
  }): Promise<PersonalRecord> {
    return apiClient.put(`${API_ENDPOINTS.EXERCISES.EXERCISES}/personal-records/${id}`, data)
  }

  async deletePersonalRecord(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EXERCISES.EXERCISES}/personal-records/${id}`)
  }

  // Exercise Statistics
  async getExerciseStatistics(): Promise<ExerciseStatistics> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/statistics`)
  }

  async getExerciseUsageStats(exerciseId: number): Promise<{
    total_workouts: number
    total_users: number
    average_sets: number
    average_reps: number
    average_weight: number
    popularity_rank: number
  }> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/${exerciseId}/usage-stats`)
  }

  // Bulk Operations
  async bulkImportExercises(file: File): Promise<{
    successful: number
    failed: number
    errors: Array<{ row: number; error: string }>
  }> {
    return apiClient.uploadFile(`${API_ENDPOINTS.EXERCISES.EXERCISES}/bulk-import`, file)
  }

  async exportExercises(params?: ExerciseSearchParams): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.EXERCISES.EXERCISES}/export`, { params })
  }

  // Exercise Recommendations
  async getExerciseRecommendations(params?: {
    user_id?: number
    muscle_groups?: string[]
    equipment_available?: string[]
    difficulty_level?: string
    workout_type?: string
    limit?: number
  }): Promise<Exercise[]> {
    return apiClient.get(`${API_ENDPOINTS.EXERCISES.EXERCISES}/recommendations`, { params })
  }
}

export const exercisesService = new ExercisesService()
export default ExercisesService