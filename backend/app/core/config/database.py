"""
Backend - Configuración de base de datos
Este archivo contiene la configuración de base de datos del backend.
"""
import os
import logging
from typing import Optional
from pydantic import field_validator, Field

# Configurar logging
logger = logging.getLogger(__name__)

class DatabaseSettings:
    """Configuración específica de base de datos"""
    
    # Base de datos PostgreSQL
    DATABASE_URI: Optional[str] = Field(default=None, alias='GYM_DATABASE_URI')
    DB_HOST: str = Field(default='localhost', alias='GYM_DB_HOST')
    DB_PORT: int = Field(default=5432, alias='GYM_DB_PORT')
    DB_USER: str = Field(default='gym_production_user', alias='GYM_DB_USER')
    DB_PASSWORD: Optional[str] = Field(default='', alias='GYM_DB_PASSWORD')
    DB_NAME: str = Field(default='gym_production_db', alias='GYM_DB_NAME')
    DB_POOL_SIZE: int = Field(default=20, alias='GYM_DB_POOL_SIZE')
    DB_MAX_OVERFLOW: int = Field(default=10, alias='GYM_DB_MAX_OVERFLOW')
    DB_POOL_TIMEOUT: int = Field(default=30, alias='GYM_DB_POOL_TIMEOUT')
    DB_SSL_MODE: str = Field(default="require", alias='GYM_DB_SSL_MODE')
    DB_CONNECT_TIMEOUT: int = Field(default=10, alias='GYM_DB_CONNECT_TIMEOUT')
    DB_STATEMENT_TIMEOUT: int = Field(default=30000, alias='GYM_DB_STATEMENT_TIMEOUT')
    DB_IDLE_IN_TRANSACTION_TIMEOUT: int = Field(default=60000, alias='GYM_DB_IDLE_TIMEOUT')

    @field_validator("DATABASE_URI", mode='before')
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        """Construir URI de base de datos con validaciones de seguridad mejoradas"""
        if v and isinstance(v, str):
            return v
        
        user = os.getenv('GYM_DB_USER', 'gym_secure_user')
        password = os.getenv('GYM_DB_PASSWORD')
        host = os.getenv('GYM_DB_HOST', 'localhost')
        port = os.getenv('GYM_DB_PORT', '5432')
        db = os.getenv('GYM_DB_NAME', 'gym_secure_db')
        ssl_mode = os.getenv('GYM_DB_SSL_MODE', 'prefer')  # Cambiar de 'require' a 'prefer' por defecto

        # Validaciones para producción
        if info.data.get("ENV") == "production":
            # Validar variables críticas
            if not password:
                logger.error("GYM_DB_PASSWORD no configurado en producción")
                raise ValueError("GYM_DB_PASSWORD es requerido en producción")
            if not user or user == 'gym_production_user':
                logger.error("GYM_DB_USER usa valor por defecto en producción")
                raise ValueError("GYM_DB_USER debe ser configurado en producción")
            if not host or host == 'localhost':
                logger.error("GYM_DB_HOST usa valor por defecto en producción")
                raise ValueError("GYM_DB_HOST debe ser configurado en producción")
            if not db or db == 'gym_production_db':
                logger.error("GYM_DB_NAME usa valor por defecto en producción")
                raise ValueError("GYM_DB_NAME debe ser configurado en producción")
            
            # Validar contraseñas inseguras
            insecure_passwords = [
                "password", "123456", "admin", "gympass", "gympass123", 
                "postgres", "root", "user", "test", "demo", "example",
                "CHANGE_THIS_DB_PASSWORD_IN_PRODUCTION_USE_SECURE_PASSWORD",
                "CHANGE_THIS_TO_SECURE_PASSWORD_2024!",
                "GmY!2024$k9w3n8Zp4s7v2x1c6b5n0"  # Valor de ejemplo
            ]
            if password in insecure_passwords:
                logger.error("GYM_DB_PASSWORD usa valores por defecto inseguros en producción")
                raise ValueError("GYM_DB_PASSWORD no puede usar valores por defecto en producción")
            
            # Validar complejidad de contraseña
            if password and len(password) < 16:
                logger.error("GYM_DB_PASSWORD es demasiado corta para producción (mínimo 16 caracteres)")
                raise ValueError("GYM_DB_PASSWORD debe tener al menos 16 caracteres en producción")
            
            # Validar que la contraseña contenga caracteres complejos
            if password and not (any(c.isupper() for c in password) and 
                               any(c.islower() for c in password) and 
                               any(c.isdigit() for c in password) and
                               any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)):
                logger.error("GYM_DB_PASSWORD debe contener mayúsculas, minúsculas, números y caracteres especiales en producción")
                raise ValueError("GYM_DB_PASSWORD debe ser compleja en producción")
            
            # Validar SSL en producción
            if ssl_mode not in ['require', 'verify-ca', 'verify-full']:
                logger.error("SSL es requerido en producción")
                raise ValueError("GYM_DB_SSL_MODE debe ser 'require', 'verify-ca' o 'verify-full' en producción")
            
            # Validar que no use localhost en producción
            if host in ['localhost', '127.0.0.1']:
                logger.error("No se permite localhost en producción")
                raise ValueError("GYM_DB_HOST no puede ser localhost en producción")
        
        # Validaciones para desarrollo
        elif info.data.get("ENV") == "development":
            if not password:
                logger.warning("GYM_DB_PASSWORD no configurado en desarrollo")
            if host == 'localhost' and not os.getenv('GYM_DB_HOST'):
                logger.info("Usando configuración de base de datos local para desarrollo")
            # En desarrollo, permitir SSL más flexible
            if ssl_mode not in ['disable', 'allow', 'prefer', 'require']:
                ssl_mode = 'prefer'  # Usar 'prefer' por defecto en desarrollo

        # Construir URI con validación de parámetros
        if not user or not host or not db:
            raise ValueError("Configuración de base de datos incompleta")
        
        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{db}?sslmode={ssl_mode}"
        else:
            return f"postgresql://{user}@{host}:{port}/{db}?sslmode={ssl_mode}"

    @field_validator("DB_POOL_SIZE")
    @classmethod
    def validate_pool_size(cls, v: int, info) -> int:
        """Validar tamaño del pool de conexiones"""
        if info.data.get("ENV") == "production":
            if v < 10:
                logger.warning("DB_POOL_SIZE muy bajo para producción, recomendado mínimo 10")
            if v > 50:
                logger.warning("DB_POOL_SIZE muy alto, puede causar problemas de memoria")
        if v < 1 or v > 100:
            raise ValueError("DB_POOL_SIZE debe estar entre 1 y 100")
        return v

    @field_validator("DB_MAX_OVERFLOW")
    @classmethod
    def validate_max_overflow(cls, v: int, info) -> int:
        """Validar overflow máximo del pool"""
        if info.data.get("ENV") == "production":
            if v < 5:
                logger.warning("DB_MAX_OVERFLOW muy bajo para producción")
        if v < 0 or v > 50:
            raise ValueError("DB_MAX_OVERFLOW debe estar entre 0 y 50")
        return v

    @field_validator("DB_SSL_MODE")
    @classmethod
    def validate_ssl_mode(cls, v: str, info) -> str:
        """Validar modo SSL"""
        valid_modes = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']
        if v not in valid_modes:
            raise ValueError(f"DB_SSL_MODE debe ser uno de: {valid_modes}")
        
        if info.data.get("ENV") == "production" and v in ['disable', 'allow']:
            logger.warning("SSL mode inseguro detectado en producción")
        
        return v

    def get_database_url(self) -> str:
        """Obtener la URL de la base de datos construida"""
        return str(self.DATABASE_URI)

    def get_database_config(self) -> dict:
        """Obtener configuración completa de base de datos"""
        return {
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "connect_timeout": self.DB_CONNECT_TIMEOUT,
            "statement_timeout": self.DB_STATEMENT_TIMEOUT,
            "idle_in_transaction_timeout": self.DB_IDLE_IN_TRANSACTION_TIMEOUT,
            "ssl_mode": self.DB_SSL_MODE
        } 