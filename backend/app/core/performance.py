"""
Módulo de Performance y Optimización - Sistema de Gimnasio v6
Implementa optimizaciones de rendimiento, caché y monitoreo
"""

import time
import json
import hashlib
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, Union
from functools import wraps
from datetime import datetime, timedelta
from collections import OrderedDict
from contextlib import asynccontextmanager
from pydantic import BaseModel
import redis.asyncio as redis
from fastapi import Request, Response

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN DE PERFORMANCE
# ============================================================================

class PerformanceConfig(BaseModel):
    """Configuración de performance del sistema"""
    
    # Cache Configuration
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 300  # 5 minutos
    CACHE_MAX_SIZE: int = 1000
    CACHE_PREFIX: str = "gym_cache:"
    
    # Query Optimization
    QUERY_TIMEOUT: int = 30  # segundos
    MAX_QUERY_RESULTS: int = 1000
    SLOW_QUERY_THRESHOLD: float = 1.0  # segundos
    
    # Response Optimization
    ENABLE_ETAGS: bool = True
    ENABLE_COMPRESSION: bool = True
    ENABLE_PAGINATION: bool = True
    
    # Monitoring
    METRICS_RETENTION: int = 1000
    ALERT_THRESHOLD: float = 5.0  # segundos
    CRITICAL_THRESHOLD: float = 10.0  # segundos

# ============================================================================
# SISTEMA DE CACHÉ AVANZADO
# ============================================================================

