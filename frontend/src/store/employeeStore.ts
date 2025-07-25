import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { employeesService } from '../api/services/employees'
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
  EmployeeStatistics,
  Department,
  Position,

} from '../types'

interface EmployeeState {
  // State
  employees: Employee[]
  departments: Department[]
  positions: Position[]
  certifications: Certification[]
  workSchedules: WorkSchedule[]
  timeEntries: TimeEntry[]
  leaveRequests: LeaveRequest[]
  performanceReviews: PerformanceReview[]
  currentEmployee: Employee | null
  currentDepartment: Department | null
  currentPosition: Position | null
  currentSchedule: WorkSchedule | null
  currentLeaveRequest: LeaveRequest | null
  currentReview: PerformanceReview | null
  employeeStats: EmployeeStatistics | null
  loading: boolean
  error: string | null
  
  // Pagination
  employeePagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  leaveRequestPagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  reviewPagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  
  // Filters
  employeeFilters: EmployeeSearchParams
  
  // Actions - Employees
  getEmployees: (params?: EmployeeSearchParams) => Promise<void>
  getEmployee: (id: number) => Promise<void>
  createEmployee: (data: CreateEmployeeRequest) => Promise<Employee | null>
  updateEmployee: (id: number, data: UpdateEmployeeRequest) => Promise<Employee | null>
  deleteEmployee: (id: number) => Promise<boolean>
  toggleEmployeeStatus: (id: number) => Promise<boolean>
  terminateEmployee: (id: number, data: {
    termination_date: string
    reason: string
    final_pay_amount?: number
    return_equipment?: boolean
    notes?: string
  }) => Promise<boolean>
  rehireEmployee: (id: number, data: {
    rehire_date: string
    position_id: number
    department_id: number
    salary: number
    notes?: string
  }) => Promise<boolean>
  
  // Actions - Departments
  getDepartments: () => Promise<void>
  createDepartment: (data: {
    name: string
    description: string
    manager_id?: number
    budget?: number
    location?: string
  }) => Promise<Department | null>
  updateDepartment: (id: number, data: {
    name?: string
    description?: string
    manager_id?: number
    budget?: number
    location?: string
    is_active?: boolean
  }) => Promise<Department | null>
  deleteDepartment: (id: number) => Promise<boolean>
  
  // Actions - Positions
  getPositions: () => Promise<void>
  createPosition: (data: {
    title: string
    description: string
    department_id: number
    min_salary: number
    max_salary: number
    required_qualifications?: string[]
    responsibilities?: string[]
  }) => Promise<Position | null>
  updatePosition: (id: number, data: {
    title?: string
    description?: string
    department_id?: number
    min_salary?: number
    max_salary?: number
    required_qualifications?: string[]
    responsibilities?: string[]
    is_active?: boolean
  }) => Promise<Position | null>
  deletePosition: (id: number) => Promise<boolean>
  
  // Actions - Certifications
  getCertifications: (employeeId?: number) => Promise<void>
  createCertification: (data: {
    employee_id: number
    name: string
    issuing_organization: string
    issue_date: string
    expiry_date?: string
    certificate_number?: string
    document?: File
  }) => Promise<Certification | null>
  updateCertification: (id: number, data: {
    name?: string
    issuing_organization?: string
    issue_date?: string
    expiry_date?: string
    certificate_number?: string
    is_verified?: boolean
    document?: File
  }) => Promise<Certification | null>
  deleteCertification: (id: number) => Promise<boolean>
  
  // Actions - Work Schedules
  getWorkSchedules: (employeeId?: number) => Promise<void>
  createWorkSchedule: (data: {
    employee_id: number
    schedule_type: 'fixed' | 'flexible' | 'rotating'
    weekly_hours: number
    shifts: Omit<WorkShift, 'id'>[]
    effective_from: string
    effective_to?: string
  }) => Promise<WorkSchedule | null>
  updateWorkSchedule: (id: number, data: {
    schedule_type?: 'fixed' | 'flexible' | 'rotating'
    weekly_hours?: number
    shifts?: WorkShift[]
    effective_from?: string
    effective_to?: string
    is_active?: boolean
  }) => Promise<WorkSchedule | null>
  deleteWorkSchedule: (id: number) => Promise<boolean>
  
