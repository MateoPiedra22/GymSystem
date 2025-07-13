'use client'
export const dynamic = 'force-dynamic'
/**
 * Página de gestión de usuarios completa
 * Incluye CRUD, filtros, búsqueda y análisis
 */

import React, { useState, useEffect } from 'react'
import { DashboardLayout } from '../components/DashboardLayout'
import { 
  LoadingSpinner, 
  TableLoader, 
  SkeletonTable
} from '../components/ui/LoadingSpinner'
import { 
  EmptyState, 
  EmptyUsers, 
  EmptySearch 
} from '../components/ui/EmptyState'
import { Alert } from '../components/ui/Alert'
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
  RefreshCw
} from 'lucide-react'

// Tipos de datos
interface Usuario {
  id: string
  nombre: string
  apellido: string
  email: string
  telefono?: string
  fecha_nacimiento?: string
  direccion?: string
  tipo_membresia?: string
  objetivo?: string
  esta_activo: boolean
  fecha_registro: string
  estado_pago?: string
  username?: string
  ultima_asistencia?: string
}

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'activos' | 'inactivos'>('todos')
  const [filtroMembresia, setFiltroMembresia] = useState<'todos' | 'Premium' | 'Básica'>('todos')
  const [selectedUser, setSelectedUser] = useState<Usuario | null>(null)
  const [showUserModal, setShowUserModal] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit' | 'create'>('view')
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    nombre: '',
    apellido: '',
    email: '',
    telefono: '',
    fecha_nacimiento: '',
    direccion: '',
    tipo_membresia: '',
    objetivo: '',
    esta_activo: true,
    username: '',
    password: ''
  })

  // Cargar usuarios al montar el componente
  useEffect(() => {
    loadUsuarios()
  }, [])

  const loadUsuarios = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.getUsers()
      if (response.data) {
        setUsuarios(response.data)
      }
    } catch (error) {
      console.error('Error cargando usuarios:', error)
      setError('Error al cargar usuarios. Intenta de nuevo.')
      toast.error('Error al cargar usuarios')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = () => {
    setSelectedUser(null)
    setModalMode('create')
    setFormData({
      nombre: '',
      apellido: '',
      email: '',
      telefono: '',
      fecha_nacimiento: '',
      direccion: '',
      tipo_membresia: '',
      objetivo: '',
      esta_activo: true,
      username: '',
      password: ''
    })
    setShowUserModal(true)
  }

  const handleViewUser = (user: Usuario) => {
    setSelectedUser(user)
    setModalMode('view')
    setFormData({
      nombre: user.nombre || '',
      apellido: user.apellido || '',
      email: user.email || '',
      telefono: user.telefono || '',
      fecha_nacimiento: user.fecha_nacimiento || '',
      direccion: user.direccion || '',
      tipo_membresia: user.tipo_membresia || '',
      objetivo: user.objetivo || '',
      esta_activo: user.esta_activo,
      username: user.username || '',
      password: ''
    })
    setShowUserModal(true)
  }

  const handleEditUser = (user: Usuario) => {
    setSelectedUser(user)
    setModalMode('edit')
    setFormData({
      nombre: user.nombre || '',
      apellido: user.apellido || '',
      email: user.email || '',
      telefono: user.telefono || '',
      fecha_nacimiento: user.fecha_nacimiento || '',
      direccion: user.direccion || '',
      tipo_membresia: user.tipo_membresia || '',
      objetivo: user.objetivo || '',
      esta_activo: user.esta_activo,
      username: user.username || '',
      password: ''
    })
    setShowUserModal(true)
  }

  const handleDeleteUser = async (user: Usuario) => {
    if (confirm(`¿Estás seguro de eliminar al usuario "${user.nombre} ${user.apellido}"?`)) {
      try {
        await api.deleteUser(user.id)
        toast.success('Usuario eliminado correctamente')
        loadUsuarios() // Recargar lista
      } catch (error) {
        console.error('Error eliminando usuario:', error)
        toast.error('Error al eliminar usuario')
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (modalMode === 'view') {
      setShowUserModal(false)
      return
    }

    try {
      setSaving(true)
      setError(null)
      
      const userData = {
        nombre: formData.nombre,
        apellido: formData.apellido,
        email: formData.email,
        telefono: formData.telefono,
        fecha_nacimiento: formData.fecha_nacimiento,
        direccion: formData.direccion,
        tipo_membresia: formData.tipo_membresia,
        objetivo: formData.objetivo,
        esta_activo: formData.esta_activo,
        username: formData.username,
        ...(modalMode === 'create' && formData.password && { password: formData.password })
      }

      if (modalMode === 'create') {
        await api.createUser(userData)
        toast.success('Usuario creado correctamente')
      } else if (modalMode === 'edit' && selectedUser) {
        await api.updateUser(selectedUser.id, userData)
        toast.success('Usuario actualizado correctamente')
      }

      setShowUserModal(false)
      loadUsuarios() // Recargar lista
    } catch (error: any) {
      console.error('Error guardando usuario:', error)
      setError(error?.message || 'Error al guardar usuario')
      toast.error(error?.message || 'Error al guardar usuario')
    } finally {
      setSaving(false)
    }
  }

  const handleCloseModal = () => {
    setShowUserModal(false)
    setSelectedUser(null)
    setFormData({
      nombre: '',
      apellido: '',
      email: '',
      telefono: '',
      fecha_nacimiento: '',
      direccion: '',
      tipo_membresia: '',
      objetivo: '',
      esta_activo: true,
      username: '',
      password: ''
    })
  }

  const getEstadoPagoColor = (estado: string) => {
    switch (estado) {
      case 'Al día':
        return 'bg-green-100 text-green-800'
      case 'Pendiente':
        return 'bg-yellow-100 text-yellow-800'
      case 'Vencido':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // Filtros aplicados
  const usuariosFiltrados = usuarios.filter(usuario => {
    const matchSearch = (
      usuario.nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      usuario.apellido?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      usuario.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      usuario.username?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    
    const matchEstado = filtroEstado === 'todos' || 
      (filtroEstado === 'activos' && usuario.esta_activo) ||
      (filtroEstado === 'inactivos' && !usuario.esta_activo)
    
    const matchMembresia = filtroMembresia === 'todos' || usuario.tipo_membresia === filtroMembresia
    
    return matchSearch && matchEstado && matchMembresia
  })

  // Estadísticas
  const estadisticas = {
    total: usuarios.length,
    activos: usuarios.filter(u => u.esta_activo).length,
    nuevos_mes: usuarios.filter(u => {
      const fechaRegistro = new Date(u.fecha_registro)
      const haceUnMes = new Date()
      haceUnMes.setMonth(haceUnMes.getMonth() - 1)
      return fechaRegistro > haceUnMes
    }).length,
    pagos_vencidos: usuarios.filter(u => u.estado_pago === 'Vencido').length
  }

  if (loading) {
    return (
      <DashboardLayout>
        <TableLoader />
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout>
        <Alert variant="destructive">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={loadUsuarios}
              className="ml-4 px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Reintentar
            </button>
          </div>
        </Alert>
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
              <h1 className="page-title">
                👥 Gestión de Usuarios
              </h1>
              <p className="page-subtitle">
                Administra los usuarios y miembros del gimnasio
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={loadUsuarios}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Actualizar</span>
              </button>
              
              <button
                onClick={handleCreateUser}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <UserPlus className="h-4 w-4" />
                <span>Nuevo Usuario</span>
              </button>
            </div>
          </div>
        </div>

        {/* Estadísticas */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Usuarios</p>
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
                <p className="text-sm font-medium text-gray-600">Activos</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.activos}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Nuevos (Mes)</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.nuevos_mes}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <UserX className="h-6 w-6 text-red-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Pagos Vencidos</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.pagos_vencidos}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filtros y búsqueda */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
              {/* Búsqueda */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar usuarios..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              {/* Filtro de estado */}
              <select
                value={filtroEstado}
                onChange={(e) => setFiltroEstado(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todos los estados</option>
                <option value="activos">Solo activos</option>
                <option value="inactivos">Solo inactivos</option>
              </select>
              
              {/* Filtro de membresía */}
              <select
                value={filtroMembresia}
                onChange={(e) => setFiltroMembresia(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todas las membresías</option>
                <option value="Premium">Premium</option>
                <option value="Básica">Básica</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setSearchTerm('')
                  setFiltroEstado('todos')
                  setFiltroMembresia('todos')
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Limpiar filtros
              </button>
            </div>
          </div>
        </div>

        {/* Tabla de usuarios */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {usuariosFiltrados.length === 0 ? (
            searchTerm ? (
              <EmptySearch 
                searchTerm={searchTerm} 
              />
            ) : (
              <EmptyUsers />
            )
          ) : (
            <>
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">
                  Usuarios ({usuariosFiltrados.length})
                </h3>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Usuario
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Contacto
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Membresía
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Estado Pago
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
                    {usuariosFiltrados.map((usuario) => (
                      <tr key={usuario.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {usuario.nombre} {usuario.apellido}
                            </div>
                            <div className="text-sm text-gray-500">
                              Registro: {new Date(usuario.fecha_registro).toLocaleDateString()}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{usuario.email}</div>
                          <div className="text-sm text-gray-500">{usuario.telefono}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            usuario.tipo_membresia === 'Premium' 
                              ? 'bg-purple-100 text-purple-800' 
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {usuario.tipo_membresia || 'Sin membresía'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getEstadoPagoColor(usuario.estado_pago || '')}`}>
                            {usuario.estado_pago || 'N/A'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            usuario.esta_activo 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {usuario.esta_activo ? 'Activo' : 'Inactivo'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end space-x-2">
                            <button
                              onClick={() => handleViewUser(usuario)}
                              className="text-blue-600 hover:text-blue-900 p-1 transition-colors"
                              title="Ver detalles"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleEditUser(usuario)}
                              className="text-green-600 hover:text-green-900 p-1 transition-colors"
                              title="Editar"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteUser(usuario)}
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
            </>
          )}
        </div>
      </div>

      {/* Modal de usuario */}
      {showUserModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                {modalMode === 'create' ? 'Nuevo Usuario' : 
                 modalMode === 'edit' ? 'Editar Usuario' : 'Detalles del Usuario'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {error && (
                <Alert variant="destructive">
                  <div className="flex items-center justify-between">
                    <span>{error}</span>
                    <button
                      onClick={() => setError(null)}
                      className="ml-4 px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                    >
                      X
                    </button>
                  </div>
                </Alert>
              )}
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
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
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
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
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
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Teléfono
                  </label>
                  <input
                    type="tel"
                    value={formData.telefono}
                    onChange={(e) => setFormData({...formData, telefono: e.target.value})}
                    disabled={modalMode === 'view'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Fecha de Nacimiento
                  </label>
                  <input
                    type="date"
                    value={formData.fecha_nacimiento}
                    onChange={(e) => setFormData({...formData, fecha_nacimiento: e.target.value})}
                    disabled={modalMode === 'view'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo de Membresía
                  </label>
                  <select
                    value={formData.tipo_membresia}
                    onChange={(e) => setFormData({...formData, tipo_membresia: e.target.value})}
                    disabled={modalMode === 'view'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                  >
                    <option value="">Seleccionar membresía</option>
                    <option value="Básica">Básica</option>
                    <option value="Premium">Premium</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dirección
                </label>
                <textarea
                  value={formData.direccion}
                  onChange={(e) => setFormData({...formData, direccion: e.target.value})}
                  disabled={modalMode === 'view'}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Objetivo
                </label>
                <textarea
                  value={formData.objetivo}
                  onChange={(e) => setFormData({...formData, objetivo: e.target.value})}
                  disabled={modalMode === 'view'}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                />
              </div>
              
              {modalMode !== 'view' && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Username
                      </label>
                      <input
                        type="text"
                        value={formData.username}
                        onChange={(e) => setFormData({...formData, username: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    
                    {modalMode === 'create' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Contraseña
                        </label>
                        <input
                          type="password"
                          value={formData.password}
                          onChange={(e) => setFormData({...formData, password: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="esta_activo"
                      checked={formData.esta_activo}
                      onChange={(e) => setFormData({...formData, esta_activo: e.target.checked})}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="esta_activo" className="ml-2 block text-sm text-gray-900">
                      Usuario activo
                    </label>
                  </div>
                </>
              )}
              
              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
                
                {modalMode !== 'view' && (
                  <button
                    type="submit"
                    disabled={saving}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {saving ? (
                      <>
                        <LoadingSpinner size="sm" />
                        <span>Guardando...</span>
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4" />
                        <span>Guardar</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
