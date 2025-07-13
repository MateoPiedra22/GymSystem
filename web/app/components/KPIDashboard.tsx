'use client'

import { useState, useEffect } from 'react'
import { 
  TrendingUp, TrendingDown, DollarSign, Users, Activity, 
  Target, Clock, Star, BarChart3, PieChart, Calendar,
  UserCheck, Award, AlertCircle, Zap
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/Badge'
import { LoadingSpinner } from './ui/LoadingSpinner'
import { Alert, AlertDescription } from './ui/Alert'

interface KPIData {
  // KPIs Financieros
  ingresos_mes: number
  ingresos_por_tipo: Record<string, number>
  ingreso_promedio_usuario: number
  rentabilidad_operativa: number
  eficiencia_cobranza: number
  ltv_promedio: number
  costo_adquisicion_cliente: number
  morosidad_porcentaje: number
  
  // KPIs de Crecimiento
  nuevas_inscripciones_mes: number
  crecimiento_usuarios_mensual: number
  tasa_retencion: number
  tasa_conversion: number
  
  // KPIs Operacionales
  ocupacion_promedio_clases: number
  asistencias_diarias_promedio: number
  utilizacion_hora_pico: number
  uso_instalaciones_por_hora: Record<string, number>
  
  // KPIs de Personal
  ventas_por_empleado: Record<string, number>
  puntualidad_empleados: number
  
  // KPIs de Servicio
  clases_mas_populares: Record<string, number>
  indice_satisfaccion: number
}

interface KPICardProps {
  title: string
  value: string | number
  description: string
  icon: React.ElementType
  trend?: 'up' | 'down' | 'stable'
  trendValue?: number
  color: 'green' | 'blue' | 'purple' | 'orange' | 'red'
  category: string
}

const KPICard = ({ title, value, description, icon: Icon, trend, trendValue, color, category }: KPICardProps) => {
  const colorClasses = {
    green: 'bg-green-50 border-green-200 text-green-800',
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    purple: 'bg-purple-50 border-purple-200 text-purple-800',
    orange: 'bg-orange-50 border-orange-200 text-orange-800',
    red: 'bg-red-50 border-red-200 text-red-800'
  }

  const iconColors = {
    green: 'text-green-600',
    blue: 'text-blue-600',
    purple: 'text-purple-600',
    orange: 'text-orange-600',
    red: 'text-red-600'
  }

  return (
    <Card className={`transition-all hover:shadow-lg ${colorClasses[color]}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg bg-white ${iconColors[color]}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-sm font-medium">{title}</CardTitle>
              <Badge variant="outline" className="text-xs mt-1">{category}</Badge>
            </div>
          </div>
          {trend && trendValue && (
            <div className={`flex items-center space-x-1 text-xs ${
              trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'
            }`}>
              {trend === 'up' ? <TrendingUp className="h-3 w-3" /> : 
               trend === 'down' ? <TrendingDown className="h-3 w-3" /> : null}
              <span>{Math.abs(trendValue)}%</span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="text-2xl font-bold">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </div>
          <CardDescription className="text-xs leading-relaxed">
            {description}
          </CardDescription>
        </div>
      </CardContent>
    </Card>
  )
}

export function KPIDashboard() {
  const [kpis, setKpis] = useState<KPIData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchKPIs()
  }, [])

  const fetchKPIs = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/reportes/kpis')
      if (!response.ok) {
        throw new Error('Error al cargar KPIs')
      }
      const data = await response.json()
      setKpis(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!kpis) return null

  const getColorForMorosidad = (morosidad: number): 'red' | 'orange' => {
    return morosidad > 15 ? 'red' : 'orange'
  }

  const getColorForCrecimiento = (crecimiento: number): 'green' | 'red' => {
    return crecimiento > 0 ? 'green' : 'red'
  }

  const getColorForRetencion = (retencion: number): 'green' | 'orange' => {
    return retencion > 80 ? 'green' : 'orange'
  }

  const getColorForPuntualidad = (puntualidad: number): 'green' | 'orange' => {
    return puntualidad > 90 ? 'green' : 'orange'
  }

  const getColorForSatisfaccion = (satisfaccion: number): 'green' | 'orange' => {
    return satisfaccion > 80 ? 'green' : 'orange'
  }

  const kpiCards = [
    // KPIs Financieros
    {
      title: 'Ingresos del Mes',
      value: `$${kpis.ingresos_mes.toLocaleString()}`,
      description: 'Indicador financiero principal para evaluar la salud del negocio y proyecciones',
      icon: DollarSign,
      color: 'green' as const,
      category: 'Financiero'
    },
    {
      title: 'ARPU (Ingreso por Usuario)',
      value: `$${kpis.ingreso_promedio_usuario.toFixed(2)}`,
      description: 'Mide la rentabilidad por cliente para estrategias de pricing y segmentación',
      icon: Target,
      color: 'green' as const,
      category: 'Financiero'
    },
    {
      title: 'Rentabilidad Operativa',
      value: `$${kpis.rentabilidad_operativa.toLocaleString()}`,
      description: 'Mide la eficiencia operativa y sostenibilidad del negocio a largo plazo',
      icon: TrendingUp,
      color: 'green' as const,
      category: 'Financiero'
    },
    {
      title: 'LTV Promedio',
      value: `$${kpis.ltv_promedio.toFixed(2)}`,
      description: 'Determina cuánto invertir en adquisición de clientes y rentabilidad',
      icon: Star,
      color: 'green' as const,
      category: 'Financiero'
    },
    {
      title: 'CAC (Costo Adquisición)',
      value: `$${kpis.costo_adquisicion_cliente.toFixed(2)}`,
      description: 'Evalúa la eficiencia del gasto en marketing y ventas',
      icon: BarChart3,
      color: 'orange' as const,
      category: 'Financiero'
    },
    {
      title: 'Eficiencia de Cobranza',
      value: `${kpis.eficiencia_cobranza}%`,
      description: 'Optimiza procesos de facturación y mejora el flujo de caja',
      icon: Clock,
      color: 'blue' as const,
      category: 'Financiero'
    },
          {
        title: 'Morosidad',
        value: `${kpis.morosidad_porcentaje}%`,
        description: 'Control de flujo de caja y gestión de cobranzas efectiva',
        icon: AlertCircle,
        color: getColorForMorosidad(kpis.morosidad_porcentaje),
        category: 'Financiero'
      },

      // KPIs de Crecimiento
      {
        title: 'Nuevas Inscripciones',
        value: kpis.nuevas_inscripciones_mes,
        description: 'Mide el crecimiento del negocio y efectividad del marketing',
        icon: Users,
        color: 'blue' as const,
        category: 'Crecimiento'
      },
      {
        title: 'Crecimiento Mensual',
        value: `${kpis.crecimiento_usuarios_mensual}%`,
        description: 'Mide la velocidad de expansión del negocio comparado con períodos anteriores',
        icon: TrendingUp,
        color: getColorForCrecimiento(kpis.crecimiento_usuarios_mensual),
        category: 'Crecimiento'
      },
      {
        title: 'Tasa de Retención',
        value: `${kpis.tasa_retencion}%`,
        description: 'Retener clientes es más barato que adquirir nuevos, impacta rentabilidad',
        icon: UserCheck,
        color: getColorForRetencion(kpis.tasa_retencion),
        category: 'Crecimiento'
      },
    {
      title: 'Tasa de Conversión',
      value: `${kpis.tasa_conversion}%`,
      description: 'Mide efectividad del proceso de ventas y calidad del personal',
      icon: Target,
      color: 'purple' as const,
      category: 'Crecimiento'
    },

    // KPIs Operacionales
    {
      title: 'Ocupación de Clases',
      value: `${kpis.ocupacion_promedio_clases}%`,
      description: 'Optimiza el uso de recursos y planificación de horarios y espacios',
      icon: Calendar,
      color: 'purple' as const,
      category: 'Operacional'
    },
    {
      title: 'Asistencias Diarias',
      value: kpis.asistencias_diarias_promedio.toFixed(1),
      description: 'Indica la actividad y compromiso de los miembros con el gimnasio',
      icon: Activity,
      color: 'purple' as const,
      category: 'Operacional'
    },
    {
      title: 'Utilización Hora Pico',
      value: `${kpis.utilizacion_hora_pico}%`,
      description: 'Optimiza inversión en equipos y planificación de mantenimiento',
      icon: Zap,
      color: 'orange' as const,
      category: 'Operacional'
    },

          // KPIs de Personal
      {
        title: 'Puntualidad Empleados',
        value: `${kpis.puntualidad_empleados}%`,
        description: 'Impacta en la calidad del servicio y eficiencia de operaciones diarias',
        icon: Clock,
        color: getColorForPuntualidad(kpis.puntualidad_empleados),
        category: 'Personal'
      },

      // KPIs de Servicio
      {
        title: 'Índice de Satisfacción',
        value: `${kpis.indice_satisfaccion}%`,
        description: 'Indica calidad del servicio y probabilidad de recomendación a otros',
        icon: Star,
        color: getColorForSatisfaccion(kpis.indice_satisfaccion),
        category: 'Servicio'
      }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">KPIs del Gimnasio</h2>
          <p className="text-muted-foreground">
            20 indicadores clave de rendimiento para optimizar tu negocio
          </p>
        </div>
        <Badge variant="success" className="px-3 py-1">
          Actualizado hace 5 min
        </Badge>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4 lg:gap-6">
        {kpiCards.map((kpi, index) => (
          <KPICard key={index} {...kpi} />
        ))}
      </div>

      {/* Sección adicional para mostrar datos más detallados */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8 mt-6 sm:mt-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <PieChart className="h-5 w-5" />
              <span>Ingresos por Tipo de Cuota</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(kpis.ingresos_por_tipo).map(([tipo, monto]) => (
                <div key={tipo} className="flex justify-between items-center">
                  <span className="text-sm font-medium">{tipo}</span>
                  <span className="font-bold">${monto.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Award className="h-5 w-5" />
              <span>Clases Más Populares</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(kpis.clases_mas_populares)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([clase, asistencias]) => (
                <div key={clase} className="flex justify-between items-center">
                  <span className="text-sm font-medium">{clase}</span>
                  <Badge variant="outline">{asistencias} asistencias</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 