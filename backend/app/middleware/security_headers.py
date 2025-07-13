"""
Middleware especializado para headers de seguridad
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.security import SecurityConfig

# Configurar logging
logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware especializado para añadir headers de seguridad
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Procesa cada petición añadiendo headers de seguridad"""
        response = await call_next(request)
        
        # Añadir headers de seguridad
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response: Response):
        """Añade headers de seguridad a la respuesta"""
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        
        # Headers adicionales específicos por ambiente
        if settings.ENV == "production":
            response.headers["Server"] = "GymSystem"  # Ocultar información del servidor
        else:
            response.headers["X-Environment"] = "development" 