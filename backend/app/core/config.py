"""
Backend - Archivo de configuración principal
Este archivo contiene la configuración central del backend.
REFACTORIZADO: Dividido en módulos específicos por dominio para mejor organización
"""
from .config import settings

# Exportar la configuración para mantener compatibilidad
__all__ = ["settings"]