class AdvancedCache:
    """Sistema de caché avanzado con Redis y caché local"""
    
    def __init__(self, redis_client: redis.Redis, config: PerformanceConfig):
        self.redis = redis_client
        self.config = config
        self.local_cache = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "local_hits": 0,
            "sets": 0,
            "deletes": 0
        }
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Obtener valor del caché"""
        full_key = f"{self.config.CACHE_PREFIX}{key}"
        
        # Verificar caché local primero
        if key in self.local_cache:
            self.stats["local_hits"] += 1
            return self.local_cache[key]
        
        try:
            # Obtener de Redis
            value = await self.redis.get(full_key)
            if value:
                data = json.loads(value)
                # Agregar al caché local
                self._add_to_local_cache(key, data)
                self.stats["hits"] += 1
                return data
            else:
                self.stats["misses"] += 1
                return default
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            self.stats["misses"] += 1
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Establecer valor en caché"""
        full_key = f"{self.config.CACHE_PREFIX}{key}"
        ttl = ttl or self.config.CACHE_TTL
        
        try:
            # Guardar en Redis
            await self.redis.setex(full_key, ttl, json.dumps(value))
            # Agregar al caché local
            self._add_to_local_cache(key, value)
            self.stats["sets"] += 1
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Eliminar valor del caché"""
        full_key = f"{self.config.CACHE_PREFIX}{key}"
        
        try:
            # Eliminar de Redis
            await self.redis.delete(full_key)
            # Eliminar del caché local
            self.local_cache.pop(key, None)
            self.stats["deletes"] += 1
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidar caché por patrón"""
        try:
            full_pattern = f"{self.config.CACHE_PREFIX}{pattern}"
            keys = await self.redis.keys(full_pattern)
            if keys:
                await self.redis.delete(*keys)
                # Limpiar caché local
                self.local_cache.clear()
            return len(keys)
        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            return 0
    
    def _add_to_local_cache(self, key: str, value: Any):
        """Agregar al caché local con LRU"""
        if key in self.local_cache:
            self.local_cache.move_to_end(key)
        else:
            self.local_cache[key] = value
            if len(self.local_cache) > self.config.CACHE_MAX_SIZE:
                self.local_cache.popitem(last=False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del caché"""
        return {
            **self.stats,
            "local_cache_size": len(self.local_cache),
            "local_cache_keys": list(self.local_cache.keys())
        }

# ============================================================================
# OPTIMIZADOR DE CONSULTAS
# ============================================================================

class QueryOptimizer:
    """Optimizador de consultas de base de datos"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.slow_queries = []
        self.query_stats = {}
    
    def optimize_query(self, query_func: Callable, *args, **kwargs) -> Any:
        """Optimizar y ejecutar consulta"""
        start_time = time.time()
        
        try:
            # Ejecutar consulta con timeout
            result = asyncio.wait_for(
                query_func(*args, **kwargs),
                timeout=self.config.QUERY_TIMEOUT
            )
            
            execution_time = time.time() - start_time
            
            # Registrar estadísticas
            self._record_query_stats(query_func.__name__, execution_time, True)
            
            # Detectar consultas lentas
            if execution_time > self.config.SLOW_QUERY_THRESHOLD:
                self._record_slow_query(query_func.__name__, execution_time, args, kwargs)
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            self._record_query_stats(query_func.__name__, execution_time, False)
            logger.error(f"Query timeout: {query_func.__name__}")
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_query_stats(query_func.__name__, execution_time, False)
            logger.error(f"Query error: {query_func.__name__} - {e}")
            raise
    
    def _record_query_stats(self, query_name: str, execution_time: float, success: bool):
        """Registrar estadísticas de consulta"""
        if query_name not in self.query_stats:
            self.query_stats[query_name] = {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "errors": 0
            }
        
        stats = self.query_stats[query_name]
        stats["count"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["count"]
        
        if not success:
            stats["errors"] += 1
    
    def _record_slow_query(self, query_name: str, execution_time: float, args: tuple, kwargs: dict):
        """Registrar consulta lenta"""
        self.slow_queries.append({
            "query_name": query_name,
            "execution_time": execution_time,
            "args": str(args),
            "kwargs": str(kwargs),
            "timestamp": datetime.now().isoformat()
        })
        
        # Mantener solo las últimas 100 consultas lentas
        if len(self.slow_queries) > 100:
            self.slow_queries.pop(0)
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Obtener consultas lentas"""
        return self.slow_queries.copy()
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de consultas"""
        return self.query_stats.copy()

# ============================================================================
# OPTIMIZADOR DE RESPUESTAS
# ============================================================================

class ResponseOptimizer:
    """Optimizador de respuestas HTTP"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
    
    def generate_etag(self, data: Any) -> str:
        """Generar ETag para datos"""
        if isinstance(data, (dict, list)):
            content = json.dumps(data, sort_keys=True)
        else:
            content = str(data)
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_cache_headers(self, response: Response, data: Any, ttl: int = 300):
        """Agregar headers de caché a la respuesta"""
        if self.config.ENABLE_ETAGS:
            etag = self.generate_etag(data)
            response.headers["ETag"] = f'"{etag}"'
        
        response.headers["Cache-Control"] = f"public, max-age={ttl}"
        response.headers["Expires"] = (datetime.now() + timedelta(seconds=ttl)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    def check_etag(self, request: Request, data: Any) -> bool:
        """Verificar si el ETag coincide"""
        if not self.config.ENABLE_ETAGS:
            return False
        
        etag = self.generate_etag(data)
        if_none_match = request.headers.get("if-none-match")
        
        return bool(if_none_match and if_none_match.strip('"') == etag)
    
    def paginate_response(self, data: List[Any], page: int = 1, size: int = 50) -> Dict[str, Any]:
        """Paginación de respuestas"""
        if not self.config.ENABLE_PAGINATION:
            return {"data": data}
        
        start = (page - 1) * size
        end = start + size
        
        return {
            "data": data[start:end],
            "pagination": {
                "page": page,
                "size": size,
                "total": len(data),
                "pages": (len(data) + size - 1) // size
            }
        }

# ============================================================================
# MONITOR DE PERFORMANCE
# ============================================================================

class PerformanceMonitor:
    """Monitor de performance del sistema"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.metrics = []
        self.alerts = []
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Registrar métrica"""
        metric = {
            "name": name,
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "tags": tags or {}
        }
        
        self.metrics.append(metric)
        
        # Mantener límite de métricas
        if len(self.metrics) > self.config.METRICS_RETENTION:
            self.metrics.pop(0)
        
        # Verificar alertas
        self._check_alerts(name, value)
    
    def measure_time(self, operation_name: str):
        """Decorador para medir tiempo de operaciones"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.record_metric(f"{operation_name}_time", execution_time)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.record_metric(f"{operation_name}_error_time", execution_time, {"error": str(e)})
                    raise
            return wrapper
        return decorator
    
    def measure_async_time(self, operation_name: str):
        """Decorador para medir tiempo de operaciones asíncronas"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.record_metric(f"{operation_name}_time", execution_time)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.record_metric(f"{operation_name}_error_time", execution_time, {"error": str(e)})
                    raise
            return wrapper
        return decorator
    
    def _check_alerts(self, name: str, value: float):
        """Verificar alertas de performance"""
        if value > self.config.CRITICAL_THRESHOLD:
            self.alerts.append({
                "level": "critical",
                "name": name,
                "value": value,
                "threshold": self.config.CRITICAL_THRESHOLD,
                "timestamp": datetime.now().isoformat()
            })
        elif value > self.config.ALERT_THRESHOLD:
            self.alerts.append({
                "level": "warning",
                "name": name,
                "value": value,
                "threshold": self.config.ALERT_THRESHOLD,
                "timestamp": datetime.now().isoformat()
            })
    
    def get_metrics(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener métricas"""
        if name:
            return [m for m in self.metrics if m["name"] == name]
        return self.metrics.copy()
    
    def get_alerts(self, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener alertas"""
        if level:
            return [a for a in self.alerts if a["level"] == level]
        return self.alerts.copy()

# ============================================================================
# MIDDLEWARE DE PERFORMANCE
# ============================================================================

class PerformanceMiddleware:
    """Middleware de performance para FastAPI"""
    
    def __init__(self, config: PerformanceConfig, monitor: PerformanceMonitor):
        self.config = config
        self.monitor = monitor
    
    async def __call__(self, request: Request, call_next):
        """Procesar petición con monitoreo de performance"""
        start_time = time.time()
        
        # Procesar petición
        response = await call_next(request)
        
        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time
        
        # Registrar métrica
        self.monitor.record_metric(
            "request_processing_time",
            processing_time,
            {
                "method": request.method,
                "path": request.url.path,
                "status_code": str(response.status_code)
            }
        )
        
        # Agregar headers de performance
        response.headers["X-Processing-Time"] = str(processing_time)
        
        return response

# ============================================================================
# UTILIDADES DE PERFORMANCE
# ============================================================================

def cache_result(ttl: int = 300, key_prefix: str = "func"):
    """Decorador para cachear resultados de funciones"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar clave de caché
            key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # TODO: Implementar lógica de caché real
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def batch_process(items: List[Any], batch_size: int = 100):
    """Procesar items en lotes"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

@asynccontextmanager
async def performance_context(monitor: PerformanceMonitor, operation_name: str):
    """Context manager para medir performance"""
    start_time = time.time()
    try:
        yield
    finally:
        execution_time = time.time() - start_time
        monitor.record_metric(f"{operation_name}_time", execution_time)

# ============================================================================
# INSTANCIA GLOBAL
# ============================================================================

# Configuración por defecto
default_config = PerformanceConfig()

# Instancias globales (se inicializarán cuando sea necesario)
_cache_instance: Optional[AdvancedCache] = None
_query_optimizer: Optional[QueryOptimizer] = None
_response_optimizer: Optional[ResponseOptimizer] = None
_performance_monitor: Optional[PerformanceMonitor] = None
_performance_middleware: Optional[PerformanceMiddleware] = None

def get_cache_instance(redis_client: Optional[redis.Redis] = None, config: Optional[PerformanceConfig] = None) -> AdvancedCache:
    """Obtener instancia de caché"""
    global _cache_instance
    if _cache_instance is None:
        if redis_client is None:
            raise ValueError("Redis client required for cache initialization")
        _cache_instance = AdvancedCache(redis_client, config or default_config)
    return _cache_instance

def get_query_optimizer(config: Optional[PerformanceConfig] = None) -> QueryOptimizer:
    """Obtener instancia de optimizador de consultas"""
    global _query_optimizer
    if _query_optimizer is None:
        _query_optimizer = QueryOptimizer(config or default_config)
    return _query_optimizer

def get_response_optimizer(config: Optional[PerformanceConfig] = None) -> ResponseOptimizer:
    """Obtener instancia de optimizador de respuestas"""
    global _response_optimizer
    if _response_optimizer is None:
        _response_optimizer = ResponseOptimizer(config or default_config)
    return _response_optimizer

def get_performance_monitor(config: Optional[PerformanceConfig] = None) -> PerformanceMonitor:
    """Obtener instancia de monitor de performance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(config or default_config)
    return _performance_monitor

def get_performance_middleware(config: Optional[PerformanceConfig] = None, monitor: Optional[PerformanceMonitor] = None) -> PerformanceMiddleware:
    """Obtener instancia de middleware de performance"""
    global _performance_middleware
    if _performance_middleware is None:
        if monitor is None:
            monitor = get_performance_monitor(config)
        _performance_middleware = PerformanceMiddleware(config or default_config, monitor)
    return _performance_middleware 