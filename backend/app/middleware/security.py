"""
Middleware de seguridad mejorado para producción
REFACTORIZADO: Dividido en middlewares especializados para mejor organización
"""

import time
import json
import logging
from typing import Dict, Set, Optional, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.redis import redis_client
from app.core.security import SecurityConfig, SecurityUtils, SecurityValidator

# Configurar logging
logger = logging.getLogger(__name__)

# Importar middlewares especializados
try:
    from .attack_detection import AttackDetectionMiddleware
    from .security_headers import SecurityHeadersMiddleware
    from .ip_blocking import IPBlockingMiddleware
    MIDDLEWARES_AVAILABLE = True
except ImportError:
    MIDDLEWARES_AVAILABLE = False
    logger.warning("Middlewares especializados no disponibles")

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware de seguridad principal que coordina los middlewares especializados
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Rutas sensibles que requieren monitoring extra
        self.sensitive_paths = {
            '/api/auth/login', '/api/auth/register', '/api/usuarios',
            '/api/configuracion', '/api/empleados', '/api/multimedia/upload'
        }
    
    async def dispatch(self, request: Request, call_next):
        """Procesa cada petición aplicando validaciones de seguridad"""
        start_time = time.time()
        
        # Obtener IP del cliente
        client_ip = SecurityUtils.get_client_ip(request)
        
        # Validar origen en producción
        if settings.ENV == "production":
            origin = request.headers.get("origin")
            if origin and origin not in settings.ALLOWED_ORIGINS:
                logger.warning(f"Invalid origin: {origin} from IP: {client_ip}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid origin"}
                )
        
        # Validar tamaño de petición
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                max_size = 50 * 1024 * 1024  # 50MB max
                if size > max_size:
                    logger.warning(f"Request too large: {size} bytes from IP: {client_ip}")
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request too large"}
                    )
            except ValueError:
                pass
        
        # Procesar petición
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)} from IP: {client_ip}")
            # Log del stack trace completo para debugging
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        
        # Log de actividad en rutas sensibles
        if any(request.url.path.startswith(path) for path in self.sensitive_paths):
            processing_time = time.time() - start_time
            logger.info(
                f"Sensitive endpoint access: {request.method} {request.url.path} "
                f"IP: {client_ip} Status: {response.status_code} "
                f"Time: {processing_time:.3f}s"
            )
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware específico para validación de entrada
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Rutas que requieren validación especial
        self.validation_routes = {
            '/api/auth/login',
            '/api/auth/register', 
            '/api/usuarios',
            '/api/multimedia/upload'
        }
    
    async def dispatch(self, request: Request, call_next):
        """Valida entrada en rutas específicas"""
        
        # Solo validar en rutas específicas y métodos que envían datos
        if (request.method in ["POST", "PUT", "PATCH"] and 
            any(request.url.path.startswith(route) for route in self.validation_routes)):
            
            # Validar parámetros de query
            for param, value in request.query_params.items():
                if self._is_invalid_input(value):
                    logger.warning(f"Invalid query parameter {param}: {value}")
                    return JSONResponse(
                        status_code=400,
                        content={"detail": f"Invalid parameter: {param}"}
                    )
            
            # Para peticiones con body JSON
            if request.headers.get("content-type", "").startswith("application/json"):
                try:
                    body = await request.body()
                    if body:
                        # Validar tamaño del body
                        if len(body) > settings.MAX_REQUEST_SIZE:
                            return JSONResponse(
                                status_code=413,
                                content={"detail": "Request body too large"}
                            )
                        
                        # Intentar parsear JSON
                        json_data = json.loads(body.decode('utf-8'))
                        if self._validate_json_data(json_data):
                            return JSONResponse(
                                status_code=400,
                                content={"detail": "Invalid data format"}
                            )
                        
                        # Recrear request con body validado
                        async def receive():
                            return {
                                "type": "http.request",
                                "body": body,
                                "more_body": False
                            }
                        
                        request._receive = receive
                        
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"Invalid JSON format: {str(e)}")
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid JSON format"}
                    )
                except Exception as e:
                    logger.error(f"Error processing JSON body: {str(e)}")
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Error processing request"}
                    )
        
        return await call_next(request)
    
    def _is_invalid_input(self, value: str) -> bool:
        """Verifica si una entrada es inválida"""
        if not value:
            return False
        
        # Verificar longitud excesiva
        if len(value) > 10000:
            return True
        
        # Verificar patrones de ataque
        dangerous_patterns = [
            '<script', 'javascript:', 'data:text/html',
            'union select', 'drop table', '../../',
            'eval(', 'exec(', 'system(',
            '\x00', '\r\n\r\n'  # Null bytes y CRLF injection
        ]
        
        value_lower = value.lower()
        for pattern in dangerous_patterns:
            if pattern in value_lower:
                return True
        
        return False
    
    def _validate_json_data(self, data: any, depth: int = 0) -> bool:
        """Valida recursivamente datos JSON"""
        if depth > 10:  # Prevenir recursión infinita
            return True
        
        if isinstance(data, dict):
            for key, value in data.items():
                if self._is_invalid_input(str(key)) or self._validate_json_data(value, depth + 1):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._validate_json_data(item, depth + 1):
                    return True
        elif isinstance(data, str):
            return self._is_invalid_input(data)
        
        return False


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Middleware mejorado de rate limiting con diferentes límites por endpoint, usando Redis.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Límites específicos por endpoint
        self.endpoint_limits = {
            '/api/auth/login': 5,
            '/api/auth/register': 3,
            '/api/multimedia/upload': 10,
            'default': settings.RATE_LIMIT_PER_MINUTE
        }
    
    async def dispatch(self, request: Request, call_next):
        """Aplica rate limiting específico por endpoint usando Redis."""
        redis_conn = redis_client.get_client()
        if not redis_conn:
            # Si Redis no está disponible, se salta el rate limiting para no bloquear la app
            logger.warning("Redis no disponible, saltando el rate limiting.")
            return await call_next(request)

        client_ip = SecurityUtils.get_client_ip(request)
        endpoint = self._get_endpoint_key(request.url.path)
        
        limit = self.endpoint_limits.get(endpoint, self.endpoint_limits['default'])
        
        is_limited = await self._is_rate_limited(redis_conn, client_ip, endpoint, limit)
        if is_limited:
            logger.warning(f"Rate limit exceeded for IP {client_ip} on endpoint {endpoint}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        return await call_next(request)
    
    def _get_endpoint_key(self, path: str) -> str:
        """Obtiene la clave del endpoint para rate limiting"""
        for endpoint in self.endpoint_limits:
            if endpoint != 'default' and path.startswith(endpoint):
                return endpoint
        return 'default'
    
    async def _is_rate_limited(self, redis_conn, ip: str, endpoint: str, limit: int) -> bool:
        """Verifica si una IP ha excedido el límite para un endpoint usando Redis."""
        try:
            key = f"rate_limit:{ip}:{endpoint}"
            
            # Usar una transacción de pipeline para operaciones atómicas
            pipe = redis_conn.pipeline()
            pipe.incr(key)
            pipe.expire(key, 60) # TTL de 60 segundos
            current_count, _ = await pipe.execute()
            
            return int(current_count) > limit
        except Exception as e:
            logger.error(f"Error en el rate limiting con Redis: {e}")
            # En caso de error de Redis, no limitar para mantener la disponibilidad
            return False 