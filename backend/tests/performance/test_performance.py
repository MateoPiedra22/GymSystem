"""
Tests de Performance - Sistema de Gimnasio v6
Verifica el rendimiento y optimización del sistema
"""

import pytest
import time
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import Request, Response
import redis.asyncio as redis

from app.core.performance import (
    PerformanceConfig,
    AdvancedCache,
    QueryOptimizer,
    ResponseOptimizer,
    PerformanceMonitor,
    PerformanceMiddleware,
    cache_result,
    batch_process,
    performance_context
)
from app.main import app
from app.core.database import get_db
from app.models.usuarios import Usuario
from app.models.asistencias import Asistencia
from app.models.clases import Clase

# Configuración de tests
@pytest.fixture
def performance_config():
    """Configuración de performance para tests"""
    return PerformanceConfig(
        CACHE_ENABLED=True,
        CACHE_TTL=60,
        CACHE_MAX_SIZE=100,
        QUERY_TIMEOUT=10,
        MAX_QUERY_RESULTS=50,
        SLOW_QUERY_THRESHOLD=0.5
    )

@pytest.fixture
def mock_redis():
    """Mock de Redis para tests"""
    redis_mock = AsyncMock(spec=redis.Redis)
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.keys.return_value = []
    return redis_mock

@pytest.fixture
def cache_instance(performance_config, mock_redis):
    """Instancia de caché para tests"""
    return AdvancedCache(mock_redis, performance_config)

@pytest.fixture
def query_optimizer(performance_config):
    """Instancia de optimizador de consultas para tests"""
    return QueryOptimizer(performance_config)

@pytest.fixture
def response_optimizer(performance_config):
    """Instancia de optimizador de respuestas para tests"""
    return ResponseOptimizer(performance_config)

@pytest.fixture
def performance_monitor(performance_config):
    """Instancia de monitor de performance para tests"""
    return PerformanceMonitor(performance_config)

@pytest.fixture
def mock_request():
    """Request mock para tests"""
    request = Mock(spec=Request)
    request.method = "GET"
    request.url.path = "/test"
    request.headers = {"X-Request-ID": "test-123"}
    return request

@pytest.fixture
def mock_response():
    """Response mock para tests"""
    response = Mock(spec=Response)
    response.status_code = 200
    response.headers = {}
    return response

class TestPerformanceConfig:
    """Tests para la configuración de performance"""
    
    def test_performance_config_defaults(self):
        """Verificar valores por defecto de la configuración"""
        config = PerformanceConfig()
        
        assert config.CACHE_ENABLED is True
        assert config.CACHE_TTL == 300
        assert config.CACHE_MAX_SIZE == 1000
        assert config.QUERY_TIMEOUT == 30
        assert config.MAX_QUERY_RESULTS == 1000
        assert config.SLOW_QUERY_THRESHOLD == 1.0
    
    def test_performance_config_custom(self):
        """Verificar configuración personalizada"""
        config = PerformanceConfig(
            CACHE_TTL=120,
            CACHE_MAX_SIZE=500,
            QUERY_TIMEOUT=15,
            SLOW_QUERY_THRESHOLD=0.5
        )
        
        assert config.CACHE_TTL == 120
        assert config.CACHE_MAX_SIZE == 500
        assert config.QUERY_TIMEOUT == 15
        assert config.SLOW_QUERY_THRESHOLD == 0.5

