import { PaginationParams, PaginatedResponse } from './common'

export interface Exercise {
  id: number
  name: string
  description: string
  category: string
  muscle_groups: string[]
  equipment_needed: string[]
  difficulty_level: 'beginner' | 'intermediate' | 'advanced'
  instructions: string[]
  tips?: string[]
  warnings?: string[]
  image_url?: string
  video_url?: string
  duration_minutes?: number
  calories_burned_per_minute?: number
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
}

export interface ExerciseCategory {
  id: number
  name: string
  description: string
  icon?: string
  color?: string
  is_active: boolean
  exercise_count: number
  created_at: string
  updated_at: string
}

export interface MuscleGroup {
  id: number
  name: string
  description: string
  body_part: 'upper' | 'lower' | 'core' | 'full_body'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Equipment {
  id: number
  name: string
  description: string
  category: string
  is_available: boolean
  quantity?: number
  maintenance_date?: string
  purchase_date?: string
  cost?: number
  location?: string
  created_at: string
  updated_at: string
}

export interface CreateExerciseRequest {
  name: string
  description: string
  category: string
  muscle_groups: string[]
  equipment_needed: string[]
  difficulty_level: 'beginner' | 'intermediate' | 'advanced'
  instructions: string[]
  tips?: string[]
  warnings?: string[]
  duration_minutes?: number
  calories_burned_per_minute?: number
  image?: File
  video?: File
}

export interface UpdateExerciseRequest {
  name?: string
  description?: string
  category?: string
  muscle_groups?: string[]
  equipment_needed?: string[]
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced'
  instructions?: string[]
  tips?: string[]
  warnings?: string[]
  duration_minutes?: number
  calories_burned_per_minute?: number
  image?: File
  video?: File
  is_active?: boolean
}

export interface ExerciseSearchParams extends PaginationParams {
  category?: string
  muscle_groups?: string[]
  equipment_needed?: string[]
  difficulty_level?: string
  duration_min?: number
  duration_max?: number
  calories_min?: number
  calories_max?: number
  is_active?: boolean
  created_by?: number
}

export interface ExerciseListResponse extends PaginatedResponse<Exercise> {}

export interface ExerciseSet {
  id: number
  exercise_id: number
  reps?: number
  weight?: number
  duration_seconds?: number
  distance?: number
  rest_seconds?: number
  notes?: string
  completed: boolean
  completed_at?: string
}

export interface WorkoutExercise {
  id: number
  workout_id: number
  exercise_id: number
  exercise: Exercise
  order_index: number
  sets: ExerciseSet[]
  target_sets?: number
  target_reps?: number
  target_weight?: number
  target_duration?: number
  notes?: string
  completed: boolean
  completed_at?: string
}

export interface Workout {
  id: number
  user_id: number
  name: string
  description?: string
  workout_date: string
  start_time?: string
  end_time?: string
  duration_minutes?: number
  calories_burned?: number
  exercises: WorkoutExercise[]
  notes?: string
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled'
  created_at: string
  updated_at: string
}

export interface CreateWorkoutRequest {
  name: string
  description?: string
  workout_date: string
  exercises: Array<{
    exercise_id: number
    order_index: number
    target_sets?: number
    target_reps?: number
    target_weight?: number
    target_duration?: number
    notes?: string
  }>
  notes?: string
}

export interface WorkoutTemplate {
  id: number
  name: string
  description?: string
  category: string
  difficulty_level: 'beginner' | 'intermediate' | 'advanced'
  estimated_duration: number
  exercises: Array<{
    exercise_id: number
    exercise: Exercise
    order_index: number
    sets: number
    reps?: number
    weight?: number
    duration_seconds?: number
    rest_seconds?: number
    notes?: string
  }>
  is_public: boolean
  created_by: number
  usage_count: number
  rating?: number
  created_at: string
  updated_at: string
}

export interface ExerciseStatistics {
  total_exercises: number
  approved_exercises: number
  avg_rating: number
  total_muscle_groups: number
  exercises_by_category: Array<{
    category: string
    count: number
  }>
  exercises_by_difficulty: Array<{
    difficulty: string
    count: number
  }>
  most_popular_exercises: Array<{
    exercise_id: number
    exercise_name: string
    usage_count: number
  }>
  equipment_usage: Array<{
    equipment: string
    exercise_count: number
  }>
}

export interface PersonalRecord {
  id: number
  user_id: number
  exercise_id: number
  exercise: Exercise
  record_type: 'max_weight' | 'max_reps' | 'max_duration' | 'max_distance'
  value: number
  unit: string
  achieved_date: string
  workout_id?: number
  notes?: string
  created_at: string
  updated_at: string
}