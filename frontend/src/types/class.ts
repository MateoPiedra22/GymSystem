import { PaginationParams, PaginatedResponse } from './common'
import { User } from './auth'

export interface GymClass {
  id: number
  name: string
  description: string
  category: string
  instructor_id: number
  instructor: User
  max_capacity: number
  current_enrollment: number
  duration_minutes: number
  difficulty_level: 'beginner' | 'intermediate' | 'advanced'
  equipment_needed: string[]
  room: string
  price: number
  currency: string
  is_active: boolean
  image_url?: string
  created_at: string
  updated_at: string
}

export interface ClassSchedule {
  id: number
  class_id: number
  gym_class: GymClass
  date: string
  start_time: string
  end_time: string
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
  actual_start_time?: string
  actual_end_time?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface ClassBooking {
  id: number
  user_id: number
  user: User
  schedule_id: number
  schedule: ClassSchedule
  booking_date: string
  status: 'confirmed' | 'waitlisted' | 'cancelled' | 'attended' | 'no_show'
  payment_status: 'pending' | 'paid' | 'refunded'
  payment_id?: number
  check_in_time?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface ClassCategory {
  id: number
  name: string
  description: string
  icon?: string
  color?: string
  is_active: boolean
  class_count: number
  created_at: string
  updated_at: string
}

export interface CreateClassRequest {
  name: string
  description: string
  category: string
  instructor_id: number
  max_capacity: number
  duration_minutes: number
  difficulty_level: 'beginner' | 'intermediate' | 'advanced'
  equipment_needed: string[]
  room: string
  price: number
  currency: string
  image?: File
}

export interface UpdateClassRequest {
  name?: string
  description?: string
  category?: string
  instructor_id?: number
  max_capacity?: number
  duration_minutes?: number
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced'
  equipment_needed?: string[]
  room?: string
  price?: number
  currency?: string
  is_active?: boolean
  image?: File
}

export interface CreateScheduleRequest {
  class_id: number
  date: string
  start_time: string
  end_time: string
  notes?: string
}

export interface UpdateScheduleRequest {
  date?: string
  start_time?: string
  end_time?: string
  status?: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
  notes?: string
}

export interface BookClassRequest {
  schedule_id: number
  payment_method_id?: number
  use_membership_credit?: boolean
  notes?: string
}

export interface ClassSearchParams extends PaginationParams {
  category?: string
  instructor_id?: number
  difficulty_level?: string
  date_from?: string
  date_to?: string
  time_from?: string
  time_to?: string
  available_spots?: boolean
  price_min?: number
  price_max?: number
  room?: string
  is_active?: boolean
}

export interface ScheduleSearchParams extends PaginationParams {
  class_id?: number
  instructor_id?: number
  date_from?: string
  date_to?: string
  status?: string
  room?: string
}

export interface BookingSearchParams extends PaginationParams {
  user_id?: number
  class_id?: number
  schedule_id?: number
  status?: string
  payment_status?: string
  booking_date_from?: string
  booking_date_to?: string
  class_date_from?: string
  class_date_to?: string
}

export interface ClassListResponse extends PaginatedResponse<GymClass> {}

export interface ScheduleListResponse extends PaginatedResponse<ClassSchedule> {}

export interface BookingListResponse extends PaginatedResponse<ClassBooking> {}

export interface ClassStatistics {
  total_classes: number
  active_classes: number
  total_schedules_this_month: number
  total_bookings_this_month: number
  attendance_rate: number
  revenue_this_month: number
  popular_classes: Array<{
    class_id: number
    class_name: string
    booking_count: number
    attendance_rate: number
  }>
  classes_by_category: Array<{
    category: string
    class_count: number
    booking_count: number
  }>
  instructor_performance: Array<{
    instructor_id: number
    instructor_name: string
    classes_taught: number
    total_bookings: number
    attendance_rate: number
    average_rating: number
  }>
  peak_hours: Array<{
    hour: number
    booking_count: number
  }>
  capacity_utilization: number
}

export interface ClassAttendance {
  id: number
  booking_id: number
  user_id: number
  schedule_id: number
  check_in_time: string
  check_out_time?: string
  duration_minutes?: number
  notes?: string
  created_at: string
}

export interface ClassRating {
  id: number
  user_id: number
  class_id: number
  schedule_id: number
  rating: number
  review?: string
  created_at: string
  updated_at: string
}

export interface ClassWaitlist {
  id: number
  user_id: number
  user: User
  schedule_id: number
  schedule: ClassSchedule
  position: number
  joined_at: string
  notified_at?: string
  expires_at?: string
  status: 'active' | 'notified' | 'expired' | 'converted'
}

export interface RecurringSchedule {
  id: number
  class_id: number
  gym_class: GymClass
  days_of_week: number[]
  start_time: string
  end_time: string
  start_date: string
  end_date?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateRecurringScheduleRequest {
  class_id: number
  days_of_week: number[]
  start_time: string
  end_time: string
  start_date: string
  end_date?: string
  generate_until?: string
}

export interface ClassPackage {
  id: number
  name: string
  description: string
  class_credits: number
  price: number
  currency: string
  validity_days: number
  applicable_classes: number[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserClassPackage {
  id: number
  user_id: number
  package_id: number
  package: ClassPackage
  credits_remaining: number
  purchase_date: string
  expiry_date: string
  status: 'active' | 'expired' | 'used'
  created_at: string
  updated_at: string
}