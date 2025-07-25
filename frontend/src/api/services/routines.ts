import { apiClient } from '../client'
import { API_ENDPOINTS } from '../config'
import {
  Routine,

  RoutineCategory,
  CreateRoutineRequest,
  UpdateRoutineRequest,
  RoutineSearchParams,
  RoutineListResponse,
  UserRoutine,
  RoutineSession,
  AssignRoutineRequest,
  RoutineProgress,
  RoutineStatistics,
  RoutineRecommendation,
  PaginationParams
} from '../../types'

export class RoutinesService {
  // Routines
  async getRoutines(params?: RoutineSearchParams): Promise<RoutineListResponse> {
    return apiClient.get(API_ENDPOINTS.ROUTINES.ROUTINES, { params })
  }

  async getRoutine(id: number): Promise<Routine> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/${id}`)
  }

  async createRoutine(data: CreateRoutineRequest): Promise<Routine> {
    return apiClient.post(API_ENDPOINTS.ROUTINES.ROUTINES, data)
  }

  async updateRoutine(id: number, data: UpdateRoutineRequest): Promise<Routine> {
    return apiClient.put(`${API_ENDPOINTS.ROUTINES.ROUTINES}/${id}`, data)
  }

  async deleteRoutine(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.ROUTINES.ROUTINES}/${id}`)
  }

  async toggleRoutineStatus(id: number): Promise<Routine> {
    return apiClient.patch(`${API_ENDPOINTS.ROUTINES.ROUTINES}/${id}/toggle-status`)
  }

  async duplicateRoutine(id: number, data: {
    name: string
    description?: string
  }): Promise<Routine> {
    return apiClient.post(`${API_ENDPOINTS.ROUTINES.ROUTINES}/${id}/duplicate`, data)
  }

  // Routine Categories
  async getRoutineCategories(): Promise<RoutineCategory[]> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/categories`)
  }

  async createRoutineCategory(data: {
    name: string
    description: string
    icon?: string
    color?: string
  }): Promise<RoutineCategory> {
    return apiClient.post(`${API_ENDPOINTS.ROUTINES.ROUTINES}/categories`, data)
  }

  async updateRoutineCategory(id: number, data: {
    name?: string
    description?: string
    icon?: string
    color?: string
    is_active?: boolean
  }): Promise<RoutineCategory> {
    return apiClient.put(`${API_ENDPOINTS.ROUTINES.ROUTINES}/categories/${id}`, data)
  }

  async deleteRoutineCategory(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.ROUTINES.ROUTINES}/categories/${id}`)
  }

  // User Routines
  static async getUserRoutines(params?: {
    user_id?: number
    status?: string
    category_id?: number
    assigned_by?: number
  } & PaginationParams): Promise<{ items: UserRoutine[]; total: number }> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/user-routines`, { params })
  }

  static async getUserRoutine(id: number): Promise<UserRoutine> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/user-routines/${id}`)
  }

  static async assignRoutine(data: AssignRoutineRequest): Promise<UserRoutine> {
    return apiClient.post(`${API_ENDPOINTS.ROUTINES.ROUTINES}/assign`, data)
  }

  static async unassignRoutine(userRoutineId: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.ROUTINES.ROUTINES}/user-routines/${userRoutineId}`)
  }

  static async updateUserRoutine(id: number, data: {
    start_date?: string
    end_date?: string
    status?: 'active' | 'paused' | 'completed' | 'cancelled'
    notes?: string
    custom_schedule?: any
  }): Promise<UserRoutine> {
    return apiClient.put(`${API_ENDPOINTS.ROUTINES.ROUTINES}/user-routines/${id}`, data)
  }

  async pauseUserRoutine(id: number, reason?: string): Promise<UserRoutine> {
    return apiClient.patch(`${API_ENDPOINTS.ROUTINES.ROUTINES}/user-routines/${id}/pause`, { reason })
  }

  async resumeUserRoutine(id: number): Promise<UserRoutine> {
    return apiClient.patch(`${API_ENDPOINTS.ROUTINES.ROUTINES}/user-routines/${id}/resume`)
  }

  async completeUserRoutine(id: number, data?: {
    completion_notes?: string
    rating?: number
    feedback?: string
  }): Promise<UserRoutine> {
    return apiClient.patch(`${API_ENDPOINTS.ROUTINES.ROUTINES}/user-routines/${id}/complete`, data)
  }

  // Routine Sessions
  async getRoutineSessions(params?: {
    user_routine_id?: number
    user_id?: number
    status?: string
    date_from?: string
    date_to?: string
  } & PaginationParams): Promise<{ items: RoutineSession[]; total: number }> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/sessions`, { params })
  }

  async getRoutineSession(id: number): Promise<RoutineSession> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/sessions/${id}`)
  }

  async startRoutineSession(userRoutineId: number, data?: {
    scheduled_date?: string
    notes?: string
  }): Promise<RoutineSession> {
    return apiClient.post(`${API_ENDPOINTS.ROUTINES.ROUTINES}/user-routines/${userRoutineId}/start-session`, data)
  }

  async updateRoutineSession(id: number, data: {
    exercises?: Array<{
      exercise_id: number
      sets: Array<{
        reps?: number
        weight?: number
        duration?: number
        distance?: number
        rest_time?: number
        completed: boolean
        notes?: string
      }>
      completed: boolean
      notes?: string
    }>
    notes?: string
  }): Promise<RoutineSession> {
    return apiClient.put(`${API_ENDPOINTS.ROUTINES.ROUTINES}/sessions/${id}`, data)
  }

  async completeRoutineSession(id: number, data?: {
    duration_minutes?: number
    calories_burned?: number
    difficulty_rating?: number
    completion_notes?: string
  }): Promise<RoutineSession> {
    return apiClient.patch(`${API_ENDPOINTS.ROUTINES.ROUTINES}/sessions/${id}/complete`, data)
  }

  async cancelRoutineSession(id: number, reason?: string): Promise<RoutineSession> {
    return apiClient.patch(`${API_ENDPOINTS.ROUTINES.ROUTINES}/sessions/${id}/cancel`, { reason })
  }

  // Routine Progress
  async getRoutineProgress(userRoutineId: number): Promise<RoutineProgress> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/user-routines/${userRoutineId}/progress`)
  }

  async getUserRoutineProgress(userId: number, params?: {
    routine_id?: number
    date_from?: string
    date_to?: string
  }): Promise<RoutineProgress[]> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/users/${userId}/progress`, { params })
  }

  // Routine Statistics
  async getRoutineStatistics(): Promise<RoutineStatistics> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/statistics`)
  }

  async getRoutineUsageStats(routineId: number): Promise<{
    total_assignments: number
    active_users: number
    completion_rate: number
    average_duration: number
    average_rating: number
    popular_exercises: Array<{
      exercise_id: number
      exercise_name: string
      usage_count: number
    }>
  }> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/${routineId}/usage-stats`)
  }

  async getUserRoutineStats(userId: number): Promise<{
    total_routines: number
    active_routines: number
    completed_routines: number
    total_sessions: number
    total_workout_time: number
    average_session_duration: number
    favorite_categories: Array<{
      category_id: number
      category_name: string
      count: number
    }>
  }> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/users/${userId}/stats`)
  }

  // Routine Recommendations
  async getRoutineRecommendations(params?: {
    user_id?: number
    fitness_level?: string
    goals?: string[]
    available_time?: number
    equipment?: string[]
    muscle_groups?: string[]
    limit?: number
  }): Promise<RoutineRecommendation[]> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/recommendations`, { params })
  }

  async getPersonalizedRoutines(userId: number, params?: {
    fitness_level?: string
    goals?: string[]
    available_time?: number
    preferred_categories?: number[]
    limit?: number
  }): Promise<Routine[]> {
    return apiClient.get(`${API_ENDPOINTS.ROUTINES.ROUTINES}/users/${userId}/personalized`, { params })
  }

  // Bulk Operations
  async bulkAssignRoutines(data: {
    routine_id: number
    user_ids: number[]
    start_date: string
    end_date?: string
    notes?: string
  }): Promise<{
    successful: number
    failed: number
    errors: Array<{ user_id: number; error: string }>
  }> {
    return apiClient.post(`${API_ENDPOINTS.ROUTINES.ROUTINES}/bulk-assign`, data)
  }

  async bulkUpdateUserRoutines(data: {
    user_routine_ids: number[]
    updates: {
      status?: string
      end_date?: string
      notes?: string
    }
  }): Promise<{
    successful: number
    failed: number
    errors: Array<{ user_routine_id: number; error: string }>
  }> {
    return apiClient.put(`${API_ENDPOINTS.ROUTINES.ROUTINES}/user-routines/bulk-update`, data)
  }

  async bulkImportRoutines(file: File): Promise<{
    successful: number
    failed: number
    errors: Array<{ row: number; error: string }>
  }> {
    return apiClient.uploadFile(`${API_ENDPOINTS.ROUTINES.ROUTINES}/bulk-import`, file)
  }

  async exportRoutines(params?: RoutineSearchParams): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.ROUTINES.ROUTINES}/export`, { params })
  }

  async exportUserRoutines(params?: {
    user_id?: number
    status?: string
    date_from?: string
    date_to?: string
  }): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.ROUTINES.ROUTINES}/user-routines/export`, { params })
  }
}

export const routinesService = new RoutinesService()
export default RoutinesService