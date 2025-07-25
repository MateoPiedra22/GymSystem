import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { MembershipsService } from '../api/services/memberships'
import {
  MembershipPlan,
  UserMembership,
  CreateMembershipPlanRequest,
  UpdateMembershipPlanRequest,
  AssignMembershipRequest,
  MembershipSearchParams,
  MembershipStatistics,
  MembershipUsage,
  PaginationParams
} from '../types'

interface MembershipState {
  // State
  membershipPlans: MembershipPlan[]
  userMemberships: UserMembership[]
  currentPlan: MembershipPlan | null
  currentMembership: UserMembership | null
  membershipStats: MembershipStatistics | null
  membershipUsage: MembershipUsage | null
  expiringMemberships: UserMembership[]
  loading: boolean
  error: string | null
  
  // Pagination
  planPagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  membershipPagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  
  // Filters
  membershipFilters: MembershipSearchParams
  
  // Actions - Membership Plans
  getMembershipPlans: (params?: PaginationParams) => Promise<void>
  getMembershipPlan: (id: number) => Promise<void>
  createMembershipPlan: (data: CreateMembershipPlanRequest) => Promise<MembershipPlan | null>
  updateMembershipPlan: (id: number, data: UpdateMembershipPlanRequest) => Promise<MembershipPlan | null>
  deleteMembershipPlan: (id: number) => Promise<boolean>
  toggleMembershipPlanStatus: (id: number) => Promise<boolean>
  
  // Actions - User Memberships
  getUserMemberships: (params?: MembershipSearchParams) => Promise<void>
  getUserMembership: (id: number) => Promise<void>
  assignMembership: (data: AssignMembershipRequest) => Promise<UserMembership | null>
  cancelMembership: (id: number, reason?: string) => Promise<boolean>
  suspendMembership: (id: number, reason?: string) => Promise<boolean>
  reactivateMembership: (id: number) => Promise<boolean>
  renewMembership: (id: number) => Promise<boolean>
  
  // Actions - Statistics & Usage
  getMembershipStatistics: () => Promise<void>
  getMembershipUsage: (membershipId: number) => Promise<void>
  getExpiringMemberships: (days?: number) => Promise<void>
  sendRenewalReminders: (membershipIds: number[]) => Promise<boolean>
  
  // Actions - Bulk Operations
  bulkAssignMemberships: (data: {
    user_ids: number[]
    membership_plan_id: number
    start_date: string
    auto_renew?: boolean
  }) => Promise<boolean>
  bulkCancelMemberships: (data: {
    membership_ids: number[]
    reason?: string
  }) => Promise<boolean>
  
  // Actions - Import/Export
  exportMemberships: (params?: MembershipSearchParams) => Promise<boolean>
  importMemberships: (file: File) => Promise<any>
  
  // Utility actions
  setMembershipFilters: (filters: Partial<MembershipSearchParams>) => void
  clearFilters: () => void
  setCurrentPlan: (plan: MembershipPlan | null) => void
  setCurrentMembership: (membership: UserMembership | null) => void
  clearError: () => void
  setLoading: (loading: boolean) => void
}

const initialMembershipFilters: MembershipSearchParams = {
  page: 1,
  limit: 10
}

