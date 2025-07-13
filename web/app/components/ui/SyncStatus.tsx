import React from 'react';

interface SyncStatusProps {
  status: 'synced' | 'syncing' | 'error' | 'offline';
  lastSync?: string;
  className?: string;
}

export function SyncStatus({ status, lastSync, className = '' }: SyncStatusProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'synced':
        return {
          icon: '🟢',
          text: 'Sincronizado',
          color: 'text-green-600'
        };
      case 'syncing':
        return {
          icon: '🔄',
          text: 'Sincronizando...',
          color: 'text-blue-600'
        };
      case 'error':
        return {
          icon: '🔴',
          text: 'Error de sincronización',
          color: 'text-red-600'
        };
      case 'offline':
        return {
          icon: '⚫',
          text: 'Sin conexión',
          color: 'text-gray-600'
        };
      default:
        return {
          icon: '⚪',
          text: 'Desconocido',
          color: 'text-gray-600'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <span className="text-sm">{config.icon}</span>
      <span className={`text-sm font-medium ${config.color}`}>
        {config.text}
      </span>
      {lastSync && (
        <span className="text-xs text-gray-500">
          Última sincronización: {lastSync}
        </span>
      )}
    </div>
  );
} 