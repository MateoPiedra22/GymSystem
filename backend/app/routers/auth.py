"""
Router para autenticación de usuarios
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
import ipaddress
import asyncio
import logging
import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

# Crear limiter
limiter = Limiter(key_func=get_remote_address)
from sqlalchemy import or_

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.schemas.auth import Token, TokenData, LoginCredentials
from app.schemas.usuarios import UsuarioOut, UsuarioCreate
from app.core.auth import get_current_user, create_access_token, verify_password, get_password_hash
from app.core.database import get_db
from app.core.security import SecurityValidator, SecurityUtils
from app.models.usuarios import Usuario

# Configurar logging
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter()

# Rastreo de intentos de login fallidos usando Redis para thread-safety
import asyncio
import time
from app.core.redis import redis_client

class RedisFailedAttemptsTracker:
    def __init__(self):
        self.redis_client = redis_client.get_client()
    
    async def add_attempt(self, ip: str, username: str):
        """Agrega un intento fallido usando Redis"""
        if not self.redis_client:
            logger.warning("Redis no disponible, usando fallback en memoria")
            return
        
        try:
            # Clave para intentos fallidos por IP
            key = f"failed_attempts:{ip}"
            
            # Incrementar contador y establecer TTL
            await self.redis_client.incr(key)
            await self.redis_client.expire(key, 900)  # 15 minutos
            
        except Exception as e:
            logger.error(f"Error al rastrear intento fallido en Redis: {e}")
    
    async def is_blocked(self, ip: str) -> bool:
        """Verifica si una IP está bloqueada usando Redis"""
        if not self.redis_client:
            return False
        
        try:
            # Verificar bloqueo temporal
            block_key = f"blocked_ip:{ip}"
            if await self.redis_client.exists(block_key):
                return True
            
            # Verificar intentos fallidos recientes
            key = f"failed_attempts:{ip}"
            attempts = await self.redis_client.get(key)
            
            if attempts and int(attempts) >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                # Bloquear IP por 30 minutos
                await self.redis_client.setex(block_key, 1800, "blocked")
                logger.warning(f"IP {ip} bloqueada por demasiados intentos fallidos")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error al verificar bloqueo en Redis: {e}")
            return False
    
    async def clear_attempts(self, ip: str):
        """Limpia intentos para una IP usando Redis"""
        if not self.redis_client:
            return
        
        try:
            # Limpiar intentos fallidos y bloqueo
            await self.redis_client.delete(f"failed_attempts:{ip}")
            await self.redis_client.delete(f"blocked_ip:{ip}")
            
        except Exception as e:
            logger.error(f"Error al limpiar intentos en Redis: {e}")

# Instancia global del tracker
failed_attempts_tracker = RedisFailedAttemptsTracker()

# Función para determinar si el rate limiting está habilitado
def is_rate_limiting_enabled():
    """Determina si el rate limiting está habilitado basado en el entorno"""
    return not settings.TESTING

def rate_limit_decorator(limit_str):
    if not settings.TESTING:
        return limiter.limit(limit_str)
    else:
        def decorator(func):
            return func
        return decorator

if not settings.TESTING:
    @router.post("/login", response_model=Token)
    async def login_for_access_token(
        request: Request,
        response: Response,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Session = Depends(get_db)
    ):
        """
        Inicia sesión y genera un token de acceso JWT
        """
        # Obtener IP del cliente
        client_ip = SecurityUtils.get_client_ip(request)
        
        # Validar entrada
        if not form_data.username or not form_data.password:
            logger.warning(f"Intento de login con credenciales vacías desde IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username y password son requeridos"
            )
        
        # Validar longitud de entrada
        if len(form_data.username) > 50 or len(form_data.password) > 128:
            logger.warning(f"Intento de login con credenciales demasiado largas desde IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credenciales inválidas"
            )
        
        # Validar formato de username
        if not SecurityValidator.validate_username(form_data.username):
            logger.warning(f"Intento de login con username inválido: {form_data.username} desde IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de username inválido"
            )
        
        # Verificar si IP está bloqueada por intentos fallidos
        if await failed_attempts_tracker.is_blocked(client_ip):
            logger.warning(f"Intento de login desde IP bloqueada: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos fallidos. Intente nuevamente más tarde."
            )
        
        # Buscar usuario por username
        user = db.query(Usuario).filter(Usuario.username == form_data.username).first()
        
        # Verificar si el usuario existe y la contraseña es correcta
        if not user or not verify_password(form_data.password, user.hashed_password):
            await _track_failed_attempt(client_ip, form_data.username)
            logger.warning(f"Intento de login fallido para usuario: {form_data.username} desde IP: {client_ip}")
            # Mensaje genérico para evitar enumeración de usuarios
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar si el usuario está activo
        if not user.esta_activo:
            logger.warning(f"Intento de login de usuario inactivo: {form_data.username} desde IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar si la cuenta está bloqueada (opcional)
        if hasattr(user, 'bloqueado_hasta') and user.bloqueado_hasta and user.bloqueado_hasta > datetime.utcnow():
            logger.warning(f"Intento de login de usuario bloqueado: {form_data.username} desde IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cuenta temporalmente bloqueada",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Limpiar intentos fallidos para esta IP
        await _clear_failed_attempts(client_ip)
        
        # Crear datos para el token JWT
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires = datetime.now(timezone.utc) + expires_delta
        
        to_encode = {
            "sub": user.id,
            "username": user.username,
            "admin": user.es_admin,
            "iat": datetime.now(timezone.utc),
            "ip": client_ip  # Incluir IP en el token para validación adicional
        }
        
        # Generar el token JWT
        encoded_jwt = create_access_token(data=to_encode, expires_delta=expires_delta)
        
        # Configurar cookie segura
        cookie_secure = settings.ENV == "production"
        cookie_samesite = "strict" if settings.ENV == "production" else "lax"
        
        # Establecer cookie segura con el token
        response.set_cookie(
            key="access_token",
            value=encoded_jwt,
            httponly=True,  # Previene acceso desde JavaScript
            samesite=cookie_samesite,  # Protección CSRF
            secure=cookie_secure,  # Solo HTTPS en producción
            max_age=int(expires_delta.total_seconds()),
            expires=expires,
            path="/",  # Aplicar a todo el sitio
            domain=None  # Solo el dominio actual
        )
        
        # Actualizar último acceso
        user.ultimo_acceso = datetime.now(timezone.utc)
        db.commit()
        
        # Log de login exitoso
        logger.info(f"Login exitoso para usuario: {user.username} desde IP: {client_ip}")
        
        return {
            "access_token": encoded_jwt,
            "token_type": "bearer",
            "expires_at": expires,
            "user_id": user.id,
            "username": user.username,
            "es_admin": user.es_admin
        }

    @router.post("/login/json", response_model=Token)
    async def login_with_json(
        request: Request,
        response: Response,
        credentials: LoginCredentials,
        db: Session = Depends(get_db)
    ):
        """
        Endpoint alternativo para login con JSON en lugar de form-data
        """
        # Validar entrada JSON
        if not credentials.username or not credentials.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username y password son requeridos"
            )
        
        # Reusamos la lógica del endpoint anterior
        form_data = OAuth2PasswordRequestForm(
            username=credentials.username,
            password=credentials.password,
            scope=""
        )
        return await login_for_access_token(request, response, form_data, db)
else:
    @router.post("/login", response_model=Token)
    async def login_for_access_token(
        request: Request,
        response: Response,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Session = Depends(get_db)
    ):
        """
        Inicia sesión y genera un token de acceso JWT
        """
        # Obtener IP del cliente
        client_ip = SecurityUtils.get_client_ip(request)
        
        # Validar entrada
        if not form_data.username or not form_data.password:
            logger.warning(f"Intento de login con credenciales vacías desde IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username y password son requeridos"
            )
        
        # Validar longitud de entrada
        if len(form_data.username) > 50 or len(form_data.password) > 128:
            logger.warning(f"Intento de login con credenciales demasiado largas desde IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credenciales inválidas"
            )
        
        # Validar formato de username
        if not SecurityValidator.validate_username(form_data.username):
            logger.warning(f"Intento de login con username inválido: {form_data.username} desde IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de username inválido"
            )
        
        # Verificar si IP está bloqueada por intentos fallidos
        if failed_attempts_tracker.is_blocked(client_ip):
            logger.warning(f"Intento de login desde IP bloqueada: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos fallidos. Intente nuevamente más tarde."
            )
        
        # Buscar usuario por username
        user = db.query(Usuario).filter(Usuario.username == form_data.username).first()
        
        # Verificar si el usuario existe y la contraseña es correcta
        if not user or not verify_password(form_data.password, user.hashed_password):
            await _track_failed_attempt(client_ip, form_data.username)
            logger.warning(f"Intento de login fallido para usuario: {form_data.username} desde IP: {client_ip}")
            # Mensaje genérico para evitar enumeración de usuarios
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar si el usuario está activo
        if not user.esta_activo:
            logger.warning(f"Intento de login de usuario inactivo: {form_data.username} desde IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar si la cuenta está bloqueada (opcional)
        if hasattr(user, 'bloqueado_hasta') and user.bloqueado_hasta and user.bloqueado_hasta > datetime.utcnow():
            logger.warning(f"Intento de login de usuario bloqueado: {form_data.username} desde IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cuenta temporalmente bloqueada",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Limpiar intentos fallidos para esta IP
        await _clear_failed_attempts(client_ip)
        
        # Crear datos para el token JWT
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires = datetime.now(timezone.utc) + expires_delta
        
        to_encode = {
            "sub": user.id,
            "username": user.username,
            "admin": user.es_admin,
            "iat": datetime.now(timezone.utc),
            "ip": client_ip  # Incluir IP en el token para validación adicional
        }
        
        # Generar el token JWT
        encoded_jwt = create_access_token(data=to_encode, expires_delta=expires_delta)
        
        # Configurar cookie segura
        cookie_secure = settings.ENV == "production"
        cookie_samesite = "strict" if settings.ENV == "production" else "lax"
        
        # Establecer cookie segura con el token
        response.set_cookie(
            key="access_token",
            value=encoded_jwt,
            httponly=True,  # Previene acceso desde JavaScript
            samesite=cookie_samesite,  # Protección CSRF
            secure=cookie_secure,  # Solo HTTPS en producción
            max_age=int(expires_delta.total_seconds()),
            expires=expires,
            path="/",  # Aplicar a todo el sitio
            domain=None  # Solo el dominio actual
        )
        
        # Actualizar último acceso
        user.ultimo_acceso = datetime.now(timezone.utc)
        db.commit()
        
        # Log de login exitoso
        logger.info(f"Login exitoso para usuario: {user.username} desde IP: {client_ip}")
        
        return {
            "access_token": encoded_jwt,
            "token_type": "bearer",
            "expires_at": expires,
            "user_id": user.id,
            "username": user.username,
            "es_admin": user.es_admin
        }

    @router.post("/login/json", response_model=Token)
    async def login_with_json(
        request: Request,
        response: Response,
        credentials: LoginCredentials,
        db: Session = Depends(get_db)
    ):
        """
        Endpoint alternativo para login con JSON en lugar de form-data
        """
        # Validar entrada JSON
        if not credentials.username or not credentials.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username y password son requeridos"
            )
        
        # Reusamos la lógica del endpoint anterior
        form_data = OAuth2PasswordRequestForm(
            username=credentials.username,
            password=credentials.password,
            scope=""
        )
        return await login_for_access_token(request, response, form_data, db)

@router.post("/register", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: Request,
    user_data: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario
    """
    client_ip = SecurityUtils.get_client_ip(request)
    
    # Verificar si el username o email ya existe
    existing_user = db.query(Usuario).filter(
        or_(
            Usuario.username == user_data.username,
            Usuario.email == user_data.email
        )
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario o email ya está en uso"
        )
    
    # Generar hash de la contraseña
    hashed_password = get_password_hash(user_data.password)
    
    # Crear objeto de usuario
    new_user = Usuario(
        username=user_data.username,
        email=user_data.email,
        nombre=user_data.nombre,
        apellido=user_data.apellido,
        fecha_nacimiento=user_data.fecha_nacimiento,
        telefono=user_data.telefono,
        direccion=user_data.direccion,
        objetivo=user_data.objetivo,
        notas=user_data.notas,
        peso_inicial=user_data.peso_inicial,
        altura=user_data.altura,
        hashed_password=hashed_password,
        es_admin=user_data.es_admin
    )
    
    # Guardar en la base de datos
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log de registro exitoso
    logger.info(f"Usuario registrado exitosamente: {new_user.username} desde IP: {client_ip}")
    
    return new_user

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: Annotated[Optional[Usuario], Depends(get_current_user)] = None
):
    """
    Cierra sesión eliminando la cookie de autenticación
    """
    client_ip = SecurityUtils.get_client_ip(request)
    
    # Eliminar cookie de autenticación
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="strict" if settings.ENV == "production" else "lax",
        secure=settings.ENV == "production"
    )
    
    # Log de logout
    username = current_user.username if current_user else "unknown"
    logger.info(f"Logout exitoso para usuario: {username} desde IP: {client_ip}")
    
    return {"message": "Sesión cerrada exitosamente"}

