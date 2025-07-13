# /backend/app/schemas/asistencias.py
"""
Esquemas Pydantic para la validación y serialización de datos de asistencias
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class TipoAsistencia(str, Enum):
    """Enum para los tipos de asistencia"""
    CLASE = "clase"
    GENERAL = "general"
    ENTRENAMIENTO_PERSONAL = "entrenamiento_personal"


class AsistenciaBase(BaseModel):
    """Esquema base para asistencias"""
    usuario_id: int = Field(..., description="ID del usuario que registra asistencia")
    fecha: datetime = Field(default_factory=datetime.now, description="Fecha y hora de la asistencia")
    tipo: TipoAsistencia = Field(..., description="Tipo de asistencia")
    clase_id: Optional[int] = Field(None, description="ID de la clase (si aplica)")
    notas: Optional[str] = Field(None, max_length=200, description="Notas adicionales sobre la asistencia")
    
    @validator('clase_id')
    def validar_clase_id(cls, v, values):
        """Validar que clase_id esté presente si el tipo es CLASE"""
        if values.get('tipo') == TipoAsistencia.CLASE and v is None:
            raise ValueError('El ID de la clase es requerido para asistencias a clases')
        return v


class AsistenciaCreate(AsistenciaBase):
    """Esquema para crear una nueva asistencia"""
    duracion_minutos: Optional[int] = Field(None, gt=0, le=300, description="Duración de la sesión en minutos")
    
    @validator('duracion_minutos')
    def duracion_positiva(cls, v):
        """Validar que la duración sea positiva cuando se proporciona"""
        if v is not None and v <= 0:
            raise ValueError('La duración debe ser mayor que cero')
        return v


class AsistenciaUpdate(BaseModel):
    """Esquema para actualizar una asistencia existente"""
    fecha: Optional[datetime] = Field(None, description="Fecha y hora de la asistencia")
    tipo: Optional[TipoAsistencia] = Field(None, description="Tipo de asistencia")
    clase_id: Optional[int] = Field(None, description="ID de la clase (si aplica)")
    notas: Optional[str] = Field(None, max_length=200, description="Notas adicionales sobre la asistencia")
    duracion_minutos: Optional[int] = Field(None, gt=0, le=300, description="Duración de la sesión en minutos")
    
    @validator('duracion_minutos')
    def duracion_positiva(cls, v):
        """Validar que la duración sea positiva cuando se proporciona"""
        if v is not None and v <= 0:
            raise ValueError('La duración debe ser mayor que cero')
        return v
    
    @validator('clase_id')
    def validar_clase_id(cls, v, values):
        """Validar que clase_id esté presente si el tipo es CLASE"""
        if values.get('tipo') == TipoAsistencia.CLASE and v is None:
            raise ValueError('El ID de la clase es requerido para asistencias a clases')
        return v


class Asistencia(AsistenciaBase):
    """Esquema para representar una asistencia completa"""
    id: int
    duracion_minutos: Optional[int]
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    class Config:
        orm_mode = True


class AsistenciaResumen(BaseModel):
    """Esquema para resumen de asistencias"""
    id: int
    usuario_id: int
    fecha: datetime
    tipo: TipoAsistencia
    clase_id: Optional[int]
    duracion_minutos: Optional[int]
    
    class Config:
        orm_mode = True


class AsistenciaEstadistica(BaseModel):
    """Esquema para estadísticas de asistencias"""
    total_asistencias: int
    asistencias_por_tipo: dict
    asistencias_por_dia_semana: dict
    asistencias_por_hora: dict
    promedio_duracion: float
    hora_pico: str
    dia_semana_pico: str


class ReporteAsistenciasPeriodo(BaseModel):
    """Esquema para reporte de asistencias por periodo"""
    periodo: str
    fecha_inicio: date
    fecha_fin: date
    total_asistencias: int
    promedio_diario: float
    asistencias_por_tipo: dict
    dias_mas_concurridos: List[dict]
    horas_pico: List[dict]
