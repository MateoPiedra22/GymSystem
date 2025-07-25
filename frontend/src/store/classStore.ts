import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { ClassesService } from '../api/services/classes'
import {
  GymClass,
  ClassSchedule,
  ClassBooking,
  ClassCategory,
  CreateClassRequest,
  UpdateClassRequest,
  ClassSearchParams,
  CreateScheduleRequest,
  UpdateScheduleRequest,
  ScheduleSearchParams,
  BookingSearchParams,
  ClassStatistics,
  ClassAttendance,
  ClassRating,
  ClassWaitlist,

  ClassPackage,
  UserClassPackage,
  BookClassRequest
} from '../types'

interface ClassState {
  // State
  classes: GymClass[]
  schedules: ClassSchedule[]
  bookings: ClassBooking[]
  categories: ClassCategory[]
  currentClass: GymClass | null
  currentSchedule: ClassSchedule | null
  currentBooking: ClassBooking | null
  classStats: ClassStatistics | null
  waitlist: ClassWaitlist[]
  attendance: ClassAttendance[]
  ratings: ClassRating[]
  packages: ClassPackage[]
  userPackages: UserClassPackage[]
  loading: boolean
  error: string | null
  
  // Pagination
  classPagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  schedulePagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  bookingPagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  
  // Filters
  classFilters: ClassSearchParams
  scheduleFilters: ScheduleSearchParams
  bookingFilters: BookingSearchParams
  
  // Actions - Classes
  getClasses: (params?: ClassSearchParams) => Promise<void>
  getClass: (id: number) => Promise<void>
  createClass: (data: CreateClassRequest) => Promise<GymClass | null>
  updateClass: (id: number, data: UpdateClassRequest) => Promise<GymClass | null>
  deleteClass: (id: number) => Promise<boolean>
  toggleClassStatus: (id: number) => Promise<boolean>
  
  // Actions - Categories
  getClassCategories: () => Promise<void>
  createClassCategory: (data: { name: string; description: string; icon?: string; color?: string }) => Promise<ClassCategory | null>
  updateClassCategory: (id: number, data: any) => Promise<ClassCategory | null>
  deleteClassCategory: (id: number) => Promise<boolean>
  
  // Actions - Schedules
  getSchedules: (params?: ScheduleSearchParams) => Promise<void>
  getSchedule: (id: number) => Promise<void>
  createSchedule: (data: CreateScheduleRequest) => Promise<ClassSchedule | null>
  updateSchedule: (id: number, data: UpdateScheduleRequest) => Promise<ClassSchedule | null>
  deleteSchedule: (id: number) => Promise<boolean>
  cancelSchedule: (id: number, data: { reason: string; notify_participants?: boolean }) => Promise<boolean>
  
  // Actions - Bookings
  getBookings: (params?: BookingSearchParams) => Promise<void>
  getBooking: (id: number) => Promise<void>
  createBooking: (data: BookClassRequest) => Promise<ClassBooking | null>
  cancelBooking: (id: number, data?: { reason?: string; refund_requested?: boolean }) => Promise<boolean>
  checkInBooking: (id: number) => Promise<boolean>
  noShowBooking: (id: number, reason?: string) => Promise<boolean>
  
  // Actions - Waitlist
  joinWaitlist: (scheduleId: number, data?: any) => Promise<ClassWaitlist | null>
  leaveWaitlist: (waitlistId: number) => Promise<boolean>
  getWaitlist: (scheduleId: number) => Promise<void>
  processWaitlist: (scheduleId: number, data: any) => Promise<any>
  
  // Actions - Attendance
  markAttendance: (scheduleId: number, data: any) => Promise<boolean>
  getAttendance: (scheduleId: number) => Promise<void>
  updateAttendance: (attendanceId: number, data: any) => Promise<boolean>
  
  // Actions - Ratings
  rateClass: (scheduleId: number, data: any) => Promise<ClassRating | null>
  getClassRatings: (classId: number, params?: any) => Promise<void>
  updateRating: (ratingId: number, data: any) => Promise<boolean>
  deleteRating: (ratingId: number) => Promise<boolean>
  
  // Actions - Packages
  getClassPackages: () => Promise<void>
  createClassPackage: (data: any) => Promise<ClassPackage | null>
  updateClassPackage: (id: number, data: any) => Promise<ClassPackage | null>
  deleteClassPackage: (id: number) => Promise<boolean>
  getUserClassPackages: (userId: number) => Promise<void>
  purchaseClassPackage: (data: any) => Promise<UserClassPackage | null>
  
