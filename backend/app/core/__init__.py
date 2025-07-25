"""Core module for GymSystem backend.

This module contains the core functionality including:
- Configuration management
- Database setup and session management
- Authentication and authorization
- Utility functions
- Middleware components
"""

from .config import settings
from .database import (
    engine,
    SessionLocal,
    Base,
    get_db,
    create_tables,
    drop_tables,
    init_database
)
from .auth import (
    auth_manager,
    get_current_user,
    get_current_active_user,
    get_current_staff_user,
    get_current_admin_user,
    get_current_owner_user,
    require_permission,
    require_admin_access,
    require_user_management,
    require_class_management,
    require_routine_creation,
    require_staff_access,
    rate_limiter,
    session_manager,
    create_user_tokens,
    verify_refresh_token,
    hash_password,
    verify_password,
    generate_secure_token
)
from .utils import (
    ValidationUtils,
    FormatUtils,
    DateUtils,
    FileUtils,
    SecurityUtils,
    NotificationUtils,
    DataUtils,
    BusinessUtils
)
from .middleware import (
    SecurityMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    DatabaseMiddleware,
    MaintenanceMiddleware,
    CompressionMiddleware,
    UserContextMiddleware,
    APIVersionMiddleware,
    get_cors_middleware,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
    create_logging_middleware,
    create_rate_limit_middleware,
    create_maintenance_middleware,
    create_api_version_middleware
)

__all__ = [
    # Configuration
    "settings",
    
    # Database
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "create_tables",
    "drop_tables",
    "init_database",
    
    # Authentication
    "auth_manager",
    "get_current_user",
    "get_current_active_user",
    "get_current_staff_user",
    "get_current_admin_user",
    "get_current_owner_user",
    "require_permission",
    "require_admin_access",
    "require_user_management",
    "require_class_management",
    "require_routine_creation",
    "require_staff_access",
    "rate_limiter",
    "session_manager",
    "create_user_tokens",
    "verify_refresh_token",
    "hash_password",
    "verify_password",
    "generate_secure_token",
    
    # Utilities
    "ValidationUtils",
    "FormatUtils",
    "DateUtils",
    "FileUtils",
    "SecurityUtils",
    "NotificationUtils",
    "DataUtils",
    "BusinessUtils",
    
    # Middleware
    "SecurityMiddleware",
    "LoggingMiddleware",
    "RateLimitMiddleware",
    "DatabaseMiddleware",
    "MaintenanceMiddleware",
    "CompressionMiddleware",
    "UserContextMiddleware",
    "APIVersionMiddleware",
    "get_cors_middleware",
    "validation_exception_handler",
    "http_exception_handler",
    "general_exception_handler",
    "create_logging_middleware",
    "create_rate_limit_middleware",
    "create_maintenance_middleware",
    "create_api_version_middleware"
]