class TestAdvancedCache:
    """Tests para el sistema de caché avanzado"""
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, cache_instance):
        """Verificar inicialización del caché"""
        assert cache_instance.config.CACHE_TTL == 60
        assert cache_instance.config.CACHE_MAX_SIZE == 100
        assert len(cache_instance.local_cache) == 0
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache_instance, mock_redis):
        """Verificar operaciones básicas de caché"""
        # Configurar mock para simular Redis
        mock_redis.get.return_value = json.dumps({"test": "data"}).encode()
        
        # Test set
        success = await cache_instance.set("test_key", {"test": "data"})
        assert success is True
        
        # Test get
        result = await cache_instance.get("test_key")
        assert result == {"test": "data"}
        
        # Verificar que se llamó a Redis
        mock_redis.setex.assert_called_once()
        mock_redis.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_local_cache(self, cache_instance):
        """Verificar caché local"""
        # Agregar al caché local
        cache_instance.local_cache["local_key"] = "local_value"
        
        # Obtener del caché local
        result = await cache_instance.get("local_key")
        assert result == "local_value"
        
        # Verificar estadísticas
        stats = cache_instance.get_stats()
        assert stats["local_hits"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_instance, mock_redis):
        """Verificar comportamiento en cache miss"""
        mock_redis.get.return_value = None
        
        result = await cache_instance.get("missing_key", default="default_value")
        assert result == "default_value"
        
        # Verificar estadísticas
        stats = cache_instance.get_stats()
        assert stats["misses"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache_instance, mock_redis):
        """Verificar eliminación de caché"""
        # Agregar al caché local
        cache_instance.local_cache["delete_key"] = "delete_value"
        
        # Eliminar
        success = await cache_instance.delete("delete_key")
        assert success is True
        
        # Verificar que se eliminó del caché local
        assert "delete_key" not in cache_instance.local_cache
        
        # Verificar que se llamó a Redis
        mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_invalidate_pattern(self, cache_instance, mock_redis):
        """Verificar invalidación por patrón"""
        mock_redis.keys.return_value = [b"gym_cache:user:1", b"gym_cache:user:2"]
        
        count = await cache_instance.invalidate_pattern("user:*")
        assert count == 2
        
        # Verificar que se limpió el caché local
        assert len(cache_instance.local_cache) == 0
    
    @pytest.mark.asyncio
    async def test_cache_lru_eviction(self, cache_instance):
        """Verificar evicción LRU del caché local"""
        # Llenar el caché local
        for i in range(101):  # Más del límite de 100
            cache_instance.local_cache[f"key_{i}"] = f"value_{i}"
        
        # Verificar que se mantiene el límite
        assert len(cache_instance.local_cache) == 100
        
        # Verificar que se eliminó el elemento más antiguo
        assert "key_0" not in cache_instance.local_cache
        assert "key_100" in cache_instance.local_cache
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_instance, mock_redis):
        """Verificar estadísticas del caché"""
        # Simular algunas operaciones
        mock_redis.get.return_value = json.dumps({"data": "test"}).encode()
        
        await cache_instance.set("key1", "value1")
        await cache_instance.get("key1")
        await cache_instance.get("missing_key")
        await cache_instance.delete("key1")
        
        stats = cache_instance.get_stats()
        assert stats["sets"] == 1
        assert stats["redis_hits"] == 1
        assert stats["misses"] == 1
        assert stats["deletes"] == 1

