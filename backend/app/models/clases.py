"""
Modelo de clases para el sistema de gestión de gimnasio
"""
import uuid
from datetime import datetime, time
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Table, Time, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from app.models.enums import DiaSemana, NivelDificultad

if TYPE_CHECKING:
    from app.models.usuarios import Usuario
    from app.models.empleados import Empleado

# --- Association Table ---
inscripcion_horario = Table(
    'inscripcion_horario',
    Base.metadata,
    Column('usuario_id', String(36), ForeignKey('usuarios.id'), primary_key=True),
    Column('horario_id', String(36), ForeignKey('horarios_clases.id'), primary_key=True)
)

# --- Main Models ---
class Clase(Base):
    """
    Modelo para las plantillas de clases.
    Representa el tipo de clase (ej: "Yoga para principiantes").
    """
    __tablename__ = "clases"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duracion_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    capacidad_maxima: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    nivel: Mapped[NivelDificultad] = mapped_column(Enum(NivelDificultad), nullable=False)
    esta_activa: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata & Sync
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Relationships
    horarios: Mapped[List["HorarioClase"]] = relationship("HorarioClase", back_populates="clase", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Clase {self.nombre}>"

class HorarioClase(Base):
    """
    Modelo para los horarios específicos de una clase.
    Representa una instancia programada de una Clase (ej: "Lunes a las 10:00 en Salón A").
    """
    __tablename__ = "horarios_clases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Scheduling
    dia: Mapped[DiaSemana] = mapped_column(Enum(DiaSemana), nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    salon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Capacity & Status
    capacidad_maxima: Mapped[int] = mapped_column(Integer, default=20)
    plazas_disponibles: Mapped[Optional[int]] = mapped_column(Integer)
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    clase_id: Mapped[str] = mapped_column(String(36), ForeignKey('clases.id'), nullable=False, index=True)
    clase: Mapped["Clase"] = relationship("Clase", back_populates="horarios")
    
    instructor_id: Mapped[str] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=False, index=True)
    instructor: Mapped["Empleado"] = relationship("Empleado")

    participantes: Mapped[List["Usuario"]] = relationship("Usuario", secondary=inscripcion_horario)

    # Metadata & Sync
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)

    def __repr__(self) -> str:
        # Note: Accessing self.clase might cause a lazy load. This is generally acceptable in __repr__ for debugging.
        clase_nombre = self.clase.nombre if self.clase else "N/A"
        dia_semana = self.dia.value if self.dia else "N/A"
        return f"<HorarioClase Clase='{clase_nombre}' Dia='{dia_semana}' Hora='{self.hora_inicio}'>"
