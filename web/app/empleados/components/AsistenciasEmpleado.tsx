'use client';

import { useState, useEffect } from 'react';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

interface AsistenciaEmpleado {
  id: string;
  empleado_id: string;
  fecha: string;
  hora_entrada: string;
  hora_salida?: string;
  horas_trabajadas?: number;
  horas_extra: number;
  tipo_dia: string;
  estado: string;
  observaciones?: string;
  empleado?: {
    nombre_completo: string;
    numero_empleado: string;
  };
}

interface HorasTotales {
  horas_regulares: number;
  horas_extra: number;
  horas_totales: number;
  dias_trabajados: number;
}

interface AsistenciasEmpleadoProps {
  empleadoId?: string;
  mostrarTodos?: boolean;
}

export function AsistenciasEmpleado({ empleadoId, mostrarTodos = false }: AsistenciasEmpleadoProps) {
  const [asistencias, setAsistencias] = useState<AsistenciaEmpleado[]>([]);
  const [horasTotales, setHorasTotales] = useState<HorasTotales | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fechaInicio, setFechaInicio] = useState(() => {
    const hoy = new Date();
    const primerDia = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    return primerDia.toISOString().split('T')[0];
  });
  const [fechaFin, setFechaFin] = useState(() => {
    const hoy = new Date();
    return hoy.toISOString().split('T')[0];
  });

  // Cargar asistencias
  const cargarAsistencias = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
      });

      if (empleadoId) {
        params.append('empleado_id', empleadoId);
      }

      const response = await fetch(`/api/asistencias-empleados?${params}`);
      if (!response.ok) throw new Error('Error al cargar asistencias');
      
      const data = await response.json();
      setAsistencias(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  // Cargar horas totales
  const cargarHorasTotales = async () => {
    if (!empleadoId) return;

    try {
      const fecha = new Date(fechaFin);
      const response = await fetch(
        `/api/empleados/${empleadoId}/horas-totales?mes=${fecha.getMonth() + 1}&ano=${fecha.getFullYear()}`
      );
      if (!response.ok) throw new Error('Error al cargar horas totales');
      
      const data = await response.json();
      setHorasTotales(data);
    } catch (err) {
      console.error('Error al cargar horas totales:', err);
    }
  };

  // Registrar entrada
  const registrarEntrada = async (empleadoIdParam?: string) => {
    try {
      const response = await fetch('/api/asistencias-empleados/entrada', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          empleado_id: empleadoIdParam || empleadoId,
          fecha_hora: new Date().toISOString()
        })
      });

      if (!response.ok) throw new Error('Error al registrar entrada');
      
      await cargarAsistencias();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al registrar entrada');
    }
  };

  // Registrar salida
  const registrarSalida = async (empleadoIdParam?: string) => {
    try {
      const response = await fetch('/api/asistencias-empleados/salida', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          empleado_id: empleadoIdParam || empleadoId,
          fecha_hora: new Date().toISOString()
        })
      });

      if (!response.ok) throw new Error('Error al registrar salida');
      
      await cargarAsistencias();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al registrar salida');
    }
  };

  // Formatear horas
  const formatearHoras = (horas: number) => {
    const h = Math.floor(horas);
    const m = Math.round((horas - h) * 60);
    return `${h}h ${m}m`;
  };

  // Badge para estado
  const BadgeEstado = ({ estado }: { estado: string }) => {
    const colores = {
      'PRESENTE': 'bg-green-100 text-green-800',
      'TARDE': 'bg-yellow-100 text-yellow-800',
      'AUSENTE': 'bg-red-100 text-red-800',
      'PERMISO': 'bg-blue-100 text-blue-800',
      'VACACIONES': 'bg-purple-100 text-purple-800'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colores[estado as keyof typeof colores] || 'bg-gray-100 text-gray-800'}`}>
        {estado}
      </span>
    );
  };

  useEffect(() => {
    cargarAsistencias();
    if (empleadoId) {
      cargarHorasTotales();
    }
  }, [fechaInicio, fechaFin, empleadoId]);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Header con filtros */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Control de Asistencias</h2>
            <p className="text-gray-600">Gestión de entradas, salidas y horarios de empleados</p>
          </div>
          
          {empleadoId && (
            <div className="flex gap-2">
              <button
                onClick={() => registrarEntrada()}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
                Entrada
              </button>
              <button
                onClick={() => registrarSalida()}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Salida
              </button>
            </div>
          )}
        </div>

        {/* Filtros de fecha */}
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Inicio</label>
            <input
              type="date"
              value={fechaInicio}
              onChange={(e) => setFechaInicio(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Fin</label>
            <input
              type="date"
              value={fechaFin}
              onChange={(e) => setFechaFin(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={cargarAsistencias}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              Filtrar
            </button>
          </div>
        </div>
      </div>

      {/* Resumen de horas (solo para empleado específico) */}
      {horasTotales && empleadoId && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Horas Regulares</p>
                <p className="text-2xl font-semibold text-gray-900">{formatearHoras(horasTotales.horas_regulares)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Horas Extra</p>
                <p className="text-2xl font-semibold text-gray-900">{formatearHoras(horasTotales.horas_extra)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Horas</p>
                <p className="text-2xl font-semibold text-gray-900">{formatearHoras(horasTotales.horas_totales)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Días Trabajados</p>
                <p className="text-2xl font-semibold text-gray-900">{horasTotales.dias_trabajados}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="ml-3 text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Lista de asistencias */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {mostrarTodos && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Empleado
                  </th>
                )}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fecha
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entrada
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Salida
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Horas Trabajadas
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Observaciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {asistencias.map((asistencia) => (
                <tr key={asistencia.id} className="hover:bg-gray-50">
                  {mostrarTodos && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {asistencia.empleado?.nombre_completo}
                      </div>
                      <div className="text-sm text-gray-500">
                        {asistencia.empleado?.numero_empleado}
                      </div>
                    </td>
                  )}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {new Date(asistencia.fecha).toLocaleDateString('es-ES', {
                        weekday: 'short',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {new Date(asistencia.hora_entrada).toLocaleTimeString('es-ES', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {asistencia.hora_salida 
                        ? new Date(asistencia.hora_salida).toLocaleTimeString('es-ES', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })
                        : '-'
                      }
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {asistencia.horas_trabajadas ? formatearHoras(asistencia.horas_trabajadas) : '-'}
                    </div>
                    {asistencia.horas_extra > 0 && (
                      <div className="text-xs text-yellow-600">
                        +{formatearHoras(asistencia.horas_extra)} extra
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <BadgeEstado estado={asistencia.estado} />
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">
                      {asistencia.observaciones || '-'}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {asistencias.length === 0 && (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No hay asistencias</h3>
            <p className="mt-1 text-sm text-gray-500">No se encontraron registros para el período seleccionado.</p>
          </div>
        )}
      </div>
    </div>
  );
} 