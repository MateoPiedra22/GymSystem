"""
Schemas para empleados en la API
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

# Enums basados en los modelos
class TipoContratoSchema(str, Enum):
    TIEMPO_COMPLETO = "Tiempo Completo"
    MEDIO_TIEMPO = "Medio Tiempo"
    POR_HORAS = "Por Horas"
    TEMPORAL = "Temporal"
    PRACTICAS = "Prácticas"

class EstadoEmpleadoSchema(str, Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"
    VACACIONES = "Vacaciones"
    BAJA_MEDICA = "Baja Médica"
    SUSPENDIDO = "Suspendido"

class DepartamentoSchema(str, Enum):
    ADMINISTRACION = "Administración"
    ENTRENAMIENTO = "Entrenamiento"
    RECEPCION = "Recepción"
    LIMPIEZA = "Limpieza"
    MANTENIMIENTO = "Mantenimiento"
    VENTAS = "Ventas"
    MARKETING = "Marketing"

# Schemas base
class EmpleadoBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefono: str = Field(..., min_length=7, max_length=20)
    telefono_emergencia: Optional[str] = Field(None, min_length=7, max_length=20)
    direccion: str = Field(..., min_length=5, max_length=255)
    fecha_nacimiento: date
    dni: str = Field(..., min_length=8, max_length=20)
    numero_seguro_social: Optional[str] = Field(None, max_length=50)
    cargo: str = Field(..., min_length=3, max_length=100)
    departamento: DepartamentoSchema
    fecha_ingreso: date
    tipo_contrato: TipoContratoSchema
    salario_base: float = Field(..., gt=0)
    comisiones_porcentaje: float = Field(0.0, ge=0, le=100)
    bonos_meta: float = Field(0.0, ge=0)
    horario_entrada: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    horario_salida: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    dias_trabajo: Optional[str] = None
    notas: Optional[str] = None
    banco: Optional[str] = None
    numero_cuenta: Optional[str] = None
    tipo_cuenta: Optional[str] = None
    certificaciones: Optional[List[str]] = None
    
    @validator('fecha_nacimiento')
    def validate_fecha_nacimiento(cls, v):
        if v >= date.today():
            raise ValueError('La fecha de nacimiento debe ser en el pasado')
        edad = (date.today() - v).days / 365.25
        if edad < 18:
            raise ValueError('El empleado debe ser mayor de 18 años')
        if edad > 80:
            raise ValueError('Fecha de nacimiento no válida')
        return v
    
    @validator('fecha_ingreso')
    def validate_fecha_ingreso(cls, v):
        if v > date.today():
            raise ValueError('La fecha de ingreso no puede ser futura')
        return v

class EmpleadoCreate(EmpleadoBase):
    """Schema para crear empleado"""
    usuario_id: Optional[str] = None
    foto_url: Optional[str] = None

class EmpleadoUpdate(BaseModel):
    """Schema para actualizar empleado"""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=7, max_length=20)
    telefono_emergencia: Optional[str] = Field(None, min_length=7, max_length=20)
    direccion: Optional[str] = Field(None, min_length=5, max_length=255)
    fecha_nacimiento: Optional[date] = None
    cargo: Optional[str] = Field(None, min_length=3, max_length=100)
    departamento: Optional[DepartamentoSchema] = None
    tipo_contrato: Optional[TipoContratoSchema] = None
    estado: Optional[EstadoEmpleadoSchema] = None
    salario_base: Optional[float] = Field(None, gt=0)
    comisiones_porcentaje: Optional[float] = Field(None, ge=0, le=100)
    bonos_meta: Optional[float] = Field(None, ge=0)
    horario_entrada: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    horario_salida: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    dias_trabajo: Optional[str] = None
    notas: Optional[str] = None
    banco: Optional[str] = None
    numero_cuenta: Optional[str] = None
    tipo_cuenta: Optional[str] = None
    certificaciones: Optional[List[str]] = None
    fecha_salida: Optional[date] = None
    fecha_ultima_evaluacion: Optional[date] = None
    puntuacion_evaluacion: Optional[float] = Field(None, ge=0, le=10)
    foto_url: Optional[str] = None

class EmpleadoInDB(EmpleadoBase):
    """Schema para empleado en base de datos"""
    id: str
    numero_empleado: str
    estado: EstadoEmpleadoSchema
    fecha_salida: Optional[date] = None
    usuario_id: Optional[str] = None
    foto_url: Optional[str] = None
    fecha_ultima_evaluacion: Optional[date] = None
    puntuacion_evaluacion: Optional[float] = None
    fecha_creacion: datetime
    ultima_modificacion: datetime
    
    class Config:
        from_attributes = True

class EmpleadoOut(EmpleadoInDB):
    """Schema para respuesta de empleado"""
    edad: Optional[int] = None
    antiguedad_anos: Optional[int] = None
    nombre_completo: str
    
    @validator('certificaciones', pre=True)
    def parse_certificaciones(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return []
        return v or []

class EmpleadoList(BaseModel):
    """Schema para lista de empleados"""
    total: int
    items: List[EmpleadoOut]

# Schemas para asistencia de empleados
class AsistenciaEmpleadoBase(BaseModel):
    fecha: date
    hora_entrada: datetime
    tipo_dia: str = Field("LABORAL", pattern="^(LABORAL|FERIADO|DESCANSO)$")
    estado: str = Field("PRESENTE", pattern="^(PRESENTE|AUSENTE|TARDE|PERMISO|VACACIONES)$")
    observaciones: Optional[str] = None

class AsistenciaEmpleadoCreate(AsistenciaEmpleadoBase):
    """Schema para registrar entrada de empleado"""
    empleado_id: str

class AsistenciaEmpleadoUpdate(BaseModel):
    """Schema para actualizar asistencia (registrar salida)"""
    hora_salida: datetime
    observaciones: Optional[str] = None

class AsistenciaEmpleadoInDB(AsistenciaEmpleadoBase):
    """Schema para asistencia en base de datos"""
    id: str
    empleado_id: str
    hora_salida: Optional[datetime] = None
    horas_trabajadas: Optional[float] = None
    horas_extra: float = 0.0
    registrado_por: Optional[str] = None
    fecha_registro: datetime
    ultima_modificacion: datetime
    
    class Config:
        from_attributes = True

class AsistenciaEmpleadoOut(AsistenciaEmpleadoInDB):
    """Schema para respuesta de asistencia"""
    empleado: Optional['EmpleadoOut'] = None

# Schemas para nómina
class NominaBase(BaseModel):
    mes: int = Field(..., ge=1, le=12)
    anio: int = Field(..., ge=2020, le=2100)
    fecha_pago: date
    salario_base: float = Field(..., gt=0)
    horas_extra: float = Field(0.0, ge=0)
    comisiones: float = Field(0.0, ge=0)
    bonos: float = Field(0.0, ge=0)
    otros_ingresos: float = Field(0.0, ge=0)
    seguro_social: float = Field(0.0, ge=0)
    impuestos: float = Field(0.0, ge=0)
    prestamos: float = Field(0.0, ge=0)
    otras_deducciones: float = Field(0.0, ge=0)
    dias_trabajados: int = Field(..., ge=0, le=31)
    ausencias: int = Field(0, ge=0)
    observaciones: Optional[str] = None

class NominaCreate(NominaBase):
    """Schema para crear nómina"""
    empleado_id: str
    metodo_pago: Optional[str] = Field(None, pattern="^(TRANSFERENCIA|EFECTIVO|CHEQUE)$")
    referencia_pago: Optional[str] = None

class NominaUpdate(BaseModel):
    """Schema para actualizar nómina"""
    estado: Optional[str] = Field(None, pattern="^(PENDIENTE|PAGADA|CANCELADA)$")
    metodo_pago: Optional[str] = Field(None, pattern="^(TRANSFERENCIA|EFECTIVO|CHEQUE)$")
    referencia_pago: Optional[str] = None
    fecha_aprobacion: Optional[datetime] = None
    aprobado_por: Optional[str] = None

class NominaInDB(NominaBase):
    """Schema para nómina en base de datos"""
    id: str
    empleado_id: str
    total_ingresos: float
    total_deducciones: float
    salario_neto: float
    estado: str = "PENDIENTE"
    metodo_pago: Optional[str] = None
    referencia_pago: Optional[str] = None
    generado_por: Optional[str] = None
    aprobado_por: Optional[str] = None
    fecha_generacion: datetime
    fecha_aprobacion: Optional[datetime] = None
    ultima_modificacion: datetime
    
    class Config:
        from_attributes = True

class NominaOut(NominaInDB):
    """Schema para respuesta de nómina"""
    empleado: Optional['EmpleadoOut'] = None

# Schemas para solicitudes de vacaciones
class SolicitudVacacionesBase(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    motivo: Optional[str] = None
    
    @validator('fecha_fin')
    def validate_fechas(cls, v, values):
        if 'fecha_inicio' in values and v <= values['fecha_inicio']:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v

class SolicitudVacacionesCreate(SolicitudVacacionesBase):
    empleado_id: str

class SolicitudVacacionesUpdate(BaseModel):
    estado: Optional[str] = Field(None, pattern="^(PENDIENTE|APROBADA|RECHAZADA|CANCELADA)$")
    comentarios_respuesta: Optional[str] = None

class SolicitudVacacionesInDB(SolicitudVacacionesBase):
    id: str
    empleado_id: str
    dias_solicitados: int
    estado: str = "PENDIENTE"
    fecha_solicitud: datetime
    fecha_respuesta: Optional[datetime] = None
    respondido_por: Optional[str] = None
    comentarios_respuesta: Optional[str] = None
    dias_disponibles_antes: Optional[int] = None
    dias_disponibles_despues: Optional[int] = None
    ultima_modificacion: datetime
    
    class Config:
        from_attributes = True

class SolicitudVacacionesOut(SolicitudVacacionesInDB):
    empleado: Optional['EmpleadoOut'] = None

# Schemas para evaluaciones de desempeño
class EvaluacionDesempenoBase(BaseModel):
    fecha_evaluacion: date
    periodo_inicio: date
    periodo_fin: date
    puntualidad: float = Field(..., ge=1, le=10)
    calidad_trabajo: float = Field(..., ge=1, le=10)
    trabajo_equipo: float = Field(..., ge=1, le=10)
    comunicacion: float = Field(..., ge=1, le=10)
    iniciativa: float = Field(..., ge=1, le=10)
    cumplimiento_objetivos: float = Field(..., ge=1, le=10)
    fortalezas: Optional[str] = None
    areas_mejora: Optional[str] = None
    objetivos_siguiente_periodo: Optional[str] = None
    plan_capacitacion: Optional[str] = None
    fecha_proxima_evaluacion: Optional[date] = None

class EvaluacionDesempenoCreate(EvaluacionDesempenoBase):
    empleado_id: str
    evaluador_id: str

class EvaluacionDesempenoUpdate(BaseModel):
    comentarios_empleado: Optional[str] = None
    estado: Optional[str] = Field(None, pattern="^(BORRADOR|ENVIADA|FIRMADA|ARCHIVADA)$")
    fecha_firma_empleado: Optional[datetime] = None

class EvaluacionDesempenoInDB(EvaluacionDesempenoBase):
    id: str
    empleado_id: str
    evaluador_id: str
    puntuacion_total: float
    nivel_desempeno: str
    comentarios_empleado: Optional[str] = None
    estado: str = "BORRADOR"
    fecha_firma_empleado: Optional[datetime] = None
    fecha_firma_evaluador: Optional[datetime] = None
    fecha_creacion: datetime
    ultima_modificacion: datetime
    
    class Config:
        from_attributes = True

class EvaluacionDesempenoOut(EvaluacionDesempenoInDB):
    empleado: Optional['EmpleadoOut'] = None
    evaluador: Optional['EmpleadoOut'] = None

# Schemas para capacitaciones
class RegistroCapacitacionBase(BaseModel):
    nombre_curso: str = Field(..., min_length=3, max_length=255)
    descripcion: Optional[str] = None
    proveedor: Optional[str] = None
    modalidad: str = Field(..., pattern="^(PRESENCIAL|VIRTUAL|MIXTA)$")
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    horas_duracion: int = Field(..., gt=0)
    costo_curso: float = Field(0.0, ge=0)
    financiado_por: str = Field("EMPRESA", pattern="^(EMPRESA|EMPLEADO|MIXTO)$")
    objetivos: Optional[str] = None

class RegistroCapacitacionCreate(RegistroCapacitacionBase):
    empleado_id: str

class RegistroCapacitacionUpdate(BaseModel):
    estado: Optional[str] = Field(None, pattern="^(INSCRITO|EN_CURSO|COMPLETADO|ABANDONADO)$")
    calificacion: Optional[float] = Field(None, ge=0, le=10)
    certificado_obtenido: Optional[bool] = None
    certificado_url: Optional[str] = None
    comentarios: Optional[str] = None

class RegistroCapacitacionInDB(RegistroCapacitacionBase):
    id: str
    empleado_id: str
    estado: str = "INSCRITO"
    calificacion: Optional[float] = None
    certificado_obtenido: bool = False
    certificado_url: Optional[str] = None
    comentarios: Optional[str] = None
    registrado_por: Optional[str] = None
    fecha_registro: datetime
    ultima_modificacion: datetime
    
    class Config:
        from_attributes = True

class RegistroCapacitacionOut(RegistroCapacitacionInDB):
    empleado: Optional['EmpleadoOut'] = None

# Schemas para solicitudes de permisos
class SolicitudPermisoBase(BaseModel):
    tipo_permiso: str = Field(..., pattern="^(MEDICO|PERSONAL|FAMILIAR|ESTUDIO|OTRO)$")
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    horas_solicitadas: float = Field(..., gt=0)
    motivo: str = Field(..., min_length=10)
    documentos_adjuntos: Optional[List[str]] = None
    es_con_goce_sueldo: bool = True
    requiere_reposicion: bool = False
    fecha_reposicion: Optional[datetime] = None

class SolicitudPermisoCreate(SolicitudPermisoBase):
    empleado_id: str

class SolicitudPermisoUpdate(BaseModel):
    estado: Optional[str] = Field(None, pattern="^(PENDIENTE|APROBADA|RECHAZADA|CANCELADA)$")
    comentarios_respuesta: Optional[str] = None
    es_con_goce_sueldo: Optional[bool] = None
    requiere_reposicion: Optional[bool] = None
    fecha_reposicion: Optional[datetime] = None

class SolicitudPermisoInDB(SolicitudPermisoBase):
    id: str
    empleado_id: str
    estado: str = "PENDIENTE"
    fecha_solicitud: datetime
    fecha_respuesta: Optional[datetime] = None
    respondido_por: Optional[str] = None
    comentarios_respuesta: Optional[str] = None
    ultima_modificacion: datetime
    
    class Config:
        from_attributes = True

class SolicitudPermisoOut(SolicitudPermisoInDB):
    empleado: Optional['EmpleadoOut'] = None

# Schemas para horarios de trabajo
class HorarioTrabajoBase(BaseModel):
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    es_activo: bool = True
    lunes_entrada: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    lunes_salida: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    lunes_activo: bool = True
    martes_entrada: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    martes_salida: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    martes_activo: bool = True
    miercoles_entrada: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    miercoles_salida: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    miercoles_activo: bool = True
    jueves_entrada: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    jueves_salida: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    jueves_activo: bool = True
    viernes_entrada: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    viernes_salida: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    viernes_activo: bool = True
    sabado_entrada: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    sabado_salida: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    sabado_activo: bool = False
    domingo_entrada: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    domingo_salida: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    domingo_activo: bool = False
    horas_semanales: float = Field(..., gt=0, le=168)
    tolerancia_entrada: int = Field(15, ge=0, le=60)
    tolerancia_salida: int = Field(15, ge=0, le=60)
    tiempo_almuerzo: int = Field(60, ge=0, le=180)
    descansos_adicionales: Optional[str] = None
    tipo_horario: str = Field("FIJO", pattern="^(FIJO|FLEXIBLE|ROTATIVO)$")
    observaciones: Optional[str] = None

class HorarioTrabajoCreate(HorarioTrabajoBase):
    empleado_id: str

class HorarioTrabajoUpdate(BaseModel):
    fecha_fin: Optional[date] = None
    es_activo: Optional[bool] = None
    observaciones: Optional[str] = None

class HorarioTrabajoInDB(HorarioTrabajoBase):
    id: str
    empleado_id: str
    creado_por: Optional[str] = None
    aprobado_por: Optional[str] = None
    fecha_creacion: datetime
    fecha_aprobacion: Optional[datetime] = None
    ultima_modificacion: datetime
    
    class Config:
        from_attributes = True

class HorarioTrabajoOut(HorarioTrabajoInDB):
    empleado: Optional['EmpleadoOut'] = None

# Schemas para reemplazos
class ReemplazoEmpleadoBase(BaseModel):
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    motivo_ausencia: str = Field(..., min_length=3, max_length=100)
    tareas_asignadas: Optional[str] = None
    observaciones: Optional[str] = None
    es_reemplazo_completo: bool = True
    pago_adicional: float = Field(0.0, ge=0)
    tipo_compensacion: Optional[str] = Field(None, pattern="^(HORAS_EXTRA|BONO|PORCENTAJE)$")

class ReemplazoEmpleadoCreate(ReemplazoEmpleadoBase):
    empleado_ausente_id: str
    empleado_reemplazo_id: str

class ReemplazoEmpleadoUpdate(BaseModel):
    fecha_fin: Optional[date] = None
    estado: Optional[str] = Field(None, pattern="^(ACTIVO|FINALIZADO|CANCELADO)$")
    observaciones: Optional[str] = None

class ReemplazoEmpleadoInDB(ReemplazoEmpleadoBase):
    id: str
    empleado_ausente_id: str
    empleado_reemplazo_id: str
    estado: str = "ACTIVO"
    autorizado_por: Optional[str] = None
    fecha_autorizacion: Optional[datetime] = None
    fecha_creacion: datetime
    ultima_modificacion: datetime
    
    class Config:
        from_attributes = True

class ReemplazoEmpleadoOut(ReemplazoEmpleadoInDB):
    empleado_ausente: Optional['EmpleadoOut'] = None
    empleado_reemplazo: Optional['EmpleadoOut'] = None

# Para evitar referencias circulares
EmpleadoOut.model_rebuild()
AsistenciaEmpleadoOut.model_rebuild()
NominaOut.model_rebuild()
SolicitudVacacionesOut.model_rebuild()
EvaluacionDesempenoOut.model_rebuild()
RegistroCapacitacionOut.model_rebuild()
SolicitudPermisoOut.model_rebuild()
HorarioTrabajoOut.model_rebuild()
ReemplazoEmpleadoOut.model_rebuild() 