# /backend/app/schemas/clases.py
"""
Esquemas Pydantic para la validación y serialización de datos de clases y horarios
"""

from datetime import datetime, time
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum

# Re-usamos el enum del modelo para consistencia, pero en schemas es str
class DiaSemana(str, Enum):
    LUNES = "Lunes"
    MARTES = "Martes"
    MIERCOLES = "Miércoles"
    JUEVES = "Jueves"
    VIERNES = "Viernes"
    SABADO = "Sábado"
    DOMINGO = "Domingo"

class NivelDificultad(str, Enum):
    PRINCIPIANTE = "principiante"
    INTERMEDIO = "intermedio"
    AVANZADO = "avanzado"


# --- Horario Schemas ---

class HorarioClaseBase(BaseModel):
    """Esquema base para horarios de clases"""
    dia: DiaSemana = Field(..., description="Día de la semana")
    hora_inicio: time = Field(..., description="Hora de inicio de la clase")
    salon: Optional[str] = Field(None, min_length=1, max_length=50, description="Salón o ubicación de la clase")
    instructor_id: str = Field(..., description="ID del empleado que es instructor")
    capacidad_maxima: int = Field(..., gt=0, le=100, description="Capacidad máxima de participantes")

class HorarioClaseCreate(HorarioClaseBase):
    """Esquema para crear un nuevo horario de clase"""
    clase_id: str = Field(..., description="ID de la clase a la que pertenece este horario")

class HorarioClaseUpdate(BaseModel):
    """Esquema para actualizar un horario de clase existente"""
    dia: Optional[DiaSemana] = Field(None, description="Día de la semana")
    hora_inicio: Optional[time] = Field(None, description="Hora de inicio de la clase")
    salon: Optional[str] = Field(None, min_length=1, max_length=50, description="Salón o ubicación de la clase")
    instructor_id: Optional[str] = Field(None, description="ID del instructor")
    capacidad_maxima: Optional[int] = Field(None, gt=0, le=100, description="Capacidad máxima")
    esta_activo: Optional[bool] = Field(None, description="Si el horario está activo")

class HorarioClase(HorarioClaseBase):
    """Esquema para representar un horario de clase completo para salida"""
    id: str
    clase_id: str
    esta_activo: bool
    plazas_disponibles: int
    fecha_creacion: datetime
    
    class Config:
        orm_mode = True

# --- Clase Schemas ---

class ClaseBase(BaseModel):
    """Esquema base para clases (plantillas)"""
    nombre: str = Field(..., min_length=3, max_length=50, description="Nombre de la clase")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción detallada de la clase")
    duracion_minutos: int = Field(..., gt=0, le=240, description="Duración de la clase en minutos")
    capacidad_maxima: Optional[int] = Field(None, gt=0, le=200, description="Capacidad recomendada de la clase")
    nivel: NivelDificultad = Field(NivelDificultad.PRINCIPIANTE, description="Nivel de dificultad")

class ClaseCreate(ClaseBase):
    """Esquema para crear una nueva clase"""
    pass

class ClaseUpdate(BaseModel):
    """Esquema para actualizar una clase existente"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=500)
    duracion_minutos: Optional[int] = Field(None, gt=0, le=240)
    nivel: Optional[NivelDificultad] = Field(None)
    esta_activa: Optional[bool] = Field(None)

class Clase(BaseModel):
    """Esquema para representar una clase completa con sus horarios"""
    id: str
    capacidad_maxima: Optional[int] = None
    esta_activa: bool
    fecha_creacion: datetime
    horarios: List[HorarioClase] = []
    
    class Config:
        orm_mode = True

# --- Otros Schemas ---

class ClaseResumen(BaseModel):
    """Esquema para resumen de clases en listados"""
    id: str
    nombre: str
    nivel: NivelDificultad
    duracion_minutos: int
    esta_activa: bool
    
    class Config:
        orm_mode = True

class ClaseConAsistencias(Clase):
    """Esquema para clase con información de asistencias"""
    total_asistencias: int
    porcentaje_ocupacion: float
    asistencias_por_dia: dict
