'use client'
export const dynamic = 'force-dynamic'

import React, { useState, useEffect } from 'react'
import { DashboardLayout } from '../components/DashboardLayout'
import { 
  LoadingSpinner, 
  TableLoader, 
  SkeletonTable
} from '../components/ui/LoadingSpinner'
import { 
  EmptyState, 
  EmptyData, 
  EmptySearch 
} from '../components/ui/EmptyState'
import { Alert } from '../components/ui/Alert'
import { api } from '../utils/api'
import { useToastActions } from '../components/Toast';
import { 
  FileText, 
  Plus, 
  Search, 
  Filter, 
  Edit2, 
  Trash2, 
  Eye,
  Download,
  BarChart3,
  TrendingUp,
  CheckCircle,
  XCircle,
  Save,
  X,
  Calendar,
  Users,
  DollarSign,
  Clock
} from 'lucide-react'

// Tipos de datos
interface Reporte {
  id: string
  nombre: string
  tipo: 'usuarios' | 'asistencias' | 'pagos' | 'clases' | 'general'
  fecha_generacion: string
  periodo: string
  datos: any
  formato: 'PDF' | 'Excel' | 'CSV'
  estado: 'Completado' | 'En proceso' | 'Error'
  url_descarga?: string
}

interface Estadisticas {
  total_usuarios: number
  usuarios_activos: number
  usuarios_nuevos_mes: number
  total_asistencias: number
  asistencias_hoy: number
  promedio_asistencia: number
  total_pagos: number
  pagos_pendientes: number
  total_recaudado: number
  total_clases: number
  clases_activas: number
  ocupacion_promedio: number
}

