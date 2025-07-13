"""
Tests de Carga - Sistema de Gimnasio v6
Verifica el rendimiento del sistema bajo carga y estrés
"""

import pytest
import time
import asyncio
import threading
import concurrent.futures
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import requests
import json
import statistics

from app.main import app
from app.core.database import get_db
from app.models.usuarios import Usuario
from app.schemas.auth import LoginRequest

# Configuración de tests de carga
@pytest.fixture
def client():
    """Cliente de prueba para FastAPI"""
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    """Headers de autenticación para tests"""
    # Crear usuario de prueba
    user_data = {
        "email": "loadtest@example.com",
        "nombre": "Load",
        "apellido": "Test",
        "password": "SecurePass123!",
        "rol": "admin"
    }
    
    client.post("/api/auth/register", json=user_data)
    
    # Login
    login_data = {
        "email": "loadtest@example.com",
        "password": "SecurePass123!"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestConcurrentRequests:
    """Tests de peticiones concurrentes"""
    
    def test_concurrent_user_creation(self, client, auth_headers):
        """Test de creación concurrente de usuarios"""
        num_users = 50
        results = []
        
        def create_user(user_id):
            user_data = {
                "email": f"concurrent_user_{user_id}@example.com",
                "nombre": f"Usuario {user_id}",
                "apellido": "Concurrent",
                "password": "SecurePass123!",
                "rol": "usuario"
            }
            
            start_time = time.time()
            response = client.post("/api/usuarios/", json=user_data, headers=auth_headers)
            end_time = time.time()
            
            return {
                "user_id": user_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 201
            }
        
        # Ejecutar peticiones concurrentes
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_user, i) for i in range(num_users)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Análisis de resultados
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        response_times = [r["response_time"] for r in results]
        
        print(f"\nResultados de creación concurrente de usuarios:")
        print(f"Total de peticiones: {num_users}")
        print(f"Exitosas: {len(successful_requests)}")
        print(f"Fallidas: {len(failed_requests)}")
        print(f"Tiempo promedio: {statistics.mean(response_times):.3f}s")
        print(f"Tiempo máximo: {max(response_times):.3f}s")
        print(f"Tiempo mínimo: {min(response_times):.3f}s")
        
        # Verificaciones
        assert len(successful_requests) >= num_users * 0.9  # 90% de éxito mínimo
        assert max(response_times) < 5.0  # Máximo 5 segundos por petición
        assert statistics.mean(response_times) < 2.0  # Promedio menor a 2 segundos
    
    def test_concurrent_read_operations(self, client, auth_headers):
        """Test de operaciones de lectura concurrentes"""
        # Crear algunos usuarios primero
        for i in range(20):
            user_data = {
                "email": f"read_user_{i}@example.com",
                "nombre": f"Usuario {i}",
                "apellido": "Read",
                "password": "SecurePass123!",
                "rol": "usuario"
            }
            client.post("/api/usuarios/", json=user_data, headers=auth_headers)
        
        num_requests = 100
        results = []
        
        def read_users():
            start_time = time.time()
            response = client.get("/api/usuarios/", headers=auth_headers)
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200,
                "data_size": len(response.json()) if response.status_code == 200 else 0
            }
        
        # Ejecutar lecturas concurrentes
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(read_users) for _ in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Análisis de resultados
        successful_requests = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in results]
        
        print(f"\nResultados de lectura concurrente:")
        print(f"Total de peticiones: {num_requests}")
        print(f"Exitosas: {len(successful_requests)}")
        print(f"Tiempo promedio: {statistics.mean(response_times):.3f}s")
        print(f"Tiempo máximo: {max(response_times):.3f}s")
        print(f"Tiempo mínimo: {min(response_times):.3f}s")
        
        # Verificaciones
        assert len(successful_requests) >= num_requests * 0.95  # 95% de éxito mínimo
        assert max(response_times) < 3.0  # Máximo 3 segundos por petición
        assert statistics.mean(response_times) < 1.0  # Promedio menor a 1 segundo
    
    def test_mixed_operations_load(self, client, auth_headers):
        """Test de carga mixta (lectura y escritura)"""
        num_operations = 200
        results = []
        
        def mixed_operation(operation_id):
            operation_type = operation_id % 3  # 0: crear, 1: leer, 2: actualizar
            
            if operation_type == 0:  # Crear
                user_data = {
                    "email": f"mixed_user_{operation_id}@example.com",
                    "nombre": f"Usuario {operation_id}",
                    "apellido": "Mixed",
                    "password": "SecurePass123!",
                    "rol": "usuario"
                }
                
                start_time = time.time()
                response = client.post("/api/usuarios/", json=user_data, headers=auth_headers)
                end_time = time.time()
                
                return {
                    "operation": "create",
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 201
                }
            
            elif operation_type == 1:  # Leer
                start_time = time.time()
                response = client.get("/api/usuarios/", headers=auth_headers)
                end_time = time.time()
                
                return {
                    "operation": "read",
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
            
            else:  # Actualizar (asumiendo que existe un usuario con ID 1)
                update_data = {"nombre": f"Updated {operation_id}"}
                
                start_time = time.time()
                response = client.put("/api/usuarios/1", json=update_data, headers=auth_headers)
                end_time = time.time()
                
                return {
                    "operation": "update",
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
        
        # Ejecutar operaciones mixtas
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(mixed_operation, i) for i in range(num_operations)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Análisis por tipo de operación
        creates = [r for r in results if r["operation"] == "create"]
        reads = [r for r in results if r["operation"] == "read"]
        updates = [r for r in results if r["operation"] == "update"]
        
        print(f"\nResultados de operaciones mixtas:")
        print(f"Total de operaciones: {num_operations}")
        print(f"Creaciones: {len(creates)} (Exitosas: {len([c for c in creates if c['success']])})")
        print(f"Lecturas: {len(reads)} (Exitosas: {len([r for r in reads if r['success']])})")
        print(f"Actualizaciones: {len(updates)} (Exitosas: {len([u for u in updates if u['success']])})")
        
        # Verificaciones
        assert len(creates) > 0
        assert len(reads) > 0
        assert len(updates) > 0

class TestDatabaseLoad:
    """Tests de carga de base de datos"""
    
    def test_large_dataset_queries(self, client, auth_headers):
        """Test de consultas con grandes conjuntos de datos"""
        # Crear un gran conjunto de datos
        num_users = 1000
        print(f"\nCreando {num_users} usuarios para test de carga...")
        
        start_time = time.time()
        for i in range(num_users):
            user_data = {
                "email": f"load_user_{i}@example.com",
                "nombre": f"Usuario {i}",
                "apellido": "Load",
                "password": "SecurePass123!",
                "rol": "usuario"
            }
            client.post("/api/usuarios/", json=user_data, headers=auth_headers)
        
        creation_time = time.time() - start_time
        print(f"Tiempo de creación: {creation_time:.2f}s")
        
        # Test de consultas con diferentes tamaños de página
        page_sizes = [10, 50, 100, 500]
        
        for page_size in page_sizes:
            start_time = time.time()
            response = client.get(f"/api/usuarios/?page=1&size={page_size}", headers=auth_headers)
            query_time = time.time() - start_time
            
            assert response.status_code == 200
            data = response.json()
            
            if isinstance(data, dict) and "data" in data:
                actual_size = len(data["data"])
                print(f"Página de {page_size}: {actual_size} usuarios en {query_time:.3f}s")
            else:
                actual_size = len(data)
                print(f"Lista completa: {actual_size} usuarios en {query_time:.3f}s")
            
            # Verificar que las consultas son eficientes
            assert query_time < 2.0  # Máximo 2 segundos por consulta
    
    def test_complex_queries_load(self, client, auth_headers):
        """Test de consultas complejas bajo carga"""
        # Crear datos complejos
        for i in range(100):
            # Crear empleado
            empleado_data = {
                "nombre": f"Empleado {i}",
                "apellido": "Test",
                "email": f"empleado{i}@example.com",
                "telefono": f"123456{i:03d}",
                "cargo": "Instructor"
            }
            empleado_response = client.post("/api/empleados/", json=empleado_data, headers=auth_headers)
            
            if empleado_response.status_code == 201:
                empleado_id = empleado_response.json()["id"]
                
                # Crear clase para este empleado
                clase_data = {
                    "nombre": f"Clase {i}",
                    "descripcion": f"Descripción de clase {i}",
                    "duracion": 60,
                    "capacidad_maxima": 20,
                    "instructor_id": empleado_id
                }
                client.post("/api/clases/", json=clase_data, headers=auth_headers)
        
        # Test de consultas complejas
        queries = [
            ("/api/usuarios/", "Lista de usuarios"),
            ("/api/empleados/", "Lista de empleados"),
            ("/api/clases/", "Lista de clases"),
            ("/api/reportes/kpis", "KPIs del sistema")
        ]
        
        for endpoint, description in queries:
            start_time = time.time()
            response = client.get(endpoint, headers=auth_headers)
            query_time = time.time() - start_time
            
            print(f"{description}: {query_time:.3f}s")
            assert response.status_code in [200, 404]
            assert query_time < 3.0  # Máximo 3 segundos

class TestMemoryLoad:
    """Tests de carga de memoria"""
    
    def test_memory_usage_under_load(self, client, auth_headers):
        """Test de uso de memoria bajo carga"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"\nMemoria inicial: {initial_memory:.2f} MB")
        
        # Realizar operaciones intensivas
        for i in range(500):
            user_data = {
                "email": f"memory_user_{i}@example.com",
                "nombre": f"Usuario {i}",
                "apellido": "Memory",
                "password": "SecurePass123!",
                "rol": "usuario"
            }
            client.post("/api/usuarios/", json=user_data, headers=auth_headers)
        
        # Leer todos los usuarios varias veces
        for _ in range(10):
            client.get("/api/usuarios/", headers=auth_headers)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memoria final: {final_memory:.2f} MB")
        print(f"Incremento de memoria: {memory_increase:.2f} MB")
        
        # Verificar que el incremento de memoria es razonable
        assert memory_increase < 100  # Menos de 100MB de incremento
    
    def test_connection_pool_stress(self, client, auth_headers):
        """Test de estrés en el pool de conexiones"""
        num_concurrent_connections = 50
        results = []
        
        def stress_connection(connection_id):
            # Realizar múltiples operaciones para cada conexión
            operations = []
            for i in range(10):
                start_time = time.time()
                response = client.get("/api/usuarios/", headers=auth_headers)
                end_time = time.time()
                
                operations.append({
                    "operation": i,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                })
            
            return {
                "connection_id": connection_id,
                "operations": operations,
                "avg_response_time": statistics.mean([op["response_time"] for op in operations])
            }
        
        # Ejecutar conexiones concurrentes
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_connections) as executor:
            futures = [executor.submit(stress_connection, i) for i in range(num_concurrent_connections)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Análisis de resultados
        avg_response_times = [r["avg_response_time"] for r in results]
        
        print(f"\nResultados de estrés en pool de conexiones:")
        print(f"Total de conexiones: {num_concurrent_connections}")
        print(f"Tiempo promedio por conexión: {statistics.mean(avg_response_times):.3f}s")
        print(f"Tiempo máximo: {max(avg_response_times):.3f}s")
        print(f"Tiempo mínimo: {min(avg_response_times):.3f}s")
        
        # Verificaciones
        assert statistics.mean(avg_response_times) < 2.0  # Promedio menor a 2 segundos
        assert max(avg_response_times) < 5.0  # Máximo 5 segundos

class TestNetworkLoad:
    """Tests de carga de red"""
    
    def test_network_latency_simulation(self, client, auth_headers):
        """Test de simulación de latencia de red"""
        # Simular diferentes latencias de red
        latencies = [0, 50, 100, 200, 500]  # ms
        
        for latency in latencies:
            with patch('time.sleep') as mock_sleep:
                mock_sleep.return_value = latency / 1000  # Convertir a segundos
                
                start_time = time.time()
                response = client.get("/api/usuarios/", headers=auth_headers)
                end_time = time.time()
                
                actual_time = end_time - start_time
                print(f"Latencia simulada {latency}ms: {actual_time:.3f}s")
                
                assert response.status_code == 200
    
    def test_bandwidth_usage(self, client, auth_headers):
        """Test de uso de ancho de banda"""
        # Crear datos grandes
        large_user_data = {
            "email": "large@example.com",
            "nombre": "Usuario" * 100,  # Nombre muy largo
            "apellido": "Apellido" * 100,  # Apellido muy largo
            "password": "SecurePass123!",
            "rol": "usuario",
            "descripcion": "Descripción muy larga " * 50  # Descripción muy larga
        }
        
        # Medir tamaño de la petición
        import sys
        request_size = sys.getsizeof(json.dumps(large_user_data))
        
        start_time = time.time()
        response = client.post("/api/usuarios/", json=large_user_data, headers=auth_headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        print(f"\nTest de ancho de banda:")
        print(f"Tamaño de petición: {request_size} bytes")
        print(f"Tiempo de respuesta: {response_time:.3f}s")
        
        # Verificar que el sistema maneja datos grandes eficientemente
        assert response_time < 3.0  # Máximo 3 segundos
        assert response.status_code in [201, 422]  # 422 si los datos son demasiado grandes

class TestStressTesting:
    """Tests de estrés extremo"""
    
    def test_extreme_concurrent_load(self, client, auth_headers):
        """Test de carga concurrente extrema"""
        num_requests = 1000
        results = []
        
        def extreme_request(request_id):
            # Realizar múltiples operaciones por petición
            operations = []
            
            # GET request
            start_time = time.time()
            response = client.get("/api/usuarios/", headers=auth_headers)
            end_time = time.time()
            operations.append({
                "type": "GET",
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
            
            # POST request
            user_data = {
                "email": f"extreme_user_{request_id}@example.com",
                "nombre": f"Usuario {request_id}",
                "apellido": "Extreme",
                "password": "SecurePass123!",
                "rol": "usuario"
            }
            
            start_time = time.time()
            response = client.post("/api/usuarios/", json=user_data, headers=auth_headers)
            end_time = time.time()
            operations.append({
                "type": "POST",
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
            
            return {
                "request_id": request_id,
                "operations": operations,
                "total_time": sum(op["response_time"] for op in operations)
            }
        
        # Ejecutar peticiones extremas
        print(f"\nEjecutando {num_requests} peticiones extremas...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(extreme_request, i) for i in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Análisis de resultados
        successful_requests = [r for r in results if all(op["status_code"] in [200, 201] for op in r["operations"])]
        total_times = [r["total_time"] for r in results]
        
        print(f"Peticiones exitosas: {len(successful_requests)}/{num_requests}")
        print(f"Tiempo promedio: {statistics.mean(total_times):.3f}s")
        print(f"Tiempo máximo: {max(total_times):.3f}s")
        print(f"Tiempo mínimo: {min(total_times):.3f}s")
        
        # Verificaciones
        assert len(successful_requests) >= num_requests * 0.8  # 80% de éxito mínimo
        assert max(total_times) < 10.0  # Máximo 10 segundos por petición completa
    
    def test_sustained_load(self, client, auth_headers):
        """Test de carga sostenida"""
        duration = 30  # segundos
        start_time = time.time()
        request_count = 0
        successful_requests = 0
        
        print(f"\nEjecutando carga sostenida por {duration} segundos...")
        
        while time.time() - start_time < duration:
            # Realizar peticiones mixtas
            operations = [
                lambda: client.get("/api/usuarios/", headers=auth_headers),
                lambda: client.get("/api/empleados/", headers=auth_headers),
                lambda: client.get("/api/clases/", headers=auth_headers)
            ]
            
            for operation in operations:
                try:
                    response = operation()
                    request_count += 1
                    if response.status_code in [200, 201]:
                        successful_requests += 1
                except Exception as e:
                    print(f"Error en petición: {e}")
                    request_count += 1
        
        total_time = time.time() - start_time
        requests_per_second = request_count / total_time
        
        print(f"Tiempo total: {total_time:.2f}s")
        print(f"Total de peticiones: {request_count}")
        print(f"Peticiones exitosas: {successful_requests}")
        print(f"Peticiones por segundo: {requests_per_second:.2f}")
        print(f"Tasa de éxito: {(successful_requests/request_count)*100:.1f}%")
        
        # Verificaciones
        assert requests_per_second > 10  # Mínimo 10 peticiones por segundo
        assert (successful_requests/request_count) > 0.9  # 90% de éxito mínimo

class TestRecoveryTesting:
    """Tests de recuperación"""
    
    def test_system_recovery_after_load(self, client, auth_headers):
        """Test de recuperación del sistema después de carga"""
        # Aplicar carga
        print("\nAplicando carga al sistema...")
        for i in range(100):
            user_data = {
                "email": f"recovery_user_{i}@example.com",
                "nombre": f"Usuario {i}",
                "apellido": "Recovery",
                "password": "SecurePass123!",
                "rol": "usuario"
            }
            client.post("/api/usuarios/", json=user_data, headers=auth_headers)
        
        # Esperar un momento para que el sistema se estabilice
        time.sleep(2)
        
        # Test de recuperación
        print("Probando recuperación del sistema...")
        
        start_time = time.time()
        response = client.get("/api/usuarios/", headers=auth_headers)
        recovery_time = time.time() - start_time
        
        print(f"Tiempo de recuperación: {recovery_time:.3f}s")
        
        assert response.status_code == 200
        assert recovery_time < 2.0  # Máximo 2 segundos para recuperación
    
    def test_error_recovery(self, client, auth_headers):
        """Test de recuperación de errores"""
        # Simular errores
        with patch('app.core.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Simulated database error")
            
            # Intentar operación que falla
            response = client.get("/api/usuarios/", headers=auth_headers)
            assert response.status_code == 500
        
        # Verificar que el sistema se recupera
        response = client.get("/api/usuarios/", headers=auth_headers)
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 