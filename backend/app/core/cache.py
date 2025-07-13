import json
import hashlib
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        """Inicializar el gestor de caché en memoria"""
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.info("Sistema de caché en memoria inicializado")

    def is_available(self) -> bool:
        """Verificar si el caché está disponible"""
        return True

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generar clave única para el caché"""
        key_parts = [prefix]
        
        # Agregar argumentos posicionales
        for arg in args:
            key_parts.append(str(arg))
        
        # Agregar argumentos nombrados ordenados
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del caché"""
        try:
            if key in self._cache:
                item = self._cache[key]
                # Verificar expiración
                if 'expire_at' in item and datetime.now() > item['expire_at']:
                    del self._cache[key]
                    return None
                return item['value']
            return None
        except Exception as e:
            logger.error(f"Error obteniendo del caché: {e}")
            return None

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Establecer valor en el caché"""
        try:
            cache_item = {'value': value}
            if expire:
                cache_item['expire_at'] = datetime.now() + timedelta(seconds=expire)
            
            self._cache[key] = cache_item
            return True
        except Exception as e:
            logger.error(f"Error estableciendo en caché: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Eliminar clave del caché"""
        try:
            if key in self._cache:
                del self._cache[key]
            return True
        except Exception as e:
            logger.error(f"Error eliminando del caché: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Eliminar claves que coincidan con un patrón"""
        try:
            deleted_count = 0
            keys_to_delete = []
            
            for key in self._cache.keys():
                if pattern.replace('*', '') in key:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._cache[key]
                deleted_count += 1
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error eliminando patrón del caché: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Verificar si una clave existe"""
        try:
            return key in self._cache
        except Exception as e:
            logger.error(f"Error verificando existencia en caché: {e}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """Establecer tiempo de expiración para una clave"""
        try:
            if key in self._cache:
                self._cache[key]['expire_at'] = datetime.now() + timedelta(seconds=seconds)
                return True
            return False
        except Exception as e:
            logger.error(f"Error estableciendo expiración en caché: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del caché"""
        try:
            # Limpiar elementos expirados
            expired_count = 0
            for key in list(self._cache.keys()):
                if 'expire_at' in self._cache[key] and datetime.now() > self._cache[key]['expire_at']:
                    del self._cache[key]
                    expired_count += 1
            
            return {
                "status": "available",
                "total_keys": len(self._cache),
                "expired_cleaned": expired_count,
                "memory_usage": "N/A (in-memory)"
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del caché: {e}")
            return {"status": "error", "message": str(e)}

    def clear_all(self) -> bool:
        """Limpiar todo el caché"""
        try:
            self._cache.clear()
            return True
        except Exception as e:
            logger.error(f"Error limpiando caché: {e}")
            return False

# Instancia global del gestor de caché
cache_manager = CacheManager()

def cached(prefix: str, expire: Optional[int] = 300):
    """
    Decorador para cachear resultados de funciones
    
    Args:
        prefix: Prefijo para las claves del caché
        expire: Tiempo de expiración en segundos (por defecto 5 minutos)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única
            cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # Intentar obtener del caché
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit para {cache_key}")
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, expire)
            logger.debug(f"Cache miss para {cache_key}, resultado cacheado")
            
            return result
        return wrapper
    return decorator

def invalidate_cache(prefix: str):
    """
    Decorador para invalidar caché después de operaciones de escritura
    
    Args:
        prefix: Prefijo de las claves a invalidar
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidar todas las claves que coincidan con el prefijo
            pattern = f"{prefix}:*"
            deleted_count = cache_manager.delete_pattern(pattern)
            if deleted_count > 0:
                logger.debug(f"Invalidadas {deleted_count} claves de caché con patrón {pattern}")
            
            return result
        return wrapper
    return decorator

# Funciones de utilidad para caché específico
class CacheKeys:
    """Claves predefinidas para diferentes tipos de datos"""
    
    @staticmethod
    def user(user_id: int) -> str:
        return f"user:{user_id}"
    
    @staticmethod
    def users_list(page: int, limit: int, filters: str = "") -> str:
        return f"users:list:{page}:{limit}:{filters}"
    
    @staticmethod
    def clase(clase_id: int) -> str:
        return f"clase:{clase_id}"
    
    @staticmethod
    def clases_list(page: int, limit: int, filters: str = "") -> str:
        return f"clases:list:{page}:{limit}:{filters}"
    
    @staticmethod
    def empleado(empleado_id: int) -> str:
        return f"empleado:{empleado_id}"
    
    @staticmethod
    def empleados_list(page: int, limit: int, filters: str = "") -> str:
        return f"empleados:list:{page}:{limit}:{filters}"
    
    @staticmethod
    def pago(pago_id: int) -> str:
        return f"pago:{pago_id}"
    
    @staticmethod
    def pagos_list(page: int, limit: int, filters: str = "") -> str:
        return f"pagos:list:{page}:{limit}:{filters}"
    
    @staticmethod
    def asistencia(asistencia_id: int) -> str:
        return f"asistencia:{asistencia_id}"
    
    @staticmethod
    def asistencias_list(page: int, limit: int, filters: str = "") -> str:
        return f"asistencias:list:{page}:{limit}:{filters}"
    
    @staticmethod
    def rutina(rutina_id: int) -> str:
        return f"rutina:{rutina_id}"
    
    @staticmethod
    def rutinas_list(page: int, limit: int, filters: str = "") -> str:
        return f"rutinas:list:{page}:{limit}:{filters}"
    
    @staticmethod
    def kpis() -> str:
        return "kpis:current"
    
    @staticmethod
    def graficos() -> str:
        return "graficos:current"
    
    @staticmethod
    def reportes() -> str:
        return "reportes:current" 