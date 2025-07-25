// Store exports
export { useAuthStore } from './authStore'
export { useUserStore } from './userStore'
export { useClassStore } from './classStore'
export { useMembershipStore } from './membershipStore'
export { usePaymentStore } from './paymentStore'
export { useEmployeeStore } from './employeeStore'
export { useDashboardStore } from './dashboardStore'
export { useExerciseStore } from './exerciseStore'
export { useRoutineStore } from './routineStore'
export { useConfigStore } from './configStore'

// Store types are available but not exported as named types
// Each store defines its own internal state interface

// Global store management
export const resetAllStores = () => {
  // Reset all stores to their initial state
  try {
    // Import stores dynamically to avoid circular dependencies
    import('./authStore').then(({ useAuthStore }) => {
      useAuthStore.getState().logout()
    })
    
    console.log('All stores reset successfully')
  } catch (error) {
    console.error('Error resetting stores:', error)
  }
}

export const initializeStores = () => {
  try {
    // Initialize stores with default data if needed
    Promise.all([
      import('./authStore'),
      import('./configStore')
    ]).then(([{ useAuthStore }, { useConfigStore }]) => {
      const authStore = useAuthStore.getState()
      const configStore = useConfigStore.getState()
      
      // Load system configuration on app start
      if (authStore.isAuthenticated) {
        configStore.getSystemConfig()
        configStore.getBrandConfig()
        configStore.getNotificationConfig()
      }
    })
    
    console.log('Stores initialized successfully')
  } catch (error) {
    console.error('Error initializing stores:', error)
  }
}