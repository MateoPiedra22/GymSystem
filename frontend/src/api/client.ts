import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { API_CONFIG, HTTP_STATUS } from './config'
import type { ApiResponse } from './config'

// Custom error class for API errors
export class ApiClientError extends Error {
  public status?: number
  public code?: string
  public details?: any

  constructor(message: string, status?: number, code?: string, details?: any) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.code = code
    this.details = details
  }
}

// Token management
class TokenManager {
  private static readonly ACCESS_TOKEN_KEY = 'gym_access_token'
  private static readonly REFRESH_TOKEN_KEY = 'gym_refresh_token'

  static getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY)
  }

  static setAccessToken(token: string): void {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, token)
  }

  static getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY)
  }

  static setRefreshToken(token: string): void {
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token)
  }

  static clearTokens(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY)
    localStorage.removeItem(this.REFRESH_TOKEN_KEY)
  }

  static setTokens(accessToken: string, refreshToken?: string): void {
    this.setAccessToken(accessToken)
    if (refreshToken) {
      this.setRefreshToken(refreshToken)
    }
  }
}

// API Client class
class ApiClient {
  private axiosInstance: AxiosInstance
  private isRefreshing = false
  private failedQueue: Array<{
    resolve: (value: any) => void
    reject: (error: any) => void
  }> = []

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: API_CONFIG.BASE_URL,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const token = TokenManager.getAccessToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId()

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.axiosInstance.interceptors.response.use(
      (response) => {
        return response
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

        if (error.response?.status === HTTP_STATUS.UNAUTHORIZED && !originalRequest._retry) {
          if (this.isRefreshing) {
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject })
            }).then((token) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`
              }
              return this.axiosInstance(originalRequest)
            }).catch((err) => {
              return Promise.reject(err)
            })
          }

          originalRequest._retry = true
          this.isRefreshing = true

          try {
            const refreshToken = TokenManager.getRefreshToken()
            if (!refreshToken) {
              throw new Error('No refresh token available')
            }

            const response = await this.axiosInstance.post(
              `/api/v1/auth/refresh?refresh_token=${encodeURIComponent(refreshToken)}`
            )

            const { access_token, refresh_token: newRefreshToken } = response.data
            TokenManager.setTokens(access_token, newRefreshToken)

            this.processQueue(null, access_token)

            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access_token}`
            }

            return this.axiosInstance(originalRequest)
          } catch (refreshError) {
            this.processQueue(refreshError, null)
            TokenManager.clearTokens()
            window.location.href = '/login'
            return Promise.reject(refreshError)
          } finally {
            this.isRefreshing = false
          }
        }

        return Promise.reject(this.handleError(error))
      }
    )
  }

  private processQueue(error: any, token: string | null): void {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error)
      } else {
        resolve(token)
      }
    })

    this.failedQueue = []
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private handleError(error: AxiosError): ApiClientError {
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      const message = (data as any)?.message || error.message || 'An error occurred'
      const code = (data as any)?.code
      const details = (data as any)?.details

      return new ApiClientError(message, status, code, details)
    } else if (error.request) {
      // Request was made but no response received
      return new ApiClientError('Network error - no response received', undefined, 'NETWORK_ERROR')
    } else {
      // Something else happened
      return new ApiClientError(error.message || 'Unknown error occurred', undefined, 'UNKNOWN_ERROR')
    }
  }

  // HTTP Methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.get<ApiResponse<T>>(url, config)
    return response.data.data
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.post<ApiResponse<T>>(url, data, config)
    return response.data.data
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.put<ApiResponse<T>>(url, data, config)
    return response.data.data
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.patch<ApiResponse<T>>(url, data, config)
    return response.data.data
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.delete<ApiResponse<T>>(url, config)
    return response.data.data
  }

  // Raw response methods (for cases where you need full response)
  async getRaw(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return this.axiosInstance.get(url, config)
  }

  async postRaw(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return this.axiosInstance.post(url, data, config)
  }

  // File upload
  async uploadFile<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    }

    const response = await this.axiosInstance.post<ApiResponse<T>>(url, formData, config)
    return response.data.data
  }

  // Download file
  async downloadFile(url: string, config?: AxiosRequestConfig): Promise<Blob> {
    const response = await this.axiosInstance.get(url, {
      ...config,
      responseType: 'blob',
    })
    return new Blob([response.data])
  }

  // Download file and trigger browser download
  async downloadFileAndSave(url: string, filename?: string): Promise<void> {
    const blob = await this.downloadFile(url)
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.axiosInstance.get('/health')
      return true
    } catch {
      return false
    }
  }

  // Token management methods
  setAuthToken(token: string): void {
    TokenManager.setAccessToken(token)
  }

  clearAuthToken(): void {
    TokenManager.clearTokens()
  }

  getAuthToken(): string | null {
    return TokenManager.getAccessToken()
  }
}

// Export singleton instance
export const apiClient = new ApiClient()
export { TokenManager }
export default apiClient