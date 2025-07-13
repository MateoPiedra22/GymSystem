/**
 * Tipos TypeScript para toda la aplicación
 */

// Usuario
export interface Usuario {
  id: string;
  username: string;
  email: string;
  nombre: string;
  apellido: string;
  fecha_nacimiento?: string;
  telefono?: string;
  direccion?: string;
  esta_activo: boolean;
  es_admin: boolean;
  fecha_registro: string;
  ultimo_acceso?: string;
  fecha_inicio?: string;
  objetivo?: string;
  notas?: string;
  peso_inicial?: number;
  altura?: number;
}

// Empleado
export interface Empleado {
  id: string;
  numero_empleado: string;
  nombre: string;
  apellido: string;
  email: string;
  telefono: string;
  telefono_emergencia?: string;
  direccion: string;
  fecha_nacimiento: string;
  dni: string;
  numero_seguro_social?: string;
  cargo: string;
  departamento: 'Administración' | 'Entrenamiento' | 'Recepción' | 'Limpieza' | 'Mantenimiento' | 'Ventas' | 'Marketing';
  fecha_ingreso: string;
  fecha_salida?: string;
  tipo_contrato: 'Tiempo Completo' | 'Medio Tiempo' | 'Por Horas' | 'Temporal' | 'Prácticas';
  estado: 'Activo' | 'Inactivo' | 'Vacaciones' | 'Baja Médica' | 'Suspendido';
  salario_base: number;
  comisiones_porcentaje: number;
  bonos_meta: number;
  horario_entrada?: string;
  horario_salida?: string;
  dias_trabajo?: string;
  usuario_id?: string;
  notas?: string;
  foto_url?: string;
  banco?: string;
  numero_cuenta?: string;
  tipo_cuenta?: string;
  certificaciones?: string[];
  fecha_ultima_evaluacion?: string;
  puntuacion_evaluacion?: number;
  fecha_creacion: string;
  ultima_modificacion: string;
  edad?: number;
  antiguedad_anos?: number;
  nombre_completo: string;
}

// Tipo de Cuota
export interface TipoCuota {
  id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  duracion_dias: number;
  duracion_meses: number;
  precio: number;
  precio_promocional?: number;
  precio_efectivo: number;
  descuento_porcentaje: number;
  incluye_clases: boolean;
  limite_clases_mes?: number;
  acceso_24h: boolean;
  incluye_evaluacion: boolean;
  incluye_rutina: boolean;
  invitados_mes: number;
  edad_minima?: number;
  edad_maxima?: number;
  horario_restringido: boolean;
  horario_inicio?: string;
  horario_fin?: string;
  beneficios?: string[];
  activo: boolean;
  visible_web: boolean;
  requiere_aprobacion: boolean;
  es_promocion: boolean;
  fecha_inicio_promo?: string;
  fecha_fin_promo?: string;
  renovacion_automatica: boolean;
  dias_aviso_vencimiento: number;
  orden_visualizacion: number;
  popularidad: number;
  fecha_creacion: string;
  ultima_modificacion: string;
}

// Clase
export interface Clase {
  id: string;
  nombre: string;
  descripcion?: string;
  dia: string;
  hora_inicio: string;
  hora_fin: string;
  duracion_minutos: number;
  capacidad_maxima: number;
  plazas_disponibles: number;
  esta_activa: boolean;
  requiere_reserva: boolean;
  instructor_id?: string;
  instructor?: Usuario;
}

// Pago
export interface Pago {
  id: string;
  numero_recibo: string;
  monto: number;
  monto_pagado: number;
  monto_final: number;
  fecha_pago: string;
  fecha_vencimiento?: string;
  metodo_pago: 'Efectivo' | 'Transferencia' | 'Tarjeta Débito' | 'Tarjeta Crédito' | 'PayPal' | 'Yape' | 'Plin' | 'Otro';
  estado: 'Pendiente' | 'Pagado' | 'Parcial' | 'Vencido' | 'Cancelado' | 'Reembolsado';
  concepto: 'Membresía' | 'Clase Individual' | 'Producto' | 'Servicio Adicional' | 'Multa' | 'Otro';
  usuario_id: string;
  tipo_cuota_id?: string;
  empleado_registro_id?: string;
  descripcion?: string;
  referencia?: string;
  comprobante_url?: string;
  fecha_inicio_membresia?: string;
  fecha_fin_membresia?: string;
  descuento_monto: number;
  descuento_porcentaje: number;
  impuesto_monto: number;
  dias_mora: number;
  cargo_mora: number;
  notas?: string;
  motivo_cancelacion?: string;
  saldo_pendiente: number;
  fecha_creacion: string;
  ultima_modificacion: string;
  usuario?: Usuario;
  tipo_cuota?: TipoCuota;
  empleado_registro?: Empleado;
}

// Asistencia
export interface Asistencia {
  id: string;
  usuario_id: string;
  clase_id?: string;
  fecha: string;
  hora_entrada: string;
  hora_salida?: string;
  tipo: 'clase' | 'gimnasio' | 'otro';
  observaciones?: string;
  usuario?: Usuario;
  clase?: Clase;
}

// Asistencia de Empleado
export interface AsistenciaEmpleado {
  id: string;
  empleado_id: string;
  fecha: string;
  hora_entrada: string;
  hora_salida?: string;
  horas_trabajadas?: number;
  horas_extra: number;
  tipo_dia: 'LABORAL' | 'FERIADO' | 'DESCANSO';
  estado: 'PRESENTE' | 'AUSENTE' | 'TARDE' | 'PERMISO' | 'VACACIONES';
  observaciones?: string;
  empleado?: Empleado;
}

