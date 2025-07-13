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
  Calendar, 
  Plus, 
  Search, 
  Filter, 
  Edit2, 
  Trash2, 
  Eye,
  Clock,
  Users,
  MapPin,
  Target,
  TrendingUp,
  CheckCircle,
  XCircle,
  Download,
  Save,
  X,
  UserCheck,
  UserX,
  RefreshCw
} from 'lucide-react'

// Tipos de datos
interface Asistencia {
  id: string
  usuario_id: string
  usuario_nombre: string
  clase_id?: string
  clase_nombre?: string
  fecha: string
  hora_entrada: string
  hora_salida?: string
  estado: 'Presente' | 'Ausente' | 'Tardanza' | 'Justificada'
  tipo: 'Clase' | 'Gimnasio' | 'Entrenamiento'
  notas?: string
  fecha_creacion: string
}

export default function AsistenciasPage() {
  const toast = useToastActions();
  const [asistencias, setAsistencias] = useState<Asistencia[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'Presente' | 'Ausente' | 'Tardanza' | 'Justificada'>('todos')
  const [filtroTipo, setFiltroTipo] = useState<'todos' | 'Clase' | 'Gimnasio' | 'Entrenamiento'>('todos')
  const [filtroFecha, setFiltroFecha] = useState('')
  const [selectedAsistencia, setSelectedAsistencia] = useState<Asistencia | null>(null)
  const [showAsistenciaModal, setShowAsistenciaModal] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit' | 'create'>('view')
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    usuario_id: '',
    usuario_nombre: '',
    clase_id: '',
    clase_nombre: '',
    fecha: '',
    hora_entrada: '',
    hora_salida: '',
    estado: 'Presente',
    tipo: 'Gimnasio',
    notas: ''
  })

  // Cargar asistencias al montar el componente
  useEffect(() => {
    loadAsistencias()
  }, [])

  const loadAsistencias = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.getAsistencias()
      if (response.data) {
        setAsistencias(response.data)
      }
    } catch (error) {
      console.error('Error cargando asistencias:', error)
      setError('Error al cargar asistencias. Intenta de nuevo.')
      toast.error('Error al cargar asistencias')
    } finally {
      setLoading(false)
    }
  }

  // Filtros aplicados
  const asistenciasFiltradas = asistencias.filter(asistencia => {
    const matchSearch = (
      asistencia.usuario_nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asistencia.clase_nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asistencia.notas?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    
    const matchEstado = filtroEstado === 'todos' || asistencia.estado === filtroEstado
    const matchTipo = filtroTipo === 'todos' || asistencia.tipo === filtroTipo
    
    const matchFecha = !filtroFecha || asistencia.fecha === filtroFecha
    
    return matchSearch && matchEstado && matchTipo && matchFecha
  })

  // Estadísticas
  const estadisticas = {
    total: asistencias.length,
    presentes: asistencias.filter(a => a.estado === 'Presente').length,
    ausentes: asistencias.filter(a => a.estado === 'Ausente').length,
    tardanzas: asistencias.filter(a => a.estado === 'Tardanza').length,
    justificadas: asistencias.filter(a => a.estado === 'Justificada').length,
    clases: asistencias.filter(a => a.tipo === 'Clase').length,
    gimnasio: asistencias.filter(a => a.tipo === 'Gimnasio').length,
    entrenamientos: asistencias.filter(a => a.tipo === 'Entrenamiento').length
  }

  const handleCreateAsistencia = () => {
    setSelectedAsistencia(null)
    setModalMode('create')
    setFormData({
      usuario_id: '',
      usuario_nombre: '',
      clase_id: '',
      clase_nombre: '',
      fecha: new Date().toISOString().split('T')[0],
      hora_entrada: new Date().toTimeString().slice(0, 5),
      hora_salida: '',
      estado: 'Presente',
      tipo: 'Gimnasio',
      notas: ''
    })
    setShowAsistenciaModal(true)
  }

  const handleViewAsistencia = (asistencia: Asistencia) => {
    setSelectedAsistencia(asistencia)
    setModalMode('view')
    setFormData({
      usuario_id: asistencia.usuario_id,
      usuario_nombre: asistencia.usuario_nombre,
      clase_id: asistencia.clase_id || '',
      clase_nombre: asistencia.clase_nombre || '',
      fecha: asistencia.fecha,
      hora_entrada: asistencia.hora_entrada,
      hora_salida: asistencia.hora_salida || '',
      estado: asistencia.estado,
      tipo: asistencia.tipo,
      notas: asistencia.notas || ''
    })
    setShowAsistenciaModal(true)
  }

  const handleEditAsistencia = (asistencia: Asistencia) => {
    setSelectedAsistencia(asistencia)
    setModalMode('edit')
    setFormData({
      usuario_id: asistencia.usuario_id,
      usuario_nombre: asistencia.usuario_nombre,
      clase_id: asistencia.clase_id || '',
      clase_nombre: asistencia.clase_nombre || '',
      fecha: asistencia.fecha,
      hora_entrada: asistencia.hora_entrada,
      hora_salida: asistencia.hora_salida || '',
      estado: asistencia.estado,
      tipo: asistencia.tipo,
      notas: asistencia.notas || ''
    })
    setShowAsistenciaModal(true)
  }

  const handleDeleteAsistencia = async (asistencia: Asistencia) => {
    if (confirm(`¿Estás seguro de eliminar la asistencia de ${asistencia.usuario_nombre}?`)) {
      try {
        await api.deleteAsistencia(asistencia.id)
        toast.success('Asistencia eliminada correctamente')
        loadAsistencias() // Recargar lista
      } catch (error) {
        console.error('Error eliminando asistencia:', error)
        toast.error('Error al eliminar asistencia')
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (modalMode === 'view') {
      setShowAsistenciaModal(false)
      return
    }

    try {
      setSaving(true)
      setError(null)
      
      const asistenciaData = {
        usuario_id: formData.usuario_id,
        usuario_nombre: formData.usuario_nombre,
        clase_id: formData.clase_id,
        clase_nombre: formData.clase_nombre,
        fecha: formData.fecha,
        hora_entrada: formData.hora_entrada,
        hora_salida: formData.hora_salida,
        estado: formData.estado,
        tipo: formData.tipo,
        notas: formData.notas
      }

      if (modalMode === 'create') {
        await api.createAsistencia(asistenciaData)
        toast.success('Asistencia registrada exitosamente')
      } else {
        if (!selectedAsistencia) {
          throw new Error('No se seleccionó ninguna asistencia para editar')
        }
        await api.updateAsistencia(selectedAsistencia.id, asistenciaData)
        toast.success('Asistencia actualizada exitosamente')
      }

      setShowAsistenciaModal(false)
      loadAsistencias() // Recargar lista
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido'
      setError(errorMessage)
      toast.error(`Error: ${errorMessage}`)
    } finally {
      setSaving(false)
    }
  }

  const cerrarModal = () => {
    setShowAsistenciaModal(false)
    setSelectedAsistencia(null)
    setFormData({
      usuario_id: '',
      usuario_nombre: '',
      clase_id: '',
      clase_nombre: '',
      fecha: '',
      hora_entrada: '',
      hora_salida: '',
      estado: 'Presente',
      tipo: 'Gimnasio',
      notas: ''
    })
  }

  const exportData = () => {
    const csvContent = [
      ['ID', 'Usuario', 'Clase', 'Fecha', 'Hora Entrada', 'Hora Salida', 'Estado', 'Tipo', 'Notas'],
      ...asistenciasFiltradas.map(asistencia => [
        asistencia.id,
        asistencia.usuario_nombre,
        asistencia.clase_nombre || '',
        asistencia.fecha,
        asistencia.hora_entrada,
        asistencia.hora_salida || '',
        asistencia.estado,
        asistencia.tipo,
        asistencia.notas || ''
      ])
    ].map(row => row.map(field => `"${field}"`).join(',')).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', 'asistencias.csv')
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
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
                📊 Gestión de Asistencias
              </h1>
              <p className="page-subtitle">
                Controla la asistencia de usuarios y clases
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={exportData}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <Download className="h-4 w-4" />
                <span>Exportar</span>
              </button>
              
              <button
                onClick={handleCreateAsistencia}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span>Nueva Asistencia</span>
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Calendar className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Asistencias</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.total}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <UserCheck className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Presentes</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.presentes}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <UserX className="h-6 w-6 text-red-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Ausentes</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.ausentes}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Tardanzas</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.tardanzas}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filtros y búsqueda */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
            <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
              {/* Búsqueda */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Buscar asistencias..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-full sm:w-64"
                />
              </div>
              
              {/* Filtro de estado */}
              <select
                value={filtroEstado}
                onChange={(e) => setFiltroEstado(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todos los estados</option>
                <option value="Presente">Presente</option>
                <option value="Ausente">Ausente</option>
                <option value="Tardanza">Tardanza</option>
                <option value="Justificada">Justificada</option>
              </select>
              
              {/* Filtro de tipo */}
              <select
                value={filtroTipo}
                onChange={(e) => setFiltroTipo(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todos los tipos</option>
                <option value="Clase">Clase</option>
                <option value="Gimnasio">Gimnasio</option>
                <option value="Entrenamiento">Entrenamiento</option>
              </select>
              
              {/* Filtro de fecha */}
              <input
                type="date"
                value={filtroFecha}
                onChange={(e) => setFiltroFecha(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setSearchTerm('')
                  setFiltroEstado('todos')
                  setFiltroTipo('todos')
                  setFiltroFecha('')
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Limpiar filtros
              </button>
            </div>
          </div>
        </div>

        {/* Tabla de asistencias */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {asistenciasFiltradas.length === 0 ? (
            searchTerm ? (
              <EmptySearch 
                searchTerm={searchTerm} 
              />
            ) : (
              <EmptyData 
                title="No hay asistencias registradas"
                description="Comienza registrando la primera asistencia."
              />
            )
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Usuario
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Clase
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fecha
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Hora Entrada
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Hora Salida
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {asistenciasFiltradas.map((asistencia) => (
                    <tr key={asistencia.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {asistencia.usuario_nombre}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {asistencia.clase_nombre || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(asistencia.fecha).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {asistencia.hora_entrada}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {asistencia.hora_salida || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          asistencia.estado === 'Presente' ? 'bg-green-100 text-green-800' :
                          asistencia.estado === 'Ausente' ? 'bg-red-100 text-red-800' :
                          asistencia.estado === 'Tardanza' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {asistencia.estado}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          asistencia.tipo === 'Clase' ? 'bg-purple-100 text-purple-800' :
                          asistencia.tipo === 'Gimnasio' ? 'bg-blue-100 text-blue-800' :
                          'bg-orange-100 text-orange-800'
                        }`}>
                          {asistencia.tipo}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleViewAsistencia(asistencia)}
                            className="text-blue-600 hover:text-blue-900 p-1 transition-colors"
                            title="Ver detalles"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleEditAsistencia(asistencia)}
                            className="text-green-600 hover:text-green-900 p-1 transition-colors"
                            title="Editar"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteAsistencia(asistencia)}
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

        {/* Modal de asistencia */}
        {showAsistenciaModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-semibold text-gray-900">
                  {modalMode === 'create' ? 'Nueva Asistencia' : 
                   modalMode === 'edit' ? 'Editar Asistencia' : 'Detalles de Asistencia'}
                </h2>
                <button
                  onClick={cerrarModal}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Usuario *
                    </label>
                    <input
                      type="text"
                      value={formData.usuario_nombre}
                      onChange={(e) => setFormData({...formData, usuario_nombre: e.target.value})}
                      disabled={modalMode === 'view'}
                      placeholder="Nombre del usuario"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Clase
                    </label>
                    <input
                      type="text"
                      value={formData.clase_nombre}
                      onChange={(e) => setFormData({...formData, clase_nombre: e.target.value})}
                      disabled={modalMode === 'view'}
                      placeholder="Nombre de la clase (opcional)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Fecha *
                    </label>
                    <input
                      type="date"
                      value={formData.fecha}
                      onChange={(e) => setFormData({...formData, fecha: e.target.value})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Hora Entrada *
                    </label>
                    <input
                      type="time"
                      value={formData.hora_entrada}
                      onChange={(e) => setFormData({...formData, hora_entrada: e.target.value})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Hora Salida
                    </label>
                    <input
                      type="time"
                      value={formData.hora_salida}
                      onChange={(e) => setFormData({...formData, hora_salida: e.target.value})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Estado
                    </label>
                    <select
                      value={formData.estado}
                      onChange={(e) => setFormData({...formData, estado: e.target.value as any})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    >
                      <option value="Presente">Presente</option>
                      <option value="Ausente">Ausente</option>
                      <option value="Tardanza">Tardanza</option>
                      <option value="Justificada">Justificada</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo
                    </label>
                    <select
                      value={formData.tipo}
                      onChange={(e) => setFormData({...formData, tipo: e.target.value as any})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    >
                      <option value="Clase">Clase</option>
                      <option value="Gimnasio">Gimnasio</option>
                      <option value="Entrenamiento">Entrenamiento</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notas
                  </label>
                  <textarea
                    value={formData.notas}
                    onChange={(e) => setFormData({...formData, notas: e.target.value})}
                    disabled={modalMode === 'view'}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    placeholder="Notas adicionales..."
                  />
                </div>
                
                <div className="flex items-center justify-end space-x-3 pt-4 border-t">
                  <button
                    type="button"
                    onClick={cerrarModal}
                    className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Cancelar
                  </button>
                  {modalMode !== 'view' && (
                    <button
                      type="submit"
                      disabled={saving}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {saving ? (
                        <>
                          <LoadingSpinner size="sm" />
                          <span>Guardando...</span>
                        </>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <Save className="h-4 w-4" />
                          <span>Guardar</span>
                        </div>
                      )}
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
