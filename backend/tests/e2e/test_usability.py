"""
Tests de Usabilidad - Sistema de Gimnasio v6
Verifica la experiencia del usuario y facilidad de uso
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import Request, Response
import redis.asyncio as redis

from app.main import app
from app.core.database import get_db
from app.models.usuarios import Usuario
from app.schemas.auth import LoginRequest
from app.core.security import hash_password

# Configuración de tests
@pytest.fixture
def client():
    """Cliente de prueba para FastAPI"""
    return TestClient(app)

@pytest.fixture
def test_user_data():
    """Datos de usuario de prueba"""
    return {
        "email": "usuario@example.com",
        "nombre": "Usuario",
        "apellido": "Test",
        "password": "SecurePass123!",
        "telefono": "123456789",
        "fecha_nacimiento": "1990-01-01"
    }

@pytest.fixture
def auth_headers(client, test_user_data):
    """Headers de autenticación para tests"""
    # Crear usuario
    client.post("/api/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestUserInterfaceUsability:
    """Tests de usabilidad de la interfaz de usuario"""
    
    def test_api_response_format_consistency(self, client, auth_headers):
        """Verificar consistencia en el formato de respuestas de la API"""
        # Test de diferentes endpoints
        endpoints = [
            "/api/usuarios/",
            "/api/empleados/",
            "/api/clases/",
            "/api/asistencias/",
            "/api/pagos/"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar que las respuestas son listas o diccionarios
                assert isinstance(data, (list, dict))
                
                # Si es una lista, verificar que los elementos tienen estructura consistente
                if isinstance(data, list) and len(data) > 0:
                    first_item = data[0]
                    assert isinstance(first_item, dict)
                    assert "id" in first_item
    
    def test_error_message_clarity(self, client):
        """Verificar claridad de mensajes de error"""
        # Test de login con credenciales inválidas
        login_data = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        
        error_data = response.json()
        assert "detail" in error_data
        assert "credenciales" in error_data["detail"].lower() or "invalid" in error_data["detail"].lower()
    
    def test_validation_error_messages(self, client, auth_headers):
        """Verificar mensajes de error de validación"""
        # Test de creación de usuario con datos inválidos
        invalid_user = {
            "email": "invalid-email",
            "nombre": "",
            "password": "123"
        }
        
        response = client.post("/api/usuarios/", json=invalid_user, headers=auth_headers)
        assert response.status_code == 422
        
        error_data = response.json()
        assert "detail" in error_data
        
        # Verificar que los errores son específicos
        errors = error_data["detail"]
        assert isinstance(errors, list)
        
        # Verificar que hay errores para cada campo inválido
        error_fields = [error["loc"][-1] for error in errors]
        assert "email" in error_fields
        assert "nombre" in error_fields
        assert "password" in error_fields
    
    def test_response_headers_usability(self, client, auth_headers):
        """Verificar headers útiles en las respuestas"""
        response = client.get("/api/usuarios/", headers=auth_headers)
        
        # Verificar headers importantes
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]
        
        # Verificar headers de seguridad
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
    
    def test_pagination_usability(self, client, auth_headers):
        """Verificar usabilidad de la paginación"""
        # Crear múltiples usuarios para probar paginación
        for i in range(25):
            user_data = {
                "email": f"user{i}@example.com",
                "nombre": f"Usuario {i}",
                "apellido": "Test",
                "password": "SecurePass123!",
                "rol": "usuario"
            }
            client.post("/api/usuarios/", json=user_data, headers=auth_headers)
        
        # Test de paginación
        response = client.get("/api/usuarios/?page=1&size=10", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verificar estructura de paginación
        if isinstance(data, dict) and "data" in data:
            assert len(data["data"]) <= 10
            assert "pagination" in data
            pagination = data["pagination"]
            assert "page" in pagination
            assert "total" in pagination
            assert "pages" in pagination
            assert "has_next" in pagination
            assert "has_prev" in pagination

class TestWorkflowUsability:
    """Tests de usabilidad de flujos de trabajo"""
    
    def test_user_registration_workflow(self, client):
        """Test del flujo completo de registro de usuario"""
        # 1. Intentar registro con datos válidos
        user_data = {
            "email": "newuser@example.com",
            "nombre": "Nuevo",
            "apellido": "Usuario",
            "password": "SecurePass123!",
            "telefono": "123456789",
            "fecha_nacimiento": "1990-01-01"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        
        user_response = response.json()
        assert user_response["email"] == user_data["email"]
        assert "password" not in user_response
        
        # 2. Verificar que el usuario puede hacer login inmediatamente
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        
        login_response = response.json()
        assert "access_token" in login_response
    
    def test_clase_booking_workflow(self, client, auth_headers):
        """Test del flujo de reserva de clase"""
        # 1. Crear empleado
        empleado_data = {
            "nombre": "Instructor",
            "apellido": "Test",
            "email": "instructor@example.com",
            "telefono": "123456789",
            "cargo": "Instructor"
        }
        
        empleado_response = client.post("/api/empleados/", json=empleado_data, headers=auth_headers)
        assert empleado_response.status_code == 201
        empleado_id = empleado_response.json()["id"]
        
        # 2. Crear clase
        clase_data = {
            "nombre": "Yoga Básico",
            "descripcion": "Clase de yoga para principiantes",
            "duracion": 60,
            "capacidad_maxima": 20,
            "instructor_id": empleado_id
        }
        
        clase_response = client.post("/api/clases/", json=clase_data, headers=auth_headers)
        assert clase_response.status_code == 201
        clase_id = clase_response.json()["id"]
        
        # 3. Registrar asistencia
        asistencia_data = {
            "usuario_id": 1,  # Asumiendo que existe un usuario con ID 1
            "clase_id": clase_id,
            "fecha": "2024-01-15",
            "hora_entrada": "10:00:00",
            "estado": "presente"
        }
        
        asistencia_response = client.post("/api/asistencias/", json=asistencia_data, headers=auth_headers)
        assert asistencia_response.status_code == 201
        
        # 4. Verificar que la asistencia se registró correctamente
        asistencia_id = asistencia_response.json()["id"]
        get_response = client.get(f"/api/asistencias/{asistencia_id}", headers=auth_headers)
        assert get_response.status_code == 200
    
    def test_payment_workflow(self, client, auth_headers):
        """Test del flujo de pago"""
        # 1. Crear usuario para el pago
        user_data = {
            "email": "payment@example.com",
            "nombre": "Usuario",
            "apellido": "Pago",
            "password": "SecurePass123!",
            "rol": "usuario"
        }
        
        user_response = client.post("/api/usuarios/", json=user_data, headers=auth_headers)
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]
        
        # 2. Registrar pago
        pago_data = {
            "usuario_id": user_id,
            "monto": 50.00,
            "tipo_pago": "mensual",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "tarjeta",
            "estado": "completado"
        }
        
        pago_response = client.post("/api/pagos/", json=pago_data, headers=auth_headers)
        assert pago_response.status_code == 201
        
        # 3. Verificar que el pago se registró correctamente
        pago_id = pago_response.json()["id"]
        get_response = client.get(f"/api/pagos/{pago_id}", headers=auth_headers)
        assert get_response.status_code == 200
        
        pago = get_response.json()
        assert pago["monto"] == pago_data["monto"]
        assert pago["estado"] == pago_data["estado"]

class TestDataValidationUsability:
    """Tests de usabilidad de validación de datos"""
    
    def test_email_validation_feedback(self, client, auth_headers):
        """Verificar feedback de validación de email"""
        invalid_emails = [
            "invalid-email",
            "test@",
            "@example.com",
            "test..test@example.com",
            "test@example..com"
        ]
        
        for email in invalid_emails:
            user_data = {
                "email": email,
                "nombre": "Test",
                "apellido": "User",
                "password": "SecurePass123!"
            }
            
            response = client.post("/api/usuarios/", json=user_data, headers=auth_headers)
            assert response.status_code == 422
            
            error_data = response.json()
            assert "detail" in error_data
            
            # Verificar que el error menciona el email
            errors = error_data["detail"]
            email_errors = [error for error in errors if "email" in error["loc"]]
            assert len(email_errors) > 0
    
    def test_password_validation_feedback(self, client, auth_headers):
        """Verificar feedback de validación de contraseña"""
        weak_passwords = [
            "123",  # Muy corta
            "password",  # Sin números ni caracteres especiales
            "PASSWORD",  # Solo mayúsculas
            "12345678",  # Solo números
            "pass word"  # Con espacios
        ]
        
        for password in weak_passwords:
            user_data = {
                "email": f"test{hash(password)}@example.com",
                "nombre": "Test",
                "apellido": "User",
                "password": password
            }
            
            response = client.post("/api/usuarios/", json=user_data, headers=auth_headers)
            assert response.status_code == 422
            
            error_data = response.json()
            assert "detail" in error_data
    
    def test_phone_validation_feedback(self, client, auth_headers):
        """Verificar feedback de validación de teléfono"""
        invalid_phones = [
            "123",  # Muy corto
            "12345678901234567890",  # Muy largo
            "abc-def-ghij",  # Con letras
            "123-456-789",  # Con guiones
            "+1 234 567 8900"  # Con espacios y símbolos
        ]
        
        for phone in invalid_phones:
            user_data = {
                "email": f"test{hash(phone)}@example.com",
                "nombre": "Test",
                "apellido": "User",
                "password": "SecurePass123!",
                "telefono": phone
            }
            
            response = client.post("/api/usuarios/", json=user_data, headers=auth_headers)
            # Algunos teléfonos pueden ser válidos, pero verificamos que no causen errores 500
            assert response.status_code in [201, 422]

class TestSearchAndFilterUsability:
    """Tests de usabilidad de búsqueda y filtros"""
    
    def test_search_functionality(self, client, auth_headers):
        """Test de funcionalidad de búsqueda"""
        # Crear usuarios con nombres diferentes
        users_data = [
            {"email": "juan@example.com", "nombre": "Juan", "apellido": "Pérez"},
            {"email": "maria@example.com", "nombre": "María", "apellido": "García"},
            {"email": "pedro@example.com", "nombre": "Pedro", "apellido": "López"}
        ]
        
        for user_data in users_data:
            user_data.update({
                "password": "SecurePass123!",
                "rol": "usuario"
            })
            client.post("/api/usuarios/", json=user_data, headers=auth_headers)
        
        # Test de búsqueda por nombre
        response = client.get("/api/usuarios/?search=Juan", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        if isinstance(data, list):
            # Verificar que solo se devuelven usuarios que coinciden
            for user in data:
                assert "Juan" in user["nombre"] or "Juan" in user["apellido"]
    
    def test_filter_functionality(self, client, auth_headers):
        """Test de funcionalidad de filtros"""
        # Crear usuarios con diferentes roles
        users_data = [
            {"email": "admin@example.com", "nombre": "Admin", "rol": "admin"},
            {"email": "user1@example.com", "nombre": "User1", "rol": "usuario"},
            {"email": "user2@example.com", "nombre": "User2", "rol": "usuario"}
        ]
        
        for user_data in users_data:
            user_data.update({
                "password": "SecurePass123!",
                "apellido": "Test"
            })
            client.post("/api/usuarios/", json=user_data, headers=auth_headers)
        
        # Test de filtro por rol
        response = client.get("/api/usuarios/?rol=usuario", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        if isinstance(data, list):
            # Verificar que solo se devuelven usuarios con rol "usuario"
            for user in data:
                assert user["rol"] == "usuario"

class TestErrorRecoveryUsability:
    """Tests de usabilidad de recuperación de errores"""
    
    def test_graceful_error_handling(self, client, auth_headers):
        """Test de manejo elegante de errores"""
        # Test de endpoint que no existe
        response = client.get("/api/nonexistent/", headers=auth_headers)
        assert response.status_code == 404
        
        error_data = response.json()
        assert "detail" in error_data
        assert "not found" in error_data["detail"].lower()
    
    def test_partial_data_handling(self, client, auth_headers):
        """Test de manejo de datos parciales"""
        # Test de actualización con datos parciales
        user_data = {
            "nombre": "Usuario Actualizado"
            # Sin email ni otros campos requeridos
        }
        
        response = client.put("/api/usuarios/1", json=user_data, headers=auth_headers)
        # Debería ser 200 (actualización parcial) o 404 (usuario no existe)
        assert response.status_code in [200, 404]
    
    def test_network_error_simulation(self, client, auth_headers):
        """Test de simulación de errores de red"""
        # Simular timeout
        with patch('app.core.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Connection timeout")
            
            response = client.get("/api/usuarios/", headers=auth_headers)
            assert response.status_code == 500
            
            error_data = response.json()
            assert "detail" in error_data

class TestPerformanceUsability:
    """Tests de usabilidad de performance"""
    
    def test_response_time_expectations(self, client, auth_headers):
        """Test de expectativas de tiempo de respuesta"""
        # Test de endpoints básicos
        endpoints = [
            "/api/usuarios/",
            "/api/empleados/",
            "/api/clases/"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint, headers=auth_headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Verificar que la respuesta es rápida
            assert response_time < 2.0  # Menos de 2 segundos
            assert response.status_code in [200, 404]
    
    def test_large_dataset_handling(self, client, auth_headers):
        """Test de manejo de grandes conjuntos de datos"""
        # Crear muchos usuarios para probar performance
        start_time = time.time()
        
        for i in range(50):
            user_data = {
                "email": f"user{i}@example.com",
                "nombre": f"Usuario {i}",
                "apellido": "Test",
                "password": "SecurePass123!",
                "rol": "usuario"
            }
            client.post("/api/usuarios/", json=user_data, headers=auth_headers)
        
        creation_time = time.time() - start_time
        
        # Verificar que la creación es eficiente
        assert creation_time < 10.0  # Menos de 10 segundos para 50 usuarios
        
        # Test de obtención de la lista completa
        start_time = time.time()
        response = client.get("/api/usuarios/", headers=auth_headers)
        retrieval_time = time.time() - start_time
        
        assert response.status_code == 200
        assert retrieval_time < 3.0  # Menos de 3 segundos para obtener la lista

class TestAccessibilityUsability:
    """Tests de usabilidad de accesibilidad"""
    
    def test_api_consistency(self, client, auth_headers):
        """Test de consistencia de la API"""
        # Verificar que todos los endpoints siguen el mismo patrón
        endpoints = [
            ("/api/usuarios/", "GET"),
            ("/api/empleados/", "GET"),
            ("/api/clases/", "GET"),
            ("/api/asistencias/", "GET"),
            ("/api/pagos/", "GET")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint, headers=auth_headers)
            elif method == "POST":
                response = client.post(endpoint, headers=auth_headers)
            
            # Verificar que todos los endpoints responden de manera consistente
            assert response.status_code in [200, 401, 404, 422]
    
    def test_error_code_consistency(self, client):
        """Test de consistencia de códigos de error"""
        # Verificar que los errores usan códigos HTTP estándar
        error_scenarios = [
            ("/api/nonexistent/", 404),  # Not Found
            ("/api/auth/login", 422),    # Unprocessable Entity (sin datos)
        ]
        
        for endpoint, expected_code in error_scenarios:
            if expected_code == 422:
                response = client.post(endpoint)
            else:
                response = client.get(endpoint)
            
            assert response.status_code == expected_code

class TestDocumentationUsability:
    """Tests de usabilidad de documentación"""
    
    def test_api_documentation_access(self, client):
        """Test de acceso a la documentación de la API"""
        # Verificar que la documentación está disponible
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Verificar que contiene información útil
        content = response.text
        assert "FastAPI" in content
        assert "docs" in content
    
    def test_openapi_schema_access(self, client):
        """Test de acceso al esquema OpenAPI"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "components" in schema

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 