export default function ReportesPage() {
  const toast = useToastActions();
  const [reportes, setReportes] = useState<Reporte[]>([])
  const [estadisticas, setEstadisticas] = useState<Estadisticas | null>(null)
  const [loading, setLoading] = useState(true)
  const [generando, setGenerando] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filtroTipo, setFiltroTipo] = useState<'todos' | 'usuarios' | 'asistencias' | 'pagos' | 'clases' | 'general'>('todos')
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'Completado' | 'En proceso' | 'Error'>('todos')
  const [selectedReporte, setSelectedReporte] = useState<Reporte | null>(null)
  const [showReporteModal, setShowReporteModal] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    nombre: '',
    tipo: '',
    periodo: '',
    formato: ''
  })

  // Cargar datos al montar el componente
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Cargar reportes (simulado por ahora)
      setReportes([])
      
      // Cargar estadísticas (simulado por ahora)
      setEstadisticas({
        total_usuarios: 150,
        usuarios_activos: 120,
        usuarios_nuevos_mes: 15,
        total_asistencias: 1250,
        asistencias_hoy: 45,
        promedio_asistencia: 8.3,
        total_pagos: 180,
        pagos_pendientes: 12,
        total_recaudado: 45000,
        total_clases: 25,
        clases_activas: 20,
        ocupacion_promedio: 75
      })
    } catch (error) {
      console.error('Error cargando datos:', error)
      setError('Error al cargar datos. Intenta de nuevo.')
      toast.error('Error al cargar datos')
    } finally {
      setLoading(false)
    }
  }

  // Filtros aplicados
  const reportesFiltrados = reportes.filter(reporte => {
    const matchSearch = (
      reporte.nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      reporte.tipo?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    
    const matchTipo = filtroTipo === 'todos' || reporte.tipo === filtroTipo
    const matchEstado = filtroEstado === 'todos' || reporte.estado === filtroEstado
    
    return matchSearch && matchTipo && matchEstado
  })

  const handleCreateReporte = () => {
    setSelectedReporte(null)
    setFormData({
      nombre: '',
      tipo: '',
      periodo: '',
      formato: ''
    })
    setShowReporteModal(true)
  }

  const handleViewReporte = (reporte: Reporte) => {
    setSelectedReporte(reporte)
    setFormData({
      nombre: reporte.nombre,
      tipo: reporte.tipo,
      periodo: reporte.periodo,
      formato: reporte.formato
    })
    setShowReporteModal(true)
  }

  const handleDeleteReporte = async (reporte: Reporte) => {
    if (confirm(`¿Estás seguro de eliminar el reporte "${reporte.nombre}"?`)) {
      try {
        // Simular eliminación por ahora
        toast.success('Reporte eliminado correctamente')
        loadData() // Recargar lista
      } catch (error) {
        console.error('Error eliminando reporte:', error)
        toast.error('Error al eliminar reporte')
      }
    }
  }

  const handleGenerarReporte = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validaciones básicas
    if (!formData.nombre.trim()) {
      toast.error('El nombre del reporte es obligatorio')
      return
    }

    if (!formData.tipo) {
      toast.error('El tipo de reporte es obligatorio')
      return
    }

    if (!formData.periodo) {
      toast.error('El período es obligatorio')
      return
    }

    if (!formData.formato) {
      toast.error('El formato es obligatorio')
      return
    }

    try {
      setGenerando(true)
      
      const reporteData = {
        nombre: formData.nombre.trim(),
        tipo: formData.tipo as any,
        periodo: formData.periodo,
        formato: formData.formato as any
      }

      // Simular generación de reporte por ahora
      toast.success('Reporte generado correctamente')
      setShowReporteModal(false)
      loadData() // Recargar lista
    } catch (error) {
      console.error('Error generando reporte:', error)
      toast.error('Error al generar reporte')
    } finally {
      setGenerando(false)
    }
  }

  const cerrarModal = () => {
    setShowReporteModal(false)
    setSelectedReporte(null)
    setFormData({
      nombre: '',
      tipo: '',
      periodo: '',
      formato: ''
    })
  }

  const descargarReporte = async (reporte: Reporte) => {
    try {
      if (reporte.url_descarga) {
        window.open(reporte.url_descarga, '_blank')
      } else {
        // Simular descarga por ahora
        toast.success('Descarga simulada')
      }
      toast.success('Descarga iniciada')
    } catch (error) {
      console.error('Error descargando reporte:', error)
      toast.error('Error al descargar reporte')
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <TableLoader />
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="page-header">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="page-title gradient-gym-text">
                📊 Gestión de Reportes
              </h1>
              <p className="page-subtitle">
                Genera y administra reportes del gimnasio
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={handleCreateReporte}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span>Nuevo Reporte</span>
              </button>
            </div>
          </div>
        </div>

        {/* Alertas */}
        {error && (
          <Alert variant="destructive">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-2 text-sm underline"
            >
              Cerrar
            </button>
          </Alert>
        )}

        {/* Estadísticas */}
        {estadisticas && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Usuarios</p>
                  <p className="text-2xl font-bold text-gray-900">{estadisticas.total_usuarios}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Usuarios Activos</p>
                  <p className="text-2xl font-bold text-gray-900">{estadisticas.usuarios_activos}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <DollarSign className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Recaudado</p>
                  <p className="text-2xl font-bold text-gray-900">${estadisticas.total_recaudado.toLocaleString()}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <BarChart3 className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Ocupación Promedio</p>
                  <p className="text-2xl font-bold text-gray-900">{estadisticas.ocupacion_promedio}%</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filtros y búsqueda */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
            <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
              {/* Búsqueda */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Buscar reportes..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-full sm:w-64"
                />
              </div>
              
              {/* Filtro de tipo */}
              <select
                value={filtroTipo}
                onChange={(e) => setFiltroTipo(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todos los tipos</option>
                <option value="usuarios">Usuarios</option>
                <option value="asistencias">Asistencias</option>
                <option value="pagos">Pagos</option>
                <option value="clases">Clases</option>
                <option value="general">General</option>
              </select>
              
              {/* Filtro de estado */}
              <select
                value={filtroEstado}
                onChange={(e) => setFiltroEstado(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todos los estados</option>
                <option value="Completado">Completado</option>
                <option value="En proceso">En proceso</option>
                <option value="Error">Error</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setSearchTerm('')
                  setFiltroTipo('todos')
                  setFiltroEstado('todos')
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Limpiar filtros
              </button>
            </div>
          </div>
        </div>

        {/* Tabla de reportes */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {reportesFiltrados.length === 0 ? (
            searchTerm ? (
              <EmptySearch searchTerm={searchTerm} />
            ) : (
              <EmptyData 
                title="No hay reportes generados"
                description="Comienza generando el primer reporte."
              />
            )
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Nombre
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Período
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Formato
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fecha Generación
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {reportesFiltrados.map((reporte) => (
                    <tr key={reporte.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {reporte.nombre}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          reporte.tipo === 'usuarios' ? 'bg-blue-100 text-blue-800' :
                          reporte.tipo === 'asistencias' ? 'bg-green-100 text-green-800' :
                          reporte.tipo === 'pagos' ? 'bg-yellow-100 text-yellow-800' :
                          reporte.tipo === 'clases' ? 'bg-purple-100 text-purple-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {reporte.tipo}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {reporte.periodo}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          reporte.formato === 'PDF' ? 'bg-red-100 text-red-800' :
                          reporte.formato === 'Excel' ? 'bg-green-100 text-green-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {reporte.formato}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          reporte.estado === 'Completado' ? 'bg-green-100 text-green-800' :
                          reporte.estado === 'En proceso' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {reporte.estado}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(reporte.fecha_generacion).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleViewReporte(reporte)}
                            className="text-blue-600 hover:text-blue-900 p-1 transition-colors"
                            title="Ver detalles"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          {reporte.estado === 'Completado' && (
                            <button
                              onClick={() => descargarReporte(reporte)}
                              className="text-green-600 hover:text-green-900 p-1 transition-colors"
                              title="Descargar"
                            >
                              <Download className="h-4 w-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteReporte(reporte)}
                            className="text-red-600 hover:text-red-900 p-1 transition-colors"
                            title="Eliminar"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal de reporte */}
        {showReporteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-semibold text-gray-900">
                  {selectedReporte ? 'Detalles de Reporte' : 'Generar Nuevo Reporte'}
                </h2>
                <button
                  onClick={cerrarModal}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              {selectedReporte ? (
                // Vista de detalles
                <div className="p-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Nombre
                      </label>
                      <p className="text-sm text-gray-900">{selectedReporte.nombre}</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Tipo
                      </label>
                      <p className="text-sm text-gray-900">{selectedReporte.tipo}</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Período
                      </label>
                      <p className="text-sm text-gray-900">{selectedReporte.periodo}</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Formato
                      </label>
                      <p className="text-sm text-gray-900">{selectedReporte.formato}</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Estado
                      </label>
                      <p className="text-sm text-gray-900">{selectedReporte.estado}</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Fecha de Generación
                      </label>
                      <p className="text-sm text-gray-900">
                        {new Date(selectedReporte.fecha_generacion).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-end space-x-3 pt-4 border-t">
                    <button
                      onClick={cerrarModal}
                      className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                    >
                      Cerrar
                    </button>
                    {selectedReporte.estado === 'Completado' && (
                      <button
                        onClick={() => descargarReporte(selectedReporte)}
                        className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                      >
                        <div className="flex items-center space-x-2">
                          <Download className="h-4 w-4" />
                          <span>Descargar</span>
                        </div>
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                // Formulario para generar reporte
                <form onSubmit={handleGenerarReporte} className="p-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Nombre del Reporte *
                      </label>
                      <input
                        type="text"
                        value={formData.nombre}
                        onChange={(e) => setFormData({...formData, nombre: e.target.value})}
                        placeholder="Ej: Reporte de Usuarios Enero 2024"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Tipo de Reporte *
                      </label>
                      <select
                        value={formData.tipo}
                        onChange={(e) => setFormData({...formData, tipo: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        required
                      >
                        <option value="">Seleccionar tipo</option>
                        <option value="usuarios">Usuarios</option>
                        <option value="asistencias">Asistencias</option>
                        <option value="pagos">Pagos</option>
                        <option value="clases">Clases</option>
                        <option value="general">General</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Período *
                      </label>
                      <select
                        value={formData.periodo}
                        onChange={(e) => setFormData({...formData, periodo: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        required
                      >
                        <option value="">Seleccionar período</option>
                        <option value="Hoy">Hoy</option>
                        <option value="Esta semana">Esta semana</option>
                        <option value="Este mes">Este mes</option>
                        <option value="Este año">Este año</option>
                        <option value="Últimos 30 días">Últimos 30 días</option>
                        <option value="Últimos 90 días">Últimos 90 días</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Formato *
                      </label>
                      <select
                        value={formData.formato}
                        onChange={(e) => setFormData({...formData, formato: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        required
                      >
                        <option value="">Seleccionar formato</option>
                        <option value="PDF">PDF</option>
                        <option value="Excel">Excel</option>
                        <option value="CSV">CSV</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-end space-x-3 pt-4 border-t">
                    <button
                      type="button"
                      onClick={cerrarModal}
                      className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={generando}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {generando ? (
                        <div className="flex items-center space-x-2">
                          <LoadingSpinner size="sm" />
                          <span>Generando...</span>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <FileText className="h-4 w-4" />
                          <span>Generar Reporte</span>
                        </div>
                      )}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
