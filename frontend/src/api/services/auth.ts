import { apiClient } from '../client'
import { API_ENDPOINTS } from '../config'
import { User, ChangePasswordRequest } from '../../types/auth'

export interface LoginCredentials {
  email: string // email for login
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RegisterRequest {
  email: string
  password: string
  first_name: string
  last_name: string
  phone?: string
}

export interface RegisterResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

class AuthService {
  /**
   * Login user with credentials
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    console.log('🔑 AuthService.login called with:', { email: credentials.email })
    
    // Transform identifier to email for backend compatibility
    const loginData = {
      email: credentials.email,
      password: credentials.password
    }
    
    console.log('🌐 Making API call to:', API_ENDPOINTS.AUTH.LOGIN)
    console.log('📤 Request data:', { email: loginData.email, password: '[HIDDEN]' })
    
    try {
      // Use postRaw to get the direct response since login doesn't follow ApiResponse format
      const response = await apiClient.postRaw(
        API_ENDPOINTS.AUTH.LOGIN,
        loginData
      )
      
      console.log('📥 Raw API response:', {
        status: response.status,
        statusText: response.statusText,
        hasData: !!response.data,
        dataKeys: response.data ? Object.keys(response.data) : []
      })
      
      const loginResponse = response.data as LoginResponse
      
      console.log('🔍 Parsed login response:', {
        hasAccessToken: !!loginResponse.access_token,
        hasRefreshToken: !!loginResponse.refresh_token,
        tokenType: loginResponse.token_type,
        expiresIn: loginResponse.expires_in,
        userEmail: loginResponse.user?.email
      })
      
      // Store tokens
      apiClient.setAuthToken(loginResponse.access_token)
      console.log('💾 Access token stored in apiClient')
      
      return loginResponse
    } catch (error: any) {
      console.error('💥 AuthService.login error:', {
        message: error.message,
        status: error.status,
        code: error.code,
        response: error.response?.data,
        fullError: error
      })
      throw error
    }
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT)
    } catch (error) {
      // Even if logout fails on server, clear local tokens
      console.warn('Logout request failed, but clearing local tokens:', error)
    } finally {
      apiClient.clearAuthToken()
    }
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>(API_ENDPOINTS.AUTH.ME)
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<RefreshResponse> {
    // Use postRaw to get the direct response since refresh doesn't follow ApiResponse format
    // Send refresh_token as query parameter
    const response = await apiClient.postRaw(
      `${API_ENDPOINTS.AUTH.REFRESH}?refresh_token=${encodeURIComponent(refreshToken)}`
    )
    
    const refreshResponse = response.data as RefreshResponse
    
    // Update stored token
    apiClient.setAuthToken(refreshResponse.access_token)
    
    return refreshResponse
  }

  /**
   * Register new user
   */
  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    // Use postRaw to get the direct response since register doesn't follow ApiResponse format
    const response = await apiClient.postRaw(
      API_ENDPOINTS.AUTH.REGISTER,
      userData
    )
    
    const registerResponse = response.data as RegisterResponse
    
    // Store tokens
    apiClient.setAuthToken(registerResponse.access_token)
    
    return registerResponse
  }

  /**
   * Change user password
   */
  async changePassword(data: ChangePasswordRequest): Promise<void> {
    return apiClient.post(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, data)
  }

  /**
   * Update user profile
   */
  async updateProfile(userData: Partial<User>): Promise<User> {
    return apiClient.put<User>(API_ENDPOINTS.AUTH.PROFILE, userData)
  }

  /**
   * Forgot password - send reset email
   */
  async forgotPassword(email: string): Promise<void> {
    return apiClient.post(API_ENDPOINTS.AUTH.FORGOT_PASSWORD, { email })
  }

  /**
   * Reset password with token
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    return apiClient.post(API_ENDPOINTS.AUTH.RESET_PASSWORD, {
      token,
      new_password: newPassword
    })
  }

  /**
   * Verify email with token
   */
  async verifyEmail(token: string): Promise<void> {
    return apiClient.post(API_ENDPOINTS.AUTH.VERIFY_EMAIL, { token })
  }

  /**
   * Resend email verification
   */
  async resendVerification(): Promise<void> {
    return apiClient.post(API_ENDPOINTS.AUTH.RESEND_VERIFICATION)
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!apiClient.getAuthToken()
  }

  /**
   * Get stored auth token
   */
  getAuthToken(): string | null {
    return apiClient.getAuthToken()
  }

  /**
   * Clear authentication data
   */
  clearAuth(): void {
    apiClient.clearAuthToken()
  }
}

export const authService = new AuthService()
export default authService