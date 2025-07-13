/**
 * Hooks para sincronización
 * Proporciona un mecanismo para detectar y sincronizar cambios con el backend
 */
'use client'

import { useState, useEffect } from 'react'
import { api } from '../utils/api'

export type SyncStatus = 'idle' | 'syncing' | 'error' | 'offline'

interface SyncState {
  status: SyncStatus
  lastSynced: Date | null
  pendingChanges: number
  error: string | null
}

export function useSyncStatus() {
  const [state, setState] = useState<SyncState>({
    status: 'idle',
    lastSynced: null,
    pendingChanges: 0,
    error: null,
  })

  // Función para sincronizar cambios
  const syncChanges = async () => {
    if (state.status === 'syncing' || state.pendingChanges === 0) return

    try {
      setState(prev => ({ ...prev, status: 'syncing' }))
      
      // Aquí se implementaría la lógica real de sincronización
      // Por ahora, solo simulamos una llamada a la API
      // await api.syncChanges({ pendingChanges: state.pendingChanges })
      
      // Simular delay de sincronización
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setState({
        status: 'idle',
        lastSynced: new Date(),
        pendingChanges: 0,
        error: null,
      })
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        status: 'error',
        error: error.message || 'Error al sincronizar',
      }))
    }
  }

  // Comprobar conexión y sincronizar periódicamente
  useEffect(() => {
    const checkConnection = async () => {
      try {
        // Intentar obtener el estado de sincronización del servidor
        // const syncStatus = await api.getSyncStatus()
        
        // Si estamos en modo offline y ahora tenemos conexión, actualizamos el estado
        if (state.status === 'offline') {
          setState(prev => ({ ...prev, status: 'idle' }))
        }
      } catch (error) {
        // Si no hay conexión, marcar como offline
        setState(prev => ({ ...prev, status: 'offline' }))
      }
    }

    // Verificar conexión cada 30 segundos
    const connectionInterval = setInterval(checkConnection, 30000)
    
    // Sincronizar cambios pendientes cada 2 minutos si hay conexión
    const syncInterval = setInterval(() => {
      if (state.status !== 'offline' && state.pendingChanges > 0) {
        syncChanges()
      }
    }, 120000)

    // Limpiar intervalos al desmontar
    return () => {
      clearInterval(connectionInterval)
      clearInterval(syncInterval)
    }
  }, [state.status, state.pendingChanges])

  // Añadir un cambio pendiente (para ser llamado cuando se realiza un cambio local)
  const addPendingChange = () => {
    setState(prev => ({
      ...prev,
      pendingChanges: prev.pendingChanges + 1,
    }))
  }

  // Forzar sincronización manual
  const forceSync = () => {
    syncChanges()
  }

  return {
    ...state,
    addPendingChange,
    forceSync,
  }
}
