'use client'
export const dynamic = 'force-dynamic'

import React, { useState, useEffect, useCallback } from 'react'
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
import { toast } from 'react-hot-toast'
import { 
  Settings, 
  Plus, 
  Search, 
  Filter, 
  Edit2, 
  Trash2, 
  Eye,
  Download,
  Save,
  X,
  Palette,
  Image,
  Monitor,
  Database,
  Shield,
  Bell,
  Globe
} from 'lucide-react'

// Tipos de datos
interface Configuracion {
  id: string
  nombre: string
  valor: string
  tipo: 'texto' | 'numero' | 'booleano' | 'color' | 'archivo'
  categoria: 'general' | 'apariencia' | 'seguridad' | 'notificaciones' | 'sistema'
  descripcion?: string
  editable: boolean
  fecha_creacion: string
  ultima_modificacion: string
}

export default function ConfiguracionPage() {
  const [configuraciones, setConfiguraciones] = useState<Configuracion[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filtroCategoria, setFiltroCategoria] = useState<'todos' | 'general' | 'apariencia' | 'seguridad' | 'notificaciones' | 'sistema'>('todos')
  const [selectedConfiguracion, setSelectedConfiguracion] = useState<Configuracion | null>(null)
  const [showConfiguracionModal, setShowConfiguracionModal] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit' | 'create'>('view')
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    nombre: '',
    valor: '',
    tipo: '',
    categoria: '',
    descripcion: '',
    editable: true
  })

  // Cargar configuraciones al montar el componente
  useEffect(() => {
    loadConfiguraciones()
  }, [])

  const loadConfiguraciones = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      // Llamada real al backend
      const response = await api.get('/configuracion/sistema')
      if (response && response.data && response.data.configuraciones_adicionales) {
        setConfiguraciones(
          Object.entries(response.data.configuraciones_adicionales).map(([nombre, valor]: [string, any], idx) => ({
            id: String(idx + 1),
            nombre,
            valor: valor.valor ?? valor, // Soporta objetos o valores simples
            tipo: valor.tipo ?? typeof valor,
            categoria: valor.categoria ?? 'general',
            descripcion: valor.descripcion ?? '',
            editable: valor.editable ?? true,
            fecha_creacion: valor.fecha_creacion ?? new Date().toISOString(),
            ultima_modificacion: valor.ultima_modificacion ?? new Date().toISOString(),
          }))
        )
      } else {
        setConfiguraciones([])
      }
    } catch (error) {
      setError('Error al cargar configuraciones. Intenta de nuevo.')
      toast.error('Error al cargar configuraciones')
    } finally {
      setLoading(false)
    }
  }, [])

  // Filtros aplicados
  const configuracionesFiltradas = configuraciones.filter(config => {
    const matchSearch = (
      config.nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      config.descripcion?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      config.valor?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    
    const matchCategoria = filtroCategoria === 'todos' || config.categoria === filtroCategoria
    
    return matchSearch && matchCategoria
  })

  const handleCreateConfiguracion = () => {
    setSelectedConfiguracion(null)
    setModalMode('create')
    setFormData({
      nombre: '',
      valor: '',
      tipo: '',
      categoria: '',
      descripcion: '',
      editable: true
    })
    setShowConfiguracionModal(true)
  }

  const handleViewConfiguracion = (configuracion: Configuracion) => {
    setSelectedConfiguracion(configuracion)
    setModalMode('view')
    setFormData({
      nombre: configuracion.nombre,
      valor: configuracion.valor,
      tipo: configuracion.tipo,
      categoria: configuracion.categoria,
      descripcion: configuracion.descripcion || '',
      editable: configuracion.editable
    })
    setShowConfiguracionModal(true)
  }

  const handleEditConfiguracion = (configuracion: Configuracion) => {
    setSelectedConfiguracion(configuracion)
    setModalMode('edit')
    setFormData({
      nombre: configuracion.nombre,
      valor: configuracion.valor,
      tipo: configuracion.tipo,
      categoria: configuracion.categoria,
      descripcion: configuracion.descripcion || '',
      editable: configuracion.editable
    })
    setShowConfiguracionModal(true)
  }

  const handleDeleteConfiguracion = async (configuracion: Configuracion) => {
    if (confirm(`¿Estás seguro de eliminar la configuración "${configuracion.nombre}"?`)) {
      try {
        setSaving(true)
        setError(null)
        // Eliminar la configuración del objeto y actualizar en backend
        const nuevas = configuraciones.filter(c => c.nombre !== configuracion.nombre)
        const nuevasObj: any = {}
        nuevas.forEach(c => {
          nuevasObj[c.nombre] = {
            valor: c.valor,
            tipo: c.tipo,
            categoria: c.categoria,
            descripcion: c.descripcion,
            editable: c.editable,
            fecha_creacion: c.fecha_creacion,
            ultima_modificacion: new Date().toISOString()
          }
        })
        await api.put('/configuracion/sistema', {
          configuraciones_adicionales: nuevasObj
        })
        toast.success('Configuración eliminada correctamente')
        loadConfiguraciones()
      } catch (error) {
        setError('Error al eliminar configuración')
        toast.error('Error al eliminar configuración')
      } finally {
        setSaving(false)
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSaving(true)
      setError(null)
      const configData = {
        ...formData,
        valor: formData.valor,
        tipo: formData.tipo,
        categoria: formData.categoria,
        descripcion: formData.descripcion,
        editable: formData.editable
      }
      let response
      if (modalMode === 'create') {
        response = await api.put('/configuracion/sistema', {
          configuraciones_adicionales: {
            [formData.nombre]: configData
          }
        })
        toast.success('Configuración creada correctamente')
      } else if (modalMode === 'edit' && selectedConfiguracion) {
        response = await api.put('/configuracion/sistema', {
          configuraciones_adicionales: {
            [formData.nombre]: configData
          }
        })
        toast.success('Configuración actualizada correctamente')
      }
      setShowConfiguracionModal(false)
      loadConfiguraciones()
    } catch (error) {
      setError('Error al guardar configuración')
      toast.error('Error al guardar configuración')
    } finally {
      setSaving(false)
    }
  }

  const cerrarModal = () => {
    setShowConfiguracionModal(false)
    setSelectedConfiguracion(null)
    setFormData({
      nombre: '',
      valor: '',
      tipo: '',
      categoria: '',
      descripcion: '',
      editable: true
    })
  }

  const exportData = () => {
    const csvContent = [
      ['ID', 'Nombre', 'Valor', 'Tipo', 'Categoría', 'Descripción', 'Editable'],
      ...configuracionesFiltradas.map(config => [
        config.id,
        config.nombre,
        config.valor,
        config.tipo,
        config.categoria,
        config.descripcion || '',
        config.editable ? 'Sí' : 'No'
      ])
    ].map(row => row.map(field => `"${field}"`).join(',')).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', 'configuraciones.csv')
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

  if (error) {
    return (
      <DashboardLayout>
        <Alert variant="destructive">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={loadConfiguraciones}
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
              <h1 className="page-title gradient-gym-text">
                ⚙️ Configuración del Sistema
              </h1>
              <p className="page-subtitle">
                Administra la configuración general del gimnasio
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
                onClick={handleCreateConfiguracion}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span>Nueva Configuración</span>
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

        {/* Filtros y búsqueda */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
            <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
              {/* Búsqueda */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Buscar configuraciones..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-full sm:w-64"
                />
              </div>
              
              {/* Filtro de categoría */}
              <select
                value={filtroCategoria}
                onChange={(e) => setFiltroCategoria(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todas las categorías</option>
                <option value="general">General</option>
                <option value="apariencia">Apariencia</option>
                <option value="seguridad">Seguridad</option>
                <option value="notificaciones">Notificaciones</option>
                <option value="sistema">Sistema</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setSearchTerm('')
                  setFiltroCategoria('todos')
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Limpiar filtros
              </button>
            </div>
          </div>
        </div>

        {/* Tabla de configuraciones */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {configuracionesFiltradas.length === 0 ? (
            searchTerm ? (
              <EmptySearch searchTerm={searchTerm} />
            ) : (
              <EmptyData 
                title="No hay configuraciones"
                description="Comienza agregando la primera configuración."
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
                      Valor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Categoría
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Editable
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Última Modificación
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {configuracionesFiltradas.map((config) => (
                    <tr key={config.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {config.nombre}
                          </div>
                          {config.descripcion && (
                            <div className="text-sm text-gray-500">
                              {config.descripcion}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {config.tipo === 'color' ? (
                            <div className="flex items-center space-x-2">
                              <div 
                                className="w-4 h-4 rounded border"
                                style={{ backgroundColor: config.valor }}
                              />
                              <span>{config.valor}</span>
                            </div>
                          ) : config.tipo === 'booleano' ? (
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              config.valor === 'true' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {config.valor === 'true' ? 'Sí' : 'No'}
                            </span>
                          ) : (
                            config.valor
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          config.tipo === 'texto' ? 'bg-blue-100 text-blue-800' :
                          config.tipo === 'numero' ? 'bg-green-100 text-green-800' :
                          config.tipo === 'booleano' ? 'bg-yellow-100 text-yellow-800' :
                          config.tipo === 'color' ? 'bg-purple-100 text-purple-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {config.tipo}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          config.categoria === 'general' ? 'bg-blue-100 text-blue-800' :
                          config.categoria === 'apariencia' ? 'bg-purple-100 text-purple-800' :
                          config.categoria === 'seguridad' ? 'bg-red-100 text-red-800' :
                          config.categoria === 'notificaciones' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {config.categoria}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          config.editable ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {config.editable ? 'Sí' : 'No'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(config.ultima_modificacion).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleViewConfiguracion(config)}
                            className="text-blue-600 hover:text-blue-900 p-1 transition-colors"
                            title="Ver detalles"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          {config.editable && (
                            <button
                              onClick={() => handleEditConfiguracion(config)}
                              className="text-green-600 hover:text-green-900 p-1 transition-colors"
                              title="Editar"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteConfiguracion(config)}
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

        {/* Modal de configuración */}
        {showConfiguracionModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-semibold text-gray-900">
                  {modalMode === 'create' ? 'Nueva Configuración' : 
                   modalMode === 'edit' ? 'Editar Configuración' : 'Detalles de Configuración'}
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
                      placeholder="Ej: nombre_gimnasio"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Valor *
                    </label>
                    <input
                      type="text"
                      value={formData.valor}
                      onChange={(e) => setFormData({...formData, valor: e.target.value})}
                      disabled={modalMode === 'view'}
                      placeholder="Valor de la configuración"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo *
                    </label>
                    <select
                      value={formData.tipo}
                      onChange={(e) => setFormData({...formData, tipo: e.target.value})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                      required
                    >
                      <option value="">Seleccionar tipo</option>
                      <option value="texto">Texto</option>
                      <option value="numero">Número</option>
                      <option value="booleano">Booleano</option>
                      <option value="color">Color</option>
                      <option value="archivo">Archivo</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Categoría *
                    </label>
                    <select
                      value={formData.categoria}
                      onChange={(e) => setFormData({...formData, categoria: e.target.value})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                      required
                    >
                      <option value="">Seleccionar categoría</option>
                      <option value="general">General</option>
                      <option value="apariencia">Apariencia</option>
                      <option value="seguridad">Seguridad</option>
                      <option value="notificaciones">Notificaciones</option>
                      <option value="sistema">Sistema</option>
                    </select>
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
                    placeholder="Descripción de la configuración..."
                  />
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="editable"
                    checked={formData.editable}
                    onChange={(e) => setFormData({...formData, editable: e.target.checked})}
                    disabled={modalMode === 'view'}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="editable" className="ml-2 block text-sm text-gray-900">
                    Configuración editable
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

        {/* Sección de Funcionalidades Avanzadas */}
        <div className="mt-8">
          <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">
            Funcionalidades Avanzadas
          </h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Notificaciones Push */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                Notificaciones Push
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Configura las notificaciones push para recibir alertas en tiempo real.
              </p>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <span className="text-sm font-medium">Estado:</span>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {typeof window !== 'undefined' && 'Notification' in window 
                      ? Notification.permission === 'granted' ? 'Activo' : 'Inactivo'
                      : 'No soportado'
                    }
                  </span>
                </div>
                <button
                  onClick={() => {
                    if (typeof window !== 'undefined' && 'Notification' in window) {
                      Notification.requestPermission();
                    }
                  }}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Configurar Notificaciones
                </button>
              </div>
            </div>

            {/* Exportación de Datos */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                Exportación de Datos
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Exporta datos del sistema en diferentes formatos.
              </p>
              <div className="space-y-2">
                <button
                  onClick={() => exportData()}
                  className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  Exportar Configuraciones
                </button>
                <button
                  onClick={() => {
                    toast.success('Funcionalidad en desarrollo');
                  }}
                  className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Exportar Datos del Sistema
                </button>
              </div>
            </div>

            {/* Dashboard Personalizable */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                Dashboard Personalizable
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Personaliza la vista del dashboard según tus necesidades.
              </p>
              <div className="space-y-2">
                <button
                  onClick={() => {
                    toast.success('Funcionalidad en desarrollo');
                  }}
                  className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  Personalizar Dashboard
                </button>
                <button
                  onClick={() => {
                    toast.success('Funcionalidad en desarrollo');
                  }}
                  className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Guardar Layout
                </button>
              </div>
            </div>

            {/* Búsqueda Global */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                Búsqueda Global
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Configura la búsqueda global del sistema.
              </p>
              <div className="space-y-2">
                <button
                  onClick={() => {
                    toast.success('Funcionalidad en desarrollo');
                  }}
                  className="w-full px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                >
                  Configurar Búsqueda
                </button>
                <button
                  onClick={() => {
                    toast.success('Funcionalidad en desarrollo');
                  }}
                  className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Reindexar Datos
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
