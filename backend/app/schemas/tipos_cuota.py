"""
Schemas para tipos de cuota en la API
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class TipoCuotaBase(BaseModel):
    """Schema base para tipos de cuota"""
    codigo: str = Field(..., min_length=3, max_length=20, description="Código único del tipo de cuota")
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre del tipo de cuota")
    descripcion: Optional[str] = Field(None, max_length=500)
    duracion_dias: int = Field(..., gt=0, description="Duración en días")
    precio: float = Field(..., gt=0, description="Precio regular")
    precio_promocional: Optional[float] = Field(None, gt=0, description="Precio promocional")
    incluye_clases: bool = Field(False, description="Si incluye acceso a clases grupales")
    limite_clases_mes: Optional[int] = Field(None, ge=0, description="Límite de clases por mes (null = ilimitado)")
    acceso_24h: bool = Field(False, description="Si permite acceso 24 horas")
    incluye_evaluacion: bool = Field(True, description="Si incluye evaluación física")
    incluye_rutina: bool = Field(True, description="Si incluye diseño de rutina")
    invitados_mes: int = Field(0, ge=0, description="Número de invitados permitidos al mes")
    edad_minima: Optional[int] = Field(None, ge=0, le=100)
    edad_maxima: Optional[int] = Field(None, ge=0, le=100)
    horario_restringido: bool = Field(False)
    horario_inicio: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    horario_fin: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    beneficios: Optional[List[str]] = Field(None, description="Lista de beneficios adicionales")
    activo: bool = Field(True)
    visible_web: bool = Field(True, description="Si se muestra en la web para venta online")
    requiere_aprobacion: bool = Field(False, description="Si requiere aprobación manual")
    renovacion_automatica: bool = Field(False)
    dias_aviso_vencimiento: int = Field(5, ge=0, description="Días antes para avisar del vencimiento")
    orden_visualizacion: int = Field(100, ge=0)
    
    @field_validator('precio_promocional')
    @classmethod
    def validate_precio_promocional(cls, v: Optional[float], values: Any) -> Optional[float]:
        if v is not None and 'precio' in values.data and v >= values.data['precio']:
            raise ValueError('El precio promocional debe ser menor al precio regular')
        return v
    
    @field_validator('edad_maxima')
    @classmethod
    def validate_edad_maxima(cls, v: Optional[int], values: Any) -> Optional[int]:
        if v is not None and 'edad_minima' in values.data and values.data['edad_minima'] is not None:
            if v < values.data['edad_minima']:
                raise ValueError('La edad máxima debe ser mayor o igual a la edad mínima')
        return v
    
    @field_validator('horario_fin')
    @classmethod
    def validate_horario_fin(cls, v: Optional[str], values: Any) -> Optional[str]:
        if v is not None and 'horario_inicio' in values.data and values.data['horario_inicio'] is not None:
            if v <= values.data['horario_inicio']:
                raise ValueError('El horario de fin debe ser posterior al horario de inicio')
        return v

class TipoCuotaCreate(TipoCuotaBase):
    """Schema para crear tipo de cuota"""
    es_promocion: bool = Field(False)
    fecha_inicio_promo: Optional[datetime] = None
    fecha_fin_promo: Optional[datetime] = None
    
    @field_validator('fecha_fin_promo')
    @classmethod
    def validate_fecha_fin_promo(cls, v: Optional[datetime], values: Any) -> Optional[datetime]:
        if v is not None and 'fecha_inicio_promo' in values.data and values.data['fecha_inicio_promo'] is not None:
            if v <= values.data['fecha_inicio_promo']:
                raise ValueError('La fecha de fin de promoción debe ser posterior a la fecha de inicio')
        return v

class TipoCuotaUpdate(BaseModel):
    """Schema para actualizar tipo de cuota"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    duracion_dias: Optional[int] = Field(None, gt=0)
    precio: Optional[float] = Field(None, gt=0)
    precio_promocional: Optional[float] = Field(None, gt=0)
    incluye_clases: Optional[bool] = None
    limite_clases_mes: Optional[int] = Field(None, ge=0)
    acceso_24h: Optional[bool] = None
    incluye_evaluacion: Optional[bool] = None
    incluye_rutina: Optional[bool] = None
    invitados_mes: Optional[int] = Field(None, ge=0)
    edad_minima: Optional[int] = Field(None, ge=0, le=100)
    edad_maxima: Optional[int] = Field(None, ge=0, le=100)
    horario_restringido: Optional[bool] = None
    horario_inicio: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    horario_fin: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    beneficios: Optional[List[str]] = None
    activo: Optional[bool] = None
    visible_web: Optional[bool] = None
    requiere_aprobacion: Optional[bool] = None
    es_promocion: Optional[bool] = None
    fecha_inicio_promo: Optional[datetime] = None
    fecha_fin_promo: Optional[datetime] = None
    renovacion_automatica: Optional[bool] = None
    dias_aviso_vencimiento: Optional[int] = Field(None, ge=0)
    orden_visualizacion: Optional[int] = Field(None, ge=0)

class TipoCuotaInDB(TipoCuotaBase):
    """Schema para tipo de cuota en base de datos"""
    id: str
    es_promocion: bool = False
    fecha_inicio_promo: Optional[datetime] = None
    fecha_fin_promo: Optional[datetime] = None
    popularidad: int = 0
    fecha_creacion: datetime
    ultima_modificacion: datetime
    creado_por: Optional[str] = None
    modificado_por: Optional[str] = None
    sync_id: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }

class TipoCuotaOut(TipoCuotaInDB):
    """Schema para respuesta de tipo de cuota"""
    duracion_meses: int = Field(..., description="Duración aproximada en meses")
    precio_efectivo: float = Field(..., description="Precio actual considerando promociones")
    descuento_porcentaje: int = Field(..., description="Porcentaje de descuento si hay promoción")

class TipoCuotaList(BaseModel):
    """Schema para lista de tipos de cuota"""
    total: int
    items: List[TipoCuotaOut]

class TipoCuotaStats(BaseModel):
    """Schema para estadísticas de tipos de cuota"""
    total_tipos: int
    tipos_activos: int
    tipos_con_promocion: int
    precio_minimo: float
    precio_maximo: float
    precio_promedio: float
    tipo_mas_popular: Optional[Dict[str, Any]] = None 