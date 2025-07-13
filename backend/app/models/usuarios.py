"""
Modelo de usuarios para el sistema de gestión de gimnasio
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.asistencias import Asistencia
    from app.models.pagos import Pago
    from app.models.rutinas import Rutina, RutinaUsuario

# Tabla de relación entre usuario y roles (para implementación futura de RBAC)
usuario_rol = Table(
    'usuario_rol',
    Base.metadata,
    Column('usuario_id', String(36), ForeignKey('usuarios.id')),
    Column('rol_id', Integer, ForeignKey('roles.id'))
)

class Rol(Base):
    """Modelo para roles de usuario (RBAC)"""
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relación con usuarios
    usuarios: Mapped[List["Usuario"]] = relationship("Usuario", secondary=usuario_rol, back_populates="roles")
    
    def __repr__(self) -> str:
        return f"<Rol {self.nombre}>"

class Usuario(Base):
    """Modelo principal de usuario"""
    __tablename__ = "usuarios"
    
    # Campos de identificación
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    
    # Información personal
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_nacimiento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    direccion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Información de autenticación
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    salt: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    es_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ultimo_acceso: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Información específica de gimnasio
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    objetivo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    peso_inicial: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    altura: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Campos para sincronización
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    roles: Mapped[List["Rol"]] = relationship("Rol", secondary=usuario_rol, back_populates="usuarios")
    asistencias: Mapped[List["Asistencia"]] = relationship("Asistencia", back_populates="usuario", cascade="all, delete-orphan")
    pagos: Mapped[List["Pago"]] = relationship("Pago", back_populates="usuario", cascade="all, delete-orphan")
    rutinas: Mapped[List["Rutina"]] = relationship(
        "Rutina",
        back_populates="usuario",
        cascade="all, delete-orphan",
        foreign_keys="Rutina.usuario_id",
    )
    rutinas_asignadas: Mapped[List["RutinaUsuario"]] = relationship("RutinaUsuario", back_populates="usuario", cascade="all, delete-orphan")
    
    @hybrid_property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"
    
    @hybrid_property
    def imc(self) -> Optional[float]:
        if self.altura and self.peso_inicial and self.altura > 0:
            peso_kg = self.peso_inicial / 1000
            altura_m = self.altura / 1000
            return round(peso_kg / (altura_m ** 2), 2)
        return None
    
    @hybrid_property
    def edad(self) -> Optional[int]:
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - (
                (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None
    
    def __repr__(self) -> str:
        return f"<Usuario {self.username} ({self.nombre_completo})>"
