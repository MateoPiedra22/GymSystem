import { apiClient } from '../client'
import { API_ENDPOINTS } from '../config'
import {
  Payment,
  PaymentMethod,
  CreatePaymentRequest,
  ProcessPaymentRequest,
  RefundPaymentRequest,
  PaymentSearchParams,
  PaymentListResponse,
  PaymentMethodListResponse,
  SubscriptionListResponse,
  InvoiceListResponse,
  PaymentStatistics,
  Invoice,
  CreateInvoiceRequest,
  PaymentIntent,
  Subscription,
  SubscriptionPlan,
  PaginationParams
} from '../../types'

export class PaymentsService {
  // Payments
  async getPayments(params?: PaymentSearchParams): Promise<PaymentListResponse> {
    return apiClient.get(API_ENDPOINTS.PAYMENTS.PAYMENTS, { params })
  }

  async getPayment(id: number): Promise<Payment> {
    return apiClient.get(`${API_ENDPOINTS.PAYMENTS.PAYMENTS}/${id}`)
  }

  async createPayment(data: CreatePaymentRequest): Promise<Payment> {
    return apiClient.post(API_ENDPOINTS.PAYMENTS.PAYMENTS, data)
  }

  async processPayment(data: ProcessPaymentRequest): Promise<Payment> {
    return apiClient.post(`${API_ENDPOINTS.PAYMENTS.PAYMENTS}/process`, data)
  }

  async refundPayment(data: RefundPaymentRequest): Promise<Payment> {
    return apiClient.post(`${API_ENDPOINTS.PAYMENTS.PAYMENTS}/refund`, data)
  }

  async cancelPayment(id: number, reason?: string): Promise<Payment> {
    return apiClient.patch(`${API_ENDPOINTS.PAYMENTS.PAYMENTS}/${id}/cancel`, { reason })
  }

  // Payment Methods
  async getPaymentMethods(userId?: number): Promise<PaymentMethodListResponse> {
    return apiClient.get(API_ENDPOINTS.PAYMENTS.PAYMENT_METHODS, {
      params: userId ? { user_id: userId } : undefined
    })
  }

  async getPaymentMethod(id: number): Promise<PaymentMethod> {
    return apiClient.get(`${API_ENDPOINTS.PAYMENTS.PAYMENT_METHODS}/${id}`)
  }

  async addPaymentMethod(data: {
    user_id: number
    type: string
    token: string
    is_default?: boolean
  }): Promise<PaymentMethod> {
    return apiClient.post(API_ENDPOINTS.PAYMENTS.PAYMENT_METHODS, data)
  }

  async updatePaymentMethod(id: number, data: {
    is_default?: boolean
    is_active?: boolean
  }): Promise<PaymentMethod> {
    return apiClient.put(`${API_ENDPOINTS.PAYMENTS.PAYMENT_METHODS}/${id}`, data)
  }

