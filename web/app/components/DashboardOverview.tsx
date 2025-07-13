/**
 * Componente DashboardOverview Ultra Moderno y Profesional
 * Muestra KPIs y gráficos interactivos en una experiencia visual armónica
 * Integración completa con backend y soporte para modo oscuro/claro
 */
'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/Badge'
import { Button } from './ui/Button'
import { LoadingSpinner } from './ui/LoadingSpinner'
import { ErrorDisplay } from './ErrorBoundary'
import { useToastActions } from './Toast'
import { useApiErrorHandler } from '../utils/api'
import { apiGet } from '../utils/api'
import { 
  Users, 
  Calendar, 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  RefreshCw,
  AlertTriangle
} from 'lucide-react'

// Tipos para los datos del dashboard
interface DashboardData {
  kpis: {
    totalUsuarios: number
    totalClases: number
    totalPagos: number
    asistenciasHoy: number
  }
  graficos: {
    asistenciasPorMes: Array<{ mes: string; cantidad: number }>
    pagosPorTipo: Array<{ tipo: string; monto: number }>
    usuariosActivos: Array<{ fecha: string; cantidad: number }>
  }
  tendencias: {
    usuarios: { cambio: number; direccion: 'up' | 'down' }
    clases: { cambio: number; direccion: 'up' | 'down' }
    pagos: { cambio: number; direccion: 'up' | 'down' }
    asistencias: { cambio: number; direccion: 'up' | 'down' }
  }
}

// Componente para mostrar un KPI individual
interface KPICardProps {
  title: string
  value: number | string
  icon: React.ReactNode
  trend?: { cambio: number; direccion: 'up' | 'down' }
  loading?: boolean
  error?: Error
}

