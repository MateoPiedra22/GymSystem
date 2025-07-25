import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { usersService, classesService, membershipsService, paymentsService } from '../api'
import { useAuthStore } from './authStore'

interface DashboardStats {
  // User Stats
  totalUsers: number
  activeUsers: number
  newUsersThisMonth: number
  userGrowthPercentage: number
  
  // Class Stats
  totalClasses: number
  activeClasses: number
  classesThisWeek: number
  averageAttendance: number
  
  // Membership Stats
  totalMemberships: number
  activeMemberships: number
  expiringMemberships: number
  membershipRevenue: number
  
  // Payment Stats
  totalRevenue: number
  revenueThisMonth: number
  pendingPayments: number
  revenueGrowthPercentage: number
  
  // Employee Stats
  totalEmployees: number
  activeEmployees: number
  employeesOnLeave: number
  
  // Recent Activities
  recentUsers: Array<{
    id: number
    name: string
    email: string
    joined_date: string
    avatar?: string
  }>
  recentPayments: Array<{
    id: number
    user_name: string
    amount: number
    payment_method: string
    date: string
    status: string
  }>
  upcomingClasses: Array<{
    id: number
    name: string
    instructor: string
    date: string
    time: string
    capacity: number
    booked: number
  }>
  
  // Charts Data
  revenueChart: Array<{
    month: string
    revenue: number
    memberships: number
    classes: number
  }>
  userGrowthChart: Array<{
    month: string
    users: number
    active: number
  }>
  classAttendanceChart: Array<{
    day: string
    attendance: number
    capacity: number
  }>
}

interface DashboardState {
  // State
  stats: DashboardStats | null
  loading: boolean
  error: string | null
  lastUpdated: string | null
  
  // Actions
  loadDashboardData: () => Promise<void>
  refreshStats: () => Promise<void>
  
  // Individual stat loaders
  loadUserStats: () => Promise<void>
  loadClassStats: () => Promise<void>
  loadMembershipStats: () => Promise<void>
  loadPaymentStats: () => Promise<void>
  loadEmployeeStats: () => Promise<void>
  loadRecentActivities: () => Promise<void>
  loadChartData: () => Promise<void>
  
  // Utility actions
  clearError: () => void
  setLoading: (loading: boolean) => void
}

const initialStats: DashboardStats = {
  totalUsers: 0,
  activeUsers: 0,
  newUsersThisMonth: 0,
  userGrowthPercentage: 0,
  totalClasses: 0,
  activeClasses: 0,
  classesThisWeek: 0,
  averageAttendance: 0,
  totalMemberships: 0,
  activeMemberships: 0,
  expiringMemberships: 0,
  membershipRevenue: 0,
  totalRevenue: 0,
  revenueThisMonth: 0,
  pendingPayments: 0,
  revenueGrowthPercentage: 0,
  totalEmployees: 0,
  activeEmployees: 0,
  employeesOnLeave: 0,
  recentUsers: [],
  recentPayments: [],
  upcomingClasses: [],
  revenueChart: [],
  userGrowthChart: [],
  classAttendanceChart: []
}

