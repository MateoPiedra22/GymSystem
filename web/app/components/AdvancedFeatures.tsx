'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { LoadingSpinner } from './ui/LoadingSpinner';
import { useToast, useToastActions } from './Toast';

// Sistema de notificaciones push
interface NotificationData {
  id: string;
  title: string;
  body: string;
  icon?: string;
  badge?: string;
  tag?: string;
  data?: any;
  requireInteraction?: boolean;
  silent?: boolean;
  actions?: Array<{
    action: string;
    title: string;
    icon?: string;
  }>;
}

export const usePushNotifications = () => {
  const [isSupported, setIsSupported] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);
  const { success, error, warning, info } = useToastActions();

  useEffect(() => {
    setIsSupported('Notification' in window && 'serviceWorker' in navigator);
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }
  }, []);

  const requestPermission = useCallback(async () => {
    if (!isSupported) {
      error('Las notificaciones push no están soportadas en este navegador');
      return false;
    }

    try {
      const result = await Notification.requestPermission();
      setPermission(result);
      
      if (result === 'granted') {
        success('Notificaciones push habilitadas');
        return true;
      } else {
        warning('Permiso de notificaciones denegado');
        return false;
      }
    } catch (err) {
      error(err instanceof Error ? err.message : String(err));
      return false;
    }
  }, [isSupported, error, success, warning]);

  const subscribeToPush = useCallback(async () => {
    if (permission !== 'granted') {
      const granted = await requestPermission();
      if (!granted) return null;
    }

    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY
      });

      setSubscription(subscription);
      success('Suscripción a notificaciones push exitosa');
      return subscription;
    } catch (err) {
      error(err instanceof Error ? err.message : String(err));
      return null;
    }
  }, [permission, requestPermission, success, error]);

  const sendNotification = useCallback((data: NotificationData) => {
    if (permission !== 'granted') {
      warning('Permisos de notificación no concedidos');
      return;
    }

    const notification = new Notification(data.title, {
      body: data.body,
      icon: data.icon || '/icon-192x192.png',
      badge: data.badge,
      tag: data.tag,
      data: data.data,
      requireInteraction: data.requireInteraction,
      silent: data.silent
    });

    notification.onclick = () => {
      window.focus();
      notification.close();
    };
  }, [permission, warning]);

  return {
    isSupported,
    permission,
    subscription,
    requestPermission,
    subscribeToPush,
    sendNotification
  };
};

