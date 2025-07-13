import { useQuery } from '@tanstack/react-query'

// Tipado específico para datos de gráficos del dashboard - EXPANDIDO
export interface ChartData {
  // 1. Gráfico de ingresos mensuales (últimos 12 meses)
  ingresos_mensuales: Array<{
    mes: string
    monto: number
  }>
  
  // 2. Datos para gráfico de asistencias por día
  asistencias_por_dia: Array<{
    dia: string
    asistencias: number
    fecha: string
  }>
  
  // 3. Métodos de pago más utilizados
  metodos_pago: Array<{
    metodo: string
    cantidad: number
  }>
  
  // 4. Evolución de usuarios activos (últimos 6 meses)
  evolucion_usuarios: Array<{
    mes: string
    usuarios: number
  }>
  
  // 5. Horarios de mayor asistencia
  asistencias_por_hora: Array<{
    hora: string
    asistencias: number
  }>
  
  // 6. Estado de pagos (distribución)
  estados_pago: Array<{
    estado: string
    cantidad: number
  }>
  
  // 7. Datos para gráfico de ingresos por membresía
  rentabilidad_membresias: Array<{
    tipo: string
    ingresos: number
    cantidad_ventas: number
  }>
  
  // 8. Tendencia de nuevos usuarios vs cancelaciones
  tendencia_usuarios: Array<{
    mes: string
    nuevos: number
    cancelaciones: number
  }>
  
  // 9. Ocupación por horario (nuevo)
  ocupacion_por_horario: Array<{
    horario: string
    ocupacion: number
    capacidad: number
  }>
  
  // 10. Crecimiento mensual (nuevo)
  crecimiento_mensual: Array<{
    mes: string
    usuarios_nuevos: number
    usuarios_activos: number
    ingresos: number
  }>
  
  // 11. Clases populares (nuevo)
  clases_populares: Array<{
    nombre: string
    asistencias: number
    rating: number
    instructor: string
  }>
  
  // 12. Distribución de edad de usuarios (nuevo)
  distribucion_edad: Array<{
    rango: string
    cantidad: number
  }>
}

export function useDashboardCharts() {
  return useQuery<ChartData>({
    queryKey: ['dashboardCharts'],
    queryFn: async () => {
      const response = await fetch('/api/reportes/graficos', {
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    },
    staleTime: 3 * 60 * 1000, // 3 minutos - gráficos se actualizan con frecuencia
    gcTime: 8 * 60 * 1000, // 8 minutos en cache
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    // Prefetch datos relacionados
    meta: {
      prefetchRelated: ['kpis', 'usuarios', 'clases']
    }
  })
}

// Hook adicional para gráficos específicos con mejor performance
export function useChartData(chartType: keyof ChartData) {
  return useQuery<ChartData[typeof chartType]>({
    queryKey: ['chart', chartType],
    queryFn: async () => {
      const response = await fetch(`/api/reportes/graficos/${chartType}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    },
    staleTime: 2 * 60 * 1000, // 2 minutos para gráficos individuales
    gcTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: !!chartType, // Solo ejecutar si se especifica el tipo
  })
}

// Alias para compatibilidad
export const useGraficos = useDashboardCharts 