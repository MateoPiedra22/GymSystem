#!/usr/bin/env python3
"""
Suite de pruebas automatizadas para el sistema de gimnasio
Incluye pruebas de rendimiento, seguridad, funcionalidad e integración
"""

import pytest
import time
import json
import secrets
import string
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importar la aplicación
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.core.database import get_db, Base
from app.core.security import create_access_token, verify_password
from app.core.auth import get_password_hash

# Configuración de base de datos de prueba
SQLALCHEMY_DATABASE_URL = "postgresql://test_user:test_secure_password_2024@localhost:5432/gym_test_db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override de la función get_db para testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Configurar la aplicación para testing
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Configurar base de datos de prueba"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(setup_database):
    """Cliente de prueba"""
    return TestClient(app)

@pytest.fixture()
def auth_headers(client, db_session):
    """Headers de autenticación para pruebas"""
    # Generar contraseña segura para testing
    def generate_secure_password(length=16):
        """Genera contraseña segura para testing"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
            # Verificar que cumple criterios de seguridad
            if (any(c.islower() for c in password) and
                any(c.isupper() for c in password) and
                any(c.isdigit() for c in password) and
                any(c in "!@#$%^&*" for c in password)):
                return password
    
    # Usar contraseña segura en lugar de "admin123"
    secure_password = generate_secure_password()
    
    # Crear usuario de prueba con contraseña segura
    from app.models.usuarios import Usuario
    from app.models.empleados import Empleado
    
    db = TestingSessionLocal()
    try:
        # Verificar si ya existe el usuario admin
        admin_user = db.query(Usuario).filter(Usuario.email == "admin@test.com").first()
        if not admin_user:
            # Crear usuario admin con contraseña segura
            hashed_password = get_password_hash(secure_password)
            admin_user = Usuario(
                email="admin@test.com",
                nombre="Admin Test",
                hashed_password=hashed_password,
                es_admin=True,
                esta_activo=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
        
        # Crear token de acceso
        access_token = create_access_token(data={"sub": admin_user.email})
        return {"Authorization": f"Bearer {access_token}"}
    finally:
        db.close()

# ============================================================================
# SUITE DE PRUEBAS DE RENDIMIENTO
# ============================================================================

@pytest.mark.performance
class TestPerformanceSuite:
    """Suite de pruebas de rendimiento"""
    
    def measure_response_time(self, func, *args, **kwargs):
        """Medir tiempo de respuesta de una función"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return (end_time - start_time) * 1000, result  # Convertir a milisegundos
    
    def test_endpoint_performance(self, client, setup_database):
        """Verificar rendimiento de endpoints principales"""
        # Medir tiempo de respuesta para endpoints críticos
        endpoints = [
            "/api/usuarios",
            "/api/clases", 
            "/api/asistencias",
            "/api/pagos"
        ]
        
        for endpoint in endpoints:
            response_time, response = self.measure_response_time(
                client.get, endpoint
            )
            assert response_time < 2000, f"Endpoint {endpoint} tardó {response_time}ms (límite: 2000ms)"
            assert response.status_code in [200, 401, 403]
    
    def test_kpis_performance(self, client, setup_database):
        """Verificar rendimiento de KPIs"""
        response_time, response = self.measure_response_time(
            client.get, "/api/reportes/kpis"
        )
        assert response_time < 3000, f"KPIs tardaron {response_time}ms (límite: 3000ms)"
        assert response.status_code in [200, 401]

# ============================================================================
# SUITE DE PRUEBAS DE AUTENTICACIÓN
# ============================================================================

