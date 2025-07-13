'use client'

import React, { useState, useEffect } from 'react'
import { Wifi, WifiOff, AlertTriangle } from 'lucide-react'
import { Badge } from './ui/Badge'

interface OfflineIndicatorProps {
  showBadge?: boolean
  showBanner?: boolean
  onStatusChange?: (isOnline: boolean) => void
}

export function OfflineIndicator({ 
  showBadge = true, 
  showBanner = true,
  onStatusChange 
}: OfflineIndicatorProps) {
  const [isOnline, setIsOnline] = useState(true)
  const [showBannerState, setShowBannerState] = useState(false)

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      onStatusChange?.(true)
      // Mostrar banner de reconexión brevemente
      if (showBanner) {
        setShowBannerState(true)
        setTimeout(() => setShowBannerState(false), 3000)
      }
    }

    const handleOffline = () => {
      setIsOnline(false)
      onStatusChange?.(false)
      if (showBanner) {
        setShowBannerState(true)
      }
    }

    // Verificar estado inicial
    setIsOnline(navigator.onLine)

    // Event listeners
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [showBanner, onStatusChange])

  // Solo mostrar si hay cambios de estado
  if (isOnline && !showBannerState) {
    return null
  }

  return (
    <>
      {/* Badge pequeño */}
      {showBadge && !isOnline && (
        <div className="fixed top-4 left-4 z-40">
          <Badge variant="destructive" className="flex items-center space-x-1">
            <WifiOff className="w-3 h-3" />
            <span className="text-xs">Sin conexión</span>
          </Badge>
        </div>
      )}

      {/* Banner de estado offline */}
      {showBanner && showBannerState && !isOnline && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-red-600 text-white px-4 py-2 shadow-lg">
          <div className="flex items-center justify-center space-x-2 text-sm">
            <WifiOff className="w-4 h-4" />
            <span>Sin conexión a internet. Algunas funciones pueden no estar disponibles.</span>
          </div>
        </div>
      )}

      {/* Banner de reconexión */}
      {showBanner && showBannerState && isOnline && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-green-600 text-white px-4 py-2 shadow-lg animate-in slide-in-from-top duration-300">
          <div className="flex items-center justify-center space-x-2 text-sm">
            <Wifi className="w-4 h-4" />
            <span>Conexión restaurada</span>
          </div>
        </div>
      )}
    </>
  )
}

// Hook para usar el estado offline en otros componentes
export function useOfflineStatus() {
  const [isOnline, setIsOnline] = useState(true)
  const [lastOnline, setLastOnline] = useState<Date>(new Date())

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      setLastOnline(new Date())
    }

    const handleOffline = () => {
      setIsOnline(false)
    }

    setIsOnline(navigator.onLine)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return { isOnline, lastOnline }
}

// Componente para mostrar información detallada del estado de conexión
interface ConnectionStatusProps {
  className?: string
}

export function ConnectionStatus({ className = '' }: ConnectionStatusProps) {
  const { isOnline, lastOnline } = useOfflineStatus()

  if (isOnline) {
    return (
      <div className={`flex items-center space-x-2 text-green-600 dark:text-green-400 ${className}`}>
        <Wifi className="w-4 h-4" />
        <span className="text-sm">Conectado</span>
      </div>
    )
  }

  const timeOffline = new Date().getTime() - lastOnline.getTime()
  const minutesOffline = Math.floor(timeOffline / (1000 * 60))

  return (
    <div className={`flex items-center space-x-2 text-red-600 dark:text-red-400 ${className}`}>
      <WifiOff className="w-4 h-4" />
      <div className="text-sm">
        <span>Sin conexión</span>
        {minutesOffline > 0 && (
          <span className="ml-1 text-xs opacity-75">
            ({minutesOffline}m)
          </span>
        )}
      </div>
    </div>
  )
}

// Componente para mostrar advertencias cuando está offline
interface OfflineWarningProps {
  message?: string
  showIcon?: boolean
}

export function OfflineWarning({ 
  message = "Estás sin conexión. Los cambios se guardarán cuando se restaure la conexión.",
  showIcon = true 
}: OfflineWarningProps) {
  const { isOnline } = useOfflineStatus()

  if (isOnline) return null

  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
      <div className="flex items-start space-x-2">
        {showIcon && (
          <AlertTriangle className="w-4 h-4 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
        )}
        <div className="text-sm text-yellow-800 dark:text-yellow-200">
          {message}
        </div>
      </div>
    </div>
  )
} 