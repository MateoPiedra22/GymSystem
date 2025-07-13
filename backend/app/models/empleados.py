"""
Modelo de empleados para el sistema de gestión de gimnasio
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, Any, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Table, Float, Date, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TipoContrato, EstadoEmpleado, Departamento

if TYPE_CHECKING:
    from app.models.usuarios import Usuario

# --- Main Models ---
class Empleado(Base):
    """Modelo principal de empleado"""
    __tablename__ = "empleados"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    numero_empleado: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    telefono_emergencia: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    
    dni: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    numero_seguro_social: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    cargo: Mapped[str] = mapped_column(String(100), nullable=False)
    departamento: Mapped[Departamento] = mapped_column(Enum(Departamento), nullable=False)
    fecha_ingreso: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_salida: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    tipo_contrato: Mapped[TipoContrato] = mapped_column(Enum(TipoContrato), nullable=False)
    estado: Mapped[EstadoEmpleado] = mapped_column(Enum(EstadoEmpleado), default=EstadoEmpleado.ACTIVO)
    
    salario_base: Mapped[float] = mapped_column(Float, nullable=False)
    comisiones_porcentaje: Mapped[float] = mapped_column(Float, default=0.0)
    bonos_meta: Mapped[float] = mapped_column(Float, default=0.0)
    
    horario_entrada: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    horario_salida: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    dias_trabajo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    usuario_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=True)
    
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    foto_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    banco: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    numero_cuenta: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tipo_cuenta: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    certificaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_ultima_evaluacion: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    puntuacion_evaluacion: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    creado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    modificado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    usuario: Mapped[Optional["Usuario"]] = relationship("Usuario", backref="empleado_info", uselist=False)
    asistencias_empleado: Mapped[List["AsistenciaEmpleado"]] = relationship("AsistenciaEmpleado", back_populates="empleado", cascade="all, delete-orphan")
    nominas: Mapped[List["Nomina"]] = relationship("Nomina", back_populates="empleado", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Empleado {self.numero_empleado} - {self.nombre} {self.apellido}>"
    
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"
    
    @property
    def edad(self) -> Optional[int]:
        if self.fecha_nacimiento is not None:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None
    
    @property
    def antiguedad_anos(self) -> int:
        if self.fecha_ingreso is not None:
            today = date.today()
            return today.year - self.fecha_ingreso.year - ((today.month, today.day) < (self.fecha_ingreso.month, self.fecha_ingreso.day))
        return 0

class AsistenciaEmpleado(Base):
    __tablename__ = "asistencias_empleados"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empleado_id: Mapped[str] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=False)
    
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora_entrada: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    hora_salida: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    horas_trabajadas: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    horas_extra: Mapped[float] = mapped_column(Float, default=0.0)
    
    tipo_dia: Mapped[str] = mapped_column(String(20), default="LABORAL")
    estado: Mapped[str] = mapped_column(String(20), default="PRESENTE")
    
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    registrado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empleado: Mapped["Empleado"] = relationship("Empleado", back_populates="asistencias_empleado")
    
    def __repr__(self) -> str:
        return f"<AsistenciaEmpleado {self.empleado_id} - {self.fecha}>"

class Nomina(Base):
    __tablename__ = "nominas"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empleado_id: Mapped[str] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=False)
    
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_pago: Mapped[date] = mapped_column(Date, nullable=False)
    
    salario_base: Mapped[float] = mapped_column(Float, nullable=False)
    horas_extra: Mapped[float] = mapped_column(Float, default=0.0)
    comisiones: Mapped[float] = mapped_column(Float, default=0.0)
    bonos: Mapped[float] = mapped_column(Float, default=0.0)
    otros_ingresos: Mapped[float] = mapped_column(Float, default=0.0)
    
    seguro_social: Mapped[float] = mapped_column(Float, default=0.0)
    impuestos: Mapped[float] = mapped_column(Float, default=0.0)
    prestamos: Mapped[float] = mapped_column(Float, default=0.0)
    otras_deducciones: Mapped[float] = mapped_column(Float, default=0.0)
    
    total_ingresos: Mapped[float] = mapped_column(Float, nullable=False)
    total_deducciones: Mapped[float] = mapped_column(Float, nullable=False)
    salario_neto: Mapped[float] = mapped_column(Float, nullable=False)
    
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE")
    metodo_pago: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    referencia_pago: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    dias_trabajados: Mapped[int] = mapped_column(Integer, nullable=False)
    ausencias: Mapped[int] = mapped_column(Integer, default=0)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    generado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    aprobado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    fecha_generacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_aprobacion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empleado: Mapped["Empleado"] = relationship("Empleado", back_populates="nominas")
    
    def __repr__(self) -> str:
        return f"<Nomina {self.empleado_id} - {self.mes}/{self.anio}>"

class SolicitudVacaciones(Base):
    __tablename__ = "solicitudes_vacaciones"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empleado_id: Mapped[str] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=False)
    
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    dias_solicitados: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE")
    fecha_solicitud: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_respuesta: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    respondido_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    comentarios_respuesta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    dias_disponibles_antes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dias_disponibles_despues: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empleado: Mapped["Empleado"] = relationship("Empleado", backref="solicitudes_vacaciones")
    
    def __repr__(self) -> str:
        return f"<SolicitudVacaciones {self.empleado_id} - {self.fecha_inicio} a {self.fecha_fin}>"

class EvaluacionDesempeno(Base):
    __tablename__ = "evaluaciones_desempeno"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empleado_id: Mapped[str] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=False)
    evaluador_id: Mapped[str] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=False)
    
    fecha_evaluacion: Mapped[date] = mapped_column(Date, nullable=False)
    periodo_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    periodo_fin: Mapped[date] = mapped_column(Date, nullable=False)
    
    puntualidad: Mapped[float] = mapped_column(Float, nullable=False)
    calidad_trabajo: Mapped[float] = mapped_column(Float, nullable=False)
    trabajo_equipo: Mapped[float] = mapped_column(Float, nullable=False)
    comunicacion: Mapped[float] = mapped_column(Float, nullable=False)
    iniciativa: Mapped[float] = mapped_column(Float, nullable=False)
    cumplimiento_objetivos: Mapped[float] = mapped_column(Float, nullable=False)
    
    puntuacion_total: Mapped[float] = mapped_column(Float, nullable=False)
    nivel_desempeno: Mapped[str] = mapped_column(String(20), nullable=False)
    
    fortalezas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    areas_mejora: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objetivos_siguiente_periodo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comentarios_empleado: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    plan_capacitacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_proxima_evaluacion: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    estado: Mapped[str] = mapped_column(String(20), default="BORRADOR")
    fecha_firma_empleado: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fecha_firma_evaluador: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empleado: Mapped["Empleado"] = relationship("Empleado", foreign_keys=[empleado_id], backref="evaluaciones_recibidas")
    evaluador: Mapped["Empleado"] = relationship("Empleado", foreign_keys=[evaluador_id], backref="evaluaciones_realizadas")
    
    def __repr__(self) -> str:
        return f"<EvaluacionDesempeno {self.empleado_id} - {self.fecha_evaluacion}>"

class RegistroCapacitacion(Base):
    __tablename__ = "registros_capacitacion"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empleado_id: Mapped[str] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=False)
    
    nombre_curso: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proveedor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    modalidad: Mapped[str] = mapped_column(String(50), nullable=False)
    
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    horas_duracion: Mapped[int] = mapped_column(Integer, nullable=False)
    
    estado: Mapped[str] = mapped_column(String(20), default="INSCRITO")
    calificacion: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    certificado_obtenido: Mapped[bool] = mapped_column(Boolean, default=False)
    certificado_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    costo_curso: Mapped[float] = mapped_column(Float, default=0.0)
    financiado_por: Mapped[str] = mapped_column(String(50), default="EMPRESA")
    
    objetivos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comentarios: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    registrado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empleado: Mapped["Empleado"] = relationship("Empleado", backref="capacitaciones")
    
    def __repr__(self) -> str:
        return f"<RegistroCapacitacion {self.empleado_id} - {self.nombre_curso}>"

class SolicitudPermiso(Base):
    __tablename__ = "solicitudes_permisos"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empleado_id: Mapped[str] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=False)
    
    tipo_permiso: Mapped[str] = mapped_column(String(50), nullable=False)
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fecha_fin: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    horas_solicitadas: Mapped[float] = mapped_column(Float, nullable=False)
    
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    documentos_adjuntos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE")
    fecha_solicitud: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_respuesta: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    respondido_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    comentarios_respuesta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    es_con_goce_sueldo: Mapped[bool] = mapped_column(Boolean, default=True)
    requiere_reposicion: Mapped[bool] = mapped_column(Boolean, default=False)
    fecha_reposicion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empleado: Mapped["Empleado"] = relationship("Empleado", backref="solicitudes_permisos")
    
    def __repr__(self) -> str:
        return f"<SolicitudPermiso {self.empleado_id} - {self.tipo_permiso}>"

class HorarioTrabajo(Base):
    __tablename__ = "horarios_trabajo"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empleado_id: Mapped[str] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=False)
    
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    es_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    lunes_entrada: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    lunes_salida: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    lunes_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    martes_entrada: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    martes_salida: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    martes_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    miercoles_entrada: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    miercoles_salida: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    miercoles_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    jueves_entrada: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    jueves_salida: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    jueves_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    viernes_entrada: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    viernes_salida: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    viernes_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    sabado_entrada: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    sabado_salida: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    sabado_activo: Mapped[bool] = mapped_column(Boolean, default=False)
    
    domingo_entrada: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    domingo_salida: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    domingo_activo: Mapped[bool] = mapped_column(Boolean, default=False)
    
    horas_semanales: Mapped[float] = mapped_column(Float, nullable=False)
    tolerancia_entrada: Mapped[int] = mapped_column(Integer, default=15)
    tolerancia_salida: Mapped[int] = mapped_column(Integer, default=15)
    
    tiempo_almuerzo: Mapped[int] = mapped_column(Integer, default=60)
    descansos_adicionales: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    tipo_horario: Mapped[str] = mapped_column(String(50), default="FIJO")
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    creado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    aprobado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_aprobacion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empleado: Mapped["Empleado"] = relationship("Empleado", backref="horarios_trabajo")
    
    def __repr__(self) -> str:
        return f"<HorarioTrabajo {self.empleado_id} - {self.fecha_inicio}>"

class ReemplazoEmpleado(Base):
    __tablename__ = "reemplazos_empleados"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empleado_ausente_id: Mapped[str] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=False)
    empleado_reemplazo_id: Mapped[str] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=False)
    
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    motivo_ausencia: Mapped[str] = mapped_column(String(100), nullable=False)
    tareas_asignadas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO")
    es_reemplazo_completo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    pago_adicional: Mapped[float] = mapped_column(Float, default=0.0)
    tipo_compensacion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    autorizado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    fecha_autorizacion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    empleado_ausente: Mapped["Empleado"] = relationship("Empleado", foreign_keys=[empleado_ausente_id], backref="reemplazos_como_ausente")
    empleado_reemplazo: Mapped["Empleado"] = relationship("Empleado", foreign_keys=[empleado_reemplazo_id], backref="reemplazos_realizados")
    
    def __repr__(self) -> str:
        return f"<ReemplazoEmpleado {self.empleado_ausente_id} -> {self.empleado_reemplazo_id}>" 