"""
Middleware global para manejo de errores y excepciones
"""
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware que captura y maneja todas las excepciones de la aplicación
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self.handle_exception(request, exc)
    
    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        Maneja las excepciones y retorna una respuesta JSON consistente
        """
        # Log del error
        logger.error(
            f"Error en {request.method} {request.url.path}: {str(exc)}",
            exc_info=True,
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "user_id": getattr(request.state, "user_id", None),
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
            }
        )
        
        # Determinar el tipo de error y construir respuesta
        if isinstance(exc, HTTPException):
            return self.handle_http_exception(exc)
        elif isinstance(exc, ValidationError):
            return self.handle_validation_error(exc)
        elif isinstance(exc, IntegrityError):
            return self.handle_integrity_error(exc)
        elif isinstance(exc, SQLAlchemyError):
            return self.handle_database_error(exc)
        else:
            return self.handle_generic_error(exc)
    
    def handle_http_exception(self, exc: HTTPException) -> JSONResponse:
        """Maneja excepciones HTTP de FastAPI"""
        return JSONResponse(
            status_code=exc.status_code,
            content=self.create_error_response(
                error_type="http_error",
                message=exc.detail,
                status_code=exc.status_code
            ),
            headers=exc.headers
        )
    
    def handle_validation_error(self, exc: ValidationError) -> JSONResponse:
        """Maneja errores de validación de Pydantic"""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=self.create_error_response(
                error_type="validation_error",
                message="Error de validación en los datos enviados",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                details={"validation_errors": errors}
            )
        )
    
    def handle_integrity_error(self, exc: IntegrityError) -> JSONResponse:
        """Maneja errores de integridad de base de datos"""
        message = "Error de integridad en la base de datos"
        
        # Personalizar mensaje según el tipo de error
        error_str = str(exc.orig).lower() if exc.orig else str(exc).lower()
        if "unique constraint" in error_str or "duplicate" in error_str:
            message = "El registro ya existe o viola una restricción única"
        elif "foreign key" in error_str:
            message = "Error de referencia: el registro está relacionado con otros datos"
        elif "not null" in error_str:
            message = "Faltan campos obligatorios"
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=self.create_error_response(
                error_type="integrity_error",
                message=message,
                status_code=status.HTTP_409_CONFLICT,
                details={"database_error": str(exc.orig) if exc.orig else str(exc)}
            )
        )
    
    def handle_database_error(self, exc: SQLAlchemyError) -> JSONResponse:
        """Maneja errores generales de base de datos"""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=self.create_error_response(
                error_type="database_error",
                message="Error al acceder a la base de datos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={"error": "Error interno del servidor"}
            )
        )
    
    def handle_generic_error(self, exc: Exception) -> JSONResponse:
        """Maneja errores genéricos no capturados"""
        # En producción, no exponer detalles del error
        from app.core.config import settings
        
        details = {}
        if settings.DEBUG:
            details = {
                "error": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc().split("\n")
            }
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=self.create_error_response(
                error_type="internal_error",
                message="Error interno del servidor",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details=details
            )
        )
    
    def create_error_response(
        self,
        error_type: str,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crea una respuesta de error consistente
        """
        response = {
            "error": {
                "type": error_type,
                "message": message,
                "status_code": status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if details:
            response["error"]["details"] = details
        
        return jsonable_encoder(response)


class CustomHTTPException(HTTPException):
    """
    Excepción HTTP personalizada con soporte para detalles adicionales
    """
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_type: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_type = error_type or "custom_error"
        self.extra_details = kwargs


# Excepciones personalizadas comunes

class NotFoundException(CustomHTTPException):
    """Recurso no encontrado"""
    def __init__(self, resource: str, identifier: Any = None):
        detail = f"{resource} no encontrado"
        if identifier:
            detail += f" con identificador: {identifier}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_type="not_found"
        )


class UnauthorizedException(CustomHTTPException):
    """No autorizado"""
    def __init__(self, detail: str = "No autorizado para realizar esta acción"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_type="unauthorized",
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(CustomHTTPException):
    """Acceso prohibido"""
    def __init__(self, detail: str = "No tienes permisos para acceder a este recurso"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_type="forbidden"
        )


class BadRequestException(CustomHTTPException):
    """Solicitud incorrecta"""
    def __init__(self, detail: str, **kwargs):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_type="bad_request",
            **kwargs
        )


class ConflictException(CustomHTTPException):
    """Conflicto con el estado actual"""
    def __init__(self, detail: str, **kwargs):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_type="conflict",
            **kwargs
        )


class ServiceUnavailableException(CustomHTTPException):
    """Servicio no disponible"""
    def __init__(self, detail: str = "Servicio temporalmente no disponible", retry_after: Optional[int] = None):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_type="service_unavailable",
            headers=headers
        ) 