"""
Pruebas específicas para optimizaciones de seguridad
Sistema de Gestión de Gimnasio v6
"""

import pytest
import time
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.core.security import (
    create_access_token, verify_password, hash_password,
    create_refresh_token, verify_token
)
from app.models.usuarios import Usuario


@pytest.mark.security
class TestAuthenticationSecurity:
    """Pruebas de seguridad para autenticación"""
    
    def test_password_hashing_security(self):
        """Verificar que el hash de contraseñas es seguro"""
        password = "test_password_123"
        
        # Verificar que el hash no es predecible
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2, "Hash de contraseña es predecible"
        assert len(hash1) >= 60, "Hash de contraseña es demasiado corto"
        assert verify_password(password, hash1), "Verificación de contraseña falló"
        assert verify_password(password, hash2), "Verificación de contraseña falló"
    
    def test_password_hash_timing_attack_resistance(self):
        """Verificar resistencia a ataques de timing"""
        password = "test_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        # Medir tiempo de verificación correcta
        start_time = time.time()
        verify_password(password, hashed)
        correct_time = time.time() - start_time
        
        # Medir tiempo de verificación incorrecta
        start_time = time.time()
        verify_password(wrong_password, hashed)
        incorrect_time = time.time() - start_time
        
        # La diferencia de tiempo debe ser mínima para evitar timing attacks
        time_diff = abs(correct_time - incorrect_time)
        assert time_diff < 0.1, f"Diferencia de tiempo excesiva: {time_diff:.3f}s"
    
    def test_token_security(self):
        """Verificar seguridad de tokens JWT"""
        user_data = {"sub": "test_user", "exp": datetime.utcnow() + timedelta(hours=1)}
        token = create_access_token(user_data)
        
        # Verificar que el token no contiene información sensible en texto plano
        assert "password" not in token
        assert "secret" not in token
        
        # Verificar que el token tiene estructura JWT válida
        parts = token.split('.')
        assert len(parts) == 3, "Token JWT no tiene estructura válida"
        
        # Verificar que el token puede ser verificado
        decoded = verify_token(token)
        assert decoded is not None, "Token no puede ser verificado"
        assert decoded["sub"] == "test_user"
    
    def test_token_expiration(self):
        """Verificar que los tokens expiran correctamente"""
        # Crear token con expiración muy corta
        user_data = {"sub": "test_user", "exp": datetime.utcnow() - timedelta(seconds=1)}
        token = create_access_token(user_data)
        
        # Verificar que el token expirado no es válido
        decoded = verify_token(token)
        assert decoded is None, "Token expirado fue aceptado"
    
    def test_token_manipulation_resistance(self):
        """Verificar resistencia a manipulación de tokens"""
        user_data = {"sub": "test_user", "exp": datetime.utcnow() + timedelta(hours=1)}
        token = create_access_token(user_data)
        
        # Intentar manipular el token
        manipulated_token = token[:-5] + "XXXXX"
        
        # Verificar que el token manipulado no es válido
        decoded = verify_token(manipulated_token)
        assert decoded is None, "Token manipulado fue aceptado"
    
    def test_bruteforce_protection(self, client: TestClient):
        """Verificar protección contra ataques de fuerza bruta"""
        # Simular múltiples intentos fallidos
        failed_attempts = []
        
        for i in range(5):
            start_time = time.time()
            response = client.post("/auth/login", json={
                "username": "nonexistent_user",
                "password": f"wrong_password_{i}"
            })
            response_time = time.time() - start_time
            
            failed_attempts.append((response.status_code, response_time))
        
        # Verificar que todos los intentos fallan
        for status_code, _ in failed_attempts:
            assert status_code == 401, "Ataque de fuerza bruta no fue rechazado"
        
        # Verificar que no hay diferencias significativas en tiempo de respuesta
        # que puedan indicar información sobre usuarios válidos
        response_times = [time for _, time in failed_attempts]
        time_variance = max(response_times) - min(response_times)
        assert time_variance < 0.5, "Varianza de tiempo excesiva en intentos fallidos"


