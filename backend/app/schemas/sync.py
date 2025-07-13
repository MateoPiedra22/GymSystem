"""
Schemas para sincronización de datos entre plataformas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import enum

class TipoEntidad(str, enum.Enum):
    USUARIO = "usuario"
    CLASE = "clase"
    ASISTENCIA = "asistencia"
    PAGO = "pago"
    RUTINA = "rutina"
    EJERCICIO = "ejercicio"

class EstadoSincronizacion(str, enum.Enum):
    PENDIENTE = "pendiente"
    SINCRONIZADO = "sincronizado"
    ERROR = "error"
    CONFLICTO = "conflicto"

class SyncItemBase(BaseModel):
    """Schema base para un ítem de sincronización"""
    id: str
    tipo_entidad: TipoEntidad
    cliente_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    datos: Dict[str, Any]

class SyncItemCreate(SyncItemBase):
    """Schema para crear un nuevo ítem de sincronización"""
    pass

class SyncItemUpdate(BaseModel):
    """Schema para actualizar un ítem de sincronización"""
    estado: EstadoSincronizacion
    mensaje_error: Optional[str] = None

class SyncItemResponse(SyncItemBase):
    """Schema para respuesta de sincronización"""
    sync_id: str
    estado: EstadoSincronizacion
    ultima_sincronizacion: Optional[datetime] = None
    mensaje_error: Optional[str] = None
    
    class Config:
        orm_mode = True

class SyncBatchRequest(BaseModel):
    """Schema para solicitud de sincronización por lotes"""
    items: List[SyncItemCreate]
    cliente_id: str
    cliente_version: str
    timestamp_ultimo_sync: Optional[datetime] = None

class SyncBatchResponse(BaseModel):
    """Schema para respuesta de sincronización por lotes"""
    items_procesados: int
    items_con_error: int
    items_conflicto: int
    resultados: List[SyncItemResponse]
    servidor_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True

class SyncEstadoResponse(BaseModel):
    """Schema para estado de sincronización"""
    estado: str = "online"
    version_api: str
    ultimo_sync: Optional[datetime] = None
    pendientes_servidor: int = 0
    
    class Config:
        orm_mode = True
