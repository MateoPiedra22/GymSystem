'use client'

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { 
  CheckCircle, 
  AlertCircle, 
  AlertTriangle, 
  Info, 
  X, 
  Loader2 
} from 'lucide-react'
import { Button } from './ui/Button'

// Tipos de toast
export type ToastType = 'success' | 'error' | 'warning' | 'info' | 'loading'

// Interfaz para un toast
export interface Toast {
  id: string
  type: ToastType
  title: string
  message?: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
  onDismiss?: () => void
}

// Contexto para el sistema de toasts
interface ToastContextType {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => string
  removeToast: (id: string) => void
  clearToasts: () => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

// Hook para usar el contexto de toasts
export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

// Proveedor del contexto
interface ToastProviderProps {
  children: React.ReactNode
  maxToasts?: number
}

export function ToastProvider({ children, maxToasts = 5 }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newToast: Toast = {
      id,
      duration: 5000,
      ...toast
    }

    setToasts(prev => {
      const updated = [newToast, ...prev]
      return updated.slice(0, maxToasts)
    })

    return id
  }, [maxToasts])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }, [])

  const clearToasts = useCallback(() => {
    setToasts([])
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, clearToasts }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  )
}

// Contenedor de toasts
function ToastContainer() {
  const { toasts, removeToast } = useToast()

  return createPortal(
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm w-full">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
      ))}
    </div>,
    document.body
  )
}

// Componente individual de toast
interface ToastItemProps {
  toast: Toast
  onRemove: (id: string) => void
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [isLeaving, setIsLeaving] = useState(false)

  useEffect(() => {
    // Animación de entrada
    const enterTimer = setTimeout(() => setIsVisible(true), 100)

    // Auto-dismiss si no es loading
    if (toast.type !== 'loading' && toast.duration !== 0) {
      const dismissTimer = setTimeout(() => {
        handleDismiss()
      }, toast.duration || 5000)

      return () => {
        clearTimeout(enterTimer)
        clearTimeout(dismissTimer)
      }
    }

    return () => clearTimeout(enterTimer)
  }, [toast.duration, toast.type])

  const handleDismiss = () => {
    setIsLeaving(true)
    setTimeout(() => {
      onRemove(toast.id)
      toast.onDismiss?.()
    }, 300)
  }

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-600" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />
      case 'loading':
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
      default:
        return <Info className="w-5 h-5 text-blue-600" />
    }
  }

  const getStyles = () => {
    const baseStyles = `
      transform transition-all duration-300 ease-in-out
      ${isVisible && !isLeaving ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
    `

    switch (toast.type) {
      case 'success':
        return `${baseStyles} bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800`
      case 'error':
        return `${baseStyles} bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800`
      case 'warning':
        return `${baseStyles} bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800`
      case 'loading':
        return `${baseStyles} bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800`
      default:
        return `${baseStyles} bg-gray-50 border-gray-200 dark:bg-gray-900/20 dark:border-gray-800`
    }
  }

  return (
    <div className={`${getStyles()} border rounded-lg shadow-lg p-4 backdrop-blur-sm`}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 mt-0.5">
          {getIcon()}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {toast.title}
          </div>
          {toast.message && (
            <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              {toast.message}
            </div>
          )}
          {toast.action && (
            <div className="mt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={toast.action.onClick}
                className="text-xs"
              >
                {toast.action.label}
              </Button>
            </div>
          )}
        </div>

        {toast.type !== 'loading' && (
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 ml-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}

// Hook de conveniencia para crear toasts rápidamente
export function useToastActions() {
  const { addToast } = useToast()

  const success = useCallback((title: string, message?: string) => {
    return addToast({ type: 'success', title, message })
  }, [addToast])

  const error = useCallback((title: string, message?: string) => {
    return addToast({ type: 'error', title, message })
  }, [addToast])

  const warning = useCallback((title: string, message?: string) => {
    return addToast({ type: 'warning', title, message })
  }, [addToast])

  const info = useCallback((title: string, message?: string) => {
    return addToast({ type: 'info', title, message })
  }, [addToast])

  const loading = useCallback((title: string, message?: string) => {
    return addToast({ type: 'loading', title, message, duration: 0 })
  }, [addToast])

  return { success, error, warning, info, loading }
} 