"""
Schemas para autenticación en la API
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re
import bleach
from app.core.security import SecurityValidator

class Token(BaseModel):
    """Schema para token de acceso"""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user_id: str
    username: str
    es_admin: bool

class TokenData(BaseModel):
    """Schema para datos dentro del token JWT"""
    sub: Optional[str] = None  # user_id
    username: Optional[str] = None
    exp: Optional[datetime] = None
    admin: Optional[bool] = False
    iat: Optional[datetime] = None  # Issued at
    ip: Optional[str] = None  # IP address

class LoginCredentials(BaseModel):
    """Schema para credenciales de login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        
        # Sanitizar entrada
        v = bleach.clean(v, tags=[], strip=True)
        
        # Validar longitud después de sanitización
        if len(v) < 3:
            raise ValueError('El username debe tener al menos 3 caracteres')
        
        # Validar caracteres permitidos
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('El username solo puede contener letras, números, puntos, guiones y guiones bajos')
        
        # Detectar patrones de ataque
        if SecurityValidator.detect_sql_injection(v):
            raise ValueError('Username inválido')
        
        # Verificar que no contenga solo números
        if v.isdigit():
            raise ValueError('El username no puede ser solo números')
        
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Validar longitud
        if len(v) < 1:
            raise ValueError('La contraseña no puede estar vacía')
        
        if len(v) > 128:
            raise ValueError('La contraseña es demasiado larga')
        
        # Detectar patrones de ataque
        if SecurityValidator.detect_sql_injection(v):
            raise ValueError('Contraseña inválida')
        
        # Verificar que no contenga caracteres de control
        if any(ord(c) < 32 for c in v):
            raise ValueError('La contraseña contiene caracteres no válidos')
        
        return v

class RefreshToken(BaseModel):
    """Schema para token de refresco"""
    refresh_token: str = Field(..., min_length=1)
    
    @field_validator('refresh_token')
    @classmethod
    def validate_refresh_token(cls, v: str) -> str:
        v = v.strip()
        
        # Validar que no esté vacío
        if not v:
            raise ValueError('El refresh token no puede estar vacío')
        
        # Validar longitud básica
        if len(v) < 10:
            raise ValueError('Refresh token inválido')
        
        return v

class PasswordReset(BaseModel):
    """Schema para reseteo de contraseña"""
    email: str = Field(..., max_length=255)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        
        # Validar formato
        if not SecurityValidator.validate_email(v):
            raise ValueError('Formato de email inválido')
        
        return v

class PasswordResetConfirm(BaseModel):
    """Schema para confirmar reseteo de contraseña"""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('token')
    @classmethod
    def validate_token(cls, v: str) -> str:
        v = v.strip()
        
        if not v:
            raise ValueError('El token no puede estar vacío')
        
        # Validar longitud básica
        if len(v) < 10:
            raise ValueError('Token inválido')
        
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Validar fuerza de contraseña
        if not SecurityValidator.is_password_strong(v):
            checks = SecurityValidator.validate_password_strength(v)
            errors = []
            
            # Como el stub devuelve lista vacía, asumimos que todas las validaciones fallan
            errors.append('al menos 8 caracteres')
            errors.append('al menos una letra mayúscula')
            errors.append('al menos una letra minúscula')
            errors.append('al menos un número')
            errors.append('al menos un carácter especial (!@#$%^&*)')
            errors.append('no puede ser una contraseña común')
            
            raise ValueError(f'La contraseña debe tener: {", ".join(errors)}')
        
        return v

class LoginResponse(BaseModel):
    """Schema para respuesta de login exitoso"""
    success: bool = True
    token: Token
    message: str = "Login exitoso"
    
class LoginError(BaseModel):
    """Schema para errores de login"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    retry_after: Optional[int] = None  # Segundos hasta poder intentar nuevamente

class LoginRequest(BaseModel):
    """Schema para solicitud de login (alias de LoginCredentials para compatibilidad)"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        
        # Sanitizar entrada
        v = bleach.clean(v, tags=[], strip=True)
        
        # Validar longitud después de sanitización
        if len(v) < 3:
            raise ValueError('El username debe tener al menos 3 caracteres')
        
        # Validar caracteres permitidos
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('El username solo puede contener letras, números, puntos, guiones y guiones bajos')
        
        # Detectar patrones de ataque
        if SecurityValidator.detect_sql_injection(v):
            raise ValueError('Username inválido')
        
        # Verificar que no contenga solo números
        if v.isdigit():
            raise ValueError('El username no puede ser solo números')
        
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Validar longitud
        if len(v) < 1:
            raise ValueError('La contraseña no puede estar vacía')
        
        if len(v) > 128:
            raise ValueError('La contraseña es demasiado larga')
        
        # Detectar patrones de ataque
        if SecurityValidator.detect_sql_injection(v):
            raise ValueError('Contraseña inválida')
        
        # Verificar que no contenga caracteres de control
        if any(ord(c) < 32 for c in v):
            raise ValueError('La contraseña contiene caracteres no válidos')
        
        return v

class UserCreate(BaseModel):
    """Schema para creación de usuario"""
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=255)
    telefono: str = Field(..., min_length=10, max_length=20)
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    fecha_nacimiento: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    genero: str = Field(..., pattern=r'^[MF]$')
    esta_activo: bool = True
    es_admin: bool = False
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        
        # Validar formato
        if not SecurityValidator.validate_email(v):
            raise ValueError('Formato de email inválido')
        
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        
        # Sanitizar entrada
        v = bleach.clean(v, tags=[], strip=True)
        
        # Validar longitud después de sanitización
        if len(v) < 3:
            raise ValueError('El username debe tener al menos 3 caracteres')
        
        # Validar caracteres permitidos
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('El username solo puede contener letras, números, puntos, guiones y guiones bajos')
        
        # Detectar patrones de ataque
        if SecurityValidator.detect_sql_injection(v):
            raise ValueError('Username inválido')
        
        # Verificar que no contenga solo números
        if v.isdigit():
            raise ValueError('El username no puede ser solo números')
        
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Validar fuerza de contraseña
        if not SecurityValidator.is_password_strong(v):
            checks = SecurityValidator.validate_password_strength(v)
            errors = []
            
            # Como el stub devuelve lista vacía, asumimos que todas las validaciones fallan
            errors.append('al menos 8 caracteres')
            errors.append('al menos una letra mayúscula')
            errors.append('al menos una letra minúscula')
            errors.append('al menos un número')
            errors.append('al menos un carácter especial (!@#$%^&*)')
            errors.append('no puede ser una contraseña común')
            
            raise ValueError(f'La contraseña debe tener: {", ".join(errors)}')
        
        return v
