import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { paymentsService } from '../api'
import {
  Payment,
  PaymentMethod,
  CreatePaymentRequest,
  ProcessPaymentRequest,
  RefundPaymentRequest,
  PaymentSearchParams,
  PaymentStatistics,
  Invoice,
  CreateInvoiceRequest,
  PaymentIntent,
  Subscription,
  SubscriptionPlan,
  PaginationParams
} from '../types'

interface PaymentState {
  // State
  payments: Payment[]
  paymentMethods: PaymentMethod[]
  invoices: Invoice[]
  subscriptions: Subscription[]
  subscriptionPlans: SubscriptionPlan[]
  currentPayment: Payment | null
  currentPaymentMethod: PaymentMethod | null
  currentInvoice: Invoice | null
  currentSubscription: Subscription | null
  paymentStats: PaymentStatistics | null
  paymentIntent: PaymentIntent | null
  loading: boolean
  error: string | null
  
  // Pagination
  paymentPagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  invoicePagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  subscriptionPagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  
  // Filters
  paymentFilters: PaymentSearchParams
  
  // Actions - Payments
  getPayments: (params?: PaymentSearchParams) => Promise<void>
  getPayment: (id: number) => Promise<void>
  createPayment: (data: CreatePaymentRequest) => Promise<Payment | null>
  processPayment: (data: ProcessPaymentRequest) => Promise<Payment | null>
  refundPayment: (data: RefundPaymentRequest) => Promise<Payment | null>
  cancelPayment: (id: number, reason?: string) => Promise<boolean>
  
  // Actions - Payment Methods
  getPaymentMethods: (userId?: number) => Promise<void>
  getPaymentMethod: (id: number) => Promise<void>
  addPaymentMethod: (data: {
    user_id: number
    type: string
    token: string
    is_default?: boolean
  }) => Promise<PaymentMethod | null>
  updatePaymentMethod: (id: number, data: {
    is_default?: boolean
    is_active?: boolean
  }) => Promise<PaymentMethod | null>
  deletePaymentMethod: (id: number) => Promise<boolean>
  setDefaultPaymentMethod: (id: number) => Promise<boolean>
  
  // Actions - Statistics
  getPaymentStatistics: (params?: {
    start_date?: string
    end_date?: string
    user_id?: number
  }) => Promise<void>
  
  // Actions - Invoices
  getInvoices: (params?: PaginationParams) => Promise<void>
  getInvoice: (id: number) => Promise<void>
  createInvoice: (data: CreateInvoiceRequest) => Promise<Invoice | null>
  sendInvoice: (id: number) => Promise<boolean>
  markInvoiceAsPaid: (id: number, paymentId?: number) => Promise<boolean>
  downloadInvoice: (id: number) => Promise<boolean>
  
  // Actions - Payment Intents
  createPaymentIntent: (data: {
    amount: number
    currency: string
    payment_method_types: string[]
    metadata?: Record<string, any>
  }) => Promise<PaymentIntent | null>
  confirmPaymentIntent: (intentId: string, data?: {
    payment_method?: string
    return_url?: string
  }) => Promise<PaymentIntent | null>
  
  // Actions - Subscriptions
  getSubscriptions: (params?: PaginationParams) => Promise<void>
  getSubscription: (id: number) => Promise<void>
  createSubscription: (data: {
    user_id: number
    plan_id: number
    payment_method_id?: number
    trial_days?: number
  }) => Promise<Subscription | null>
  cancelSubscription: (id: number, data?: {
    cancel_at_period_end?: boolean
    reason?: string
  }) => Promise<boolean>
  reactivateSubscription: (id: number) => Promise<boolean>
  
  // Actions - Subscription Plans
  getSubscriptionPlans: () => Promise<void>
  getSubscriptionPlan: (id: number) => Promise<void>
  
  // Actions - Bulk Operations
  bulkProcessPayments: (paymentIds: number[]) => Promise<any>
  bulkRefundPayments: (data: {
    payment_ids: number[]
    reason: string
    amount?: number
  }) => Promise<any>
  
  // Actions - Export
  exportPayments: (params?: PaymentSearchParams) => Promise<boolean>
  
  // Utility actions
  setPaymentFilters: (filters: Partial<PaymentSearchParams>) => void
  clearFilters: () => void
  setCurrentPayment: (payment: Payment | null) => void
  setCurrentPaymentMethod: (paymentMethod: PaymentMethod | null) => void
  setCurrentInvoice: (invoice: Invoice | null) => void
  setCurrentSubscription: (subscription: Subscription | null) => void
  clearError: () => void
  setLoading: (loading: boolean) => void
}

const initialPaymentFilters: PaymentSearchParams = {
  page: 1,
  limit: 10
}

