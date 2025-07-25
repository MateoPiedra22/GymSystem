import { PaginationParams, PaginatedResponse, Status } from './common'

export interface MembershipPlan {
  id: number
  name: string
  description: string
  price: number
  currency: string
  duration_days: number
  features: string[]
  max_classes_per_month?: number
  max_guest_passes?: number
  access_hours: {
    start_time: string
    end_time: string
    days: string[]
  }
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserMembership {
  id: number
  user_id: number
  membership_plan_id: number
  membership_plan: MembershipPlan
  start_date: string
  end_date: string
  status: 'active' | 'expired' | 'cancelled' | 'suspended'
  auto_renew: boolean
  payment_method_id?: number
  classes_used_this_month: number
  guest_passes_used: number
  created_at: string
  updated_at: string
}

export interface CreateMembershipPlanRequest {
  name: string
  description: string
  price: number
  currency: string
  duration_days: number
  features: string[]
  max_classes_per_month?: number
  max_guest_passes?: number
  access_hours: {
    start_time: string
    end_time: string
    days: string[]
  }
}

export interface UpdateMembershipPlanRequest {
  name?: string
  description?: string
  price?: number
  duration_days?: number
  features?: string[]
  max_classes_per_month?: number
  max_guest_passes?: number
  access_hours?: {
    start_time: string
    end_time: string
    days: string[]
  }
  is_active?: boolean
}

export interface AssignMembershipRequest {
  user_id: number
  membership_plan_id: number
  start_date: string
  auto_renew?: boolean
  payment_method_id?: number
}

export interface MembershipSearchParams extends PaginationParams {
  status?: Status
  plan_id?: number
  start_date_from?: string
  start_date_to?: string
  end_date_from?: string
  end_date_to?: string
  auto_renew?: boolean
}

export interface MembershipListResponse extends PaginatedResponse<UserMembership> {}

export interface MembershipPlanListResponse extends PaginatedResponse<MembershipPlan> {}

export interface MembershipStatistics {
  total_memberships: number
  active_memberships: number
  expired_memberships: number
  revenue_this_month: number
  revenue_last_month: number
  popular_plans: Array<{
    plan_name: string
    member_count: number
    revenue: number
  }>
  expiring_soon: number
  renewal_rate: number
}

export interface MembershipUsage {
  membership_id: number
  classes_attended: number
  classes_remaining: number
  guest_passes_used: number
  guest_passes_remaining: number
  last_activity_date?: string
  usage_percentage: number
}