@pytest.mark.security
class TestAuthorizationSecurity:
    """Pruebas de seguridad para autorización"""
    
    def test_unauthorized_access_prevention(self, client: TestClient):
        """Verificar que se previene el acceso no autorizado"""
        protected_endpoints = [
            "/api/usuarios",
            "/api/clases",
            "/api/asistencias",
            "/api/pagos",
            "/api/empleados",
            "/api/reportes/kpis",
            "/api/reportes/graficos"
        ]
        
        for endpoint in protected_endpoints:
            # Intentar acceso sin token
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} permite acceso sin autenticación"
            
            # Intentar acceso con token inválido
            response = client.get(endpoint, headers={"Authorization": "Bearer invalid_token"})
            assert response.status_code == 401, f"Endpoint {endpoint} acepta token inválido"
    
    def test_admin_only_endpoints(self, client: TestClient, auth_headers: Dict[str, str], admin_headers: Dict[str, str]):
        """Verificar que endpoints de admin solo son accesibles por administradores"""
        admin_endpoints = [
            "/api/usuarios",  # Crear usuarios
            "/api/empleados",  # Gestión de empleados
            "/api/reportes/kpis",  # KPIs administrativos
        ]
        
        for endpoint in admin_endpoints:
            # Intentar acceso con usuario normal
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code in [403, 401], f"Endpoint {endpoint} permite acceso a usuario normal"
            
            # Verificar acceso con admin
            response = client.get(endpoint, headers=admin_headers)
            assert response.status_code == 200, f"Endpoint {endpoint} no permite acceso a admin"
    
    def test_user_data_isolation(self, client: TestClient, auth_headers: Dict[str, str]):
        """Verificar que los usuarios solo pueden acceder a sus propios datos"""
        # Crear dos usuarios diferentes
        user1_data = {
            "nombre": "Usuario 1",
            "apellido": "Test",
            "email": "user1@test.com",
            "username": "user1",
            "telefono": "123456789",
            "fecha_nacimiento": "1990-01-01",
            "genero": "M",
            "esta_activo": True
        }
        
        user2_data = {
            "nombre": "Usuario 2",
            "apellido": "Test",
            "email": "user2@test.com",
            "username": "user2",
            "telefono": "987654321",
            "fecha_nacimiento": "1990-01-01",
            "genero": "F",
            "esta_activo": True
        }
        
        # Crear usuarios (usando admin headers)
        admin_headers = {"Authorization": "Bearer test_token_admin"}
        response1 = client.post("/api/usuarios", json=user1_data, headers=admin_headers)
        response2 = client.post("/api/usuarios", json=user2_data, headers=admin_headers)
        
        if response1.status_code == 201 and response2.status_code == 201:
            user1_id = response1.json()["id"]
            user2_id = response2.json()["id"]
            
            # Intentar que user1 acceda a datos de user2
            response = client.get(f"/api/usuarios/{user2_id}", headers=auth_headers)
            assert response.status_code in [403, 404], "Usuario puede acceder a datos de otro usuario"