@router.get("/me", response_model=UsuarioOut)
async def read_users_me(
    request: Request,
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """
    Devuelve la información del usuario autenticado
    """
    client_ip = SecurityUtils.get_client_ip(request)
    logger.info(f"Usuario {current_user.username} accedió a /me desde IP: {client_ip}")
    return current_user

@router.get("/debug-token")
async def debug_token(token: str = Query(..., description="Token JWT para debug")):
    """
    Endpoint de debug para verificar tokens JWT
    """
    try:
        # Decodificar el token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return {
            "success": True,
            "payload": payload,
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "admin": payload.get("admin")
        }
    except jwt.PyJWTError as e:
        return {
            "success": False,
            "error": str(e)
        }

# Funciones auxiliares para manejo de intentos fallidos
async def _track_failed_attempt(ip: str, username: str):
    """Rastrea intentos fallidos por IP"""
    await failed_attempts_tracker.add_attempt(ip, username)

async def _is_ip_blocked(ip: str) -> bool:
    """Verifica si una IP está bloqueada por intentos fallidos"""
    return await failed_attempts_tracker.is_blocked(ip)

async def _clear_failed_attempts(ip: str):
    """Limpia intentos fallidos para una IP tras login exitoso"""
    await failed_attempts_tracker.clear_attempts(ip)
