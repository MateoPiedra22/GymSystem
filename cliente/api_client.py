"""
Cliente API Optimizado para comunicación con el backend del Sistema de Gimnasio v6
Incluye pooling de conexiones, retry inteligente, cache y validaciones robustas
"""
import requests
import logging
import time
import json
import hashlib
import ssl
import socket
from typing import Dict, Any, Optional, List, Union, Callable
from urllib.parse import urljoin, urlparse
from requests.adapters import HTTPAdapter
import threading
from datetime import datetime, timedelta
from functools import wraps
import weakref
import random

# Configurar warnings y retry con fallback
try:
    import requests.packages.urllib3 as urllib3
    urllib3.disable_warnings()
except:
    pass  # Ignorar si no está disponible

# Importar Retry con fallback
try:
    from requests.packages.urllib3.util.retry import Retry
except ImportError:
    # Usar clase básica de retry personalizada
    class Retry:
        def __init__(self, total=3, backoff_factor=1, status_forcelist=None, **kwargs):
            self.total = total
            self.backoff_factor = backoff_factor
            self.status_forcelist = status_forcelist or []

logger = logging.getLogger(__name__)

class ApiConnectionError(Exception):
    """Error de conexión con la API"""
    pass

class ApiAuthenticationError(Exception):
    """Error de autenticación"""
    pass

class ApiValidationError(Exception):
    """Error de validación de datos"""
    pass

class ApiRateLimitError(Exception):
    """Error de límite de velocidad"""
    pass

class ApiSSLValidationError(Exception):
    """Error de validación SSL"""
    pass

class ExponentialBackoff:
    """Implementación de backoff exponencial con jitter"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, max_attempts: int = 10):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts
        self.attempt = 0
    
    def get_delay(self) -> float:
        """Calcula el delay para el siguiente intento"""
        if self.attempt >= self.max_attempts:
            return self.max_delay
        
        # Backoff exponencial: base_delay * 2^attempt
        delay = min(self.base_delay * (2 ** self.attempt), self.max_delay)
        
        # Agregar jitter para evitar thundering herd
        jitter = random.uniform(0, 0.1 * delay)
        delay += jitter
        
        self.attempt += 1
        return delay
    
    def reset(self) -> None:
        """Reinicia el contador de intentos"""
        self.attempt = 0
    
    def should_retry(self) -> bool:
        """Determina si se debe reintentar"""
        return self.attempt < self.max_attempts

class SSLCertificateValidator:
    """Validador de certificados SSL"""
    
    @staticmethod
    def validate_certificate(hostname: str, port: int = 443) -> bool:
        """
        Valida el certificado SSL de un hostname
        
        Args:
            hostname: Nombre del host a validar
            port: Puerto para la conexión SSL
            
        Returns:
            True si el certificado es válido, False en caso contrario
        """
        try:
            # Crear contexto SSL con validación estricta
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            # Intentar conexión SSL
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Verificar que el certificado existe
                    if not cert:
                        logger.warning(f"No se pudo obtener certificado SSL para {hostname}")
                        return False
                    
                    # Verificar fecha de expiración
                    if 'notAfter' in cert:
                        import datetime
                        not_after_str = cert['notAfter']
                        if isinstance(not_after_str, str):
                            not_after = datetime.datetime.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z')
                            if not_after < datetime.datetime.now():
                                logger.warning(f"Certificado SSL expirado para {hostname}")
                                return False
                    
                    logger.info(f"Certificado SSL válido para {hostname}")
                    return True
                    
        except ssl.SSLError as e:
            logger.error(f"Error SSL para {hostname}: {e}")
            return False
        except socket.timeout:
            logger.error(f"Timeout validando certificado SSL para {hostname}")
            return False
        except Exception as e:
            logger.error(f"Error validando certificado SSL para {hostname}: {e}")
            return False
    
    @staticmethod
    def validate_url_ssl(url: str) -> bool:
        """
        Valida SSL para una URL
        
        Args:
            url: URL a validar
            
        Returns:
            True si la URL tiene SSL válido, False en caso contrario
        """
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme.lower() != 'https':
                return True  # No es HTTPS, no hay SSL que validar
            
            hostname = parsed_url.hostname
            if not hostname:
                return False
            
            port = parsed_url.port or 443
            
            return SSLCertificateValidator.validate_certificate(hostname, port)
            
        except Exception as e:
            logger.error(f"Error validando SSL para URL {url}: {e}")
            return False

class CacheEntry:
    """Representa una entrada individual en el cache"""
    
    def __init__(self, value: Any, ttl: int, created: Optional[float] = None):
        self.value = value
        self.ttl = ttl
        self.created = created if created is not None else time.time()
    
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado"""
        return time.time() - self.created > self.ttl
    
    def get_age(self) -> float:
        """Obtiene la edad de la entrada en segundos"""
        return time.time() - self.created

