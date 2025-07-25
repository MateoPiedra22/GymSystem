import time
import json
import logging
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import SessionLocal
from .config import settings
from ..models.configuration import SystemLog
import uuid
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for headers and basic protection"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS header for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware for request/response tracking"""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Get client info
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Log request
        if self.log_requests:
            logger.info(
                f"Request {request_id}: {request.method} {request.url} "
                f"from {client_ip} - {user_agent}"
            )
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            if self.log_responses:
                logger.info(
                    f"Response {request_id}: {response.status_code} "
                    f"in {process_time:.4f}s"
                )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log to database for important endpoints
            if self.should_log_to_db(request):
                await self.log_to_database(request, response, request_id, process_time, client_ip)
            
            return response
        
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error {request_id}: {str(e)} in {process_time:.4f}s"
            )
            
            # Log error to database
            await self.log_error_to_database(request, e, request_id, process_time, client_ip)
            
            # Re-raise the exception
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address considering proxies"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def should_log_to_db(self, request: Request) -> bool:
        """Determine if request should be logged to database"""
        # Log API endpoints but not static files
        path = request.url.path
        return (
            path.startswith("/api/") and
            not path.startswith("/api/health") and
            not path.startswith("/api/docs") and
            not path.startswith("/api/openapi.json")
        )
    
    async def log_to_database(self, request: Request, response: Response, 
                            request_id: str, process_time: float, client_ip: str):
        """Log request to database"""
        try:
            db = SessionLocal()
            
            # Determine log level based on status code
            if response.status_code >= 500:
                level = "ERROR"
            elif response.status_code >= 400:
                level = "WARNING"
            else:
                level = "INFO"
            
            log_entry = SystemLog(
                level=level,
                category="HTTP_REQUEST",
                message=f"{request.method} {request.url.path}",
                user_id=getattr(request.state, 'user_id', None),
                metadata={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("user-agent", "")
                }
            )
            
            db.add(log_entry)
            db.commit()
            db.close()
        
        except Exception as e:
            logger.error(f"Failed to log to database: {e}")
    
    async def log_error_to_database(self, request: Request, error: Exception,
                                  request_id: str, process_time: float, client_ip: str):
        """Log error to database"""
        try:
            db = SessionLocal()
            
            log_entry = SystemLog(
                level="ERROR",
                category="HTTP_ERROR",
                message=f"Error in {request.method} {request.url.path}: {str(error)}",
                user_id=getattr(request.state, 'user_id', None),
                metadata={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "traceback": traceback.format_exc(),
                    "process_time": process_time,
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("user-agent", "")
                }
            )
            
            db.add(log_entry)
            db.commit()
            db.close()
        
        except Exception as e:
            logger.error(f"Failed to log error to database: {e}")

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests
        self.cleanup_old_requests(current_time)
        
        # Check rate limit
        if self.is_rate_limited(client_ip, current_time):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                }
            )
        
        # Record request
        self.record_request(client_ip, current_time)
        
        return await call_next(request)
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def cleanup_old_requests(self, current_time: float):
        """Remove requests older than 1 minute"""
        cutoff_time = current_time - 60
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                req_time for req_time in self.requests[ip]
                if req_time > cutoff_time
            ]
            if not self.requests[ip]:
                del self.requests[ip]
    
    def is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client is rate limited"""
        if client_ip not in self.requests:
            return False
        
        return len(self.requests[client_ip]) >= self.requests_per_minute
    
    def record_request(self, client_ip: str, current_time: float):
        """Record a request for rate limiting"""
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)

class DatabaseMiddleware(BaseHTTPMiddleware):
    """Database session middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Create database session
        db = SessionLocal()
        request.state.db = db
        
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Rollback on error
            db.rollback()
            raise
        finally:
            # Always close the session
            db.close()

