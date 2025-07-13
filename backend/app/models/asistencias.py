"""
Modelo de asistencias para el sistema de gestión de gimnasio
"""
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.usuarios import Usuario
    from app.models.clases import Clase

class Asistencia(Base):
    """Modelo para registrar las asistencias de usuarios al gimnasio"""
    __tablename__ = "asistencias"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Datos de asistencia
    fecha_hora_entrada: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_hora_salida: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Referencias
    usuario_id: Mapped[str] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=False)
    clase_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('clases.id'), nullable=True)
    
    # Notas y observaciones
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Sincronización
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="asistencias")
    clase: Mapped[Optional["Clase"]] = relationship("Clase")
    
    def __repr__(self) -> str:
        return f"<Asistencia {self.usuario_id} - {self.fecha_hora_entrada}>"
