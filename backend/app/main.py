"""
Archivo principal de inicialización del backend
OPTIMIZADO: Middlewares mejorados, configuración de rendimiento optimizada, manejo de errores robusto
"""
import logging
import asyncio
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.redis import redis_client
from app.core.database import advanced_health_check, cleanup_database, get_db_stats
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware

# Configurar logging optimizado
logger = logging.getLogger(__name__)

# Importar routers
from app.routers import (
    usuarios, clases, asistencias, pagos, rutinas, auth, sync, 
    empleados, tipos_cuota, reportes, configuracion, multimedia
)
from app.routers import logos

async def _initialize_redis():
    """Inicializar conexión con Redis"""
    try:
        await redis_client.connect()
        logger.info("✓ Redis conectado")
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando Redis: {str(e)}")
        # En desarrollo, permitir continuar sin Redis
        if settings.ENV == "development":
            logger.warning("⚠️ Continuando sin Redis en desarrollo")
            return True
        return False

async def _check_database_health():
    """Verificar salud de la base de datos"""
    try:
        db_health = advanced_health_check()
        if db_health.get("status") == "healthy":
            query_time = db_health.get('query_time_ms', 0)
            logger.info(f"✓ Base de datos conectada - Latencia: {query_time}ms")
            return True
        else:
            error_msg = db_health.get('error', 'Unknown')
            logger.warning(f"⚠️ Base de datos con problemas: {error_msg}")
            return False
    except Exception as e:
        logger.error(f"❌ Error verificando base de datos: {str(e)}")
        return False

async def _setup_production_environment():
    """Configurar entorno de producción"""
    if settings.ENV == "production":
        logger.info("✓ Tareas de producción configuradas")
        return True
    return True

async def _startup_tasks():
    """Tareas de inicio separadas por responsabilidad"""
    logger.info("🚀 Iniciando aplicación FastAPI...")
    
    # Validar configuración de seguridad en producción
    if settings.is_production():
        security_issues = settings.validate_production_security()
        if security_issues:
            logger.critical(f"❌ Configuración insegura detectada en producción: {security_issues}")
            print("ERROR CRÍTICO: El sistema no puede arrancar en producción con valores inseguros.")
            print("Revisa las variables de entorno y configura claves, contraseñas y dominios reales y seguros.")
            raise SystemExit(1)
    
    # Inicializar servicios en paralelo
    redis_ok = await _initialize_redis()
    db_ok = await _check_database_health()
    prod_ok = await _setup_production_environment()
    
    if redis_ok and db_ok and prod_ok:
        logger.info("✅ Aplicación iniciada correctamente")
    else:
        logger.warning("⚠️ Aplicación iniciada con algunos problemas")

async def _cleanup_redis():
    """Cerrar conexión con Redis"""
    try:
        await redis_client.close()
        logger.info("✓ Redis desconectado")
        return True
    except Exception as e:
        logger.error(f"❌ Error desconectando Redis: {str(e)}")
        return False

async def _cleanup_database():
    """Cerrar conexiones de base de datos"""
    try:
        cleanup_database()
        logger.info("✓ Base de datos desconectada")
        return True
    except Exception as e:
        logger.error(f"❌ Error desconectando base de datos: {str(e)}")
        return False