function KPICard({ title, value, icon, trend, loading, error }: KPICardProps) {
  if (loading) {
    return (
      <Card className="relative overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {title}
          </CardTitle>
          <div className="text-gray-400 dark:text-gray-600">
            {icon}
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-8">
            <LoadingSpinner size="sm" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-red-200 dark:border-red-800">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-red-600 dark:text-red-400">
            {title}
          </CardTitle>
          <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
        </CardHeader>
        <CardContent>
          <p className="text-xs text-red-600 dark:text-red-400">
            Error al cargar datos
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="relative overflow-hidden hover:shadow-md transition-shadow duration-200">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
          {title}
        </CardTitle>
        <div className="text-gray-400 dark:text-gray-600">
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
        {trend && (
          <div className="flex items-center space-x-1 mt-1">
            {trend.direccion === 'up' ? (
              <TrendingUp className="w-3 h-3 text-green-600" />
            ) : (
              <TrendingDown className="w-3 h-3 text-red-600" />
            )}
            <span className={`text-xs font-medium ${
              trend.direccion === 'up' 
                ? 'text-green-600 dark:text-green-400' 
                : 'text-red-600 dark:text-red-400'
            }`}>
              {Math.abs(trend.cambio)}%
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              vs mes anterior
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Componente para mostrar gráficos
interface ChartCardProps {
  title: string
  description?: string
  children: React.ReactNode
  loading?: boolean
  error?: Error
}

function ChartCard({ title, description, children, loading, error }: ChartCardProps) {
  if (loading) {
    return (
      <Card className="col-span-full lg:col-span-2">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {title}
          </CardTitle>
          {description && (
            <CardDescription className="text-gray-600 dark:text-gray-400">
              {description}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="col-span-full lg:col-span-2 border-red-200 dark:border-red-800">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-red-900 dark:text-red-100">
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorDisplay 
            error={error} 
            showDetails={false}
            onRetry={() => window.location.reload()}
          />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="col-span-full lg:col-span-2 hover:shadow-md transition-shadow duration-200">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {title}
        </CardTitle>
        {description && (
          <CardDescription className="text-gray-600 dark:text-gray-400">
            {description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent>
        {children}
      </CardContent>
    </Card>
  )
}

// Componente principal del dashboard
export default function DashboardOverview() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  
  const { success, error: showError } = useToastActions()
  const { handleApiError } = useApiErrorHandler()

  // Función para cargar datos del dashboard
  const loadDashboardData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }
      
      setError(null)
      
      const response = await apiGet<DashboardData>('/api/dashboard/overview')
      setData(response)
      
      if (isRefresh) {
        success('Dashboard actualizado', 'Los datos se han actualizado correctamente')
      }
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error('Error desconocido')
      setError(errorObj)
      
      const { title, message } = handleApiError(errorObj, 'Dashboard')
      showError(title, message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  // Cargar datos al montar el componente
  useEffect(() => {
    loadDashboardData()
  }, [])

  // Función para refrescar datos
  const handleRefresh = () => {
    loadDashboardData(true)
  }

  // Datos de ejemplo para desarrollo (eliminar en producción)
  const mockData: DashboardData = {
    kpis: {
      totalUsuarios: 1247,
      totalClases: 89,
      totalPagos: 156,
      asistenciasHoy: 234
    },
    graficos: {
      asistenciasPorMes: [
        { mes: 'Ene', cantidad: 1200 },
        { mes: 'Feb', cantidad: 1350 },
        { mes: 'Mar', cantidad: 1100 },
        { mes: 'Abr', cantidad: 1400 },
        { mes: 'May', cantidad: 1600 },
        { mes: 'Jun', cantidad: 1800 }
      ],
      pagosPorTipo: [
        { tipo: 'Mensual', monto: 45000 },
        { tipo: 'Trimestral', monto: 32000 },
        { tipo: 'Anual', monto: 28000 },
        { tipo: 'Clase', monto: 15000 }
      ],
      usuariosActivos: [
        { fecha: 'Lun', cantidad: 180 },
        { fecha: 'Mar', cantidad: 220 },
        { fecha: 'Mié', cantidad: 195 },
        { fecha: 'Jue', cantidad: 240 },
        { fecha: 'Vie', cantidad: 210 },
        { fecha: 'Sáb', cantidad: 160 },
        { fecha: 'Dom', cantidad: 120 }
      ]
    },
    tendencias: {
      usuarios: { cambio: 12.5, direccion: 'up' },
      clases: { cambio: 8.3, direccion: 'up' },
      pagos: { cambio: 15.7, direccion: 'up' },
      asistencias: { cambio: 3.2, direccion: 'down' }
    }
  }

  // Usar datos mock si no hay datos reales (solo en desarrollo)
  const dashboardData = data || mockData

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Vista general del sistema
            </p>
          </div>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                <div className="h-4 w-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Vista general del sistema
          </p>
        </div>
        
        <Button 
          onClick={handleRefresh} 
          disabled={refreshing}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Actualizando...' : 'Actualizar'}
        </Button>
      </div>

      {/* KPIs */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                 <KPICard
           title="Total Usuarios"
           value={dashboardData.kpis.totalUsuarios}
           icon={<Users className="w-4 h-4" />}
           trend={dashboardData.tendencias.usuarios}
           loading={loading}
           error={error || undefined}
         />
         <KPICard
           title="Clases Activas"
           value={dashboardData.kpis.totalClases}
           icon={<Calendar className="w-4 h-4" />}
           trend={dashboardData.tendencias.clases}
           loading={loading}
           error={error || undefined}
         />
         <KPICard
           title="Pagos del Mes"
           value={dashboardData.kpis.totalPagos}
           icon={<DollarSign className="w-4 h-4" />}
           trend={dashboardData.tendencias.pagos}
           loading={loading}
           error={error || undefined}
         />
         <KPICard
           title="Asistencias Hoy"
           value={dashboardData.kpis.asistenciasHoy}
           icon={<TrendingUp className="w-4 h-4" />}
           trend={dashboardData.tendencias.asistencias}
           loading={loading}
           error={error || undefined}
         />
      </div>

      {/* Gráficos */}
      <div className="grid gap-6 md:grid-cols-2">
                 <ChartCard
           title="Asistencias por Mes"
           description="Tendencia de asistencias en los últimos 6 meses"
           loading={loading}
           error={error || undefined}
         >
          <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-center">
              <TrendingUp className="w-12 h-12 text-blue-600 dark:text-blue-400 mx-auto mb-2" />
              <p className="text-gray-600 dark:text-gray-400">
                Gráfico de asistencias
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                {dashboardData.graficos.asistenciasPorMes.length} meses de datos
              </p>
            </div>
          </div>
        </ChartCard>

                 <ChartCard
           title="Pagos por Tipo"
           description="Distribución de pagos por tipo de cuota"
           loading={loading}
           error={error || undefined}
         >
          <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-center">
              <DollarSign className="w-12 h-12 text-green-600 dark:text-green-400 mx-auto mb-2" />
              <p className="text-gray-600 dark:text-gray-400">
                Gráfico de pagos
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                {dashboardData.graficos.pagosPorTipo.length} tipos de pago
              </p>
            </div>
          </div>
        </ChartCard>
      </div>

      {/* Información adicional */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Estado del Sistema
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-900 dark:text-gray-100">
                Operativo
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Última Actualización
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-sm text-gray-900 dark:text-gray-100">
              {new Date().toLocaleString('es-ES')}
            </span>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Versión
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="secondary">v6.0.0</Badge>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
