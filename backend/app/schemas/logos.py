"""
Schemas para gestión de logos personalizados
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, HttpUrl, validator

class LogoBase(BaseModel):
    """Schema base para logos"""
    nombre: str
    descripcion: Optional[str] = None
    activo: bool = True

class LogoCreate(LogoBase):
    """Schema para crear un nuevo logo"""
    # Los campos de archivo se manejan en el upload
    pass

class LogoUpdate(BaseModel):
    """Schema para actualizar un logo"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    es_principal: Optional[bool] = None
    activo: Optional[bool] = None

class LogoResponse(LogoBase):
    """Schema para respuesta de logo"""
    id: int
    archivo_path: str
    url: str
    tipo_archivo: str
    tamaño_kb: int
    dimensiones: Dict[str, int]
    es_principal: bool
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    metadata_adicional: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class LogoUploadResponse(BaseModel):
    """Schema para respuesta de upload de logo"""
    id: int
    nombre: str
    descripcion: Optional[str]
    archivo_path: str
    url: str
    tipo_archivo: str
    tamaño_kb: int
    dimensiones: Dict[str, int]
    mensaje: str = "Logo subido exitosamente"

class LogoPrincipalUpdate(BaseModel):
    """Schema para establecer logo principal"""
    logo_id: int

class LogosListResponse(BaseModel):
    """Schema para respuesta de lista de logos"""
    logos: list[LogoResponse]
    total: int
    logo_principal: Optional[LogoResponse] = None 