  // Actions - Time Entries
  getTimeEntries: (params?: {
    employee_id?: number
    date_from?: string
    date_to?: string
    status?: string
  }) => Promise<void>
  createTimeEntry: (data: {
    employee_id: number
    date: string
    clock_in_time?: string
    clock_out_time?: string
    break_start_time?: string
    break_end_time?: string
    status: string
    notes?: string
  }) => Promise<TimeEntry | null>
  updateTimeEntry: (id: number, data: {
    clock_in_time?: string
    clock_out_time?: string
    break_start_time?: string
    break_end_time?: string
    status?: string
    notes?: string
  }) => Promise<TimeEntry | null>
  deleteTimeEntry: (id: number) => Promise<boolean>
  approveTimeEntry: (id: number) => Promise<boolean>
  
  // Actions - Leave Requests
  getLeaveRequests: (params?: {
    employee_id?: number
    status?: string
    leave_type?: string
    start_date_from?: string
    start_date_to?: string
  }) => Promise<void>
  createLeaveRequest: (data: {
    employee_id: number
    leave_type: string
    start_date: string
    end_date: string
    reason: string
  }) => Promise<LeaveRequest | null>
  updateLeaveRequest: (id: number, data: {
    leave_type?: string
    start_date?: string
    end_date?: string
    reason?: string
  }) => Promise<LeaveRequest | null>
  approveLeaveRequest: (id: number) => Promise<boolean>
  rejectLeaveRequest: (id: number, reason: string) => Promise<boolean>
  cancelLeaveRequest: (id: number) => Promise<boolean>
  
  // Actions - Performance Reviews
  getPerformanceReviews: (params?: {
    employee_id?: number
    reviewer_id?: number
    status?: string
    review_period_start?: string
    review_period_end?: string
  }) => Promise<void>
  createPerformanceReview: (data: {
    employee_id: number
    review_period_start: string
    review_period_end: string
    overall_rating: number
    goals_achievement: number
    strengths: string[]
    areas_for_improvement: string[]
    goals_for_next_period: string[]
    comments: string
  }) => Promise<PerformanceReview | null>
  updatePerformanceReview: (id: number, data: {
    overall_rating?: number
    goals_achievement?: number
    strengths?: string[]
    areas_for_improvement?: string[]
    goals_for_next_period?: string[]
    comments?: string
    employee_comments?: string
    status?: string
  }) => Promise<PerformanceReview | null>
  deletePerformanceReview: (id: number) => Promise<boolean>
  
  // Actions - Statistics
  getEmployeeStatistics: () => Promise<void>
  
  // Actions - Bulk Operations
  bulkUpdateEmployees: (data: {
    employee_ids: number[]
    updates: Partial<UpdateEmployeeRequest>
  }) => Promise<boolean>
  bulkDeleteEmployees: (employeeIds: number[]) => Promise<boolean>
  
  // Actions - Export/Import
  exportEmployees: (params?: EmployeeSearchParams) => Promise<boolean>
  importEmployees: (file: File) => Promise<any>
  
  // Utility actions
  setEmployeeFilters: (filters: Partial<EmployeeSearchParams>) => void
  clearFilters: () => void
  setCurrentEmployee: (employee: Employee | null) => void
  setCurrentDepartment: (department: Department | null) => void
  setCurrentPosition: (position: Position | null) => void
  setCurrentSchedule: (schedule: WorkSchedule | null) => void
  setCurrentLeaveRequest: (leaveRequest: LeaveRequest | null) => void
  setCurrentReview: (review: PerformanceReview | null) => void
  clearError: () => void
  setLoading: (loading: boolean) => void
}