class MaintenanceMiddleware(BaseHTTPMiddleware):
    """Maintenance mode middleware"""
    
    def __init__(self, app, maintenance_mode: bool = False, 
                 maintenance_message: str = "System is under maintenance"):
        super().__init__(app)
        self.maintenance_mode = maintenance_mode
        self.maintenance_message = maintenance_message
        self.allowed_paths = ["/api/health", "/api/docs", "/api/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if maintenance mode is enabled
        if self.maintenance_mode and request.url.path not in self.allowed_paths:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": self.maintenance_message,
                    "maintenance_mode": True
                }
            )
        
        return await call_next(request)

class CompressionMiddleware(BaseHTTPMiddleware):
    """Response compression middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add compression headers if supported
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" in accept_encoding:
            response.headers["Content-Encoding"] = "gzip"
        
        return response

class UserContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add user context to requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract user info from JWT token if present
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            try:
                from .auth import auth_manager
                token = authorization.split(" ")[1]
                token_data = auth_manager.verify_token(token)
                if token_data:
                    request.state.user_id = token_data.user_id
                    
                    # Get user from database
                    db = getattr(request.state, 'db', None)
                    if db:
                        from ..models.user import User
                        user = db.query(User).filter(User.id == token_data.user_id).first()
                        if user:
                            request.state.user = user
            except Exception:
                pass  # Ignore token errors in middleware
        
        return await call_next(request)

class APIVersionMiddleware(BaseHTTPMiddleware):
    """API versioning middleware"""
    
    def __init__(self, app, current_version: str = "v1", supported_versions: list = None):
        super().__init__(app)
        self.current_version = current_version
        self.supported_versions = supported_versions or ["v1"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract version from URL or headers
        path = request.url.path
        version = None
        
        # Check URL path for version
        if path.startswith("/api/v"):
            version_part = path.split("/")[2]  # /api/v1/...
            if version_part in self.supported_versions:
                version = version_part
        
        # Check headers for version
        if not version:
            version = request.headers.get("api-version", self.current_version)
        
        # Validate version
        if version not in self.supported_versions:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": f"Unsupported API version: {version}",
                    "supported_versions": self.supported_versions
                }
            )
        
        # Add version to request state
        request.state.api_version = version
        
        response = await call_next(request)
        
        # Add version to response headers
        response.headers["API-Version"] = version
        
        return response

# Exception handlers
async def validation_exception_handler(request: Request, exc):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors() if hasattr(exc, 'errors') else str(exc)
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Don't expose internal errors in production
    if settings.ENVIRONMENT == "production":
        detail = "Internal server error"
    else:
        detail = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": detail,
            "type": type(exc).__name__
        }
    )

# CORS configuration
def get_cors_middleware():
    """Get CORS middleware with proper configuration"""
    return CORSMiddleware(
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

# Middleware factory functions
def create_logging_middleware(log_requests: bool = True, log_responses: bool = True):
    """Create logging middleware with configuration"""
    return LoggingMiddleware(None, log_requests, log_responses)

def create_rate_limit_middleware(requests_per_minute: int = 60):
    """Create rate limiting middleware with configuration"""
    return RateLimitMiddleware(None, requests_per_minute)

def create_maintenance_middleware(enabled: bool = False, message: str = None):
    """Create maintenance middleware with configuration"""
    return MaintenanceMiddleware(
        None, 
        enabled, 
        message or "System is under maintenance. Please try again later."
    )

def create_api_version_middleware(current_version: str = "v1", supported_versions: list = None):
    """Create API versioning middleware with configuration"""
    return APIVersionMiddleware(None, current_version, supported_versions)

# Export all middleware
__all__ = [
    'SecurityMiddleware',
    'LoggingMiddleware', 
    'RateLimitMiddleware',
    'DatabaseMiddleware',
    'MaintenanceMiddleware',
    'CompressionMiddleware',
    'UserContextMiddleware',
    'APIVersionMiddleware',
    'get_cors_middleware',
    'validation_exception_handler',
    'http_exception_handler',
    'general_exception_handler',
    'create_logging_middleware',
    'create_rate_limit_middleware',
    'create_maintenance_middleware',
    'create_api_version_middleware'
]