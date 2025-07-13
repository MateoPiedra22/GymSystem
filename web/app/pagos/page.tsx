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
import { toast } from 'react-hot-toast'
import { 
  DollarSign, 
  Plus, 
  Search, 
  Filter, 
  Edit2, 
  Trash2, 
  Eye,
  CreditCard,
  TrendingUp,
  CheckCircle,
  XCircle,
  Download,
  Save,
  X,
  Calendar,
  User,
  Receipt
} from 'lucide-react'

// Tipos de datos
interface Pago {
  id: string
  usuario_id: string
  usuario_nombre: string
  monto: number
  metodo_pago: 'Efectivo' | 'Tarjeta' | 'Transferencia' | 'Otro'
  tipo_pago: 'Mensualidad' | 'Clase' | 'Producto' | 'Servicio'
  estado: 'Completado' | 'Pendiente' | 'Cancelado' | 'Reembolsado'
  fecha_pago: string
  fecha_vencimiento?: string
  descripcion?: string
  referencia?: string
  fecha_creacion: string
}

export default function PagosPage() {
  const [pagos, setPagos] = useState<Pago[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'Completado' | 'Pendiente' | 'Cancelado' | 'Reembolsado'>('todos')
  const [filtroMetodo, setFiltroMetodo] = useState<'todos' | 'Efectivo' | 'Tarjeta' | 'Transferencia' | 'Otro'>('todos')
  const [filtroTipo, setFiltroTipo] = useState<'todos' | 'Mensualidad' | 'Clase' | 'Producto' | 'Servicio'>('todos')
  const [selectedPago, setSelectedPago] = useState<Pago | null>(null)
  const [showPagoModal, setShowPagoModal] = useState(false)
  const [modalMode, setModalMode] = useState<'view' | 'edit' | 'create'>('view')
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    usuario_id: '',
    usuario_nombre: '',
    monto: '',
    metodo_pago: 'Efectivo',
    tipo_pago: 'Mensualidad',
    estado: 'Completado',
    fecha_pago: '',
    fecha_vencimiento: '',
    descripcion: '',
    referencia: ''
  })

  // Cargar pagos al montar el componente
  useEffect(() => {
    loadPagos()
  }, [])

  const loadPagos = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.getPagos()
      if (response.data) {
        setPagos(response.data)
      }
    } catch (error) {
      console.error('Error cargando pagos:', error)
      setError('Error al cargar pagos. Intenta de nuevo.')
      toast.error('Error al cargar pagos')
    } finally {
      setLoading(false)
    }
  }

  // Filtros aplicados
  const pagosFiltrados = pagos.filter(pago => {
    const matchSearch = (
      pago.usuario_nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pago.descripcion?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pago.referencia?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    
    const matchEstado = filtroEstado === 'todos' || pago.estado === filtroEstado
    const matchMetodo = filtroMetodo === 'todos' || pago.metodo_pago === filtroMetodo
    const matchTipo = filtroTipo === 'todos' || pago.tipo_pago === filtroTipo
    
    return matchSearch && matchEstado && matchMetodo && matchTipo
  })

  // Estadísticas
  const estadisticas = {
    total: pagos.length,
    completados: pagos.filter(p => p.estado === 'Completado').length,
    pendientes: pagos.filter(p => p.estado === 'Pendiente').length,
    cancelados: pagos.filter(p => p.estado === 'Cancelado').length,
    total_recaudado: pagos.filter(p => p.estado === 'Completado').reduce((sum, p) => sum + p.monto, 0),
    promedio_pago: pagos.length > 0 ? pagos.reduce((sum, p) => sum + p.monto, 0) / pagos.length : 0,
    efectivo: pagos.filter(p => p.metodo_pago === 'Efectivo').length,
    tarjeta: pagos.filter(p => p.metodo_pago === 'Tarjeta').length,
    transferencia: pagos.filter(p => p.metodo_pago === 'Transferencia').length
  }

  const handleCreatePago = () => {
    setSelectedPago(null)
    setModalMode('create')
    setFormData({
      usuario_id: '',
      usuario_nombre: '',
      monto: '',
      metodo_pago: 'Efectivo',
      tipo_pago: 'Mensualidad',
      estado: 'Completado',
      fecha_pago: new Date().toISOString().split('T')[0],
      fecha_vencimiento: '',
      descripcion: '',
      referencia: ''
    })
    setShowPagoModal(true)
  }

  const handleViewPago = (pago: Pago) => {
    setSelectedPago(pago)
    setModalMode('view')
    setFormData({
      usuario_id: pago.usuario_id,
      usuario_nombre: pago.usuario_nombre,
      monto: pago.monto.toString(),
      metodo_pago: pago.metodo_pago,
      tipo_pago: pago.tipo_pago,
      estado: pago.estado,
      fecha_pago: pago.fecha_pago,
      fecha_vencimiento: pago.fecha_vencimiento || '',
      descripcion: pago.descripcion || '',
      referencia: pago.referencia || ''
    })
    setShowPagoModal(true)
  }

  const handleEditPago = (pago: Pago) => {
    setSelectedPago(pago)
    setModalMode('edit')
    setFormData({
      usuario_id: pago.usuario_id,
      usuario_nombre: pago.usuario_nombre,
      monto: pago.monto.toString(),
      metodo_pago: pago.metodo_pago,
      tipo_pago: pago.tipo_pago,
      estado: pago.estado,
      fecha_pago: pago.fecha_pago,
      fecha_vencimiento: pago.fecha_vencimiento || '',
      descripcion: pago.descripcion || '',
      referencia: pago.referencia || ''
    })
    setShowPagoModal(true)
  }

  const handleDeletePago = async (pago: Pago) => {
    if (confirm(`¿Estás seguro de eliminar el pago de ${pago.usuario_nombre}?`)) {
      try {
        await api.deletePago(pago.id)
        toast.success('Pago eliminado correctamente')
        loadPagos() // Recargar lista
      } catch (error) {
        console.error('Error eliminando pago:', error)
        toast.error('Error al eliminar pago')
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (modalMode === 'view') {
      setShowPagoModal(false)
      return
    }

    try {
      setSaving(true)
      setError(null)
      
      const pagoData = {
        usuario_id: formData.usuario_id,
        monto: formData.monto,
        fecha_pago: formData.fecha_pago,
        metodo_pago: formData.metodo_pago,
        descripcion: formData.descripcion,
        estado: formData.estado,
        referencia: formData.referencia
      }

      if (modalMode === 'create') {
        await api.createPago(pagoData)
        toast.success('Pago registrado exitosamente')
      } else {
        if (!selectedPago) {
          throw new Error('No se seleccionó ningún pago para editar')
        }
        await api.updatePago(selectedPago.id, pagoData)
        toast.success('Pago actualizado exitosamente')
      }

      setShowPagoModal(false)
      loadPagos() // Recargar lista
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido'
      setError(errorMessage)
      toast.error(`Error: ${errorMessage}`)
    } finally {
      setSaving(false)
    }
  }

  const cerrarModal = () => {
    setShowPagoModal(false)
    setSelectedPago(null)
    setFormData({
      usuario_id: '',
      usuario_nombre: '',
      monto: '',
      metodo_pago: 'Efectivo',
      tipo_pago: 'Mensualidad',
      estado: 'Completado',
      fecha_pago: '',
      fecha_vencimiento: '',
      descripcion: '',
      referencia: ''
    })
  }

  const exportData = () => {
    const csvContent = [
      ['ID', 'Usuario', 'Monto', 'Método', 'Tipo', 'Estado', 'Fecha Pago', 'Fecha Vencimiento', 'Descripción', 'Referencia'],
      ...pagosFiltrados.map(pago => [
        pago.id,
        pago.usuario_nombre,
        pago.monto.toString(),
        pago.metodo_pago,
        pago.tipo_pago,
        pago.estado,
        pago.fecha_pago,
        pago.fecha_vencimiento || '',
        pago.descripcion || '',
        pago.referencia || ''
      ])
    ].map(row => row.map(field => `"${field}"`).join(',')).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', 'pagos.csv')
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
                💰 Gestión de Pagos
              </h1>
              <p className="page-subtitle">
                Administra los pagos y transacciones del gimnasio
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
                onClick={handleCreatePago}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span>Nuevo Pago</span>
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
                <DollarSign className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Recaudado</p>
                <p className="text-2xl font-bold text-gray-900">${estadisticas.total_recaudado.toLocaleString()}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Completados</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.completados}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Calendar className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Pendientes</p>
                <p className="text-2xl font-bold text-gray-900">{estadisticas.pendientes}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Promedio</p>
                <p className="text-2xl font-bold text-gray-900">${estadisticas.promedio_pago.toFixed(2)}</p>
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
                  placeholder="Buscar pagos..."
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
                <option value="Completado">Completado</option>
                <option value="Pendiente">Pendiente</option>
                <option value="Cancelado">Cancelado</option>
                <option value="Reembolsado">Reembolsado</option>
              </select>
              
              {/* Filtro de método */}
              <select
                value={filtroMetodo}
                onChange={(e) => setFiltroMetodo(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todos los métodos</option>
                <option value="Efectivo">Efectivo</option>
                <option value="Tarjeta">Tarjeta</option>
                <option value="Transferencia">Transferencia</option>
                <option value="Otro">Otro</option>
              </select>
              
              {/* Filtro de tipo */}
              <select
                value={filtroTipo}
                onChange={(e) => setFiltroTipo(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="todos">Todos los tipos</option>
                <option value="Mensualidad">Mensualidad</option>
                <option value="Clase">Clase</option>
                <option value="Producto">Producto</option>
                <option value="Servicio">Servicio</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setSearchTerm('')
                  setFiltroEstado('todos')
                  setFiltroMetodo('todos')
                  setFiltroTipo('todos')
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Limpiar filtros
              </button>
            </div>
          </div>
        </div>

        {/* Tabla de pagos */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {pagosFiltrados.length === 0 ? (
            searchTerm ? (
              <EmptySearch 
                searchTerm={searchTerm} 
              />
            ) : (
              <EmptyData 
                title="No hay pagos registrados"
                description="Comienza registrando el primer pago."
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
                      Monto
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Método
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fecha
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Referencia
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {pagosFiltrados.map((pago) => (
                    <tr key={pago.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {pago.usuario_nombre}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${pago.monto.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          pago.metodo_pago === 'Efectivo' ? 'bg-green-100 text-green-800' :
                          pago.metodo_pago === 'Tarjeta' ? 'bg-blue-100 text-blue-800' :
                          pago.metodo_pago === 'Transferencia' ? 'bg-purple-100 text-purple-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {pago.metodo_pago}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          pago.tipo_pago === 'Mensualidad' ? 'bg-blue-100 text-blue-800' :
                          pago.tipo_pago === 'Clase' ? 'bg-orange-100 text-orange-800' :
                          pago.tipo_pago === 'Producto' ? 'bg-green-100 text-green-800' :
                          'bg-purple-100 text-purple-800'
                        }`}>
                          {pago.tipo_pago}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          pago.estado === 'Completado' ? 'bg-green-100 text-green-800' :
                          pago.estado === 'Pendiente' ? 'bg-yellow-100 text-yellow-800' :
                          pago.estado === 'Cancelado' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {pago.estado}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(pago.fecha_pago).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {pago.referencia || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleViewPago(pago)}
                            className="text-blue-600 hover:text-blue-900 p-1 transition-colors"
                            title="Ver detalles"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleEditPago(pago)}
                            className="text-green-600 hover:text-green-900 p-1 transition-colors"
                            title="Editar"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeletePago(pago)}
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

        {/* Modal de pago */}
        {showPagoModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-semibold text-gray-900">
                  {modalMode === 'create' ? 'Nuevo Pago' : 
                   modalMode === 'edit' ? 'Editar Pago' : 'Detalles de Pago'}
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
                      Monto *
                    </label>
                    <input
                      type="number"
                      value={formData.monto}
                      onChange={(e) => setFormData({...formData, monto: e.target.value})}
                      disabled={modalMode === 'view'}
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Método de Pago
                    </label>
                    <select
                      value={formData.metodo_pago}
                      onChange={(e) => setFormData({...formData, metodo_pago: e.target.value as any})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    >
                      <option value="Efectivo">Efectivo</option>
                      <option value="Tarjeta">Tarjeta</option>
                      <option value="Transferencia">Transferencia</option>
                      <option value="Otro">Otro</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo de Pago
                    </label>
                    <select
                      value={formData.tipo_pago}
                      onChange={(e) => setFormData({...formData, tipo_pago: e.target.value as any})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    >
                      <option value="Mensualidad">Mensualidad</option>
                      <option value="Clase">Clase</option>
                      <option value="Producto">Producto</option>
                      <option value="Servicio">Servicio</option>
                    </select>
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
                      <option value="Completado">Completado</option>
                      <option value="Pendiente">Pendiente</option>
                      <option value="Cancelado">Cancelado</option>
                      <option value="Reembolsado">Reembolsado</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Fecha de Pago *
                    </label>
                    <input
                      type="date"
                      value={formData.fecha_pago}
                      onChange={(e) => setFormData({...formData, fecha_pago: e.target.value})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Fecha de Vencimiento
                    </label>
                    <input
                      type="date"
                      value={formData.fecha_vencimiento}
                      onChange={(e) => setFormData({...formData, fecha_vencimiento: e.target.value})}
                      disabled={modalMode === 'view'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Referencia
                    </label>
                    <input
                      type="text"
                      value={formData.referencia}
                      onChange={(e) => setFormData({...formData, referencia: e.target.value})}
                      disabled={modalMode === 'view'}
                      placeholder="Número de referencia"
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
                    placeholder="Descripción del pago..."
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
