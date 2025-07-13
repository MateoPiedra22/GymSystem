"""
Configuración avanzada de pytest para el sistema de gestión de gimnasio
Optimizada para rendimiento y cobertura completa
"""

import os
import sys

# ================= CARGA DE VARIABLES DE ENTORNO DE TEST =====================
# Cargar archivo de configuración de tests ANTES de cualquier import del backend
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

test_env_file = os.path.join(backend_dir, ".env.test")
if os.path.exists(test_env_file):
    with open(test_env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    print("[INFO] Archivo de configuración de tests cargado (.env.test)")
else:
    print("[WARNING] Archivo .env.test no encontrado, usando configuración por defecto")

# ================= RESTO DE IMPORTS Y CONFIGURACIÓN ORIGINAL ================

import asyncio
import pytest
import logging
from typing import Dict, Any, Generator, AsyncGenerator
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
import time
import psutil
import gc

# Configurar logging para pruebas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar todos los modelos para que Base conozca las tablas
from app import models  # noqa: F401

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, QueuePool
from app.core.database import Base, get_db
from app.main import app
from app.core.config import settings
settings.TESTING = True

# Configuración de rendimiento para pruebas
class TestPerformanceMonitor:
    """Monitor de rendimiento para pruebas"""
    
    def __init__(self):
        self.start_time = time.time()
        self.test_times = {}
        self.memory_usage = {}
        self.db_queries = {}
        self.slow_tests = []
        self.memory_intensive_tests = []
        
    def start_test(self, test_name: str):
        """Inicia el monitoreo de una prueba"""
        self.test_times[test_name] = time.time()
        self.memory_usage[test_name] = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
    def end_test(self, test_name: str):
        """Finaliza el monitoreo de una prueba"""
        if test_name in self.test_times:
            elapsed = time.time() - self.test_times[test_name]
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_diff = current_memory - self.memory_usage[test_name]
            
            logger.info(f"Prueba {test_name}: {elapsed:.3f}s, Memoria: {memory_diff:+.2f}MB")
            
            # Alertar sobre pruebas lentas
            if elapsed > 5.0:
                logger.warning(f"Prueba lenta detectada: {test_name} tardó {elapsed:.3f}s")
                self.slow_tests.append(test_name)
            
            # Alertar sobre uso excesivo de memoria
            if memory_diff > 50:
                logger.warning(f"Uso excesivo de memoria: {test_name} usó {memory_diff:.2f}MB")
                self.memory_intensive_tests.append(test_name)

# Instancia global del monitor
perf_monitor = TestPerformanceMonitor()

# Configuración de base de datos optimizada para pruebas
def create_test_engine(use_memory=True):
    """Crea un motor de base de datos optimizado para pruebas"""
    if use_memory:
        # Base de datos en memoria para pruebas rápidas
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={
                "check_same_thread": False,
                "timeout": 30,
                "isolation_level": None,
            },
            poolclass=StaticPool,
            echo=False,  # Cambiar a True para debug SQL
            future=True
        )
    else:
        # Base de datos en archivo para pruebas de integración
        db_file = "test_integration.db"
        engine = create_engine(
            f"sqlite:///{db_file}",
            connect_args={
                "check_same_thread": False,
                "timeout": 30,
            },
            poolclass=QueuePool,
            pool_size=5,  # Reducido para pruebas
            max_overflow=10,  # Reducido para pruebas
            echo=False,
            future=True
        )
    
    # Configurar eventos para monitoreo de queries
    query_count = {"count": 0}
    
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        query_count["count"] += 1
        context._query_start_time = time.time()
    
    @event.listens_for(engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - context._query_start_time
        if total > 1.0:  # Queries muy lentas en pruebas
            logger.warning(f"Query muy lenta en pruebas: {total:.3f}s")
    
    return engine
    
    # Configurar eventos para monitoreo de queries
    query_count = {"count": 0}
    
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        query_count["count"] += 1
        context._query_start_time = time.time()
    
    @event.listens_for(engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - context._query_start_time
        if total > 0.5:  # Queries lentas
            logger.warning(f"Query lenta detectada: {total:.3f}s")
    
    return engine

# Motores de base de datos
memory_engine = create_test_engine(use_memory=True)
file_engine = create_test_engine(use_memory=False)

# Session makers
MemorySessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=memory_engine)
FileSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=file_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configuración inicial del entorno de pruebas"""
    logger.info("Iniciando configuración de entorno de pruebas")
    
    # Crear directorio de logs si no existe
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    # Configurar variables de entorno para pruebas
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "INFO"
    
    # Cargar archivo de configuración de tests
    test_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.test")
    if os.path.exists(test_env_file):
        with open(test_env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        logger.info("Archivo de configuración de tests cargado")
    else:
        logger.warning("Archivo .env.test no encontrado, usando configuración por defecto")
    
    # Importar configuración después de configurar variables de entorno
    from app.core.config import settings
    settings.TESTING = True
    
    # Crear todas las tablas en ambos motores
    Base.metadata.create_all(bind=memory_engine)
    Base.metadata.create_all(bind=file_engine)
    
    yield
    
    # Limpieza final
    Base.metadata.drop_all(bind=memory_engine)
    Base.metadata.drop_all(bind=file_engine)
    
    # Limpiar archivos de prueba
    if os.path.exists("test_integration.db"):
        try:
            os.remove("test_integration.db")
        except PermissionError:
            # El archivo puede estar en uso, ignorar el error
            pass
    
    logger.info("Limpieza de entorno completada")

@pytest.fixture(scope="session")
def event_loop():
    """Crear un loop de eventos para pruebas asíncronas"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Sesión de base de datos en memoria para pruebas rápidas"""
    # Limpiar y recrear tablas para cada prueba
    Base.metadata.drop_all(bind=memory_engine)
    Base.metadata.create_all(bind=memory_engine)
    
    session = MemorySessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Limpiar después de cada prueba
        Base.metadata.drop_all(bind=memory_engine)
        # Forzar limpieza de memoria
        gc.collect()

@pytest.fixture()
def integration_db_session() -> Generator[Session, None, None]:
    """Sesión de base de datos en archivo para pruebas de integración"""
    # Limpiar y recrear tablas para cada prueba
    Base.metadata.drop_all(bind=file_engine)
    Base.metadata.create_all(bind=file_engine)
    
    session = FileSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Limpiar después de cada prueba
        Base.metadata.drop_all(bind=file_engine)

@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP para pruebas de API con base de datos en memoria"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Limpiar overrides
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture()
def integration_client(integration_db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP para pruebas de integración con base de datos persistente"""
    def override_get_db():
        try:
            yield integration_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Limpiar overrides
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture()
def async_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP asíncrono para pruebas (ahora síncrono para evitar error de 'async with')"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.pop(get_db, None)

# Fixtures para datos de prueba
@pytest.fixture()
def sample_user_data() -> Dict[str, Any]:
    """Datos de ejemplo para usuario"""
    return {
        "nombre": "Usuario Test",
        "apellido": "Apellido Test",
        "email": "test@example.com",
        "telefono": "123456789",
        "username": "testuser",
        "fecha_nacimiento": "1990-01-01",
        "genero": "M",
        "esta_activo": True,
        "es_admin": False
    }

@pytest.fixture()
def sample_admin_data() -> Dict[str, Any]:
    """Datos de ejemplo para administrador"""
    return {
        "nombre": "Admin Test",
        "apellido": "Administrator",
        "email": "admin@example.com",
        "telefono": "987654321",
        "username": "admin",
        "fecha_nacimiento": "1985-01-01",
        "genero": "F",
        "esta_activo": True,
        "es_admin": True
    }

@pytest.fixture()
def sample_clase_data() -> Dict[str, Any]:
    """Datos de ejemplo para clase"""
    return {
        "nombre": "Clase Test",
        "descripcion": "Descripción de clase de prueba",
        "dia_semana": "lunes",
        "hora_inicio": "09:00",
        "hora_fin": "10:00",
        "capacidad_maxima": 20,
        "precio": 25.00,
        "esta_activa": True
    }

@pytest.fixture()
def sample_empleado_data() -> Dict[str, Any]:
    """Datos de ejemplo para empleado"""
    return {
        "nombre": "Empleado Test",
        "apellido": "Instructor",
        "email": "instructor@example.com",
        "telefono": "555-1234",
        "tipo_empleado": "instructor",
        "salario": 2500.00,
        "fecha_contratacion": "2024-01-01",
        "esta_activo": True
    }

# Fixtures para autenticación
@pytest.fixture()
def auth_headers() -> Dict[str, str]:
    """Headers de autenticación para pruebas"""
    return {"Authorization": "Bearer test_token_user"}

@pytest.fixture()
def admin_headers() -> Dict[str, str]:
    """Headers de autenticación para administrador"""
    return {"Authorization": "Bearer test_token_admin"}

@pytest.fixture()
def invalid_headers() -> Dict[str, str]:
    """Headers de autenticación inválidos"""
    return {"Authorization": "Bearer invalid_token"}

# Fixtures para monitoreo de rendimiento
@pytest.fixture(autouse=True)
def monitor_test_performance(request):
    """Monitorea el rendimiento de cada prueba"""
    test_name = request.node.name
    perf_monitor.start_test(test_name)
    
    # Limpiar memoria antes de la prueba
    gc.collect()
    
    yield
    
    perf_monitor.end_test(test_name)
    
    # Limpiar memoria después de la prueba
    gc.collect()

# Overrides de autenticación para pruebas
@pytest.fixture(autouse=True)
def override_auth_dependencies(db_session: Session):
    """Sobrescribe las dependencias de autenticación para pruebas"""
    from app.core.auth import get_current_user, get_current_admin_user
    from app.models.usuarios import Usuario
    from fastapi import Request, HTTPException
    
    def _create_test_user(is_admin: bool = False) -> Usuario:
        """Crea un usuario de prueba"""
        username = "test_admin" if is_admin else "test_user"
        user = db_session.query(Usuario).filter(Usuario.username == username).first()
        
        if not user:
            user = Usuario(
                id=f"test-{'admin' if is_admin else 'user'}-id",
                nombre="Test",
                apellido="User" if not is_admin else "Admin",
                email=f"{'admin' if is_admin else 'user'}@test.com",
                telefono="123456789",
                username=username,
                hashed_password="hashed_password",
                salt="test_salt",
                es_admin=is_admin,
                esta_activo=True,
                fecha_nacimiento="1990-01-01",
                genero="M"
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
        
        return user
    
    async def _override_get_current_user(request: Request):
        """Override para obtener usuario actual"""
        # Permitir acceso sin token a endpoints públicos
        if request.url.path.startswith("/api/reportes") or request.url.path.startswith("/health"):
            return _create_test_user(is_admin=False)
        
        auth_header = request.headers.get("authorization", "")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Token no proporcionado")
        
        if "admin" in auth_header:
            return _create_test_user(is_admin=True)
        elif "user" in auth_header:
            return _create_test_user(is_admin=False)
        else:
            raise HTTPException(status_code=401, detail="Token inválido")
    
    async def _override_get_admin_user(request: Request):
        """Override para obtener usuario administrador"""
        if request.url.path.startswith("/api/reportes"):
            return _create_test_user(is_admin=True)
        
        auth_header = request.headers.get("authorization", "")
        if not auth_header or "admin" not in auth_header:
            raise HTTPException(status_code=403, detail="Permisos de administrador requeridos")
        
        return _create_test_user(is_admin=True)
    
    # TEMPORALMENTE DESHABILITADO: Aplicar overrides
    # app.dependency_overrides[get_current_user] = _override_get_current_user
    # app.dependency_overrides[get_current_admin_user] = _override_get_admin_user
    
    # Registrar endpoint de login para pruebas
    if not any(getattr(r, "path", None) == "/auth/login" for r in app.router.routes):
        from fastapi import Body
        
        @app.post("/auth/login")
        async def test_login(credentials: dict = Body(...)):
            username = credentials.get("username")
            password = credentials.get("password")
            
            if username == "admin" and password == "admin123":
                return {"access_token": "test_token_admin", "token_type": "bearer"}
            elif username == "user" and password == "user123":
                return {"access_token": "test_token_user", "token_type": "bearer"}
            else:
                raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    yield
    
    # Limpiar overrides
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_admin_user, None)

# Fixtures para pruebas de carga
@pytest.fixture()
def stress_test_data() -> Dict[str, Any]:
    """Datos para pruebas de estrés"""
    return {
        "concurrent_users": 50,
        "requests_per_user": 10,
        "ramp_up_time": 30,  # segundos
        "test_duration": 60,  # segundos
    }

@pytest.fixture()
def load_test_endpoints() -> list:
    """Endpoints para pruebas de carga"""
    return [
        "/api/usuarios",
        "/api/clases",
        "/api/asistencias",
        "/api/pagos",
        "/api/reportes/kpis",
        "/api/reportes/graficos",
        "/health"
    ]

# Fixtures para mocking
@pytest.fixture()
def mock_redis():
    """Mock de Redis para pruebas"""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.exists.return_value = False
    return mock

@pytest.fixture()
def mock_email_service():
    """Mock del servicio de email"""
    mock = AsyncMock()
    mock.send_email.return_value = True
    return mock

@pytest.fixture()
def mock_payment_gateway():
    """Mock del gateway de pagos"""
    mock = MagicMock()
    mock.process_payment.return_value = {
        "success": True,
        "transaction_id": "test_transaction_123",
        "amount": 100.00
    }
    return mock

# Utilidades para pruebas
@pytest.fixture()
def test_db_with_sample_data(db_session: Session, sample_user_data: Dict[str, Any]):
    """Base de datos con datos de ejemplo"""
    from app.models.usuarios import Usuario
    
    # Crear usuario de ejemplo
    user = Usuario(**sample_user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return {"user": user, "db": db_session}

# Hooks de pytest para logging personalizado
def pytest_runtest_setup(item):
    """Setup ejecutado antes de cada prueba"""
    logger.info(f"Iniciando prueba: {item.name}")

def pytest_runtest_teardown(item):
    """Teardown ejecutado después de cada prueba"""
    logger.info(f"Finalizando prueba: {item.name}")

def pytest_sessionstart(session):
    """Ejecutado al inicio de la sesión de pruebas"""
    logger.info("=== Iniciando sesión de pruebas ===")

def pytest_sessionfinish(session, exitstatus):
    """Ejecutado al final de la sesión de pruebas"""
    logger.info(f"=== Finalizando sesión de pruebas (código: {exitstatus}) ===")
    
    # Reporte de rendimiento
    total_time = time.time() - perf_monitor.start_time
    logger.info(f"Tiempo total de pruebas: {total_time:.2f}s")
    
    # Estadísticas de base de datos
    # Elimino cualquier referencia a engine.query_count
    pass

# Configuración de marcadores
def pytest_configure(config):
    """Configuración de pytest"""
    # Registrar marcadores personalizados
    config.addinivalue_line("markers", "smoke: pruebas de humo básicas")
    config.addinivalue_line("markers", "critical: pruebas críticas")
    config.addinivalue_line("markers", "flaky: pruebas que pueden fallar ocasionalmente")
    config.addinivalue_line("markers", "performance: pruebas de rendimiento")
    config.addinivalue_line("markers", "load: pruebas de carga")
    config.addinivalue_line("markers", "stress: pruebas de estrés")
    config.addinivalue_line("markers", "e2e: pruebas end-to-end")
    config.addinivalue_line("markers", "regression: pruebas de regresión")

# Función para ejecutar pruebas por categoría
def run_smoke_tests():
    """Ejecutar solo pruebas de humo"""
    import subprocess
    return subprocess.run(["pytest", "-m", "smoke", "-v"], capture_output=True, text=True)

def run_critical_tests():
    """Ejecutar solo pruebas críticas"""
    import subprocess
    return subprocess.run(["pytest", "-m", "critical", "-v"], capture_output=True, text=True)

def run_performance_tests():
    """Ejecutar solo pruebas de rendimiento"""
    import subprocess
    return subprocess.run(["pytest", "-m", "performance", "-v"], capture_output=True, text=True) 

@pytest.fixture(autouse=True)
def disable_rate_limit_middleware(monkeypatch):
    """Desactiva el rate limiting en todos los tests"""
    try:
        from app.middleware.rate_limit import RateLimitMiddleware
    except ImportError:
        return  # Si no existe, no hacer nada
    async def no_rate_limit(self, request, call_next):
        return await call_next(request)
    monkeypatch.setattr(RateLimitMiddleware, "dispatch", no_rate_limit) 

@pytest.fixture(autouse=True)
def disable_slowapi_rate_limit(monkeypatch):
    """Desactiva el rate limiting de slowapi en todos los tests de integración"""
    try:
        from app.routers.auth import limiter
    except ImportError:
        return
    def no_limit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    monkeypatch.setattr(limiter, "limit", no_limit) 