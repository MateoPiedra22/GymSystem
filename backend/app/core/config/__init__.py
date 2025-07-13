"""
Backend - Configuración principal
Este archivo combina todas las configuraciones específicas por dominio.
"""
import logging
from typing import List
from pydantic import Field

from .base import Settings
from .security import SecuritySettings
from .database import DatabaseSettings
from .redis import RedisSettings
from .services import ServicesSettings

# Configurar logging
logger = logging.getLogger(__name__)

class GymSettings(Settings, SecuritySettings, DatabaseSettings, RedisSettings, ServicesSettings):
    """
    Clase de configuración completa que hereda de todas las configuraciones específicas.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Validar configuración en producción
        if self.is_production():
            security_issues = self.validate_production_security()
            if security_issues:
                logger.error(f"Problemas de seguridad detectados en producción: {security_issues}")
                print("ERROR CRÍTICO: El sistema no puede arrancar en producción con valores inseguros. Revisa las variables de entorno y configura claves, contraseñas y dominios reales y seguros.")
                raise SystemExit(1)
        
        logger.info(f"Configuración cargada exitosamente para entorno: {self.ENV}")
    
    def validate_production_security(self) -> List[str]:
        """Valida configuración de seguridad para producción"""
        issues = []
        # Verificar claves secretas
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 64 or 'changeme' in self.SECRET_KEY or 'dev' in self.SECRET_KEY or 'example' in self.SECRET_KEY:
            issues.append("SECRET_KEY debe tener al menos 64 caracteres, ser única y no contener valores de ejemplo/dev")
        if not self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 64 or 'changeme' in self.JWT_SECRET_KEY or 'dev' in self.JWT_SECRET_KEY or 'example' in self.JWT_SECRET_KEY:
            issues.append("JWT_SECRET_KEY debe tener al menos 64 caracteres, ser única y no contener valores de ejemplo/dev")
        # Verificar contraseñas de base de datos
        if not self.DB_PASSWORD or len(self.DB_PASSWORD) < 16 or 'changeme' in self.DB_PASSWORD or 'dev' in self.DB_PASSWORD or 'example' in self.DB_PASSWORD:
            issues.append("DB_PASSWORD debe tener al menos 16 caracteres y no contener valores de ejemplo/dev")
        # Verificar contraseña de Redis
        if not self.REDIS_PASSWORD or len(self.REDIS_PASSWORD) < 16 or 'changeme' in self.REDIS_PASSWORD or 'dev' in self.REDIS_PASSWORD or 'example' in self.REDIS_PASSWORD:
            issues.append("REDIS_PASSWORD debe tener al menos 16 caracteres y no contener valores de ejemplo/dev")
        # Verificar configuración CORS
        if not self.ALLOWED_ORIGINS or any(o in ["*", "localhost", "127.0.0.1"] for o in self.ALLOWED_ORIGINS):
            issues.append("ALLOWED_ORIGINS debe configurarse solo con dominios reales y seguros, sin comodines ni localhost")
        # Verificar backup key
        if not self.BACKUP_ENCRYPTION_KEY or len(self.BACKUP_ENCRYPTION_KEY) < 32 or 'changeme' in self.BACKUP_ENCRYPTION_KEY or 'dev' in self.BACKUP_ENCRYPTION_KEY or 'example' in self.BACKUP_ENCRYPTION_KEY:
            issues.append("BACKUP_ENCRYPTION_KEY debe tener al menos 32 caracteres y no contener valores de ejemplo/dev")
        # Verificar admin password
        if hasattr(self, 'ADMIN_PASSWORD') and (not self.ADMIN_PASSWORD or len(self.ADMIN_PASSWORD) < 16 or 'changeme' in self.ADMIN_PASSWORD or 'dev' in self.ADMIN_PASSWORD or 'example' in self.ADMIN_PASSWORD):
            issues.append("ADMIN_PASSWORD debe tener al menos 16 caracteres y no contener valores de ejemplo/dev")
        return issues

# Instancia global de configuración
try:
    settings = GymSettings()
    logger.info(f"Configuración cargada exitosamente para entorno: {settings.ENV}")
except Exception as e:
    logger.error(f"Error al cargar configuración: {e}")
    print("ERROR CRÍTICO: La configuración contiene valores inseguros o de ejemplo. Por favor, revisa las variables de entorno y asegúrate de que todas las claves, contraseñas y tokens sean únicos y seguros. Consulta la documentación para más detalles.")
    raise

# Exportar la configuración
__all__ = ["settings"] 