  // Actions - Statistics
  getClassStatistics: () => Promise<void>
  getClassUsageStats: (classId: number) => Promise<any>
  getInstructorStats: (instructorId: number) => Promise<any>
  
  // Utility actions
  setClassFilters: (filters: Partial<ClassSearchParams>) => void
  setScheduleFilters: (filters: Partial<ScheduleSearchParams>) => void
  setBookingFilters: (filters: Partial<BookingSearchParams>) => void
  clearFilters: () => void
  setCurrentClass: (gymClass: GymClass | null) => void
  setCurrentSchedule: (schedule: ClassSchedule | null) => void
  setCurrentBooking: (booking: ClassBooking | null) => void
  clearError: () => void
  setLoading: (loading: boolean) => void
}

const initialClassFilters: ClassSearchParams = {
  page: 1,
  limit: 10
}

const initialScheduleFilters: ScheduleSearchParams = {
  page: 1,
  limit: 10
}

const initialBookingFilters: BookingSearchParams = {
  page: 1,
  limit: 10
}

export const useClassStore = create<ClassState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        classes: [],
        schedules: [],
        bookings: [],
        categories: [],
        currentClass: null,
        currentSchedule: null,
        currentBooking: null,
        classStats: null,
        waitlist: [],
        attendance: [],
        ratings: [],
        packages: [],
        userPackages: [],
        loading: false,
        error: null,
        
        classPagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        schedulePagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        bookingPagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        
        classFilters: initialClassFilters,
        scheduleFilters: initialScheduleFilters,
        bookingFilters: initialBookingFilters,

        // Actions - Classes
        getClasses: async (params?: ClassSearchParams) => {
          set({ loading: true, error: null })
          try {
            const response = await ClassesService.getClasses(params)
            set({
              classes: response.items,
              classPagination: {
                page: response.page,
                limit: response.limit,
                total: response.total,
                totalPages: response.pages
              },
              loading: false
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar clases',
              loading: false 
            })
          }
        },

        getClass: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const gymClass = await ClassesService.getClass(id)
            set({ currentClass: gymClass, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar clase',
              loading: false 
            })
          }
        },

        createClass: async (data: CreateClassRequest) => {
          set({ loading: true, error: null })
          try {
            const newClass = await ClassesService.createClass(data)
            const { classes } = get()
            set({ 
              classes: [newClass, ...classes],
              loading: false 
            })
            return newClass
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear clase',
              loading: false 
            })
            return null
          }
        },

        updateClass: async (id: number, data: UpdateClassRequest) => {
          set({ loading: true, error: null })
          try {
            const updatedClass = await ClassesService.updateClass(id, data)
            const { classes, currentClass } = get()
            set({ 
              classes: classes.map(c => c.id === id ? updatedClass : c),
              currentClass: currentClass?.id === id ? updatedClass : currentClass,
              loading: false 
            })
            return updatedClass
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar clase',
              loading: false 
            })
            return null
          }
        },

        deleteClass: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await ClassesService.deleteClass(id)
            const { classes } = get()
            set({ 
              classes: classes.filter(c => c.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar clase',
              loading: false 
            })
            return false
          }
        },

        toggleClassStatus: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const updatedClass = await ClassesService.toggleClassStatus(id)
            const { classes, currentClass } = get()
            set({ 
              classes: classes.map(c => c.id === id ? updatedClass : c),
              currentClass: currentClass?.id === id ? updatedClass : currentClass,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cambiar estado de clase',
              loading: false 
            })
            return false
          }
        },

        // Actions - Categories
        getClassCategories: async () => {
          set({ loading: true, error: null })
          try {
            const categories = await ClassesService.getClassCategories()
            set({ categories, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar categorías',
              loading: false 
            })
          }
        },

        createClassCategory: async (data) => {
          set({ loading: true, error: null })
          try {
            const newCategory = await ClassesService.createClassCategory(data)
            const state = get()
            const { categories } = state
            set({ 
              categories: [newCategory, ...categories],
              loading: false 
            })
            return newCategory
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear categoría',
              loading: false 
            })
            return null
          }
        },

        updateClassCategory: async (id: number, data: any) => {
          set({ loading: true, error: null })
          try {
            const updatedCategory = await ClassesService.updateClassCategory(id, data)
            const state = get()
            const { categories } = state
            set({ 
              categories: categories.map((c: any) => c.id === id ? updatedCategory : c),
              loading: false 
            })
            return updatedCategory
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar categoría',
              loading: false 
            })
            return null
          }
        },

        deleteClassCategory: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await ClassesService.deleteClassCategory(id)
            const state = get()
            const { categories } = state
            set({ 
              categories: categories.filter((c: any) => c.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar categoría',
              loading: false 
            })
            return false
          }
        },

        // Actions - Schedules
        getSchedules: async (params?: ScheduleSearchParams) => {
          set({ loading: true, error: null })
          try {
            const response = await ClassesService.getSchedules(params)
            set({
              schedules: response.items,
              schedulePagination: {
                page: response.page,
                limit: response.limit,
                total: response.total,
                totalPages: response.pages
              },
              loading: false
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar horarios',
              loading: false 
            })
          }
        },

        getSchedule: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const schedule = await ClassesService.getSchedule(id)
            set({ currentSchedule: schedule, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar horario',
              loading: false 
            })
          }
        },

        createSchedule: async (data: CreateScheduleRequest) => {
          set({ loading: true, error: null })
          try {
            const newSchedule = await ClassesService.createSchedule(data)
            const state = get()
            const { schedules } = state
            set({ 
              schedules: [newSchedule, ...schedules],
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

        updateSchedule: async (id: number, data: UpdateScheduleRequest) => {
          set({ loading: true, error: null })
          try {
            const updatedSchedule = await ClassesService.updateSchedule(id, data)
            const state = get()
            const { schedules, currentSchedule } = state
            set({ 
              schedules: schedules.map((s: any) => s.id === id ? updatedSchedule : s),
              currentSchedule: currentSchedule?.id === id ? updatedSchedule : currentSchedule,
              loading: false 
            })
            return updatedSchedule
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar horario',
              loading: false 
            })
            return null
          }
        },

        deleteSchedule: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await ClassesService.deleteSchedule(id)
            const state = get()
            const { schedules } = state
            set({ 
              schedules: schedules.filter((s: any) => s.id !== id),
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

        cancelSchedule: async (id: number, data: { reason: string; notify_participants?: boolean }) => {
          set({ loading: true, error: null })
          try {
            const updatedSchedule = await ClassesService.cancelSchedule(id, data)
            const state = get()
            const { schedules, currentSchedule } = state
            set({ 
              schedules: schedules.map((s: any) => s.id === id ? updatedSchedule : s),
              currentSchedule: currentSchedule?.id === id ? updatedSchedule : currentSchedule,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cancelar horario',
              loading: false 
            })
            return false
          }
        },

        // Actions - Bookings
        getBookings: async (params?: BookingSearchParams) => {
          set({ loading: true, error: null })
          try {
            const response = await ClassesService.getBookings(params)
            set({
              bookings: response.items,
              bookingPagination: {
                page: response.page,
                limit: response.limit,
                total: response.total,
                totalPages: response.pages
              },
              loading: false
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar reservas',
              loading: false 
            })
          }
        },

        getBooking: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const booking = await ClassesService.getBooking(id)
            set({ currentBooking: booking, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar reserva',
              loading: false 
            })
          }
        },

        createBooking: async (data: BookClassRequest) => {
          set({ loading: true, error: null })
          try {
            const newBooking = await ClassesService.createBooking(data)
            const state = get()
            const { bookings } = state
            set({ 
              bookings: [newBooking, ...bookings],
              loading: false 
            })
            return newBooking
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear reserva',
              loading: false 
            })
            return null
          }
        },

        cancelBooking: async (id: number, data?: { reason?: string; refund_requested?: boolean }) => {
          set({ loading: true, error: null })
          try {
            const updatedBooking = await ClassesService.cancelBooking(id, data)
            const state = get()
            const { bookings, currentBooking } = state
            set({ 
              bookings: bookings.map((b: any) => b.id === id ? updatedBooking : b),
              currentBooking: currentBooking?.id === id ? updatedBooking : currentBooking,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cancelar reserva',
              loading: false 
            })
            return false
          }
        },

        checkInBooking: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const updatedBooking = await ClassesService.checkInBooking(id)
            const { bookings, currentBooking } = get()
            set({ 
              bookings: bookings.map(b => b.id === id ? updatedBooking : b),
              currentBooking: currentBooking?.id === id ? updatedBooking : currentBooking,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al hacer check-in',
              loading: false 
            })
            return false
          }
        },

        noShowBooking: async (id: number, reason?: string) => {
          set({ loading: true, error: null })
          try {
            const updatedBooking = await ClassesService.noShowBooking(id, reason)
            const { bookings, currentBooking } = get()
            set({ 
              bookings: bookings.map(b => b.id === id ? updatedBooking : b),
              currentBooking: currentBooking?.id === id ? updatedBooking : currentBooking,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al marcar no show',
              loading: false 
            })
            return false
          }
        },

        // Actions - Waitlist
        joinWaitlist: async (scheduleId: number, data?: any) => {
          set({ loading: true, error: null })
          try {
            const waitlistEntry = await ClassesService.joinWaitlist(scheduleId, data)
            const state = get()
            const { waitlist } = state
            set({ 
              waitlist: [waitlistEntry, ...waitlist],
              loading: false 
            })
            return waitlistEntry
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al unirse a lista de espera',
              loading: false 
            })
            return null
          }
        },

        leaveWaitlist: async (waitlistId: number) => {
          set({ loading: true, error: null })
          try {
            await ClassesService.leaveWaitlist(waitlistId)
            const state = get()
            const { waitlist } = state
            set({ 
              waitlist: waitlist.filter((w: any) => w.id !== waitlistId),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al salir de lista de espera',
              loading: false 
            })
            return false
          }
        },

        getWaitlist: async (scheduleId: number) => {
          set({ loading: true, error: null })
          try {
            const waitlist = await ClassesService.getWaitlist(scheduleId)
            set({ waitlist, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar lista de espera',
              loading: false 
            })
          }
        },

        processWaitlist: async (scheduleId: number, data: any) => {
          set({ loading: true, error: null })
          try {
            const result = await ClassesService.processWaitlist(scheduleId, data)
            set({ loading: false })
            return result
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al procesar lista de espera',
              loading: false 
            })
            return null
          }
        },

        // Actions - Attendance
        markAttendance: async (scheduleId: number, data: any) => {
          set({ loading: true, error: null })
          try {
            const attendance = await ClassesService.markAttendance(scheduleId, data)
            set({ attendance, loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al marcar asistencia',
              loading: false 
            })
            return false
          }
        },

        getAttendance: async (scheduleId: number) => {
          set({ loading: true, error: null })
          try {
            const attendance = await ClassesService.getAttendance(scheduleId)
            set({ attendance, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar asistencia',
              loading: false 
            })
          }
        },

        updateAttendance: async (attendanceId: number, data: any) => {
          set({ loading: true, error: null })
          try {
            const updatedAttendance = await ClassesService.updateAttendance(attendanceId, data)
            const { attendance } = get()
            set({ 
              attendance: attendance.map(a => a.id === attendanceId ? updatedAttendance : a),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar asistencia',
              loading: false 
            })
            return false
          }
        },

        // Actions - Ratings
        rateClass: async (scheduleId: number, data: any) => {
          set({ loading: true, error: null })
          try {
            const rating = await ClassesService.rateClass(scheduleId, data)
            const { ratings } = get()
            set({ 
              ratings: [rating, ...ratings],
              loading: false 
            })
            return rating
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al calificar clase',
              loading: false 
            })
            return null
          }
        },

        getClassRatings: async (classId: number, params?: any) => {
          set({ loading: true, error: null })
          try {
            const response = await ClassesService.getClassRatings(classId, params)
            set({ ratings: response.items, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar calificaciones',
              loading: false 
            })
          }
        },

        updateRating: async (ratingId: number, data: any) => {
          set({ loading: true, error: null })
          try {
            const updatedRating = await ClassesService.updateRating(ratingId, data)
            const { ratings } = get()
            set({ 
              ratings: ratings.map(r => r.id === ratingId ? updatedRating : r),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar calificación',
              loading: false 
            })
            return false
          }
        },

        deleteRating: async (ratingId: number) => {
          set({ loading: true, error: null })
          try {
            await ClassesService.deleteRating(ratingId)
            const { ratings } = get()
            set({ 
              ratings: ratings.filter(r => r.id !== ratingId),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar calificación',
              loading: false 
            })
            return false
          }
        },

        // Actions - Packages
        getClassPackages: async () => {
          set({ loading: true, error: null })
          try {
            const packages = await ClassesService.getClassPackages()
            set({ packages, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar paquetes',
              loading: false 
            })
          }
        },

        createClassPackage: async (data: any) => {
          set({ loading: true, error: null })
          try {
            const newPackage = await ClassesService.createClassPackage(data)
            const { packages } = get()
            set({ 
              packages: [newPackage, ...packages],
              loading: false 
            })
            return newPackage
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear paquete',
              loading: false 
            })
            return null
          }
        },

        updateClassPackage: async (id: number, data: any) => {
          set({ loading: true, error: null })
          try {
            const updatedPackage = await ClassesService.updateClassPackage(id, data)
            const { packages } = get()
            set({ 
              packages: packages.map(p => p.id === id ? updatedPackage : p),
              loading: false 
            })
            return updatedPackage
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar paquete',
              loading: false 
            })
            return null
          }
        },

        deleteClassPackage: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await ClassesService.deleteClassPackage(id)
            const { packages } = get()
            set({ 
              packages: packages.filter(p => p.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar paquete',
              loading: false 
            })
            return false
          }
        },

        getUserClassPackages: async (userId: number) => {
          set({ loading: true, error: null })
          try {
            const userPackages = await ClassesService.getUserClassPackages(userId)
            set({ userPackages, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar paquetes del usuario',
              loading: false 
            })
          }
        },

        purchaseClassPackage: async (data: any) => {
          set({ loading: true, error: null })
          try {
            const userPackage = await ClassesService.purchaseClassPackage(data)
            const { userPackages } = get()
            set({ 
              userPackages: [userPackage, ...userPackages],
              loading: false 
            })
            return userPackage
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al comprar paquete',
              loading: false 
            })
            return null
          }
        },

        // Actions - Statistics
        getClassStatistics: async () => {
          set({ loading: true, error: null })
          try {
            const classStats = await ClassesService.getClassStatistics()
            set({ classStats, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar estadísticas',
              loading: false 
            })
          }
        },

        getClassUsageStats: async (classId: number) => {
          set({ loading: true, error: null })
          try {
            const stats = await ClassesService.getClassUsageStats(classId)
            set({ loading: false })
            return stats
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar estadísticas de uso',
              loading: false 
            })
            return null
          }
        },

        getInstructorStats: async (instructorId: number) => {
          set({ loading: true, error: null })
          try {
            const stats = await ClassesService.getInstructorStats(instructorId)
            set({ loading: false })
            return stats
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar estadísticas del instructor',
              loading: false 
            })
            return null
          }
        },

        // Utility actions
        setClassFilters: (filters: Partial<ClassSearchParams>) => {
          set(state => ({ 
            classFilters: { ...state.classFilters, ...filters } 
          }))
        },

        setScheduleFilters: (filters: Partial<ScheduleSearchParams>) => {
          set(state => ({ 
            scheduleFilters: { ...state.scheduleFilters, ...filters } 
          }))
        },

        setBookingFilters: (filters: Partial<BookingSearchParams>) => {
          set(state => ({ 
            bookingFilters: { ...state.bookingFilters, ...filters } 
          }))
        },

        clearFilters: () => {
          set({ 
            classFilters: initialClassFilters,
            scheduleFilters: initialScheduleFilters,
            bookingFilters: initialBookingFilters
          })
        },

        setCurrentClass: (gymClass: GymClass | null) => {
          set({ currentClass: gymClass })
        },

        setCurrentSchedule: (schedule: ClassSchedule | null) => {
          set({ currentSchedule: schedule })
        },

        setCurrentBooking: (booking: ClassBooking | null) => {
          set({ currentBooking: booking })
        },

        clearError: () => {
          set({ error: null })
        },

        setLoading: (loading: boolean) => {
          set({ loading })
        }
      }),
      {
        name: 'class-store',
        partialize: (state) => ({
          classFilters: state.classFilters,
          scheduleFilters: state.scheduleFilters,
          bookingFilters: state.bookingFilters
        })
      }
    )
  )
)

export default useClassStore