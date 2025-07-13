"""
Backend - Configuración base
Este archivo contiene la configuración base del backend.
"""
import os
import secrets
import logging
from typing import Optional, List
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Configurar logging
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Clase de configuración centralizada para el backend.
    Utiliza Pydantic para validar y cargar la configuración desde
    variables de entorno y/o un archivo .env.
    
    SEGURIDAD: Todas las configuraciones críticas tienen validaciones estrictas
    y valores por defecto seguros que se generan automáticamente.
    """
    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8', 
        case_sensitive=True,
        extra='ignore' # Ignorar variables de entorno extra
    )

    # Configuración general
    APP_NAME: str = "Gym Management System"
    API_VERSION: str = "v1"
    DEBUG: bool = Field(default=False, alias='GYM_DEBUG')
    ENV: str = Field(default="production", alias='GYM_ENV')
    TESTING: bool = Field(default=False, alias='GYM_TESTING')

    # Configuración de servidor
    SERVER_HOST: str = Field(default="0.0.0.0", alias='GYM_SERVER_HOST')
    SERVER_PORT: int = Field(default=8000, alias='GYM_SERVER_PORT')
    SERVER_WORKERS: int = Field(default=1, alias='GYM_SERVER_WORKERS')
    SERVER_RELOAD: bool = Field(default=False, alias='GYM_SERVER_RELOAD')

    # Logs con configuración mejorada
    LOG_LEVEL: str = Field(default="INFO", alias='GYM_LOG_LEVEL')
    LOG_FILE: str = Field(default="logs/gym_app.log", alias='GYM_LOG_FILE')
    LOG_ROTATION: str = Field(default="midnight", alias='GYM_LOG_ROTATION')
    LOG_MAX_SIZE: str = Field(default="10MB", alias='GYM_LOG_MAX_SIZE')
    LOG_BACKUP_COUNT: int = Field(default=5, alias='GYM_LOG_BACKUP_COUNT')
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s", alias='GYM_LOG_FORMAT')
    LOG_DATE_FORMAT: str = Field(default="%Y-%m-%d %H:%M:%S", alias='GYM_LOG_DATE_FORMAT')
    LOG_ENABLE_JSON: bool = Field(default=False, alias='GYM_LOG_ENABLE_JSON')
    LOG_ENABLE_STRUCTURED: bool = Field(default=True, alias='GYM_LOG_ENABLE_STRUCTURED')
    LOG_INCLUDE_SENSITIVE: bool = Field(default=False, alias='GYM_LOG_INCLUDE_SENSITIVE')

    # Configuración de archivos con validación mejorada
    UPLOAD_DIR: str = Field(default="uploads", alias='GYM_UPLOAD_DIR')
    ALLOWED_EXTENSIONS: Optional[List[str]] = Field(default=None, alias='GYM_ALLOWED_EXTENSIONS')
    
    # URLs de servicios externos
    EXTERNAL_API_URL: Optional[str] = Field(default=None, alias='GYM_EXTERNAL_API_URL')
    EXTERNAL_API_KEY: Optional[str] = Field(default=None, alias='GYM_EXTERNAL_API_KEY')

    @field_validator("ALLOWED_EXTENSIONS", mode='before')
    @classmethod
    def validate_file_extensions(cls, v) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(',') if ext.strip()]
        if isinstance(v, list):
            return [str(ext).strip().lower() for ext in v if str(ext).strip()]
        return []

    @field_validator("UPLOAD_DIR")
    @classmethod
    def validate_directories(cls, v: str) -> str:
        # Crear directorios si no existen
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        valid_envs = ["development", "testing", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"ENV debe ser uno de: {valid_envs}")
        return v.lower()

    def is_production(self) -> bool:
        """Verificar si estamos en producción"""
        return self.ENV == "production"

    def is_development(self) -> bool:
        """Verificar si estamos en desarrollo"""
        return self.ENV == "development"

    def is_testing(self) -> bool:
        """Verificar si estamos en modo de pruebas"""
        return self.ENV == "testing" or self.TESTING 