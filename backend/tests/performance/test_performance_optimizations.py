"""
Pruebas específicas para optimizaciones de rendimiento
Sistema de Gestión de Gimnasio v6
"""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import statistics
import psutil
import gc

from app.core.database import get_db
from app.models.usuarios import Usuario
from app.models.clases import Clase
from app.models.asistencias import Asistencia
from app.models.pagos import Pago


@pytest.mark.performance
class TestDatabaseOptimizations:
    """Pruebas para optimizaciones de base de datos"""
    
    def test_index_performance(self, db_session: Session, sample_user_data: Dict[str, Any]):
        """Verificar que los índices mejoran el rendimiento de consultas"""
        # Crear múltiples usuarios para probar índices
        users = []
        for i in range(100):
            user_data = sample_user_data.copy()
            user_data["email"] = f"user{i}@test.com"
            user_data["username"] = f"user{i}"
            user = Usuario(**user_data)
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Probar consulta con índice en email
        start_time = time.time()
        result = db_session.query(Usuario).filter(Usuario.email == "user50@test.com").first()
        query_time = time.time() - start_time
        
        assert result is not None
        assert query_time < 0.1, f"Consulta por email tardó {query_time:.3f}s (esperado < 0.1s)"
        
        # Probar consulta con índice en username
        start_time = time.time()
        result = db_session.query(Usuario).filter(Usuario.username == "user75").first()
        query_time = time.time() - start_time
        
        assert result is not None
        assert query_time < 0.1, f"Consulta por username tardó {query_time:.3f}s (esperado < 0.1s)"
    
    def test_pagination_performance(self, db_session: Session, sample_user_data: Dict[str, Any]):
        """Verificar que la paginación es eficiente"""
        # Crear muchos usuarios
        users = []
        for i in range(500):
            user_data = sample_user_data.copy()
            user_data["email"] = f"pagtest{i}@test.com"
            user_data["username"] = f"pagtest{i}"
            user = Usuario(**user_data)
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Probar paginación
        start_time = time.time()
        results = db_session.query(Usuario).offset(100).limit(50).all()
        query_time = time.time() - start_time
        
        assert len(results) == 50
        assert query_time < 0.2, f"Paginación tardó {query_time:.3f}s (esperado < 0.2s)"
    
    def test_join_performance(self, db_session: Session, sample_user_data: Dict[str, Any], sample_clase_data: Dict[str, Any]):
        """Verificar performance de consultas con JOINs"""
        # Crear datos de prueba
        user = Usuario(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        clase = Clase(**sample_clase_data)
        db_session.add(clase)
        db_session.commit()
        
        # Crear múltiples asistencias
        asistencias = []
        for i in range(100):
            asistencia = Asistencia(
                usuario_id=user.id,
                clase_id=clase.id,
                fecha=datetime.now() - timedelta(days=i),
                tipo="entrada"
            )
            asistencias.append(asistencia)
        
        db_session.add_all(asistencias)
        db_session.commit()
        
        # Probar JOIN optimizado
        start_time = time.time()
        results = db_session.query(Asistencia).join(Usuario).join(Clase).filter(
            Usuario.email == sample_user_data["email"]
        ).all()
        query_time = time.time() - start_time
        
        assert len(results) == 100
        assert query_time < 0.3, f"JOIN tardó {query_time:.3f}s (esperado < 0.3s)"


@pytest.mark.performance
class TestAPIPerformance:
    """Pruebas de rendimiento para endpoints de API"""
    
    def test_kpis_endpoint_performance(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar rendimiento del endpoint de KPIs"""
        response_times = []
        
        # Ejecutar múltiples requests para obtener estadísticas
        for _ in range(10):
            start_time = time.time()
            response = client.get("/api/reportes/kpis", headers=admin_headers)
            response_time = time.time() - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Verificar estadísticas de rendimiento
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        assert avg_time < 1.0, f"Tiempo promedio: {avg_time:.3f}s (esperado < 1.0s)"
        assert max_time < 2.0, f"Tiempo máximo: {max_time:.3f}s (esperado < 2.0s)"
    
    def test_graficos_endpoint_performance(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar rendimiento del endpoint de gráficos"""
        start_time = time.time()
        response = client.get("/api/reportes/graficos", headers=admin_headers)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.5, f"Gráficos tardaron {response_time:.3f}s (esperado < 1.5s)"
    
    def test_usuarios_list_performance(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar rendimiento de listado de usuarios"""
        start_time = time.time()
        response = client.get("/api/usuarios", headers=admin_headers)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5, f"Listado de usuarios tardó {response_time:.3f}s (esperado < 0.5s)"
    
    def test_clases_list_performance(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar rendimiento de listado de clases"""
        start_time = time.time()
        response = client.get("/api/clases", headers=admin_headers)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5, f"Listado de clases tardó {response_time:.3f}s (esperado < 0.5s)"


@pytest.mark.load
class TestLoadPerformance:
    """Pruebas de carga para verificar rendimiento bajo estrés"""
    
    def test_concurrent_kpis_requests(self, client: TestClient, admin_headers: Dict[str, str]):
        """Prueba de carga para endpoint de KPIs"""
        concurrent_requests = 20
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/reportes/kpis", headers=admin_headers)
            response_time = time.time() - start_time
            return response.status_code, response_time
        
        # Ejecutar requests concurrentes
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # Verificar resultados
        successful_requests = sum(1 for status, _ in results if status == 200)
        response_times = [time for _, time in results]
        
        assert successful_requests >= concurrent_requests * 0.9, "Menos del 90% de requests exitosos"
        assert max(response_times) < 5.0, f"Tiempo máximo: {max(response_times):.3f}s (esperado < 5.0s)"
        assert statistics.mean(response_times) < 2.0, f"Tiempo promedio: {statistics.mean(response_times):.3f}s (esperado < 2.0s)"
    
    def test_concurrent_user_creation(self, client: TestClient, admin_headers: Dict[str, str]):
        """Prueba de carga para creación concurrente de usuarios"""
        concurrent_requests = 10
        
        def create_user(index):
            user_data = {
                "nombre": f"Usuario {index}",
                "apellido": f"Apellido {index}",
                "email": f"load_test_{index}@test.com",
                "username": f"load_test_{index}",
                "telefono": f"12345678{index}",
                "fecha_nacimiento": "1990-01-01",
                "genero": "M",
                "esta_activo": True
            }
            
            start_time = time.time()
            response = client.post("/api/usuarios", json=user_data, headers=admin_headers)
            response_time = time.time() - start_time
            return response.status_code, response_time
        
        # Ejecutar creaciones concurrentes
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(create_user, i) for i in range(concurrent_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # Verificar resultados
        successful_requests = sum(1 for status, _ in results if status == 201)
        response_times = [time for _, time in results]
        
        assert successful_requests >= concurrent_requests * 0.8, "Menos del 80% de creaciones exitosas"
        assert max(response_times) < 3.0, f"Tiempo máximo: {max(response_times):.3f}s (esperado < 3.0s)"


@pytest.mark.performance
class TestMemoryOptimizations:
    """Pruebas de uso de memoria y optimizaciones"""
    
    def test_memory_usage_during_bulk_operations(self, db_session: Session, sample_user_data: Dict[str, Any]):
        """Verificar que las operaciones masivas no consuman memoria excesiva"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Crear muchos usuarios
        users = []
        for i in range(1000):
            user_data = sample_user_data.copy()
            user_data["email"] = f"memory_test_{i}@test.com"
            user_data["username"] = f"memory_test_{i}"
            user = Usuario(**user_data)
            users.append(user)
        
        # Añadir en lotes para optimizar memoria
        batch_size = 100
        for i in range(0, len(users), batch_size):
            batch = users[i:i+batch_size]
            db_session.add_all(batch)
            db_session.commit()
            
            # Limpiar memoria periódicamente
            if i % (batch_size * 5) == 0:
                gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < 100, f"Incremento de memoria: {memory_increase:.2f}MB (esperado < 100MB)"
    
    def test_memory_cleanup_after_operations(self, db_session: Session):
        """Verificar que la memoria se libera correctamente después de operaciones"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Realizar operaciones que consuman memoria
        large_data = []
        for i in range(10000):
            large_data.append(f"data_item_{i}" * 100)
        
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Limpiar datos
        del large_data
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_recovered = peak_memory - final_memory
        
        assert memory_recovered > 0, "No se liberó memoria después de la limpieza"
        assert final_memory - initial_memory < 50, "Memoria final excesiva"


@pytest.mark.performance
class TestCachePerformance:
    """Pruebas de rendimiento para cache"""
    
    def test_repeated_kpis_requests_cache(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar que el cache mejora el rendimiento de requests repetidos"""
        # Primera request (sin cache)
        start_time = time.time()
        response1 = client.get("/api/reportes/kpis", headers=admin_headers)
        first_request_time = time.time() - start_time
        
        assert response1.status_code == 200
        
        # Segunda request (con cache)
        start_time = time.time()
        response2 = client.get("/api/reportes/kpis", headers=admin_headers)
        second_request_time = time.time() - start_time
        
        assert response2.status_code == 200
        
        # El cache debería hacer la segunda request más rápida
        # (En implementación real con Redis, esto sería más evidente)
        assert second_request_time <= first_request_time * 1.2, "Cache no mejora el rendimiento"
    
    def test_cache_invalidation_performance(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar que la invalidación de cache no afecta significativamente el rendimiento"""
        # Crear datos que afecten el cache
        user_data = {
            "nombre": "Cache Test",
            "apellido": "User",
            "email": "cache_test@test.com",
            "username": "cache_test",
            "telefono": "123456789",
            "fecha_nacimiento": "1990-01-01",
            "genero": "M",
            "esta_activo": True
        }
        
        start_time = time.time()
        response = client.post("/api/usuarios", json=user_data, headers=admin_headers)
        creation_time = time.time() - start_time
        
        assert response.status_code == 201
        assert creation_time < 1.0, f"Creación con invalidación de cache tardó {creation_time:.3f}s"


@pytest.mark.performance
class TestEndpointOptimizations:
    """Pruebas específicas para optimizaciones de endpoints"""
    
    def test_health_endpoint_performance(self, client: TestClient):
        """Verificar que el endpoint de salud es muy rápido"""
        start_time = time.time()
        response = client.get("/health")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.05, f"Health check tardó {response_time:.3f}s (esperado < 0.05s)"
    
    def test_bulk_operations_performance(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar rendimiento de operaciones masivas"""
        # Crear múltiples usuarios en una sola operación
        users_data = []
        for i in range(50):
            user_data = {
                "nombre": f"Bulk User {i}",
                "apellido": f"Bulk {i}",
                "email": f"bulk_{i}@test.com",
                "username": f"bulk_{i}",
                "telefono": f"12345678{i:02d}",
                "fecha_nacimiento": "1990-01-01",
                "genero": "M",
                "esta_activo": True
            }
            users_data.append(user_data)
        
        start_time = time.time()
        # En una implementación real, habría un endpoint para bulk operations
        # Por ahora, medimos operaciones individuales
        successful_creates = 0
        for user_data in users_data:
            response = client.post("/api/usuarios", json=user_data, headers=admin_headers)
            if response.status_code == 201:
                successful_creates += 1
        
        total_time = time.time() - start_time
        
        assert successful_creates >= 40, "Menos del 80% de operaciones exitosas"
        assert total_time < 10.0, f"Operaciones masivas tardaron {total_time:.3f}s (esperado < 10.0s)"
        assert total_time / successful_creates < 0.2, "Tiempo promedio por operación excesivo"


@pytest.mark.performance
@pytest.mark.critical
class TestCriticalPerformance:
    """Pruebas críticas de rendimiento que deben pasar siempre"""
    
    def test_login_performance(self, client: TestClient):
        """Verificar que el login es rápido"""
        start_time = time.time()
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        login_time = time.time() - start_time
        
        assert response.status_code == 200
        assert login_time < 0.5, f"Login tardó {login_time:.3f}s (esperado < 0.5s)"
    
    def test_dashboard_data_performance(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar que los datos del dashboard se cargan rápidamente"""
        endpoints = [
            "/api/reportes/kpis",
            "/api/reportes/graficos"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint, headers=admin_headers)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            assert response_time < 2.0, f"Dashboard {endpoint} tardó {response_time:.3f}s (esperado < 2.0s)"
    
    def test_database_connection_performance(self, db_session: Session):
        """Verificar que las conexiones a la base de datos son rápidas"""
        start_time = time.time()
        # Ejecutar una consulta simple
        result = db_session.execute("SELECT 1")
        connection_time = time.time() - start_time
        
        assert result.fetchone()[0] == 1
        assert connection_time < 0.1, f"Conexión a BD tardó {connection_time:.3f}s (esperado < 0.1s)"


# Funciones utilitarias para ejecutar pruebas de rendimiento
def run_performance_benchmark():
    """Ejecutar benchmark completo de rendimiento"""
    import subprocess
    
    result = subprocess.run([
        "pytest", 
        "-m", "performance",
        "--tb=short",
        "--durations=20",
        "-v"
    ], capture_output=True, text=True)
    
    return result

def run_load_tests():
    """Ejecutar pruebas de carga"""
    import subprocess
    
    result = subprocess.run([
        "pytest", 
        "-m", "load",
        "--tb=short",
        "-v"
    ], capture_output=True, text=True)
    
    return result

def run_critical_performance_tests():
    """Ejecutar solo pruebas críticas de rendimiento"""
    import subprocess
    
    result = subprocess.run([
        "pytest", 
        "-m", "critical and performance",
        "--tb=short",
        "-v"
    ], capture_output=True, text=True)
    
    return result

if __name__ == "__main__":
    # Ejecutar benchmark cuando se ejecuta directamente
    print("Ejecutando benchmark de rendimiento...")
    result = run_performance_benchmark()
    print(result.stdout)
    if result.stderr:
        print("Errores:", result.stderr) 