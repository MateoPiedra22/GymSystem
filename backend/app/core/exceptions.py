from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger
import traceback


class GymSystemException(Exception):
    """Base exception for GymSystem"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(GymSystemException):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)


class AuthorizationError(GymSystemException):
    """Authorization related errors"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)


class NotFoundError(GymSystemException):
    """Resource not found errors"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404)


class ValidationError(GymSystemException):
    """Validation related errors"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, 422)


class DatabaseError(GymSystemException):
    """Database related errors"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, 500)


async def gym_system_exception_handler(request: Request, exc: GymSystemException):
    """Handle custom GymSystem exceptions"""
    logger.error(f"GymSystem Exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "type": exc.__class__.__name__
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "type": "HTTPException"
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions"""
    logger.warning(f"Validation Exception: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation failed",
            "details": exc.errors(),
            "type": "ValidationError"
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled Exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "type": "InternalServerError"
        }
    )


def setup_exception_handlers(app: FastAPI):
    """Setup all exception handlers for the FastAPI app"""
    app.add_exception_handler(GymSystemException, gym_system_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers configured")