import time
import logging
from typing import Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        """
        Inicializar el rate limiter
        
        Args:
            requests_per_minute: Máximo de requests por minuto
            requests_per_hour: Máximo de requests por hora
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Almacenar requests por IP
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()
        
        # Limpiar requests antiguos cada 5 minutos
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutos

    def is_allowed(self, ip: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verificar si una request está permitida
        
        Returns:
            Tuple[bool, Dict]: (permitido, información del rate limit)
        """
        current_time = time.time()
        
        with self.lock:
            # Limpiar requests antiguos periódicamente
            if current_time - self.last_cleanup > self.cleanup_interval:
                self._cleanup_old_requests(current_time)
                self.last_cleanup = current_time
            
            # Obtener requests recientes para esta IP
            requests = self.requests[ip]
            
            # Filtrar requests del último minuto
            minute_ago = current_time - 60
            requests_last_minute = [req for req in requests if req > minute_ago]
            
            # Filtrar requests de la última hora
            hour_ago = current_time - 3600
            requests_last_hour = [req for req in requests if req > hour_ago]
            
            # Verificar límites
            minute_limit_exceeded = len(requests_last_minute) >= self.requests_per_minute
            hour_limit_exceeded = len(requests_last_hour) >= self.requests_per_hour
            
            is_allowed = not (minute_limit_exceeded or hour_limit_exceeded)
            
            if is_allowed:
                # Agregar request actual
                requests.append(current_time)
            
            # Calcular información del rate limit
            rate_limit_info = {
                "allowed": is_allowed,
                "requests_last_minute": len(requests_last_minute),
                "requests_last_hour": len(requests_last_hour),
                "limit_per_minute": self.requests_per_minute,
                "limit_per_hour": self.requests_per_hour,
                "reset_time_minute": minute_ago + 60,
                "reset_time_hour": hour_ago + 3600
            }
            
            return is_allowed, rate_limit_info

    def _cleanup_old_requests(self, current_time: float):
        """Limpiar requests más antiguos que 1 hora"""
        cutoff_time = current_time - 3600
        
        for ip in list(self.requests.keys()):
            self.requests[ip] = [req for req in self.requests[ip] if req > cutoff_time]
            
            # Eliminar IPs sin requests
            if not self.requests[ip]:
                del self.requests[ip]

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del rate limiter"""
        with self.lock:
            current_time = time.time()
            total_ips = len(self.requests)
            total_requests = sum(len(requests) for requests in self.requests.values())
            
            # IPs más activas
            active_ips = []
            for ip, requests in self.requests.items():
                recent_requests = [req for req in requests if req > current_time - 300]  # Últimos 5 minutos
                if recent_requests:
                    active_ips.append({
                        "ip": ip,
                        "requests_last_5min": len(recent_requests)
                    })
            
            active_ips.sort(key=lambda x: x["requests_last_5min"], reverse=True)
            
            return {
                "total_ips": total_ips,
                "total_requests": total_requests,
                "active_ips": active_ips[:10],  # Top 10 IPs más activas
                "limits": {
                    "requests_per_minute": self.requests_per_minute,
                    "requests_per_hour": self.requests_per_hour
                }
            }

class AdvancedRateLimiter:
    """Rate limiter avanzado con diferentes reglas por endpoint"""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self.endpoint_rules: Dict[str, Dict[str, int]] = {
            # Reglas por defecto
            "default": {"requests_per_minute": 60, "requests_per_hour": 1000},
            
            # Reglas específicas por endpoint
            "auth": {"requests_per_minute": 5, "requests_per_hour": 50},  # Login más restrictivo
            "upload": {"requests_per_minute": 10, "requests_per_hour": 100},  # Uploads limitados
            "reports": {"requests_per_minute": 30, "requests_per_hour": 500},  # Reportes moderados
            "api": {"requests_per_minute": 120, "requests_per_hour": 2000},  # API general más permisiva
        }

    def get_limiter(self, endpoint: str) -> RateLimiter:
        """Obtener o crear rate limiter para un endpoint"""
        if endpoint not in self.limiters:
            rules = self.endpoint_rules.get(endpoint, self.endpoint_rules["default"])
            self.limiters[endpoint] = RateLimiter(
                requests_per_minute=rules["requests_per_minute"],
                requests_per_hour=rules["requests_per_hour"]
            )
        return self.limiters[endpoint]

    def is_allowed(self, ip: str, endpoint: str = "default") -> Tuple[bool, Dict[str, Any]]:
        """Verificar si una request está permitida para un endpoint específico"""
        limiter = self.get_limiter(endpoint)
        return limiter.is_allowed(ip)

    def get_all_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de todos los limiters"""
        stats = {}
        for endpoint, limiter in self.limiters.items():
            stats[endpoint] = limiter.get_stats()
        return stats

# Instancias globales
rate_limiter = RateLimiter()
advanced_rate_limiter = AdvancedRateLimiter()

def rate_limit_middleware(endpoint: str = "default"):
    """
    Middleware para aplicar rate limiting
    
    Args:
        endpoint: Nombre del endpoint para aplicar reglas específicas
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            # Obtener IP del cliente
            client_ip = request.client.host if hasattr(request, 'client') else "unknown"
            
            # Verificar rate limit
            is_allowed, rate_info = advanced_rate_limiter.is_allowed(client_ip, endpoint)
            
            if not is_allowed:
                logger.warning(f"Rate limit excedido para IP {client_ip} en endpoint {endpoint}")
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": "Demasiadas requests. Intenta de nuevo más tarde.",
                        "rate_limit_info": rate_info
                    }
                )
            
            # Agregar headers de rate limit
            response = func(request, *args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit-Minute"] = str(rate_info["limit_per_minute"])
                response.headers["X-RateLimit-Limit-Hour"] = str(rate_info["limit_per_hour"])
                response.headers["X-RateLimit-Remaining-Minute"] = str(
                    rate_info["limit_per_minute"] - rate_info["requests_last_minute"]
                )
                response.headers["X-RateLimit-Remaining-Hour"] = str(
                    rate_info["limit_per_hour"] - rate_info["requests_last_hour"]
                )
                response.headers["X-RateLimit-Reset-Minute"] = str(int(rate_info["reset_time_minute"]))
                response.headers["X-RateLimit-Reset-Hour"] = str(int(rate_info["reset_time_hour"]))
            
            return response
        return wrapper
    return decorator

# Funciones de utilidad
def get_client_ip(request) -> str:
    """Obtener IP del cliente de forma segura"""
    # Intentar obtener IP real detrás de proxy
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # IP directa
    if hasattr(request, 'client') and request.client:
        return request.client.host
    
    return "unknown"

def is_whitelisted_ip(ip: str) -> bool:
    """Verificar si una IP está en la whitelist"""
    whitelist = [
        "127.0.0.1",  # localhost
        "::1",        # localhost IPv6
        "10.0.0.0/8", # Red privada
        "172.16.0.0/12", # Red privada
        "192.168.0.0/16", # Red privada
    ]
    
    # Verificación simple (en producción usar ipaddress module)
    for whitelisted in whitelist:
        if ip == whitelisted or ip.startswith(whitelisted.split("/")[0]):
            return True
    
    return False 