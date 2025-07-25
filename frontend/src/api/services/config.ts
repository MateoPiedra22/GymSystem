import { apiClient } from '../client'
import { API_ENDPOINTS } from '../config'
import type { ApiResponse } from '../config'
import type {
  SystemConfig,
  BrandConfig,
  NotificationConfig,
  ConfigUpdateRequest,
  BrandConfigUpdateRequest,
  NotificationConfigUpdateRequest
} from '../../types/config'

export class ConfigService {
  // Get system configuration
  async getConfig(): Promise<ApiResponse<SystemConfig>> {
    const response = await apiClient.get(API_ENDPOINTS.CONFIG.GET)
    return response.data
  }

  // Update system configuration
  async updateConfig(data: ConfigUpdateRequest): Promise<ApiResponse<SystemConfig>> {
    const response = await apiClient.put(API_ENDPOINTS.CONFIG.UPDATE, data)
    return response.data
  }

  // Get brand configuration
  async getBrandConfig(): Promise<ApiResponse<BrandConfig>> {
    const response = await apiClient.get(API_ENDPOINTS.CONFIG.BRAND)
    return response.data
  }

  // Update brand configuration
  async updateBrandConfig(data: BrandConfigUpdateRequest): Promise<ApiResponse<BrandConfig>> {
    const response = await apiClient.put(API_ENDPOINTS.CONFIG.BRAND, data)
    return response.data
  }

  // Get notification configuration
  async getNotificationConfig(): Promise<ApiResponse<NotificationConfig>> {
    const response = await apiClient.get(API_ENDPOINTS.CONFIG.NOTIFICATIONS)
    return response.data
  }

  // Update notification configuration
  async updateNotificationConfig(data: NotificationConfigUpdateRequest): Promise<ApiResponse<NotificationConfig>> {
    const response = await apiClient.put(API_ENDPOINTS.CONFIG.NOTIFICATIONS, data)
    return response.data
  }

  // Upload brand logo
  async uploadLogo(file: File): Promise<ApiResponse<{ url: string }>> {
    const formData = new FormData()
    formData.append('logo', file)
    
    const response = await apiClient.post(`${API_ENDPOINTS.CONFIG.BRAND}/logo`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }

  // Upload brand favicon
  async uploadFavicon(file: File): Promise<ApiResponse<{ url: string }>> {
    const formData = new FormData()
    formData.append('favicon', file)
    
    const response = await apiClient.post(`${API_ENDPOINTS.CONFIG.BRAND}/favicon`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }

  // Reset configuration to defaults
  async resetConfig(): Promise<ApiResponse<SystemConfig>> {
    const response = await apiClient.post(`${API_ENDPOINTS.CONFIG.UPDATE}/reset`)
    return response.data
  }

  // Test email configuration
  async testEmailConfig(email: string): Promise<ApiResponse<{ success: boolean }>> {
    const response = await apiClient.post(`${API_ENDPOINTS.CONFIG.NOTIFICATIONS}/test-email`, { email })
    return response.data
  }

  // Test SMS configuration
  async testSmsConfig(phone: string): Promise<ApiResponse<{ success: boolean }>> {
    const response = await apiClient.post(`${API_ENDPOINTS.CONFIG.NOTIFICATIONS}/test-sms`, { phone })
    return response.data
  }
}

// Create and export service instance
export const configService = new ConfigService()

export default ConfigService