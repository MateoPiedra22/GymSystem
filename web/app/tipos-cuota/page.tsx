'use client'
export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react';
import { TipoCuota, FormularioTipoCuota, ListResponse, Filtros } from '../types';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';

export default function TiposCuotaPage() {
  const [tiposCuota, setTiposCuota] = useState<TipoCuota[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tipoSeleccionado, setTipoSeleccionado] = useState<TipoCuota | null>(null);
  const [mostrarModal, setMostrarModal] = useState(false);
  const [modoEdicion, setModoEdicion] = useState(false);
  const [filtros, setFiltros] = useState<Filtros>({});
  const [paginacion, setPaginacion] = useState({ page: 1, limit: 10, total: 0, pages: 0 });
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Estados para el formulario
  const [formulario, setFormulario] = useState<FormularioTipoCuota>({
    codigo: '',
    nombre: '',
    descripcion: '',
    duracion_dias: 30,
    precio: 0,
    precio_promocional: undefined,
    incluye_clases: true,
    limite_clases_mes: undefined,
    acceso_24h: false,
    incluye_evaluacion: true,
    incluye_rutina: true,
    invitados_mes: 0,
    edad_minima: undefined,
    edad_maxima: undefined,
    horario_restringido: false,
    horario_inicio: undefined,
    horario_fin: undefined,
    beneficios: [],
    activo: true,
    visible_web: true,
    requiere_aprobacion: false,
    renovacion_automatica: true,
    dias_aviso_vencimiento: 7,
    orden_visualizacion: 1
  });

  // Cargar tipos de cuota
  const cargarTiposCuota = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Filtrar propiedades undefined de filtros
      const filtrosLimpios = Object.fromEntries(
        Object.entries(filtros).filter(([_, value]) => value !== undefined)
      );
      
      const params = new URLSearchParams({
        page: paginacion.page.toString(),
        limit: paginacion.limit.toString(),
        ...filtrosLimpios
      });

      const response = await fetch(`/api/tipos-cuota?${params}`);
      if (!response.ok) throw new Error('Error al cargar tipos de cuota');
      
      const data: ListResponse<TipoCuota> = await response.json();
      setTiposCuota(data.items);
      setPaginacion({
        page: data.page,
        limit: data.limit,
        total: data.total,
        pages: data.pages
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
      console.error(`Error al cargar tipos de cuota: ${err instanceof Error ? err.message : 'Error desconocido'}`);
    } finally {
      setLoading(false);
    }
  };

  // Crear o actualizar tipo de cuota
  const guardarTipoCuota = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      const url = modoEdicion ? `/api/tipos-cuota/${tipoSeleccionado?.id}` : '/api/tipos-cuota';
      const method = modoEdicion ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formulario)
      });

      if (!response.ok) throw new Error('Error al guardar tipo de cuota');

      await cargarTiposCuota();
      cerrarModal();
      console.log(modoEdicion ? 'Tipo de cuota actualizado exitosamente' : 'Tipo de cuota creado exitosamente');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar');
      console.error(`Error al guardar tipo de cuota: ${err instanceof Error ? err.message : 'Error desconocido'}`);
    } finally {
      setSaving(false);
    }
  };

  // Eliminar tipo de cuota
  const eliminarTipoCuota = async (id: string) => {
    if (!confirm('¿Estás seguro de que deseas eliminar este tipo de cuota?')) return;

    try {
      setDeleting(id);
      const response = await fetch(`/api/tipos-cuota/${id}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Error al eliminar tipo de cuota');
      
      await cargarTiposCuota();
      console.log('Tipo de cuota eliminado exitosamente');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al eliminar');
      console.error(`Error al eliminar tipo de cuota: ${err instanceof Error ? err.message : 'Error desconocido'}`);
    } finally {
      setDeleting(null);
    }
  };

  // Toggle estado activo
  const toggleActivo = async (id: string, activo: boolean) => {
    try {
      const response = await fetch(`/api/tipos-cuota/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ activo: !activo })
      });

      if (!response.ok) throw new Error('Error al actualizar estado');
      
      await cargarTiposCuota();
      console.log('Estado actualizado exitosamente');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar');
      console.error(`Error al actualizar estado: ${err instanceof Error ? err.message : 'Error desconocido'}`);
    }
  };

  // Abrir modal para crear
  const abrirModalCrear = () => {
    setFormulario({
      codigo: '',
      nombre: '',
      descripcion: '',
      duracion_dias: 30,
      precio: 0,
      precio_promocional: undefined,
      incluye_clases: true,
      limite_clases_mes: undefined,
      acceso_24h: false,
      incluye_evaluacion: true,
      incluye_rutina: true,
      invitados_mes: 0,
      edad_minima: undefined,
      edad_maxima: undefined,
      horario_restringido: false,
      horario_inicio: undefined,
      horario_fin: undefined,
      beneficios: [],
      activo: true,
      visible_web: true,
      requiere_aprobacion: false,
      renovacion_automatica: true,
      dias_aviso_vencimiento: 7,
      orden_visualizacion: 1
    });
    setTipoSeleccionado(null);
    setModoEdicion(false);
    setMostrarModal(true);
  };

  // Abrir modal para editar
  const abrirModalEditar = (tipo: TipoCuota) => {
    setFormulario({
      codigo: tipo.codigo,
      nombre: tipo.nombre,
      descripcion: tipo.descripcion || '',
      duracion_dias: tipo.duracion_dias,
      precio: tipo.precio,
      precio_promocional: tipo.precio_promocional,
      incluye_clases: tipo.incluye_clases,
      limite_clases_mes: tipo.limite_clases_mes,
      acceso_24h: tipo.acceso_24h,
      incluye_evaluacion: tipo.incluye_evaluacion,
      incluye_rutina: tipo.incluye_rutina,
      invitados_mes: tipo.invitados_mes,
      edad_minima: tipo.edad_minima,
      edad_maxima: tipo.edad_maxima,
      horario_restringido: tipo.horario_restringido,
      horario_inicio: tipo.horario_inicio,
      horario_fin: tipo.horario_fin,
      beneficios: tipo.beneficios || [],
      activo: tipo.activo,
      visible_web: tipo.visible_web,
      requiere_aprobacion: tipo.requiere_aprobacion,
      renovacion_automatica: tipo.renovacion_automatica,
      dias_aviso_vencimiento: tipo.dias_aviso_vencimiento,
      orden_visualizacion: tipo.orden_visualizacion
    });
    setTipoSeleccionado(tipo);
    setModoEdicion(true);
    setMostrarModal(true);
  };

  // Cerrar modal
  const cerrarModal = () => {
    setMostrarModal(false);
    setTipoSeleccionado(null);
    setModoEdicion(false);
  };

  // Formatear precio
  const formatearPrecio = (precio: number) => {
    return new Intl.NumberFormat('es-PE', {
      style: 'currency',
      currency: 'PEN'
    }).format(precio);
  };

  // Badge para promoción
  const BadgePromocion = ({ esPromocion }: { esPromocion: boolean }) => {
    if (!esPromocion) return null;
    return (
      <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
        Promoción
      </span>
    );
  };

  // Badge para estado
  const BadgeEstado = ({ activo }: { activo: boolean }) => {
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
        activo ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
      }`}>
        {activo ? 'Activo' : 'Inactivo'}
      </span>
    );
  };

  useEffect(() => {
    cargarTiposCuota();
  }, [filtros, paginacion.page]);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Tipos de Cuota</h1>
              <p className="text-gray-600 mt-2">Gestiona los planes de membresía del gimnasio</p>
            </div>
            <button
              onClick={abrirModalCrear}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Nuevo Tipo de Cuota
            </button>
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <input
              type="text"
              placeholder="Buscar tipos de cuota..."
              value={filtros.busqueda || ''}
              onChange={(e) => setFiltros({ ...filtros, busqueda: e.target.value })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <select
              value={filtros.activo?.toString() || ''}
              onChange={(e) => setFiltros({ 
                ...filtros, 
                activo: e.target.value === '' ? undefined : e.target.value === 'true' 
              })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Todos los estados</option>
              <option value="true">Activos</option>
              <option value="false">Inactivos</option>
            </select>
            <select
              value={filtros.tipo || ''}
              onChange={(e) => setFiltros({ ...filtros, tipo: e.target.value || undefined })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Todos los tipos</option>
              <option value="promocion">En promoción</option>
              <option value="premium">Premium</option>
              <option value="basico">Básico</option>
            </select>
            <button
              onClick={() => setFiltros({})}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Limpiar Filtros
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex">
              <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="ml-3 text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Grid de tipos de cuota */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tiposCuota.map((tipo) => (
            <div key={tipo.id} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{tipo.nombre}</h3>
                      <BadgePromocion esPromocion={tipo.es_promocion} />
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{tipo.codigo}</p>
                    {tipo.descripcion && (
                      <p className="text-sm text-gray-600 mb-3">{tipo.descripcion}</p>
                    )}
                  </div>
                  <BadgeEstado activo={tipo.activo} />
                </div>

                {/* Precio */}
                <div className="mb-4">
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold text-gray-900">
                      {formatearPrecio(tipo.precio_efectivo)}
                    </span>
                    {tipo.precio_promocional && tipo.precio_promocional < tipo.precio && (
                      <span className="text-lg text-gray-500 line-through">
                        {formatearPrecio(tipo.precio)}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">
                    Por {tipo.duracion_meses} {tipo.duracion_meses === 1 ? 'mes' : 'meses'}
                  </p>
                </div>

                {/* Características */}
                <div className="space-y-2 mb-4">
                  <div className="flex items-center text-sm">
                    <svg className={`w-4 h-4 mr-2 ${tipo.incluye_clases ? 'text-green-500' : 'text-gray-400'}`} fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span className={tipo.incluye_clases ? 'text-gray-700' : 'text-gray-400'}>
                      Clases grupales {tipo.limite_clases_mes ? `(${tipo.limite_clases_mes}/mes)` : '(ilimitadas)'}
                    </span>
                  </div>
                  
                  <div className="flex items-center text-sm">
                    <svg className={`w-4 h-4 mr-2 ${tipo.acceso_24h ? 'text-green-500' : 'text-gray-400'}`} fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span className={tipo.acceso_24h ? 'text-gray-700' : 'text-gray-400'}>
                      Acceso 24 horas
                    </span>
                  </div>

                  <div className="flex items-center text-sm">
                    <svg className={`w-4 h-4 mr-2 ${tipo.incluye_evaluacion ? 'text-green-500' : 'text-gray-400'}`} fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span className={tipo.incluye_evaluacion ? 'text-gray-700' : 'text-gray-400'}>
                      Evaluación física
                    </span>
                  </div>

                  <div className="flex items-center text-sm">
                    <svg className={`w-4 h-4 mr-2 ${tipo.incluye_rutina ? 'text-green-500' : 'text-gray-400'}`} fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span className={tipo.incluye_rutina ? 'text-gray-700' : 'text-gray-400'}>
                      Rutina personalizada
                    </span>
                  </div>

                  {tipo.invitados_mes > 0 && (
                    <div className="flex items-center text-sm">
                      <svg className="w-4 h-4 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      <span className="text-gray-700">
                        {tipo.invitados_mes} invitado(s) por mes
                      </span>
                    </div>
                  )}
                </div>

                {/* Beneficios adicionales */}
                {tipo.beneficios && tipo.beneficios.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Beneficios adicionales:</h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {tipo.beneficios.map((beneficio, index) => (
                        <li key={index} className="flex items-center">
                          <svg className="w-3 h-3 mr-2 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          {beneficio}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Estadísticas */}
                <div className="flex justify-between items-center text-sm text-gray-600 mb-4">
                  <span>Popularidad: {tipo.popularidad}%</span>
                  <span>Orden: {tipo.orden_visualizacion}</span>
                </div>

                {/* Acciones */}
                <div className="flex justify-between items-center pt-4 border-t border-gray-200">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => abrirModalEditar(tipo)}
                      className="text-blue-600 hover:text-blue-900 p-1"
                      title="Editar"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => eliminarTipoCuota(tipo.id)}
                      className="text-red-600 hover:text-red-900 p-1"
                      title="Eliminar"
                      disabled={deleting === tipo.id}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        {deleting === tipo.id ? (
                          <LoadingSpinner size="sm" />
                        ) : (
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        )}
                      </svg>
                    </button>
                  </div>
                  <button
                    onClick={() => toggleActivo(tipo.id, tipo.activo)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      tipo.activo 
                        ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                    disabled={saving}
                  >
                    {saving ? (
                      <>
                        <LoadingSpinner size="sm" />
                        <span>Actualizando...</span>
                      </>
                    ) : (
                      tipo.activo ? 'Desactivar' : 'Activar'
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Paginación */}
        {paginacion.pages > 1 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 mt-6 rounded-lg shadow-sm">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setPaginacion({ ...paginacion, page: paginacion.page - 1 })}
                disabled={paginacion.page === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Anterior
              </button>
              <button
                onClick={() => setPaginacion({ ...paginacion, page: paginacion.page + 1 })}
                disabled={paginacion.page === paginacion.pages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Siguiente
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Mostrando <span className="font-medium">{(paginacion.page - 1) * paginacion.limit + 1}</span> a{' '}
                  <span className="font-medium">
                    {Math.min(paginacion.page * paginacion.limit, paginacion.total)}
                  </span>{' '}
                  de <span className="font-medium">{paginacion.total}</span> tipos de cuota
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  {Array.from({ length: paginacion.pages }, (_, i) => i + 1).map((page) => (
                    <button
                      key={page}
                      onClick={() => setPaginacion({ ...paginacion, page })}
                      className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                        page === paginacion.page
                          ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                          : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  ))}
                </nav>
              </div>
            </div>
          </div>
        )}

        {/* Modal para crear/editar tipo de cuota */}
        {mostrarModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  {modoEdicion ? 'Editar Tipo de Cuota' : 'Nuevo Tipo de Cuota'}
                </h3>
                
                <form onSubmit={guardarTipoCuota} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Información básica */}
                    <div className="space-y-4">
                      <h4 className="text-md font-medium text-gray-900">Información Básica</h4>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Código</label>
                        <input
                          type="text"
                          required
                          value={formulario.codigo}
                          onChange={(e) => setFormulario({ ...formulario, codigo: e.target.value })}
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700">Nombre</label>
                        <input
                          type="text"
                          required
                          value={formulario.nombre}
                          onChange={(e) => setFormulario({ ...formulario, nombre: e.target.value })}
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700">Descripción</label>
                        <textarea
                          value={formulario.descripcion}
                          onChange={(e) => setFormulario({ ...formulario, descripcion: e.target.value })}
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          rows={3}
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Duración (días)</label>
                          <input
                            type="number"
                            min="1"
                            required
                            value={formulario.duracion_dias}
                            onChange={(e) => setFormulario({ ...formulario, duracion_dias: parseInt(e.target.value) || 1 })}
                            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Orden</label>
                          <input
                            type="number"
                            min="1"
                            value={formulario.orden_visualizacion}
                            onChange={(e) => setFormulario({ ...formulario, orden_visualizacion: parseInt(e.target.value) || 1 })}
                            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Precio (PEN)</label>
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            required
                            value={formulario.precio}
                            onChange={(e) => setFormulario({ ...formulario, precio: parseFloat(e.target.value) || 0 })}
                            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Precio Promocional (PEN)</label>
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={formulario.precio_promocional || ''}
                            onChange={(e) => setFormulario({ ...formulario, precio_promocional: e.target.value ? parseFloat(e.target.value) : undefined })}
                            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Configuración */}
                    <div className="space-y-4">
                      <h4 className="text-md font-medium text-gray-900">Configuración</h4>
                      
                      <div className="space-y-3">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formulario.incluye_clases}
                            onChange={(e) => setFormulario({ ...formulario, incluye_clases: e.target.checked })}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">Incluye clases grupales</span>
                        </label>

                        {formulario.incluye_clases && (
                          <div className="ml-6">
                            <label className="block text-sm font-medium text-gray-700">Límite de clases por mes</label>
                            <input
                              type="number"
                              min="0"
                              placeholder="Ilimitado"
                              value={formulario.limite_clases_mes || ''}
                              onChange={(e) => setFormulario({ ...formulario, limite_clases_mes: e.target.value ? parseInt(e.target.value) : undefined })}
                              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            />
                          </div>
                        )}

                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formulario.acceso_24h}
                            onChange={(e) => setFormulario({ ...formulario, acceso_24h: e.target.checked })}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">Acceso 24 horas</span>
                        </label>

                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formulario.incluye_evaluacion}
                            onChange={(e) => setFormulario({ ...formulario, incluye_evaluacion: e.target.checked })}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">Incluye evaluación física</span>
                        </label>

                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formulario.incluye_rutina}
                            onChange={(e) => setFormulario({ ...formulario, incluye_rutina: e.target.checked })}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">Incluye rutina personalizada</span>
                        </label>

                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formulario.activo}
                            onChange={(e) => setFormulario({ ...formulario, activo: e.target.checked })}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">Activo</span>
                        </label>

                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formulario.visible_web}
                            onChange={(e) => setFormulario({ ...formulario, visible_web: e.target.checked })}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">Visible en web</span>
                        </label>

                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formulario.renovacion_automatica}
                            onChange={(e) => setFormulario({ ...formulario, renovacion_automatica: e.target.checked })}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">Renovación automática</span>
                        </label>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700">Invitados por mes</label>
                        <input
                          type="number"
                          min="0"
                          value={formulario.invitados_mes}
                          onChange={(e) => setFormulario({ ...formulario, invitados_mes: parseInt(e.target.value) || 0 })}
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700">Días de aviso antes del vencimiento</label>
                        <input
                          type="number"
                          min="1"
                          value={formulario.dias_aviso_vencimiento}
                          onChange={(e) => setFormulario({ ...formulario, dias_aviso_vencimiento: parseInt(e.target.value) || 7 })}
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Botones */}
                  <div className="flex justify-end space-x-3 pt-4 border-t">
                    <button
                      type="button"
                      onClick={cerrarModal}
                      className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      disabled={saving}
                    >
                      {saving ? (
                        <>
                          <LoadingSpinner size="sm" />
                          <span>Guardando...</span>
                        </>
                      ) : (
                        modoEdicion ? 'Actualizar' : 'Crear'
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 