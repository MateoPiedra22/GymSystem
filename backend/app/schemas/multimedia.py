"""
Schemas para gestión de multimedia en ejercicios y rutinas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.models.enums import TipoMultimedia, EstadoMultimedia, CategoriaMultimedia, NivelDificultad

# ============= SCHEMAS BASE =============

class MultimediaBase(BaseModel):
    """Schema base para multimedia"""
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = None
    tipo: TipoMultimedia
    categoria: CategoriaMultimedia
    orden: int = Field(default=1, ge=1, le=100)
    es_principal: bool = False
    mostrar_en_preview: bool = True
    etiquetas: Optional[List[str]] = []
    nivel_dificultad: Optional[NivelDificultad] = None
    es_premium: bool = False
    edad_minima: Optional[int] = Field(None, ge=0, le=100)
    requiere_supervision: bool = False

class MultimediaCreate(MultimediaBase):
    """Schema para crear multimedia"""
    ejercicio_id: str
    idioma: str = "es"
    autoplay: bool = False
    loop: bool = False

class MultimediaUpdate(BaseModel):
    """Schema para actualizar multimedia"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = None
    categoria: Optional[CategoriaMultimedia] = None
    orden: Optional[int] = Field(None, ge=1, le=100)
    es_principal: Optional[bool] = None
    mostrar_en_preview: Optional[bool] = None
    etiquetas: Optional[List[str]] = None
    nivel_dificultad: Optional[NivelDificultad] = None
    es_premium: Optional[bool] = None
    edad_minima: Optional[int] = Field(None, ge=0, le=100)
    requiere_supervision: Optional[bool] = None
    autoplay: Optional[bool] = None
    loop: Optional[bool] = None
    estado: Optional[EstadoMultimedia] = None

class EstadisticasMultimedia(BaseModel):
    """Schema para estadísticas de multimedia"""
    vistas: int = 0
    descargas: int = 0
    me_gusta: int = 0
    reportes: int = 0

class MultimediaResponse(MultimediaBase):
    """Schema para respuesta de multimedia"""
    id: str
    ejercicio_id: str
    archivo_url: str
    thumbnail_url: Optional[str] = None
    formato: str
    tamaño_mb: float
    duracion_segundos: Optional[int] = None
    dimensiones: Optional[Dict[str, int]] = None
    fps: Optional[int] = None
    bitrate: Optional[int] = None
    calidad_original: Optional[str] = None
    versiones_disponibles: Optional[Dict[str, Any]] = None
    estado: EstadoMultimedia
    motivo_rechazo: Optional[str] = None
    subido_por: Optional[str] = None
    fecha_subida: datetime
    aprobado_por: Optional[str] = None
    fecha_aprobacion: Optional[datetime] = None
    estadisticas: EstadisticasMultimedia
    idioma: str

    model_config = { "from_attributes": True }

