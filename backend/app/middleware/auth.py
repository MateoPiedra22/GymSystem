"""
Middleware de autenticación y funciones relacionadas
"""
from datetime import datetime
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

import jwt
from app.core.config import settings

class JWTAuthMiddleware:
    """
    Middleware para autenticación JWT.
    Este middleware se ha desactivado temporalmente en favor de la inyección
    de dependencias de FastAPI para gestionar la autenticación por ruta.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            try:
                token_type, token = auth_header.split()
                if token_type.lower() == "bearer":
                    # Validar token con manejo de errores mejorado
                    payload = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=[settings.ALGORITHM],
                        options={
                            "verify_signature": True,
                            "verify_exp": True,
                            "verify_iat": True,
                            "require": ["exp", "iat", "sub", "iss", "aud"]
                        }
                    )
                    scope["user"] = {"id": payload.get("sub")}
            except (ValueError, jwt.PyJWTError) as e:
                # Log del error para debugging
                logger.warning(f"Token JWT inválido: {str(e)}")
                scope["user"] = {"id": None}
        else:
            scope["user"] = {"id": None}

        await self.app(scope, receive, send)