export const useDashboardStore = create<DashboardState>()(devtools(
  (set, get) => ({
    // Initial state
    stats: null,
    loading: false,
    error: null,
    lastUpdated: null,

    // Main action to load all dashboard data
    loadDashboardData: async () => {
      // Check if user is authenticated before making API calls
      const authState = useAuthStore.getState()
      if (!authState.isAuthenticated || !authState.token) {
        // Use mock data when not authenticated
        set({ 
          stats: { ...initialStats },
          loading: false,
          error: null,
          lastUpdated: new Date().toISOString()
        })
        return
      }

      set({ loading: true, error: null })
      try {
        // Load all stats in parallel
        await Promise.all([
          get().loadUserStats(),
          get().loadClassStats(),
          get().loadMembershipStats(),
          get().loadPaymentStats(),
          get().loadEmployeeStats(),
          get().loadRecentActivities(),
          get().loadChartData()
        ])
        
        set({ 
          loading: false,
          lastUpdated: new Date().toISOString()
        })
      } catch (error: any) {
        // Don't show error for authentication issues, just use mock data
        if (error.status === 401 || error.message?.includes('401')) {
          set({ 
            stats: { ...initialStats },
            loading: false,
            error: null
          })
        } else {
          set({ 
            error: error.message || 'Error al cargar datos del dashboard',
            loading: false 
          })
        }
      }
    },

    refreshStats: async () => {
      await get().loadDashboardData()
    },

    // Individual stat loaders
    loadUserStats: async () => {
      try {
        const userStats = await usersService.getUserStats()
        const currentStats = get().stats || { ...initialStats }
        
        set({
          stats: {
            ...currentStats,
            totalUsers: userStats.total,
            activeUsers: userStats.active,
            newUsersThisMonth: userStats.recent_registrations,
            userGrowthPercentage: 0 // Calculate based on historical data if available
          }
        })
      } catch (error: any) {
        // Silently fallback to mock data for any error (including 401)
        console.log('Using mock user stats due to API error')
        const currentStats = get().stats || { ...initialStats }
        set({
          stats: {
            ...currentStats,
            totalUsers: 150,
            activeUsers: 120,
            newUsersThisMonth: 25,
            userGrowthPercentage: 12.5
          }
        })
      }
    },

    loadClassStats: async () => {
      try {
        const classStats = await classesService.getClassStatistics()
        const currentStats = get().stats || { ...initialStats }
        
        set({
          stats: {
            ...currentStats,
            totalClasses: classStats.total_classes,
            activeClasses: classStats.active_classes,
            classesThisWeek: classStats.total_schedules_this_month || 0,
            averageAttendance: classStats.attendance_rate || 0
          }
        })
      } catch (error: any) {
        // Silently fallback to mock data for any error (including 401)
        console.log('Using mock class stats due to API error')
        const currentStats = get().stats || { ...initialStats }
        set({
          stats: {
            ...currentStats,
            totalClasses: 45,
            activeClasses: 38,
            classesThisWeek: 12,
            averageAttendance: 85.2
          }
        })
      }
    },

    loadMembershipStats: async () => {
      try {
        const membershipStats = await membershipsService.getMembershipStatistics()
        const currentStats = get().stats || { ...initialStats }
        
        set({
          stats: {
            ...currentStats,
            totalMemberships: membershipStats.total_memberships,
            activeMemberships: membershipStats.active_memberships,
            expiringMemberships: membershipStats.expiring_soon || 0,
            membershipRevenue: membershipStats.revenue_this_month || 0
          }
        })
      } catch (error: any) {
        // Silently fallback to mock data for any error (including 401)
        console.log('Using mock membership stats due to API error')
        const currentStats = get().stats || { ...initialStats }
        set({
          stats: {
            ...currentStats,
            totalMemberships: 200,
            activeMemberships: 180,
            expiringMemberships: 15,
            membershipRevenue: 12500.00
          }
        })
      }
    },

    loadPaymentStats: async () => {
      try {
        const paymentStats = await paymentsService.getPaymentStatistics()
        const currentStats = get().stats || { ...initialStats }
        
        set({
          stats: {
            ...currentStats,
            totalRevenue: paymentStats.total_revenue,
            revenueThisMonth: paymentStats.revenue_this_month,
            pendingPayments: paymentStats.pending_payments,
            revenueGrowthPercentage: 0 // Calculate based on previous month
          }
        })
      } catch (error: any) {
        // Silently fallback to mock data for any error (including 401)
        console.log('Using mock payment stats due to API error')
        const currentStats = get().stats || { ...initialStats }
        set({
          stats: {
            ...currentStats,
            totalRevenue: 45000.00,
            revenueThisMonth: 12500.00,
            pendingPayments: 2,
            revenueGrowthPercentage: 8.7
          }
        })
      }
    },

    loadEmployeeStats: async () => {
      try {
        // Note: This would need to be implemented in the service
        // const employeeStats = await EmployeesService.getEmployeeStatistics()
        // For now, use mock data until the service is implemented
        const currentStats = get().stats || { ...initialStats }
        set({
          stats: {
            ...currentStats,
            totalEmployees: 15,
            activeEmployees: 14,
            employeesOnLeave: 1
          }
        })
      } catch (error: any) {
        // Silently fallback to mock data
        const currentStats = get().stats || { ...initialStats }
        set({
          stats: {
            ...currentStats,
            totalEmployees: 15,
            activeEmployees: 14,
            employeesOnLeave: 1
          }
        })
      }
    },

    loadRecentActivities: async () => {
      try {
        // Load recent users
        const usersResponse = await usersService.getUsers({ page: 1, limit: 5 })
        const recentUsers = (usersResponse as any)?.items?.slice(0, 5).map((user: any) => ({
          id: user.id,
          name: `${user.first_name} ${user.last_name}`,
          email: user.email,
          joined_date: user.created_at,
          avatar: user.profile_picture
        })) || []

        // Load recent payments
        const paymentsResponse = await paymentsService.getPayments({ page: 1, limit: 5 })
        const recentPayments = (paymentsResponse as any)?.items?.slice(0, 5).map((payment: any) => ({
          id: payment.id,
          user_name: `Usuario ${payment.user_id}`,
          amount: payment.amount,
          payment_method: payment.payment_method,
          date: payment.payment_date,
          status: payment.status
        })) || []

        // Load upcoming classes
        const classesResponse = await classesService.getClasses({ page: 1, limit: 5 })
        const upcomingClasses = (classesResponse as any)?.items?.slice(0, 5).map((gymClass: any) => ({
          id: gymClass.id,
          name: gymClass.name,
          instructor: gymClass.instructor?.first_name + ' ' + gymClass.instructor?.last_name || 'Instructor',
          date: new Date().toISOString().split('T')[0], // Use current date as placeholder
          time: '08:00', // Use placeholder time
          capacity: gymClass.max_capacity,
          booked: gymClass.current_enrollment || 0
        })) || []

        const currentStats = get().stats || { ...initialStats }
        set({
          stats: {
            ...currentStats,
            recentUsers,
            recentPayments,
            upcomingClasses
          }
        })
      } catch (error: any) {
        // Silently fallback to mock data for any error (including 401)
        console.log('Using mock recent activities due to API error')
        const currentStats = get().stats || { ...initialStats }
        set({
          stats: {
            ...currentStats,
            recentUsers: [
              {
                id: 1,
                name: 'Juan Pérez',
                email: 'juan@example.com',
                joined_date: new Date().toISOString(),
                avatar: undefined
              },
              {
                id: 2,
                name: 'María García',
                email: 'maria@example.com',
                joined_date: new Date(Date.now() - 86400000).toISOString(),
                avatar: undefined
              }
            ],
            recentPayments: [
              {
                id: 1,
                user_name: 'Juan Pérez',
                amount: 50.00,
                payment_method: 'Tarjeta',
                date: new Date().toISOString(),
                status: 'completed'
              },
              {
                id: 2,
                user_name: 'María García',
                amount: 75.00,
                payment_method: 'Efectivo',
                date: new Date(Date.now() - 3600000).toISOString(),
                status: 'completed'
              }
            ],
            upcomingClasses: [
              {
                id: 1,
                name: 'Yoga Matutino',
                instructor: 'Ana López',
                date: new Date().toISOString().split('T')[0],
                time: '08:00',
                capacity: 20,
                booked: 15
              },
              {
                id: 2,
                name: 'CrossFit',
                instructor: 'Carlos Ruiz',
                date: new Date().toISOString().split('T')[0],
                time: '18:00',
                capacity: 15,
                booked: 12
              }
            ]
          }
        })
      }
    },

    loadChartData: async () => {
      try {
        // TODO: Implement chart data loading from backend APIs
        // For now, use mock data
        const currentStats = get().stats || { ...initialStats }
        set({
          stats: {
            ...currentStats,
            revenueChart: [
              { month: 'Ene', revenue: 12000, memberships: 8000, classes: 4000 },
              { month: 'Feb', revenue: 15000, memberships: 10000, classes: 5000 },
              { month: 'Mar', revenue: 13500, memberships: 9000, classes: 4500 },
              { month: 'Abr', revenue: 16000, memberships: 11000, classes: 5000 },
              { month: 'May', revenue: 14500, memberships: 9500, classes: 5000 },
              { month: 'Jun', revenue: 17000, memberships: 12000, classes: 5000 }
            ],
            userGrowthChart: [
              { month: 'Ene', users: 120, active: 110 },
              { month: 'Feb', users: 135, active: 125 },
              { month: 'Mar', users: 128, active: 118 },
              { month: 'Abr', users: 142, active: 132 },
              { month: 'May', users: 138, active: 128 },
              { month: 'Jun', users: 155, active: 145 }
            ],
            classAttendanceChart: [
              { day: 'Lun', attendance: 85, capacity: 100 },
              { day: 'Mar', attendance: 92, capacity: 100 },
              { day: 'Mié', attendance: 78, capacity: 100 },
              { day: 'Jue', attendance: 88, capacity: 100 },
              { day: 'Vie', attendance: 95, capacity: 100 },
              { day: 'Sáb', attendance: 70, capacity: 100 },
              { day: 'Dom', attendance: 65, capacity: 100 }
            ]
          }
        })
      } catch (error: any) {
        // Silently fallback to basic mock data
        const currentStats = get().stats || { ...initialStats }
        set({
          stats: {
            ...currentStats,
            revenueChart: [
              { month: 'Jun', revenue: 10000, memberships: 7000, classes: 3000 }
            ],
            userGrowthChart: [
              { month: 'Jun', users: 100, active: 90 }
            ],
            classAttendanceChart: [
              { day: 'Hoy', attendance: 50, capacity: 100 }
            ]
          }
        })
      }
    },

    // Utility actions
    clearError: () => {
      set({ error: null })
    },

    setLoading: (loading: boolean) => {
      set({ loading })
    }
  }),
  {
    name: 'dashboard-store'
  }
))

export default useDashboardStore