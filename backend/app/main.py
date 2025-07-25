from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
from .core.config import settings
from .core.database import engine, Base
from .core.middleware import (
    SecurityMiddleware, LoggingMiddleware, RateLimitMiddleware,
    DatabaseMiddleware, MaintenanceMiddleware, CompressionMiddleware,
    UserContextMiddleware, APIVersionMiddleware,
    validation_exception_handler, http_exception_handler, general_exception_handler
)
from .middleware.audit_middleware import AuditMiddleware, SecurityAuditMiddleware
from .api import (
    auth, users, memberships, exercises, routines, 
    classes, employees, payments, reports
)
from .api.v1 import health, config, audit, push_notifications, email, whatsapp, notifications, backup, monitoring, integrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up GymSystem API...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
    
    # Additional startup tasks
    logger.info("GymSystem API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GymSystem API...")
    logger.info("GymSystem API shutdown complete")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sistema de gestión integral para gimnasios",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Setup CORS
from starlette.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "X-API-Version",
        "X-Request-ID"
    ],
    expose_headers=[
        "X-Request-ID",
        "X-Process-Time",
        "API-Version"
    ]
)

# Add custom middleware (order matters!) - Temporarily simplified for debugging
app.add_middleware(SecurityMiddleware)
app.add_middleware(DatabaseMiddleware)
app.add_middleware(LoggingMiddleware)

# Exception handlers - temporarily simplified for debugging
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
# app.add_exception_handler(Exception, general_exception_handler)  # Temporarily disabled

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": f"Bienvenido a {settings.PROJECT_NAME} API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Documentación no disponible en producción",
        "health": "/health"
    }

# API version endpoint
@app.get("/api/v1", tags=["API Info"])
async def api_info():
    """API version information"""
    return {
        "api_version": "v1",
        "service": settings.PROJECT_NAME,
        "description": "Sistema de gestión integral para gimnasios",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "memberships": "/api/v1/memberships",
            "exercises": "/api/v1/exercises",
            "routines": "/api/v1/routines",
            "classes": "/api/v1/classes",
            "employees": "/api/v1/employees",
            "payments": "/api/v1/payments",
            "reports": "/api/v1/reports",
            "health": "/api/v1/health",
            "config": "/api/v1/config",
            "audit": "/api/v1/audit",
            "push_notifications": "/api/v1/push-notifications",
            "email": "/api/v1/email",
            "whatsapp": "/api/v1/whatsapp",
            "notifications": "/api/v1/notifications",
            "backup": "/api/v1/backup",
            "monitoring": "/api/v1/monitoring",
            "integrations": "/api/v1/integrations"
        }
    }

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(users.router, prefix="/api/v1")
app.include_router(memberships.router, prefix="/api/v1")
app.include_router(exercises.router, prefix="/api/v1")
app.include_router(routines.router, prefix="/api/v1")
app.include_router(classes.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(config.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(push_notifications.router, prefix="/api/v1")
app.include_router(email.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(backup.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")
app.include_router(integrations.router, prefix="/api/v1")

# Custom error responses
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: StarletteHTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "El recurso solicitado no fue encontrado",
            "path": str(request.url.path),
            "method": request.method
        }
    )

@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc: StarletteHTTPException):
    """Custom 405 handler"""
    return JSONResponse(
        status_code=405,
        content={
            "error": "Method Not Allowed",
            "message": "El método HTTP no está permitido para este endpoint",
            "path": str(request.url.path),
            "method": request.method
        }
    )

# Temporarily disabled custom 500 handler for debugging
# @app.exception_handler(500)
# async def internal_server_error_handler(request: Request, exc: Exception):
#     """Custom 500 handler"""
#     logger.error(f"Internal server error: {exc}", exc_info=True)
#     return JSONResponse(
#         status_code=500,
#         content={
#             "error": "Internal Server Error",
#             "message": "Ha ocurrido un error interno del servidor",
#             "path": str(request.url.path),
#             "method": request.method
#         }
#     )

# Maintenance mode check
@app.middleware("http")
async def maintenance_check(request: Request, call_next):
    """Check if application is in maintenance mode"""
    # Skip maintenance check for health endpoint
    if request.url.path == "/health":
        response = await call_next(request)
        return response
    
    # Check maintenance mode from environment or database
    maintenance_mode = getattr(settings, 'MAINTENANCE_MODE', False)
    
    if maintenance_mode:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service Unavailable",
                "message": "El sistema está en mantenimiento. Intente más tarde.",
                "retry_after": "3600"  # 1 hour
            },
            headers={"Retry-After": "3600"}
        )
    
    response = await call_next(request)
    return response

# Request size limit middleware
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Limit request body size"""
    max_size = 10 * 1024 * 1024  # 10MB
    
    if request.headers.get("content-length"):
        content_length = int(request.headers["content-length"])
        if content_length > max_size:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Payload Too Large",
                    "message": "El tamaño del archivo excede el límite permitido (10MB)",
                    "max_size": max_size
                }
            )
    
    response = await call_next(request)
    return response

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )