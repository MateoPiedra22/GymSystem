"""
Middleware para generar IDs únicos de requests y contexto de logging
"""
import uuid
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware que agrega un ID único a cada request y mide el tiempo de ejecución
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generar ID único para el request
        request_id = str(uuid.uuid4())
        
        # Agregar a los headers y al estado del request
        request.state.request_id = request_id
        
        # Obtener información del usuario si está disponible
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = getattr(request.state.user, "id", None)
        
        # Medir tiempo de ejecución
        start_time = time.time()
        
        try:
            # Log del inicio del request
            logger.info(
                "Request started",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                user_agent=request.headers.get("user-agent"),
                user_id=user_id,
                client_ip=request.client.host if request.client else None
            )
            
            # Procesar request
            response = await call_next(request)
            
            # Calcular tiempo de ejecución
            execution_time = time.time() - start_time
            
            # Agregar headers de respuesta
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Execution-Time"] = f"{execution_time:.3f}s"
            
            # Log del final del request
            logger.info(
                "Request completed",
                request_id=request_id,
                status_code=response.status_code,
                execution_time=execution_time,
                user_id=user_id
            )
            
            return response
            
        except Exception as exc:
            execution_time = time.time() - start_time
            
            # Log del error
            logger.error(
                "Request failed",
                request_id=request_id,
                execution_time=execution_time,
                error=str(exc),
                error_type=type(exc).__name__,
                user_id=user_id
            )
            
            raise  # Re-lanzar la excepción para que sea manejada por el error handler 