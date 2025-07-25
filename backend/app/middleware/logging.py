from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import time
import json


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware for request/response logging"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get request info
        request_id = getattr(request.state, 'request_id', 'unknown')
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(
            f"Request started - {method} {url} | "
            f"Client: {client_ip} | Request ID: {request_id}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed - {method} {url} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.4f}s | "
                f"Request ID: {request_id}"
            )
            
            return response
            
        except Exception as e:
            # Calculate processing time for errors
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed - {method} {url} | "
                f"Error: {str(e)} | "
                f"Time: {process_time:.4f}s | "
                f"Request ID: {request_id}"
            )
            
            # Re-raise the exception
            raise