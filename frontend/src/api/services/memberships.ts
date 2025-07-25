import { apiClient } from '../client'
import { API_ENDPOINTS } from '../config'
import {
  MembershipPlan,
  UserMembership,
  CreateMembershipPlanRequest,
  UpdateMembershipPlanRequest,
  AssignMembershipRequest,
  MembershipSearchParams,
  MembershipListResponse,
  MembershipPlanListResponse,
  MembershipStatistics,
  MembershipUsage,
  PaginationParams
} from '../../types'

export class MembershipsService {
  // Membership Plans
  static async getMembershipPlans(params?: PaginationParams): Promise<MembershipPlanListResponse> {
    return apiClient.get(API_ENDPOINTS.MEMBERSHIPS.PLANS, { params })
  }

  static async getMembershipPlan(id: number): Promise<MembershipPlan> {
    return apiClient.get(`${API_ENDPOINTS.MEMBERSHIPS.PLANS}/${id}`)
  }

  static async createMembershipPlan(data: CreateMembershipPlanRequest): Promise<MembershipPlan> {
    return apiClient.post(API_ENDPOINTS.MEMBERSHIPS.PLANS, data)
  }

  static async updateMembershipPlan(id: number, data: UpdateMembershipPlanRequest): Promise<MembershipPlan> {
    return apiClient.put(`${API_ENDPOINTS.MEMBERSHIPS.PLANS}/${id}`, data)
  }

  static async deleteMembershipPlan(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.MEMBERSHIPS.PLANS}/${id}`)
  }

  static async toggleMembershipPlanStatus(id: number): Promise<MembershipPlan> {
    return apiClient.patch(`${API_ENDPOINTS.MEMBERSHIPS.PLANS}/${id}/toggle-status`)
  }

  // User Memberships
  static async getUserMemberships(params?: MembershipSearchParams): Promise<MembershipListResponse> {
    return apiClient.get(API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS, { params })
  }

  static async getUserMembership(id: number): Promise<UserMembership> {
    return apiClient.get(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${id}`)
  }

  static async assignMembership(data: AssignMembershipRequest): Promise<UserMembership> {
    return apiClient.post(API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS, data)
  }

  static async cancelMembership(id: number, reason?: string): Promise<UserMembership> {
    return apiClient.patch(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${id}/cancel`, { reason })
  }

  static async suspendMembership(id: number, reason?: string): Promise<UserMembership> {
    return apiClient.patch(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${id}/suspend`, { reason })
  }

  static async reactivateMembership(id: number): Promise<UserMembership> {
    return apiClient.patch(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${id}/reactivate`)
  }

  static async renewMembership(id: number): Promise<UserMembership> {
    return apiClient.post(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${id}/renew`)
  }

  // Membership Statistics
  static async getMembershipStatistics(): Promise<MembershipStatistics> {
    return apiClient.get(API_ENDPOINTS.MEMBERSHIPS.STATISTICS)
  }

  static async getMembershipUsage(membershipId: number): Promise<MembershipUsage> {
    return apiClient.get(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${membershipId}/usage`)
  }

  // Bulk Operations
  static async bulkAssignMemberships(data: {
    user_ids: number[]
    membership_plan_id: number
    start_date: string
    auto_renew?: boolean
  }): Promise<UserMembership[]> {
    return apiClient.post(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/bulk-assign`, data)
  }

  static async bulkCancelMemberships(data: {
    membership_ids: number[]
    reason?: string
  }): Promise<void> {
    return apiClient.post(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/bulk-cancel`, data)
  }

  // Export/Import
  static async exportMemberships(params?: MembershipSearchParams): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/export`, { params })
  }

  static async importMemberships(file: File): Promise<{
    successful: number
    failed: number
    errors: Array<{ row: number; error: string }>
  }> {
    return apiClient.uploadFile(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/import`, file)
  }

  // Membership Renewals
  static async getExpiringMemberships(days?: number): Promise<UserMembership[]> {
    return apiClient.get(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/expiring`, {
      params: { days: days || 30 }
    })
  }

  static async sendRenewalReminders(membershipIds: number[]): Promise<void> {
    return apiClient.post(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/send-renewal-reminders`, {
      membership_ids: membershipIds
    })
  }
}

export const membershipsService = MembershipsService