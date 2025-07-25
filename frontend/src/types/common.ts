export interface PaginationParams {
  page?: number
  limit?: number
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
  errors?: Record<string, string[]>
}

export interface ApiError {
  message: string
  code?: string
  status?: number
  details?: Record<string, any>
}

export interface SelectOption {
  value: string | number
  label: string
  disabled?: boolean
}

export interface TableColumn {
  key: string
  label: string
  sortable?: boolean
  width?: string
  align?: 'left' | 'center' | 'right'
  render?: (value: any, row: any) => React.ReactNode
}

export interface FilterOption {
  key: string
  label: string
  type: 'text' | 'select' | 'date' | 'daterange' | 'number'
  options?: SelectOption[]
  placeholder?: string
}

export interface BulkAction {
  key: string
  label: string
  icon?: string
  variant?: 'default' | 'destructive' | 'outline'
  requiresConfirmation?: boolean
  confirmationMessage?: string
}

export interface FileUpload {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

export interface Address {
  street: string
  city: string
  state: string
  postal_code: string
  country: string
}

export interface ContactInfo {
  phone?: string
  email?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
}

export interface DateRange {
  start_date: string
  end_date: string
}

export interface TimeSlot {
  start_time: string
  end_time: string
}

export interface Statistics {
  total: number
  active: number
  inactive: number
  growth_rate?: number
  period_comparison?: {
    current: number
    previous: number
    percentage_change: number
  }
}

export type Status = 'active' | 'inactive' | 'pending' | 'suspended' | 'expired'

export type Priority = 'low' | 'medium' | 'high' | 'urgent'

export type NotificationType = 'info' | 'success' | 'warning' | 'error'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  timestamp: string
  read: boolean
  action_url?: string
}