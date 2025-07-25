import { apiClient } from '../client'
import { API_ENDPOINTS } from '../config'
import { UserProfile, CreateUserRequest, UpdateUserRequest, UserSearchParams, PaginatedResponse } from '../../types'

export interface UsersListParams {
  page?: number
  limit?: number
  search?: string
  role?: string
  status?: string
  membership_type?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface BulkImportResult {
  success_count: number
  error_count: number
  errors: Array<{
    row: number
    message: string
  }>
}

class UsersService {
  /**
   * Get paginated list of users
   */
  async getUsers(params: UsersListParams = {}): Promise<PaginatedResponse<UserProfile>> {
    const queryParams = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value.toString())
      }
    })

    const url = `${API_ENDPOINTS.USERS.LIST}?${queryParams.toString()}`
    return apiClient.get<PaginatedResponse<UserProfile>>(url)
  }

  /**
   * Get user by ID
   */
  async getUser(id: string): Promise<UserProfile> {
    return apiClient.get<UserProfile>(API_ENDPOINTS.USERS.GET(id))
  }

  /**
   * Create new user
   */
  async createUser(userData: CreateUserRequest): Promise<UserProfile> {
    return apiClient.post<UserProfile>(API_ENDPOINTS.USERS.CREATE, userData)
  }

  /**
   * Update user
   */
  async updateUser(id: string, userData: UpdateUserRequest): Promise<UserProfile> {
    return apiClient.put<UserProfile>(API_ENDPOINTS.USERS.UPDATE(id), userData)
  }

  /**
   * Delete user
   */
  async deleteUser(id: string): Promise<void> {
    return apiClient.delete(API_ENDPOINTS.USERS.DELETE(id))
  }

  /**
   * Search users
   */
  async searchUsers(query: string, filters?: UserSearchParams): Promise<UserProfile[]> {
    const params = new URLSearchParams({ q: query })
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString())
        }
      })
    }

    const url = `${API_ENDPOINTS.USERS.SEARCH}?${params.toString()}`
    return apiClient.get<UserProfile[]>(url)
  }

  /**
   * Bulk import users from CSV
   */
  async bulkImportUsers(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<BulkImportResult> {
    return apiClient.uploadFile<BulkImportResult>(
      API_ENDPOINTS.USERS.BULK_IMPORT,
      file,
      onProgress
    )
  }

  /**
   * Export users to CSV
   */
  async exportUsers(filters?: UserSearchParams): Promise<void> {
    const params = new URLSearchParams()
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString())
        }
      })
    }

    const url = `${API_ENDPOINTS.USERS.LIST}/export?${params.toString()}`
    return apiClient.downloadFileAndSave(url, 'users_export.csv')
  }

  /**
   * Get user statistics
   */
  async getUserStats(): Promise<{
    total: number
    active: number
    inactive: number
    by_role: Record<string, number>
    by_membership: Record<string, number>
    recent_registrations: number
  }> {
    return apiClient.get(API_ENDPOINTS.USERS.STATS)
  }

  /**
   * Activate user
   */
  async activateUser(id: string): Promise<UserProfile> {
    return apiClient.post<UserProfile>(`${API_ENDPOINTS.USERS.GET(id)}/activate`)
  }

  /**
   * Deactivate user
   */
  async deactivateUser(id: string): Promise<UserProfile> {
    return apiClient.post<UserProfile>(`${API_ENDPOINTS.USERS.GET(id)}/deactivate`)
  }

  /**
   * Reset user password
   */
  async resetUserPassword(id: string): Promise<{ temporary_password: string }> {
    return apiClient.post(`${API_ENDPOINTS.USERS.GET(id)}/reset-password`)
  }

  /**
   * Send welcome email to user
   */
  async sendWelcomeEmail(id: string): Promise<void> {
    return apiClient.post(`${API_ENDPOINTS.USERS.GET(id)}/send-welcome`)
  }

  /**
   * Get user's membership history
   */
  async getUserMembershipHistory(id: string): Promise<any[]> {
    return apiClient.get(`${API_ENDPOINTS.USERS.GET(id)}/membership-history`)
  }

  /**
   * Get user's payment history
   */
  async getUserPaymentHistory(id: string): Promise<any[]> {
    return apiClient.get(`${API_ENDPOINTS.USERS.GET(id)}/payment-history`)
  }

  /**
   * Get user's attendance history
   */
  async getUserAttendanceHistory(id: string, params?: {
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<any[]> {
    const queryParams = new URLSearchParams()
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, value.toString())
        }
      })
    }

    const url = `${API_ENDPOINTS.USERS.GET(id)}/attendance?${queryParams.toString()}`
    return apiClient.get(url)
  }
}

export const usersService = new UsersService()
export default usersService