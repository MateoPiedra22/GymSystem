"""
Schemas para la configuración del sistema
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class ConfiguracionEstilosBase(BaseModel):
    """Schema base para configuración de estilos"""
    nombre_tema: str = Field(..., description="Nombre del tema")
    descripcion: Optional[str] = Field(None, description="Descripción del tema")
    colores_primarios: Dict[str, str] = Field(default_factory=dict, description="Colores primarios del tema")
    colores_secundarios: Dict[str, str] = Field(default_factory=dict, description="Colores secundarios del tema")
    fuentes: Dict[str, str] = Field(default_factory=dict, description="Configuración de fuentes")
    tamaños: Dict[str, Any] = Field(default_factory=dict, description="Tamaños de elementos")
    bordes_y_sombras: Dict[str, str] = Field(default_factory=dict, description="Configuración de bordes y sombras")
    animaciones: Dict[str, Any] = Field(default_factory=dict, description="Configuración de animaciones")
    es_predeterminado: bool = Field(False, description="Si es el tema predeterminado")
    activo: bool = Field(True, description="Si el tema está activo")

class ConfiguracionEstilosCreate(ConfiguracionEstilosBase):
    """Schema para crear configuración de estilos"""
    pass

class ConfiguracionEstilosUpdate(BaseModel):
    """Schema para actualizar configuración de estilos"""
    nombre_tema: Optional[str] = None
    descripcion: Optional[str] = None
    colores_primarios: Optional[Dict[str, str]] = None
    colores_secundarios: Optional[Dict[str, str]] = None
    fuentes: Optional[Dict[str, str]] = None
    tamaños: Optional[Dict[str, Any]] = None
    bordes_y_sombras: Optional[Dict[str, str]] = None
    animaciones: Optional[Dict[str, Any]] = None
    es_predeterminado: Optional[bool] = None
    activo: Optional[bool] = None

class ConfiguracionEstilos(ConfiguracionEstilosBase):
    """Schema completo para configuración de estilos"""
    id: str
    creado_en: datetime
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True

class LogoPersonalizadoBase(BaseModel):
    """Schema base para logo personalizado"""
    nombre: str = Field(..., description="Nombre del logo")
    descripcion: Optional[str] = Field(None, description="Descripción del logo")
    archivo_path: str = Field(..., description="Ruta del archivo del logo")
    tipo_archivo: str = Field(..., description="Tipo de archivo (png, jpg, svg)")
    tamaño_kb: int = Field(..., description="Tamaño del archivo en KB")
    dimensiones: Dict[str, int] = Field(default_factory=dict, description="Dimensiones del logo (width, height)")
    es_principal: bool = Field(False, description="Si es el logo principal")
    activo: bool = Field(True, description="Si el logo está activo")

class LogoPersonalizadoCreate(LogoPersonalizadoBase):
    """Schema para crear logo personalizado"""
    pass

class LogoPersonalizadoUpdate(BaseModel):
    """Schema para actualizar logo personalizado"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    archivo_path: Optional[str] = None
    tipo_archivo: Optional[str] = None
    tamaño_kb: Optional[int] = None
    dimensiones: Optional[Dict[str, int]] = None
    es_principal: Optional[bool] = None
    activo: Optional[bool] = None

class LogoPersonalizado(LogoPersonalizadoBase):
    """Schema completo para logo personalizado"""
    id: str
    creado_en: datetime
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConfiguracionSistema(BaseModel):
    """Schema para configuración general del sistema"""
    tema_activo: Optional[ConfiguracionEstilos] = None
    logo_principal: Optional[LogoPersonalizado] = None
    configuraciones_adicionales: Dict[str, Any] = Field(default_factory=dict)

class ConfiguracionSistemaUpdate(BaseModel):
    """Schema para actualizar configuración del sistema"""
    tema_activo_id: Optional[str] = None
    logo_principal_id: Optional[str] = None
    configuraciones_adicionales: Optional[Dict[str, Any]] = None

