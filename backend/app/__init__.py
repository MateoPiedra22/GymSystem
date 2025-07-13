"""
Archivo de inicialización del paquete de la aplicación
"""
from app.core.config import settings

__version__ = settings.API_VERSION

# Alias para mantener compatibilidad con importaciones antiguas que usan 'app.database'
import sys as _sys
from types import ModuleType as _ModuleType

from app.core import database as _database_module

# Registrar el alias si no existe
if 'app.database' not in _sys.modules:
    _sys.modules['app.database'] = _database_module  # type: ignore[assignment]
