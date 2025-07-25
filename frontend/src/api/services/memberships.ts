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
  async getMembershipPlans(params?: PaginationParams): Promise<MembershipPlanListResponse> {
    return apiClient.get(API_ENDPOINTS.MEMBERSHIPS.PLANS, { params })
  }

  async getMembershipPlan(id: number): Promise<MembershipPlan> {
    return apiClient.get(`${API_ENDPOINTS.MEMBERSHIPS.PLANS}/${id}`)
  }

  async createMembershipPlan(data: CreateMembershipPlanRequest): Promise<MembershipPlan> {
    return apiClient.post(API_ENDPOINTS.MEMBERSHIPS.PLANS, data)
  }

  async updateMembershipPlan(id: number, data: UpdateMembershipPlanRequest): Promise<MembershipPlan> {
    return apiClient.put(`${API_ENDPOINTS.MEMBERSHIPS.PLANS}/${id}`, data)
  }

  async deleteMembershipPlan(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.MEMBERSHIPS.PLANS}/${id}`)
  }

  async toggleMembershipPlanStatus(id: number): Promise<MembershipPlan> {
    return apiClient.patch(`${API_ENDPOINTS.MEMBERSHIPS.PLANS}/${id}/toggle-status`)
  }

  // User Memberships
  async getUserMemberships(params?: MembershipSearchParams): Promise<MembershipListResponse> {
    return apiClient.get(API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS, { params })
  }

  async getUserMembership(id: number): Promise<UserMembership> {
    return apiClient.get(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${id}`)
  }

  async assignMembership(data: AssignMembershipRequest): Promise<UserMembership> {
    return apiClient.post(API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS, data)
  }

  async cancelMembership(id: number, reason?: string): Promise<UserMembership> {
    return apiClient.patch(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${id}/cancel`, { reason })
  }

  async suspendMembership(id: number, reason?: string): Promise<UserMembership> {
    return apiClient.patch(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${id}/suspend`, { reason })
  }

  async reactivateMembership(id: number): Promise<UserMembership> {
    return apiClient.patch(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${id}/reactivate`)
  }

  async renewMembership(id: number): Promise<UserMembership> {
    return apiClient.post(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${id}/renew`)
  }

  // Membership Statistics
  async getMembershipStatistics(): Promise<MembershipStatistics> {
    return apiClient.get(API_ENDPOINTS.MEMBERSHIPS.STATISTICS)
  }

  async getMembershipUsage(membershipId: number): Promise<MembershipUsage> {
    return apiClient.get(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/${membershipId}/usage`)
  }

  // Bulk Operations
  async bulkAssignMemberships(data: {
    user_ids: number[]
    membership_plan_id: number
    start_date: string
    auto_renew?: boolean
  }): Promise<UserMembership[]> {
    return apiClient.post(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/bulk-assign`, data)
  }

  async bulkCancelMemberships(data: {
    membership_ids: number[]
    reason?: string
  }): Promise<void> {
    return apiClient.post(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/bulk-cancel`, data)
  }

  // Export/Import
  async exportMemberships(params?: MembershipSearchParams): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/export`, { params })
  }

  async importMemberships(file: File): Promise<{
    successful: number
    failed: number
    errors: Array<{ row: number; error: string }>
  }> {
    return apiClient.uploadFile(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/import`, file)
  }

  // Membership Renewals
  async getExpiringMemberships(days?: number): Promise<UserMembership[]> {
    return apiClient.get(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/expiring`, {
      params: { days: days || 30 }
    })
  }

  async sendRenewalReminders(membershipIds: number[]): Promise<void> {
    return apiClient.post(`${API_ENDPOINTS.MEMBERSHIPS.USER_MEMBERSHIPS}/send-renewal-reminders`, {
      membership_ids: membershipIds
    })
  }
}

export const membershipsService = new MembershipsService()