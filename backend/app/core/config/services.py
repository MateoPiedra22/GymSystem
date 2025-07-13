"""
Backend - Configuración de servicios externos
Este archivo contiene la configuración de servicios externos del backend.
"""
import os
import logging
from typing import Optional
from pydantic import field_validator, Field
from pathlib import Path

# Configurar logging
logger = logging.getLogger(__name__)

class ServicesSettings:
    """Configuración específica de servicios externos"""
    
    # Configuración de email (opcional)
    SMTP_HOST: Optional[str] = Field(default=None, alias='GYM_SMTP_HOST')
    SMTP_PORT: int = Field(default=587, alias='GYM_SMTP_PORT')
    SMTP_USERNAME: Optional[str] = Field(default=None, alias='GYM_SMTP_USERNAME')
    SMTP_PASSWORD: Optional[str] = Field(default=None, alias='GYM_SMTP_PASSWORD')
    SMTP_FROM_EMAIL: Optional[str] = Field(default=None, alias='GYM_SMTP_FROM')
    SMTP_USE_TLS: bool = Field(default=True, alias='GYM_SMTP_TLS')
    
    # Configuración de monitoreo
    SENTRY_DSN: Optional[str] = Field(default=None, alias='GYM_SENTRY_DSN')
    PROMETHEUS_METRICS: bool = Field(default=True, alias='GYM_PROMETHEUS_METRICS')
    METRICS_PORT: int = Field(default=9000, alias='GYM_METRICS_PORT')
    
    # Configuración de backup
    BACKUP_DIR: str = Field(default="backups", alias='GYM_BACKUP_DIR')
    BACKUP_RETENTION_DAYS: int = Field(default=30, alias='GYM_BACKUP_RETENTION_DAYS')
    AUTO_BACKUP_ENABLED: bool = Field(default=True, alias='GYM_AUTO_BACKUP_ENABLED')
    BACKUP_SCHEDULE: str = Field(default="0 2 * * *", alias='GYM_BACKUP_SCHEDULE')  # Cron format
    
    # URLs de servicios externos
    EXTERNAL_API_URL: Optional[str] = Field(default=None, alias='GYM_EXTERNAL_API_URL')
    EXTERNAL_API_KEY: Optional[str] = Field(default=None, alias='GYM_EXTERNAL_API_KEY')
    
    # Configuración de timeouts de conexión
    HTTP_TIMEOUT: int = Field(default=30, alias='GYM_HTTP_TIMEOUT')

    @field_validator("BACKUP_DIR")
    @classmethod
    def validate_directories(cls, v: str) -> str:
        # Crear directorios si no existen
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("SMTP_HOST")
    @classmethod
    def validate_smtp_config(cls, v: Optional[str], info) -> Optional[str]:
        if v:
            # Buscar SMTP_USERNAME en info.data primero, luego en os.environ como fallback
            smtp_username = info.data.get('SMTP_USERNAME') or os.environ.get('GYM_SMTP_USERNAME')
            if not smtp_username:
                raise ValueError("SMTP_USERNAME es requerido cuando SMTP_HOST está configurado.")
            
            # Buscar SMTP_PASSWORD en info.data primero, luego en os.environ como fallback
            smtp_password = info.data.get('SMTP_PASSWORD') or os.environ.get('GYM_SMTP_PASSWORD')
            if not smtp_password:
                logger.warning("SMTP_PASSWORD no configurado cuando SMTP_HOST está configurado.")
        return v

    def get_smtp_config(self) -> Optional[dict]:
        """Obtener configuración SMTP si está disponible"""
        if not self.SMTP_HOST:
            return None
        
        return {
            "host": self.SMTP_HOST,
            "port": self.SMTP_PORT,
            "username": self.SMTP_USERNAME,
            "password": self.SMTP_PASSWORD,
            "from_email": self.SMTP_FROM_EMAIL,
            "use_tls": self.SMTP_USE_TLS,
        } 