from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
import time
import json
import logging
from datetime import datetime
from ..services.audit_service import (
    audit_service,
    AuditAction,
    AuditCategory,
    AuditLevel,
    AuditContext
)
from ..core.auth import auth_manager
from ..core.database import get_db
from ..models.user import User
import uuid
from urllib.parse import urlparse
import asyncio

logger = logging.getLogger(__name__)

class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic audit logging of HTTP requests"""
    
    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        
        # Paths to exclude from audit logging
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static",
            "/health/ping",
            "/health/ready",
            "/health/live"
        ]
        
        # Sensitive endpoints that should always be logged
        self.sensitive_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/auth/register",
            "/api/v1/auth/reset-password",
            "/api/v1/users",
            "/api/v1/payments",
            "/api/v1/config",
            "/api/v1/audit"
        ]
        
        # Methods that modify data
        self.modifying_methods = ["POST", "PUT", "PATCH", "DELETE"]
        
        # Rate limiting for audit logs
        self.max_requests_per_minute = 1000
        self.request_counts = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process HTTP request and response with audit logging"""
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Check if path should be audited
        should_audit = self._should_audit_request(request)
        
        # Extract user information
        user_info = await self._extract_user_info(request)
        
        # Create audit context
        audit_context = AuditContext(
            user_id=user_info.get("user_id"),
            user_email=user_info.get("user_email"),
            user_role=user_info.get("user_role"),
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            session_id=request.headers.get("x-session-id"),
            request_id=request_id,
            endpoint=str(request.url.path),
            method=request.method
        )
        
        # Set audit context for this request
        audit_service.set_context(audit_context)
        
        # Process request
        response = None
        error_message = None
        
        try:
            response = await call_next(request)
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Request {request_id} failed: {e}")
            raise
        
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log audit event if needed
            if should_audit:
                await self._log_request_audit(
                    request=request,
                    response=response,
                    duration_ms=duration_ms,
                    error_message=error_message,
                    audit_context=audit_context
                )
        
        return response
    
    def _should_audit_request(self, request: Request) -> bool:
        """Determine if request should be audited"""
        path = request.url.path
        method = request.method
        
        # Always audit sensitive endpoints
        for sensitive_path in self.sensitive_endpoints:
            if path.startswith(sensitive_path):
                return True
        
        # Always audit modifying operations
        if method in self.modifying_methods:
            return True
        
        # Skip excluded paths
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return False
        
        # Audit API calls
        if path.startswith("/api/"):
            return True
        
        return False
    
    async def _extract_user_info(self, request: Request) -> dict:
        """Extract user information from request"""
        user_info = {
            "user_id": None,
            "user_email": None,
            "user_role": None
        }
        
        try:
            # Try to get user from Authorization header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                
                # Verify token
                token_data = auth_manager.verify_token(token)
                if token_data:
                    # Get database session
                    db = next(get_db())
                    try:
                        # Get user from database
                        user = db.query(User).filter(User.id == token_data.user_id).first()
                        if user and user.is_active:
                            user_info["user_id"] = user.id
                            user_info["user_email"] = user.email
                            user_info["user_role"] = user.role
                    finally:
                        db.close()
            
            # Try to get user from session or other sources
            # This can be extended based on your authentication mechanism
            
        except Exception as e:
            logger.debug(f"Could not extract user info: {e}")
        
        return user_info
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _log_request_audit(
        self,
        request: Request,
        response: Optional[Response],
        duration_ms: float,
        error_message: Optional[str],
        audit_context: AuditContext
    ):
        """Log audit event for HTTP request"""
        try:
            # Determine success status
            success = response is not None and 200 <= response.status_code < 400
            
            # Determine audit level based on status
            if error_message or (response and response.status_code >= 500):
                level = AuditLevel.ERROR
            elif response and response.status_code >= 400:
                level = AuditLevel.WARNING
            else:
                level = AuditLevel.INFO
            
            # Determine action based on method and endpoint
            action = self._determine_audit_action(request, response)
            
            # Determine category
            category = self._determine_audit_category(request)
            
            # Create description
            status_code = response.status_code if response else "ERROR"
            description = f"{request.method} {request.url.path} - {status_code}"
            
            # Prepare metadata
            metadata = {
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "status_code": response.status_code if response else None,
                "response_size": response.headers.get("content-length") if response else None
            }
            
            # Remove sensitive headers
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                metadata["headers"].pop(header, None)
            
            # Log the audit event
            audit_service.log(
                action=action,
                category=category,
                level=level,
                description=description,
                resource_type="api_endpoint",
                resource_id=request.url.path,
                metadata=metadata,
                success=success,
                error_message=error_message,
                duration_ms=duration_ms,
                context=audit_context
            )
            
        except Exception as e:
            logger.error(f"Error logging request audit: {e}")
    
    def _determine_audit_action(self, request: Request, response: Optional[Response]) -> AuditAction:
        """Determine audit action based on request"""
        path = request.url.path
        method = request.method
        
        # Authentication endpoints
        if "/auth/login" in path:
            return AuditAction.LOGIN if response and response.status_code == 200 else AuditAction.LOGIN_FAILED
        elif "/auth/logout" in path:
            return AuditAction.LOGOUT
        elif "/auth/register" in path:
            return AuditAction.USER_CREATE
        elif "/auth/reset-password" in path:
            return AuditAction.PASSWORD_RESET
        
        # User management
        elif "/users" in path:
            if method == "POST":
                return AuditAction.USER_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.USER_UPDATE
            elif method == "DELETE":
                return AuditAction.USER_DELETE
        
        # Membership management
        elif "/memberships" in path:
            if method == "POST":
                return AuditAction.MEMBERSHIP_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.MEMBERSHIP_UPDATE
            elif method == "DELETE":
                return AuditAction.MEMBERSHIP_DELETE
        
        # Payment management
        elif "/payments" in path:
            if method == "POST":
                return AuditAction.PAYMENT_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.PAYMENT_UPDATE
            elif method == "DELETE":
                return AuditAction.PAYMENT_DELETE
        
        # Class management
        elif "/classes" in path:
            if method == "POST":
                return AuditAction.CLASS_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.CLASS_UPDATE
            elif method == "DELETE":
                return AuditAction.CLASS_DELETE
        
        # Exercise management
        elif "/exercises" in path:
            if method == "POST":
                return AuditAction.EXERCISE_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.EXERCISE_UPDATE
            elif method == "DELETE":
                return AuditAction.EXERCISE_DELETE
        
        # Routine management
        elif "/routines" in path:
            if method == "POST":
                return AuditAction.ROUTINE_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.ROUTINE_UPDATE
            elif method == "DELETE":
                return AuditAction.ROUTINE_DELETE
        
        # Configuration management
        elif "/config" in path:
            if method in ["PUT", "PATCH", "POST"]:
                return AuditAction.CONFIG_UPDATE
            elif method == "DELETE":
                return AuditAction.CONFIG_RESET
        
        # Data export/import
        elif "/export" in path:
            return AuditAction.DATA_EXPORT
        elif "/import" in path:
            return AuditAction.DATA_IMPORT
        
        # File operations
        elif "/upload" in path:
            return AuditAction.FILE_UPLOAD
        elif "/files" in path and method == "DELETE":
            return AuditAction.FILE_DELETE
        elif "/files" in path:
            return AuditAction.FILE_ACCESS
        
        # Default to API call
        return AuditAction.API_CALL
    
    def _determine_audit_category(self, request: Request) -> AuditCategory:
        """Determine audit category based on request"""
        path = request.url.path
        
        # Authentication and authorization
        if "/auth/" in path:
            return AuditCategory.AUTHENTICATION
        
        # System administration
        elif any(admin_path in path for admin_path in ["/config", "/health", "/audit"]):
            return AuditCategory.SYSTEM_ADMINISTRATION
        
        # Security-related
        elif any(sec_path in path for sec_path in ["/security", "/permissions"]):
            return AuditCategory.SECURITY
        
        # Data modification
        elif request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return AuditCategory.DATA_MODIFICATION
        
        # Data access
        elif request.method == "GET":
            return AuditCategory.DATA_ACCESS
        
        # Business operations
        elif any(biz_path in path for biz_path in ["/payments", "/memberships", "/classes"]):
            return AuditCategory.BUSINESS_OPERATION
        
        # User activity
        elif "/users" in path:
            return AuditCategory.USER_ACTIVITY
        
        # Default to API usage
        return AuditCategory.API_USAGE

