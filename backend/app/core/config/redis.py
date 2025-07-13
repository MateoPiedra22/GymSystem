"""
Backend - Configuración de Redis
Este archivo contiene la configuración de Redis del backend.
"""
import logging
from typing import Optional
from pydantic import field_validator, Field
import secrets

# Configurar logging
logger = logging.getLogger(__name__)

class RedisSettings:
    """Configuración específica de Redis"""
    
    # Redis
    REDIS_HOST: str = Field(default='localhost', alias='GYM_REDIS_HOST')
    REDIS_PORT: int = Field(default=6379, alias='GYM_REDIS_PORT')
    REDIS_PASSWORD: str = Field(default='', alias='GYM_REDIS_PASSWORD')
    REDIS_DB: int = Field(default=0, alias='GYM_REDIS_DB')
    REDIS_SSL: bool = Field(default=False, alias='GYM_REDIS_SSL')
    REDIS_SSL_CERT_REQS: str = Field(default='required', alias='GYM_REDIS_SSL_CERT_REQS')
    
    # Pool de conexiones Redis
    REDIS_POOL_SIZE: int = Field(default=10, alias='GYM_REDIS_POOL_SIZE')
    REDIS_MAX_CONNECTIONS: int = Field(default=20, alias='GYM_REDIS_MAX_CONNECTIONS')
    REDIS_CONNECT_TIMEOUT: int = Field(default=5, alias='GYM_REDIS_CONNECT_TIMEOUT')
    REDIS_READ_TIMEOUT: int = Field(default=5, alias='GYM_REDIS_READ_TIMEOUT')
    REDIS_WRITE_TIMEOUT: int = Field(default=5, alias='GYM_REDIS_WRITE_TIMEOUT')
    
    # Configuración de cache
    REDIS_CACHE_TTL: int = Field(default=3600, alias='GYM_REDIS_CACHE_TTL')
    REDIS_SESSION_TTL: int = Field(default=1800, alias='GYM_REDIS_SESSION_TTL')
    REDIS_RATE_LIMIT_TTL: int = Field(default=60, alias='GYM_REDIS_RATE_LIMIT_TTL')

    @field_validator("REDIS_PASSWORD")
    @classmethod
    def validate_redis_password(cls, v: str, info) -> str:
        """Validar que la contraseña de Redis sea segura"""
        if info.data.get("ENV") == "production":
            if not v or len(v) < 16:
                logger.error("REDIS_PASSWORD es demasiado corta para producción (mínimo 16 caracteres)")
                raise ValueError("REDIS_PASSWORD debe tener al menos 16 caracteres en producción")
            
            # Validar contraseñas inseguras
            insecure_passwords = [
                "password", "123456", "redis", "admin", "test", "demo", "example",
                "CHANGE_THIS_REDIS_PASSWORD_IN_PRODUCTION_USE_SECURE_PASSWORD",
                "RdS!2024$z8x7c6v5b4n3m2a1s0d9"  # Valor de ejemplo
            ]
            if v in insecure_passwords:
                logger.error("REDIS_PASSWORD usa valores por defecto inseguros en producción")
                raise ValueError("REDIS_PASSWORD no puede usar valores por defecto en producción")
            
            # Validar que la contraseña contenga caracteres complejos
            if not (any(c.isupper() for c in v) and 
                   any(c.islower() for c in v) and 
                   any(c.isdigit() for c in v) and
                   any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v)):
                logger.error("REDIS_PASSWORD debe contener mayúsculas, minúsculas, números y caracteres especiales en producción")
                raise ValueError("REDIS_PASSWORD debe ser compleja en producción")
        
        if not v or len(v) < 8:
            logger.warning("REDIS_PASSWORD es demasiado corta, generando una nueva")
            v = secrets.token_urlsafe(16)
        
        return v

    @field_validator("REDIS_SSL_CERT_REQS")
    @classmethod
    def validate_ssl_cert_reqs(cls, v: str, info) -> str:
        """Validar configuración SSL de Redis"""
        valid_values = ['none', 'optional', 'required']
        if v not in valid_values:
            raise ValueError(f"REDIS_SSL_CERT_REQS debe ser uno de: {valid_values}")
        
        if info.data.get("ENV") == "production" and v == 'none':
            logger.warning("REDIS_SSL_CERT_REQS está configurado como 'none' en producción")
        
        return v

    def get_redis_url(self) -> str:
        """Obtener URL de Redis construida"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def get_redis_config(self) -> dict:
        """Obtener configuración de Redis para el cliente"""
        config = {
            'host': self.REDIS_HOST,
            'port': self.REDIS_PORT,
            'db': self.REDIS_DB,
            'ssl': self.REDIS_SSL,
            'ssl_cert_reqs': self.REDIS_SSL_CERT_REQS,
            'max_connections': self.REDIS_MAX_CONNECTIONS,
            'connect_timeout': self.REDIS_CONNECT_TIMEOUT,
            'read_timeout': self.REDIS_READ_TIMEOUT,
            'write_timeout': self.REDIS_WRITE_TIMEOUT,
        }
        
        if self.REDIS_PASSWORD:
            config['password'] = self.REDIS_PASSWORD
        
        return config 