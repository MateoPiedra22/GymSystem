"""
Middleware para control de tasa de peticiones (rate limiting)
"""
import time
from typing import Dict, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware para limitar la tasa de peticiones por IP
    
    Atributos:
        rate_limit: Número máximo de peticiones permitidas por minuto
        ip_cache: Diccionario para almacenar información de peticiones por IP
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit = settings.RATE_LIMIT_PER_MINUTE
        self.ip_cache: Dict[str, Tuple[int, float]] = {}  # {ip: (count, timestamp)}
    
    async def dispatch(self, request: Request, call_next):
        """
        Procesa cada petición y aplica los límites de tasa
        """
        if settings.TESTING:
            return await call_next(request)
        # Obtener la IP real del cliente (considerando posibles proxies)
        client_ip = self._get_client_ip(request)
        # Ignorar límites para rutas específicas
        if self._should_ignore_path(request.url.path):
            return await call_next(request)
        # Comprobar si la IP ha excedido el límite
        if self._is_rate_limited(client_ip):
            # Devolver respuesta de error 429 (Too Many Requests)
            return Response(
                content="Demasiadas peticiones. Inténtalo de nuevo más tarde.",
                status_code=429,
                media_type="text/plain"
            )
        # Procesar la petición normalmente
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtiene la IP real del cliente, considerando proxies"""
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # Tomar la primera IP de la cadena (cliente original)
            return x_forwarded_for.split(",")[0].strip()
        
        # Si no hay proxy, usar la IP directa
        return request.client.host if request.client else "unknown"
    
    def _should_ignore_path(self, path: str) -> bool:
        """Determina si una ruta debe ignorar los límites de tasa"""
        # Ignorar rutas de documentación y estáticas
        ignore_paths = [
            "/docs", 
            "/redoc", 
            "/openapi.json",
            "/static",
            "/health"
        ]
        
        return any(path.startswith(ignore) for ignore in ignore_paths)
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """
        Comprueba si una IP ha excedido el límite de peticiones
        
        Args:
            client_ip: IP del cliente
            
        Returns:
            True si ha excedido el límite, False en caso contrario
        """
        current_time = time.time()
        
        # Limpiar entradas antiguas (más de 1 minuto)
        self._clean_old_entries(current_time)
        
        # Obtener contador actual o inicializar en 0
        count, timestamp = self.ip_cache.get(client_ip, (0, current_time))
        
        # Reiniciar contador si ha pasado más de un minuto
        if current_time - timestamp > 60:
            count = 0
            timestamp = current_time
        
        # Incrementar contador
        count += 1
        self.ip_cache[client_ip] = (count, timestamp)
        
        # Verificar si excede el límite
        return count > self.rate_limit
    
    def _clean_old_entries(self, current_time: float):
        """Limpia entradas antiguas del caché de IPs"""
        # Eliminar entradas que tienen más de 1 minuto de antigüedad
        self.ip_cache = {
            ip: (count, timestamp) 
            for ip, (count, timestamp) in self.ip_cache.items() 
            if current_time - timestamp < 60
        }
