# /backend/app/schemas/rutinas.py
"""
Esquemas Pydantic para la validación y serialización de datos de rutinas y ejercicios
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.models.enums import TipoEjercicio, NivelDificultad

class EjercicioBase(BaseModel):
    """Esquema base para ejercicios"""
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre del ejercicio")
    descripcion: str = Field(..., min_length=10, max_length=1000, description="Descripción detallada del ejercicio")
    categoria: TipoEjercicio = Field(..., description="Categoría principal del ejercicio")
    instrucciones: str = Field(..., min_length=10, description="Instrucciones paso a paso para realizar el ejercicio")
    nivel: NivelDificultad = Field(..., description="Nivel de dificultad del ejercicio")
    es_compuesto: bool = Field(default=False, description="Indica si es un ejercicio compuesto (trabaja múltiples grupos musculares)")
    imagen_url: Optional[str] = Field(None, description="URL de la imagen demostrativa")
    video_url: Optional[str] = Field(None, description="URL del video demostrativo")
    variaciones: Optional[List[str]] = Field(None, description="Variaciones posibles del ejercicio")
    precauciones: Optional[str] = Field(None, description="Precauciones o contraindicaciones")


class EjercicioCreate(EjercicioBase):
    """Esquema para crear un nuevo ejercicio"""
    equipo_necesario: Optional[List[str]] = Field(None, description="Equipo necesario para realizar el ejercicio")
    musculos_secundarios: Optional[List[str]] = Field(None, description="Músculos secundarios trabajados")


class EjercicioUpdate(BaseModel):
    """Esquema para actualizar un ejercicio existente"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100, description="Nombre del ejercicio")
    descripcion: Optional[str] = Field(None, min_length=10, max_length=1000, description="Descripción detallada del ejercicio")
    categoria: Optional[TipoEjercicio] = Field(None, description="Categoría principal del ejercicio")
    instrucciones: Optional[str] = Field(None, min_length=10, description="Instrucciones paso a paso para realizar el ejercicio")
    nivel: Optional[NivelDificultad] = Field(None, description="Nivel de dificultad del ejercicio")
    es_compuesto: Optional[bool] = Field(None, description="Indica si es un ejercicio compuesto (trabaja múltiples grupos musculares)")
    imagen_url: Optional[str] = Field(None, description="URL de la imagen demostrativa")
    video_url: Optional[str] = Field(None, description="URL del video demostrativo")
    variaciones: Optional[List[str]] = Field(None, description="Variaciones posibles del ejercicio")
    precauciones: Optional[str] = Field(None, description="Precauciones o contraindicaciones")
    equipo_necesario: Optional[List[str]] = Field(None, description="Equipo necesario para realizar el ejercicio")
    musculos_secundarios: Optional[List[str]] = Field(None, description="Músculos secundarios trabajados")


class Ejercicio(EjercicioBase):
    """Esquema para representar un ejercicio completo"""
    id: int
    equipo_necesario: Optional[List[str]]
    musculos_secundarios: Optional[List[str]]
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    model_config = { "from_attributes": True }


class EjercicioResumen(BaseModel):
    """Esquema para resumen de ejercicios"""
    id: int
    nombre: str
    categoria: TipoEjercicio
    nivel: NivelDificultad
    es_compuesto: bool
    
    model_config = { "from_attributes": True }


class EjercicioRutina(BaseModel):
    """Esquema para ejercicios dentro de una rutina"""
    ejercicio_id: int = Field(..., description="ID del ejercicio")
    series: int = Field(..., gt=0, le=10, description="Número de series")
    repeticiones: str = Field(..., description="Repeticiones por serie (ej: '12,10,8' o '12-15')")
    descanso_segundos: int = Field(..., ge=0, le=300, description="Tiempo de descanso entre series en segundos")
    notas: Optional[str] = Field(None, description="Notas específicas para este ejercicio en la rutina")
    orden: int = Field(..., ge=1, description="Orden del ejercicio en la rutina")
    superset_con: Optional[int] = Field(None, description="ID del ejercicio con el que forma un superset")


class RutinaBase(BaseModel):
    """Esquema base para rutinas"""
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre de la rutina")
    descripcion: str = Field(..., min_length=10, max_length=1000, description="Descripción detallada de la rutina")
    nivel: NivelDificultad = Field(..., description="Nivel de dificultad de la rutina")
    objetivo: str = Field(..., description="Objetivo principal de la rutina (ej: hipertrofia, fuerza, resistencia)")
    dias_semana: List[str] = Field(..., description="Días de la semana recomendados")
    duracion_estimada_minutos: int = Field(..., gt=0, le=180, description="Duración estimada en minutos")
    notas_generales: Optional[str] = Field(None, description="Notas generales sobre la rutina")


