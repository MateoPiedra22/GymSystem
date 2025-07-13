"""
Schemas para usuarios en la API
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from pydantic_core.core_schema import ValidationInfo
from typing import Optional, List
from datetime import datetime, date
import re
import bleach
from app.core.security import SecurityValidator, SecurityUtils

# Schema para Rol
class RolBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=255)
    
    @field_validator('nombre')
    @classmethod
    def validate_nombre(cls, v: str) -> str:
        # Sanitizar HTML
        v = bleach.clean(v.strip(), tags=[], strip=True)
        
        # Validar caracteres permitidos
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s\-_]+$', v):
            raise ValueError('El nombre del rol solo puede contener letras, espacios, guiones y guiones bajos')
        
        return v
    
    @field_validator('descripcion')
    @classmethod
    def validate_descripcion(cls, v: Optional[str]) -> Optional[str]:
        if v:
            # Sanitizar HTML permitiendo solo tags básicos
            v = bleach.clean(v.strip(), tags=['b', 'i', 'em', 'strong'], strip=True)
        return v

class RolCreate(RolBase):
    pass

class RolUpdate(RolBase):
    nombre: Optional[str] = Field(None, min_length=1, max_length=50)

class RolInDB(RolBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# Schemas para Usuario
class UsuarioBase(BaseModel):
    """Schema base para datos de usuario"""
    email: EmailStr = Field(..., max_length=255)
    username: str = Field(..., min_length=3, max_length=20)
    nombre: str = Field(..., min_length=1, max_length=50)
    apellido: str = Field(..., min_length=1, max_length=50)
    fecha_nacimiento: Optional[date] = None
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=255)
    objetivo: Optional[str] = Field(None, max_length=500)
    notas: Optional[str] = Field(None, max_length=1000)
    peso_inicial: Optional[int] = Field(None, ge=20000, le=500000)  # 20kg - 500kg en gramos
    altura: Optional[int] = Field(None, ge=500, le=2500)  # 50cm - 250cm en milímetros
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not SecurityValidator.validate_email(v):
            raise ValueError('Formato de email inválido')
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        
        # Validar con SecurityValidator
        if not SecurityValidator.validate_username(v):
            raise ValueError('El nombre de usuario debe tener 3-20 caracteres y solo puede contener letras, números, guiones y guiones bajos')
        
        # Verificar que no sea solo números
        if v.isdigit():
            raise ValueError('El nombre de usuario no puede ser solo números')
        
        # Verificar palabras prohibidas
        prohibited_words = ['admin', 'administrator', 'root', 'system', 'test', 'user', 'null']
        if v in prohibited_words:
            raise ValueError('Nombre de usuario no permitido')
        
        return v
    
    @field_validator('nombre', 'apellido')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        
        # Sanitizar HTML
        v = bleach.clean(v, tags=[], strip=True)
        
        # Validar caracteres permitidos (letras, espacios, acentos, apostrofes)
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s\'\.]+$', v):
            raise ValueError('Solo se permiten letras, espacios, acentos y apostrofes')
        
        # Validar longitud
        if len(v) < 1:
            raise ValueError('El nombre no puede estar vacío')
        
        return v
    
    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v:
            # Limpiar espacios y caracteres especiales
            v = re.sub(r'[^\d+]', '', v.strip())
            
            # Validar formato
            if not re.match(r'^\+?[0-9]{8,15}$', v):
                raise ValueError('Formato de teléfono inválido. Debe tener 8-15 dígitos y puede incluir +')
            
            # Verificar que no sea solo el código de país
            if len(v.replace('+', '')) < 8:
                raise ValueError('Número de teléfono demasiado corto')
        
        return v
    
    @field_validator('direccion')
    @classmethod
    def validate_direccion(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            
            # Sanitizar HTML
            v = bleach.clean(v, tags=[], strip=True)
            
            # Validar longitud
            if len(v) < 5:
                raise ValueError('La dirección debe tener al menos 5 caracteres')
            
            # Validar caracteres permitidos
            if not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚüÜñÑ\s\-_#.,]+$', v):
                raise ValueError('La dirección contiene caracteres no permitidos')
        
        return v
    
    @field_validator('objetivo')
    @classmethod
    def validate_objetivo(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            
            # Sanitizar HTML permitiendo solo tags básicos
            v = bleach.clean(v, tags=['b', 'i', 'em', 'strong'], strip=True)
            
            # Validar longitud
            if len(v) > 500:
                raise ValueError('El objetivo no puede exceder 500 caracteres')
        
        return v
    
    @field_validator('notas')
    @classmethod
    def validate_notas(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            
            # Sanitizar HTML permitiendo solo tags básicos
            v = bleach.clean(v, tags=['b', 'i', 'em', 'strong', 'p', 'br'], strip=True)
            
            # Validar longitud
            if len(v) > 1000:
                raise ValueError('Las notas no pueden exceder 1000 caracteres')
        
        return v
    
    @field_validator('fecha_nacimiento')
    @classmethod
    def validate_fecha_nacimiento(cls, v: Optional[date]) -> Optional[date]:
        if v:
            # Verificar edad mínima y máxima
            today = date.today()
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            
            if age < 13:
                raise ValueError('La edad mínima es 13 años')
            
            if age > 120:
                raise ValueError('Fecha de nacimiento no válida')
            
            # Verificar que no sea fecha futura
            if v > today:
                raise ValueError('La fecha de nacimiento no puede ser futura')
        
        return v

class UsuarioCreate(UsuarioBase):
    """Schema para crear un nuevo usuario"""
    password: str = Field(..., min_length=8, max_length=128)
    es_admin: Optional[bool] = False
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Validar fuerza de contraseña
        if not SecurityValidator.is_password_strong(v):
            checks = SecurityValidator.validate_password_strength(v)
            errors = []
            
            if not checks['length']:
                errors.append('al menos 8 caracteres')
            if not checks['uppercase']:
                errors.append('al menos una letra mayúscula')
            if not checks['lowercase']:
                errors.append('al menos una letra minúscula')
            if not checks['digit']:
                errors.append('al menos un número')
            if not checks['special']:
                errors.append('al menos un carácter especial (!@#$%^&*)')
            if not checks['no_common']:
                errors.append('no puede ser una contraseña común')
            
            raise ValueError(f'La contraseña debe tener: {", ".join(errors)}')
        
        return v

class UsuarioUpdate(BaseModel):
    """Schema para actualizar datos de usuario"""
    email: Optional[EmailStr] = Field(None, max_length=255)
    nombre: Optional[str] = Field(None, min_length=1, max_length=50)
    apellido: Optional[str] = Field(None, min_length=1, max_length=50)
    fecha_nacimiento: Optional[date] = None
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=255)
    objetivo: Optional[str] = Field(None, max_length=500)
    notas: Optional[str] = Field(None, max_length=1000)
    peso_inicial: Optional[int] = Field(None, ge=20000, le=500000)
    altura: Optional[int] = Field(None, ge=500, le=2500)
    esta_activo: Optional[bool] = None
    
    # Aplicar las mismas validaciones que UsuarioBase
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip().lower()
            if not SecurityValidator.validate_email(v):
                raise ValueError('Formato de email inválido')
        return v
    
    @field_validator('nombre', 'apellido')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            v = bleach.clean(v, tags=[], strip=True)
            
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s\'\.]+$', v):
                raise ValueError('Solo se permiten letras, espacios, acentos y apostrofes')
            
            if len(v) < 1:
                raise ValueError('El nombre no puede estar vacío')
        
        return v
    
    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = re.sub(r'[^\d+]', '', v.strip())
            
            if not re.match(r'^\+?[0-9]{8,15}$', v):
                raise ValueError('Formato de teléfono inválido')
            
            if len(v.replace('+', '')) < 8:
                raise ValueError('Número de teléfono demasiado corto')
        
        return v
    
    @field_validator('direccion')
    @classmethod
    def validate_direccion(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            v = bleach.clean(v, tags=[], strip=True)
            
            if len(v) < 5:
                raise ValueError('La dirección debe tener al menos 5 caracteres')
            
            if not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚüÜñÑ\s\-_#.,]+$', v):
                raise ValueError('La dirección contiene caracteres no permitidos')
        
        return v
    
    @field_validator('objetivo')
    @classmethod
    def validate_objetivo(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            v = bleach.clean(v, tags=['b', 'i', 'em', 'strong'], strip=True)
            
            if len(v) > 500:
                raise ValueError('El objetivo no puede exceder 500 caracteres')
        
        return v
    
    @field_validator('notas')
    @classmethod
    def validate_notas(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            v = bleach.clean(v, tags=['b', 'i', 'em', 'strong', 'p', 'br'], strip=True)
            
            if len(v) > 1000:
                raise ValueError('Las notas no pueden exceder 1000 caracteres')
        
        return v
    
    @field_validator('fecha_nacimiento')
    @classmethod
    def validate_fecha_nacimiento(cls, v: Optional[date]) -> Optional[date]:
        if v:
            today = date.today()
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            
            if age < 13:
                raise ValueError('La edad mínima es 13 años')
            
            if age > 120:
                raise ValueError('Fecha de nacimiento no válida')
            
            if v > today:
                raise ValueError('La fecha de nacimiento no puede ser futura')
        
        return v

class UsuarioInDB(UsuarioBase):
    """Schema para datos de usuario en DB"""
    id: str
    esta_activo: bool
    es_admin: bool
    fecha_registro: datetime
    ultimo_acceso: Optional[datetime] = None
    fecha_inicio: datetime
    roles: List[RolInDB] = []
    
    model_config = ConfigDict(from_attributes=True)

class UsuarioOut(UsuarioBase):
    """Schema para datos de usuario devueltos por la API"""
    id: str
    esta_activo: bool
    es_admin: bool
    fecha_registro: datetime
    fecha_inicio: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @property
    def nombre_completo(self) -> str:
        """Devuelve el nombre completo del usuario"""
        return f"{self.nombre} {self.apellido}"
    
    @property
    def edad(self) -> Optional[int]:
        """Calcula la edad basada en fecha de nacimiento"""
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None
    
    @property
    def imc(self) -> Optional[float]:
        """Calcula el IMC si peso y altura están disponibles"""
        if self.peso_inicial and self.altura:
            # Convertir de gramos a kg y de mm a metros
            peso_kg = self.peso_inicial / 1000
            altura_m = self.altura / 1000
            imc = peso_kg / (altura_m ** 2)
            return round(imc, 1)
        return None

class ChangePassword(BaseModel):
    """Schema para cambio de contraseña"""
    current_password: str = Field(..., max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Validar fuerza de contraseña
        if not SecurityValidator.is_password_strong(v):
            checks = SecurityValidator.validate_password_strength(v)
            errors = []
            
            if not checks['length']:
                errors.append('al menos 8 caracteres')
            if not checks['uppercase']:
                errors.append('al menos una letra mayúscula')
            if not checks['lowercase']:
                errors.append('al menos una letra minúscula')
            if not checks['digit']:
                errors.append('al menos un número')
            if not checks['special']:
                errors.append('al menos un carácter especial (!@#$%^&*)')
            if not checks['no_common']:
                errors.append('no puede ser una contraseña común')
            
            raise ValueError(f'La contraseña debe tener: {", ".join(errors)}')
        
        return v