class TestQueryOptimizer:
    """Tests para el optimizador de consultas"""
    
    def test_query_optimizer_initialization(self, query_optimizer):
        """Verificar inicialización del optimizador"""
        assert query_optimizer.config.QUERY_TIMEOUT == 10
        assert query_optimizer.config.MAX_QUERY_RESULTS == 50
        assert len(query_optimizer.query_stats) == 0
    
    def test_query_optimizer_limit(self, query_optimizer):
        """Verificar aplicación de límites"""
        # Mock de query
        mock_query = Mock()
        mock_query._limit = None
        
        optimized_query = query_optimizer.optimize_query(mock_query)
        
        # Verificar que se aplicó el límite
        assert optimized_query == mock_query
    
    def test_query_optimizer_timeout(self, query_optimizer):
        """Verificar aplicación de timeout"""
        # Mock de query con execution_options
        mock_query = Mock()
        mock_query.execution_options = Mock()
        
        optimized_query = query_optimizer.optimize_query(mock_query)
        
        # Verificar que se aplicó el timeout
        mock_query.execution_options.assert_called_once_with(timeout=10)
    
    def test_query_optimizer_eager_loading(self, query_optimizer):
        """Verificar eager loading"""
        # Mock de query
        mock_query = Mock()
        mock_query.options = Mock()
        
        relationships = ["usuario", "clase"]
        optimized_query = query_optimizer.add_eager_loading(mock_query, relationships)
        
        # Verificar que se agregaron las opciones
        assert mock_query.options.call_count == 2
    
    def test_query_optimizer_selective_loading(self, query_optimizer):
        """Verificar selective loading"""
        # Mock de query
        mock_query = Mock()
        mock_query.options = Mock()
        
        relationships = ["usuario", "clase"]
        optimized_query = query_optimizer.add_selective_loading(mock_query, relationships)
        
        # Verificar que se agregaron las opciones
        assert mock_query.options.call_count == 2
    
    def test_query_optimizer_monitoring(self, query_optimizer):
        """Verificar monitoreo de consultas"""
        # Función de consulta mock
        def mock_query_func():
            time.sleep(0.1)  # Simular consulta lenta
            return "result"
        
        # Aplicar decorador de monitoreo
        monitored_func = query_optimizer.monitor_query("test_query", mock_query_func)
        
        # Ejecutar función monitoreada
        result = monitored_func()
        assert result == "result"
        
        # Verificar estadísticas
        stats = query_optimizer.get_query_stats()
        assert "test_query" in stats
        assert stats["test_query"]["count"] == 1
        assert stats["test_query"]["avg_time"] > 0
    
    def test_query_optimizer_slow_query_detection(self, query_optimizer):
        """Verificar detección de consultas lentas"""
        # Función de consulta muy lenta
        def slow_query_func():
            time.sleep(0.6)  # Más del threshold de 0.5
            return "slow_result"
        
        # Aplicar decorador de monitoreo
        monitored_func = query_optimizer.monitor_query("slow_query", slow_query_func)
        
        # Ejecutar función monitoreada
        with patch('logging.Logger.warning') as mock_warning:
            result = monitored_func()
            assert result == "slow_result"
            
            # Verificar que se registró la advertencia
            mock_warning.assert_called_once()
    
    def test_query_optimizer_error_handling(self, query_optimizer):
        """Verificar manejo de errores en consultas"""
        # Función que genera error
        def error_query_func():
            raise Exception("Database error")
        
        # Aplicar decorador de monitoreo
        monitored_func = query_optimizer.monitor_query("error_query", error_query_func)
        
        # Ejecutar función monitoreada
        with patch('logging.Logger.error') as mock_error:
            with pytest.raises(Exception):
                monitored_func()
            
            # Verificar que se registró el error
            mock_error.assert_called_once()

class TestResponseOptimizer:
    """Tests para el optimizador de respuestas"""
    
    def test_response_optimizer_initialization(self, response_optimizer):
        """Verificar inicialización del optimizador"""
        assert response_optimizer.config.ENABLE_ETAGS is True
        assert response_optimizer.config.RESPONSE_CACHE_TTL == 60
    
    def test_response_optimizer_etag_generation(self, response_optimizer):
        """Verificar generación de ETags"""
        data = {"test": "data", "number": 123}
        etag = response_optimizer._generate_etag(data)
        
        assert len(etag) == 32  # MD5 hash
        assert isinstance(etag, str)
        
        # Verificar que el mismo dato genera el mismo ETag
        etag2 = response_optimizer._generate_etag(data)
        assert etag == etag2
    
    def test_response_optimizer_etag_different_data(self, response_optimizer):
        """Verificar que datos diferentes generan ETags diferentes"""
        data1 = {"test": "data1"}
        data2 = {"test": "data2"}
        
        etag1 = response_optimizer._generate_etag(data1)
        etag2 = response_optimizer._generate_etag(data2)
        
        assert etag1 != etag2
    
    def test_response_optimizer_headers(self, response_optimizer, mock_response, mock_request):
        """Verificar agregado de headers de optimización"""
        data = {"test": "data"}
        
        optimized_response = response_optimizer.optimize_response(mock_response, data, mock_request)
        
        # Verificar headers agregados
        assert "ETag" in optimized_response.headers
        assert "Cache-Control" in optimized_response.headers
        assert "public, max-age=60" in optimized_response.headers["Cache-Control"]
    
    def test_response_optimizer_304_response(self, response_optimizer, mock_response, mock_request):
        """Verificar respuesta 304 para ETags coincidentes"""
        data = {"test": "data"}
        etag = response_optimizer._generate_etag(data)
        
        # Configurar request con If-None-Match
        mock_request.headers = {"If-None-Match": etag}
        
        optimized_response = response_optimizer.optimize_response(mock_response, data, mock_request)
        
        # Verificar respuesta 304
        assert optimized_response.status_code == 304
    
    def test_response_optimizer_pagination(self, response_optimizer):
        """Verificar paginación de respuestas"""
        data = [f"item_{i}" for i in range(100)]
        
        # Primera página
        result = response_optimizer.paginate_response(data, page=1, size=20)
        
        assert len(result["data"]) == 20
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["total"] == 100
        assert result["pagination"]["pages"] == 5
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is False
        
        # Segunda página
        result = response_optimizer.paginate_response(data, page=2, size=20)
        
        assert len(result["data"]) == 20
        assert result["pagination"]["page"] == 2
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is True
        
        # Última página
        result = response_optimizer.paginate_response(data, page=5, size=20)
        
        assert len(result["data"]) == 20
        assert result["pagination"]["has_next"] is False
        assert result["pagination"]["has_prev"] is True

