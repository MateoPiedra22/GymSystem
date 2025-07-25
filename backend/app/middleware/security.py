from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from loguru import logger
import time
import uuid


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for adding security headers and request tracking"""
    
    async def dispatch(self, request: Request, call_next):
        # Add request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add security headers
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Add CORS headers if not already present
            if "Access-Control-Allow-Origin" not in response.headers:
                response.headers["Access-Control-Allow-Origin"] = "*"
            
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            # Return a basic error response
            return StarletteResponse(
                content="Internal Server Error",
                status_code=500,
                headers={
                    "X-Request-ID": request_id,
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                }
            )