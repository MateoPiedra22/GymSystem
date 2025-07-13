import { useQuery } from '@tanstack/react-query'

// Tipado específico para KPIs del gimnasio - EXPANDIDO
export interface KpiData {
  // KPIs Financieros
  ingresos_mes: number
  ingresos_total: number
  ingresos_por_tipo: Record<string, number>
  ingreso_promedio_usuario: number
  rentabilidad_operativa: number
  eficiencia_cobranza: number
  ltv_promedio: number
  costo_adquisicion_cliente: number
  morosidad_porcentaje: number
  margen_utilidad: number
  flujo_caja_operativo: number
  ratio_liquidez: number

  // KPIs de Crecimiento
  nuevas_inscripciones_mes: number
  usuarios_activos: number
  total_usuarios: number
  crecimiento_usuarios_mensual: number
  tasa_retencion: number
  tasa_conversion: number
  usuarios_nuevos_mes: number
  tasa_abandono: number
  crecimiento_ingresos: number

  // KPIs Operacionales
  ocupacion_promedio_clases: number
  asistencias_diarias_promedio: number
  utilizacion_hora_pico: number
  uso_instalaciones_por_hora: Record<number, number>
  eficiencia_horarios: number
  capacidad_carga: number
  tiempo_permanencia_promedio: number

  // KPIs de Personal
  ventas_por_empleado: Record<string, number>
  puntualidad_empleados: number
  productividad_empleado: number
  rotacion_personal: number
  satisfaccion_empleado: number
  horas_trabajadas_promedio: number

  // KPIs de Servicio
  clases_mas_populares: Array<{
    nombre: string
    asistencias: number
    capacidad: number
    ocupacion: number
  }>
  indice_satisfaccion: number | null
  calidad_servicio: number
  eficiencia_operacional: number
  tiempo_espera_promedio: number
  proximos_vencimientos: number
  equipos_en_mantenimiento: number
}

export function useKPIs() {
  return useQuery<KpiData>({
    queryKey: ['kpis'],
    queryFn: async () => {
      const response = await fetch('/api/reportes/kpis', {
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    },
    staleTime: 5 * 60 * 1000, // 5 minutos - KPIs cambian con frecuencia moderada
    gcTime: 10 * 60 * 1000, // 10 minutos en cache
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
} 