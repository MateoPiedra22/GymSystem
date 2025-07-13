"""
Middleware especializado para detección de ataques
"""
import time
import logging
from typing import Dict, Set
from urllib.parse import unquote
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.redis import redis_client
from app.core.security import SecurityValidator

# Configurar logging
logger = logging.getLogger(__name__)

class AttackDetectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware especializado para detección de patrones de ataque
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Patrones de ataques conocidos
        self.attack_patterns = {
            'xss': [
                '<script', '</script>', 'javascript:', 'onload=', 'onerror=', 'onclick=',
                'eval(', 'alert(', 'document.cookie', 'window.location', 'innerHTML',
                'outerHTML', 'document.write', 'document.writeln', 'setTimeout',
                'setInterval', 'Function(', 'constructor', 'prototype', 'toString',
                'vbscript:', 'data:text/html', '&#x3C;script', '&#60;script',
                '\\u003Cscript', '\\x3Cscript', '\\074script', '\\074script'
            ],
            'lfi': [
                '../', '..\\', '/etc/passwd', '/proc/version', '/proc/self/environ',
                'boot.ini', 'windows/win.ini', 'windows/system32', 'c:\\windows',
                '/var/log/', '/var/www/', '/home/', '/root/', '~/.bashrc',
                '..%2F', '..%5C', '%2e%2e%2f', '%2e%2e%5c', '..%252f', '..%255c'
            ],
            'rfi': [
                'http://', 'https://', 'ftp://', 'data:', 'file://', 'gopher://',
                'dict://', 'ldap://', 'tftp://', 'php://', 'jar://', 'netdoc://',
                'mailto:', 'news:', 'nntp:', 'telnet://', 'ssh://', 'sftp://'
            ],
            'command_injection': [
                ';cat ', '|cat ', '&cat ', ';ls ', '|ls ', '&ls ', ';dir ', '|dir ',
                'wget ', 'curl ', 'nc ', 'netcat', 'python ', 'perl ', 'ruby ',
                'bash ', 'sh ', '/bin/', 'cmd.exe', 'powershell', 'whoami',
                'id ', 'pwd ', 'cd ', 'rm ', 'del ', 'copy ', 'move ', 'mkdir',
                'echo ', 'printf ', 'grep ', 'find ', 'xargs ', 'tee ', 'dd ',
                '; ', '| ', '& ', '&& ', '|| ', '`', '$()', '$(', ')', ';${IFS}',
                ';%20', '|%20', '&%20', ';%09', '|%09', '&%09'
            ],
            'sql_injection': [
                "' OR '1'='1", "' OR 1=1--", "' UNION SELECT", "'; DROP TABLE",
                "' OR 'x'='x", "admin'--", "admin'/*", "1' OR '1' = '1'",
                "1' AND '1' = '2'", "1' UNION SELECT NULL--", "1' ORDER BY 1--",
                "1' AND 1=1--", "1' AND 1=2--", "1' AND SLEEP(5)--",
                "1' AND (SELECT COUNT(*) FROM users)--", "1' AND ASCII(SUBSTRING(",
                "1' AND EXISTS(SELECT * FROM users)--", "1' AND (SELECT LENGTH(",
                "1' AND (SELECT SUBSTRING(", "1' AND (SELECT CONCAT(",
                "1' AND (SELECT GROUP_CONCAT(", "1' AND (SELECT LOAD_FILE(",
                "1' AND (SELECT INTO OUTFILE", "1' AND (SELECT INTO DUMPFILE"
            ],
            'path_traversal': [
                '....//', '....\\\\', '..%2F..%2F', '..%5C..%5C',
                '%2e%2e%2f%2e%2e%2f', '%2e%2e%5c%2e%2e%5c',
                '..%252f..%252f', '..%255c..%255c', '..%c0%af..%c0%af',
                '..%c1%9c..%c1%9c', '..%ef%bc%8f..%ef%bc%8f',
                '..%ef%bc%8c..%ef%bc%8c', '..%c0%2f..%c0%2f',
                '..%c1%af..%c1%af', '..%c0%5c..%c0%5c', '..%c1%9c..%c1%9c'
            ],
            'no_sql_injection': [
                '{"$ne": null}', '{"$ne": ""}', '{"$gt": ""}', '{"$lt": ""}',
                '{"$regex": ".*"}', '{"$where": "1==1"}', '{"$exists": true}',
                '{"$in": []}', '{"$nin": []}', '{"$or": []}', '{"$and": []}',
                '{"$not": {}}', '{"$nor": []}', '{"$all": []}', '{"$elemMatch": {}}',
                '{"$size": 0}', '{"$type": "string"}', '{"$text": {"$search": ""}}'
            ]
        }
    
    async def dispatch(self, request: Request, call_next):
        """Procesa cada petición detectando patrones de ataque"""
        # Obtener IP del cliente
        client_ip = self._get_client_ip(request)
        
        # Detectar patrones de ataque en URL
        raw_path = request.url.path
        raw_query = request.url.query
        url_path = unquote(f"{raw_path}?{raw_query}" if raw_query else raw_path)
        
        if self._detect_attack_patterns(url_path):
            logger.warning(f"Attack pattern detected in URL: {url_path} from IP: {client_ip}")
            await self._track_suspicious_activity(client_ip, "url_attack")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request"}
            )
        
        # Validar headers sospechosos
        if self._validate_headers(request):
            logger.warning(f"Suspicious headers from IP: {client_ip}")
            await self._track_suspicious_activity(client_ip, "header_attack")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid headers"}
            )
        
        return await call_next(request)
    
    def _detect_attack_patterns(self, text: str) -> bool:
        """Detecta patrones de ataque en texto"""
        text_lower = text.lower()
        
        for attack_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    logger.debug(f"Attack pattern detected: {attack_type} - {pattern}")
                    return True
        
        # Detectar inyección SQL usando SecurityValidator
        if SecurityValidator.detect_sql_injection(text):
            logger.debug("SQL injection pattern detected")
            return True
        
        return False
    
    def _validate_headers(self, request: Request) -> bool:
        """Valida headers sospechosos"""
        suspicious_headers = {
            'x-forwarded-host', 'x-originating-ip', 'x-remote-ip',
            'x-remote-addr', 'x-cluster-client-ip'
        }
        
        for header_name, header_value in request.headers.items():
            # Verificar headers sospechosos
            if header_name.lower() in suspicious_headers:
                logger.debug(f"Suspicious header: {header_name}")
                return True
            
            # Verificar patrones de ataque en valores de headers
            if self._detect_attack_patterns(header_value):
                logger.debug(f"Attack pattern in header {header_name}: {header_value}")
                return True
        
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtiene la IP real del cliente"""
        # Verificar headers de proxy
        for header in ['x-forwarded-for', 'x-real-ip', 'x-client-ip']:
            if header in request.headers:
                return request.headers[header].split(',')[0].strip()
        
        # IP directa
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _track_suspicious_activity(self, ip: str, activity_type: str):
        """Rastrea actividad sospechosa por IP usando Redis."""
        redis_conn = redis_client.get_client()
        if not redis_conn:
            logger.warning("Redis no disponible, no se puede rastrear actividad sospechosa.")
            return

        try:
            key = f"suspicious_ip:{ip}"
            
            # Incrementar el contador para el tipo de actividad específico
            current_count = await redis_conn.hincrby(key, activity_type, 1)
            
            # Establecer un TTL para la clave si es la primera vez que se registra
            if current_count == 1:
                await redis_conn.expire(key, 3600)  # Bloqueo temporal de 1 hora
            
            # Verificar si el total de actividades sospechosas excede el umbral
            all_activities = await redis_conn.hgetall(key)
            total_suspicious = sum(int(count) for count in all_activities.values())

            if total_suspicious > 10:
                logger.critical(f"IP {ip} has {total_suspicious} suspicious activities. Blocking for 1 hour.")
                await self._block_ip(ip, 3600) # Bloquear por 1 hora
        except Exception as e:
            logger.error(f"Error rastreando actividad sospechosa con Redis: {e}")

    async def _block_ip(self, ip: str, ttl_seconds: int):
        """Bloquea una IP usando Redis con un TTL."""
        redis_conn = redis_client.get_client()
        if not redis_conn:
            return
        try:
            await redis_conn.set(f"blocked_ip:{ip}", "true", ex=ttl_seconds)
        except Exception as e:
            logger.error(f"Error al bloquear la IP {ip} en Redis: {e}") 