class CacheStorage:
    """Maneja el almacenamiento físico del cache"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Obtiene una entrada del cache"""
        with self._lock:
            return self.cache.get(key)
    
    def set(self, key: str, entry: CacheEntry) -> None:
        """Almacena una entrada en el cache"""
        with self._lock:
            self.cache[key] = entry
    
    def remove(self, key: str) -> None:
        """Remueve una entrada del cache"""
        with self._lock:
            self.cache.pop(key, None)
    
    def clear(self) -> None:
        """Limpia todo el cache"""
        with self._lock:
            self.cache.clear()
    
    def size(self) -> int:
        """Obtiene el tamaño actual del cache"""
        with self._lock:
            return len(self.cache)
    
    def keys(self) -> list:
        """Obtiene todas las claves del cache"""
        with self._lock:
            return list(self.cache.keys())

class CacheEvictionPolicy:
    """Implementa políticas de evicción para el cache"""
    
    @staticmethod
    def lru_evict(storage: CacheStorage) -> str:
        """Evicción LRU (Least Recently Used)"""
        oldest_key = min(storage.keys(), key=lambda k: storage.get(k).created if storage.get(k) else 0)
        return oldest_key
    
    @staticmethod
    def ttl_evict(storage: CacheStorage) -> list:
        """Evicción por TTL expirado"""
        expired_keys = []
        for key in storage.keys():
            entry = storage.get(key)
            if entry and entry.is_expired():
                expired_keys.append(key)
        return expired_keys

class CacheMetrics:
    """Maneja métricas del cache"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self._lock = threading.RLock()
    
    def record_hit(self) -> None:
        """Registra un hit en el cache"""
        with self._lock:
            self.hits += 1
    
    def record_miss(self) -> None:
        """Registra un miss en el cache"""
        with self._lock:
            self.misses += 1
    
    def record_eviction(self) -> None:
        """Registra una evicción del cache"""
        with self._lock:
            self.evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            return {
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }

class ApiCache:
    """Cache inteligente para respuestas de API"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.storage = CacheStorage(max_size)
        self.default_ttl = default_ttl
        self.metrics = CacheMetrics()
        self.eviction_policy = CacheEvictionPolicy()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del cache si no ha expirado"""
        entry = self.storage.get(key)
        
        if entry is None:
            self.metrics.record_miss()
            return None
        
        # Verificar expiración
        if entry.is_expired():
            self.storage.remove(key)
            self.metrics.record_miss()
            return None
        
        self.metrics.record_hit()
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Almacena un valor en el cache"""
        # Limpiar entradas expiradas
        self._cleanup_expired()
        
        # Verificar si el cache está lleno
        if self.storage.size() >= self.storage.max_size:
            self._evict_oldest()
        
        # Crear y almacenar entrada
        entry = CacheEntry(value, ttl or self.default_ttl)
        self.storage.set(key, entry)
    
    def _cleanup_expired(self) -> None:
        """Limpia entradas expiradas"""
        expired_keys = self.eviction_policy.ttl_evict(self.storage)
        for key in expired_keys:
            self.storage.remove(key)
            self.metrics.record_eviction()
    
    def _evict_oldest(self) -> None:
        """Evicta la entrada más antigua"""
        if self.storage.size() > 0:
            oldest_key = self.eviction_policy.lru_evict(self.storage)
            self.storage.remove(oldest_key)
            self.metrics.record_eviction()
    
    def clear(self) -> None:
        """Limpia todo el cache"""
        self.storage.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        stats = self.metrics.get_stats()
        stats['current_size'] = self.storage.size()
        stats['max_size'] = self.storage.max_size
        return stats

