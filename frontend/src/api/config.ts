// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  API_VERSION: 'v1',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    LOGOUT: '/api/v1/auth/logout',
    REFRESH: '/api/v1/auth/refresh',
    ME: '/api/v1/auth/me',
    PROFILE: '/api/v1/auth/profile',
    CHANGE_PASSWORD: '/api/v1/auth/change-password',
    FORGOT_PASSWORD: '/api/v1/auth/forgot-password',
    RESET_PASSWORD: '/api/v1/auth/reset-password',
    VERIFY_EMAIL: '/api/v1/auth/verify-email',
    RESEND_VERIFICATION: '/api/v1/auth/resend-verification',
  },
  
  // Users
  USERS: {
    LIST: '/api/v1/users',
    CREATE: '/api/v1/users',
    GET: (id: string) => `/api/v1/users/${id}`,
    UPDATE: (id: string) => `/api/v1/users/${id}`,
    DELETE: (id: string) => `/api/v1/users/${id}`,
    SEARCH: '/api/v1/users/search',
    BULK_IMPORT: '/api/v1/users/bulk-import',
    STATS: '/api/v1/users/stats',
  },
  
  // Memberships
  MEMBERSHIPS: {
    LIST: '/api/v1/memberships',
    CREATE: '/api/v1/memberships',
    GET: (id: string) => `/api/v1/memberships/${id}`,
    UPDATE: (id: string) => `/api/v1/memberships/${id}`,
    DELETE: (id: string) => `/api/v1/memberships/${id}`,
    TYPES: '/api/v1/memberships/types',
    STATS: '/api/v1/memberships/stats',
    PLANS: '/api/v1/memberships/plans',
    USER_MEMBERSHIPS: '/api/v1/memberships/user-memberships',
    STATISTICS: '/api/v1/memberships/statistics',
  },
  
  // Payments
  PAYMENTS: {
    LIST: '/api/v1/payments',
    PAYMENTS: '/api/v1/payments',
    CREATE: '/api/v1/payments',
    GET: (id: string) => `/api/v1/payments/${id}`,
    UPDATE: (id: string) => `/api/v1/payments/${id}`,
    DELETE: (id: string) => `/api/v1/payments/${id}`,
    STATS: '/api/v1/payments/stats',
    STATISTICS: '/api/v1/payments/statistics',
    PENDING: '/api/v1/payments/pending',
    OVERDUE: '/api/v1/payments/overdue',
    PAYMENT_METHODS: '/api/v1/payments/methods',
    INVOICES: '/api/v1/payments/invoices',
    SUBSCRIPTIONS: '/api/v1/payments/subscriptions',
  },
  
  // Exercises
  EXERCISES: {
    LIST: '/api/v1/exercises',
    EXERCISES: '/api/v1/exercises',
    CREATE: '/api/v1/exercises',
    GET: (id: string) => `/api/v1/exercises/${id}`,
    UPDATE: (id: string) => `/api/v1/exercises/${id}`,
    DELETE: (id: string) => `/api/v1/exercises/${id}`,
    CATEGORIES: '/api/v1/exercises/categories',
    MUSCLE_GROUPS: '/api/v1/exercises/muscle-groups',
  },
  
  // Routines
  ROUTINES: {
    LIST: '/api/v1/routines',
    ROUTINES: '/api/v1/routines',
    CREATE: '/api/v1/routines',
    GET: (id: string) => `/api/v1/routines/${id}`,
    UPDATE: (id: string) => `/api/v1/routines/${id}`,
    DELETE: (id: string) => `/api/v1/routines/${id}`,
    TEMPLATES: '/api/v1/routines/templates',
    ASSIGN: '/api/v1/routines/assign',
  },
  
  // Classes
  CLASSES: {
    LIST: '/api/v1/classes',
    CLASSES: '/api/v1/classes',
    CREATE: '/api/v1/classes',
    GET: (id: string) => `/api/v1/classes/${id}`,
    UPDATE: (id: string) => `/api/v1/classes/${id}`,
    DELETE: (id: string) => `/api/v1/classes/${id}`,
    SCHEDULE: '/api/v1/classes/schedule',
    SCHEDULES: '/api/v1/classes/schedules',
    BOOKINGS: '/api/v1/classes/bookings',
    BOOK: (id: string) => `/api/v1/classes/${id}/book`,
    CANCEL: (id: string) => `/api/v1/classes/${id}/cancel`,
    STATS: '/api/v1/classes/stats',
  },
  
  // Employees
  EMPLOYEES: {
    LIST: '/api/v1/employees',
    EMPLOYEES: '/api/v1/employees',
    CREATE: '/api/v1/employees',
    GET: (id: string) => `/api/v1/employees/${id}`,
    UPDATE: (id: string) => `/api/v1/employees/${id}`,
    DELETE: (id: string) => `/api/v1/employees/${id}`,
    ROLES: '/api/v1/employees/roles',
    PERMISSIONS: '/api/v1/employees/permissions',
    DEPARTMENTS: '/api/v1/employees/departments',
    POSITIONS: '/api/v1/employees/positions',
    CERTIFICATIONS: '/api/v1/employees/certifications',
    SCHEDULES: '/api/v1/employees/schedules',
    SHIFTS: '/api/v1/employees/shifts',
    TIME_ENTRIES: '/api/v1/employees/time-entries',
    LEAVE_REQUESTS: '/api/v1/employees/leave-requests',
    PERFORMANCE_REVIEWS: '/api/v1/employees/performance-reviews',
    PAYROLL: '/api/v1/employees/payroll',
    STATISTICS: '/api/v1/employees/statistics',
    BULK_IMPORT: '/api/v1/employees/bulk-import',
    EXPORT: '/api/v1/employees/export',
  },
  
  // Reports
  REPORTS: {
    DASHBOARD: '/api/v1/reports/dashboard',
    REVENUE: '/api/v1/reports/revenue',
    MEMBERSHIP: '/api/v1/reports/membership',
    ATTENDANCE: '/api/v1/reports/attendance',
    EXPORT: '/api/v1/reports/export',
  },
  
  // Configuration
  CONFIG: {
    GET: '/api/v1/config',
    UPDATE: '/api/v1/config',
    BRAND: '/api/v1/config/brand',
    NOTIFICATIONS: '/api/v1/config/notifications',
  },
  
  // Health
  HEALTH: '/health',
} as const

// Request/Response Types
export interface ApiResponse<T = any> {
  data: T
  message?: string
  success: boolean
  errors?: string[]
}

export interface PaginatedResponse<T = any> {
  data: T[]
  total: number
  page: number
  limit: number
  totalPages: number
}

export interface ApiError {
  message: string
  code?: string
  details?: any
}

// HTTP Status Codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_SERVER_ERROR: 500,
} as const