// Ejercicio
export interface Ejercicio {
  id: string;
  nombre: string;
  descripcion?: string;
  tipo: string;
  dificultad: string;
  musculos_trabajados?: string;
  imagen_url?: string;
  video_url?: string;
}

// Rutina
export interface Rutina {
  id: string;
  nombre: string;
  descripcion?: string;
  objetivo: string;
  nivel: 'principiante' | 'intermedio' | 'avanzado';
  duracion_semanas: number;
  dias_por_semana: number;
  usuario_id?: string;
  instructor_id?: string;
  esta_activa: boolean;
  fecha_creacion: string;
  usuario?: Usuario;
  instructor?: Usuario;
}

// ProgresoRutina
export interface ProgresoRutina {
  id: string;
  usuario_id: string;
  rutina_id: string;
  ejercicio_id?: string;
  fecha: string;
  completado: boolean;
  series?: number;
  repeticiones?: number;
  peso?: number;
  duracion?: number;
  dificultad_percibida?: number;
  sensacion?: string;
  notas?: string;
}

// SyncStatus
export interface SyncStatus {
  connected: boolean;
  last_sync?: string;
  pending_changes: number;
  peer_count: number;
  node_id: string;
}

// Dashboard Data
export interface DashboardData {
  usuarios_totales: number;
  usuarios_activos: number;
  clases_hoy: number;
  ingresos_mes: number;
  ingresos_hoy: number;
  asistencias_hoy: number;
  usuarios_nuevos_mes: number;
  ocupacion_promedio: number;
  pagos_pendientes: number;
  empleados_activos: number;
  estadisticas_semanales: {
    fecha: string;
    usuarios: number;
    ingresos: number;
    asistencias: number;
  }[];
  top_clases: {
    nombre: string;
    asistencias: number;
    ocupacion: number;
  }[];
  distribucion_pagos: {
    metodo: string;
    cantidad: number;
    monto: number;
  }[];
  tendencia_ingresos: {
    mes: string;
    ingresos: number;
    meta: number;
  }[];
}

// KPIs
export interface KPI {
  id: string;
  titulo: string;
  valor: number | string;
  unidad?: string;
  tendencia?: 'up' | 'down' | 'stable';
  porcentaje_cambio?: number;
  descripcion?: string;
  icono?: string;
  color?: 'green' | 'red' | 'blue' | 'yellow' | 'purple' | 'orange';
}

// Filtros y paginación
export interface Filtros {
  busqueda?: string;
  estado?: string;
  fecha_inicio?: string;
  fecha_fin?: string;
  departamento?: string;
  tipo?: string;
  activo?: boolean;
}

export interface PaginationData {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// Configuración
export interface ConfiguracionSistema {
  nombre_gimnasio: string;
  direccion: string;
  telefono: string;
  email: string;
  horario_apertura: string;
  horario_cierre: string;
  dias_operacion: string[];
  moneda: string;
  zona_horaria: string;
  idioma: string;
  tema: 'light' | 'dark';
  notificaciones_email: boolean;
  backup_automatico: boolean;
  mantenimiento: boolean;
}

// Estado de sincronización
export interface EstadoSync {
  ultimo_sync: string;
  conectado: boolean;
  cambios_pendientes: number;
  errores: string[];
  en_progreso: boolean;
}

// Formularios
export interface FormularioEmpleado {
  nombre: string;
  apellido: string;
  email: string;
  telefono: string;
  telefono_emergencia?: string;
  direccion: string;
  fecha_nacimiento: string;
  dni: string;
  numero_seguro_social?: string;
  cargo: string;
  departamento: string;
  fecha_ingreso: string;
  tipo_contrato: string;
  salario_base: number;
  comisiones_porcentaje: number;
  bonos_meta: number;
  horario_entrada?: string;
  horario_salida?: string;
  dias_trabajo?: string;
  notas?: string;
  banco?: string;
  numero_cuenta?: string;
  tipo_cuenta?: string;
  certificaciones?: string[];
}

export interface FormularioTipoCuota {
  codigo: string;
  nombre: string;
  descripcion?: string;
  duracion_dias: number;
  precio: number;
  precio_promocional?: number;
  incluye_clases: boolean;
  limite_clases_mes?: number;
  acceso_24h: boolean;
  incluye_evaluacion: boolean;
  incluye_rutina: boolean;
  invitados_mes: number;
  edad_minima?: number;
  edad_maxima?: number;
  horario_restringido: boolean;
  horario_inicio?: string;
  horario_fin?: string;
  beneficios?: string[];
  activo: boolean;
  visible_web: boolean;
  requiere_aprobacion: boolean;
  renovacion_automatica: boolean;
  dias_aviso_vencimiento: number;
  orden_visualizacion: number;
}

// Reportes
export interface ReporteData {
  titulo: string;
  periodo: string;
  datos: any[];
  graficos: GraficoData[];
  kpis: KPI[];
  exportable: boolean;
}

export interface GraficoData {
  tipo: 'line' | 'bar' | 'pie' | 'doughnut' | 'area';
  titulo: string;
  datos: {
    labels: string[];
    datasets: {
      label: string;
      data: number[];
      backgroundColor?: string | string[];
      borderColor?: string;
      borderWidth?: number;
    }[];
  };
  opciones?: any;
} 