"""
Modelo de rutinas para el sistema de gestión de gimnasio
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Table, Float, Enum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TipoEjercicio, NivelDificultad

if TYPE_CHECKING:
    from app.models.usuarios import Usuario
    from app.models.multimedia import MultimediaEjercicio, MultimediaRutina

rutina_ejercicio = Table(
    'rutina_ejercicio',
    Base.metadata,
    Column('rutina_id', String(36), ForeignKey('rutinas.id')),
    Column('ejercicio_id', String(36), ForeignKey('ejercicios.id'))
)

class Ejercicio(Base):
    __tablename__ = "ejercicios"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    tipo: Mapped[TipoEjercicio] = mapped_column(Enum(TipoEjercicio), nullable=False)
    dificultad: Mapped[NivelDificultad] = mapped_column(Enum(NivelDificultad), nullable=False)
    musculos_trabajados: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    imagen_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    rutinas: Mapped[List["Rutina"]] = relationship("Rutina", secondary=rutina_ejercicio, back_populates="ejercicios")
    multimedia: Mapped[List["MultimediaEjercicio"]] = relationship("MultimediaEjercicio", back_populates="ejercicio")
    
    def __repr__(self) -> str:
        return f"<Ejercicio {self.nombre} - {self.tipo.value}>"

class Rutina(Base):
    __tablename__ = "rutinas"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    nivel: Mapped[NivelDificultad] = mapped_column(Enum(NivelDificultad), nullable=False)
    duracion_estimada: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    calorias_estimadas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_inicio: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fecha_fin: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    dias_semana: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    objetivo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    usuario_id: Mapped[str] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=False)
    creador_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    usuario: Mapped["Usuario"] = relationship("Usuario", foreign_keys=[usuario_id], back_populates="rutinas")
    creador: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[creador_id])
    ejercicios: Mapped[List["Ejercicio"]] = relationship("Ejercicio", secondary=rutina_ejercicio, back_populates="rutinas")
    multimedia: Mapped[List["MultimediaRutina"]] = relationship("MultimediaRutina", back_populates="rutina")
    
    def __repr__(self) -> str:
        return f"<Rutina {self.nombre} para {self.usuario_id}>"

class RutinaUsuario(Base):
    __tablename__ = "rutinas_usuarios"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    usuario_id: Mapped[str] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=False)
    rutina_id: Mapped[str] = mapped_column(String(36), ForeignKey('rutinas.id'), nullable=False)
    
    fecha_asignacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_inicio: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fecha_fin: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="Asignada")
    
    modificaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="rutinas_asignadas")
    rutina: Mapped["Rutina"] = relationship("Rutina")
    
    def __repr__(self) -> str:
        return f"<RutinaUsuario {self.rutina_id} - {self.usuario_id}>"

class ProgresoRutina(Base):
    __tablename__ = "progreso_rutinas"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    usuario_id: Mapped[str] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=False)
    rutina_id: Mapped[str] = mapped_column(String(36), ForeignKey('rutinas.id'), nullable=False)
    ejercicio_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('ejercicios.id'), nullable=True)
    
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completado: Mapped[bool] = mapped_column(Boolean, default=False)
    
    series: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    repeticiones: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    peso: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duracion: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    dificultad_percibida: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sensacion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    usuario: Mapped["Usuario"] = relationship("Usuario")
    rutina: Mapped["Rutina"] = relationship("Rutina")
    ejercicio: Mapped[Optional["Ejercicio"]] = relationship("Ejercicio")
    
    def __repr__(self) -> str:
        return f"<ProgresoRutina {self.usuario_id} - {self.rutina_id} - {self.fecha}>"

class ConfiguracionEstilos(Base):
    __tablename__ = "configuracion_estilos"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    nombre_tema: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    
    color_primario: Mapped[str] = mapped_column(String(7), nullable=False)
    color_secundario: Mapped[str] = mapped_column(String(7), nullable=False)
    color_acento: Mapped[str] = mapped_column(String(7), nullable=False)
    color_fondo: Mapped[str] = mapped_column(String(7), nullable=False)
    color_texto: Mapped[str] = mapped_column(String(7), nullable=False)
    color_exito: Mapped[str] = mapped_column(String(7), default="#28a745")
    color_advertencia: Mapped[str] = mapped_column(String(7), default="#ffc107")
    color_error: Mapped[str] = mapped_column(String(7), default="#dc3545")
    color_info: Mapped[str] = mapped_column(String(7), default="#17a2b8")
    
    fuente_principal: Mapped[str] = mapped_column(String(100), default="Inter, sans-serif")
    fuente_secundaria: Mapped[str] = mapped_column(String(100), default="Roboto, sans-serif")
    tamaño_fuente_base: Mapped[str] = mapped_column(String(10), default="16px")
    
    espaciado_pequeno: Mapped[str] = mapped_column(String(10), default="8px")
    espaciado_medio: Mapped[str] = mapped_column(String(10), default="16px")
    espaciado_grande: Mapped[str] = mapped_column(String(10), default="24px")
    radio_borde: Mapped[str] = mapped_column(String(10), default="8px")
    
    sombra_sutil: Mapped[str] = mapped_column(String(100), default="0 2px 4px rgba(0,0,0,0.1)")
    sombra_media: Mapped[str] = mapped_column(String(100), default="0 4px 8px rgba(0,0,0,0.15)")
    sombra_intensa: Mapped[str] = mapped_column(String(100), default="0 8px 16px rgba(0,0,0,0.2)")
    
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    logo_pequeno_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    css_personalizado: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    configuracion_avanzada: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    es_tema_predeterminado: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    aplicar_a_web: Mapped[bool] = mapped_column(Boolean, default=True)
    aplicar_a_cliente: Mapped[bool] = mapped_column(Boolean, default=True)
    
    publico: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ConfiguracionEstilos {self.nombre_tema}>"
