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
  EmptyClasses, 
  EmptySearch 
} from '../components/ui/EmptyState'
import { Alert } from '../components/ui/Alert'
import { api } from '../utils/api'
import { toast } from 'react-hot-toast'
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
  Dumbbell,
  Play,
  Pause,
  RefreshCw
} from 'lucide-react'

// Tipos de datos
interface Clase {
  id: string
  nombre: string
  descripcion?: string
  instructor?: string
  horario?: string
  duracion?: number
  capacidad_maxima?: number
  nivel?: string
  tipo?: string
  sala?: string
  esta_activa: boolean
  precio?: number
  fecha_creacion: string
  ultima_modificacion: string
}

export default function ClasesPage() {
  const [clases, setClases] = useState<Clase[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'activas' | 'inactivas'>('todos')
  const [filtroNivel, setFiltroNivel] = useState<'todos' | 'Principiante' | 'Intermedio' | 'Avanzado'>('todos')
  const [selectedClase, setSelectedClase] = useState<Clase | null>(null)
  const [showClaseModal, setShowClaseModal] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit' | 'create'>('view')
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    nombre: '',
    descripcion: '',
    instructor: '',
    horario: '',
    duracion: '',
    capacidad_maxima: '',
    nivel: '',
    tipo: '',
    sala: '',
    esta_activa: true,
    precio: ''
  })

  // Cargar clases al montar el componente
  useEffect(() => {
    loadClases()
  }, [])

  const loadClases = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.getClases()
      if (response.data) {
        setClases(response.data)
      }
    } catch (error) {
      console.error('Error cargando clases:', error)
      setError('Error al cargar clases. Intenta de nuevo.')
      toast.error('Error al cargar clases')
    } finally {
      setLoading(false)
    }
  }

  // Filtros aplicados
  const clasesFiltradas = clases.filter(clase => {
    const matchSearch = (
      clase.nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      clase.descripcion?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      clase.instructor?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      clase.tipo?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    
    const matchEstado = filtroEstado === 'todos' || 
      (filtroEstado === 'activas' && clase.esta_activa) ||
      (filtroEstado === 'inactivas' && !clase.esta_activa)
    
    const matchNivel = filtroNivel === 'todos' || clase.nivel === filtroNivel
    
    return matchSearch && matchEstado && matchNivel
  })

  // Estadísticas
  const estadisticas = {
    total: clases.length,
    activas: clases.filter(c => c.esta_activa).length,
    inactivas: clases.filter(c => !c.esta_activa).length,
    principiantes: clases.filter(c => c.nivel === 'Principiante').length,
    intermedios: clases.filter(c => c.nivel === 'Intermedio').length,
    avanzados: clases.filter(c => c.nivel === 'Avanzado').length
  }

  const handleCreateClase = () => {
    setSelectedClase(null)
    setModalMode('create')
    setFormData({
      nombre: '',
      descripcion: '',
      instructor: '',
      horario: '',
      duracion: '',
      capacidad_maxima: '',
      nivel: '',
      tipo: '',
      sala: '',
      esta_activa: true,
      precio: ''
    })
    setShowClaseModal(true)
  }

  const handleViewClase = (clase: Clase) => {
    setSelectedClase(clase)
    setModalMode('view')
    setFormData({
      nombre: clase.nombre || '',
      descripcion: clase.descripcion || '',
      instructor: clase.instructor || '',
      horario: clase.horario || '',
      duracion: clase.duracion?.toString() || '',
      capacidad_maxima: clase.capacidad_maxima?.toString() || '',
      nivel: clase.nivel || '',
      tipo: clase.tipo || '',
      sala: clase.sala || '',
      esta_activa: clase.esta_activa,
      precio: clase.precio?.toString() || ''
    })
    setShowClaseModal(true)
  }

  const handleEditClase = (clase: Clase) => {
    setSelectedClase(clase)
    setModalMode('edit')
    setFormData({
      nombre: clase.nombre || '',
      descripcion: clase.descripcion || '',
      instructor: clase.instructor || '',
      horario: clase.horario || '',
      duracion: clase.duracion?.toString() || '',
      capacidad_maxima: clase.capacidad_maxima?.toString() || '',
      nivel: clase.nivel || '',
      tipo: clase.tipo || '',
      sala: clase.sala || '',
      esta_activa: clase.esta_activa,
      precio: clase.precio?.toString() || ''
    })
    setShowClaseModal(true)
  }

  const handleDeleteClase = async (clase: Clase) => {
    if (confirm(`¿Estás seguro de eliminar la clase "${clase.nombre}"?`)) {
      try {
        await api.deleteClase(clase.id)
        toast.success('Clase eliminada correctamente')
        loadClases() // Recargar lista
      } catch (error) {
        console.error('Error eliminando clase:', error)
        toast.error('Error al eliminar clase')
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (modalMode === 'view') {
      setShowClaseModal(false)
      return
    }

    try {
      setSaving(true)
      setError(null)
      
      const claseData = {
        nombre: formData.nombre,
        descripcion: formData.descripcion,
        instructor: formData.instructor,
        capacidad: formData.capacidad_maxima,
        duracion: formData.duracion,
        horario: formData.horario,
        nivel: formData.nivel,
        esta_activa: formData.esta_activa,
        precio: formData.precio
      }

      if (modalMode === 'create') {
        await api.createClase(claseData)
        toast.success('Clase creada exitosamente')
      } else {
        if (!selectedClase) {
          throw new Error('No se seleccionó ninguna clase para editar')
        }
        await api.updateClase(selectedClase.id, claseData)
        toast.success('Clase actualizada exitosamente')
      }

      setShowClaseModal(false)
      setFormData({
        nombre: '',
        descripcion: '',
        instructor: '',
        horario: '',
        duracion: '',
        capacidad_maxima: '',
        nivel: '',
        tipo: '',
        sala: '',
        esta_activa: true,
        precio: ''
      })
      loadClases() // Recargar lista
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido'
      setError(errorMessage)
      toast.error(`Error: ${errorMessage}`)
    } finally {
      setSaving(false)
    }
  }

  const cerrarModal = () => {
    setShowClaseModal(false)
    setSelectedClase(null)
    setFormData({
      nombre: '',
      descripcion: '',
      instructor: '',
      horario: '',
      duracion: '',
      capacidad_maxima: '',
      nivel: '',
      tipo: '',
      sala: '',
      esta_activa: true,
      precio: ''
    })
  }

  const exportData = () => {
    const csvContent = [
      ['ID', 'Nombre', 'Descripción', 'Instructor', 'Horario', 'Duración', 'Capacidad', 'Nivel', 'Tipo', 'Sala', 'Estado', 'Precio'],
      ...clasesFiltradas.map(clase => [
        clase.id,
        clase.nombre,
        clase.descripcion || '',
        clase.instructor || '',
        clase.horario || '',
        clase.duracion?.toString() || '',
        clase.capacidad_maxima?.toString() || '',
        clase.nivel || '',
        clase.tipo || '',
        clase.sala || '',
        clase.esta_activa ? 'Activa' : 'Inactiva',
        clase.precio?.toString() || ''
      ])
    ].map(row => row.map(field => `"${field}"`).join(',')).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', 'clases.csv')
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
                🏋️ Gestión de Clases
              </h1>
              <p className="page-subtitle">
                Administra las clases y horarios de tu gimnasio
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
                onClick={handleCreateClase}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span>Nueva Clase</span>
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
                <Dumbbell className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Clases</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.total}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Activas</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.activas}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Users className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Principiantes</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.principiantes}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Target className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avanzados</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.avanzados}</p>
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
                  placeholder="Buscar clases..."
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
                <option value="activas">Solo activas</option>
                <option value="inactivas">Solo inactivas</option>
              </select>
              
              {/* Filtro de nivel */}
              <select
                value={filtroNivel}
                onChange={(e) => setFiltroNivel(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todos los niveles</option>
                <option value="Principiante">Principiante</option>
                <option value="Intermedio">Intermedio</option>
                <option value="Avanzado">Avanzado</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setSearchTerm('')
                  setFiltroEstado('todos')
                  setFiltroNivel('todos')
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Limpiar filtros
              </button>
            </div>
          </div>
        </div>

        {/* Tabla de clases */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {clasesFiltradas.length === 0 ? (
            searchTerm ? (
              <EmptySearch 
                searchTerm={searchTerm} 
              />
            ) : (
              <EmptyClasses />
            )
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Clase
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Instructor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Horario
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duración
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Capacidad
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Nivel
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Precio
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {clasesFiltradas.map((clase) => (
                    <tr key={clase.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {clase.nombre}
                          </div>
                          {clase.descripcion && (
                            <div className="text-sm text-gray-500">
                              {clase.descripcion}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {clase.instructor || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {clase.horario || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {clase.duracion ? `${clase.duracion} min` : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {clase.capacidad_maxima || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          clase.nivel === 'Principiante' ? 'bg-green-100 text-green-800' :
                          clase.nivel === 'Intermedio' ? 'bg-yellow-100 text-yellow-800' :
                          clase.nivel === 'Avanzado' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {clase.nivel || 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          clase.esta_activa 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {clase.esta_activa ? 'Activa' : 'Inactiva'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {clase.precio ? `$${clase.precio.toLocaleString()}` : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleViewClase(clase)}
                            className="text-blue-600 hover:text-blue-900 p-1 transition-colors"
                            title="Ver detalles"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleEditClase(clase)}
                            className="text-green-600 hover:text-green-900 p-1 transition-colors"
                            title="Editar"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteClase(clase)}
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

        {/* Modal de clase */}
        {showClaseModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-semibold text-gray-900">
                  {modalMode === 'create' ? 'Nueva Clase' : 
                   modalMode === 'edit' ? 'Editar Clase' : 'Detalles de Clase'}
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
                      Nombre *
                    </label>
                    <input
                      type="text"
                      value={formData.nombre}
                      onChange={(e) => setFormData({...formData, nombre: e.target.value})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Instructor
                    </label>
                    <input
                      type="text"
                      value={formData.instructor}
                      onChange={(e) => setFormData({...formData, instructor: e.target.value})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Horario
                    </label>
                    <input
                      type="text"
                      value={formData.horario}
                      onChange={(e) => setFormData({...formData, horario: e.target.value})}
                      disabled={modalMode === 'view'}
                      placeholder="Ej: Lunes y Miércoles 18:00"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Duración (minutos)
                    </label>
                    <input
                      type="number"
                      value={formData.duracion}
                      onChange={(e) => setFormData({...formData, duracion: e.target.value})}
                      disabled={modalMode === 'view'}
                      min="0"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Capacidad Máxima
                    </label>
                    <input
                      type="number"
                      value={formData.capacidad_maxima}
                      onChange={(e) => setFormData({...formData, capacidad_maxima: e.target.value})}
                      disabled={modalMode === 'view'}
                      min="0"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nivel
                    </label>
                    <select
                      value={formData.nivel}
                      onChange={(e) => setFormData({...formData, nivel: e.target.value})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    >
                      <option value="">Seleccionar nivel</option>
                      <option value="Principiante">Principiante</option>
                      <option value="Intermedio">Intermedio</option>
                      <option value="Avanzado">Avanzado</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo
                    </label>
                    <input
                      type="text"
                      value={formData.tipo}
                      onChange={(e) => setFormData({...formData, tipo: e.target.value})}
                      disabled={modalMode === 'view'}
                      placeholder="Ej: Yoga, Spinning, etc."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Sala
                    </label>
                    <input
                      type="text"
                      value={formData.sala}
                      onChange={(e) => setFormData({...formData, sala: e.target.value})}
                      disabled={modalMode === 'view'}
                      placeholder="Ej: Sala A, Gimnasio Principal"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Precio
                    </label>
                    <input
                      type="number"
                      value={formData.precio}
                      onChange={(e) => setFormData({...formData, precio: e.target.value})}
                      disabled={modalMode === 'view'}
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Descripción
                  </label>
                  <textarea
                    value={formData.descripcion}
                    onChange={(e) => setFormData({...formData, descripcion: e.target.value})}
                    disabled={modalMode === 'view'}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    placeholder="Descripción detallada de la clase..."
                  />
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="esta_activa"
                    checked={formData.esta_activa}
                    onChange={(e) => setFormData({...formData, esta_activa: e.target.checked})}
                    disabled={modalMode === 'view'}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="esta_activa" className="ml-2 block text-sm text-gray-900">
                    Clase activa
                  </label>
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