export const useMembershipStore = create<MembershipState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        membershipPlans: [],
        userMemberships: [],
        currentPlan: null,
        currentMembership: null,
        membershipStats: null,
        membershipUsage: null,
        expiringMemberships: [],
        loading: false,
        error: null,
        
        planPagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        membershipPagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        
        membershipFilters: initialMembershipFilters,

        // Actions - Membership Plans
        getMembershipPlans: async (params?: PaginationParams) => {
          set({ loading: true, error: null })
          try {
            const response = await MembershipsService.getMembershipPlans(params)
            set({
              membershipPlans: response.items,
              planPagination: {
                page: response.page,
                limit: response.limit,
                total: response.total,
                totalPages: response.pages
              },
              loading: false
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar planes de membresía',
              loading: false 
            })
          }
        },

        getMembershipPlan: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const plan = await MembershipsService.getMembershipPlan(id)
            set({ currentPlan: plan, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar plan de membresía',
              loading: false 
            })
          }
        },

        createMembershipPlan: async (data: CreateMembershipPlanRequest) => {
          set({ loading: true, error: null })
          try {
            const newPlan = await MembershipsService.createMembershipPlan(data)
            const { membershipPlans } = get()
            set({ 
              membershipPlans: [newPlan, ...membershipPlans],
              loading: false 
            })
            return newPlan
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear plan de membresía',
              loading: false 
            })
            return null
          }
        },

        updateMembershipPlan: async (id: number, data: UpdateMembershipPlanRequest) => {
          set({ loading: true, error: null })
          try {
            const updatedPlan = await MembershipsService.updateMembershipPlan(id, data)
            const { membershipPlans, currentPlan } = get()
            set({ 
              membershipPlans: membershipPlans.map(p => p.id === id ? updatedPlan : p),
              currentPlan: currentPlan?.id === id ? updatedPlan : currentPlan,
              loading: false 
            })
            return updatedPlan
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar plan de membresía',
              loading: false 
            })
            return null
          }
        },

        deleteMembershipPlan: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await MembershipsService.deleteMembershipPlan(id)
            const { membershipPlans } = get()
            set({ 
              membershipPlans: membershipPlans.filter(p => p.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar plan de membresía',
              loading: false 
            })
            return false
          }
        },

        toggleMembershipPlanStatus: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const updatedPlan = await MembershipsService.toggleMembershipPlanStatus(id)
            const { membershipPlans, currentPlan } = get()
            set({ 
              membershipPlans: membershipPlans.map(p => p.id === id ? updatedPlan : p),
              currentPlan: currentPlan?.id === id ? updatedPlan : currentPlan,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cambiar estado del plan',
              loading: false 
            })
            return false
          }
        },

        // Actions - User Memberships
        getUserMemberships: async (params?: MembershipSearchParams) => {
          set({ loading: true, error: null })
          try {
            const response = await MembershipsService.getUserMemberships(params)
            set({
              userMemberships: response.items,
              membershipPagination: {
                page: response.page,
                limit: response.limit,
                total: response.total,
                totalPages: response.pages
              },
              loading: false
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar membresías',
              loading: false 
            })
          }
        },

        getUserMembership: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const membership = await MembershipsService.getUserMembership(id)
            set({ currentMembership: membership, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar membresía',
              loading: false 
            })
          }
        },

        assignMembership: async (data: AssignMembershipRequest) => {
          set({ loading: true, error: null })
          try {
            const newMembership = await MembershipsService.assignMembership(data)
            const { userMemberships } = get()
            set({ 
              userMemberships: [newMembership, ...userMemberships],
              loading: false 
            })
            return newMembership
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al asignar membresía',
              loading: false 
            })
            return null
          }
        },

        cancelMembership: async (id: number, reason?: string) => {
          set({ loading: true, error: null })
          try {
            const updatedMembership = await MembershipsService.cancelMembership(id, reason)
            const { userMemberships, currentMembership } = get()
            set({ 
              userMemberships: userMemberships.map(m => m.id === id ? updatedMembership : m),
              currentMembership: currentMembership?.id === id ? updatedMembership : currentMembership,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cancelar membresía',
              loading: false 
            })
            return false
          }
        },

        suspendMembership: async (id: number, reason?: string) => {
          set({ loading: true, error: null })
          try {
            const updatedMembership = await MembershipsService.suspendMembership(id, reason)
            const { userMemberships, currentMembership } = get()
            set({ 
              userMemberships: userMemberships.map(m => m.id === id ? updatedMembership : m),
              currentMembership: currentMembership?.id === id ? updatedMembership : currentMembership,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al suspender membresía',
              loading: false 
            })
            return false
          }
        },

        reactivateMembership: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const updatedMembership = await MembershipsService.reactivateMembership(id)
            const { userMemberships, currentMembership } = get()
            set({ 
              userMemberships: userMemberships.map(m => m.id === id ? updatedMembership : m),
              currentMembership: currentMembership?.id === id ? updatedMembership : currentMembership,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al reactivar membresía',
              loading: false 
            })
            return false
          }
        },

        renewMembership: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const renewedMembership = await MembershipsService.renewMembership(id)
            const { userMemberships, currentMembership } = get()
            set({ 
              userMemberships: userMemberships.map(m => m.id === id ? renewedMembership : m),
              currentMembership: currentMembership?.id === id ? renewedMembership : currentMembership,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al renovar membresía',
              loading: false 
            })
            return false
          }
        },

        // Actions - Statistics & Usage
        getMembershipStatistics: async () => {
          set({ loading: true, error: null })
          try {
            const membershipStats = await MembershipsService.getMembershipStatistics()
            set({ membershipStats, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar estadísticas de membresías',
              loading: false 
            })
          }
        },

        getMembershipUsage: async (membershipId: number) => {
          set({ loading: true, error: null })
          try {
            const membershipUsage = await MembershipsService.getMembershipUsage(membershipId)
            set({ membershipUsage, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar uso de membresía',
              loading: false 
            })
          }
        },

        getExpiringMemberships: async (days?: number) => {
          set({ loading: true, error: null })
          try {
            const expiringMemberships = await MembershipsService.getExpiringMemberships(days)
            set({ expiringMemberships, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar membresías por vencer',
              loading: false 
            })
          }
        },

        sendRenewalReminders: async (membershipIds: number[]) => {
          set({ loading: true, error: null })
          try {
            await MembershipsService.sendRenewalReminders(membershipIds)
            set({ loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al enviar recordatorios de renovación',
              loading: false 
            })
            return false
          }
        },

        // Actions - Bulk Operations
        bulkAssignMemberships: async (data: {
          user_ids: number[]
          membership_plan_id: number
          start_date: string
          auto_renew?: boolean
        }) => {
          set({ loading: true, error: null })
          try {
            const newMemberships = await MembershipsService.bulkAssignMemberships(data)
            const { userMemberships } = get()
            set({ 
              userMemberships: [...newMemberships, ...userMemberships],
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al asignar membresías en lote',
              loading: false 
            })
            return false
          }
        },

        bulkCancelMemberships: async (data: {
          membership_ids: number[]
          reason?: string
        }) => {
          set({ loading: true, error: null })
          try {
            await MembershipsService.bulkCancelMemberships(data)
            // Refresh memberships list
            await get().getUserMemberships()
            set({ loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cancelar membresías en lote',
              loading: false 
            })
            return false
          }
        },

        // Actions - Import/Export
        exportMemberships: async (params?: MembershipSearchParams) => {
          set({ loading: true, error: null })
          try {
            await MembershipsService.exportMemberships(params)
            set({ loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al exportar membresías',
              loading: false 
            })
            return false
          }
        },

        importMemberships: async (file: File) => {
          set({ loading: true, error: null })
          try {
            const result = await MembershipsService.importMemberships(file)
            // Refresh memberships list after import
            await get().getUserMemberships()
            set({ loading: false })
            return result
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al importar membresías',
              loading: false 
            })
            return null
          }
        },

        // Utility actions
        setMembershipFilters: (filters: Partial<MembershipSearchParams>) => {
          set(state => ({ 
            membershipFilters: { ...state.membershipFilters, ...filters } 
          }))
        },

        clearFilters: () => {
          set({ membershipFilters: initialMembershipFilters })
        },

        setCurrentPlan: (plan: MembershipPlan | null) => {
          set({ currentPlan: plan })
        },

        setCurrentMembership: (membership: UserMembership | null) => {
          set({ currentMembership: membership })
        },

        clearError: () => {
          set({ error: null })
        },

        setLoading: (loading: boolean) => {
          set({ loading })
        }
      }),
      {
        name: 'membership-store',
        partialize: (state) => ({
          membershipFilters: state.membershipFilters
        })
      }
    ),
    {
      name: 'membership-store'
    }
  )
)