import { PaginationParams, PaginatedResponse } from './common'
import { Exercise } from './exercise'

export interface Routine {
  id: number
  name: string
  description: string
  category: string
  difficulty_level: 'beginner' | 'intermediate' | 'advanced'
  duration_weeks: number
  sessions_per_week: number
  estimated_session_duration: number
  goals: string[]
  equipment_needed: string[]
  exercises: RoutineExercise[]
  is_public: boolean
  is_active: boolean
  created_by: number
  usage_count: number
  rating?: number
  created_at: string
  updated_at: string
}

export interface RoutineExercise {
  id: number
  routine_id: number
  exercise_id: number
  exercise: Exercise
  week_number: number
  day_number: number
  order_index: number
  sets: number
  reps?: number
  weight?: number
  duration_seconds?: number
  rest_seconds?: number
  intensity?: 'low' | 'medium' | 'high'
  notes?: string
  progression_notes?: string
}

export interface RoutineCategory {
  id: number
  name: string
  description: string
  icon?: string
  color?: string
  is_active: boolean
  routine_count: number
  created_at: string
  updated_at: string
}

export interface CreateRoutineRequest {
  name: string
  description: string
  category: string
  difficulty_level: 'beginner' | 'intermediate' | 'advanced'
  duration_weeks: number
  sessions_per_week: number
  estimated_session_duration: number
  goals: string[]
  equipment_needed: string[]
  exercises: Array<{
    exercise_id: number
    week_number: number
    day_number: number
    order_index: number
    sets: number
    reps?: number
    weight?: number
    duration_seconds?: number
    rest_seconds?: number
    intensity?: 'low' | 'medium' | 'high'
    notes?: string
    progression_notes?: string
  }>
  is_public?: boolean
}

export interface UpdateRoutineRequest {
  name?: string
  description?: string
  category?: string
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced'
  duration_weeks?: number
  sessions_per_week?: number
  estimated_session_duration?: number
  goals?: string[]
  equipment_needed?: string[]
  exercises?: Array<{
    id?: number
    exercise_id: number
    week_number: number
    day_number: number
    order_index: number
    sets: number
    reps?: number
    weight?: number
    duration_seconds?: number
    rest_seconds?: number
    intensity?: 'low' | 'medium' | 'high'
    notes?: string
    progression_notes?: string
  }>
  is_public?: boolean
  is_active?: boolean
}

export interface RoutineSearchParams extends PaginationParams {
  category?: string
  difficulty_level?: string
  duration_weeks_min?: number
  duration_weeks_max?: number
  sessions_per_week?: number
  goals?: string[]
  equipment_needed?: string[]
  is_public?: boolean
  is_active?: boolean
  created_by?: number
  rating_min?: number
}

export interface RoutineListResponse extends PaginatedResponse<Routine> {}

export interface UserRoutine {
  id: number
  user_id: number
  routine_id: number
  routine: Routine
  start_date: string
  end_date?: string
  current_week: number
  current_day: number
  status: 'active' | 'paused' | 'completed' | 'cancelled'
  progress_percentage: number
  sessions_completed: number
  total_sessions: number
  last_session_date?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface RoutineSession {
  id: number
  user_routine_id: number
  week_number: number
  day_number: number
  session_date: string
  start_time?: string
  end_time?: string
  duration_minutes?: number
  exercises_completed: number
  total_exercises: number
  calories_burned?: number
  notes?: string
  status: 'scheduled' | 'in_progress' | 'completed' | 'skipped'
  created_at: string
  updated_at: string
}

export interface AssignRoutineRequest {
  user_id: number
  routine_id: number
  start_date: string
  custom_schedule?: {
    days_of_week: number[]
    preferred_time?: string
  }
  notes?: string
}

export interface RoutineProgress {
  user_routine_id: number
  total_weeks: number
  completed_weeks: number
  current_week: number
  total_sessions: number
  completed_sessions: number
  skipped_sessions: number
  progress_percentage: number
  weekly_progress: Array<{
    week_number: number
    sessions_completed: number
    sessions_total: number
    completion_percentage: number
  }>
  exercise_progress: Array<{
    exercise_id: number
    exercise_name: string
    sessions_completed: number
    best_performance: {
      weight?: number
      reps?: number
      duration?: number
    }
    improvement_percentage: number
  }>
}

export interface RoutineStatistics {
  total_routines: number
  active_user_routines: number
  completed_routines: number
  popular_routines: Array<{
    routine_id: number
    routine_name: string
    usage_count: number
    completion_rate: number
  }>
  routines_by_category: Array<{
    category: string
    count: number
  }>
  routines_by_difficulty: Array<{
    difficulty: string
    count: number
  }>
  average_completion_rate: number
  most_effective_routines: Array<{
    routine_id: number
    routine_name: string
    completion_rate: number
    user_rating: number
  }>
}

export interface RoutineRecommendation {
  routine_id: number
  routine: Routine
  match_score: number
  reasons: string[]
  estimated_difficulty: 'easy' | 'moderate' | 'challenging'
  time_commitment: string
}