async def _shutdown_tasks():
    """Tareas de cierre separadas por responsabilidad"""
    try:
        logger.info("🔄 Cerrando aplicación...")
        
        # Cerrar servicios en paralelo
        redis_ok = await _cleanup_redis()
        db_ok = await _cleanup_database()
        
        if redis_ok and db_ok:
            logger.info("✅ Aplicación cerrada correctamente")
        else:
            logger.warning("⚠️ Aplicación cerrada con algunos problemas")
    except Exception as e:
        logger.error(f"❌ Error durante cierre: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor optimizado de ciclo de vida de la aplicación.
    Maneja inicio y cierre de recursos de forma eficiente.
    """
    await _startup_tasks()
    yield
    await _shutdown_tasks()

# Crear la aplicación FastAPI con configuraciones optimizadas
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description="API optimizada del Sistema de Gestión de Gimnasio",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,  # Respuestas JSON más rápidas
    # Configuraciones adicionales para rendimiento
    generate_unique_id_function=lambda route: f"{route.tags[0]}-{route.name}" if route.tags else route.name,
    servers=None,
)

# ============================================================================
# CONFIGURACIÓN DE MIDDLEWARES (ORDEN IMPORTANTE)
# ============================================================================

# 1. Middleware de manejo de errores (debe ser el primero)
app.add_middleware(ErrorHandlerMiddleware)

# 2. Middleware de hosts confiables (solo en producción)
if settings.ENV == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS != ["*"] else ["*"],
    )

# 3. Middleware de compresión para mejorar transferencia
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Solo comprimir respuestas > 1KB
    compresslevel=6     # Balance entre velocidad y compresión
)

# 4. Middleware de sesiones (solo si se necesita)
if settings.ENV in ["development", "testing"]:
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        max_age=settings.SESSION_TIMEOUT_MINUTES * 60,
        same_site="strict" if settings.SAMESITE_COOKIES == "strict" else "lax",
        https_only=settings.SECURE_COOKIES
    )

# 5. Configurar CORS de forma optimizada
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
    # Configuraciones adicionales para rendimiento
    max_age=86400,  # Cache preflight por 24h
    expose_headers=["X-Total-Count", "X-Page-Count"],
)

# 6. Middlewares de seguridad (si están habilitados)
if settings.ENABLE_SECURITY_HEADERS:
    from app.middleware.security import SecurityMiddleware
    app.add_middleware(SecurityMiddleware)
    logger.info("✓ Security middleware habilitado")

if settings.ENABLE_INPUT_VALIDATION:
    from app.middleware.security import InputValidationMiddleware
    app.add_middleware(InputValidationMiddleware)
    logger.info("✓ Input validation middleware habilitado")

# 7. Rate limiting (si está habilitado)
if settings.ENABLE_RATE_LIMITING:
    from app.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
    logger.info("✓ Rate limiting middleware habilitado")

# ============================================================================
# MANEJADORES DE EXCEPCIONES MEJORADOS
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejar errores de validación de forma segura"""
    # No exponer detalles internos en producción
    if settings.ENV == "production":
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Error de validación en los datos enviados",
                "type": "validation_error"
            }
        )
    else:
        # En desarrollo, mostrar detalles para debugging
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Error de validación",
                "errors": exc.errors(),
                "type": "validation_error"
            }
        )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Manejar excepciones HTTP de forma segura"""
    # Log del error para auditoría
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail} - IP: {request.client.host if request.client else 'unknown'}")
    
    # No exponer detalles internos en producción para errores 500+
    if exc.status_code >= 500 and settings.ENV == "production":
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": "Error interno del servidor",
                "type": "server_error"
            }
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "type": "http_error"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejar excepciones generales de forma segura"""
    # Log del error completo para debugging
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Registrar en auditoría si está habilitado
    if hasattr(settings, 'ENABLE_AUDIT_LOG') and settings.ENABLE_AUDIT_LOG:
        try:
            from app.core.audit import SecurityAuditor, AuditEvent, EventType, RiskLevel
            auditor = SecurityAuditor()
            event = AuditEvent(
                event_type=EventType.SYSTEM_ERROR,
                risk_level=RiskLevel.HIGH,
                message=f"Excepción no capturada: {type(exc).__name__}: {str(exc)}",
                ip_address=getattr(request.state, 'client_ip', 'unknown'),
                endpoint=str(request.url),
                method=request.method,
                success=False
            )
            auditor.log_event(event)
        except Exception as audit_error:
            logger.error(f"Error en auditoría: {audit_error}")
    
    # En producción, no exponer detalles del error
    if settings.ENV == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Error interno del servidor",
                "type": "server_error"
            }
        )
    else:
        # En desarrollo, mostrar detalles para debugging
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Error interno del servidor",
                "error": str(exc),
                "type": "server_error"
            }
        )

# ============================================================================
# ROUTERS
# ============================================================================