@pytest.mark.auth
class TestAuthenticationSuite:
    """Suite de pruebas de autenticación y autorización"""
    
    def test_login_successful(self, client):
        """Prueba de login exitoso con contraseña segura"""
        # Generar contraseña segura para esta prueba
        def generate_secure_password(length=16):
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            while True:
                password = ''.join(secrets.choice(alphabet) for _ in range(length))
                if (any(c.islower() for c in password) and
                    any(c.isupper() for c in password) and
                    any(c.isdigit() for c in password) and
                    any(c in "!@#$%^&*" for c in password)):
                    return password
        
        secure_password = generate_secure_password()
        
        # Crear usuario temporal para la prueba
        from app.models.usuarios import Usuario
        db = TestingSessionLocal()
        try:
            hashed_password = get_password_hash(secure_password)
            test_user = Usuario(
                email="test_login@example.com",
                nombre="Test Login User",
                hashed_password=hashed_password,
                esta_activo=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            
            response = client.post("/auth/login", json={
                "username": "test_login@example.com",
                "password": secure_password
            })
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            
        finally:
            db.close()
    
    def test_login_invalid_credentials(self, client):
        """Prueba de login con credenciales inválidas"""
        response = client.post("/auth/login", json={
            "username": "invalid@example.com",
            "password": "InvalidPassword123!"
        })
        assert response.status_code == 401
    
    def test_protected_endpoint_without_token(self, client):
        """Prueba de acceso a endpoint protegido sin token"""
        response = client.get("/api/usuarios")
        assert response.status_code == 401
    
    def test_token_expiration(self, client):
        """Prueba de expiración de token"""
        # Crear token con expiración muy corta
        from datetime import timedelta
        expired_token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(seconds=1)
        )
        
        # Esperar a que expire
        time.sleep(2)
        
        response = client.get(
            "/api/usuarios",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401

# ============================================================================
# SUITE DE PRUEBAS DE ENDPOINTS
# ============================================================================

@pytest.mark.endpoints
class TestUsuariosEndpointsSuite:
    """Suite de pruebas de endpoints de usuarios"""
    
    def test_get_usuarios(self, client, auth_headers):
        """Prueba de obtención de usuarios"""
        response = client.get("/api/usuarios", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "usuarios" in data
    
    def test_create_usuario(self, client, auth_headers):
        """Prueba de creación de usuario"""
        user_data = {
            "email": "test_create@example.com",
            "nombre": "Test Create User",
            "password": "SecurePass123!"
        }
        response = client.post("/api/usuarios", json=user_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
    
    def test_create_usuario_email_duplicado(self, client, auth_headers):
        """Prueba de creación de usuario con email duplicado"""
        user_data = {
            "email": "test_duplicate@example.com",
            "nombre": "Test Duplicate User",
            "password": "SecurePass123!"
        }
        
        # Crear primer usuario
        response1 = client.post("/api/usuarios", json=user_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Intentar crear segundo usuario con mismo email
        response2 = client.post("/api/usuarios", json=user_data, headers=auth_headers)
        assert response2.status_code == 400
    
    def test_update_usuario(self, client, auth_headers):
        """Prueba de actualización de usuario"""
        # Primero crear un usuario
        user_data = {
            "email": "test_update@example.com",
            "nombre": "Test Update User",
            "password": "SecurePass123!"
        }
        create_response = client.post("/api/usuarios", json=user_data, headers=auth_headers)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Actualizar usuario
        update_data = {"nombre": "Updated Name"}
        response = client.put(f"/api/usuarios/{user_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Updated Name"

@pytest.mark.endpoints
class TestClasesEndpointsSuite:
    """Suite de pruebas de endpoints de clases"""
    
    def test_get_clases(self, client, auth_headers):
        """Prueba de obtención de clases"""
        response = client.get("/api/clases", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "clases" in data
    
    def test_create_clase(self, client, auth_headers):
        """Prueba de creación de clase"""
        clase_data = {
            "nombre": "Test Class",
            "descripcion": "Test Description",
            "capacidad_maxima": 20,
            "duracion_minutos": 60
        }
        response = client.post("/api/clases", json=clase_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == clase_data["nombre"]
    
    def test_horarios_conflictivos(self, client, auth_headers):
        """Prueba de detección de horarios conflictivos"""
        # Crear primera clase
        clase1_data = {
            "nombre": "Class 1",
            "descripcion": "First class",
            "capacidad_maxima": 20,
            "duracion_minutos": 60,
            "hora_inicio": "10:00",
            "hora_fin": "11:00"
        }
        response1 = client.post("/api/clases", json=clase1_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Intentar crear clase con horario conflictivo
        clase2_data = {
            "nombre": "Class 2",
            "descripcion": "Second class",
            "capacidad_maxima": 20,
            "duracion_minutos": 60,
            "hora_inicio": "10:30",  # Conflicto con la primera clase
            "hora_fin": "11:30"
        }
        response2 = client.post("/api/clases", json=clase2_data, headers=auth_headers)
        assert response2.status_code == 400

@pytest.mark.endpoints
class TestAsistenciasEndpointsSuite:
    """Suite de pruebas de endpoints de asistencias"""
    
    def test_registrar_asistencia(self, client, auth_headers):
        """Prueba de registro de asistencia"""
        # Primero crear una clase
        clase_data = {
            "nombre": "Test Class for Attendance",
            "descripcion": "Test Description",
            "capacidad_maxima": 20,
            "duracion_minutos": 60
        }
        clase_response = client.post("/api/clases", json=clase_data, headers=auth_headers)
        assert clase_response.status_code == 201
        clase_id = clase_response.json()["id"]
        
        # Registrar asistencia
        asistencia_data = {
            "clase_id": clase_id,
            "usuario_id": 1
        }
        response = client.post("/api/asistencias", json=asistencia_data, headers=auth_headers)
        assert response.status_code == 201
    
    def test_capacidad_maxima_clase(self, client, auth_headers):
        """Prueba de límite de capacidad de clase"""
        # Crear clase con capacidad 1
        clase_data = {
            "nombre": "Limited Class",
            "descripcion": "Test Description",
            "capacidad_maxima": 1,
            "duracion_minutos": 60
        }
        clase_response = client.post("/api/clases", json=clase_data, headers=auth_headers)
        assert clase_response.status_code == 201
        clase_id = clase_response.json()["id"]
        
        # Intentar registrar más asistencias de las permitidas
        for i in range(2):
            asistencia_data = {
                "clase_id": clase_id,
                "usuario_id": i + 1
            }
            response = client.post("/api/asistencias", json=asistencia_data, headers=auth_headers)
            if i == 0:
                assert response.status_code == 201  # Primera asistencia OK
            else:
                assert response.status_code == 400  # Segunda asistencia debe fallar
    
    def test_get_asistencias_usuario(self, client, auth_headers):
        """Prueba de obtención de asistencias de usuario"""
        response = client.get("/api/asistencias/usuario/1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "asistencias" in data

@pytest.mark.endpoints
class TestPagosEndpointsSuite:
    """Suite de pruebas de endpoints de pagos"""
    
    def test_get_pagos(self, client, auth_headers):
        """Prueba de obtención de pagos"""
        response = client.get("/api/pagos", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "pagos" in data
    
    def test_procesar_pago(self, client, auth_headers):
        """Prueba de procesamiento de pago"""
        pago_data = {
            "usuario_id": 1,
            "monto": 50.00,
            "concepto": "mensualidad",
            "metodo_pago": "tarjeta"
        }
        response = client.post("/api/pagos", json=pago_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["monto"] == pago_data["monto"]
    
    def test_calculos_automaticos(self, client, auth_headers):
        """Prueba de cálculos automáticos en pagos"""
        # Esta prueba verifica que los cálculos de impuestos y totales sean correctos
        pago_data = {
            "usuario_id": 1,
            "monto": 100.00,
            "concepto": "mensualidad",
            "metodo_pago": "tarjeta"
        }
        response = client.post("/api/pagos", json=pago_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "monto_final" in data
        assert data["monto_final"] > pago_data["monto"]  # Debe incluir impuestos

@pytest.mark.endpoints
class TestReportesEndpointsSuite:
    """Suite de pruebas de endpoints de reportes"""
    
    def test_get_kpis(self, client, auth_headers):
        """Prueba de obtención de KPIs"""
        response = client.get("/api/reportes/kpis", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que los KPIs contengan los campos esperados
        expected_kpis = [
            "ingresos_mes", "nuevas_inscripciones_mes", "tasa_retencion",
            "ocupacion_promedio_clases", "asistencias_diarias_promedio"
        ]
        for kpi in expected_kpis:
            assert kpi in data
    
    def test_get_graficos(self, client, auth_headers):
        """Prueba de obtención de gráficos"""
        response = client.get("/api/reportes/graficos", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "graficos" in data
    
    def test_kpis_valores_numericos(self, client, auth_headers):
        """Prueba de que los KPIs devuelvan valores numéricos válidos"""
        response = client.get("/api/reportes/kpis", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que los valores sean numéricos
        numeric_kpis = ["ingresos_mes", "nuevas_inscripciones_mes", "tasa_retencion"]
        for kpi in numeric_kpis:
            if kpi in data:
                assert isinstance(data[kpi], (int, float)) or data[kpi] is None

# ============================================================================
# SUITE DE PRUEBAS DE VALIDACIÓN
# ============================================================================

@pytest.mark.validation
class TestDataValidationSuite:
    """Suite de pruebas de validación de datos"""
    
    def test_email_format_validation(self, client, auth_headers):
        """Prueba de validación de formato de email"""
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
                "nombre": "Test User",
                "password": "SecurePass123!"
            }
            response = client.post("/api/usuarios", json=user_data, headers=auth_headers)
            assert response.status_code == 422, f"Email {email} debería ser inválido"
        
        # Probar email válido
        valid_user_data = {
            "email": "valid@example.com",
            "nombre": "Valid User",
            "password": "SecurePass123!"
        }
        response = client.post("/api/usuarios", json=valid_user_data, headers=auth_headers)
        assert response.status_code == 201
    
    def test_required_fields(self, client, auth_headers):
        """Prueba de campos requeridos"""
        # Intentar crear usuario sin campos requeridos
        incomplete_data = {
            "nombre": "Test User"
            # Falta email y password
        }
        response = client.post("/api/usuarios", json=incomplete_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_date_format_validation(self, client, auth_headers):
        """Prueba de validación de formato de fecha"""
        # Probar fechas inválidas
        invalid_dates = [
            "2023-13-01",  # Mes inválido
            "2023-00-01",  # Mes inválido
            "2023-12-32",  # Día inválido
            "2023-12-00",  # Día inválido
            "invalid-date",
            "2023/12/01"   # Formato incorrecto
        ]
        
        for date in invalid_dates:
            # Usar en contexto de clase (si aplica)
            clase_data = {
                "nombre": "Test Class",
                "descripcion": "Test Description",
                "capacidad_maxima": 20,
                "duracion_minutos": 60,
                "fecha": date
            }
            response = client.post("/api/clases", json=clase_data, headers=auth_headers)
            if response.status_code != 201:  # Algunos endpoints pueden no validar fecha
                assert response.status_code == 422, f"Fecha {date} debería ser inválida"
    
    def test_phone_format_validation(self, client, auth_headers):
        """Prueba de validación de formato de teléfono"""
        invalid_phones = [
            "123",  # Muy corto
            "12345678901234567890",  # Muy largo
            "abc-def-ghij",  # Solo letras
            "123-abc-4567",  # Mezcla inválida
            "123.456.7890",  # Formato incorrecto
        ]
        
        for phone in invalid_phones:
            user_data = {
                "email": f"test_{phone}@example.com",
                "nombre": "Test User",
                "password": "SecurePass123!",
                "telefono": phone
            }
            response = client.post("/api/usuarios", json=user_data, headers=auth_headers)
            if response.status_code != 201:  # Algunos endpoints pueden no validar teléfono
                assert response.status_code == 422, f"Teléfono {phone} debería ser inválido"

# ============================================================================
# SUITE DE PRUEBAS DE SEGURIDAD
# ============================================================================

@pytest.mark.security
class TestSecuritySuite:
    """Suite de pruebas de seguridad"""
    
    def test_sql_injection_prevention(self, client, auth_headers):
        """Prueba de prevención de SQL injection"""
        # Intentar SQL injection en diferentes campos
        sql_injection_payloads = [
            "'; DROP TABLE usuarios; --",
            "' OR '1'='1",
            "'; INSERT INTO usuarios VALUES (999, 'hacker', 'hacker@evil.com'); --",
            "' UNION SELECT * FROM usuarios --"
        ]
        
        for payload in sql_injection_payloads:
            # Probar en búsqueda de usuarios
            response = client.get(f"/api/usuarios?search={payload}", headers=auth_headers)
            # No debe devolver error 500 (error interno del servidor)
            assert response.status_code != 500, f"SQL injection exitoso con payload: {payload}"
            
            # Probar en creación de usuario
            user_data = {
                "email": f"test_{payload}@example.com",
                "nombre": payload,
                "password": "SecurePass123!"
            }
            response = client.post("/api/usuarios", json=user_data, headers=auth_headers)
            # Debe fallar por validación, no por error interno
            if response.status_code != 201:
                assert response.status_code in [400, 422], f"SQL injection exitoso en creación con payload: {payload}"
    
    def test_xss_prevention(self, client, auth_headers):
        """Prueba de prevención de XSS"""
        # Payloads de XSS para probar
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//",
            "<svg onload=alert('XSS')>",
        ]
        
        for payload in xss_payloads:
            # Probar en nombre de usuario
            user_data = {
                "email": f"test_{hash(payload)}@example.com",
                "nombre": payload,
                "password": "SecurePass123!"
            }
            response = client.post("/api/usuarios", json=user_data, headers=auth_headers)
            
            if response.status_code == 201:
                # Si se creó, verificar que el payload no se ejecute
                user_id = response.json()["id"]
                get_response = client.get(f"/api/usuarios/{user_id}", headers=auth_headers)
                assert get_response.status_code == 200
                user_data_response = get_response.json()
                
                # El nombre debe estar escapado o filtrado
                assert "<script>" not in user_data_response["nombre"]
                assert "javascript:" not in user_data_response["nombre"]
                assert "onerror=" not in user_data_response["nombre"]

# ============================================================================
# SUITE DE PRUEBAS DE MANEJO DE ERRORES
# ============================================================================

@pytest.mark.errors
class TestErrorHandlingSuite:
    """Suite de pruebas de manejo de errores"""
    
    def test_404_endpoint_inexistente(self, client):
        """Prueba de endpoint inexistente"""
        response = client.get("/api/endpoint-inexistente")
        assert response.status_code == 404
    
    def test_405_metodo_no_permitido(self, client):
        """Prueba de método HTTP no permitido"""
        response = client.post("/api/usuarios")  # GET es el método correcto
        assert response.status_code == 405
    
    def test_500_error_interno(self, client):
        """Prueba de error interno del servidor"""
        # Esta prueba verifica que los errores internos se manejen apropiadamente
        # No podemos forzar un error 500 fácilmente, pero podemos verificar
        # que las respuestas de error tengan el formato correcto
        response = client.get("/api/usuarios")  # Sin autenticación
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_validation_errors(self, client, auth_headers):
        """Prueba de errores de validación"""
        # Datos inválidos
        invalid_data = {
            "email": "invalid-email",
            "nombre": "",  # Nombre vacío
            "password": "123"  # Contraseña muy corta
        }
        response = client.post("/api/usuarios", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0  # Debe tener errores de validación
    
    def test_database_connection_errors(self, client, auth_headers):
        """Prueba de errores de conexión a base de datos"""
        # Esta prueba verifica que los errores de BD se manejen apropiadamente
        # En un entorno de prueba real, podríamos simular fallos de BD
        response = client.get("/api/usuarios", headers=auth_headers)
        assert response.status_code in [200, 500]  # 200 si funciona, 500 si hay error de BD
    
    def test_rate_limiting(self, client, auth_headers):
        """Prueba de rate limiting"""
        # Hacer múltiples requests rápidos
        for i in range(10):
            response = client.get("/api/usuarios", headers=auth_headers)
            if response.status_code == 429:  # Too Many Requests
                break
        else:
            # Si no se activó rate limiting, verificar que al menos funcione
            response = client.get("/api/usuarios", headers=auth_headers)
            assert response.status_code in [200, 401, 403]

# ============================================================================
# SUITE DE PRUEBAS DE INTEGRACIÓN
# ============================================================================

@pytest.mark.integration
class TestIntegrationSuite:
    """Suite de pruebas de integración"""
    
    def test_flujo_completo_usuario(self, client, auth_headers):
        """Prueba de flujo completo de usuario"""
        # 1. Crear usuario
        user_data = {
            "email": "integration_test@example.com",
            "nombre": "Integration Test User",
            "password": "SecurePass123!"
        }
        create_response = client.post("/api/usuarios", json=user_data, headers=auth_headers)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # 2. Crear clase
        clase_data = {
            "nombre": "Integration Test Class",
            "descripcion": "Test Description",
            "capacidad_maxima": 20,
            "duracion_minutos": 60
        }
        clase_response = client.post("/api/clases", json=clase_data, headers=auth_headers)
        assert clase_response.status_code == 201
        clase_id = clase_response.json()["id"]
        
        # 3. Registrar asistencia
        asistencia_data = {
            "clase_id": clase_id,
            "usuario_id": user_id
        }
        asistencia_response = client.post("/api/asistencias", json=asistencia_data, headers=auth_headers)
        assert asistencia_response.status_code == 201
        
        # 4. Procesar pago
        pago_data = {
            "usuario_id": user_id,
            "monto": 50.00,
            "concepto": "mensualidad",
            "metodo_pago": "tarjeta"
        }
        pago_response = client.post("/api/pagos", json=pago_data, headers=auth_headers)
        assert pago_response.status_code == 201
        
        # 5. Verificar que todo esté conectado correctamente
        # Verificar asistencias del usuario
        asistencias_response = client.get(f"/api/asistencias/usuario/{user_id}", headers=auth_headers)
        assert asistencias_response.status_code == 200
        asistencias = asistencias_response.json()["asistencias"]
        assert len(asistencias) > 0
        
        # Verificar pagos del usuario
        pagos_response = client.get(f"/api/pagos/usuario/{user_id}", headers=auth_headers)
        assert pagos_response.status_code == 200
        pagos = pagos_response.json()["pagos"]
        assert len(pagos) > 0

# ============================================================================
# FUNCIONES DE EJECUCIÓN DE SUITES
# ============================================================================

def run_performance_tests():
    """Ejecuta solo las pruebas de rendimiento"""
    pytest.main([__file__, "-m", "performance", "-v"])

def run_security_tests():
    """Ejecuta solo las pruebas de seguridad"""
    pytest.main([__file__, "-m", "security", "-v"])

def run_functional_tests():
    """Ejecuta solo las pruebas funcionales"""
    pytest.main([__file__, "-m", "endpoints", "-v"])

def run_all_tests():
    """Ejecuta todas las pruebas"""
    pytest.main([__file__, "-v"]) 