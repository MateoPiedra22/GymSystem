import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { ConfigService } from '../api/services/config'
import type {
  SystemConfig,
  BrandConfig,
  NotificationConfig,
  ConfigUpdateRequest,
  BrandConfigUpdateRequest,
  NotificationConfigUpdateRequest,
  ConfigSearchParams,
  ConfigStatistics,
  ConfigValidation,
  ConfigExportData,
  ConfigImportRequest,
  ConfigImportResult
} from '../types/config'

interface ConfigState {
  // System Configuration
  systemConfig: SystemConfig | null
  brandConfig: BrandConfig | null
  notificationConfig: NotificationConfig | null
  
  // Statistics
  statistics: ConfigStatistics | null
  
  // Validation
  validation: ConfigValidation | null
  
  // UI State
  loading: boolean
  error: string | null
  
  // Search and Filters
  searchParams: ConfigSearchParams
  
  // Actions
  // System Config Actions
  getSystemConfig: () => Promise<void>
  updateSystemConfig: (data: ConfigUpdateRequest) => Promise<void>
  resetSystemConfig: () => Promise<void>
  
  // Brand Config Actions
  getBrandConfig: () => Promise<void>
  updateBrandConfig: (data: BrandConfigUpdateRequest) => Promise<void>
  uploadLogo: (file: File) => Promise<string>
  uploadFavicon: (file: File) => Promise<string>
  
  // Notification Config Actions
  getNotificationConfig: () => Promise<void>
  updateNotificationConfig: (data: NotificationConfigUpdateRequest) => Promise<void>
  testEmailConfig: (email: string) => Promise<boolean>
  testSmsConfig: (phone: string) => Promise<boolean>
  
  // Statistics Actions
  getConfigStatistics: () => Promise<void>
  
  // Validation Actions
  validateConfig: () => Promise<void>
  
  // Import/Export Actions
  exportConfig: () => Promise<ConfigExportData>
  importConfig: (data: ConfigImportRequest) => Promise<ConfigImportResult>
  
  // Utility Actions
  setSearchParams: (params: Partial<ConfigSearchParams>) => void
  clearSearchParams: () => void
  clearError: () => void
  setLoading: (loading: boolean) => void
}

export const useConfigStore = create<ConfigState>()(persist(
  (set, get) => ({
    // Initial State
    systemConfig: null,
    brandConfig: null,
    notificationConfig: null,
    statistics: null,
    validation: null,
    loading: false,
    error: null,
    searchParams: {},
    
    // System Config Actions
    getSystemConfig: async () => {
      try {
        set({ loading: true, error: null })
        const response = await ConfigService.getConfig()
        set({ systemConfig: response.data, loading: false })
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al obtener la configuración del sistema',
          loading: false 
        })
      }
    },
    
    updateSystemConfig: async (data: ConfigUpdateRequest) => {
      try {
        set({ loading: true, error: null })
        const response = await ConfigService.updateConfig(data)
        set({ systemConfig: response.data, loading: false })
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al actualizar la configuración del sistema',
          loading: false 
        })
        throw error
      }
    },
    
    resetSystemConfig: async () => {
      try {
        set({ loading: true, error: null })
        const response = await ConfigService.resetConfig()
        set({ systemConfig: response.data, loading: false })
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al restablecer la configuración',
          loading: false 
        })
        throw error
      }
    },
    
    // Brand Config Actions
    getBrandConfig: async () => {
      try {
        set({ loading: true, error: null })
        const response = await ConfigService.getBrandConfig()
        set({ brandConfig: response.data, loading: false })
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al obtener la configuración de marca',
          loading: false 
        })
      }
    },
    
    updateBrandConfig: async (data: BrandConfigUpdateRequest) => {
      try {
        set({ loading: true, error: null })
        const response = await ConfigService.updateBrandConfig(data)
        set({ brandConfig: response.data, loading: false })
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al actualizar la configuración de marca',
          loading: false 
        })
        throw error
      }
    },
    
    uploadLogo: async (file: File) => {
      try {
        set({ loading: true, error: null })
        const response = await ConfigService.uploadLogo(file)
        
        // Update brand config with new logo URL
        const { brandConfig } = get()
        if (brandConfig) {
          set({ 
            brandConfig: { ...brandConfig, logoUrl: response.data.url },
            loading: false 
          })
        }
        
        return response.data.url
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al subir el logo',
          loading: false 
        })
        throw error
      }
    },
    
    uploadFavicon: async (file: File) => {
      try {
        set({ loading: true, error: null })
        const response = await ConfigService.uploadFavicon(file)
        
        // Update brand config with new favicon URL
        const { brandConfig } = get()
        if (brandConfig) {
          set({ 
            brandConfig: { ...brandConfig, faviconUrl: response.data.url },
            loading: false 
          })
        }
        
        return response.data.url
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al subir el favicon',
          loading: false 
        })
        throw error
      }
    },
    
    // Notification Config Actions
    getNotificationConfig: async () => {
      try {
        set({ loading: true, error: null })
        const response = await ConfigService.getNotificationConfig()
        set({ notificationConfig: response.data, loading: false })
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al obtener la configuración de notificaciones',
          loading: false 
        })
      }
    },
    
    updateNotificationConfig: async (data: NotificationConfigUpdateRequest) => {
      try {
        set({ loading: true, error: null })
        const response = await ConfigService.updateNotificationConfig(data)
        set({ notificationConfig: response.data, loading: false })
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al actualizar la configuración de notificaciones',
          loading: false 
        })
        throw error
      }
    },
    
    testEmailConfig: async (email: string) => {
      try {
        set({ loading: true, error: null })
        const response = await ConfigService.testEmailConfig(email)
        set({ loading: false })
        return response.data.success
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al probar la configuración de email',
          loading: false 
        })
        return false
      }
    },
    
    testSmsConfig: async (phone: string) => {
      try {
        set({ loading: true, error: null })
        const response = await ConfigService.testSmsConfig(phone)
        set({ loading: false })
        return response.data.success
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al probar la configuración de SMS',
          loading: false 
        })
        return false
      }
    },
    
    // Statistics Actions
    getConfigStatistics: async () => {
      try {
        set({ loading: true, error: null })
        // This would be implemented when the backend provides config statistics
        // For now, we'll calculate basic statistics from existing data
        const { systemConfig } = get()
        
        if (systemConfig) {
          const activeIntegrations = Object.values(systemConfig.integrations || {}).filter(
            (integration: any) => integration?.isActive
          ).length
          
          const enabledFeatures = Object.values(systemConfig.features || {}).filter(
            (feature) => feature === true
          ).length
          
          const statistics: ConfigStatistics = {
            totalConfigurations: 1, // Only counting systemConfig for now
            activeIntegrations,
            enabledFeatures,
            lastUpdated: systemConfig.updatedAt,
            systemHealth: 'healthy'
          }
          
          set({ statistics, loading: false })
        } else {
          set({ loading: false })
        }
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al obtener las estadísticas de configuración',
          loading: false 
        })
      }
    },
    
    // Validation Actions
    validateConfig: async () => {
      try {
        set({ loading: true, error: null })
        // This would be implemented when the backend provides config validation
        // For now, we'll do basic client-side validation
        const { systemConfig } = get()
        
        const errors: any[] = []
        const warnings: any[] = []
        
        // Basic validation logic
        if (systemConfig) {
          if (!systemConfig.gymName) {
            errors.push({ field: 'gymName', message: 'El nombre del gimnasio es requerido', code: 'REQUIRED' })
          }
          if (!systemConfig.email) {
            errors.push({ field: 'email', message: 'El email es requerido', code: 'REQUIRED' })
          }
        }
        
        const validation: ConfigValidation = {
          isValid: errors.length === 0,
          errors,
          warnings
        }
        
        set({ validation, loading: false })
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al validar la configuración',
          loading: false 
        })
      }
    },
    
    // Import/Export Actions
    exportConfig: async () => {
      try {
        set({ loading: true, error: null })
        const { systemConfig } = get()
        
        if (!systemConfig) {
          throw new Error('No se pueden exportar configuraciones incompletas')
        }
        
        const exportData: ConfigExportData = {
          systemConfig,
          brandConfig: {
            id: 'default',
            primaryColor: '#3b82f6',
            secondaryColor: '#64748b',
            accentColor: '#10b981',
            backgroundColor: '#ffffff',
            textColor: '#1f2937',
            fontFamily: 'Inter, sans-serif',
            borderRadius: '8px',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          },
          notificationConfig: {
            id: 'default',
            emailNotifications: {
              enabled: true,
              welcomeEmail: true,
              membershipExpiry: true,
              paymentReminder: true,
              classReminder: true,
              classConfirmation: true,
              classCancellation: true,
              promotionalEmails: false,
              newsletterEmails: false,
              systemAlerts: true
            },
            smsNotifications: {
              enabled: false,
              membershipExpiry: false,
              paymentReminder: false,
              classReminder: false,
              classConfirmation: false,
              classCancellation: false,
              emergencyAlerts: true
            },
            pushNotifications: {
              enabled: false,
              classReminder: false,
              paymentReminder: false,
              promotionalOffers: false,
              systemUpdates: true
            },
            inAppNotifications: {
              enabled: true,
              realTimeUpdates: true,
              systemMessages: true,
              userMessages: true,
              adminAlerts: true
            },
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          },
          exportedAt: new Date().toISOString(),
          version: '1.0.0'
        }
        
        set({ loading: false })
        return exportData
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al exportar la configuración',
          loading: false 
        })
        throw error
      }
    },
    
    importConfig: async (data: ConfigImportRequest) => {
      try {
        set({ loading: true, error: null })
        
        // This would be implemented when the backend provides config import
        // For now, we'll simulate the import process
        const result: ConfigImportResult = {
          success: true,
          imported: 1, // only system config for now
          skipped: 0,
          errors: [],
          warnings: []
        }
        
        if (data.overwrite) {
          set({
            systemConfig: data.data.systemConfig,
            loading: false
          })
        }
        
        return result
      } catch (error: any) {
        set({ 
          error: error.response?.data?.message || 'Error al importar la configuración',
          loading: false 
        })
        throw error
      }
    },
    
    // Utility Actions
    setSearchParams: (params: Partial<ConfigSearchParams>) => {
      set(state => ({
        searchParams: { ...state.searchParams, ...params }
      }))
    },
    
    clearSearchParams: () => {
      set({ searchParams: {} })
    },
    
    clearError: () => {
      set({ error: null })
    },
    
    setLoading: (loading: boolean) => {
      set({ loading })
    }
  }),
  {
    name: 'config-store',
    partialize: (state) => ({
      systemConfig: state.systemConfig,
      brandConfig: state.brandConfig,
      notificationConfig: state.notificationConfig,
      searchParams: state.searchParams
    })
  }
))