# Incluir routers con prefijos optimizados
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(usuarios.router, prefix="/api/usuarios", tags=["Usuarios"])
app.include_router(clases.router, prefix="/api/clases", tags=["Clases"])
app.include_router(asistencias.router, prefix="/api/asistencias", tags=["Asistencias"])
app.include_router(pagos.router, prefix="/api/pagos", tags=["Pagos"])
app.include_router(rutinas.router, prefix="/api/rutinas", tags=["Rutinas"])
app.include_router(empleados.router, prefix="/api/empleados", tags=["Empleados"])
app.include_router(tipos_cuota.router, prefix="/api/tipos-cuota", tags=["Tipos de Cuota"])
app.include_router(reportes.router, prefix="/api/reportes", tags=["Reportes"])
app.include_router(configuracion.router, prefix="/api/configuracion", tags=["Configuración"])
app.include_router(multimedia.router, prefix="/api/multimedia", tags=["Multimedia"])
app.include_router(sync.router, prefix="/api/sync", tags=["Sincronización"])
app.include_router(logos.router, prefix="/api/configuracion/logos", tags=["Logos"])

# ============================================================================
# ENDPOINTS PRINCIPALES
# ============================================================================

@app.get("/", tags=["Root"], response_class=ORJSONResponse)
async def root():
    """Endpoint raíz con información básica"""
    return {
        "message": "Sistema de Gestión de Gimnasio API",
        "version": settings.API_VERSION,
        "status": "operativo",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health", tags=["Health"], response_class=ORJSONResponse)
async def health_check():
    """Health check mejorado con información detallada"""
    try:
        # Verificar base de datos
        db_health = advanced_health_check()
        db_status = db_health.get("status", "unknown")
        db_latency = db_health.get("query_time_ms", 0)
        
        # Verificar Redis
        try:
            redis_status = "healthy" if redis_client.get_client() else "unhealthy"
        except Exception:
            redis_status = "unhealthy"
        
        # Verificar memoria
        import psutil
        memory = psutil.virtual_memory()
        memory_usage = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent
        }
        
        # Determinar estado general
        overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": settings.API_VERSION,
            "environment": settings.ENV,
            "services": {
                "database": {
                    "status": db_status,
                    "latency_ms": db_latency
                },
                "redis": {
                    "status": redis_status
                }
            },
            "system": {
                "memory": memory_usage,
                "uptime": psutil.boot_time()
            }
        }
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": "Error verificando servicios",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@app.get("/metrics", tags=["Monitoring"], response_class=ORJSONResponse)
async def metrics(request: Request):
    """Endpoint de métricas para monitoreo"""
    # Verificar autenticación básica para métricas
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida para métricas"
        )
    
    try:
        # Obtener estadísticas de base de datos
        db_stats = get_db_stats()
        
        # Obtener estadísticas de Redis
        redis_stats = {}
        try:
            redis_client_instance = redis_client.get_client()
            if redis_client_instance:
                redis_stats = {
                    "connected": True,
                    "memory_usage": "available",
                    "clients": "available"
                }
            else:
                redis_stats = {"connected": False}
        except Exception:
            redis_stats = {"connected": False}
        
        # Obtener estadísticas del sistema
        import psutil
        system_stats = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": dict(psutil.virtual_memory()._asdict()),
            "disk": dict(psutil.disk_usage('/')._asdict()),
            "network": dict(psutil.net_io_counters()._asdict())
        }
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": db_stats,
            "redis": redis_stats,
            "system": system_stats
        }
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo métricas"
        )

# ============================================================================
# CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS
# ============================================================================

# Montar archivos estáticos solo en desarrollo
if settings.ENV == "development":
    # Verificar que los directorios existan antes de montarlos
    static_dir = Path("static")
    uploads_dir = Path("uploads")
    
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory="static"), name="static")
    
    if uploads_dir.exists():
        app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Configuración de logging para desarrollo
    logging.basicConfig(
        level=logging.INFO if settings.ENV == "production" else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Ejecutar servidor
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.SERVER_RELOAD,
        workers=settings.SERVER_WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )
