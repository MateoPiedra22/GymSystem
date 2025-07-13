/**
 * Componente SyncStatus
 * Muestra el estado de sincronización con el sistema
 */
'use client'

import React from 'react'
import { Cloud, CloudOff, RefreshCw } from 'lucide-react'
import { useState, useEffect } from 'react'

export function SyncStatus() {
  // Estado de sincronización
  const [status, setStatus] = useState<'online' | 'offline' | 'syncing'>('online')
  const [lastSync, setLastSync] = useState<string>('')
  const [pendingChanges, setPendingChanges] = useState<number>(0)

  // Simulación de cambio de estado para demostración
  useEffect(() => {
    // En una implementación real, esto vendría de un servicio de sincronización
    const timer = setInterval(() => {
      // Simular cambios de estado ocasionales
      const random = Math.random()
      if (random < 0.05) {
        setStatus('syncing')
        setTimeout(() => {
          setStatus('online')
          setLastSync(new Date().toLocaleTimeString())
        }, 2000)
      } else if (random > 0.95) {
        setStatus('offline')
        setPendingChanges(Math.floor(Math.random() * 10) + 1)
      }
    }, 5000)

    // Limpieza
    return () => clearInterval(timer)
  }, [])

  // Colores según el estado
  const statusColors = {
    online: 'text-gym-success',
    offline: 'text-gym-danger',
    syncing: 'text-gym-warning animate-pulse',
  }

  // Textos según el estado
  const statusText = {
    online: 'Sincronizado',
    offline: 'Sin conexión',
    syncing: 'Sincronizando...',
  }

  // Iconos según el estado
  const StatusIcon = status === 'online' 
    ? Cloud 
    : status === 'offline' 
      ? CloudOff 
      : RefreshCw

  return (
    <div className="flex items-center space-x-1 px-2 py-1 rounded-md border">
      <StatusIcon
        size={16}
        className={statusColors[status]}
      />
      <span className={`text-xs ${statusColors[status]}`}>
        {statusText[status]}
      </span>
      
      {status === 'offline' && pendingChanges > 0 && (
        <span className="text-xs bg-gym-danger text-white rounded-full px-1.5">
          {pendingChanges}
        </span>
      )}
    </div>
  )
}
