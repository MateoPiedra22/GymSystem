// API Client and Configuration
export { apiClient, TokenManager, ApiClientError } from './client'
export { API_CONFIG, API_ENDPOINTS, HTTP_STATUS } from './config'
export type { ApiResponse, PaginatedResponse, ApiError } from './config'

// Services
export { authService } from './services/auth'
export { usersService } from './services/users'
export { membershipsService } from './services/memberships'
export { paymentsService } from './services/payments'
export { exercisesService } from './services/exercises'
export { routinesService } from './services/routines'
export { classesService } from './services/classes'
export { employeesService } from './services/employees'

// Service Types
export type { LoginResponse, RefreshResponse } from './services/auth'
export type { UsersListParams, BulkImportResult } from './services/users'

// Note: Use apiClient directly from the import above for API calls