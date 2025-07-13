"""
Modelos para gestión de contenido multimedia en ejercicios y rutinas
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Float, JSON, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TipoMultimedia, EstadoMultimedia, CategoriaMultimedia

if TYPE_CHECKING:
    from app.models.usuarios import Usuario
    from app.models.rutinas import Ejercicio, Rutina

class MultimediaEjercicio(Base):
    __tablename__ = "multimedia_ejercicios"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ejercicio_id: Mapped[str] = mapped_column(String(36), ForeignKey('ejercicios.id'), nullable=False)
    
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo: Mapped[TipoMultimedia] = mapped_column(Enum(TipoMultimedia), nullable=False)
    categoria: Mapped[CategoriaMultimedia] = mapped_column(Enum(CategoriaMultimedia), nullable=False)
    
    archivo_path: Mapped[str] = mapped_column(String(500), nullable=False)
    archivo_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    formato: Mapped[str] = mapped_column(String(10), nullable=False)
    tamaño_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    duracion_segundos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dimensiones: Mapped[Optional[Dict[str, int]]] = mapped_column(JSON, nullable=True)
    fps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    orden: Mapped[int] = mapped_column(Integer, default=1)
    es_principal: Mapped[bool] = mapped_column(Boolean, default=False)
    mostrar_en_preview: Mapped[bool] = mapped_column(Boolean, default=True)
    autoplay: Mapped[bool] = mapped_column(Boolean, default=False)
    loop: Mapped[bool] = mapped_column(Boolean, default=False)
    
    etiquetas: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    nivel_dificultad: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    idioma: Mapped[str] = mapped_column(String(10), default="es")
    
    es_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    edad_minima: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    requiere_supervision: Mapped[bool] = mapped_column(Boolean, default=False)
    
    estado: Mapped[EstadoMultimedia] = mapped_column(Enum(EstadoMultimedia), default=EstadoMultimedia.PENDIENTE)
    motivo_rechazo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    subido_por: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=True)
    fecha_subida: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    aprobado_por: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=True)
    fecha_aprobacion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    vistas: Mapped[int] = mapped_column(Integer, default=0)
    descargas: Mapped[int] = mapped_column(Integer, default=0)
    me_gusta: Mapped[int] = mapped_column(Integer, default=0)
    reportes: Mapped[int] = mapped_column(Integer, default=0)
    
    calidad_original: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    versiones_disponibles: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ejercicio: Mapped["Ejercicio"] = relationship("Ejercicio", back_populates="multimedia")
    usuario_subida: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[subido_por])
    usuario_aprobacion: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[aprobado_por])
    anotaciones: Mapped[List["AnotacionMultimedia"]] = relationship("AnotacionMultimedia", back_populates="multimedia")
    
    def __repr__(self) -> str:
        return f"<MultimediaEjercicio {self.nombre} - {self.tipo}>"

class MultimediaRutina(Base):
    __tablename__ = "multimedia_rutinas"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rutina_id: Mapped[str] = mapped_column(String(36), ForeignKey('rutinas.id'), nullable=False)
    
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo: Mapped[TipoMultimedia] = mapped_column(Enum(TipoMultimedia), nullable=False)
    categoria: Mapped[CategoriaMultimedia] = mapped_column(Enum(CategoriaMultimedia), nullable=False)
    
    archivo_path: Mapped[str] = mapped_column(String(500), nullable=False)
    archivo_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    formato: Mapped[str] = mapped_column(String(10), nullable=False)
    tamaño_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    duracion_segundos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dimensiones: Mapped[Optional[Dict[str, int]]] = mapped_column(JSON, nullable=True)
    
    orden: Mapped[int] = mapped_column(Integer, default=1)
    es_principal: Mapped[bool] = mapped_column(Boolean, default=False)
    es_introduccion: Mapped[bool] = mapped_column(Boolean, default=False)
    
    estado: Mapped[EstadoMultimedia] = mapped_column(Enum(EstadoMultimedia), default=EstadoMultimedia.PENDIENTE)
    subido_por: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=True)
    fecha_subida: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    vistas: Mapped[int] = mapped_column(Integer, default=0)
    descargas: Mapped[int] = mapped_column(Integer, default=0)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    rutina: Mapped["Rutina"] = relationship("Rutina", back_populates="multimedia")
    usuario_subida: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[subido_por])
    
    def __repr__(self) -> str:
        return f"<MultimediaRutina {self.nombre} - {self.tipo}>"

class AnotacionMultimedia(Base):
    __tablename__ = "anotaciones_multimedia"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    multimedia_id: Mapped[str] = mapped_column(String(36), ForeignKey('multimedia_ejercicios.id'), nullable=False)
    
    titulo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_anotacion: Mapped[str] = mapped_column(String(20), default="nota")
    
    tiempo_inicio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tiempo_fin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    posicion_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    posicion_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    color: Mapped[str] = mapped_column(String(7), default="#ffff00")
    tamaño_fuente: Mapped[int] = mapped_column(Integer, default=12)
    mostrar_automaticamente: Mapped[bool] = mapped_column(Boolean, default=True)
    
    es_interactiva: Mapped[bool] = mapped_column(Boolean, default=False)
    accion_requerida: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    creado_por: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    multimedia: Mapped["MultimediaEjercicio"] = relationship("MultimediaEjercicio", back_populates="anotaciones")
    creador: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[creado_por])
    
    def __repr__(self) -> str:
        return f"<AnotacionMultimedia {self.titulo or 'Sin título'}>"

class HistorialMultimedia(Base):
    __tablename__ = "historial_multimedia"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id: Mapped[str] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=False)
    multimedia_id: Mapped[str] = mapped_column(String(36), ForeignKey('multimedia_ejercicios.id'), nullable=False)
    
    fecha_acceso: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    duracion_visualizacion: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progreso: Mapped[float] = mapped_column(Float, default=0.0)
    
    dispositivo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    calidad_reproducida: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    le_gusto: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    marco_como_favorito: Mapped[bool] = mapped_column(Boolean, default=False)
    compartio: Mapped[bool] = mapped_column(Boolean, default=False)
    descargo: Mapped[bool] = mapped_column(Boolean, default=False)
    
    ip_acceso: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    usuario: Mapped["Usuario"] = relationship("Usuario")
    multimedia: Mapped["MultimediaEjercicio"] = relationship("MultimediaEjercicio")
    
    def __repr__(self) -> str:
        return f"<HistorialMultimedia {self.usuario_id} - {self.multimedia_id}>"

class ColeccionMultimedia(Base):
    __tablename__ = "colecciones_multimedia"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    es_publica: Mapped[bool] = mapped_column(Boolean, default=False)
    es_destacada: Mapped[bool] = mapped_column(Boolean, default=False)
    color_tema: Mapped[str] = mapped_column(String(7), default="#007bff")
    icono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    categoria_principal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    nivel_recomendado: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    duracion_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    creado_por: Mapped[str] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    visualizaciones: Mapped[int] = mapped_column(Integer, default=0)
    seguidores: Mapped[int] = mapped_column(Integer, default=0)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creador: Mapped["Usuario"] = relationship("Usuario", foreign_keys=[creado_por])
    items: Mapped[List["ItemColeccionMultimedia"]] = relationship("ItemColeccionMultimedia", back_populates="coleccion")
    
    def __repr__(self) -> str:
        return f"<ColeccionMultimedia {self.nombre}>"

class ItemColeccionMultimedia(Base):
    __tablename__ = "items_coleccion_multimedia"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    coleccion_id: Mapped[str] = mapped_column(String(36), ForeignKey('colecciones_multimedia.id'), nullable=False)
    multimedia_id: Mapped[str] = mapped_column(String(36), ForeignKey('multimedia_ejercicios.id'), nullable=False)
    
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    titulo_personalizado: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    descripcion_personalizada: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    obligatorio: Mapped[bool] = mapped_column(Boolean, default=False)
    desbloqueado: Mapped[bool] = mapped_column(Boolean, default=True)
    requisitos: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    agregado_por: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=True)
    fecha_agregado: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    coleccion: Mapped["ColeccionMultimedia"] = relationship("ColeccionMultimedia", back_populates="items")
    multimedia: Mapped["MultimediaEjercicio"] = relationship("MultimediaEjercicio")
    usuario_agregado: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[agregado_por])
    
    def __repr__(self) -> str:
        return f"<ItemColeccionMultimedia {self.coleccion_id} - {self.multimedia_id}>" 