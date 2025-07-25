import { User } from './auth'
import { PaginationParams, PaginatedResponse, Address, ContactInfo, Status } from './common'

export interface UserProfile extends User {
  date_of_birth?: string
  gender?: 'male' | 'female' | 'other'
  address?: Address
  contact_info?: ContactInfo
  emergency_contact?: {
    name: string
    phone: string
    relationship: string
  }
  medical_conditions?: string[]
  fitness_goals?: string[]
  preferences?: {
    notifications: boolean
    newsletter: boolean
    marketing: boolean
  }
  last_login?: string
  registration_date: string
}

export interface CreateUserRequest {
  email: string
  first_name: string
  last_name: string
  password: string
  role: 'admin' | 'owner' | 'trainer' | 'member'
  phone?: string
  date_of_birth?: string
  gender?: 'male' | 'female' | 'other'
  address?: Address
  emergency_contact?: {
    name: string
    phone: string
    relationship: string
  }
  medical_conditions?: string[]
  fitness_goals?: string[]
  send_welcome_email?: boolean
}

export interface UpdateUserRequest {
  first_name?: string
  last_name?: string
  phone?: string
  date_of_birth?: string
  gender?: 'male' | 'female' | 'other'
  address?: Address
  emergency_contact?: {
    name: string
    phone: string
    relationship: string
  }
  medical_conditions?: string[]
  fitness_goals?: string[]
  preferences?: {
    notifications: boolean
    newsletter: boolean
    marketing: boolean
  }
  profile_picture?: File
}

export interface UserSearchParams extends PaginationParams {
  query?: string
  role?: string
  status?: Status
  registration_date_from?: string
  registration_date_to?: string
  last_login_from?: string
  last_login_to?: string
  has_active_membership?: boolean
}

export interface UserListResponse extends PaginatedResponse<UserProfile> {}

export interface UserStatistics {
  total_users: number
  active_users: number
  new_users_this_month: number
  users_by_role: {
    admin: number
    owner: number
    trainer: number
    member: number
  }
  users_by_status: {
    active: number
    inactive: number
    suspended: number
  }
  growth_metrics: {
    monthly_growth: number
    yearly_growth: number
  }
}

export interface UserActivity {
  id: number
  user_id: number
  activity_type: 'login' | 'logout' | 'profile_update' | 'password_change' | 'membership_purchase' | 'class_booking' | 'workout_completed'
  description: string
  timestamp: string
  ip_address?: string
  user_agent?: string
  metadata?: Record<string, any>
}

export interface UserMembershipHistory {
  id: number
  membership_type: string
  start_date: string
  end_date: string
  status: 'active' | 'expired' | 'cancelled'
  amount_paid: number
  payment_method: string
  created_at: string
}

export interface UserPaymentHistory {
  id: number
  amount: number
  currency: string
  payment_method: string
  status: 'pending' | 'completed' | 'failed' | 'refunded'
  description: string
  transaction_id?: string
  created_at: string
}

export interface UserAttendanceRecord {
  id: number
  check_in_time: string
  check_out_time?: string
  duration_minutes?: number
  facility_area?: string
  notes?: string
  created_at: string
}

export interface BulkUserImport {
  file: File
  mapping: Record<string, string>
  options: {
    skip_duplicates: boolean
    send_welcome_emails: boolean
    default_role: string
    default_password_length: number
  }
}

export interface BulkUserImportResult {
  total_processed: number
  successful_imports: number
  failed_imports: number
  errors: Array<{
    row: number
    email: string
    error: string
  }>
  imported_users: UserProfile[]
}