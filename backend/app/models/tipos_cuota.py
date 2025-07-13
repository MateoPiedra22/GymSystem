"""
Modelo de tipos de cuota para el sistema de gestión de gimnasio
"""
import uuid
from datetime import datetime
from typing import Optional, List, Any, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Float, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.pagos import Pago

class TipoCuota(Base):
    """Modelo para los diferentes tipos de cuotas/membresías del gimnasio"""
    __tablename__ = "tipos_cuota"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    duracion_dias: Mapped[int] = mapped_column(Integer, nullable=False)
    precio: Mapped[float] = mapped_column(Float, nullable=False)
    precio_promocional: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    incluye_clases: Mapped[bool] = mapped_column(Boolean, default=False)
    limite_clases_mes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    acceso_24h: Mapped[bool] = mapped_column(Boolean, default=False)
    incluye_evaluacion: Mapped[bool] = mapped_column(Boolean, default=True)
    incluye_rutina: Mapped[bool] = mapped_column(Boolean, default=True)
    invitados_mes: Mapped[int] = mapped_column(Integer, default=0)
    
    edad_minima: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    edad_maxima: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    horario_restringido: Mapped[bool] = mapped_column(Boolean, default=False)
    horario_inicio: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    horario_fin: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    
    beneficios: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    visible_web: Mapped[bool] = mapped_column(Boolean, default=True)
    requiere_aprobacion: Mapped[bool] = mapped_column(Boolean, default=False)
    
    es_promocion: Mapped[bool] = mapped_column(Boolean, default=False)
    fecha_inicio_promo: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fecha_fin_promo: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    renovacion_automatica: Mapped[bool] = mapped_column(Boolean, default=False)
    dias_aviso_vencimiento: Mapped[int] = mapped_column(Integer, default=5)
    
    orden_visualizacion: Mapped[int] = mapped_column(Integer, default=100)
    popularidad: Mapped[int] = mapped_column(Integer, default=0)
    
    creado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    modificado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    pagos: Mapped[List["Pago"]] = relationship("Pago", back_populates="tipo_cuota")
    
    def __repr__(self) -> str:
        return f"<TipoCuota {self.codigo} - {self.nombre}>" 