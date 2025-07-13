from typing import Optional
try:
    import redis.asyncio as redis
    from redis import exceptions as redis_exceptions
except ImportError:
    # Fallback para desarrollo si redis no está instalado
    redis = None
    redis_exceptions = None

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class RedisClient:
    def __init__(self, host: Optional[str], port: Optional[int], password: Optional[str]):
        self.host = host
        self.port = port
        self.password = password
        self.pool: Optional[redis.ConnectionPool] = None
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """
        Establece el pool de conexiones a Redis usando la URL de configuración.
        """
        if not redis:
            logger.warning("Redis no disponible - biblioteca no instalada")
            return
            
        if not self.host or not self.port:
            logger.info("Redis no configurado (host o puerto no especificado), omitiendo conexión.")
            return

        try:
            # Usar la URL construida por settings que maneja SSL y protocolo correctamente
            from app.core.config import settings
            redis_url = settings.get_redis_url()
            
            self.pool = redis.ConnectionPool.from_url(
                redis_url,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.client = redis.Redis.from_pool(self.pool)
            
            if self.client:
                await self.client.ping()
                logger.info(f"Conectado exitosamente a Redis en {self.host}:{self.port}")

        except redis_exceptions.AuthenticationError as e:
            logger.error(f"Error de autenticación al conectar con Redis: {e}")
            self.pool = None
            self.client = None
            raise
        except redis_exceptions.ConnectionError as e:
            logger.error(f"No se pudo conectar a Redis en {self.host}:{self.port}. Error: {e}")
            self.pool = None
            self.client = None
            raise
        except Exception as e:
            logger.error(f"Ocurrió un error inesperado al conectar con Redis: {e}")
            self.pool = None
            self.client = None
            raise

    async def close(self):
        """
        Cierra la conexión a Redis.
        """
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        logger.info("Conexión con Redis cerrada.")
    
    def get_client(self) -> Optional[redis.Redis]:
        """
        Retorna una instancia del cliente de Redis si está conectado.
        """
        if not self.client:
            logger.warning("Intento de obtener cliente de Redis sin estar conectado.")
        return self.client


# Instancia global del cliente de Redis
redis_client = RedisClient(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD
)

# Exportar la instancia para ser usada en la aplicación
__all__ = ["redis_client"] 