def cache_response(ttl: int = 300, cache_key_func: Optional[Callable] = None):
    """Decorador para cachear respuestas de API"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, '_cache'):
                return func(self, *args, **kwargs)
            
            # Generar clave de cache
            if cache_key_func:
                cache_key = cache_key_func(self, *args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Intentar obtener del cache
            cached_result = self._cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit para {cache_key}")
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = func(self, *args, **kwargs)
            if result is not None:
                self._cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

class ApiClient:
    """
    Cliente optimizado para comunicación con la API del backend.
    
    Features:
    - Pooling de conexiones HTTP
    - Retry inteligente con backoff exponencial
    - Cache de respuestas
    - Validación de datos
    - Manejo robusto de errores
    - Métricas de rendimiento
    - Validación de certificados SSL
    """
    
    def __init__(self, base_url: str = "https://api.gymnasium.com/api", **kwargs):
        """
        Inicializa el cliente API optimizado.
        
        Args:
            base_url: URL base de la API
            **kwargs: Configuraciones adicionales
        """
        # Configuración básica
        self.base_url = base_url.rstrip('/')
        self.timeout = kwargs.get('timeout', 30)
        self.max_retries = kwargs.get('max_retries', 3)
        self.verify_ssl = kwargs.get('verify_ssl', True)
        self.cache_enabled = kwargs.get('cache_enabled', True)
        self.ssl_validation = kwargs.get('ssl_validation', True)
        
        # Estado de autenticación
        self.access_token: Optional[str] = None
        self.token_type: str = "Bearer"
        self.user_id: Optional[str] = None
        self.username: Optional[str] = None
        self.is_admin: bool = False
        self.session_expires_at: Optional[datetime] = None
        
        # Backoff exponencial
        self.backoff = ExponentialBackoff(
            base_delay=kwargs.get('backoff_base_delay', 1.0),
            max_delay=kwargs.get('backoff_max_delay', 60.0),
            max_attempts=kwargs.get('backoff_max_attempts', 10)
        )
        
        # Cache y métricas
        if self.cache_enabled:
            self._cache = ApiCache(
                max_size=kwargs.get('cache_max_size', 1000),
                default_ttl=kwargs.get('cache_ttl', 300)
            )
        
        self._metrics = {
            'requests_made': 0,
            'requests_failed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_response_time': 0,
            'last_request_time': None,
            'ssl_validation_failures': 0,
            'backoff_retries': 0
        }
        
        # Lock para thread safety
        self._lock = threading.RLock()
        
        # Validar SSL si es necesario
        if self.ssl_validation and self.verify_ssl:
            self._validate_ssl_certificate()
        
        # Configurar sesión HTTP optimizada
        self._setup_session()
        
        logger.info(f"ApiClient inicializado para {self.base_url}")
    
    def _validate_ssl_certificate(self) -> None:
        """Valida el certificado SSL del servidor"""
        try:
            parsed_url = urlparse(self.base_url)
            if parsed_url.scheme.lower() == 'https':
                if not SSLCertificateValidator.validate_url_ssl(self.base_url):
                    with self._lock:
                        self._metrics['ssl_validation_failures'] += 1
                    if self.ssl_validation:
                        raise ApiSSLValidationError(f"Certificado SSL inválido para {self.base_url}")
                    else:
                        logger.warning(f"Certificado SSL inválido para {self.base_url}, continuando sin validación")
        except Exception as e:
            logger.error(f"Error validando certificado SSL: {e}")
            if self.ssl_validation:
                raise
    
    def _setup_session(self) -> None:
        """Configura la sesión HTTP con pooling optimizado"""
        self.session = requests.Session()
        
        # Configurar headers por defecto
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "GymClient/6.0.0"
        })
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
            raise_on_redirect=False,
            raise_on_status=False
        )
        
        # Configurar adaptadores HTTP con pooling
        http_adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
            pool_block=False
        )
        
        self.session.mount("http://", http_adapter)
        self.session.mount("https://", http_adapter)
        
        # Configuración SSL
        self.session.verify = self.verify_ssl
    
    def _make_request_with_backoff(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        retries: Optional[int] = None
    ) -> Any:
        """
        Realiza una petición HTTP con backoff exponencial robusto.
        """
        self.backoff.reset()
        last_exception = None
        
        while self.backoff.should_retry():
            try:
                return self._make_request(
                    method, endpoint, params, data, files, headers, timeout, retries
                )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_exception = e
                delay = self.backoff.get_delay()
                
                with self._lock:
                    self._metrics['backoff_retries'] += 1
                
                logger.warning(f"Error de conexión en {method} {endpoint}, reintentando en {delay:.2f}s: {e}")
                time.sleep(delay)
                
                # Recrear sesión si es necesario
                if isinstance(e, requests.exceptions.ConnectionError):
                    self._setup_session()
            except (ApiAuthenticationError, ApiValidationError, ApiRateLimitError):
                # No reintentar para estos errores
                raise
            except Exception as e:
                last_exception = e
                delay = self.backoff.get_delay()
                
                with self._lock:
                    self._metrics['backoff_retries'] += 1
                
                logger.warning(f"Error inesperado en {method} {endpoint}, reintentando en {delay:.2f}s: {e}")
                time.sleep(delay)
        
        # Si llegamos aquí, se agotaron los intentos
        if last_exception:
            raise ApiConnectionError(f"Se agotaron los intentos de conexión para {method} {endpoint}: {last_exception}")
        else:
            raise ApiConnectionError(f"Se agotaron los intentos de conexión para {method} {endpoint}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        retries: Optional[int] = None
    ) -> Any:
        """
        Realiza una petición HTTP optimizada con métricas y validaciones.
        """
        start_time = time.time()
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        
        # Configurar headers de la petición
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Configurar timeout
        request_timeout = timeout or self.timeout
        
        # Incrementar contador de peticiones
        with self._lock:
            self._metrics['requests_made'] += 1
        
        try:
            # Validar datos antes de enviar
            if data:
                self._validate_request_data(data)
            
            # Preparar argumentos de la petición
            request_kwargs = {
                'timeout': request_timeout,
                'headers': request_headers,
                'params': params,
            }
            
            if files:
                # Para archivos, usar form-data
                request_kwargs['data'] = data
                request_kwargs['files'] = files
                # Remover Content-Type para que requests lo configure automáticamente
                request_headers.pop('Content-Type', None)
            else:
                # Para datos JSON
                request_kwargs['json'] = data
            
            # Realizar petición
            response = self.session.request(method, url, **request_kwargs)
            
            # Manejar respuesta
            return self._handle_response(response, start_time)
            
        except requests.exceptions.Timeout:
            self._record_failed_request()
            raise ApiConnectionError(f"Timeout al conectar con {endpoint}")
        
        except requests.exceptions.ConnectionError:
            self._record_failed_request()
            raise ApiConnectionError(f"Error de conexión al endpoint {endpoint}")
        
        except requests.exceptions.RequestException as e:
            self._record_failed_request()
            raise ApiConnectionError(f"Error en petición a {endpoint}: {str(e)}")
        
        except Exception as e:
            self._record_failed_request()
            logger.error(f"Error inesperado en {method} {endpoint}: {e}")
            raise
    
    def _handle_response(self, response: requests.Response, start_time: float) -> Any:
        """Maneja la respuesta HTTP con validaciones y métricas"""
        
        # Calcular tiempo de respuesta
        response_time = time.time() - start_time
        self._update_metrics(response_time)
        
        # Log de la petición
        logger.debug(f"{response.request.method} {response.url} - {response.status_code} ({response_time:.2f}s)")
        
        # Manejar códigos de estado específicos
        if response.status_code == 401:
            self._handle_unauthorized()
            raise ApiAuthenticationError("Token de autenticación inválido o expirado")
        
        elif response.status_code == 403:
            raise ApiAuthenticationError("Acceso denegado - permisos insuficientes")
        
        elif response.status_code == 429:
            retry_after = response.headers.get('Retry-After', '60')
            raise ApiRateLimitError(f"Límite de velocidad excedido. Reintentar en {retry_after} segundos")
        
        elif response.status_code == 422:
            try:
                error_data = response.json()
                raise ApiValidationError(f"Error de validación: {error_data}")
            except ValueError:
                raise ApiValidationError("Error de validación en los datos enviados")
        
        elif not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get('detail', f'Error HTTP {response.status_code}')
            except ValueError:
                error_message = f'Error HTTP {response.status_code}: {response.text}'
            
            raise ApiConnectionError(error_message)
        
        # Procesar respuesta exitosa
        if response.status_code == 204:
            return None
        
        try:
            return response.json()
        except ValueError:
            logger.warning(f"Respuesta no JSON desde {response.url}")
            return response.text
    
    def _validate_request_data(self, data: Dict[str, Any]) -> None:
        """Valida datos de la petición antes de enviar"""
        if not isinstance(data, dict):
            raise ApiValidationError("Los datos deben ser un diccionario")
        
        # Validar que no haya valores None en campos requeridos
        # Esta validación se puede expandir según necesidades específicas
        for key, value in data.items():
            if isinstance(value, str) and len(value.strip()) == 0:
                logger.warning(f"Campo {key} está vacío")
    
    def _handle_unauthorized(self) -> None:
        """Maneja respuestas de autenticación inválida"""
        with self._lock:
            self.user_id = None
            self.username = None
            self.is_admin = False
            self.session_expires_at = None
            
            # Limpiar cache
            if hasattr(self, '_cache'):
                self._cache.clear()
        
        logger.warning("Sesión expirada o inválida - limpiando estado de autenticación")
    
    def _record_failed_request(self) -> None:
        """Registra una petición fallida en las métricas"""
        with self._lock:
            self._metrics['requests_failed'] += 1
    
    def _update_metrics(self, response_time: float) -> None:
        """Actualiza métricas de rendimiento"""
        with self._lock:
            # Actualizar tiempo promedio de respuesta
            if self._metrics['requests_made'] == 1:
                self._metrics['average_response_time'] = response_time
            else:
                # Promedio móvil ponderado
                alpha = 0.1  # Factor de suavizado
                self._metrics['average_response_time'] = (
                    alpha * response_time + 
                    (1 - alpha) * self._metrics['average_response_time']
                )
            
            self._metrics['last_request_time'] = datetime.now()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento del cliente"""
        with self._lock:
            metrics = self._metrics.copy()
            
            # Agregar métricas de cache si está habilitado
            if hasattr(self, '_cache'):
                metrics['cache_size'] = self._cache.storage.size()
                metrics['cache_hit_rate'] = (
                    self._metrics['cache_hits'] / 
                    (self._metrics['cache_hits'] + self._metrics['cache_misses'])
                    if (self._metrics['cache_hits'] + self._metrics['cache_misses']) > 0
                    else 0
                )
            
            return metrics
    
    def clear_cache(self) -> None:
        """Limpia el cache de respuestas"""
        if hasattr(self, '_cache'):
            self._cache.clear()
            logger.info("Cache de API limpiado")
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Realiza login con credenciales de usuario.
        
        Args:
            username: Nombre de usuario o email
            password: Contraseña del usuario
            
        Returns:
            Datos del token de autenticación
            
        Raises:
            ApiAuthenticationError: Si las credenciales son inválidas
            ApiConnectionError: Si hay problemas de conexión
        """
        try:
            # Validar credenciales
            if not username or not password:
                raise ApiValidationError("Usuario y contraseña son requeridos")
            
            if len(username.strip()) < 3:
                raise ApiValidationError("Usuario debe tener al menos 3 caracteres")
            
            if len(password) < 1:
                raise ApiValidationError("Contraseña es requerida")
            
            # Realizar petición de login con backoff
            response_data = self._make_request_with_backoff(
                'POST',
                '/auth/login/json',
                data={
                    'username': username.strip(),
                    'password': password
                }
            )
            
            # Validar respuesta
            if not response_data or 'access_token' not in response_data:
                raise ApiAuthenticationError("Respuesta de login inválida")
            
            # Configurar token
            self.set_token(response_data)
            
            logger.info(f"Login exitoso para usuario: {username}")
            return response_data
            
        except ApiAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error en login: {e}")
            raise ApiAuthenticationError(f"Error en login: {str(e)}")
    
    def logout(self) -> bool:
        """
        Realiza logout del usuario actual.
        
        Returns:
            True si el logout fue exitoso, False en caso contrario
        """
        try:
            if not self.is_authenticated():
                logger.info("Usuario no autenticado, no se requiere logout")
                return True
            
            # Intentar logout en el servidor
            try:
                self._make_request_with_backoff('POST', '/auth/logout')
            except Exception as e:
                logger.warning(f"Error en logout del servidor: {e}")
            
            # Limpiar estado local
            self.clear_token()
            logger.info("Logout exitoso")
            return True
            
        except Exception as e:
            logger.error(f"Error en logout: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """
        Verifica si el usuario está autenticado.
        
        Returns:
            True si está autenticado, False en caso contrario
        """
        if not self.access_token:
            return False
        
        # Verificar expiración si está disponible
        if self.session_expires_at and datetime.now() > self.session_expires_at:
            logger.info("Token expirado")
            self.clear_token()
            return False
        
        return True
    
    def set_token(self, token_data: Dict[str, Any]) -> None:
        """
        Configura el token de autenticación.
        
        Args:
            token_data: Datos del token incluyendo access_token, user_id, etc.
        """
        try:
            # Validar datos del token
            required_fields = ['access_token']
            for field in required_fields:
                if field not in token_data:
                    raise ApiValidationError(f"Campo requerido faltante en token_data: {field}")
            
            with self._lock:
                self.access_token = token_data['access_token']
                self.token_type = token_data.get('token_type', 'Bearer')
                self.user_id = token_data.get('user_id')
                self.username = token_data.get('username')
                self.is_admin = token_data.get('is_admin', False)
                
                # Configurar expiración si está disponible
                if 'expires_in' in token_data:
                    self.session_expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
                else:
                    self.session_expires_at = None
            
            # Configurar header de autorización
            self.session.headers['Authorization'] = f"{self.token_type} {self.access_token}"
            
            logger.info(f"Token configurado para usuario: {self.username}")
            
        except Exception as e:
            logger.error(f"Error configurando token: {e}")
            raise
    
    def clear_token(self) -> None:
        """Limpia el token de autenticación y estado relacionado"""
        with self._lock:
            self.access_token = None
            self.token_type = "Bearer"
            self.user_id = None
            self.username = None
            self.is_admin = False
            self.session_expires_at = None
        
        # Remover header de autorización
        self.session.headers.pop('Authorization', None)
        
        # Limpiar cache
        if hasattr(self, '_cache'):
            self._cache.clear()
        
        logger.info("Token de autenticación limpiado")
    
    @cache_response(ttl=60)
    def get_current_user_profile(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el perfil del usuario actual.
        
        Returns:
            Datos del perfil del usuario o None si no está autenticado
        """
        if not self.is_authenticated():
            return None
        
        try:
            return self._make_request_with_backoff('GET', '/auth/me')
        except Exception as e:
            logger.error(f"Error obteniendo perfil de usuario: {e}")
            return None
    
    def check_connection(self, timeout: int = 5) -> bool:
        """
        Verifica la conectividad con el servidor.
        
        Args:
            timeout: Timeout en segundos para la verificación
            
        Returns:
            True si hay conectividad, False en caso contrario
        """
        try:
            self._make_request('GET', '/health', timeout=timeout)
            return True
        except Exception as e:
            logger.debug(f"Error verificando conectividad: {e}")
            return False
    
    def ping(self) -> Dict[str, Any]:
        """
        Realiza un ping al servidor para verificar estado.
        
        Returns:
            Información del estado del servidor
        """
        try:
            return self._make_request_with_backoff('GET', '/health')
        except Exception as e:
            logger.error(f"Error en ping: {e}")
            return {'status': 'error', 'message': str(e)}
    
    # Métodos para usuarios
    @cache_response(ttl=180)
    def get_usuarios(self, **kwargs) -> List[Dict[str, Any]]:
        """Obtiene lista de usuarios con filtros opcionales"""
        return self._make_request_with_backoff('GET', '/usuarios', params=kwargs)
    
    def get_usuario(self, usuario_id: str) -> Dict[str, Any]:
        """Obtiene un usuario específico por ID"""
        return self._make_request_with_backoff('GET', f'/usuarios/{usuario_id}')
    
    def create_usuario(self, usuario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo usuario"""
        return self._make_request_with_backoff('POST', '/usuarios', data=usuario_data)
    
    def update_usuario(self, usuario_id: str, usuario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un usuario existente"""
        return self._make_request_with_backoff('PUT', f'/usuarios/{usuario_id}', data=usuario_data)
    
    def delete_usuario(self, usuario_id: str) -> None:
        """Elimina un usuario"""
        self._make_request_with_backoff('DELETE', f'/usuarios/{usuario_id}')
    
    # Métodos para clases
    @cache_response(ttl=300)
    def get_clases(self, **kwargs) -> List[Dict[str, Any]]:
        """Obtiene lista de clases con filtros opcionales"""
        return self._make_request_with_backoff('GET', '/clases', params=kwargs)
    
    def get_clase(self, clase_id: str) -> Dict[str, Any]:
        """Obtiene una clase específica por ID"""
        return self._make_request_with_backoff('GET', f'/clases/{clase_id}')
    
    def create_clase(self, clase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una nueva clase"""
        return self._make_request_with_backoff('POST', '/clases', data=clase_data)
    
    def update_clase(self, clase_id: str, clase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza una clase existente"""
        return self._make_request_with_backoff('PUT', f'/clases/{clase_id}', data=clase_data)
    
    def delete_clase(self, clase_id: str) -> None:
        """Elimina una clase"""
        self._make_request_with_backoff('DELETE', f'/clases/{clase_id}')
    
    # Métodos para pagos
    @cache_response(ttl=120)
    def get_pagos(self, **kwargs) -> List[Dict[str, Any]]:
        """Obtiene lista de pagos con filtros opcionales"""
        return self._make_request_with_backoff('GET', '/pagos', params=kwargs)
    
    def get_pago(self, pago_id: str) -> Dict[str, Any]:
        """Obtiene un pago específico por ID"""
        return self._make_request_with_backoff('GET', f'/pagos/{pago_id}')
    
    def create_pago(self, pago_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo pago"""
        return self._make_request_with_backoff('POST', '/pagos', data=pago_data)
    
    def update_pago(self, pago_id: str, pago_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un pago existente"""
        return self._make_request_with_backoff('PUT', f'/pagos/{pago_id}', data=pago_data)
    
    def delete_pago(self, pago_id: str) -> None:
        """Elimina un pago"""
        self._make_request_with_backoff('DELETE', f'/pagos/{pago_id}')
    
    def cleanup(self) -> None:
        """Limpia recursos del cliente"""
        try:
            # Cerrar sesión HTTP
            if hasattr(self, 'session'):
                self.session.close()
            
            # Limpiar cache
            if hasattr(self, '_cache'):
                self._cache.clear()
            
            logger.info("Recursos del ApiClient limpiados")
            
        except Exception as e:
            logger.error(f"Error limpiando recursos: {e}")
    
    def __del__(self):
        """Destructor para limpieza automática"""
        try:
            self.cleanup()
        except:
            pass

def create_api_client(config: Dict[str, Any]) -> ApiClient:
    """
    Factory function para crear un ApiClient configurado.
    
    Args:
        config: Configuración del cliente API
        
    Returns:
        Instancia de ApiClient configurada
    """
    return ApiClient(
        base_url=config.get('api_url', 'http://localhost:8000/api'),
        timeout=config.get('timeout', 30),
        max_retries=config.get('max_retries', 3),
        verify_ssl=config.get('verify_ssl', True),
        cache_enabled=config.get('cache_enabled', True),
        ssl_validation=config.get('ssl_validation', True),
        cache_max_size=config.get('cache_max_size', 1000),
        cache_ttl=config.get('cache_ttl', 300),
        backoff_base_delay=config.get('backoff_base_delay', 1.0),
        backoff_max_delay=config.get('backoff_max_delay', 60.0),
        backoff_max_attempts=config.get('backoff_max_attempts', 10)
    )

# Ejemplo de uso con manejo de errores robusto
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'api_url': 'http://127.0.0.1:8000',
        'cache_enabled': True,
        'verify_ssl': False,  # Para desarrollo
        'ssl_validation': True # Validar certificados SSL en producción
    }
    
    client = create_api_client(config)
    
    try:
        # Probar conexión
        ping_result = client.ping()
        logger.info(f"Ping: {ping_result}")
        
        if ping_result['status'] == 'ok':
            # Probar login
            try:
                login_data = client.login("admin", "admin123")
                if login_data:
                    logger.info(f"✅ Login exitoso: {login_data.get('username')}")
                    
                    # Obtener métricas
                    metrics = client.get_metrics()
                    logger.info(f"📊 Métricas: {metrics}")
                    
                    # Logout
                    client.logout()
                    
                else:
                    logger.error("❌ Login fallido")
                    
            except ApiValidationError as e:
                logger.error(f"❌ Error de validación: {e}")
            except ApiAuthenticationError as e:
                logger.error(f"❌ Error de autenticación: {e}")
        
    except ApiConnectionError as e:
        logger.error(f"❌ Error de conexión: {e}")
    
    finally:
        client.cleanup()