// Componente de configuración de notificaciones
export const NotificationSettings: React.FC = () => {
  const { 
    isSupported, 
    permission, 
    subscription, 
    requestPermission, 
    subscribeToPush 
  } = usePushNotifications();

  if (!isSupported) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Notificaciones Push</h3>
        <p className="text-gray-600 dark:text-gray-400">
          Las notificaciones push no están soportadas en este navegador.
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Notificaciones Push</h3>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span>Estado de permisos:</span>
          <Badge variant={permission === 'granted' ? 'success' : 'warning'}>
            {permission === 'granted' ? 'Concedido' : 'No concedido'}
          </Badge>
        </div>

        <div className="flex items-center justify-between">
          <span>Suscripción:</span>
          <Badge variant={subscription ? 'success' : 'secondary'}>
            {subscription ? 'Activa' : 'Inactiva'}
          </Badge>
        </div>

        <div className="flex gap-2">
          {permission !== 'granted' && (
            <Button onClick={requestPermission} variant="default">
              Solicitar Permisos
            </Button>
          )}
          
          {permission === 'granted' && !subscription && (
            <Button onClick={subscribeToPush} variant="default">
              Activar Notificaciones
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
};

// Dashboard personalizable
interface DashboardWidget {
  id: string;
  type: 'kpi' | 'chart' | 'table' | 'custom';
  title: string;
  config: any;
  position: { x: number; y: number; w: number; h: number };
}

interface DashboardLayout {
  id: string;
  name: string;
  widgets: DashboardWidget[];
  isDefault?: boolean;
}

export const useDashboardCustomization = () => {
  const [layouts, setLayouts] = useState<DashboardLayout[]>([]);
  const [currentLayout, setCurrentLayout] = useState<string>('');
  const { success, error, warning, info } = useToastActions();

  useEffect(() => {
    const savedLayouts = localStorage.getItem('dashboard-layouts');
    const savedCurrent = localStorage.getItem('dashboard-current-layout');
    
    if (savedLayouts) {
      setLayouts(JSON.parse(savedLayouts));
    }
    
    if (savedCurrent) {
      setCurrentLayout(savedCurrent);
    }
  }, []);

  const saveLayout = useCallback((layout: DashboardLayout) => {
    const newLayouts = layouts.filter(l => l.id !== layout.id);
    newLayouts.push(layout);
    
    setLayouts(newLayouts);
    localStorage.setItem('dashboard-layouts', JSON.stringify(newLayouts));
    success('Layout guardado exitosamente');
  }, [layouts, success]);

  const deleteLayout = useCallback((layoutId: string) => {
    const newLayouts = layouts.filter(l => l.id !== layoutId);
    setLayouts(newLayouts);
    localStorage.setItem('dashboard-layouts', JSON.stringify(newLayouts));
    success('Layout eliminado');
  }, [layouts, success]);

  const setCurrentLayoutId = useCallback((layoutId: string) => {
    setCurrentLayout(layoutId);
    localStorage.setItem('dashboard-current-layout', layoutId);
  }, []);

  return {
    layouts,
    currentLayout,
    saveLayout,
    deleteLayout,
    setCurrentLayoutId
  };
};

// Componente de exportación de datos
interface ExportOptions {
  format: 'csv' | 'json' | 'excel' | 'pdf';
  dateRange?: { start: Date; end: Date };
  filters?: Record<string, any>;
  includeHeaders?: boolean;
}

export const useDataExport = () => {
  const [isExporting, setIsExporting] = useState(false);
  const { success, error, warning, info } = useToastActions();

  const exportData = useCallback(async (
    endpoint: string, 
    options: ExportOptions,
    filename?: string
  ) => {
    setIsExporting(true);
    
    try {
      const response = await fetch(`/api/export/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
      });

      if (!response.ok) {
        throw new Error('Error al exportar datos');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `export-${Date.now()}.${options.format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      success('Datos exportados exitosamente');
    } catch (err) {
      error(err instanceof Error ? err.message : String(err));
    } finally {
      setIsExporting(false);
    }
  }, [success, error]);

  return { exportData, isExporting };
};

// Componente de exportación
export const DataExport: React.FC<{ endpoint: string; title: string }> = ({ 
  endpoint, 
  title 
}) => {
  const { exportData, isExporting } = useDataExport();
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'csv',
    includeHeaders: true
  });

  const handleExport = () => {
    exportData(endpoint, exportOptions, `${title}-${Date.now()}.${exportOptions.format}`);
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Exportar {title}</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Formato</label>
          <select
            value={exportOptions.format}
            onChange={(e) => setExportOptions(prev => ({ 
              ...prev, 
              format: e.target.value as ExportOptions['format'] 
            }))}
            className="w-full p-2 border rounded-md dark:bg-gray-800 dark:border-gray-700"
          >
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
            <option value="excel">Excel</option>
            <option value="pdf">PDF</option>
          </select>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="includeHeaders"
            checked={exportOptions.includeHeaders}
            onChange={(e) => setExportOptions(prev => ({ 
              ...prev, 
              includeHeaders: e.target.checked 
            }))}
            className="mr-2"
          />
          <label htmlFor="includeHeaders">Incluir encabezados</label>
        </div>

        <Button 
          onClick={handleExport} 
          disabled={isExporting}
          variant="default"
          className="w-full"
        >
          {isExporting ? (
            <>
              <LoadingSpinner size="sm" className="mr-2" />
              Exportando...
            </>
          ) : (
            `Exportar como ${exportOptions.format.toUpperCase()}`
          )}
        </Button>
      </div>
    </Card>
  );
};

// Búsqueda global inteligente
interface SearchResult {
  id: string;
  type: 'usuario' | 'empleado' | 'clase' | 'pago' | 'asistencia';
  title: string;
  description: string;
  url: string;
  relevance: number;
}

export const useGlobalSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const { success, error, warning, info } = useToastActions();

  const search = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setIsSearching(true);
    
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}`);
      
      if (!response.ok) {
        throw new Error('Error en la búsqueda');
      }

      const data = await response.json();
      setResults(data.results || []);
    } catch (err) {
      error(err instanceof Error ? err.message : String(err));
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [success, error]);

  const debouncedQuery = useMemo(() => {
    let timeoutId: NodeJS.Timeout;
    return (searchQuery: string) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        setQuery(searchQuery);
        search(searchQuery);
      }, 300);
    };
  }, [setQuery, search]);

  useEffect(() => {
    debouncedQuery(query);
  }, [query, debouncedQuery]);

  return {
    query,
    setQuery,
    results,
    isSearching,
    search
  };
};

// Componente de búsqueda global
export const GlobalSearch: React.FC = () => {
  const { query, setQuery, results, isSearching } = useGlobalSearch();
  const [isOpen, setIsOpen] = useState(false);

  const handleResultClick = (result: SearchResult) => {
    window.location.href = result.url;
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          placeholder="Buscar en todo el sistema..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsOpen(true)}
          className="w-full pl-10 pr-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
        />
        <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
          {isSearching ? (
            <LoadingSpinner size="sm" />
          ) : (
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          )}
        </div>
      </div>

      {isOpen && (query || results.length > 0) && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
          {results.length > 0 ? (
            <div className="py-2">
              {results.map((result) => (
                <div
                  key={result.id}
                  onClick={() => handleResultClick(result)}
                  className="px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{result.title}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {result.description}
                      </div>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      {result.type}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : query && !isSearching ? (
            <div className="px-4 py-8 text-center text-gray-500">
              No se encontraron resultados para "{query}"
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}; 