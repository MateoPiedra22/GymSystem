import { apiClient } from '../client'
import { API_ENDPOINTS } from '../config'
import {
  Employee,
  Certification,
  WorkSchedule,
  WorkShift,
  TimeEntry,
  LeaveRequest,
  PerformanceReview,
  CreateEmployeeRequest,
  UpdateEmployeeRequest,
  EmployeeSearchParams,
  EmployeeListResponse,
  CreateWorkScheduleRequest,
  UpdateWorkScheduleRequest,
  WorkScheduleSearchParams,
  CreateShiftRequest,
  UpdateShiftRequest,
  ShiftSearchParams,
  CreateTimeEntryRequest,
  TimeEntrySearchParams,
  CreateLeaveRequest,
  LeaveSearchParams,
  CreateReviewRequest,
  ReviewSearchParams,
  EmployeeStatistics,
  PayrollEntry,
  Department,
  Position,
  PaginationParams
} from '../../types'

export class EmployeesService {
  // Employees
  static async getEmployees(params?: EmployeeSearchParams): Promise<EmployeeListResponse> {
    return apiClient.get(API_ENDPOINTS.EMPLOYEES.EMPLOYEES, { params })
  }

  static async getEmployee(id: number): Promise<Employee> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/${id}`)
  }

  static async createEmployee(data: CreateEmployeeRequest): Promise<Employee> {
    return apiClient.post(API_ENDPOINTS.EMPLOYEES.EMPLOYEES, data)
  }

  static async updateEmployee(id: number, data: UpdateEmployeeRequest): Promise<Employee> {
    return apiClient.put(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/${id}`, data)
  }

  static async deleteEmployee(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/${id}`)
  }

  static async toggleEmployeeStatus(id: number): Promise<Employee> {
    return apiClient.patch(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/${id}/toggle-status`)
  }

  static async terminateEmployee(id: number, data: {
    termination_date: string
    reason: string
    final_pay_amount?: number
    return_equipment?: boolean
    notes?: string
  }): Promise<Employee> {
    return apiClient.patch(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/${id}/terminate`, data)
  }

  static async rehireEmployee(id: number, data: {
    rehire_date: string
    position_id: number
    department_id: number
    salary: number
    notes?: string
  }): Promise<Employee> {
    return apiClient.patch(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/${id}/rehire`, data)
  }

  // Departments
  static async getDepartments(): Promise<Department[]> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/departments`)
  }

  static async createDepartment(data: {
    name: string
    description: string
    manager_id?: number
    budget?: number
    location?: string
  }): Promise<Department> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/departments`, data)
  }

  static async updateDepartment(id: number, data: {
    name?: string
    description?: string
    manager_id?: number
    budget?: number
    location?: string
    is_active?: boolean
  }): Promise<Department> {
    return apiClient.put(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/departments/${id}`, data)
  }

  static async deleteDepartment(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/departments/${id}`)
  }

  // Positions
  static async getPositions(): Promise<Position[]> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/positions`)
  }

  static async createPosition(data: {
    title: string
    description: string
    department_id: number
    min_salary: number
    max_salary: number
    required_qualifications?: string[]
    responsibilities?: string[]
  }): Promise<Position> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/positions`, data)
  }

  static async updatePosition(id: number, data: {
    title?: string
    description?: string
    department_id?: number
    min_salary?: number
    max_salary?: number
    required_qualifications?: string[]
    responsibilities?: string[]
    is_active?: boolean
  }): Promise<Position> {
    return apiClient.put(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/positions/${id}`, data)
  }

  static async deletePosition(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/positions/${id}`)
  }

  // Certifications
  static async getCertifications(employeeId?: number): Promise<Certification[]> {
    const endpoint = employeeId 
      ? `${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/${employeeId}/certifications`
      : `${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/certifications`
    return apiClient.get(endpoint)
  }

  static async createCertification(data: {
    employee_id: number
    name: string
    issuing_organization: string
    issue_date: string
    expiry_date?: string
    certification_number?: string
    description?: string
    certificate_file?: File
  }): Promise<Certification> {
    const formData = new FormData()
    
    Object.entries(data).forEach(([key, value]) => {
      if (key !== 'certificate_file' && value !== undefined) {
        formData.append(key, String(value))
      }
    })
    
    if (data.certificate_file) {
      formData.append('certificate_file', data.certificate_file)
    }
    
    const response = await apiClient.postRaw(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/certifications`, formData)
    return response.data.data
  }

  static async updateCertification(id: number, data: {
    name?: string
    issuing_organization?: string
    issue_date?: string
    expiry_date?: string
    certification_number?: string
    description?: string
    certificate_file?: File
    is_active?: boolean
  }): Promise<Certification> {
    const formData = new FormData()
    
    Object.entries(data).forEach(([key, value]) => {
      if (key !== 'certificate_file' && value !== undefined) {
        formData.append(key, String(value))
      }
    })
    
    if (data.certificate_file) {
      formData.append('certificate_file', data.certificate_file)
    }
    
    const response = await apiClient.postRaw(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/certifications/${id}`, formData)
    return response.data.data
  }

  static async deleteCertification(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/certifications/${id}`)
  }

  // Work Schedules
  static async getWorkSchedules(params?: WorkScheduleSearchParams): Promise<{ items: WorkSchedule[]; total: number }> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/schedules`, { params })
  }

  static async getWorkSchedule(id: number): Promise<WorkSchedule> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/schedules/${id}`)
  }

  static async createWorkSchedule(data: CreateWorkScheduleRequest): Promise<WorkSchedule> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/schedules`, data)
  }

  static async updateWorkSchedule(id: number, data: UpdateWorkScheduleRequest): Promise<WorkSchedule> {
    return apiClient.put(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/schedules/${id}`, data)
  }

  static async deleteWorkSchedule(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/schedules/${id}`)
  }

  // Work Shifts
  static async getWorkShifts(params?: ShiftSearchParams): Promise<{ items: WorkShift[]; total: number }> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/shifts`, { params })
  }

  static async getWorkShift(id: number): Promise<WorkShift> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/shifts/${id}`)
  }

  static async createWorkShift(data: CreateShiftRequest): Promise<WorkShift> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/shifts`, data)
  }

  static async updateWorkShift(id: number, data: UpdateShiftRequest): Promise<WorkShift> {
    return apiClient.put(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/shifts/${id}`, data)
  }

  static async deleteWorkShift(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/shifts/${id}`)
  }

  static async assignShift(data: {
    employee_id: number
    shift_id: number
    date: string
    notes?: string
  }): Promise<{ id: number; employee_id: number; shift_id: number; date: string }> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/shifts/assign`, data)
  }

  static async unassignShift(assignmentId: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/shifts/assignments/${assignmentId}`)
  }

  // Time Entries
  static async getTimeEntries(params?: TimeEntrySearchParams): Promise<{ items: TimeEntry[]; total: number }> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/time-entries`, { params })
  }

  static async getTimeEntry(id: number): Promise<TimeEntry> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/time-entries/${id}`)
  }

  static async createTimeEntry(data: CreateTimeEntryRequest): Promise<TimeEntry> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/time-entries`, data)
  }

  static async updateTimeEntry(id: number, data: {
    clock_in?: string
    clock_out?: string
    break_duration?: number
    notes?: string
    status?: 'pending' | 'approved' | 'rejected'
  }): Promise<TimeEntry> {
    return apiClient.put(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/time-entries/${id}`, data)
  }

  static async deleteTimeEntry(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/time-entries/${id}`)
  }

  static async clockIn(employeeId: number, data?: {
    location?: string
    notes?: string
  }): Promise<TimeEntry> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/${employeeId}/clock-in`, data)
  }

  static async clockOut(employeeId: number, data?: {
    location?: string
    notes?: string
  }): Promise<TimeEntry> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/${employeeId}/clock-out`, data)
  }

  // Leave Requests
  static async getLeaveRequests(params?: LeaveSearchParams): Promise<{ items: LeaveRequest[]; total: number }> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/leave-requests`, { params })
  }

  static async getLeaveRequest(id: number): Promise<LeaveRequest> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/leave-requests/${id}`)
  }

  static async createLeaveRequest(data: CreateLeaveRequest): Promise<LeaveRequest> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/leave-requests`, data)
  }

  static async updateLeaveRequest(id: number, data: {
    start_date?: string
    end_date?: string
    leave_type?: string
    reason?: string
    emergency_contact?: string
  }): Promise<LeaveRequest> {
    return apiClient.put(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/leave-requests/${id}`, data)
  }

  static async deleteLeaveRequest(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/leave-requests/${id}`)
  }

  static async approveLeaveRequest(id: number, data?: {
    approved_by_notes?: string
  }): Promise<LeaveRequest> {
    return apiClient.patch(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/leave-requests/${id}/approve`, data)
  }

  static async rejectLeaveRequest(id: number, data: {
    rejection_reason: string
  }): Promise<LeaveRequest> {
    return apiClient.patch(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/leave-requests/${id}/reject`, data)
  }

  // Performance Reviews
  static async getPerformanceReviews(params?: ReviewSearchParams): Promise<{ items: PerformanceReview[]; total: number }> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/performance-reviews`, { params })
  }

  static async getPerformanceReview(id: number): Promise<PerformanceReview> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/performance-reviews/${id}`)
  }

  static async createPerformanceReview(data: CreateReviewRequest): Promise<PerformanceReview> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/performance-reviews`, data)
  }

  static async updatePerformanceReview(id: number, data: {
    review_period_start?: string
    review_period_end?: string
    goals?: any[]
    achievements?: any[]
    areas_for_improvement?: any[]
    overall_rating?: number
    reviewer_comments?: string
    employee_comments?: string
    status?: 'draft' | 'in_progress' | 'completed' | 'acknowledged'
  }): Promise<PerformanceReview> {
    return apiClient.put(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/performance-reviews/${id}`, data)
  }

  static async deletePerformanceReview(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/performance-reviews/${id}`)
  }

  static async submitPerformanceReview(id: number): Promise<PerformanceReview> {
    return apiClient.patch(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/performance-reviews/${id}/submit`)
  }

  static async acknowledgePerformanceReview(id: number, data?: {
    employee_signature?: string
    acknowledgment_date?: string
    employee_comments?: string
  }): Promise<PerformanceReview> {
    return apiClient.patch(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/performance-reviews/${id}/acknowledge`, data)
  }

  // Payroll
  static async getPayrollEntries(params?: {
    employee_id?: number
    pay_period_start?: string
    pay_period_end?: string
    status?: string
  } & PaginationParams): Promise<{ items: PayrollEntry[]; total: number }> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/payroll`, { params })
  }

  static async generatePayroll(data: {
    pay_period_start: string
    pay_period_end: string
    employee_ids?: number[]
    include_overtime?: boolean
    include_bonuses?: boolean
  }): Promise<{
    generated: number
    total_amount: number
    entries: PayrollEntry[]
  }> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/payroll/generate`, data)
  }

  static async processPayroll(payrollIds: number[]): Promise<{
    processed: number
    failed: number
    total_amount: number
  }> {
    return apiClient.post(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/payroll/process`, { payroll_ids: payrollIds })
  }

  // Employee Statistics
  static async getEmployeeStatistics(): Promise<EmployeeStatistics> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/statistics`)
  }

  static async getEmployeePerformanceStats(employeeId: number): Promise<{
    attendance_rate: number
    punctuality_rate: number
    overtime_hours: number
    leave_days_taken: number
    performance_ratings: Array<{
      review_date: string
      overall_rating: number
    }>
    certifications_count: number
    training_hours: number
  }> {
    return apiClient.get(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/${employeeId}/performance-stats`)
  }

  // Bulk Operations
  static async bulkImportEmployees(file: File): Promise<{
    successful: number
    failed: number
    errors: Array<{ row: number; error: string }>
  }> {
    return apiClient.uploadFile(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/bulk-import`, file)
  }

  static async exportEmployees(params?: EmployeeSearchParams): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/export`, { params })
  }

  static async exportTimeEntries(params?: {
    employee_id?: number
    date_from?: string
    date_to?: string
    status?: string
  }): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/time-entries/export`, { params })
  }

  static async exportPayroll(params?: {
    pay_period_start?: string
    pay_period_end?: string
    employee_id?: number
  }): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.EMPLOYEES.EMPLOYEES}/payroll/export`, { params })
  }
}

export const employeesService = EmployeesService