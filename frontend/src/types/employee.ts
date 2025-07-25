import { PaginationParams, PaginatedResponse, Address, ContactInfo, Status } from './common'
import { User } from './auth'

export interface Employee extends User {
  employee_id: string
  department: string
  position: string
  hire_date: string
  employment_type: 'full_time' | 'part_time' | 'contract' | 'intern'
  salary?: number
  hourly_rate?: number
  currency: string
  manager_id?: number
  manager?: Employee
  address?: Address
  contact_info?: ContactInfo
  emergency_contact?: {
    name: string
    phone: string
    relationship: string
  }
  certifications: Certification[]
  skills: string[]
  schedule: WorkSchedule
  performance_rating?: number
  last_review_date?: string
  next_review_date?: string
  employment_status: 'active' | 'inactive' | 'on_leave' | 'terminated'
  termination_date?: string
  termination_reason?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface Certification {
  id: number
  name: string
  issuing_organization: string
  issue_date: string
  expiry_date?: string
  certificate_number?: string
  is_verified: boolean
  document_url?: string
}

export interface WorkSchedule {
  id: number
  employee_id: number
  schedule_type: 'fixed' | 'flexible' | 'rotating'
  weekly_hours: number
  shifts: WorkShift[]
  effective_from: string
  effective_to?: string
  is_active: boolean
}

export interface WorkShift {
  id: number
  day_of_week: number
  start_time: string
  end_time: string
  break_duration_minutes?: number
  is_working_day: boolean
}

export interface TimeEntry {
  id: number
  employee_id: number
  date: string
  clock_in_time?: string
  clock_out_time?: string
  break_start_time?: string
  break_end_time?: string
  total_hours: number
  overtime_hours: number
  status: 'present' | 'absent' | 'late' | 'early_leave' | 'holiday' | 'sick_leave'
  notes?: string
  approved_by?: number
  approved_at?: string
  created_at: string
  updated_at: string
}

export interface LeaveRequest {
  id: number
  employee_id: number
  employee: Employee
  leave_type: 'vacation' | 'sick' | 'personal' | 'maternity' | 'paternity' | 'bereavement' | 'other'
  start_date: string
  end_date: string
  days_requested: number
  reason: string
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  approved_by?: number
  approved_at?: string
  rejection_reason?: string
  created_at: string
  updated_at: string
}

export interface PerformanceReview {
  id: number
  employee_id: number
  employee: Employee
  reviewer_id: number
  reviewer: Employee
  review_period_start: string
  review_period_end: string
  overall_rating: number
  goals_achievement: number
  strengths: string[]
  areas_for_improvement: string[]
  goals_for_next_period: string[]
  comments: string
  employee_comments?: string
  status: 'draft' | 'submitted' | 'completed'
  created_at: string
  updated_at: string
}

export interface CreateEmployeeRequest {
  email: string
  first_name: string
  last_name: string
  password: string
  employee_id: string
  department: string
  position: string
  hire_date: string
  employment_type: 'full_time' | 'part_time' | 'contract' | 'intern'
  salary?: number
  hourly_rate?: number
  currency: string
  manager_id?: number
  phone?: string
  address?: Address
  emergency_contact?: {
    name: string
    phone: string
    relationship: string
  }
  certifications?: Omit<Certification, 'id'>[]
  skills?: string[]
  send_welcome_email?: boolean
}

export interface UpdateEmployeeRequest {
  first_name?: string
  last_name?: string
  employee_id?: string
  department?: string
  position?: string
  employment_type?: 'full_time' | 'part_time' | 'contract' | 'intern'
  salary?: number
  hourly_rate?: number
  manager_id?: number
  phone?: string
  address?: Address
  emergency_contact?: {
    name: string
    phone: string
    relationship: string
  }
  certifications?: Certification[]
  skills?: string[]
  performance_rating?: number
  employment_status?: 'active' | 'inactive' | 'on_leave' | 'terminated'
  termination_date?: string
  termination_reason?: string
  notes?: string
}

export interface EmployeeSearchParams extends PaginationParams {
  department?: string
  position?: string
  employment_type?: string
  manager_id?: number
  status?: Status
  hire_date_from?: string
  hire_date_to?: string
  salary_min?: number
  salary_max?: number
  skills?: string[]
  certification?: string
}

export interface EmployeeListResponse extends PaginatedResponse<Employee> {}

export interface EmployeeStatistics {
  total_employees: number
  active_employees: number
  employees_on_leave: number
  new_hires_this_month: number
  terminations_this_month: number
  employees_by_department: Array<{
    department: string
    count: number
  }>
  employees_by_employment_type: Array<{
    type: string
    count: number
  }>
  average_tenure_months: number
  turnover_rate: number
  upcoming_reviews: number
  expiring_certifications: number
  avg_performance: number
  total_payroll: number
}

export interface PayrollEntry {
  id: number
  employee_id: number
  employee: Employee
  pay_period_start: string
  pay_period_end: string
  regular_hours: number
  overtime_hours: number
  regular_pay: number
  overtime_pay: number
  bonuses: number
  deductions: number
  gross_pay: number
  tax_deductions: number
  net_pay: number
  status: 'draft' | 'processed' | 'paid'
  pay_date?: string
  created_at: string
  updated_at: string
}

export interface Department {
  id: number
  name: string
  description: string
  manager_id?: number
  manager?: Employee
  budget?: number
  employee_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Position {
  id: number
  title: string
  description: string
  department_id: number
  department: Department
  required_skills: string[]
  required_certifications: string[]
  salary_range_min?: number
  salary_range_max?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateLeaveRequestRequest {
  leave_type: 'vacation' | 'sick' | 'personal' | 'maternity' | 'paternity' | 'bereavement' | 'other'
  start_date: string
  end_date: string
  reason: string
}

export interface CreateTimeEntryRequest {
  employee_id: number
  date: string
  clock_in_time?: string
  clock_out_time?: string
  break_start_time?: string
  break_end_time?: string
  status: 'present' | 'absent' | 'late' | 'early_leave' | 'holiday' | 'sick_leave'
  notes?: string
}

export interface CreatePerformanceReviewRequest {
  employee_id: number
  review_period_start: string
  review_period_end: string
  overall_rating: number
  goals_achievement: number
  strengths: string[]
  areas_for_improvement: string[]
  goals_for_next_period: string[]
  comments: string
}

// Additional interfaces for employees service
export interface WorkScheduleSearchParams extends PaginationParams {
  employee_id?: number
  schedule_type?: string
  is_active?: boolean
}

export interface CreateWorkScheduleRequest {
  employee_id: number
  schedule_type: 'fixed' | 'flexible' | 'rotating'
  weekly_hours: number
  shifts: Omit<WorkShift, 'id'>[]
  effective_from: string
  effective_to?: string
}

export interface UpdateWorkScheduleRequest {
  schedule_type?: 'fixed' | 'flexible' | 'rotating'
  weekly_hours?: number
  shifts?: WorkShift[]
  effective_from?: string
  effective_to?: string
  is_active?: boolean
}

export interface ShiftSearchParams extends PaginationParams {
  day_of_week?: number
  start_time?: string
  end_time?: string
}

export interface CreateShiftRequest {
  day_of_week: number
  start_time: string
  end_time: string
  break_duration_minutes?: number
  is_working_day: boolean
}

export interface UpdateShiftRequest {
  day_of_week?: number
  start_time?: string
  end_time?: string
  break_duration_minutes?: number
  is_working_day?: boolean
}

export interface TimeEntrySearchParams extends PaginationParams {
  employee_id?: number
  date_from?: string
  date_to?: string
  status?: string
}

export interface LeaveSearchParams extends PaginationParams {
  employee_id?: number
  leave_type?: string
  status?: string
  start_date?: string
  end_date?: string
}

export interface CreateLeaveRequest {
  employee_id: number
  leave_type: 'vacation' | 'sick' | 'personal' | 'maternity' | 'paternity' | 'bereavement' | 'other'
  start_date: string
  end_date: string
  reason: string
  emergency_contact?: string
}

export interface ReviewSearchParams extends PaginationParams {
  employee_id?: number
  reviewer_id?: number
  status?: string
  review_period_start?: string
  review_period_end?: string
}

export interface CreateReviewRequest {
  employee_id: number
  review_period_start: string
  review_period_end: string
  goals?: any[]
  achievements?: any[]
  areas_for_improvement?: any[]
  overall_rating?: number
  reviewer_comments?: string
}

export interface CreateDepartmentRequest {
  name: string
  description: string
  manager_id?: number
  budget?: number
}

export interface UpdateDepartmentRequest {
  name?: string
  description?: string
  manager_id?: number
  budget?: number
  is_active?: boolean
}

export interface CreatePositionRequest {
  title: string
  description: string
  department_id: number
  required_skills?: string[]
  required_certifications?: string[]
  salary_range_min?: number
  salary_range_max?: number
}

export interface UpdatePositionRequest {
  title?: string
  description?: string
  department_id?: number
  required_skills?: string[]
  required_certifications?: string[]
  salary_range_min?: number
  salary_range_max?: number
  is_active?: boolean
}