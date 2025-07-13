'use client'
export const dynamic = 'force-dynamic'
/**
 * Página de gestión de empleados completa
 * Incluye CRUD, filtros, búsqueda y análisis
 */

import React, { useState, useEffect } from 'react'
import { DashboardLayout } from '../components/DashboardLayout'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { api } from '../utils/api'
import { toast } from 'react-hot-toast'
import { 
  Users, 
  UserPlus, 
  Search, 
  Filter, 
  Edit2, 
  Trash2, 
  Eye,
  Mail,
  Phone,
  Calendar,
  MapPin,
  Target,
  TrendingUp,
  UserCheck,
  UserX,
  Download,
  Upload,
  MoreHorizontal,
  Save,
  X,
  Briefcase,
  Clock,
  DollarSign
} from 'lucide-react'

// Tipos de datos
interface Empleado {
  id: string
  nombre: string
  apellido: string
  email: string
  telefono?: string
  fecha_contratacion: string
  direccion?: string
  cargo: string
  salario?: number
  esta_activo: boolean
  horario_trabajo?: string
  especialidad?: string
  username?: string
  es_admin?: boolean
}

export default function EmpleadosPage() {
  const [empleados, setEmpleados] = useState<Empleado[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'activos' | 'inactivos'>('todos')
  const [filtroCargo, setFiltroCargo] = useState<'todos' | 'Entrenador' | 'Recepcionista' | 'Administrador'>('todos')
  const [selectedEmpleado, setSelectedEmpleado] = useState<Empleado | null>(null)
  const [showEmpleadoModal, setShowEmpleadoModal] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit' | 'create'>('view')
  const [formData, setFormData] = useState({
    nombre: '',
    apellido: '',
    email: '',
    telefono: '',
    fecha_contratacion: '',
    direccion: '',
    cargo: '',
    salario: '',
    esta_activo: true,
    horario_trabajo: '',
    especialidad: '',
    username: '',
    password: ''
  })
  const [error, setError] = useState<string | null>(null)

  // Cargar empleados al montar el componente
  useEffect(() => {
    loadEmpleados()
  }, [])

  const loadEmpleados = async () => {
    try {
      setLoading(true)
      const response = await api.getEmpleados()
      if (response.data) {
        setEmpleados(response.data)
      }
    } catch (error) {
      console.error('Error cargando empleados:', error)
      toast.error('Error al cargar empleados')
    } finally {
      setLoading(false)
    }
  }

  // Filtros aplicados
  const empleadosFiltrados = empleados.filter(empleado => {
    const matchSearch = (
      empleado.nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      empleado.apellido?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      empleado.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      empleado.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      empleado.cargo?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    
    const matchEstado = filtroEstado === 'todos' || 
      (filtroEstado === 'activos' && empleado.esta_activo) ||
      (filtroEstado === 'inactivos' && !empleado.esta_activo)
    
    const matchCargo = filtroCargo === 'todos' || empleado.cargo === filtroCargo
    
    return matchSearch && matchEstado && matchCargo
  })

  // Estadísticas
  const estadisticas = {
    total: empleados.length,
    activos: empleados.filter(e => e.esta_activo).length,
    entrenadores: empleados.filter(e => e.cargo === 'Entrenador').length,
    recepcionistas: empleados.filter(e => e.cargo === 'Recepcionista').length,
    administradores: empleados.filter(e => e.cargo === 'Administrador').length
  }

  const handleCreateEmpleado = () => {
    setSelectedEmpleado(null)
    setModalMode('create')
    setFormData({
      nombre: '',
      apellido: '',
      email: '',
      telefono: '',
      fecha_contratacion: new Date().toISOString().split('T')[0],
      direccion: '',
      cargo: '',
      salario: '',
      esta_activo: true,
      horario_trabajo: '',
      especialidad: '',
      username: '',
      password: ''
    })
    setShowEmpleadoModal(true)
  }

  const handleViewEmpleado = (empleado: Empleado) => {
    setSelectedEmpleado(empleado)
    setModalMode('view')
    setFormData({
      nombre: empleado.nombre || '',
      apellido: empleado.apellido || '',
      email: empleado.email || '',
      telefono: empleado.telefono || '',
      fecha_contratacion: empleado.fecha_contratacion || '',
      direccion: empleado.direccion || '',
      cargo: empleado.cargo || '',
      salario: empleado.salario?.toString() || '',
      esta_activo: empleado.esta_activo,
      horario_trabajo: empleado.horario_trabajo || '',
      especialidad: empleado.especialidad || '',
      username: empleado.username || '',
      password: ''
    })
    setShowEmpleadoModal(true)
  }

  const handleEditEmpleado = (empleado: Empleado) => {
    setSelectedEmpleado(empleado)
    setModalMode('edit')
    setFormData({
      nombre: empleado.nombre || '',
      apellido: empleado.apellido || '',
      email: empleado.email || '',
      telefono: empleado.telefono || '',
      fecha_contratacion: empleado.fecha_contratacion || '',
      direccion: empleado.direccion || '',
      cargo: empleado.cargo || '',
      salario: empleado.salario?.toString() || '',
      esta_activo: empleado.esta_activo,
      horario_trabajo: empleado.horario_trabajo || '',
      especialidad: empleado.especialidad || '',
      username: empleado.username || '',
      password: ''
    })
    setShowEmpleadoModal(true)
  }

  const handleDeleteEmpleado = async (empleado: Empleado) => {
    if (confirm(`¿Estás seguro de eliminar a ${empleado.nombre} ${empleado.apellido}?`)) {
      try {
        await api.deleteEmpleado(empleado.id)
        toast.success('Empleado eliminado correctamente')
        loadEmpleados() // Recargar lista
      } catch (error) {
        console.error('Error eliminando empleado:', error)
        toast.error('Error al eliminar empleado')
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (modalMode === 'view') {
      setShowEmpleadoModal(false)
      return
    }

    try {
      setSaving(true)
      setError(null)
      
      const empleadoData = {
        nombre: formData.nombre,
        apellido: formData.apellido,
        email: formData.email,
        telefono: formData.telefono,
        fecha_contratacion: formData.fecha_contratacion,
        direccion: formData.direccion,
        cargo: formData.cargo,
        salario: formData.salario ? parseFloat(formData.salario) : undefined,
        esta_activo: formData.esta_activo,
        horario_trabajo: formData.horario_trabajo,
        especialidad: formData.especialidad,
        username: formData.username,
        ...(modalMode === 'create' && formData.password && { password: formData.password })
      }

      if (modalMode === 'create') {
        await api.createEmpleado(empleadoData)
        toast.success('Empleado creado exitosamente')
      } else {
        if (!selectedEmpleado) {
          throw new Error('No se seleccionó ningún empleado para editar')
        }
        await api.updateEmpleado(selectedEmpleado.id, empleadoData)
        toast.success('Empleado actualizado exitosamente')
      }

      setShowEmpleadoModal(false)
      loadEmpleados() // Recargar lista
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido'
      setError(errorMessage)
      toast.error(`Error: ${errorMessage}`)
    } finally {
      setSaving(false)
    }
  }

  const getCargoColor = (cargo: string) => {
    switch (cargo) {
      case 'Entrenador': return 'bg-blue-100 text-blue-800'
      case 'Recepcionista': return 'bg-green-100 text-green-800'
      case 'Administrador': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const exportData = () => {
    const csvData = empleadosFiltrados.map(e => 
      `${e.nombre || ''},${e.apellido || ''},${e.email || ''},${e.telefono || ''},${e.cargo || ''},${e.salario || ''}`
    ).join('\n')
    
    const blob = new Blob([`Nombre,Apellido,Email,Teléfono,Cargo,Salario\n${csvData}`], 
      { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'empleados.csv'
    a.click()
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="page-header">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="page-title gradient-gym-text">
                👨‍💼 Gestión de Empleados
              </h1>
              <p className="page-subtitle">
                Administra el personal de tu gimnasio
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
                onClick={handleCreateEmpleado}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <UserPlus className="h-4 w-4" />
                <span>Nuevo Empleado</span>
              </button>
            </div>
          </div>
        </div>

        {/* Estadísticas */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="gym-card">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-blue-100 rounded-full">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Empleados</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.total}</p>
              </div>
            </div>
          </div>

          <div className="gym-card">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-green-100 rounded-full">
                <UserCheck className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Empleados Activos</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.activos}</p>
              </div>
            </div>
          </div>

          <div className="gym-card">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-blue-100 rounded-full">
                <Target className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Entrenadores</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.entrenadores}</p>
              </div>
            </div>
          </div>

          <div className="gym-card">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-green-100 rounded-full">
                <Briefcase className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Recepcionistas</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.recepcionistas}</p>
              </div>
            </div>
          </div>

          <div className="gym-card">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-purple-100 rounded-full">
                <DollarSign className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Administradores</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.administradores}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filtros y búsqueda */}
        <div className="gym-card">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            {/* Barra de búsqueda */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar empleados..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Filtros */}
            <div className="flex items-center space-x-3">
              <select
                value={filtroEstado}
                onChange={(e) => setFiltroEstado(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todos los estados</option>
                <option value="activos">Solo activos</option>
                <option value="inactivos">Solo inactivos</option>
              </select>

              <select
                value={filtroCargo}
                onChange={(e) => setFiltroCargo(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todos los cargos</option>
                <option value="Entrenador">Entrenadores</option>
                <option value="Recepcionista">Recepcionistas</option>
                <option value="Administrador">Administradores</option>
              </select>
            </div>
          </div>
        </div>

        {/* Tabla de empleados */}
        <div className="gym-card overflow-hidden">
          {loading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Empleado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contacto
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cargo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Salario
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Horario
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {empleadosFiltrados.map((empleado) => (
                    <tr key={empleado.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {empleado.nombre} {empleado.apellido}
                          </div>
                          <div className="text-sm text-gray-500">
                            Contratación: {new Date(empleado.fecha_contratacion).toLocaleDateString()}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{empleado.email}</div>
                        <div className="text-sm text-gray-500">{empleado.telefono}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCargoColor(empleado.cargo)}`}>
                          {empleado.cargo}
                        </span>
                        {empleado.especialidad && (
                          <div className="text-xs text-gray-500 mt-1">
                            {empleado.especialidad}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {empleado.salario ? `$${empleado.salario.toLocaleString()}` : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {empleado.horario_trabajo || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          empleado.esta_activo 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {empleado.esta_activo ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleViewEmpleado(empleado)}
                            className="text-blue-600 hover:text-blue-900 p-1 transition-colors"
                            title="Ver detalles"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleEditEmpleado(empleado)}
                            className="text-green-600 hover:text-green-900 p-1 transition-colors"
                            title="Editar"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteEmpleado(empleado)}
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
              
              {empleadosFiltrados.length === 0 && (
                <div className="text-center py-12">
                  <Users className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No hay empleados</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {searchTerm || filtroEstado !== 'todos' || filtroCargo !== 'todos'
                      ? 'No se encontraron empleados con los filtros aplicados.'
                      : 'Comienza agregando un nuevo empleado.'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal completo para empleados */}
        {showEmpleadoModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-semibold text-gray-900">
                    {modalMode === 'create' ? 'Nuevo Empleado' : 
                     modalMode === 'edit' ? 'Editar Empleado' : 'Detalles del Empleado'}
                  </h3>
                  <button
                    onClick={() => setShowEmpleadoModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>
              </div>
              
              <div className="p-6">
                <form onSubmit={handleSubmit}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Información personal */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-gray-900">Información Personal</h4>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Nombre *
                        </label>
                        <input
                          type="text"
                          value={formData.nombre}
                          onChange={(e) => setFormData({...formData, nombre: e.target.value})}
                          disabled={modalMode === 'view'}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                          required
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Apellido *
                        </label>
                        <input
                          type="text"
                          value={formData.apellido}
                          onChange={(e) => setFormData({...formData, apellido: e.target.value})}
                          disabled={modalMode === 'view'}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                          required
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Email *
                        </label>
                        <input
                          type="email"
                          value={formData.email}
                          onChange={(e) => setFormData({...formData, email: e.target.value})}
                          disabled={modalMode === 'view'}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                          required
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Username *
                        </label>
                        <input
                          type="text"
                          value={formData.username}
                          onChange={(e) => setFormData({...formData, username: e.target.value})}
                          disabled={modalMode === 'view'}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                          required
                        />
                      </div>

                      {modalMode === 'create' && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Contraseña *
                          </label>
                          <input
                            type="password"
                            value={formData.password}
                            onChange={(e) => setFormData({...formData, password: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            required
                          />
                        </div>
                      )}
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Teléfono
                        </label>
                        <input
                          type="tel"
                          value={formData.telefono}
                          onChange={(e) => setFormData({...formData, telefono: e.target.value})}
                          disabled={modalMode === 'view'}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                        />
                      </div>
                    </div>
                    
                    {/* Información laboral */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-gray-900">Información Laboral</h4>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Cargo *
                        </label>
                        <select
                          value={formData.cargo}
                          onChange={(e) => setFormData({...formData, cargo: e.target.value})}
                          disabled={modalMode === 'view'}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                          required
                        >
                          <option value="">Seleccionar...</option>
                          <option value="Entrenador">Entrenador</option>
                          <option value="Recepcionista">Recepcionista</option>
                          <option value="Administrador">Administrador</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Fecha de Contratación *
                        </label>
                        <input
                          type="date"
                          value={formData.fecha_contratacion}
                          onChange={(e) => setFormData({...formData, fecha_contratacion: e.target.value})}
                          disabled={modalMode === 'view'}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                          required
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Salario
                        </label>
                        <input
                          type="number"
                          value={formData.salario}
                          onChange={(e) => setFormData({...formData, salario: e.target.value})}
                          disabled={modalMode === 'view'}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                          placeholder="0.00"
                          step="0.01"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Horario de Trabajo
                        </label>
                        <input
                          type="text"
                          value={formData.horario_trabajo}
                          onChange={(e) => setFormData({...formData, horario_trabajo: e.target.value})}
                          disabled={modalMode === 'view'}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                          placeholder="Ej: Lunes a Viernes 8:00-17:00"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Especialidad
                        </label>
                        <input
                          type="text"
                          value={formData.especialidad}
                          onChange={(e) => setFormData({...formData, especialidad: e.target.value})}
                          disabled={modalMode === 'view'}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                          placeholder="Ej: Musculación, Cardio, Yoga"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Dirección
                        </label>
                        <textarea
                          value={formData.direccion}
                          onChange={(e) => setFormData({...formData, direccion: e.target.value})}
                          disabled={modalMode === 'view'}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                        />
                      </div>
                      
                      <div>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formData.esta_activo}
                            onChange={(e) => setFormData({...formData, esta_activo: e.target.checked})}
                            disabled={modalMode === 'view'}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:bg-gray-100"
                          />
                          <span className="ml-2 text-sm text-gray-700">Empleado activo</span>
                        </label>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-200">
                    <button
                      type="button"
                      onClick={() => setShowEmpleadoModal(false)}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                    >
                      Cancelar
                    </button>
                    {modalMode !== 'view' && (
                      <button
                        type="submit"
                        disabled={saving}
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                      >
                        {saving ? (
                          <>
                            <LoadingSpinner size="sm" />
                            <span>Guardando...</span>
                          </>
                        ) : (
                          <>
                            <Save className="h-4 w-4" />
                            <span>{modalMode === 'create' ? 'Crear Empleado' : 'Guardar Cambios'}</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
} 