class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Specialized middleware for security event detection"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Suspicious patterns
        self.suspicious_patterns = [
            "../",  # Path traversal
            "<script",  # XSS attempts
            "union select",  # SQL injection
            "drop table",  # SQL injection
            "exec(",  # Code injection
            "eval(",  # Code injection
        ]
        
        # Rate limiting tracking
        self.request_counts = {}
        self.max_requests_per_minute = 100
        
        # Failed login tracking
        self.failed_logins = {}
        self.max_failed_logins = 5
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor for security threats"""
        
        # Check for suspicious patterns
        await self._check_suspicious_patterns(request)
        
        # Check rate limiting
        await self._check_rate_limiting(request)
        
        # Process request
        response = await call_next(request)
        
        # Check for failed authentication
        await self._check_failed_authentication(request, response)
        
        return response
    
    async def _check_suspicious_patterns(self, request: Request):
        """Check for suspicious patterns in request"""
        try:
            # Check URL path
            path = request.url.path.lower()
            query = str(request.url.query).lower()
            
            for pattern in self.suspicious_patterns:
                if pattern in path or pattern in query:
                    audit_service.log_security_event(
                        action=AuditAction.SUSPICIOUS_ACTIVITY,
                        description=f"Suspicious pattern detected: {pattern}",
                        level=AuditLevel.WARNING,
                        metadata={
                            "pattern": pattern,
                            "path": request.url.path,
                            "query": str(request.url.query),
                            "user_agent": request.headers.get("user-agent")
                        }
                    )
                    break
            
        except Exception as e:
            logger.error(f"Error checking suspicious patterns: {e}")
    
    async def _check_rate_limiting(self, request: Request):
        """Check for rate limiting violations"""
        try:
            client_ip = self._get_client_ip(request)
            current_minute = datetime.now().replace(second=0, microsecond=0)
            
            # Initialize tracking for this IP
            if client_ip not in self.request_counts:
                self.request_counts[client_ip] = {}
            
            # Count requests for current minute
            if current_minute not in self.request_counts[client_ip]:
                self.request_counts[client_ip][current_minute] = 0
            
            self.request_counts[client_ip][current_minute] += 1
            
            # Check if rate limit exceeded
            if self.request_counts[client_ip][current_minute] > self.max_requests_per_minute:
                audit_service.log_security_event(
                    action=AuditAction.RATE_LIMIT_EXCEEDED,
                    description=f"Rate limit exceeded for IP {client_ip}",
                    level=AuditLevel.WARNING,
                    metadata={
                        "ip_address": client_ip,
                        "requests_count": self.request_counts[client_ip][current_minute],
                        "rate_limit": self.max_requests_per_minute
                    }
                )
            
            # Clean old entries
            cutoff_time = current_minute - timedelta(minutes=5)
            for ip in list(self.request_counts.keys()):
                self.request_counts[ip] = {
                    k: v for k, v in self.request_counts[ip].items()
                    if k >= cutoff_time
                }
                if not self.request_counts[ip]:
                    del self.request_counts[ip]
            
        except Exception as e:
            logger.error(f"Error checking rate limiting: {e}")
    
    async def _check_failed_authentication(self, request: Request, response: Response):
        """Check for failed authentication attempts"""
        try:
            if "/auth/login" in request.url.path and response.status_code == 401:
                client_ip = self._get_client_ip(request)
                current_time = datetime.now()
                
                # Initialize tracking for this IP
                if client_ip not in self.failed_logins:
                    self.failed_logins[client_ip] = []
                
                # Add failed login attempt
                self.failed_logins[client_ip].append(current_time)
                
                # Remove old attempts (older than 1 hour)
                cutoff_time = current_time - timedelta(hours=1)
                self.failed_logins[client_ip] = [
                    attempt for attempt in self.failed_logins[client_ip]
                    if attempt >= cutoff_time
                ]
                
                # Check if threshold exceeded
                if len(self.failed_logins[client_ip]) >= self.max_failed_logins:
                    audit_service.log_security_event(
                        action=AuditAction.SECURITY_BREACH_ATTEMPT,
                        description=f"Multiple failed login attempts from IP {client_ip}",
                        level=AuditLevel.CRITICAL,
                        metadata={
                            "ip_address": client_ip,
                            "failed_attempts": len(self.failed_logins[client_ip]),
                            "threshold": self.max_failed_logins,
                            "time_window": "1 hour"
                        }
                    )
            
        except Exception as e:
            logger.error(f"Error checking failed authentication: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"