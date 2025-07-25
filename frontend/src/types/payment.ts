import { PaginationParams, PaginatedResponse } from './common'

export interface Payment {
  id: number
  user_id: number
  amount: number
  currency: string
  payment_method: 'credit_card' | 'debit_card' | 'cash' | 'bank_transfer' | 'paypal' | 'stripe'
  payment_type: 'membership' | 'class' | 'personal_training' | 'product' | 'fee' | 'other'
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled' | 'refunded'
  description: string
  transaction_id?: string
  reference_id?: string
  metadata?: Record<string, any>
  payment_date: string
  due_date?: string
  created_at: string
  updated_at: string
}

export interface PaymentMethod {
  id: number
  user_id: number
  type: 'credit_card' | 'debit_card' | 'bank_account' | 'paypal'
  provider: 'stripe' | 'paypal' | 'manual'
  last_four: string
  brand?: string
  expiry_month?: number
  expiry_year?: number
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreatePaymentRequest {
  user_id: number
  amount: number
  currency: string
  payment_method: string
  payment_type: string
  description: string
  reference_id?: string
  due_date?: string
  metadata?: Record<string, any>
}

export interface ProcessPaymentRequest {
  payment_id: number
  payment_method_id?: number
  payment_token?: string
  confirm_payment?: boolean
}

export interface RefundPaymentRequest {
  payment_id: number
  amount?: number
  reason: string
  notify_user?: boolean
}

export interface PaymentSearchParams extends PaginationParams {
  user_id?: number
  status?: string
  payment_method?: string
  payment_type?: string
  amount_min?: number
  amount_max?: number
  payment_date_from?: string
  payment_date_to?: string
  due_date_from?: string
  due_date_to?: string
}

export interface PaymentListResponse extends PaginatedResponse<Payment> {}

export interface PaymentMethodListResponse extends PaginatedResponse<PaymentMethod> {}

export interface SubscriptionListResponse extends PaginatedResponse<Subscription> {}

export interface InvoiceListResponse extends PaginatedResponse<Invoice> {}

export interface PaymentStatistics {
  total_revenue: number
  revenue_this_month: number
  revenue_last_month: number
  pending_payments: number
  failed_payments: number
  refunded_amount: number
  payment_methods_breakdown: Array<{
    method: string
    count: number
    total_amount: number
    percentage: number
  }>
  payment_types_breakdown: Array<{
    type: string
    count: number
    total_amount: number
    percentage: number
  }>
  monthly_revenue_trend: Array<{
    month: string
    revenue: number
    payment_count: number
  }>
}

export interface Invoice {
  id: number
  payment_id: number
  invoice_number: string
  user_id: number
  amount: number
  currency: string
  tax_amount?: number
  discount_amount?: number
  total_amount: number
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled'
  issue_date: string
  due_date: string
  paid_date?: string
  items: InvoiceItem[]
  notes?: string
  created_at: string
  updated_at: string
}

export interface InvoiceItem {
  id: number
  description: string
  quantity: number
  unit_price: number
  total_price: number
  tax_rate?: number
  discount_rate?: number
}

export interface CreateInvoiceRequest {
  user_id: number
  items: Omit<InvoiceItem, 'id'>[]
  due_date: string
  tax_rate?: number
  discount_amount?: number
  notes?: string
  send_to_user?: boolean
}

export interface PaymentIntent {
  id: string
  amount: number
  currency: string
  status: 'requires_payment_method' | 'requires_confirmation' | 'requires_action' | 'processing' | 'succeeded' | 'cancelled'
  client_secret: string
  payment_method_types: string[]
  metadata?: Record<string, any>
  created_at: string
}

export interface SubscriptionPlan {
  id: number
  name: string
  description: string
  amount: number
  currency: string
  interval: 'day' | 'week' | 'month' | 'year'
  interval_count: number
  trial_period_days?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Subscription {
  id: number
  user_id: number
  plan_id: number
  plan: SubscriptionPlan
  status: 'active' | 'past_due' | 'cancelled' | 'unpaid' | 'trialing'
  current_period_start: string
  current_period_end: string
  trial_start?: string
  trial_end?: string
  cancelled_at?: string
  ended_at?: string
  payment_method_id?: number
  created_at: string
  updated_at: string
}