const initialEmployeeFilters: EmployeeSearchParams = {
  page: 1,
  limit: 10
}

export const useEmployeeStore = create<EmployeeState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        employees: [],
        departments: [],
        positions: [],
        certifications: [],
        workSchedules: [],
        timeEntries: [],
        leaveRequests: [],
        performanceReviews: [],
        currentEmployee: null,
        currentDepartment: null,
        currentPosition: null,
        currentSchedule: null,
        currentLeaveRequest: null,
        currentReview: null,
        employeeStats: null,
        loading: false,
        error: null,
        
        employeePagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        leaveRequestPagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        reviewPagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        
        employeeFilters: initialEmployeeFilters,

        // Actions - Employees
        getEmployees: async (params?: EmployeeSearchParams) => {
          set({ loading: true, error: null })
          try {
            const response = await employeesService.getEmployees(params)
            set({
              employees: response.items,
              employeePagination: {
                page: response.page,
                limit: response.limit,
                total: response.total,
                totalPages: response.pages
              },
              loading: false
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar empleados',
              loading: false 
            })
          }
        },

        getEmployee: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const employee = await employeesService.getEmployee(id)
            set({ currentEmployee: employee, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar empleado',
              loading: false 
            })
          }
        },

        createEmployee: async (data: CreateEmployeeRequest) => {
          set({ loading: true, error: null })
          try {
            const newEmployee = await employeesService.createEmployee(data)
            const { employees } = get()
            set({ 
              employees: [newEmployee, ...employees],
              loading: false 
            })
            return newEmployee
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear empleado',
              loading: false 
            })
            return null
          }
        },

        updateEmployee: async (id: number, data: UpdateEmployeeRequest) => {
          set({ loading: true, error: null })
          try {
            const updatedEmployee = await employeesService.updateEmployee(id, data)
            const { employees, currentEmployee } = get()
            set({ 
              employees: employees.map(e => e.id === id ? updatedEmployee : e),
              currentEmployee: currentEmployee?.id === id ? updatedEmployee : currentEmployee,
              loading: false 
            })
            return updatedEmployee
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar empleado',
              loading: false 
            })
            return null
          }
        },

        deleteEmployee: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await employeesService.deleteEmployee(id)
            const { employees } = get()
            set({ 
              employees: employees.filter(e => e.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar empleado',
              loading: false 
            })
            return false
          }
        },

        toggleEmployeeStatus: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const updatedEmployee = await employeesService.toggleEmployeeStatus(id)
            const { employees, currentEmployee } = get()
            set({ 
              employees: employees.map(e => e.id === id ? updatedEmployee : e),
              currentEmployee: currentEmployee?.id === id ? updatedEmployee : currentEmployee,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cambiar estado del empleado',
              loading: false 
            })
            return false
          }
        },

        terminateEmployee: async (id: number, data: {
          termination_date: string
          reason: string
          final_pay_amount?: number
          return_equipment?: boolean
          notes?: string
        }) => {
          set({ loading: true, error: null })
          try {
            const terminatedEmployee = await employeesService.terminateEmployee(id, data)
            const { employees, currentEmployee } = get()
            set({ 
              employees: employees.map(e => e.id === id ? terminatedEmployee : e),
              currentEmployee: currentEmployee?.id === id ? terminatedEmployee : currentEmployee,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al terminar empleado',
              loading: false 
            })
            return false
          }
        },

        rehireEmployee: async (id: number, data: {
          rehire_date: string
          position_id: number
          department_id: number
          salary: number
          notes?: string
        }) => {
          set({ loading: true, error: null })
          try {
            const rehiredEmployee = await employeesService.rehireEmployee(id, data)
            const { employees, currentEmployee } = get()
            set({ 
              employees: employees.map(e => e.id === id ? rehiredEmployee : e),
              currentEmployee: currentEmployee?.id === id ? rehiredEmployee : currentEmployee,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al reincorporar empleado',
              loading: false 
            })
            return false
          }
        },

        // Actions - Departments
        getDepartments: async () => {
          set({ loading: true, error: null })
          try {
            const departments = await employeesService.getDepartments()
            set({ departments, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar departamentos',
              loading: false 
            })
          }
        },

        createDepartment: async (data: {
          name: string
          description: string
          manager_id?: number
          budget?: number
          location?: string
        }) => {
          set({ loading: true, error: null })
          try {
            const newDepartment = await employeesService.createDepartment(data)
            const { departments } = get()
            set({ 
              departments: [newDepartment, ...departments],
              loading: false 
            })
            return newDepartment
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear departamento',
              loading: false 
            })
            return null
          }
        },

        updateDepartment: async (id: number, data: {
          name?: string
          description?: string
          manager_id?: number
          budget?: number
          location?: string
          is_active?: boolean
        }) => {
          set({ loading: true, error: null })
          try {
            const updatedDepartment = await employeesService.updateDepartment(id, data)
            const { departments, currentDepartment } = get()
            set({ 
              departments: departments.map(d => d.id === id ? updatedDepartment : d),
              currentDepartment: currentDepartment?.id === id ? updatedDepartment : currentDepartment,
              loading: false 
            })
            return updatedDepartment
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar departamento',
              loading: false 
            })
            return null
          }
        },

        deleteDepartment: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await employeesService.deleteDepartment(id)
            const { departments } = get()
            set({ 
              departments: departments.filter(d => d.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar departamento',
              loading: false 
            })
            return false
          }
        },

        // Actions - Positions
        getPositions: async () => {
          set({ loading: true, error: null })
          try {
            const positions = await employeesService.getPositions()
            set({ positions, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar posiciones',
              loading: false 
            })
          }
        },

        createPosition: async (data: {
          title: string
          description: string
          department_id: number
          min_salary: number
          max_salary: number
          required_qualifications?: string[]
          responsibilities?: string[]
        }) => {
          set({ loading: true, error: null })
          try {
            const newPosition = await employeesService.createPosition(data)
            const { positions } = get()
            set({ 
              positions: [newPosition, ...positions],
              loading: false 
            })
            return newPosition
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear posición',
              loading: false 
            })
            return null
          }
        },

        updatePosition: async (id: number, data: {
          title?: string
          description?: string
          department_id?: number
          min_salary?: number
          max_salary?: number
          required_qualifications?: string[]
          responsibilities?: string[]
          is_active?: boolean
        }) => {
          set({ loading: true, error: null })
          try {
            const updatedPosition = await employeesService.updatePosition(id, data)
            const { positions, currentPosition } = get()
            set({ 
              positions: positions.map(p => p.id === id ? updatedPosition : p),
              currentPosition: currentPosition?.id === id ? updatedPosition : currentPosition,
              loading: false 
            })
            return updatedPosition
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar posición',
              loading: false 
            })
            return null
          }
        },

        deletePosition: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await employeesService.deletePosition(id)
            const { positions } = get()
            set({ 
              positions: positions.filter(p => p.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar posición',
              loading: false 
            })
            return false
          }
        },

        // Actions - Certifications
        getCertifications: async (employeeId?: number) => {
          set({ loading: true, error: null })
          try {
            const certifications = await employeesService.getCertifications(employeeId)
            set({ certifications, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar certificaciones',
              loading: false 
            })
          }
        },

        createCertification: async (data: {
          employee_id: number
          name: string
          issuing_organization: string
          issue_date: string
          expiry_date?: string
          certificate_number?: string
          document?: File
        }) => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            // const newCertification = await EmployeesService.createCertification(data)
            // For now, we'll simulate the response
            const newCertification: Certification = {
              id: Date.now(),
              name: data.name,
              issuing_organization: data.issuing_organization,
              issue_date: data.issue_date,
              expiry_date: data.expiry_date,
              certificate_number: data.certificate_number,
              is_verified: false
            }
            const { certifications } = get()
            set({ 
              certifications: [newCertification, ...certifications],
              loading: false 
            })
            return newCertification
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear certificación',
              loading: false 
            })
            return null
          }
        },

        updateCertification: async (id: number, data: {
          name?: string
          issuing_organization?: string
          issue_date?: string
          expiry_date?: string
          certificate_number?: string
          is_verified?: boolean
          document?: File
        }) => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            const { certifications } = get()
            const updatedCertification = certifications.find(c => c.id === id)
            if (updatedCertification) {
              Object.assign(updatedCertification, data)
              set({ 
                certifications: certifications.map(c => c.id === id ? updatedCertification : c),
                loading: false 
              })
              return updatedCertification
            }
            throw new Error('Certificación no encontrada')
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar certificación',
              loading: false 
            })
            return null
          }
        },

        deleteCertification: async (id: number) => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            const { certifications } = get()
            set({ 
              certifications: certifications.filter(c => c.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar certificación',
              loading: false 
            })
            return false
          }
        },

        // Actions - Work Schedules
        getWorkSchedules: async (_employeeId?: number) => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            set({ workSchedules: [], loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar horarios',
              loading: false 
            })
          }
        },

        createWorkSchedule: async (data: {
          employee_id: number
          schedule_type: 'fixed' | 'flexible' | 'rotating'
          weekly_hours: number
          shifts: Omit<WorkShift, 'id'>[]
          effective_from: string
          effective_to?: string
        }) => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            const newSchedule: WorkSchedule = {
              id: Date.now(),
              employee_id: data.employee_id,
              schedule_type: data.schedule_type,
              weekly_hours: data.weekly_hours,
              shifts: data.shifts.map((shift, index) => ({ ...shift, id: index + 1 })),
              effective_from: data.effective_from,
              effective_to: data.effective_to,
              is_active: true
            }
            const { workSchedules } = get()
            set({ 
              workSchedules: [newSchedule, ...workSchedules],
              loading: false 
            })
            return newSchedule
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear horario',
              loading: false 
            })
            return null
          }
        },

        updateWorkSchedule: async (id: number, data: {
          schedule_type?: 'fixed' | 'flexible' | 'rotating'
          weekly_hours?: number
          shifts?: WorkShift[]
          effective_from?: string
          effective_to?: string
          is_active?: boolean
        }) => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            const { workSchedules, currentSchedule } = get()
            const updatedSchedule = workSchedules.find(s => s.id === id)
            if (updatedSchedule) {
              Object.assign(updatedSchedule, data)
              set({ 
                workSchedules: workSchedules.map(s => s.id === id ? updatedSchedule : s),
                currentSchedule: currentSchedule?.id === id ? updatedSchedule : currentSchedule,
                loading: false 
              })
              return updatedSchedule
            }
            throw new Error('Horario no encontrado')
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar horario',
              loading: false 
            })
            return null
          }
        },

        deleteWorkSchedule: async (id: number) => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            const { workSchedules } = get()
            set({ 
              workSchedules: workSchedules.filter(s => s.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar horario',
              loading: false 
            })
            return false
          }
        },

        // Actions - Time Entries (simplified implementations)
        getTimeEntries: async (_params?: {
          employee_id?: number
          date_from?: string
          date_to?: string
          status?: string
        }) => {
          set({ loading: true, error: null })
          try {
            set({ timeEntries: [], loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar registros de tiempo',
              loading: false 
            })
          }
        },

        createTimeEntry: async (data: {
          employee_id: number
          date: string
          clock_in_time?: string
          clock_out_time?: string
          break_start_time?: string
          break_end_time?: string
          status: string
          notes?: string
        }) => {
          set({ loading: true, error: null })
          try {
            const newTimeEntry: TimeEntry = {
              id: Date.now(),
              employee_id: data.employee_id,
              date: data.date,
              clock_in_time: data.clock_in_time,
              clock_out_time: data.clock_out_time,
              break_start_time: data.break_start_time,
              break_end_time: data.break_end_time,
              total_hours: 8,
              overtime_hours: 0,
              status: data.status as any,
              notes: data.notes,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
            const { timeEntries } = get()
            set({ 
              timeEntries: [newTimeEntry, ...timeEntries],
              loading: false 
            })
            return newTimeEntry
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear registro de tiempo',
              loading: false 
            })
            return null
          }
        },

        updateTimeEntry: async (id: number, data: {
          clock_in_time?: string
          clock_out_time?: string
          break_start_time?: string
          break_end_time?: string
          status?: string
          notes?: string
        }) => {
          set({ loading: true, error: null })
          try {
            const { timeEntries } = get()
            const updatedTimeEntry = timeEntries.find(t => t.id === id)
            if (updatedTimeEntry) {
              Object.assign(updatedTimeEntry, data)
              set({ 
                timeEntries: timeEntries.map(t => t.id === id ? updatedTimeEntry : t),
                loading: false 
              })
              return updatedTimeEntry
            }
            throw new Error('Registro de tiempo no encontrado')
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar registro de tiempo',
              loading: false 
            })
            return null
          }
        },

        deleteTimeEntry: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const { timeEntries } = get()
            set({ 
              timeEntries: timeEntries.filter(t => t.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar registro de tiempo',
              loading: false 
            })
            return false
          }
        },

        approveTimeEntry: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const { timeEntries } = get()
            const timeEntry = timeEntries.find(t => t.id === id)
            if (timeEntry) {
              timeEntry.approved_at = new Date().toISOString()
              set({ 
                timeEntries: timeEntries.map(t => t.id === id ? timeEntry : t),
                loading: false 
              })
            }
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al aprobar registro de tiempo',
              loading: false 
            })
            return false
          }
        },

        // Actions - Leave Requests (simplified implementations)
        getLeaveRequests: async (_params?: {
          employee_id?: number
          status?: string
          leave_type?: string
          start_date_from?: string
          start_date_to?: string
        }) => {
          set({ loading: true, error: null })
          try {
            set({ leaveRequests: [], loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar solicitudes de permiso',
              loading: false 
            })
          }
        },

        createLeaveRequest: async (data: {
          employee_id: number
          leave_type: string
          start_date: string
          end_date: string
          reason: string
        }) => {
          set({ loading: true, error: null })
          try {
            const newLeaveRequest: LeaveRequest = {
              id: Date.now(),
              employee_id: data.employee_id,
              employee: {} as Employee,
              leave_type: data.leave_type as any,
              start_date: data.start_date,
              end_date: data.end_date,
              days_requested: 1,
              reason: data.reason,
              status: 'pending',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
            const { leaveRequests } = get()
            set({ 
              leaveRequests: [newLeaveRequest, ...leaveRequests],
              loading: false 
            })
            return newLeaveRequest
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear solicitud de permiso',
              loading: false 
            })
            return null
          }
        },

        updateLeaveRequest: async (id: number, data: {
          leave_type?: string
          start_date?: string
          end_date?: string
          reason?: string
        }) => {
          set({ loading: true, error: null })
          try {
            const { leaveRequests, currentLeaveRequest } = get()
            const updatedLeaveRequest = leaveRequests.find(l => l.id === id)
            if (updatedLeaveRequest) {
              Object.assign(updatedLeaveRequest, data)
              set({ 
                leaveRequests: leaveRequests.map(l => l.id === id ? updatedLeaveRequest : l),
                currentLeaveRequest: currentLeaveRequest?.id === id ? updatedLeaveRequest : currentLeaveRequest,
                loading: false 
              })
              return updatedLeaveRequest
            }
            throw new Error('Solicitud de permiso no encontrada')
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar solicitud de permiso',
              loading: false 
            })
            return null
          }
        },

        approveLeaveRequest: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const { leaveRequests, currentLeaveRequest } = get()
            const leaveRequest = leaveRequests.find(l => l.id === id)
            if (leaveRequest) {
              leaveRequest.status = 'approved'
              leaveRequest.approved_at = new Date().toISOString()
              set({ 
                leaveRequests: leaveRequests.map(l => l.id === id ? leaveRequest : l),
                currentLeaveRequest: currentLeaveRequest?.id === id ? leaveRequest : currentLeaveRequest,
                loading: false 
              })
            }
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al aprobar solicitud de permiso',
              loading: false 
            })
            return false
          }
        },

        rejectLeaveRequest: async (id: number, reason: string) => {
          set({ loading: true, error: null })
          try {
            const { leaveRequests, currentLeaveRequest } = get()
            const leaveRequest = leaveRequests.find(l => l.id === id)
            if (leaveRequest) {
              leaveRequest.status = 'rejected'
              leaveRequest.rejection_reason = reason
              set({ 
                leaveRequests: leaveRequests.map(l => l.id === id ? leaveRequest : l),
                currentLeaveRequest: currentLeaveRequest?.id === id ? leaveRequest : currentLeaveRequest,
                loading: false 
              })
            }
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al rechazar solicitud de permiso',
              loading: false 
            })
            return false
          }
        },

        cancelLeaveRequest: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const { leaveRequests, currentLeaveRequest } = get()
            const leaveRequest = leaveRequests.find(l => l.id === id)
            if (leaveRequest) {
              leaveRequest.status = 'cancelled'
              set({ 
                leaveRequests: leaveRequests.map(l => l.id === id ? leaveRequest : l),
                currentLeaveRequest: currentLeaveRequest?.id === id ? leaveRequest : currentLeaveRequest,
                loading: false 
              })
            }
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cancelar solicitud de permiso',
              loading: false 
            })
            return false
          }
        },

        // Actions - Performance Reviews (simplified implementations)
        getPerformanceReviews: async (_params?: {
          employee_id?: number
          reviewer_id?: number
          status?: string
          review_period_start?: string
          review_period_end?: string
        }) => {
          set({ loading: true, error: null })
          try {
            set({ performanceReviews: [], loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar evaluaciones de desempeño',
              loading: false 
            })
          }
        },

        createPerformanceReview: async (data: {
          employee_id: number
          review_period_start: string
          review_period_end: string
          overall_rating: number
          goals_achievement: number
          strengths: string[]
          areas_for_improvement: string[]
          goals_for_next_period: string[]
          comments: string
        }) => {
          set({ loading: true, error: null })
          try {
            const newReview: PerformanceReview = {
              id: Date.now(),
              employee_id: data.employee_id,
              employee: {} as Employee,
              reviewer_id: 1, // Current user
              reviewer: {} as Employee,
              review_period_start: data.review_period_start,
              review_period_end: data.review_period_end,
              overall_rating: data.overall_rating,
              goals_achievement: data.goals_achievement,
              strengths: data.strengths,
              areas_for_improvement: data.areas_for_improvement,
              goals_for_next_period: data.goals_for_next_period,
              comments: data.comments,
              status: 'draft',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
            const { performanceReviews } = get()
            set({ 
              performanceReviews: [newReview, ...performanceReviews],
              loading: false 
            })
            return newReview
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear evaluación de desempeño',
              loading: false 
            })
            return null
          }
        },

        updatePerformanceReview: async (id: number, data: {
          overall_rating?: number
          goals_achievement?: number
          strengths?: string[]
          areas_for_improvement?: string[]
          goals_for_next_period?: string[]
          comments?: string
          employee_comments?: string
          status?: string
        }) => {
          set({ loading: true, error: null })
          try {
            const { performanceReviews, currentReview } = get()
            const updatedReview = performanceReviews.find(r => r.id === id)
            if (updatedReview) {
              Object.assign(updatedReview, data)
              set({ 
                performanceReviews: performanceReviews.map(r => r.id === id ? updatedReview : r),
                currentReview: currentReview?.id === id ? updatedReview : currentReview,
                loading: false 
              })
              return updatedReview
            }
            throw new Error('Evaluación de desempeño no encontrada')
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar evaluación de desempeño',
              loading: false 
            })
            return null
          }
        },

        deletePerformanceReview: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const { performanceReviews } = get()
            set({ 
              performanceReviews: performanceReviews.filter(r => r.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar evaluación de desempeño',
              loading: false 
            })
            return false
          }
        },

        // Actions - Statistics
        getEmployeeStatistics: async () => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            const employeeStats: EmployeeStatistics = {
              total_employees: 0,
              active_employees: 0,
              employees_on_leave: 0,
              new_hires_this_month: 0,
              terminations_this_month: 0,
              employees_by_department: [],
              employees_by_employment_type: [],
              average_tenure_months: 0,
              turnover_rate: 0,
              upcoming_reviews: 0,
              expiring_certifications: 0,
              avg_performance: 0,
              total_payroll: 0
            }
            set({ employeeStats, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar estadísticas de empleados',
              loading: false 
            })
          }
        },

        // Actions - Bulk Operations
        bulkUpdateEmployees: async (data: {
          employee_ids: number[]
          updates: Partial<UpdateEmployeeRequest>
        }) => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            const { employees } = get()
            const updatedEmployees = employees.map(e => 
              data.employee_ids.includes(e.id) ? { ...e, ...data.updates } : e
            )
            set({ employees: updatedEmployees, loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar empleados en lote',
              loading: false 
            })
            return false
          }
        },

        bulkDeleteEmployees: async (employeeIds: number[]) => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            const { employees } = get()
            set({ 
              employees: employees.filter(e => !employeeIds.includes(e.id)),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar empleados en lote',
              loading: false 
            })
            return false
          }
        },

        // Actions - Export/Import
        exportEmployees: async (_params?: EmployeeSearchParams) => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            set({ loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al exportar empleados',
              loading: false 
            })
            return false
          }
        },

        importEmployees: async (_file: File) => {
          set({ loading: true, error: null })
          try {
            // Note: This would need to be implemented in the service
            set({ loading: false })
            return { success: true, imported: 0, errors: [] }
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al importar empleados',
              loading: false 
            })
            return null
          }
        },

        // Utility actions
        setEmployeeFilters: (filters: Partial<EmployeeSearchParams>) => {
          set(state => ({ 
            employeeFilters: { ...state.employeeFilters, ...filters } 
          }))
        },

        clearFilters: () => {
          set({ employeeFilters: initialEmployeeFilters })
        },

        setCurrentEmployee: (employee: Employee | null) => {
          set({ currentEmployee: employee })
        },

        setCurrentDepartment: (department: Department | null) => {
          set({ currentDepartment: department })
        },

        setCurrentPosition: (position: Position | null) => {
          set({ currentPosition: position })
        },

        setCurrentSchedule: (schedule: WorkSchedule | null) => {
          set({ currentSchedule: schedule })
        },

        setCurrentLeaveRequest: (leaveRequest: LeaveRequest | null) => {
          set({ currentLeaveRequest: leaveRequest })
        },

        setCurrentReview: (review: PerformanceReview | null) => {
          set({ currentReview: review })
        },

        clearError: () => {
          set({ error: null })
        },

        setLoading: (loading: boolean) => {
          set({ loading })
        }
      }),
      {
        name: 'employee-store',
        partialize: (state) => ({
          employeeFilters: state.employeeFilters
        })
      }
    ),
    {
      name: 'employee-store'
    }
  )
)