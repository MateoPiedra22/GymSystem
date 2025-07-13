import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

interface OfflineAction {
  id: string;
  type: 'create' | 'update' | 'delete';
  endpoint: string;
  data: any;
  timestamp: Date;
  retries: number;
}

interface OfflineManagerProps {
  onSync?: (actions: OfflineAction[]) => Promise<void>;
  className?: string;
}

export function OfflineManager({ 
  onSync, 
  className = '' 
}: OfflineManagerProps) {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingActions, setPendingActions] = useState<OfflineAction[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSync, setLastSync] = useState<Date | null>(null);

  // Detectar cambios de conectividad
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Cargar acciones pendientes del localStorage
  useEffect(() => {
    const savedActions = localStorage.getItem('offlineActions');
    if (savedActions) {
      try {
        const actions = JSON.parse(savedActions).map((action: any) => ({
          ...action,
          timestamp: new Date(action.timestamp)
        }));
        setPendingActions(actions);
      } catch (error) {
        console.error('Error cargando acciones offline:', error);
      }
    }

    const savedLastSync = localStorage.getItem('lastSync');
    if (savedLastSync) {
      setLastSync(new Date(savedLastSync));
    }
  }, []);

  // Guardar acciones pendientes en localStorage
  useEffect(() => {
    localStorage.setItem('offlineActions', JSON.stringify(pendingActions));
  }, [pendingActions]);

  // Sincronizar automáticamente cuando vuelve la conexión
  useEffect(() => {
    if (isOnline && pendingActions.length > 0) {
      handleSync();
    }
  }, [isOnline, pendingActions.length]);

  const addOfflineAction = useCallback((action: Omit<OfflineAction, 'id' | 'timestamp' | 'retries'>) => {
    const newAction: OfflineAction = {
      ...action,
      id: Date.now().toString(),
      timestamp: new Date(),
      retries: 0
    };

    setPendingActions(prev => [...prev, newAction]);
  }, []);

  const handleSync = useCallback(async () => {
    if (pendingActions.length === 0 || isSyncing) return;

    setIsSyncing(true);
    try {
      if (onSync) {
        await onSync(pendingActions);
      } else {
        // Sync por defecto
        for (const action of pendingActions) {
          try {
            const response = await fetch(action.endpoint, {
              method: action.type === 'create' ? 'POST' : 
                      action.type === 'update' ? 'PUT' : 'DELETE',
              headers: {
                'Content-Type': 'application/json',
              },
              body: action.type !== 'delete' ? JSON.stringify(action.data) : undefined,
            });

            if (!response.ok) {
              throw new Error(`HTTP ${response.status}`);
            }
          } catch (error) {
            console.error(`Error sincronizando acción ${action.id}:`, error);
            // Incrementar contador de reintentos
            setPendingActions(prev => 
              prev.map(a => 
                a.id === action.id 
                  ? { ...a, retries: a.retries + 1 }
                  : a
              )
            );
            return; // Parar si hay error
          }
        }
      }

      // Limpiar acciones exitosas
      setPendingActions([]);
      setLastSync(new Date());
      localStorage.setItem('lastSync', new Date().toISOString());
      
    } catch (error) {
      console.error('Error en sincronización:', error);
    } finally {
      setIsSyncing(false);
    }
  }, [pendingActions, onSync, isSyncing]);

  const clearPendingActions = useCallback(() => {
    setPendingActions([]);
    localStorage.removeItem('offlineActions');
  }, []);

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));

    if (minutes < 1) return 'Ahora';
    if (minutes < 60) return `Hace ${minutes} min`;
    return `Hace ${hours} h`;
  };

  const getActionIcon = (type: OfflineAction['type']) => {
    switch (type) {
      case 'create': return '➕';
      case 'update': return '✏️';
      case 'delete': return '🗑️';
      default: return '📝';
    }
  };

  const getActionLabel = (type: OfflineAction['type']) => {
    switch (type) {
      case 'create': return 'Crear';
      case 'update': return 'Actualizar';
      case 'delete': return 'Eliminar';
      default: return 'Acción';
    }
  };

  return (
    <div className={className}>
      {/* Indicador de estado */}
      <div className="flex items-center space-x-2 mb-4">
        <div className={`w-3 h-3 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`}></div>
        <span className="text-sm font-medium">
          {isOnline ? 'En línea' : 'Sin conexión'}
        </span>
        
        {pendingActions.length > 0 && (
          <Badge variant="warning">
            {pendingActions.length} pendiente{pendingActions.length > 1 ? 's' : ''}
          </Badge>
        )}
      </div>

      {/* Acciones pendientes */}
      {pendingActions.length > 0 && (
        <div className="space-y-2 mb-4">
          <h4 className="text-sm font-medium text-gray-700">Acciones pendientes:</h4>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {pendingActions.slice(0, 5).map((action) => (
              <div
                key={action.id}
                className="flex items-center justify-between p-2 bg-gray-50 rounded text-xs"
              >
                <div className="flex items-center space-x-2">
                  <span>{getActionIcon(action.type)}</span>
                  <span>{getActionLabel(action.type)}</span>
                  <span className="text-gray-500">
                    {formatTime(action.timestamp)}
                  </span>
                </div>
                {action.retries > 0 && (
                  <Badge variant="destructive" className="text-xs">
                    {action.retries} reintento{action.retries > 1 ? 's' : ''}
                  </Badge>
                )}
              </div>
            ))}
            {pendingActions.length > 5 && (
              <div className="text-xs text-gray-500 text-center">
                +{pendingActions.length - 5} más...
              </div>
            )}
          </div>
        </div>
      )}

      {/* Botones de acción */}
      <div className="flex space-x-2">
        {isOnline && pendingActions.length > 0 && (
          <Button
            onClick={handleSync}
            loading={isSyncing}
            size="sm"
            className="flex-1"
          >
            {isSyncing ? 'Sincronizando...' : 'Sincronizar'}
          </Button>
        )}
        
        {pendingActions.length > 0 && (
          <Button
            variant="outline"
            onClick={clearPendingActions}
            size="sm"
          >
            Limpiar
          </Button>
        )}
      </div>

      {/* Última sincronización */}
      {lastSync && (
        <div className="mt-2 text-xs text-gray-500">
          Última sincronización: {formatTime(lastSync)}
        </div>
      )}
    </div>
  );
} 