"""
Modelo para gestión de logos personalizados del sistema
"""
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base

class LogoPersonalizado(Base):
    """
    Modelo para logos personalizados del sistema
    
    Permite gestionar múltiples logos y establecer uno como principal
    """
    __tablename__ = "logos_personalizados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    archivo_path: Mapped[str] = mapped_column(String(500), nullable=False)
    archivo_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    tipo_archivo: Mapped[str] = mapped_column(String(10), nullable=False)
    tamaño_kb: Mapped[int] = mapped_column(Integer, nullable=False)
    
    dimensiones: Mapped[Optional[Dict[str, int]]] = mapped_column(JSON, nullable=True)
    
    es_principal: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    metadata_adicional: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<LogoPersonalizado(id={self.id}, nombre='{self.nombre}', es_principal={self.es_principal})>"
    
    def get_url(self) -> str:
        """Obtiene la URL completa del logo"""
        if self.archivo_url:
            return str(self.archivo_url)
        return f"/uploads/{str(self.archivo_path)}"
    
    def to_dict(self) -> dict:
        """Convierte el logo a diccionario para serialización"""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "archivo_path": self.archivo_path,
            "url": self.get_url(),
            "tipo_archivo": self.tipo_archivo,
            "tamaño_kb": self.tamaño_kb,
            "dimensiones": self.dimensiones or {"width": 0, "height": 0},
            "es_principal": self.es_principal,
            "activo": self.activo,
            "fecha_creacion": self.creado_en.isoformat() if self.creado_en else None,
            "fecha_actualizacion": self.actualizado_en.isoformat() if self.actualizado_en else None,
            "metadata_adicional": self.metadata_adicional
        } 