# Predefined theme templates
TEMAS_PREDEFINIDOS = {
    "clasico": {
        "nombre_tema": "Clásico",
        "descripcion": "Tema clásico con colores tradicionales",
        "colores_primarios": {
            "primary": "#2563eb",
            "primary-foreground": "#ffffff",
            "secondary": "#64748b",
            "secondary-foreground": "#ffffff"
        },
        "colores_secundarios": {
            "accent": "#10b981",
            "accent-foreground": "#ffffff",
            "muted": "#f1f5f9",
            "muted-foreground": "#64748b"
        },
        "fuentes": {
            "font-family": "Inter, sans-serif",
            "font-size-base": "14px",
            "font-weight-normal": "400",
            "font-weight-bold": "600"
        },
        "tamaños": {
            "border-radius": "0.375rem",
            "spacing-unit": "0.25rem"
        },
        "bordes_y_sombras": {
            "border": "1px solid #e2e8f0",
            "shadow": "0 1px 3px 0 rgb(0 0 0 / 0.1)"
        },
        "animaciones": {
            "transition": "all 0.2s ease-in-out"
        }
    },
    "moderno": {
        "nombre_tema": "Moderno",
        "descripcion": "Tema moderno con colores vibrantes",
        "colores_primarios": {
            "primary": "#7c3aed",
            "primary-foreground": "#ffffff",
            "secondary": "#06b6d4",
            "secondary-foreground": "#ffffff"
        },
        "colores_secundarios": {
            "accent": "#f59e0b",
            "accent-foreground": "#ffffff",
            "muted": "#f8fafc",
            "muted-foreground": "#475569"
        },
        "fuentes": {
            "font-family": "Poppins, sans-serif",
            "font-size-base": "15px",
            "font-weight-normal": "400",
            "font-weight-bold": "700"
        },
        "tamaños": {
            "border-radius": "0.75rem",
            "spacing-unit": "0.5rem"
        },
        "bordes_y_sombras": {
            "border": "2px solid #e2e8f0",
            "shadow": "0 10px 25px -5px rgb(0 0 0 / 0.1)"
        },
        "animaciones": {
            "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
        }
    },
    "minimalista": {
        "nombre_tema": "Minimalista",
        "descripcion": "Tema minimalista con colores neutros",
        "colores_primarios": {
            "primary": "#000000",
            "primary-foreground": "#ffffff",
            "secondary": "#6b7280",
            "secondary-foreground": "#ffffff"
        },
        "colores_secundarios": {
            "accent": "#374151",
            "accent-foreground": "#ffffff",
            "muted": "#f9fafb",
            "muted-foreground": "#6b7280"
        },
        "fuentes": {
            "font-family": "system-ui, sans-serif",
            "font-size-base": "14px",
            "font-weight-normal": "300",
            "font-weight-bold": "500"
        },
        "tamaños": {
            "border-radius": "0.125rem",
            "spacing-unit": "0.25rem"
        },
        "bordes_y_sombras": {
            "border": "1px solid #d1d5db",
            "shadow": "none"
        },
        "animaciones": {
            "transition": "all 0.15s ease-out"
        }
    },
    "oscuro": {
        "nombre_tema": "Oscuro",
        "descripcion": "Tema oscuro para ambientes con poca luz",
        "colores_primarios": {
            "primary": "#3b82f6",
            "primary-foreground": "#ffffff",
            "secondary": "#6b7280",
            "secondary-foreground": "#ffffff"
        },
        "colores_secundarios": {
            "accent": "#10b981",
            "accent-foreground": "#ffffff",
            "muted": "#1f2937",
            "muted-foreground": "#9ca3af",
            "background": "#111827",
            "foreground": "#f9fafb"
        },
        "fuentes": {
            "font-family": "Inter, sans-serif",
            "font-size-base": "14px",
            "font-weight-normal": "400",
            "font-weight-bold": "600"
        },
        "tamaños": {
            "border-radius": "0.5rem",
            "spacing-unit": "0.25rem"
        },
        "bordes_y_sombras": {
            "border": "1px solid #374151",
            "shadow": "0 4px 6px -1px rgb(0 0 0 / 0.5)"
        },
        "animaciones": {
            "transition": "all 0.2s ease-in-out"
        }
    }
}

class TemaPredefinido(BaseModel):
    """Schema para temas predefinidos"""
    nombre: str
    datos: ConfiguracionEstilosBase

def obtener_temas_predefinidos() -> List[TemaPredefinido]:
    """Obtiene la lista de temas predefinidos"""
    return [
        TemaPredefinido(
            nombre=nombre,
            datos=ConfiguracionEstilosBase(**datos)
        )
        for nombre, datos in TEMAS_PREDEFINIDOS.items()
    ] 