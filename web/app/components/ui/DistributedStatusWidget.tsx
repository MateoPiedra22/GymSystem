import React from 'react';

interface DistributedStatusWidgetProps {
  status: 'online' | 'offline' | 'maintenance' | 'error';
  serviceName: string;
  lastCheck?: string;
  className?: string;
}

export function DistributedStatusWidget({ 
  status, 
  serviceName, 
  lastCheck, 
  className = '' 
}: DistributedStatusWidgetProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'online':
        return {
          icon: '🟢',
          text: 'En línea',
          color: 'text-green-600',
          bgColor: 'bg-green-50'
        };
      case 'offline':
        return {
          icon: '🔴',
          text: 'Fuera de línea',
          color: 'text-red-600',
          bgColor: 'bg-red-50'
        };
      case 'maintenance':
        return {
          icon: '🟡',
          text: 'Mantenimiento',
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50'
        };
      case 'error':
        return {
          icon: '🔴',
          text: 'Error',
          color: 'text-red-600',
          bgColor: 'bg-red-50'
        };
      default:
        return {
          icon: '⚪',
          text: 'Desconocido',
          color: 'text-gray-600',
          bgColor: 'bg-gray-50'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className={`flex items-center justify-between p-3 rounded-lg border ${config.bgColor} ${className}`}>
      <div className="flex items-center space-x-3">
        <span className="text-lg">{config.icon}</span>
        <div>
          <h4 className="text-sm font-medium text-gray-900">{serviceName}</h4>
          <p className={`text-xs font-medium ${config.color}`}>
            {config.text}
          </p>
        </div>
      </div>
      {lastCheck && (
        <div className="text-right">
          <p className="text-xs text-gray-500">
            Última verificación: {lastCheck}
          </p>
        </div>
      )}
    </div>
  );
} 