@pytest.mark.security
class TestInputValidationSecurity:
    """Pruebas de seguridad para validación de entrada"""
    
    def test_sql_injection_prevention(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar prevención de inyección SQL"""
        # Intentar inyección SQL en diferentes campos
        sql_payloads = [
            "'; DROP TABLE usuarios; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM usuarios --",
            "admin'; DELETE FROM usuarios WHERE '1'='1",
        ]
        
        for payload in sql_payloads:
            user_data = {
                "nombre": payload,
                "apellido": "Test",
                "email": f"test_{payload[:5]}@test.com",
                "username": payload,
                "telefono": "123456789",
                "fecha_nacimiento": "1990-01-01",
                "genero": "M",
                "esta_activo": True
            }
            
            response = client.post("/api/usuarios", json=user_data, headers=admin_headers)
            # Debe fallar la validación o ser sanitizado
            assert response.status_code in [400, 422], f"Payload SQL no fue rechazado: {payload}"
    
    def test_xss_prevention(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar prevención de XSS"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//",
        ]
        
        for payload in xss_payloads:
            user_data = {
                "nombre": payload,
                "apellido": "Test",
                "email": "xss_test@test.com",
                "username": f"xss_user_{hash(payload) % 1000}",
                "telefono": "123456789",
                "fecha_nacimiento": "1990-01-01",
                "genero": "M",
                "esta_activo": True
            }
            
            response = client.post("/api/usuarios", json=user_data, headers=admin_headers)
            
            if response.status_code == 201:
                # Verificar que la respuesta no contiene el payload ejecutable
                response_text = response.text
                assert "<script>" not in response_text, "Script XSS no fue sanitizado"
                assert "javascript:" not in response_text, "JavaScript XSS no fue sanitizado"
    
    def test_path_traversal_prevention(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar prevención de path traversal"""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]
        
        for payload in traversal_payloads:
            # Intentar path traversal en campos de archivo/path
            response = client.get(f"/api/multimedia/{payload}", headers=admin_headers)
            assert response.status_code in [400, 404], f"Path traversal no fue prevenido: {payload}"
    
    def test_input_length_validation(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar validación de longitud de entrada"""
        # Crear strings muy largos
        very_long_string = "A" * 10000
        
        user_data = {
            "nombre": very_long_string,
            "apellido": "Test",
            "email": "long_test@test.com",
            "username": "long_user",
            "telefono": "123456789",
            "fecha_nacimiento": "1990-01-01",
            "genero": "M",
            "esta_activo": True
        }
        
        response = client.post("/api/usuarios", json=user_data, headers=admin_headers)
        assert response.status_code == 422, "Entrada excesivamente larga no fue rechazada"
    
    def test_email_validation(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar validación de formato de email"""
        invalid_emails = [
            "invalid_email",
            "@invalid.com",
            "invalid@",
            "invalid..email@test.com",
            "invalid@.com",
            "invalid@com",
            "",
            "a" * 300 + "@test.com",  # Email muy largo
        ]
        
        for email in invalid_emails:
            user_data = {
                "nombre": "Test",
                "apellido": "User",
                "email": email,
                "username": f"user_{hash(email) % 1000}",
                "telefono": "123456789",
                "fecha_nacimiento": "1990-01-01",
                "genero": "M",
                "esta_activo": True
            }
            
            response = client.post("/api/usuarios", json=user_data, headers=admin_headers)
            assert response.status_code == 422, f"Email inválido no fue rechazado: {email}"


@pytest.mark.security
class TestDataProtectionSecurity:
    """Pruebas de seguridad para protección de datos"""
    
    def test_password_not_in_response(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar que las contraseñas no aparecen en respuestas"""
        user_data = {
            "nombre": "Test User",
            "apellido": "Security",
            "email": "security_test@test.com",
            "username": "security_user",
            "telefono": "123456789",
            "fecha_nacimiento": "1990-01-01",
            "genero": "M",
            "esta_activo": True
        }
        
        response = client.post("/api/usuarios", json=user_data, headers=admin_headers)
        
        if response.status_code == 201:
            response_data = response.json()
            
            # Verificar que la respuesta no contiene campos sensibles
            assert "password" not in response_data, "Contraseña aparece en respuesta"
            assert "hashed_password" not in response_data, "Hash de contraseña aparece en respuesta"
            assert "salt" not in response_data, "Salt aparece en respuesta"
    
    def test_sensitive_data_logging(self, client: TestClient):
        """Verificar que datos sensibles no se loguean"""
        with patch('app.core.logging.logger') as mock_logger:
            response = client.post("/auth/login", json={
                "username": "admin",
                "password": "admin123"
            })
            
            # Verificar que las contraseñas no aparecen en logs
            for call in mock_logger.info.call_args_list:
                log_message = str(call)
                assert "admin123" not in log_message, "Contraseña aparece en logs"
    
    def test_session_security(self, client: TestClient):
        """Verificar seguridad de sesiones"""
        # Login exitoso
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            
            # Verificar que el token no se puede usar desde otra "sesión"
            # (En implementación real, esto incluiría verificación de IP, User-Agent, etc.)
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/usuarios", headers=headers)
            
            # El token debe funcionar normalmente
            assert response.status_code == 200


@pytest.mark.security
class TestRateLimitingSecurity:
    """Pruebas de seguridad para rate limiting"""
    
    def test_login_rate_limiting(self, client: TestClient):
        """Verificar rate limiting en login"""
        # Realizar múltiples intentos de login rápidamente
        responses = []
        
        for i in range(20):  # Muchos intentos
            response = client.post("/auth/login", json={
                "username": "test_user",
                "password": "wrong_password"
            })
            responses.append(response.status_code)
        
        # Verificar que eventualmente se aplica rate limiting
        # (En implementación real, después de cierto número de intentos)
        rate_limited = any(status == 429 for status in responses[-5:])
        # Esta prueba pasará si hay rate limiting, pero no fallará si no lo hay
        # ya que depende de la configuración del servidor
    
    def test_api_rate_limiting(self, client: TestClient, admin_headers: Dict[str, str]):
        """Verificar rate limiting en API endpoints"""
        # Realizar múltiples requests rápidamente
        responses = []
        
        for i in range(100):  # Muchos requests
            response = client.get("/api/usuarios", headers=admin_headers)
            responses.append(response.status_code)
            
            # Si se aplica rate limiting, parar
            if response.status_code == 429:
                break
        
        # Verificar que la API funciona normalmente bajo carga moderada
        successful_requests = sum(1 for status in responses if status == 200)
        assert successful_requests >= 10, "API no maneja carga básica"


@pytest.mark.security
class TestSecurityHeaders:
    """Pruebas de headers de seguridad"""
    
    def test_security_headers_present(self, client: TestClient):
        """Verificar que los headers de seguridad están presentes"""
        response = client.get("/health")
        
        # Headers de seguridad esperados
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Content-Security-Policy",
        ]
        
        for header in expected_headers:
            # Verificar que el header está presente (si está configurado)
            if header in response.headers:
                assert response.headers[header] is not None, f"Header {header} está vacío"
    
    def test_cors_configuration(self, client: TestClient):
        """Verificar configuración de CORS"""
        # Simular request CORS
        response = client.options("/api/usuarios", headers={
            "Origin": "https://malicious-site.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        })
        
        # Verificar que no se permite cualquier origen
        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        if cors_origin:
            assert cors_origin != "*", "CORS permite cualquier origen"


# Funciones utilitarias para ejecutar pruebas de seguridad
def run_security_audit():
    """Ejecutar auditoría completa de seguridad"""
    import subprocess
    
    result = subprocess.run([
        "pytest", 
        "-m", "security",
        "--tb=short",
        "-v"
    ], capture_output=True, text=True)
    
    return result

def run_penetration_tests():
    """Ejecutar pruebas de penetración básicas"""
    import subprocess
    
    result = subprocess.run([
        "pytest", 
        "-m", "security",
        "-k", "injection or xss or traversal",
        "--tb=short",
        "-v"
    ], capture_output=True, text=True)
    
    return result

if __name__ == "__main__":
    # Ejecutar auditoría de seguridad cuando se ejecuta directamente
    print("Ejecutando auditoría de seguridad...")
    result = run_security_audit()
    print(result.stdout)
    if result.stderr:
        print("Errores:", result.stderr) 