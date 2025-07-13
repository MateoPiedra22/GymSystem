"""
Middleware especializado para bloqueo de IPs
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.redis import redis_client

# Configurar logging
logger = logging.getLogger(__name__)

class IPBlockingMiddleware(BaseHTTPMiddleware):
    """
    Middleware especializado para verificar y bloquear IPs
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Procesa cada petición verificando si la IP está bloqueada"""
        # Obtener IP del cliente
        client_ip = self._get_client_ip(request)
        
        # Verificar si la IP está bloqueada (usando Redis)
        if await self._is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP attempt: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtiene la IP real del cliente"""
        # Verificar headers de proxy
        for header in ['x-forwarded-for', 'x-real-ip', 'x-client-ip']:
            if header in request.headers:
                return request.headers[header].split(',')[0].strip()
        
        # IP directa
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _is_ip_blocked(self, ip: str) -> bool:
        """Verifica si una IP está bloqueada en Redis."""
        redis_conn = redis_client.get_client()
        if not redis_conn:
            return False # No bloquear si Redis falla
        try:
            return await redis_conn.exists(f"blocked_ip:{ip}")
        except Exception as e:
            logger.error(f"Error al verificar IP bloqueada {ip} en Redis: {e}")
            return False 