export const usePaymentStore = create<PaymentState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        payments: [],
        paymentMethods: [],
        invoices: [],
        subscriptions: [],
        subscriptionPlans: [],
        currentPayment: null,
        currentPaymentMethod: null,
        currentInvoice: null,
        currentSubscription: null,
        paymentStats: null,
        paymentIntent: null,
        loading: false,
        error: null,
        
        paymentPagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        invoicePagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        subscriptionPagination: {
          page: 1,
          limit: 10,
          total: 0,
          totalPages: 0
        },
        
        paymentFilters: initialPaymentFilters,

        // Actions - Payments
        getPayments: async (params?: PaymentSearchParams) => {
          set({ loading: true, error: null })
          try {
            const response = await paymentsService.getPayments(params)
            set({
              payments: response.items,
              paymentPagination: {
                page: response.page,
                limit: response.limit,
                total: response.total,
                totalPages: response.pages
              },
              loading: false
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar pagos',
              loading: false 
            })
          }
        },

        getPayment: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const payment = await paymentsService.getPayment(id)
            set({ currentPayment: payment, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar pago',
              loading: false 
            })
          }
        },

        createPayment: async (data: CreatePaymentRequest) => {
          set({ loading: true, error: null })
          try {
            const newPayment = await paymentsService.createPayment(data)
            const { payments } = get()
            set({ 
              payments: [newPayment, ...payments],
              loading: false 
            })
            return newPayment
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear pago',
              loading: false 
            })
            return null
          }
        },

        processPayment: async (data: ProcessPaymentRequest) => {
          set({ loading: true, error: null })
          try {
            const processedPayment = await paymentsService.processPayment(data)
            const { payments, currentPayment } = get()
            set({ 
              payments: payments.map(p => p.id === processedPayment.id ? processedPayment : p),
              currentPayment: currentPayment?.id === processedPayment.id ? processedPayment : currentPayment,
              loading: false 
            })
            return processedPayment
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al procesar pago',
              loading: false 
            })
            return null
          }
        },

        refundPayment: async (data: RefundPaymentRequest) => {
          set({ loading: true, error: null })
          try {
            const refundedPayment = await paymentsService.refundPayment(data)
            const { payments, currentPayment } = get()
            set({ 
              payments: payments.map(p => p.id === refundedPayment.id ? refundedPayment : p),
              currentPayment: currentPayment?.id === refundedPayment.id ? refundedPayment : currentPayment,
              loading: false 
            })
            return refundedPayment
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al reembolsar pago',
              loading: false 
            })
            return null
          }
        },

        cancelPayment: async (id: number, reason?: string) => {
          set({ loading: true, error: null })
          try {
            const cancelledPayment = await paymentsService.cancelPayment(id, reason)
            const { payments, currentPayment } = get()
            set({ 
              payments: payments.map(p => p.id === id ? cancelledPayment : p),
              currentPayment: currentPayment?.id === id ? cancelledPayment : currentPayment,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cancelar pago',
              loading: false 
            })
            return false
          }
        },

        // Actions - Payment Methods
        getPaymentMethods: async (userId?: number) => {
          set({ loading: true, error: null })
          try {
            const response = await paymentsService.getPaymentMethods(userId)
            set({ paymentMethods: response.items, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar métodos de pago',
              loading: false 
            })
          }
        },

        getPaymentMethod: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const paymentMethod = await paymentsService.getPaymentMethod(id)
            set({ currentPaymentMethod: paymentMethod, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar método de pago',
              loading: false 
            })
          }
        },

        addPaymentMethod: async (data: {
          user_id: number
          type: string
          token: string
          is_default?: boolean
        }) => {
          set({ loading: true, error: null })
          try {
            const newPaymentMethod = await paymentsService.addPaymentMethod(data)
            const { paymentMethods } = get()
            set({ 
              paymentMethods: [newPaymentMethod, ...paymentMethods],
              loading: false 
            })
            return newPaymentMethod
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al agregar método de pago',
              loading: false 
            })
            return null
          }
        },

        updatePaymentMethod: async (id: number, data: {
          is_default?: boolean
          is_active?: boolean
        }) => {
          set({ loading: true, error: null })
          try {
            const updatedPaymentMethod = await paymentsService.updatePaymentMethod(id, data)
            const { paymentMethods, currentPaymentMethod } = get()
            set({ 
              paymentMethods: paymentMethods.map(pm => pm.id === id ? updatedPaymentMethod : pm),
              currentPaymentMethod: currentPaymentMethod?.id === id ? updatedPaymentMethod : currentPaymentMethod,
              loading: false 
            })
            return updatedPaymentMethod
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al actualizar método de pago',
              loading: false 
            })
            return null
          }
        },

        deletePaymentMethod: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await paymentsService.deletePaymentMethod(id)
            const { paymentMethods } = get()
            set({ 
              paymentMethods: paymentMethods.filter(pm => pm.id !== id),
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al eliminar método de pago',
              loading: false 
            })
            return false
          }
        },

        setDefaultPaymentMethod: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const updatedPaymentMethod = await paymentsService.setDefaultPaymentMethod(id)
            const { paymentMethods, currentPaymentMethod } = get()
            set({ 
              paymentMethods: paymentMethods.map(pm => ({
                ...pm,
                is_default: pm.id === id
              })),
              currentPaymentMethod: currentPaymentMethod?.id === id ? updatedPaymentMethod : currentPaymentMethod,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al establecer método de pago por defecto',
              loading: false 
            })
            return false
          }
        },

        // Actions - Statistics
        getPaymentStatistics: async (params?: {
          start_date?: string
          end_date?: string
          user_id?: number
        }) => {
          set({ loading: true, error: null })
          try {
            const paymentStats = await paymentsService.getPaymentStatistics(params)
            set({ paymentStats, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar estadísticas de pagos',
              loading: false 
            })
          }
        },

        // Actions - Invoices
        getInvoices: async (params?: PaginationParams) => {
          set({ loading: true, error: null })
          try {
            const response = await paymentsService.getInvoices(params)
            set({
              invoices: response.items,
              invoicePagination: {
                page: response.page,
                limit: response.limit,
                total: response.total,
                totalPages: response.pages
              },
              loading: false
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar facturas',
              loading: false 
            })
          }
        },

        getInvoice: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const invoice = await paymentsService.getInvoice(id)
            set({ currentInvoice: invoice, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar factura',
              loading: false 
            })
          }
        },

        createInvoice: async (data: CreateInvoiceRequest) => {
          set({ loading: true, error: null })
          try {
            const newInvoice = await paymentsService.createInvoice(data)
            const { invoices } = get()
            set({ 
              invoices: [newInvoice, ...invoices],
              loading: false 
            })
            return newInvoice
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear factura',
              loading: false 
            })
            return null
          }
        },

        sendInvoice: async (id: number) => {
          set({ loading: true, error: null })
          try {
            await paymentsService.sendInvoice(id)
            set({ loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al enviar factura',
              loading: false 
            })
            return false
          }
        },

        markInvoiceAsPaid: async (id: number, paymentId?: number) => {
          set({ loading: true, error: null })
          try {
            const updatedInvoice = await paymentsService.markInvoiceAsPaid(id, paymentId)
            const { invoices, currentInvoice } = get()
            set({ 
              invoices: invoices.map(i => i.id === id ? updatedInvoice : i),
              currentInvoice: currentInvoice?.id === id ? updatedInvoice : currentInvoice,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al marcar factura como pagada',
              loading: false 
            })
            return false
          }
        },

        downloadInvoice: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const blob = await paymentsService.downloadInvoice(id)
            // Create download link
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = `invoice-${id}.pdf`
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            window.URL.revokeObjectURL(url)
            set({ loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al descargar factura',
              loading: false 
            })
            return false
          }
        },

        // Actions - Payment Intents
        createPaymentIntent: async (data: {
          amount: number
          currency: string
          payment_method_types: string[]
          metadata?: Record<string, any>
        }) => {
          set({ loading: true, error: null })
          try {
            const paymentIntent = await paymentsService.createPaymentIntent(data)
            set({ paymentIntent, loading: false })
            return paymentIntent
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear intención de pago',
              loading: false 
            })
            return null
          }
        },

        confirmPaymentIntent: async (intentId: string, data?: {
          payment_method?: string
          return_url?: string
        }) => {
          set({ loading: true, error: null })
          try {
            const confirmedIntent = await paymentsService.confirmPaymentIntent(intentId, data)
            set({ paymentIntent: confirmedIntent, loading: false })
            return confirmedIntent
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al confirmar intención de pago',
              loading: false 
            })
            return null
          }
        },

        // Actions - Subscriptions
        getSubscriptions: async (params?: PaginationParams) => {
          set({ loading: true, error: null })
          try {
            const response = await paymentsService.getSubscriptions(params)
            set({
              subscriptions: response.items,
              subscriptionPagination: {
                page: response.page,
                limit: response.limit,
                total: response.total,
                totalPages: response.pages
              },
              loading: false
            })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar suscripciones',
              loading: false 
            })
          }
        },

        getSubscription: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const subscription = await paymentsService.getSubscription(id)
            set({ currentSubscription: subscription, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar suscripción',
              loading: false 
            })
          }
        },

        createSubscription: async (data: {
          user_id: number
          plan_id: number
          payment_method_id?: number
          trial_days?: number
        }) => {
          set({ loading: true, error: null })
          try {
            const newSubscription = await paymentsService.createSubscription(data)
            const { subscriptions } = get()
            set({ 
              subscriptions: [newSubscription, ...subscriptions],
              loading: false 
            })
            return newSubscription
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al crear suscripción',
              loading: false 
            })
            return null
          }
        },

        cancelSubscription: async (id: number, data?: {
          cancel_at_period_end?: boolean
          reason?: string
        }) => {
          set({ loading: true, error: null })
          try {
            const cancelledSubscription = await paymentsService.cancelSubscription(id, data)
            const { subscriptions, currentSubscription } = get()
            set({ 
              subscriptions: subscriptions.map(s => s.id === id ? cancelledSubscription : s),
              currentSubscription: currentSubscription?.id === id ? cancelledSubscription : currentSubscription,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cancelar suscripción',
              loading: false 
            })
            return false
          }
        },

        reactivateSubscription: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const reactivatedSubscription = await paymentsService.reactivateSubscription(id)
            const { subscriptions, currentSubscription } = get()
            set({ 
              subscriptions: subscriptions.map(s => s.id === id ? reactivatedSubscription : s),
              currentSubscription: currentSubscription?.id === id ? reactivatedSubscription : currentSubscription,
              loading: false 
            })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al reactivar suscripción',
              loading: false 
            })
            return false
          }
        },

        // Actions - Subscription Plans
        getSubscriptionPlans: async () => {
          set({ loading: true, error: null })
          try {
            const subscriptionPlans = await paymentsService.getSubscriptionPlans()
            set({ subscriptionPlans, loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar planes de suscripción',
              loading: false 
            })
          }
        },

        getSubscriptionPlan: async (id: number) => {
          set({ loading: true, error: null })
          try {
            const plan = await paymentsService.getSubscriptionPlan(id)
            // Store in subscriptionPlans if not already there
            const { subscriptionPlans } = get()
            const existingPlan = subscriptionPlans.find(p => p.id === id)
            if (!existingPlan) {
              set({ subscriptionPlans: [...subscriptionPlans, plan] })
            }
            set({ loading: false })
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al cargar plan de suscripción',
              loading: false 
            })
          }
        },

        // Actions - Bulk Operations
        bulkProcessPayments: async (paymentIds: number[]) => {
          set({ loading: true, error: null })
          try {
            const result = await paymentsService.bulkProcessPayments(paymentIds)
            // Refresh payments list
            await get().getPayments()
            set({ loading: false })
            return result
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al procesar pagos en lote',
              loading: false 
            })
            return null
          }
        },

        bulkRefundPayments: async (data: {
          payment_ids: number[]
          reason: string
          amount?: number
        }) => {
          set({ loading: true, error: null })
          try {
            const result = await paymentsService.bulkRefundPayments(data)
            // Refresh payments list
            await get().getPayments()
            set({ loading: false })
            return result
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al reembolsar pagos en lote',
              loading: false 
            })
            return null
          }
        },

        // Actions - Export
        exportPayments: async (params?: PaymentSearchParams) => {
          set({ loading: true, error: null })
          try {
            const blob = await paymentsService.exportPayments(params)
            // Create download link
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = `payments-export-${new Date().toISOString().split('T')[0]}.csv`
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            window.URL.revokeObjectURL(url)
            set({ loading: false })
            return true
          } catch (error: any) {
            set({ 
              error: error.message || 'Error al exportar pagos',
              loading: false 
            })
            return false
          }
        },

        // Utility actions
        setPaymentFilters: (filters: Partial<PaymentSearchParams>) => {
          set((state: PaymentState) => ({ 
            paymentFilters: { ...state.paymentFilters, ...filters } 
          }))
        },

        clearFilters: () => {
          set({ paymentFilters: initialPaymentFilters })
        },

        setCurrentPayment: (payment: Payment | null) => {
          set({ currentPayment: payment })
        },

        setCurrentPaymentMethod: (paymentMethod: PaymentMethod | null) => {
          set({ currentPaymentMethod: paymentMethod })
        },

        setCurrentInvoice: (invoice: Invoice | null) => {
          set({ currentInvoice: invoice })
        },

        setCurrentSubscription: (subscription: Subscription | null) => {
          set({ currentSubscription: subscription })
        },

        clearError: () => {
          set({ error: null })
        },

        setLoading: (loading: boolean) => {
          set({ loading })
        }
      }),
      {
        name: 'payment-store',
        partialize: (state: PaymentState) => ({
          paymentFilters: state.paymentFilters
        })
      }
    ),
    {
      name: 'payment-store'
    }
  )
)

export default usePaymentStore