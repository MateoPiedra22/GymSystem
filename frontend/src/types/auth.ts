export interface User {
  id: number
  email?: string
  first_name: string
  last_name: string
  role: 'owner' | 'trainer'
  user_type?: string
  membership_type?: string
  status: 'active' | 'inactive' | 'suspended' | 'pending'
  last_checkin?: string
  phone?: string
  is_active: boolean
  profile_picture?: string
  created_at: string
  updated_at?: string
  // For owner role - gym information
  gym_name?: string
}

export interface LoginRequest {
  role: 'owner' | 'trainer'
  password: string
  trainer_id?: number // Only for trainer login
}

export interface LoginResponse {
  user: User
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface RefreshTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface RegisterRequest {
  email: string
  password: string
  first_name: string
  last_name: string
  phone?: string
}

export interface AuthError {
  message: string
  code?: string
  details?: Record<string, any>
}

export type UserRole = 'owner' | 'trainer'

export interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (identifier: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  getCurrentUser: () => Promise<void>
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>
  clearError: () => void
}