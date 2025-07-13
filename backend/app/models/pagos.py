"""
Modelo de pagos para el sistema de gestión de gimnasio
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Float, Enum, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from app.models.enums import MetodoPago, EstadoPago, ConceptoPago

if TYPE_CHECKING:
    from app.models.usuarios import Usuario
    from app.models.tipos_cuota import TipoCuota
    from app.models.empleados import Empleado
    from app.models.clases import Clase

class Pago(Base):
    """Modelo para pagos realizados por usuarios"""
    __tablename__ = "pagos"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    numero_recibo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    
    monto: Mapped[float] = mapped_column(Float, nullable=False)
    monto_pagado: Mapped[float] = mapped_column(Float, default=0.0)
    fecha_pago: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_vencimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    metodo_pago: Mapped[MetodoPago] = mapped_column(Enum(MetodoPago), nullable=False)
    estado: Mapped[EstadoPago] = mapped_column(Enum(EstadoPago), default=EstadoPago.PENDIENTE)
    concepto: Mapped[ConceptoPago] = mapped_column(Enum(ConceptoPago), nullable=False)
    
    usuario_id: Mapped[str] = mapped_column(String(36), ForeignKey('usuarios.id'), nullable=False)
    tipo_cuota_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('tipos_cuota.id'), nullable=True)
    empleado_registro_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('empleados.id'), nullable=True)
    
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referencia: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    comprobante_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    fecha_inicio_membresia: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_fin_membresia: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    descuento_monto: Mapped[float] = mapped_column(Float, default=0.0)
    descuento_porcentaje: Mapped[float] = mapped_column(Float, default=0.0)
    impuesto_monto: Mapped[float] = mapped_column(Float, default=0.0)
    monto_final: Mapped[float] = mapped_column(Float, nullable=False)
    
    dias_mora: Mapped[int] = mapped_column(Integer, default=0)
    cargo_mora: Mapped[float] = mapped_column(Float, default=0.0)
    
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    motivo_cancelacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    creado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    modificado_por: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="pagos")
    tipo_cuota: Mapped[Optional["TipoCuota"]] = relationship("TipoCuota", back_populates="pagos")
    empleado_registro: Mapped[Optional["Empleado"]] = relationship("Empleado", foreign_keys=[empleado_registro_id])
    detalles_pago: Mapped[List["DetallePago"]] = relationship("DetallePago", back_populates="pago", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Pago {self.numero_recibo} - {self.usuario_id} - {self.monto}>"

class DetallePago(Base):
    """Modelo para detalles de items en un pago"""
    __tablename__ = "detalles_pago"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pago_id: Mapped[str] = mapped_column(String(36), ForeignKey('pagos.id'), nullable=False)
    
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, default=1)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    
    clase_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('clases.id'), nullable=True)
    producto_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    sync_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ultima_modificacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    pago: Mapped["Pago"] = relationship("Pago", back_populates="detalles_pago")
    clase: Mapped[Optional["Clase"]] = relationship("Clase")
    
    def __repr__(self) -> str:
        return f"<DetallePago {self.descripcion} - {self.subtotal}>"
