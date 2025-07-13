"""
Módulo central para autenticación y autorización
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated, Union
import secrets
import hashlib

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.core.config import settings
from app.schemas.auth import TokenData
from app.core.database import get_db
from app.models.usuarios import Usuario

# Configuración OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/json")

def _validate_jwt_payload(payload: dict) -> TokenData:
    """Validar y extraer datos del payload JWT"""
    # Validar claims requeridos
    user_id: Optional[str] = payload.get("sub")
    username: Optional[str] = payload.get("username")
    admin: bool = payload.get("admin", False)
    issuer: Optional[str] = payload.get("iss")
    audience: Optional[str] = payload.get("aud")
    jti: Optional[str] = payload.get("jti")  # JWT ID para revocación
    exp: Optional[int] = payload.get("exp")  # Expiración
    iat: Optional[int] = payload.get("iat")  # Emitido en
    
    # Validar que todos los claims requeridos estén presentes
    if not all([user_id, username, issuer, audience, jti, exp, iat]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas - claims faltantes",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validar que el token no haya expirado
    current_time = datetime.now(timezone.utc).timestamp()
    if exp and current_time > exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validar que el token no sea del futuro
    if iat and current_time < iat - 300:  # 5 minutos de tolerancia
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token emitido en el futuro",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenData(sub=user_id, username=username, admin=admin)

def _validate_token_issuer_audience(issuer: str, audience: str):
    """Validar issuer y audience del token"""
    # Validar issuer (debe ser nuestro dominio)
    expected_issuer = f"gym-system-{settings.ENV}"
    if issuer != expected_issuer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token emitido por fuente no autorizada",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validar audience (debe ser nuestro cliente)
    expected_audience = "gym-system-client"
    if audience != expected_audience:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no válido para este cliente",
            headers={"WWW-Authenticate": "Bearer"},
        )

def _validate_token_timestamps(payload: dict):
    """Validar timestamps del token"""
    exp = payload.get("exp")
    iat = payload.get("iat")
    
    if exp is None or iat is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    current_time = datetime.now(timezone.utc).timestamp()
    
    # Verificar que el token no sea muy antiguo (más de 24 horas)
    if current_time - iat > 86400:  # 24 horas
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token demasiado antiguo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que el token no sea del futuro (tolerancia de 5 minutos)
    if iat > current_time + 300:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token con timestamp futuro inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def _validate_user_id_format(user_id: str):
    """Validar formato del ID de usuario"""
    try:
        import uuid
        uuid.UUID(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de ID de usuario inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def _decode_jwt_token(token: str) -> dict:
    """Decodificar y validar token JWT"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
                "verify_aud": True,
                "require": ["exp", "iat", "sub", "iss", "aud", "jti"]
            }
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

def _get_user_from_database(user_id: str, db: Session) -> Usuario:
    """Obtener usuario de la base de datos"""
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar si el usuario está activo
    if not user.esta_activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    return user

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Obtiene el usuario actual basado en el token JWT
    
    Args:
        token: Token JWT de autenticación
        db: Sesión de base de datos
        
    Returns:
        Usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    # Decodificar token
    payload = _decode_jwt_token(token)
    
    # Validar payload
    token_data = _validate_jwt_payload(payload)
    
    # Validar issuer y audience
    _validate_token_issuer_audience(payload.get("iss"), payload.get("aud"))
    
    # Validar timestamps
    _validate_token_timestamps(payload)
    
    # Validar formato de user_id
    _validate_user_id_format(token_data.sub)
    
    # Obtener usuario de la base de datos
    return _get_user_from_database(token_data.sub, db)

async def get_current_admin_user(
    current_user: Annotated[Usuario, Depends(get_current_user)]
) -> Usuario:
    """
    Verifica que el usuario actual sea administrador
    
    Args:
        current_user: Usuario autenticado
        
    Returns:
        Usuario administrador
        
    Raises:
        HTTPException: Si el usuario no tiene permisos de administrador
    """
    if not current_user.es_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes"
        )
    return current_user

# Añadido: esquema OAuth2 opcional (no error si falta token)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login/json", auto_error=False)

async def get_current_user_optional(
    token: Annotated[Optional[str], Depends(oauth2_scheme_optional)],
    db: Session = Depends(get_db)
) -> Optional[Usuario]:
    """Devuelve el usuario autenticado si hay token; permite anónimo en entornos no producción.

    Args:
        token: Token JWT opcional.
        db: Sesión de base de datos.

    Returns:
        ``Usuario`` autenticado o ``None`` si no hay token y no estamos en producción.

    Raises:
        HTTPException: Si el token falta o es inválido en producción.
    """
    # Si se proporciona token, reutilizar la lógica existente
    if token:
        # Reutilizamos get_current_user pasando el token explícitamente
        return await get_current_user(token, db)  # type: ignore[arg-type]

    # Si no hay token, permitir acceso solo si no estamos en producción
    if settings.ENV != "production":
        return None

    # En producción, requerir credenciales
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token JWT con claims completos y seguros"""
    to_encode = data.copy()
    
    # Configurar expiración
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Agregar claims estándar de seguridad
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": f"gym-system-{settings.ENV}",  # Issuer
        "aud": "gym-system-client",  # Audience
        "jti": secrets.token_urlsafe(32),  # JWT ID único
        "type": "access"  # Tipo de token
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Contexto de encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña contra su hash
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Contraseña hasheada
        
    Returns:
        True si la contraseña coincide, False en caso contrario
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Genera un hash de contraseña
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Hash de la contraseña
    """
    return pwd_context.hash(password)