class MultimediaListResponse(BaseModel):
    """Schema para lista de multimedia"""
    multimedia: List[MultimediaResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int

# ============= SCHEMAS DE RUTINAS =============

class MultimediaRutinaBase(BaseModel):
    """Schema base para multimedia de rutinas"""
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = None
    tipo: TipoMultimedia
    categoria: CategoriaMultimedia
    orden: int = Field(default=1, ge=1, le=100)
    es_principal: bool = False
    es_introduccion: bool = False

class MultimediaRutinaCreate(MultimediaRutinaBase):
    """Schema para crear multimedia de rutina"""
    rutina_id: str

class MultimediaRutinaResponse(MultimediaRutinaBase):
    """Schema para respuesta de multimedia de rutina"""
    id: str
    rutina_id: str
    archivo_url: str
    thumbnail_url: Optional[str] = None
    formato: str
    tamaño_bytes: Optional[int] = None
    duracion_segundos: Optional[int] = None
    dimensiones: Optional[Dict[str, int]] = None
    estado: EstadoMultimedia
    subido_por: Optional[str] = None
    fecha_subida: datetime
    vistas: int
    descargas: int

    model_config = { "from_attributes": True }

# ============= SCHEMAS DE ANOTACIONES =============

class AnotacionBase(BaseModel):
    """Schema base para anotaciones"""
    titulo: Optional[str] = Field(None, max_length=255)
    texto: str = Field(..., min_length=1)
    tipo_anotacion: str = Field(default="nota")
    tiempo_inicio: Optional[float] = Field(None, ge=0)
    tiempo_fin: Optional[float] = Field(None, ge=0)
    posicion_x: Optional[float] = Field(None, ge=0, le=100)
    posicion_y: Optional[float] = Field(None, ge=0, le=100)
    color: str = Field(default="#ffff00")
    tamaño_fuente: int = Field(default=12, ge=8, le=24)
    mostrar_automaticamente: bool = True
    es_interactiva: bool = False
    accion_requerida: Optional[str] = None

    @field_validator('tiempo_fin')
    @classmethod
    def validar_tiempos(cls, v: Optional[float], info: ValidationInfo) -> Optional[float]:
        if v is not None and 'tiempo_inicio' in info.data and info.data['tiempo_inicio'] is not None:
            if v <= info.data['tiempo_inicio']:
                raise ValueError('tiempo_fin debe ser mayor que tiempo_inicio')
        return v

class AnotacionCreate(AnotacionBase):
    """Schema para crear anotación"""
    multimedia_id: str

class AnotacionUpdate(BaseModel):
    """Schema para actualizar anotación"""
    titulo: Optional[str] = Field(None, max_length=255)
    texto: Optional[str] = Field(None, min_length=1)
    tipo_anotacion: Optional[str] = None
    tiempo_inicio: Optional[float] = Field(None, ge=0)
    tiempo_fin: Optional[float] = Field(None, ge=0)
    posicion_x: Optional[float] = Field(None, ge=0, le=100)
    posicion_y: Optional[float] = Field(None, ge=0, le=100)
    color: Optional[str] = None
    tamaño_fuente: Optional[int] = Field(None, ge=8, le=24)
    mostrar_automaticamente: Optional[bool] = None
    es_interactiva: Optional[bool] = None
    accion_requerida: Optional[str] = None
    activo: Optional[bool] = None

class AnotacionResponse(AnotacionBase):
    """Schema para respuesta de anotación"""
    id: str
    multimedia_id: str
    creado_por: Optional[str] = None
    fecha_creacion: datetime
    activo: bool

    model_config = { "from_attributes": True }

# ============= SCHEMAS DE COLECCIONES =============

class ColeccionBase(BaseModel):
    """Schema base para colecciones"""
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = None
    es_publica: bool = False
    es_destacada: bool = False
    color_tema: str = Field(default="#007bff")
    icono: Optional[str] = None
    categoria_principal: Optional[str] = None
    nivel_recomendado: Optional[NivelDificultad] = None

class ColeccionCreate(ColeccionBase):
    """Schema para crear colección"""
    pass

class ColeccionUpdate(BaseModel):
    """Schema para actualizar colección"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = None
    es_publica: Optional[bool] = None
    es_destacada: Optional[bool] = None
    color_tema: Optional[str] = None
    icono: Optional[str] = None
    categoria_principal: Optional[str] = None
    nivel_recomendado: Optional[NivelDificultad] = None
    activo: Optional[bool] = None

class ItemColeccionBase(BaseModel):
    """Schema base para items de colección"""
    orden: int = Field(..., ge=1)
    titulo_personalizado: Optional[str] = Field(None, max_length=255)
    descripcion_personalizada: Optional[str] = None
    obligatorio: bool = False
    desbloqueado: bool = True
    requisitos: Optional[Dict[str, Any]] = None

class ItemColeccionCreate(ItemColeccionBase):
    """Schema para crear item de colección"""
    multimedia_id: str

class ItemColeccionResponse(ItemColeccionBase):
    """Schema para respuesta de item de colección"""
    id: str
    coleccion_id: str
    multimedia_id: str
    agregado_por: Optional[str] = None
    fecha_agregado: datetime
    activo: bool
    multimedia: Optional[MultimediaResponse] = None

    model_config = { "from_attributes": True }

class ColeccionResponse(ColeccionBase):
    """Schema para respuesta de colección"""
    id: str
    creado_por: str
    fecha_creacion: datetime
    activo: bool
    visualizaciones: int
    seguidores: int
    duracion_total: Optional[int] = None
    items: Optional[List[ItemColeccionResponse]] = []

    model_config = { "from_attributes": True }

# ============= SCHEMAS DE HISTORIAL =============

class HistorialAcceso(BaseModel):
    """Schema para registrar acceso a multimedia"""
    multimedia_id: str
    duracion_visualizacion: Optional[int] = None
    progreso: float = Field(default=0.0, ge=0.0, le=1.0)
    dispositivo: Optional[str] = None
    calidad_reproducida: Optional[str] = None
    le_gusto: Optional[bool] = None
    marco_como_favorito: bool = False
    compartio: bool = False
    descargo: bool = False

class HistorialResponse(BaseModel):
    """Schema para respuesta de historial"""
    id: str
    usuario_id: str
    multimedia_id: str
    fecha_acceso: datetime
    duracion_visualizacion: Optional[int] = None
    progreso: float
    dispositivo: Optional[str] = None
    calidad_reproducida: Optional[str] = None
    le_gusto: Optional[bool] = None
    marco_como_favorito: bool
    compartio: bool
    descargo: bool
    multimedia: Optional[MultimediaResponse] = None

    model_config = { "from_attributes": True }

# ============= SCHEMAS DE UPLOAD =============

class MultimediaUploadResponse(BaseModel):
    """Schema para respuesta de upload"""
    id: str
    nombre: str
    archivo_url: str
    thumbnail_url: Optional[str] = None
    formato: str
    tamaño_mb: float
    duracion_segundos: Optional[int] = None
    dimensiones: Optional[Dict[str, int]] = None
    mensaje: str = "Archivo subido exitosamente"

class MultimediaUploadProgress(BaseModel):
    """Schema para progreso de upload"""
    upload_id: str
    progreso: float = Field(..., ge=0.0, le=1.0)
    estado: str  # uploading, processing, completed, error
    mensaje: Optional[str] = None
    archivo_procesado: Optional[str] = None

# ============= SCHEMAS DE BÚSQUEDA Y FILTROS =============

class FiltrosMultimedia(BaseModel):
    """Schema para filtros de búsqueda"""
    tipo: Optional[TipoMultimedia] = None
    categoria: Optional[CategoriaMultimedia] = None
    estado: Optional[EstadoMultimedia] = None
    nivel_dificultad: Optional[NivelDificultad] = None
    es_premium: Optional[bool] = None
    etiquetas: Optional[List[str]] = None
    duracion_min: Optional[int] = Field(None, ge=0)
    duracion_max: Optional[int] = Field(None, ge=0)
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    subido_por: Optional[str] = None
    ordenar_por: str = Field(default="fecha_subida")
    orden_desc: bool = True

class BusquedaMultimedia(BaseModel):
    """Schema para búsqueda de multimedia"""
    query: Optional[str] = None
    ejercicio_id: Optional[str] = None
    filtros: Optional[FiltrosMultimedia] = None
    pagina: int = Field(default=1, ge=1)
    por_pagina: int = Field(default=20, ge=1, le=100)

# ============= SCHEMAS DE ESTADÍSTICAS =============

class EstadisticasGenerales(BaseModel):
    """Schema para estadísticas generales"""
    total_archivos: int
    total_por_tipo: Dict[str, int]
    total_por_categoria: Dict[str, int]
    total_por_estado: Dict[str, int]
    espacio_usado_mb: float
    archivos_mas_vistos: List[MultimediaResponse]
    archivos_recientes: List[MultimediaResponse]

class EstadisticasUsuario(BaseModel):
    """Schema para estadísticas de usuario"""
    archivos_subidos: int
    archivos_aprobados: int
    total_vistas: int
    total_descargas: int
    archivos_favoritos: int
    tiempo_total_visualizado: int  # en minutos
    historial_reciente: List[HistorialResponse]

# ============= SCHEMAS DE VALIDACIÓN =============

class ValidacionArchivo(BaseModel):
    """Schema para validación de archivos"""
    es_valido: bool
    tipo_detectado: Optional[str] = None
    formato_detectado: Optional[str] = None
    tamaño_mb: float
    duracion_segundos: Optional[int] = None
    dimensiones: Optional[Dict[str, int]] = None
    calidad_detectada: Optional[str] = None
    errores: List[str] = []
    advertencias: List[str] = []

class ConfiguracionMultimedia(BaseModel):
    """Schema para configuración del sistema multimedia"""
    formatos_permitidos: Dict[str, List[str]]
    tamaño_maximo_mb: Dict[str, int]
    calidades_video: List[str]
    requiere_aprobacion: bool
    generar_thumbnails: bool
    comprimir_automaticamente: bool
    watermark_enabled: bool
    watermark_texto: Optional[str] = None 