  async deletePaymentMethod(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.PAYMENTS.PAYMENT_METHODS}/${id}`)
  }

  async setDefaultPaymentMethod(id: number): Promise<PaymentMethod> {
    return apiClient.patch(`${API_ENDPOINTS.PAYMENTS.PAYMENT_METHODS}/${id}/set-default`)
  }

  // Payment Statistics
  async getPaymentStatistics(params?: {
    start_date?: string
    end_date?: string
    user_id?: number
  }): Promise<PaymentStatistics> {
    return apiClient.get(API_ENDPOINTS.PAYMENTS.STATISTICS, { params })
  }

  // Invoices
  async getInvoices(params?: PaginationParams): Promise<InvoiceListResponse> {
    return apiClient.get(API_ENDPOINTS.PAYMENTS.INVOICES, { params })
  }

  async getInvoice(id: number): Promise<Invoice> {
    return apiClient.get(`${API_ENDPOINTS.PAYMENTS.INVOICES}/${id}`)
  }

  async createInvoice(data: CreateInvoiceRequest): Promise<Invoice> {
    return apiClient.post(API_ENDPOINTS.PAYMENTS.INVOICES, data)
  }

  async sendInvoice(id: number): Promise<void> {
    return apiClient.post(`${API_ENDPOINTS.PAYMENTS.INVOICES}/${id}/send`)
  }

  async markInvoiceAsPaid(id: number, paymentId?: number): Promise<Invoice> {
    return apiClient.patch(`${API_ENDPOINTS.PAYMENTS.INVOICES}/${id}/mark-paid`, {
      payment_id: paymentId
    })
  }

  async downloadInvoice(id: number): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.PAYMENTS.INVOICES}/${id}/download`)
  }

  // Payment Intents (for Stripe integration)
  async createPaymentIntent(data: {
    amount: number
    currency: string
    payment_method_types: string[]
    metadata?: Record<string, any>
  }): Promise<PaymentIntent> {
    return apiClient.post(`${API_ENDPOINTS.PAYMENTS.PAYMENTS}/create-intent`, data)
  }

  async confirmPaymentIntent(intentId: string, data?: {
    payment_method?: string
    return_url?: string
  }): Promise<PaymentIntent> {
    return apiClient.post(`${API_ENDPOINTS.PAYMENTS.PAYMENTS}/confirm-intent/${intentId}`, data)
  }

  // Subscriptions
  async getSubscriptions(params?: PaginationParams): Promise<SubscriptionListResponse> {
    return apiClient.get(API_ENDPOINTS.PAYMENTS.SUBSCRIPTIONS, { params })
  }

  async getSubscription(id: number): Promise<Subscription> {
    return apiClient.get(`${API_ENDPOINTS.PAYMENTS.SUBSCRIPTIONS}/${id}`)
  }

  async createSubscription(data: {
    user_id: number
    plan_id: number
    payment_method_id?: number
    trial_days?: number
  }): Promise<Subscription> {
    return apiClient.post(API_ENDPOINTS.PAYMENTS.SUBSCRIPTIONS, data)
  }

  async cancelSubscription(id: number, data?: {
    cancel_at_period_end?: boolean
    reason?: string
  }): Promise<Subscription> {
    return apiClient.patch(`${API_ENDPOINTS.PAYMENTS.SUBSCRIPTIONS}/${id}/cancel`, data)
  }

  async reactivateSubscription(id: number): Promise<Subscription> {
    return apiClient.patch(`${API_ENDPOINTS.PAYMENTS.SUBSCRIPTIONS}/${id}/reactivate`)
  }

  // Subscription Plans
  async getSubscriptionPlans(): Promise<SubscriptionPlan[]> {
    return apiClient.get(`${API_ENDPOINTS.PAYMENTS.SUBSCRIPTIONS}/plans`)
  }

  async getSubscriptionPlan(id: number): Promise<SubscriptionPlan> {
    return apiClient.get(`${API_ENDPOINTS.PAYMENTS.SUBSCRIPTIONS}/plans/${id}`)
  }

  // Bulk Operations
  async bulkProcessPayments(paymentIds: number[]): Promise<{
    successful: number
    failed: number
    errors: Array<{ payment_id: number; error: string }>
  }> {
    return apiClient.post(`${API_ENDPOINTS.PAYMENTS.PAYMENTS}/bulk-process`, {
      payment_ids: paymentIds
    })
  }

  async bulkRefundPayments(data: {
    payment_ids: number[]
    reason: string
    amount?: number
  }): Promise<{
    successful: number
    failed: number
    errors: Array<{ payment_id: number; error: string }>
  }> {
    return apiClient.post(`${API_ENDPOINTS.PAYMENTS.PAYMENTS}/bulk-refund`, data)
  }

  // Export/Import
  async exportPayments(params?: PaymentSearchParams): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.PAYMENTS.PAYMENTS}/export`, { params })
  }

  // Reports
  async getPaymentReport(params: {
    start_date: string
    end_date: string
    group_by?: 'day' | 'week' | 'month'
    payment_type?: string
    payment_method?: string
  }): Promise<{
    total_revenue: number
    total_transactions: number
    average_transaction: number
    data: Array<{
      period: string
      revenue: number
      transaction_count: number
    }>
  }> {
    return apiClient.get(`${API_ENDPOINTS.PAYMENTS.PAYMENTS}/report`, { params })
  }

  // Webhooks (for payment provider notifications)
  async handleWebhook(provider: string, data: any): Promise<void> {
    return apiClient.post(`${API_ENDPOINTS.PAYMENTS.PAYMENTS}/webhook/${provider}`, data)
  }
}

export const paymentsService = new PaymentsService()