class TestPerformanceMonitor:
    """Tests para el monitor de performance"""
    
    def test_performance_monitor_initialization(self, performance_monitor):
        """Verificar inicialización del monitor"""
        assert performance_monitor.config.PERFORMANCE_MONITORING is True
        assert len(performance_monitor.metrics) == 0
    
    def test_performance_monitor_record_metric(self, performance_monitor):
        """Verificar registro de métricas"""
        performance_monitor.record_metric("test_metric", 1.5, {"tag": "value"})
        
        assert "test_metric" in performance_monitor.metrics
        assert len(performance_monitor.metrics["test_metric"]) == 1
        
        metric = performance_monitor.metrics["test_metric"][0]
        assert metric["value"] == 1.5
        assert metric["tags"]["tag"] == "value"
    
    def test_performance_monitor_metric_limit(self, performance_monitor):
        """Verificar límite de métricas"""
        # Agregar más de 1000 métricas
        for i in range(1100):
            performance_monitor.record_metric("test_metric", i)
        
        # Verificar que se mantiene el límite
        assert len(performance_monitor.metrics["test_metric"]) == 1000
        
        # Verificar que se mantienen las más recientes
        latest_metric = performance_monitor.metrics["test_metric"][-1]
        assert latest_metric["value"] == 1099
    
    def test_performance_monitor_sync_decorator(self, performance_monitor):
        """Verificar decorador síncrono"""
        @performance_monitor.measure_time("test_operation")
        def test_function():
            time.sleep(0.1)
            return "result"
        
        result = test_function()
        assert result == "result"
        
        # Verificar que se registró la métrica
        assert "test_operation_duration" in performance_monitor.metrics
    
    @pytest.mark.asyncio
    async def test_performance_monitor_async_decorator(self, performance_monitor):
        """Verificar decorador asíncrono"""
        @performance_monitor.measure_async_time("async_test_operation")
        async def async_test_function():
            await asyncio.sleep(0.1)
            return "async_result"
        
        result = await async_test_function()
        assert result == "async_result"
        
        # Verificar que se registró la métrica
        assert "async_test_operation_duration" in performance_monitor.metrics
    
    def test_performance_monitor_get_metrics(self, performance_monitor):
        """Verificar obtención de métricas"""
        # Agregar algunas métricas
        performance_monitor.record_metric("metric1", 1.0)
        performance_monitor.record_metric("metric1", 2.0)
        performance_monitor.record_metric("metric2", 3.0)
        
        # Obtener métricas específicas
        metrics = performance_monitor.get_metrics("metric1")
        assert metrics["metric"] == "metric1"
        assert metrics["count"] == 2
        assert metrics["avg"] == 1.5
        
        # Obtener todas las métricas
        all_metrics = performance_monitor.get_metrics()
        assert "metric1" in all_metrics
        assert "metric2" in all_metrics
    
    def test_performance_monitor_system_stats(self, performance_monitor):
        """Verificar estadísticas del sistema"""
        # Agregar algunas métricas
        performance_monitor.record_metric("test_metric", 1.0)
        performance_monitor.record_metric("test_metric", 2.0)
        
        stats = performance_monitor.get_system_stats()
        
        assert "uptime" in stats
        assert "uptime_formatted" in stats
        assert stats["total_metrics"] == 2
        assert stats["metric_types"] == 1

