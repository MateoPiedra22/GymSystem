import React from 'react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  variant?: 'default' | 'search' | 'error';
}

export function EmptyState({ 
  title = 'No hay datos disponibles',
  description = 'No se encontraron elementos para mostrar.',
  icon = '📋',
  action,
  variant = 'default'
}: EmptyStateProps) {
  const getVariantStyles = () => {
    switch (variant) {
      case 'search':
        return 'text-gray-500 bg-gray-50';
      case 'error':
        return 'text-red-500 bg-red-50';
      default:
        return 'text-gray-500 bg-gray-50';
    }
  };

  return (
    <div className={`flex flex-col items-center justify-center py-12 px-4 rounded-lg ${getVariantStyles()}`}>
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-lg font-medium mb-2">{title}</h3>
      <p className="text-sm text-center mb-4 max-w-md">{description}</p>
      {action && (
        <div className="mt-4">
          {action}
        </div>
      )}
    </div>
  );
}

export function EmptySearch({ searchTerm }: { searchTerm: string }) {
  return (
    <EmptyState
      title="No se encontraron resultados"
      description={`No hay elementos que coincidan con "${searchTerm}". Intenta con otros términos de búsqueda.`}
      icon="🔍"
      variant="search"
    />
  );
}

export function EmptyUsers() {
  return (
    <EmptyState
      title="No hay usuarios registrados"
      description="Aún no se han registrado usuarios en el sistema."
      icon="👥"
    />
  );
}

export function EmptyClases() {
  return (
    <EmptyState
      title="No hay clases disponibles"
      description="Aún no se han creado clases en el sistema."
      icon="🏋️"
    />
  );
}

export function EmptyEmpleados() {
  return (
    <EmptyState
      title="No hay empleados registrados"
      description="Aún no se han registrado empleados en el sistema."
      icon="👨‍💼"
    />
  );
}

export function EmptyPagos() {
  return (
    <EmptyState
      title="No hay pagos registrados"
      description="Aún no se han registrado pagos en el sistema."
      icon="💳"
    />
  );
}

export function EmptyAsistencias() {
  return (
    <EmptyState
      title="No hay asistencias registradas"
      description="Aún no se han registrado asistencias en el sistema."
      icon="📊"
    />
  );
}

export function EmptyRutinas() {
  return (
    <EmptyState
      title="No hay rutinas disponibles"
      description="Aún no se han creado rutinas en el sistema."
      icon="🏃"
    />
  );
}

export function EmptyTiposCuota() {
  return (
    <EmptyState
      title="No hay tipos de cuota"
      description="Aún no se han creado tipos de cuota en el sistema."
      icon="💰"
    />
  );
}

export function EmptyData({ title = "No hay datos disponibles", description = "No se encontraron elementos para mostrar." }: { title?: string; description?: string }) {
  return (
    <EmptyState
      title={title}
      description={description}
      icon="📋"
    />
  );
} 