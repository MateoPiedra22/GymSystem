"""
Tests de Seguridad - Sistema de Gimnasio v6
Verifica todas las funcionalidades de seguridad implementadas
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session

from app.core.security import (
    SecurityConfig,
    AdvancedRateLimiter,
    PasswordValidator,
    FileValidator,
    SecurityAuditor,
    SecurityMiddleware,
    generate_secure_token,
    hash_password,
    verify_password,
    sanitize_filename
)
from app.main import app
from app.core.database import get_db
from app.models.usuarios import Usuario
from app.schemas.auth import LoginRequest

# Configuración de tests
@pytest.fixture
def security_config():
    """Configuración de seguridad para tests"""
    return SecurityConfig(
        RATE_LIMIT_REQUESTS=10,
        RATE_LIMIT_WINDOW=60,
        MAX_LOGIN_ATTEMPTS=3,
        LOGIN_LOCKOUT_TIME=300,
        MIN_PASSWORD_LENGTH=8,
        MAX_FILE_SIZE=1024 * 1024,  # 1MB
        ALLOWED_FILE_TYPES=["jpg", "png", "pdf"]
    )

@pytest.fixture
def rate_limiter(security_config):
    """Instancia de rate limiter para tests"""
    return AdvancedRateLimiter(security_config)

@pytest.fixture
def password_validator(security_config):
    """Instancia de validador de contraseñas para tests"""
    return PasswordValidator(security_config)

@pytest.fixture
def file_validator(security_config):
    """Instancia de validador de archivos para tests"""
    return FileValidator(security_config)

@pytest.fixture
def security_auditor(security_config):
    """Instancia de auditor de seguridad para tests"""
    return SecurityAuditor(security_config)

@pytest.fixture
def mock_request():
    """Request mock para tests"""
    request = Mock(spec=Request)
    request.headers = {
        "User-Agent": "test-agent",
        "X-Forwarded-For": "192.168.1.1",
        "X-Request-ID": "test-request-id"
    }
    request.client = Mock()
    request.client.host = "192.168.1.1"
    request.method = "GET"
    request.url.path = "/test"
    return request

class TestSecurityConfig:
    """Tests para la configuración de seguridad"""
    
    def test_security_config_defaults(self):
        """Verificar valores por defecto de la configuración"""
        config = SecurityConfig()
        
        assert config.RATE_LIMIT_REQUESTS == 100
        assert config.RATE_LIMIT_WINDOW == 60
        assert config.MAX_LOGIN_ATTEMPTS == 5
        assert config.MIN_PASSWORD_LENGTH == 12
        assert config.ENABLE_COMPRESSION is True
    
    def test_security_config_custom(self):
        """Verificar configuración personalizada"""
        config = SecurityConfig(
            RATE_LIMIT_REQUESTS=50,
            MAX_LOGIN_ATTEMPTS=3,
            MIN_PASSWORD_LENGTH=10
        )
        
        assert config.RATE_LIMIT_REQUESTS == 50
        assert config.MAX_LOGIN_ATTEMPTS == 3
        assert config.MIN_PASSWORD_LENGTH == 10
    
    def test_security_config_ip_validation(self):
        """Verificar validación de IPs"""
        config = SecurityConfig(
            ALLOWED_IPS=["192.168.1.1", "10.0.0.1"],
            BLOCKED_IPS=["192.168.1.100"]
        )
        
        assert "192.168.1.1" in config.ALLOWED_IPS
        assert "192.168.1.100" in config.BLOCKED_IPS
    
    def test_security_config_invalid_ip(self):
        """Verificar que IPs inválidas generen error"""
        with pytest.raises(ValueError):
            SecurityConfig(ALLOWED_IPS=["invalid-ip"])

class TestAdvancedRateLimiter:
    """Tests para el rate limiter avanzado"""
    
    def test_rate_limiter_initialization(self, rate_limiter):
        """Verificar inicialización del rate limiter"""
        assert rate_limiter.config.RATE_LIMIT_REQUESTS == 10
        assert len(rate_limiter.requests) == 0
        assert len(rate_limiter.blocked_ips) == 0
    
    def test_rate_limiter_normal_request(self, rate_limiter, mock_request):
        """Verificar que peticiones normales no sean limitadas"""
        is_limited, info = rate_limiter.is_rate_limited(mock_request)
        
        assert is_limited is False
        assert info == {}
    
    def test_rate_limiter_exceed_limit(self, rate_limiter, mock_request):
        """Verificar que se limite cuando se excede el límite"""
        # Simular múltiples peticiones
        for _ in range(10):
            rate_limiter.is_rate_limited(mock_request)
        
        # La siguiente petición debe ser limitada
        is_limited, info = rate_limiter.is_rate_limited(mock_request)
        
        assert is_limited is True
        assert "Rate limit excedido" in info["reason"]
        assert "retry_after" in info
    
    def test_rate_limiter_window_expiry(self, rate_limiter, mock_request):
        """Verificar que el rate limit se resetee después del tiempo de ventana"""
        # Simular peticiones hasta el límite
        for _ in range(10):
            rate_limiter.is_rate_limited(mock_request)
        
        # Verificar que está limitado
        is_limited, _ = rate_limiter.is_rate_limited(mock_request)
        assert is_limited is True
        
        # Simular paso del tiempo (más de 60 segundos)
        with patch('time.time') as mock_time:
            mock_time.return_value = time.time() + 70
            
            # Ahora debería permitir peticiones nuevamente
            is_limited, _ = rate_limiter.is_rate_limited(mock_request)
            assert is_limited is False
    
    def test_rate_limiter_login_attempts(self, rate_limiter, mock_request):
        """Verificar bloqueo por intentos de login fallidos"""
        # Simular intentos de login fallidos
        for _ in range(3):
            is_blocked, info = rate_limiter.record_login_attempt(mock_request, False)
            assert is_blocked is False
        
        # El cuarto intento debe bloquear
        is_blocked, info = rate_limiter.record_login_attempt(mock_request, False)
        assert is_blocked is True
        assert "Demasiados intentos" in info["reason"]
        assert info["attempts"] == 4
    
    def test_rate_limiter_login_success_reset(self, rate_limiter, mock_request):
        """Verificar que el login exitoso resetea los contadores"""
        # Simular algunos intentos fallidos
        for _ in range(2):
            rate_limiter.record_login_attempt(mock_request, False)
        
        # Login exitoso
        is_blocked, info = rate_limiter.record_login_attempt(mock_request, True)
        assert is_blocked is False
        
        # Verificar que los contadores se resetean
        attempts = rate_limiter.ip_attempts[mock_request.client.host]
        assert attempts["count"] == 0
        assert attempts["first_attempt"] is None
    
    def test_rate_limiter_ip_detection(self, rate_limiter):
        """Verificar detección correcta de IP del cliente"""
        # Test con X-Forwarded-For
        request = Mock(spec=Request)
        request.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        request.client = None
        
        ip = rate_limiter._get_client_ip(request)
        assert ip == "10.0.0.1"
        
        # Test con X-Real-IP
        request.headers = {"X-Real-IP": "172.16.0.1"}
        ip = rate_limiter._get_client_ip(request)
        assert ip == "172.16.0.1"
        
        # Test con client.host
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.100"
        ip = rate_limiter._get_client_ip(request)
        assert ip == "192.168.1.100"

class TestPasswordValidator:
    """Tests para el validador de contraseñas"""
    
    def test_password_validator_initialization(self, password_validator):
        """Verificar inicialización del validador"""
        assert password_validator.config.MIN_PASSWORD_LENGTH == 8
        assert password_validator.config.REQUIRE_SPECIAL_CHARS is True
    
    def test_password_validator_valid_password(self, password_validator):
        """Verificar contraseña válida"""
        password = "SecurePass123!"
        is_valid, errors = password_validator.validate_password(password)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_password_validator_too_short(self, password_validator):
        """Verificar contraseña demasiado corta"""
        password = "Short1!"
        is_valid, errors = password_validator.validate_password(password)
        
        assert is_valid is False
        assert any("8 caracteres" in error for error in errors)
    
    def test_password_validator_no_special_chars(self, password_validator):
        """Verificar contraseña sin caracteres especiales"""
        password = "SecurePass123"
        is_valid, errors = password_validator.validate_password(password)
        
        assert is_valid is False
        assert any("carácter especial" in error for error in errors)
    
    def test_password_validator_no_numbers(self, password_validator):
        """Verificar contraseña sin números"""
        password = "SecurePass!"
        is_valid, errors = password_validator.validate_password(password)
        
        assert is_valid is False
        assert any("número" in error for error in errors)
    
    def test_password_validator_no_uppercase(self, password_validator):
        """Verificar contraseña sin mayúsculas"""
        password = "securepass123!"
        is_valid, errors = password_validator.validate_password(password)
        
        assert is_valid is False
        assert any("mayúscula" in error for error in errors)
    
    def test_password_validator_no_lowercase(self, password_validator):
        """Verificar contraseña sin minúsculas"""
        password = "SECUREPASS123!"
        is_valid, errors = password_validator.validate_password(password)
        
        assert is_valid is False
        assert any("minúscula" in error for error in errors)
    
    def test_password_validator_common_password(self, password_validator):
        """Verificar contraseña común"""
        password = "password123"
        is_valid, errors = password_validator.validate_password(password)
        
        assert is_valid is False
        assert any("común" in error for error in errors)
    
    def test_password_validator_repetitive_patterns(self, password_validator):
        """Verificar patrones repetitivos"""
        password = "aaa123!"
        is_valid, errors = password_validator.validate_password(password)
        
        assert is_valid is False
        assert any("repetitivos" in error for error in errors)
    
    def test_password_validator_history_check(self, password_validator):
        """Verificar validación contra historial"""
        password = "NewPass123!"
        history = ["OldPass123!", "NewPass123!"]
        
        is_valid, errors = password_validator.validate_password(password, history)
        
        assert is_valid is False
        assert any("anterior" in error for error in errors)

class TestFileValidator:
    """Tests para el validador de archivos"""
    
    def test_file_validator_initialization(self, file_validator):
        """Verificar inicialización del validador"""
        assert file_validator.config.MAX_FILE_SIZE == 1024 * 1024
        assert "jpg" in file_validator.config.ALLOWED_FILE_TYPES
    
    def test_file_validator_valid_image(self, file_validator):
        """Verificar archivo de imagen válido"""
        # Simular contenido de imagen JPEG
        content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
        filename = "test.jpg"
        content_type = "image/jpeg"
        
        is_valid, errors = file_validator.validate_file(content, filename, content_type)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_file_validator_file_too_large(self, file_validator):
        """Verificar archivo demasiado grande"""
        content = b"x" * (2 * 1024 * 1024)  # 2MB
        filename = "large.jpg"
        content_type = "image/jpeg"
        
        is_valid, errors = file_validator.validate_file(content, filename, content_type)
        
        assert is_valid is False
        assert any("tamaño máximo" in error for error in errors)
    
    def test_file_validator_invalid_extension(self, file_validator):
        """Verificar extensión no permitida"""
        content = b"test content"
        filename = "test.exe"
        content_type = "application/octet-stream"
        
        is_valid, errors = file_validator.validate_file(content, filename, content_type)
        
        assert is_valid is False
        assert any("no permitido" in error for error in errors)
    
    def test_file_validator_malicious_content(self, file_validator):
        """Verificar detección de contenido malicioso"""
        content = b'<script>alert("xss")</script>'
        filename = "test.html"
        content_type = "text/html"
        
        is_valid, errors = file_validator.validate_file(content, filename, content_type)
        
        assert is_valid is False
        assert any("malicioso" in error for error in errors)
    
    def test_file_validator_magic_bytes_validation(self, file_validator):
        """Verificar validación de magic bytes"""
        # Archivo PNG con magic bytes incorrectos
        content = b'PNG\x89\x0a\x1a\x0a'  # Magic bytes incorrectos
        filename = "fake.png"
        content_type = "image/png"
        
        is_valid, errors = file_validator.validate_file(content, filename, content_type)
        
        assert is_valid is False
        assert any("no coincide" in error for error in errors)

class TestSecurityAuditor:
    """Tests para el auditor de seguridad"""
    
    def test_security_auditor_initialization(self, security_auditor):
        """Verificar inicialización del auditor"""
        assert security_auditor.config.AUDIT_LOG_ENABLED is True
        assert "password" in security_auditor.config.SENSITIVE_FIELDS
    
    def test_security_auditor_log_event(self, security_auditor, mock_request):
        """Verificar logging de eventos de seguridad"""
        with patch.object(security_auditor.logger, 'info') as mock_log:
            security_auditor.log_security_event(
                "LOGIN_ATTEMPT",
                {"username": "test", "success": False},
                mock_request
            )
            
            mock_log.assert_called_once()
            log_call = mock_log.call_args[0][0]
            assert "LOGIN_ATTEMPT" in log_call
    
    def test_security_auditor_sanitize_data(self, security_auditor):
        """Verificar sanitización de datos sensibles"""
        data = {
            "username": "test",
            "password": "secret123",
            "token": "jwt_token",
            "normal_field": "value"
        }
        
        sanitized = security_auditor._sanitize_data(data)
        
        assert sanitized["username"] == "test"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["token"] == "***REDACTED***"
        assert sanitized["normal_field"] == "value"
    
    def test_security_auditor_get_client_ip(self, security_auditor):
        """Verificar obtención de IP del cliente"""
        request = Mock(spec=Request)
        request.headers = {"X-Forwarded-For": "10.0.0.1"}
        request.client = None
        
        ip = security_auditor._get_client_ip(request)
        assert ip == "10.0.0.1"

class TestSecurityMiddleware:
    """Tests para el middleware de seguridad"""
    
    def test_security_middleware_initialization(self, security_config):
        """Verificar inicialización del middleware"""
        middleware = SecurityMiddleware(security_config)
        assert middleware.config == security_config
    
    @pytest.mark.asyncio
    async def test_security_middleware_normal_request(self, security_config, mock_request):
        """Verificar que peticiones normales pasen el middleware"""
        middleware = SecurityMiddleware(security_config)
        
        # Mock de la función call_next
        async def mock_call_next(request):
            response = Mock()
            response.status_code = 200
            response.headers = {}
            return response
        
        response = await middleware(mock_request, mock_call_next)
        
        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
    
    @pytest.mark.asyncio
    async def test_security_middleware_blocked_ip(self, security_config, mock_request):
        """Verificar bloqueo de IPs en lista negra"""
        security_config.BLOCKED_IPS = ["192.168.1.1"]
        middleware = SecurityMiddleware(security_config)
        
        async def mock_call_next(request):
            return Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware(mock_request, mock_call_next)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_security_middleware_blocked_user_agent(self, security_config):
        """Verificar bloqueo de User-Agent sospechoso"""
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "bot"}
        request.client = Mock()
        request.client.host = "192.168.1.2"
        request.method = "GET"
        request.url.path = "/test"
        
        security_config.BLOCKED_USER_AGENTS = ["bot"]
        middleware = SecurityMiddleware(security_config)
        
        async def mock_call_next(request):
            return Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware(request, mock_call_next)
        
        assert exc_info.value.status_code == 403

class TestSecurityUtilities:
    """Tests para utilidades de seguridad"""
    
    def test_generate_secure_token(self):
        """Verificar generación de tokens seguros"""
        token1 = generate_secure_token(32)
        token2 = generate_secure_token(32)
        
        assert len(token1) == 43  # Base64 encoding de 32 bytes
        assert len(token2) == 43
        assert token1 != token2  # Tokens únicos
    
    def test_hash_password(self):
        """Verificar hashing de contraseñas"""
        password = "testpassword123"
        hashed, salt = hash_password(password)
        
        assert len(hashed) == 64  # SHA256 hex
        assert len(salt) == 32  # 16 bytes en hex
        assert hashed != password  # Contraseña hasheada
    
    def test_verify_password(self):
        """Verificar verificación de contraseñas"""
        password = "testpassword123"
        hashed, salt = hash_password(password)
        
        # Verificar contraseña correcta
        assert verify_password(password, hashed, salt) is True
        
        # Verificar contraseña incorrecta
        assert verify_password("wrongpassword", hashed, salt) is False
    
    def test_sanitize_filename(self):
        """Verificar sanitización de nombres de archivo"""
        # Nombre con caracteres peligrosos
        dangerous_name = "file<>:\"/\\|?*.txt"
        sanitized = sanitize_filename(dangerous_name)
        
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert sanitized == "file.txt"
        
        # Nombre muy largo
        long_name = "a" * 300 + ".txt"
        sanitized = sanitize_filename(long_name)
        
        assert len(sanitized) <= 255
        assert sanitized.endswith(".txt")

class TestSecurityIntegration:
    """Tests de integración de seguridad"""
    
    def test_security_integration_with_fastapi(self):
        """Verificar integración con FastAPI"""
        client = TestClient(app)
        
        # Test de endpoint protegido
        response = client.get("/api/usuarios/")
        assert response.status_code in [401, 403]  # Debe requerir autenticación
    
    def test_rate_limiting_integration(self, rate_limiter, mock_request):
        """Verificar integración del rate limiting"""
        # Simular múltiples peticiones rápidas
        for _ in range(5):
            is_limited, _ = rate_limiter.is_rate_limited(mock_request)
            assert is_limited is False
        
        # Verificar que no se excede el límite prematuramente
        is_limited, _ = rate_limiter.is_rate_limited(mock_request)
        assert is_limited is False
    
    def test_password_validation_integration(self, password_validator):
        """Verificar integración de validación de contraseñas"""
        # Contraseña que cumple todos los requisitos
        strong_password = "MySecurePass123!"
        is_valid, errors = password_validator.validate_password(strong_password)
        
        assert is_valid is True
        assert len(errors) == 0
        
        # Contraseña débil
        weak_password = "123"
        is_valid, errors = password_validator.validate_password(weak_password)
        
        assert is_valid is False
        assert len(errors) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 