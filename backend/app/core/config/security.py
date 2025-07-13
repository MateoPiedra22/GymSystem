"""
Backend - Configuración de seguridad
Este archivo contiene la configuración de seguridad del backend.
"""
import secrets
import logging
from typing import List, Optional
from pydantic import field_validator, Field

# Configurar logging
logger = logging.getLogger(__name__)

class SecuritySettings:
    """Configuración específica de seguridad"""
    
    # Seguridad - Configuración JWT con valores seguros por defecto
    SECRET_KEY: str = Field(default="", alias='GYM_SECRET_KEY')
    JWT_SECRET_KEY: str = Field(default="", alias='GYM_JWT_SECRET_KEY')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, alias='GYM_ACCESS_TOKEN_EXPIRE_MINUTES')
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, alias='GYM_REFRESH_TOKEN_EXPIRE_DAYS')
    ALGORITHM: str = Field(default="HS256", alias='GYM_ALGORITHM')
    BCRYPT_ROUNDS: int = Field(default=14, alias='GYM_BCRYPT_ROUNDS')
    
    # Configuración de seguridad adicional
    BACKUP_ENCRYPTION_KEY: str = Field(default="", alias='GYM_BACKUP_KEY')
    FORCE_HTTPS: bool = Field(default=True, alias='GYM_FORCE_HTTPS')
    SECURE_COOKIES: bool = Field(default=True, alias='GYM_SECURE_COOKIES')
    SAMESITE_COOKIES: str = Field(default="strict", alias='GYM_SAMESITE_COOKIES')

    # Admin User - Leído desde variables de entorno con validación mejorada
    ADMIN_USERNAME: str = Field(default="admin", alias='ADMIN_USERNAME')
    ADMIN_EMAIL: str = Field(default="admin@gymnasium.local", alias='ADMIN_EMAIL')
    ADMIN_PASSWORD: str = Field(default="AdMiN!2024$z9x8c7v6b5n4m3a2s1d0", alias='ADMIN_PASSWORD')

    # CORS con configuración más restrictiva por defecto
    ALLOWED_ORIGINS: Optional[List[str]] = Field(default=None, alias='GYM_CORS_ORIGINS')
    ALLOWED_METHODS: Optional[List[str]] = Field(default=None, alias='GYM_CORS_METHODS')
    ALLOWED_HEADERS: Optional[List[str]] = Field(default=None, alias='GYM_CORS_HEADERS')
    
    # Seguridad adicional con configuraciones más estrictas
    ENABLE_SECURITY_HEADERS: bool = Field(default=True, alias='GYM_SECURITY_HEADERS')
    ENABLE_INPUT_VALIDATION: bool = Field(default=True, alias='GYM_INPUT_VALIDATION')
    ENABLE_ATTACK_DETECTION: bool = Field(default=True, alias='GYM_ATTACK_DETECTION')
    ENABLE_CSRF_PROTECTION: bool = Field(default=True, alias='GYM_CSRF_PROTECTION')
    ENABLE_RATE_LIMITING: bool = Field(default=True, alias='GYM_RATE_LIMITING')

    # Límites y timeouts más estrictos
    SESSION_TIMEOUT_MINUTES: int = Field(default=30, alias='GYM_SESSION_TIMEOUT')
    MAX_FAILED_LOGIN_ATTEMPTS: int = Field(default=3, alias='GYM_MAX_LOGIN_ATTEMPTS')
    ACCOUNT_LOCKOUT_MINUTES: int = Field(default=30, alias='GYM_LOCKOUT_TIME')
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, alias='GYM_RATE_LIMIT')
    MAX_UPLOAD_SIZE: int = Field(default=10485760, alias='GYM_MAX_UPLOAD_SIZE')
    MAX_REQUEST_SIZE: int = Field(default=20971520, alias='GYM_MAX_REQUEST_SIZE')

    # Configuración de seguridad adicional
    TRUSTED_PROXIES: List[str] = Field(default=[], alias='GYM_TRUSTED_PROXIES')
    ENABLE_AUDIT_LOG: bool = Field(default=True, alias='GYM_AUDIT_LOG')
    ENABLE_IP_WHITELIST: bool = Field(default=False, alias='GYM_IP_WHITELIST')
    ALLOWED_IPS: List[str] = Field(default=[], alias='GYM_ALLOWED_IPS')

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_secure(cls, v: str, info) -> str:
        """Validar que la clave secreta sea segura"""
        insecure_values = [
            "changeme", "changeme_dev_only", "secret", "mysecret", "dev_secret",
            "default", "password", "123456", "admin", "test", "demo", "example",
            "CAMBIAR_ESTA_CLAVE_SECRETA", "your-secret-key", "replace-me",
            "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION_USE_SECURE_RANDOM_GENERATOR",
            "CHANGE_THIS_TO_SECURE_SECRET_KEY_GENERATED_WITH_SECRETS_TOKEN_URLSAFE_64",
            "QwErTyUiOpAsDfGhJkLzXcVbNm1234567890!@#$%^&*()_+AaBbCcDdEeFfGgHh"
        ]
        
        if info.data.get("ENV") == "production":
            if not v or len(v) < 64:
                raise ValueError("ERROR: La clave secreta (SECRET_KEY) es demasiado corta para producción. Debe tener al menos 64 caracteres y ser única. Consulta la documentación para generar una clave segura.")
            if any(insecure in v.lower() for insecure in insecure_values):
                raise ValueError("ERROR: La clave secreta (SECRET_KEY) contiene valores inseguros o de ejemplo. Debes cambiarla por una clave única y segura. Consulta la documentación para más ayuda.")
            if not any(c.isupper() for c in v) or not any(c.islower() for c in v) or not any(c.isdigit() for c in v):
                raise ValueError("ERROR: La clave secreta (SECRET_KEY) debe contener mayúsculas, minúsculas y números para ser segura en producción.")
        
        if not v or len(v) < 32:
            logger.warning("SECRET_KEY es demasiado corta, generando una nueva")
            v = secrets.token_urlsafe(64)
        
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_secret_key_must_be_secure(cls, v: str, info) -> str:
        """Validar que la clave JWT sea segura"""
        insecure_values = [
            "changeme", "changeme_dev_only", "jwt", "token", "dev_jwt",
            "default", "password", "123456", "admin", "test", "demo", "example",
            "CAMBIAR_ESTA_CLAVE_JWT", "your-jwt-secret", "replace-me",
            "CHANGE_THIS_JWT_SECRET_IN_PRODUCTION_USE_SECURE_RANDOM_GENERATOR",
            "CHANGE_THIS_TO_SECURE_JWT_SECRET_KEY_GENERATED_WITH_SECRETS_TOKEN_URLSAFE_64"
        ]
        
        if info.data.get("ENV") == "production":
            if not v or len(v) < 64:
                logger.error("JWT_SECRET_KEY es demasiado corta para producción (mínimo 64 caracteres)")
                raise ValueError("JWT_SECRET_KEY debe tener al menos 64 caracteres en producción")
            if any(insecure in v.lower() for insecure in insecure_values):
                logger.error("JWT_SECRET_KEY contiene valores inseguros en producción")
                raise ValueError("JWT_SECRET_KEY no puede contener valores por defecto en producción")
            if not any(c.isupper() for c in v) or not any(c.islower() for c in v) or not any(c.isdigit() for c in v):
                logger.error("JWT_SECRET_KEY debe contener mayúsculas, minúsculas y números en producción")
                raise ValueError("JWT_SECRET_KEY debe ser compleja en producción")
        
        if not v or len(v) < 32:
            logger.warning("JWT_SECRET_KEY es demasiado corta, generando una nueva")
            v = secrets.token_urlsafe(64)
        
        return v

    @field_validator("BACKUP_ENCRYPTION_KEY")
    @classmethod
    def backup_key_must_be_secure(cls, v: str, info) -> str:
        """Validar que la clave de backup sea segura"""
        insecure_values = [
            "changeme", "changeme_dev_only", "backup", "key", "dev_backup",
            "CHANGE_THIS_BACKUP_KEY_IN_PRODUCTION_USE_SECURE_RANDOM_GENERATOR",
            "CHANGE_THIS_TO_SECURE_BACKUP_KEY_GENERATED_WITH_SECRETS_TOKEN_URLSAFE_32"
        ]
        
        if info.data.get("ENV") == "production":
            if not v or len(v) < 32:
                raise ValueError("BACKUP_ENCRYPTION_KEY debe tener al menos 32 caracteres en producción")
            if any(insecure in v.lower() for insecure in insecure_values):
                raise ValueError("BACKUP_ENCRYPTION_KEY no puede contener valores inseguros en producción")
        
        if not v or len(v) < 16:
            logger.warning("BACKUP_ENCRYPTION_KEY es demasiado corta, generando una nueva")
            v = secrets.token_urlsafe(32)
        
        return v

    @field_validator("ADMIN_PASSWORD")
    @classmethod
    def admin_password_must_be_secure(cls, v: str, info) -> str:
        """Validar que la contraseña del admin sea segura"""
        insecure_values = [
            "changeme123", "admin123", "password", "123456", "admin", "gympass",
            "CHANGE_THIS_ADMIN_PASSWORD_IN_PRODUCTION_USE_SECURE_PASSWORD"
        ]
        
        if info.data.get("ENV") == "production":
            if not v or len(v) < 16:
                logger.error("ADMIN_PASSWORD es demasiado débil para producción (mínimo 16 caracteres)")
                raise ValueError("ADMIN_PASSWORD debe tener al menos 16 caracteres en producción")
            if v.lower() in insecure_values:
                logger.error("ADMIN_PASSWORD usa valores por defecto inseguros en producción")
                raise ValueError("ADMIN_PASSWORD no puede usar valores por defecto en producción")
            if not any(c.isupper() for c in v) or not any(c.islower() for c in v) or not any(c.isdigit() for c in v) or not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
                logger.error("ADMIN_PASSWORD debe contener mayúsculas, minúsculas, números y caracteres especiales en producción")
                raise ValueError("ADMIN_PASSWORD debe ser compleja en producción")
        
        if not v or len(v) < 12:
            logger.warning("ADMIN_PASSWORD es demasiado débil, generando una nueva")
            v = secrets.token_urlsafe(16)
        
        return v

    @field_validator("ALLOWED_ORIGINS", mode='before')
    @classmethod
    def origins_must_be_secure_in_prod(cls, v, info) -> List[str]:
        """Validar que los orígenes CORS sean seguros en producción"""
        # Permitir None o vacío
        if v is None:
            v = []
        # Procesar string a lista si es necesario
        if isinstance(v, str):
            v = [origin.strip() for origin in v.split(',') if origin.strip()]
        elif not isinstance(v, list):
            v = []
        # Ahora v siempre es lista
        if info.data.get("ENV") == "production":
            if v and "*" in v:
                raise ValueError("No se permite '*' en CORS en producción")
            if v and any("localhost" in origin.lower() or "127.0.0.1" in origin for origin in v):
                raise ValueError("No se permiten localhost o 127.0.0.1 en CORS en producción")
            if v and any(not origin.startswith("https://") for origin in v):
                raise ValueError("Todos los orígenes deben usar HTTPS en producción")
        return v

    @field_validator("ALLOWED_METHODS", mode='before')
    @classmethod
    def methods_must_be_secure(cls, v, info) -> List[str]:
        if v is None:
            v = []
        if isinstance(v, str):
            v = [method.strip().upper() for method in v.split(',') if method.strip()]
        elif not isinstance(v, list):
            v = []
        if info.data.get("ENV") == "production":
            dangerous_methods = ["DELETE", "PUT", "PATCH"]
            if v and any(method in v for method in dangerous_methods):
                logger.warning("Métodos peligrosos detectados en producción")
        return v

    @field_validator("ALLOWED_HEADERS", mode='before')
    @classmethod
    def headers_must_be_restrictive(cls, v, info) -> List[str]:
        if v is None:
            v = []
        if isinstance(v, str):
            v = [header.strip() for header in v.split(',') if header.strip()]
        elif not isinstance(v, list):
            v = []
        if info.data.get("ENV") == "production":
            if "*" in v:
                raise ValueError("ALLOWED_HEADERS no debe usar wildcard (*) en producción por razones de seguridad")
        return v

    @field_validator("BCRYPT_ROUNDS")
    @classmethod
    def validate_bcrypt_rounds(cls, v: int, info) -> int:
        """Validar rounds de bcrypt según el entorno"""
        if info.data.get("ENV") == "production":
            if v < 12:
                raise ValueError("BCRYPT_ROUNDS debe ser al menos 12 en producción")
        if v < 10 or v > 20:
            raise ValueError("BCRYPT_ROUNDS debe estar entre 10 y 20")
        return v

    @field_validator("RATE_LIMIT_PER_MINUTE")
    @classmethod
    def validate_rate_limit(cls, v: int, info) -> int:
        """Validar límites de tasa según el entorno"""
        if info.data.get("ENV") == "production" and v > 100:
            logger.warning("RATE_LIMIT_PER_MINUTE muy alto para producción, considere reducir")
        if v < 1 or v > 1000:
            raise ValueError("RATE_LIMIT_PER_MINUTE debe estar entre 1 y 1000")
        return v

    @field_validator("MAX_FAILED_LOGIN_ATTEMPTS")
    @classmethod
    def validate_login_attempts(cls, v: int, info) -> int:
        """Validar intentos de login según el entorno"""
        if info.data.get("ENV") == "production" and v > 5:
            logger.warning("MAX_FAILED_LOGIN_ATTEMPTS muy alto para producción")
        if v < 1 or v > 10:
            raise ValueError("MAX_FAILED_LOGIN_ATTEMPTS debe estar entre 1 y 10")
        return v

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_token_expiration(cls, v: int, info) -> int:
        """Validar expiración de tokens según el entorno"""
        if info.data.get("ENV") == "production" and v > 60:
            logger.warning("ACCESS_TOKEN_EXPIRE_MINUTES muy alto para producción")
        if v < 5 or v > 1440:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES debe estar entre 5 y 1440 minutos")
        return v

    def get_cors_config(self) -> dict:
        """Obtener configuración CORS segura"""
        return {
            "allow_origins": self.ALLOWED_ORIGINS,
            "allow_credentials": True,
            "allow_methods": self.ALLOWED_METHODS,
            "allow_headers": self.ALLOWED_HEADERS,
            "max_age": 86400,
            "expose_headers": ["X-Total-Count", "X-Page-Count"]
        }

    def get_security_config(self) -> dict:
        """Obtener configuración de seguridad"""
        return {
            "force_https": self.FORCE_HTTPS,
            "secure_cookies": self.SECURE_COOKIES,
            "samesite_cookies": self.SAMESITE_COOKIES,
            "enable_security_headers": self.ENABLE_SECURITY_HEADERS,
            "enable_input_validation": self.ENABLE_INPUT_VALIDATION,
            "enable_attack_detection": self.ENABLE_ATTACK_DETECTION,
            "enable_csrf_protection": self.ENABLE_CSRF_PROTECTION,
            "enable_rate_limiting": self.ENABLE_RATE_LIMITING
        }

    def validate_production_security(self) -> List[str]:
        """Validar configuración de seguridad para producción"""
        issues = []
        
        # Obtener ENV desde info.data si está disponible, o usar un valor por defecto
        env = getattr(self, 'ENV', 'development')
        
        if env == "production":
            # Validar HTTPS
            if not self.FORCE_HTTPS:
                issues.append("FORCE_HTTPS debe estar habilitado en producción")
            
            # Validar cookies seguras
            if not self.SECURE_COOKIES:
                issues.append("SECURE_COOKIES debe estar habilitado en producción")
            
            # Validar CORS
            if "*" in self.ALLOWED_ORIGINS:
                issues.append("CORS no debe permitir '*' en producción")
            
            # Validar rate limiting
            if not self.ENABLE_RATE_LIMITING:
                issues.append("RATE_LIMITING debe estar habilitado en producción")
            
            # Validar headers de seguridad
            if not self.ENABLE_SECURITY_HEADERS:
                issues.append("SECURITY_HEADERS debe estar habilitado en producción")
        
        return issues 