class RutinaCreate(RutinaBase):
    """Esquema para crear una nueva rutina"""
    ejercicios: List[EjercicioRutina] = Field(..., min_length=1, description="Ejercicios que componen la rutina")
    publico: bool = Field(default=True, description="Indica si la rutina es pública o privada")
    creador_id: Optional[int] = Field(None, description="ID del usuario creador (admin o entrenador)")


class RutinaUpdate(BaseModel):
    """Esquema para actualizar una rutina existente"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100, description="Nombre de la rutina")
    descripcion: Optional[str] = Field(None, min_length=10, max_length=1000, description="Descripción detallada de la rutina")
    nivel: Optional[NivelDificultad] = Field(None, description="Nivel de dificultad de la rutina")
    objetivo: Optional[str] = Field(None, description="Objetivo principal de la rutina")
    dias_semana: Optional[List[str]] = Field(None, description="Días de la semana recomendados")
    duracion_estimada_minutos: Optional[int] = Field(None, gt=0, le=180, description="Duración estimada en minutos")
    notas_generales: Optional[str] = Field(None, description="Notas generales sobre la rutina")
    ejercicios: Optional[List[EjercicioRutina]] = Field(None, description="Ejercicios que componen la rutina")
    publico: Optional[bool] = Field(None, description="Indica si la rutina es pública o privada")


class RutinaUsuarioBase(BaseModel):
    """Esquema base para asignación de rutinas a usuarios"""
    usuario_id: int = Field(..., description="ID del usuario")
    rutina_id: int = Field(..., description="ID de la rutina")
    fecha_inicio: date = Field(..., description="Fecha de inicio de la rutina")
    fecha_fin: Optional[date] = Field(None, description="Fecha de finalización planificada (opcional)")
    notas: Optional[str] = Field(None, description="Notas sobre la asignación")
    
    @field_validator('fecha_fin')
    @classmethod
    def fecha_fin_despues_inicio(cls, v: Optional[date], info: ValidationInfo) -> Optional[date]:
        if v is not None and 'fecha_inicio' in info.data and v <= info.data['fecha_inicio']:
            raise ValueError('La fecha de finalización debe ser posterior a la fecha de inicio')
        return v


class RutinaUsuarioCreate(RutinaUsuarioBase):
    """Esquema para crear una nueva asignación de rutina a usuario"""
    asignado_por_id: Optional[int] = Field(None, description="ID del usuario que asigna la rutina (entrenador)")


class RutinaUsuarioUpdate(BaseModel):
    """Esquema para actualizar una asignación de rutina a usuario"""
    fecha_fin: Optional[date] = Field(None, description="Fecha de finalización planificada")
    notas: Optional[str] = Field(None, description="Notas sobre la asignación")
    completada: Optional[bool] = Field(None, description="Indica si la rutina se ha completado")


class Rutina(RutinaBase):
    """Esquema para representar una rutina completa"""
    id: int
    ejercicios: List[Dict[str, Any]]
    publico: bool
    creador_id: Optional[int]
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    model_config = { "from_attributes": True }


class RutinaResumen(BaseModel):
    """Esquema para resumen de rutinas"""
    id: int
    nombre: str
    nivel: NivelDificultad
    objetivo: str
    duracion_estimada_minutos: int
    cantidad_ejercicios: int
    publico: bool
    
    model_config = { "from_attributes": True }


class RutinaUsuario(RutinaUsuarioBase):
    """Esquema para representar una asignación de rutina a usuario"""
    id: int
    asignado_por_id: Optional[int]
    completada: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    rutina: RutinaResumen
    
    model_config = { "from_attributes": True }


class ProgresoRutina(BaseModel):
    """Esquema para seguimiento de progreso en rutinas"""
    usuario_id: int
    rutina_usuario_id: int
    fecha: date
    ejercicios_completados: List[int]
    porcentaje_completado: float
    notas: Optional[str]
    carga_incrementada: bool
    estado_animo: Optional[int]
    dificultad_percibida: Optional[int]


class ProgresoRutinaCreate(BaseModel):
    """Esquema para crear un nuevo registro de progreso en rutinas"""
    usuario_id: int = Field(..., description="ID del usuario")
    rutina_id: int = Field(..., description="ID de la rutina")
    ejercicio_id: Optional[int] = Field(None, description="ID del ejercicio (opcional)")
    fecha: date = Field(..., description="Fecha del registro de progreso")
    completado: bool = Field(default=False, description="Indica si se completó la sesión/ejercicio")
    series: Optional[int] = Field(None, description="Número de series realizadas")
    repeticiones: Optional[int] = Field(None, description="Repeticiones realizadas")
    peso: Optional[float] = Field(None, description="Peso utilizado (en kg)")
    duracion: Optional[int] = Field(None, description="Duración en minutos")
    dificultad_percibida: Optional[int] = Field(None, ge=1, le=10, description="Dificultad percibida (1-10)")
    sensacion: Optional[str] = Field(None, description="Sensación después del ejercicio")
    notas: Optional[str] = Field(None, description="Notas adicionales")
