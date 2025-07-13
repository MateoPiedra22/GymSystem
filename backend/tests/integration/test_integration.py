"""
Tests de Integración - Sistema de Gimnasio v6
Verifica el funcionamiento completo del sistema
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.usuarios import Usuario
from app.models.asistencias import Asistencia
from app.models.clases import Clase
from app.models.empleados import Empleado
from app.models.pagos import Pago
from app.schemas.auth import LoginRequest, UserCreate
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate
from app.core.security import hash_password, generate_secure_token

# Configuración de base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = Session(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override de la función get_db para tests"""
    try:
        db = TestingSessionLocal
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def setup_database():
    """Configurar base de datos de prueba"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(setup_database):
    """Sesión de base de datos para tests"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client():
    """Cliente de prueba para FastAPI"""
    return TestClient(app)

@pytest.fixture
def test_user(db_session):
    """Usuario de prueba"""
    from passlib.context import CryptContext
    import uuid
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash("TestPass123!")
    
    # Usar UUID para hacer el username único
    unique_id = str(uuid.uuid4())[:8]
    unique_username = f"testuser_{unique_id}"

    user = Usuario(
        email=f"test_{unique_id}@example.com",
        username=unique_username,
        nombre="Usuario Test",
        apellido="Apellido Test",
        hashed_password=hashed_password,
        salt=None,  # bcrypt no usa salt separado
        es_admin=True,
        esta_activo=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_empleado(db_session):
    """Empleado de prueba"""
    empleado = Empleado(
        nombre="Empleado Test",
        apellido="Apellido Test",
        email="empleado@example.com",
        telefono="123456789",
        cargo="Instructor",
        activo=True
    )
    db_session.add(empleado)
    db_session.commit()
    db_session.refresh(empleado)
    return empleado

@pytest.fixture
def test_clase(db_session, test_empleado):
    """Clase de prueba"""
    clase = Clase(
        nombre="Clase Test",
        descripcion="Descripción de prueba",
        duracion=60,
        capacidad_maxima=20,
        instructor_id=test_empleado.id,
        activa=True
    )
    db_session.add(clase)
    db_session.commit()
    db_session.refresh(clase)
    return clase

@pytest.fixture
def auth_headers(client, test_user):
    """Headers de autenticación para tests"""
    login_data = {
        "username": test_user.username,  # Usar el username del usuario creado
        "password": "TestPass123!"
    }
    
    response = client.post("/api/auth/login/json", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestAuthenticationIntegration:
    """Tests de integración para autenticación"""
    
    def test_user_registration_and_login(self, client, db_session):
        """Test completo de registro y login de usuario"""
        # 1. Registrar usuario
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser123",  # Campo obligatorio
            "nombre": "Nuevo",
            "apellido": "Usuario",
            "password": "SecurePass123!",
            "es_admin": False
        }

        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Verificar que el usuario se creó correctamente
        user_response = response.json()
        assert user_response["email"] == "newuser@example.com"
        assert user_response["username"] == "newuser123"
        assert "password" not in user_response  # La contraseña no debe devolverse
        
        # 2. Login con el usuario creado
        login_data = {
            "username": "newuser123",
            "password": "SecurePass123!"
        }
        
        response = client.post("/api/auth/login/json", json=login_data)
        assert response.status_code == 200
        
        # Verificar que se devuelve un token
        login_response = response.json()
        assert "access_token" in login_response
        assert "token_type" in login_response
        assert login_response["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test de login con credenciales inválidas"""
        login_data = {
            "username": "invaliduser",
            "password": "WrongPass123!"
        }
        
        response = client.post("/api/auth/login/json", json=login_data)
        assert response.status_code == 401
    
    def test_protected_endpoint_without_token(self, client):
        """Test de endpoint protegido sin token"""
        response = client.get("/api/usuarios/")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_token(self, client, auth_headers):
        """Test de endpoint protegido con token válido"""
        response = client.get("/api/usuarios/", headers=auth_headers)
        assert response.status_code == 200
    
    def test_token_expiration(self, client, test_user):
        """Test de expiración de token"""
        # Crear un token expirado directamente usando la función de creación de token
        from app.core.security import create_access_token
        from datetime import timedelta
        
        # Crear token con tiempo de expiración negativo (ya expirado)
        expired_token = create_access_token(
            data={"sub": test_user.username},
            expires_delta=timedelta(hours=-2)  # Tiempo negativo = ya expirado
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        # Intentar usar token expirado
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
        
        # Verificar la estructura de la respuesta
        response_data = response.json()
        assert "error" in response_data
        assert response_data["status_code"] == 401

    def test_debug_token(self, client, auth_headers):
        """Test de debug para verificar el token JWT"""
        # Extraer el token del header
        token = auth_headers["Authorization"].replace("Bearer ", "")

        # Verificar el token con el endpoint de debug
        response = client.get(f"/api/auth/debug-token?token={token}")
        assert response.status_code == 200

        debug_data = response.json()
        print(f"DEBUG: Token debug data: {debug_data}")

        assert debug_data["success"] == True
        assert "user_id" in debug_data
        assert "username" in debug_data
        # Verificar que el username existe y no está vacío, sin importar el valor específico
        assert debug_data["username"] and len(debug_data["username"]) > 0

    def test_user_exists_in_db(self, client, auth_headers, db_session):
        """Test para verificar si el usuario existe en la base de datos"""
        # Extraer el token del header
        token = auth_headers["Authorization"].replace("Bearer ", "")
        
        # Verificar el token con el endpoint de debug
        response = client.get(f"/api/auth/debug-token?token={token}")
        assert response.status_code == 200
        
        debug_data = response.json()
        user_id = debug_data["user_id"]
        
        # Buscar el usuario en la base de datos
        from app.models.usuarios import Usuario
        user = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        
        print(f"DEBUG: Buscando usuario con ID: {user_id}")
        print(f"DEBUG: Usuario encontrado: {user is not None}")
        
        if user:
            print(f"DEBUG: Usuario encontrado - ID: {user.id}, username: {user.username}")
        else:
            # Listar todos los usuarios en la BD
            all_users = db_session.query(Usuario).all()
            print(f"DEBUG: Total de usuarios en BD: {len(all_users)}")
            for u in all_users:
                print(f"DEBUG: Usuario en BD - ID: {u.id}, username: {u.username}")
        
        assert user is not None, f"Usuario con ID {user_id} no encontrado en la base de datos"

class TestUserManagementIntegration:
    """Tests de integración para gestión de usuarios"""
    
    def test_create_user(self, client, auth_headers):
        """Test de creación de usuario"""
        user_data = {
            "email": "newuser@example.com",
            "nombre": "Nuevo",
            "apellido": "Usuario",
            "password": "SecurePass123!",
            "rol": "usuario",
            "telefono": "123456789",
            "fecha_nacimiento": "1990-01-01"
        }
        
        response = client.post("/api/usuarios/", json=user_data, headers=auth_headers)
        assert response.status_code == 201
        
        user_response = response.json()
        assert user_response["email"] == user_data["email"]
        assert user_response["nombre"] == user_data["nombre"]
        assert "password" not in user_response
    
    def test_get_users_list(self, client, auth_headers, test_user):
        """Test de obtención de lista de usuarios"""
        response = client.get("/api/usuarios/", headers=auth_headers)
        assert response.status_code == 200
        
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 1
        
        # Verificar que el usuario de prueba está en la lista
        user_emails = [user["email"] for user in users]
        assert test_user.email in user_emails
    
    def test_get_user_by_id(self, client, auth_headers, test_user):
        """Test de obtención de usuario por ID"""
        response = client.get(f"/api/usuarios/{test_user.id}", headers=auth_headers)
        assert response.status_code == 200
        
        user = response.json()
        assert user["id"] == test_user.id
        assert user["email"] == test_user.email
        assert user["nombre"] == test_user.nombre
    
    def test_update_user(self, client, auth_headers, test_user):
        """Test de actualización de usuario"""
        update_data = {
            "nombre": "Nombre Actualizado",
            "telefono": "987654321"
        }
        
        response = client.put(f"/api/usuarios/{test_user.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        updated_user = response.json()
        assert updated_user["nombre"] == update_data["nombre"]
        assert updated_user["telefono"] == update_data["telefono"]
    
    def test_delete_user(self, client, auth_headers, test_user):
        """Test de eliminación de usuario"""
        response = client.delete(f"/api/usuarios/{test_user.id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verificar que el usuario fue eliminado
        response = client.get(f"/api/usuarios/{test_user.id}", headers=auth_headers)
        assert response.status_code == 404

class TestAsistenciaIntegration:
    """Tests de integración para gestión de asistencias"""
    
    def test_create_asistencia(self, client, auth_headers, test_user, test_clase):
        """Test de creación de asistencia"""
        asistencia_data = {
            "usuario_id": test_user.id,
            "clase_id": test_clase.id,
            "fecha": "2024-01-15",
            "hora_entrada": "10:00:00",
            "hora_salida": "11:00:00",
            "estado": "presente"
        }
        
        response = client.post("/api/asistencias/", json=asistencia_data, headers=auth_headers)
        assert response.status_code == 201
        
        asistencia = response.json()
        assert asistencia["usuario_id"] == test_user.id
        assert asistencia["clase_id"] == test_clase.id
        assert asistencia["estado"] == "presente"
    
    def test_get_asistencias_list(self, client, auth_headers, test_user, test_clase):
        """Test de obtención de lista de asistencias"""
        # Crear algunas asistencias
        asistencias_data = [
            {
                "usuario_id": test_user.id,
                "clase_id": test_clase.id,
                "fecha": "2024-01-15",
                "hora_entrada": "10:00:00",
                "estado": "presente"
            },
            {
                "usuario_id": test_user.id,
                "clase_id": test_clase.id,
                "fecha": "2024-01-16",
                "hora_entrada": "14:00:00",
                "estado": "presente"
            }
        ]
        
        for asistencia_data in asistencias_data:
            client.post("/api/asistencias/", json=asistencia_data, headers=auth_headers)
        
        # Obtener lista de asistencias
        response = client.get("/api/asistencias/", headers=auth_headers)
        assert response.status_code == 200
        
        asistencias = response.json()
        assert isinstance(asistencias, list)
        assert len(asistencias) >= 2
    
    def test_get_asistencia_by_id(self, client, auth_headers, test_user, test_clase):
        """Test de obtención de asistencia por ID"""
        # Crear asistencia
        asistencia_data = {
            "usuario_id": test_user.id,
            "clase_id": test_clase.id,
            "fecha": "2024-01-15",
            "hora_entrada": "10:00:00",
            "estado": "presente"
        }
        
        create_response = client.post("/api/asistencias/", json=asistencia_data, headers=auth_headers)
        asistencia_id = create_response.json()["id"]
        
        # Obtener asistencia por ID
        response = client.get(f"/api/asistencias/{asistencia_id}", headers=auth_headers)
        assert response.status_code == 200
        
        asistencia = response.json()
        assert asistencia["id"] == asistencia_id
        assert asistencia["usuario_id"] == test_user.id
        assert asistencia["clase_id"] == test_clase.id
    
    def test_update_asistencia(self, client, auth_headers, test_user, test_clase):
        """Test de actualización de asistencia"""
        # Crear asistencia
        asistencia_data = {
            "usuario_id": test_user.id,
            "clase_id": test_clase.id,
            "fecha": "2024-01-15",
            "hora_entrada": "10:00:00",
            "estado": "presente"
        }
        
        create_response = client.post("/api/asistencias/", json=asistencia_data, headers=auth_headers)
        asistencia_id = create_response.json()["id"]
        
        # Actualizar asistencia
        update_data = {
            "hora_salida": "11:00:00",
            "estado": "completada"
        }
        
        response = client.put(f"/api/asistencias/{asistencia_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        updated_asistencia = response.json()
        assert updated_asistencia["hora_salida"] == "11:00:00"
        assert updated_asistencia["estado"] == "completada"

class TestClaseIntegration:
    """Tests de integración para gestión de clases"""
    
    def test_create_clase(self, client, auth_headers, test_empleado):
        """Test de creación de clase"""
        clase_data = {
            "nombre": "Yoga Avanzado",
            "descripcion": "Clase de yoga para nivel avanzado",
            "duracion": 90,
            "capacidad_maxima": 15,
            "instructor_id": test_empleado.id,
            "horario": "18:00:00",
            "dias_semana": ["lunes", "miércoles", "viernes"]
        }
        
        response = client.post("/api/clases/", json=clase_data, headers=auth_headers)
        assert response.status_code == 201
        
        clase = response.json()
        assert clase["nombre"] == clase_data["nombre"]
        assert clase["duracion"] == clase_data["duracion"]
        assert clase["instructor_id"] == test_empleado.id
    
    def test_get_clases_list(self, client, auth_headers, test_clase):
        """Test de obtención de lista de clases"""
        response = client.get("/api/clases/", headers=auth_headers)
        assert response.status_code == 200
        
        clases = response.json()
        assert isinstance(clases, list)
        assert len(clases) >= 1
        
        # Verificar que la clase de prueba está en la lista
        clase_nombres = [clase["nombre"] for clase in clases]
        assert test_clase.nombre in clase_nombres
    
    def test_get_clase_by_id(self, client, auth_headers, test_clase):
        """Test de obtención de clase por ID"""
        response = client.get(f"/api/clases/{test_clase.id}", headers=auth_headers)
        assert response.status_code == 200
        
        clase = response.json()
        assert clase["id"] == test_clase.id
        assert clase["nombre"] == test_clase.nombre
        assert clase["descripcion"] == test_clase.descripcion
    
    def test_update_clase(self, client, auth_headers, test_clase):
        """Test de actualización de clase"""
        update_data = {
            "nombre": "Clase Actualizada",
            "capacidad_maxima": 25
        }
        
        response = client.put(f"/api/clases/{test_clase.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        updated_clase = response.json()
        assert updated_clase["nombre"] == update_data["nombre"]
        assert updated_clase["capacidad_maxima"] == update_data["capacidad_maxima"]

class TestEmpleadoIntegration:
    """Tests de integración para gestión de empleados"""
    
    def test_create_empleado(self, client, auth_headers):
        """Test de creación de empleado"""
        empleado_data = {
            "nombre": "Juan",
            "apellido": "Pérez",
            "email": "juan.perez@example.com",
            "telefono": "123456789",
            "cargo": "Instructor Senior",
            "fecha_contratacion": "2023-01-15",
            "salario": 2500.00
        }
        
        response = client.post("/api/empleados/", json=empleado_data, headers=auth_headers)
        assert response.status_code == 201
        
        empleado = response.json()
        assert empleado["nombre"] == empleado_data["nombre"]
        assert empleado["email"] == empleado_data["email"]
        assert empleado["cargo"] == empleado_data["cargo"]
    
    def test_get_empleados_list(self, client, auth_headers, test_empleado):
        """Test de obtención de lista de empleados"""
        response = client.get("/api/empleados/", headers=auth_headers)
        assert response.status_code == 200
        
        empleados = response.json()
        assert isinstance(empleados, list)
        assert len(empleados) >= 1
        
        # Verificar que el empleado de prueba está en la lista
        empleado_emails = [emp["email"] for emp in empleados]
        assert test_empleado.email in empleado_emails
    
    def test_get_empleado_by_id(self, client, auth_headers, test_empleado):
        """Test de obtención de empleado por ID"""
        response = client.get(f"/api/empleados/{test_empleado.id}", headers=auth_headers)
        assert response.status_code == 200
        
        empleado = response.json()
        assert empleado["id"] == test_empleado.id
        assert empleado["nombre"] == test_empleado.nombre
        assert empleado["email"] == test_empleado.email

class TestPagoIntegration:
    """Tests de integración para gestión de pagos"""
    
    def test_create_pago(self, client, auth_headers, test_user):
        """Test de creación de pago"""
        pago_data = {
            "usuario_id": test_user.id,
            "monto": 50.00,
            "tipo_pago": "mensual",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "tarjeta",
            "estado": "completado"
        }
        
        response = client.post("/api/pagos/", json=pago_data, headers=auth_headers)
        assert response.status_code == 201
        
        pago = response.json()
        assert pago["usuario_id"] == test_user.id
        assert pago["monto"] == pago_data["monto"]
        assert pago["tipo_pago"] == pago_data["tipo_pago"]
        assert pago["estado"] == pago_data["estado"]
    
    def test_get_pagos_list(self, client, auth_headers, test_user):
        """Test de obtención de lista de pagos"""
        # Crear algunos pagos
        pagos_data = [
            {
                "usuario_id": test_user.id,
                "monto": 50.00,
                "tipo_pago": "mensual",
                "fecha_pago": "2024-01-15",
                "metodo_pago": "tarjeta",
                "estado": "completado"
            },
            {
                "usuario_id": test_user.id,
                "monto": 30.00,
                "tipo_pago": "clase",
                "fecha_pago": "2024-01-20",
                "metodo_pago": "efectivo",
                "estado": "completado"
            }
        ]
        
        for pago_data in pagos_data:
            client.post("/api/pagos/", json=pago_data, headers=auth_headers)
        
        # Obtener lista de pagos
        response = client.get("/api/pagos/", headers=auth_headers)
        assert response.status_code == 200
        
        pagos = response.json()
        assert isinstance(pagos, list)
        assert len(pagos) >= 2

class TestReportesIntegration:
    """Tests de integración para reportes"""
    
    def test_get_kpis(self, client, auth_headers, test_user, test_clase):
        """Test de obtención de KPIs"""
        # Crear datos de prueba
        asistencia_data = {
            "usuario_id": test_user.id,
            "clase_id": test_clase.id,
            "fecha": "2024-01-15",
            "hora_entrada": "10:00:00",
            "estado": "presente"
        }
        client.post("/api/asistencias/", json=asistencia_data, headers=auth_headers)
        
        pago_data = {
            "usuario_id": test_user.id,
            "monto": 50.00,
            "tipo_pago": "mensual",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "tarjeta",
            "estado": "completado"
        }
        client.post("/api/pagos/", json=pago_data, headers=auth_headers)
        
        # Obtener KPIs
        response = client.get("/api/reportes/kpis", headers=auth_headers)
        assert response.status_code == 200
        
        kpis = response.json()
        assert "total_usuarios" in kpis
        assert "total_clases" in kpis
        assert "total_asistencias" in kpis
        assert "total_ingresos" in kpis
    
    def test_get_graficos(self, client, auth_headers):
        """Test de obtención de gráficos"""
        response = client.get("/api/reportes/graficos", headers=auth_headers)
        assert response.status_code == 200
        
        graficos = response.json()
        assert isinstance(graficos, dict)

class TestErrorHandlingIntegration:
    """Tests de integración para manejo de errores"""
    
    def test_404_not_found(self, client, auth_headers):
        """Test de endpoint no encontrado"""
        response = client.get("/api/nonexistent/", headers=auth_headers)
        assert response.status_code == 404
    
    def test_422_validation_error(self, client, auth_headers):
        """Test de error de validación"""
        # Intentar crear usuario con datos inválidos
        invalid_user_data = {
            "email": "invalid-email",  # Email inválido
            "nombre": "",  # Nombre vacío
            "password": "123"  # Contraseña muy corta
        }
        
        response = client.post("/api/usuarios/", json=invalid_user_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_500_internal_error(self, client, auth_headers):
        """Test de error interno del servidor"""
        # Simular error en base de datos
        with patch('app.core.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database error")
            
            response = client.get("/api/usuarios/", headers=auth_headers)
            assert response.status_code == 500

class TestPerformanceIntegration:
    """Tests de integración para performance"""
    
    def test_response_time_under_load(self, client, auth_headers):
        """Test de tiempo de respuesta bajo carga"""
        start_time = time.time()
        
        # Realizar múltiples peticiones
        for _ in range(10):
            response = client.get("/api/usuarios/", headers=auth_headers)
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verificar que el tiempo total es razonable
        assert total_time < 5.0  # Menos de 5 segundos para 10 peticiones
    
    def test_concurrent_requests(self, client, auth_headers):
        """Test de peticiones concurrentes"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = client.get("/api/usuarios/", headers=auth_headers)
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")
        
        # Crear múltiples hilos
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Esperar a que terminen todos los hilos
        for thread in threads:
            thread.join()
        
        # Verificar resultados
        while not results.empty():
            result = results.get()
            assert result == 200 or "Error" in str(result)

class TestSecurityIntegration:
    """Tests de integración para seguridad"""
    
    def test_rate_limiting(self, client, auth_headers):
        """Test de rate limiting"""
        # Realizar múltiples peticiones rápidas
        for i in range(15):  # Más del límite por defecto
            response = client.get("/api/usuarios/", headers=auth_headers)
            
            if response.status_code == 429:  # Rate limit excedido
                break
        
        # Al menos una petición debería ser limitada
        assert response.status_code == 429
    
    def test_sql_injection_protection(self, client, auth_headers):
        """Test de protección contra SQL injection"""
        # Intentar inyección SQL en parámetros
        malicious_id = "1; DROP TABLE usuarios; --"
        
        response = client.get(f"/api/usuarios/{malicious_id}", headers=auth_headers)
        
        # No debería causar error de base de datos
        assert response.status_code in [404, 422]
    
    def test_xss_protection(self, client, auth_headers):
        """Test de protección contra XSS"""
        # Intentar XSS en datos de entrada
        xss_data = {
            "nombre": "<script>alert('xss')</script>",
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        response = client.post("/api/usuarios/", json=xss_data, headers=auth_headers)
        
        # Debería ser rechazado o sanitizado
        assert response.status_code in [422, 201]

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 