class TestPerformanceMiddleware:
    """Tests para el middleware de performance"""
    
    @pytest.mark.asyncio
    async def test_performance_middleware_initialization(self, performance_config, performance_monitor):
        """Verificar inicialización del middleware"""
        middleware = PerformanceMiddleware(performance_config, performance_monitor)
        assert middleware.config == performance_config
        assert middleware.monitor == performance_monitor
    
    @pytest.mark.asyncio
    async def test_performance_middleware_request_processing(self, performance_config, performance_monitor, mock_request):
        """Verificar procesamiento de peticiones"""
        middleware = PerformanceMiddleware(performance_config, performance_monitor)
        
        # Mock de la función call_next
        async def mock_call_next(request):
            response = Mock(spec=Response)
            response.status_code = 200
            response.headers = {}
            return response
        
        response = await middleware(mock_request, mock_call_next)
        
        # Verificar que se agregaron headers de timing
        assert "X-Processing-Time" in response.headers
        assert "X-Request-ID" in response.headers
        
        # Verificar que se registró la métrica
        assert "request_duration" in performance_monitor.metrics

class TestPerformanceUtilities:
    """Tests para utilidades de performance"""
    
    @pytest.mark.asyncio
    async def test_cache_result_decorator(self):
        """Verificar decorador de caché de resultados"""
        call_count = 0
        
        @cache_result(ttl=60, key_prefix="test")
        async def cached_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"
        
        # Primera llamada
        result1 = await cached_function("test_param")
        assert result1 == "result_test_param"
        assert call_count == 1
        
        # Segunda llamada (debería usar caché)
        result2 = await cached_function("test_param")
        assert result2 == "result_test_param"
        assert call_count == 1  # No debería incrementar
    
    def test_batch_process(self):
        """Verificar procesamiento por lotes"""
        items = list(range(250))
        batches = list(batch_process(items, batch_size=100))
        
        assert len(batches) == 3
        assert len(batches[0]) == 100
        assert len(batches[1]) == 100
        assert len(batches[2]) == 50
    
    @pytest.mark.asyncio
    async def test_performance_context(self, performance_monitor):
        """Verificar context manager de performance"""
        async with performance_context("test_context", performance_monitor):
            await asyncio.sleep(0.1)
        
        # Verificar que se registró la métrica
        assert "test_context_duration" in performance_monitor.metrics

class TestPerformanceIntegration:
    """Tests de integración de performance"""
    
    def test_performance_integration_with_fastapi(self):
        """Verificar integración con FastAPI"""
        client = TestClient(app)
        
        # Test de endpoint básico
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Debe responder en menos de 1 segundo
    
    @pytest.mark.asyncio
    async def test_cache_integration(self, cache_instance):
        """Verificar integración del caché"""
        # Test de operaciones básicas
        await cache_instance.set("integration_test", {"data": "test"})
        result = await cache_instance.get("integration_test")
        
        assert result == {"data": "test"}
        
        # Test de eliminación
        await cache_instance.delete("integration_test")
        result = await cache_instance.get("integration_test")
        assert result is None
    
    def test_query_optimization_integration(self, query_optimizer):
        """Verificar integración de optimización de consultas"""
        # Test de monitoreo de consultas
        def test_query():
            time.sleep(0.1)
            return "query_result"
        
        monitored_query = query_optimizer.monitor_query("integration_query", test_query)
        result = monitored_query()
        
        assert result == "query_result"
        
        # Verificar estadísticas
        stats = query_optimizer.get_query_stats()
        assert "integration_query" in stats
        assert stats["integration_query"]["count"] == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 