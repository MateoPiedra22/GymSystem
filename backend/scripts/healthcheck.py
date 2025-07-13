#!/usr/bin/env python3
"""
Health Check Script para el Backend
Verifica el estado de todos los servicios críticos
"""
import os
import sys
import time
import requests
import psycopg2
import redis
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir el directorio parent al path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.redis import redis_client

def check_database():
    """Verificar conexión a la base de datos"""
    try:
        # Verificar conexión directa
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connect_timeout=5
        )
        conn.close()
        
        # Verificar con SQLAlchemy
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        logger.info("✅ Base de datos: OK")
        return True
    except Exception as e:
        logger.error(f"❌ Base de datos: ERROR - {e}")
        return False

def check_redis():
    """Verificar conexión a Redis"""
    try:
        # Verificar conexión directa
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        r.ping()
        
        # Verificar con cliente de la app (opcional)
        # if redis_client:
        #     try:
        #         redis_client.ping()
        #     except:
        #         pass
        
        logger.info("✅ Redis: OK")
        return True
    except Exception as e:
        logger.error(f"❌ Redis: ERROR - {e}")
        return False

def check_api_endpoints():
    """Verificar endpoints críticos de la API"""
    try:
        base_url = f"http://localhost:{settings.SERVER_PORT}"
        
        # Health check básico
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ API Health Check: OK")
            return True
        else:
            logger.error(f"❌ API Health Check: ERROR - Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ API Health Check: ERROR - {e}")
        return False

def check_disk_space():
    """Verificar espacio en disco"""
    try:
        import shutil
        
        # Verificar directorio de uploads
        uploads_dir = Path(settings.UPLOAD_DIR)
        if uploads_dir.exists():
            total, used, free = shutil.disk_usage(uploads_dir)
            free_gb = free / (1024**3)
            
            if free_gb > 1:  # Al menos 1GB libre
                logger.info(f"✅ Espacio en disco: OK ({free_gb:.1f}GB libre)")
                return True
            else:
                logger.warning(f"⚠️ Espacio en disco: BAJO ({free_gb:.1f}GB libre)")
                return False
        else:
            logger.warning("⚠️ Directorio de uploads no existe")
            return True
    except Exception as e:
        logger.error(f"❌ Verificación de disco: ERROR - {e}")
        return False

def check_memory_usage():
    """Verificar uso de memoria"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if memory_percent < 90:  # Menos del 90% de uso
            logger.info(f"✅ Memoria: OK ({memory_percent:.1f}% usado)")
            return True
        else:
            logger.warning(f"⚠️ Memoria: ALTO ({memory_percent:.1f}% usado)")
            return False
    except Exception as e:
        logger.error(f"❌ Verificación de memoria: ERROR - {e}")
        return False

def check_log_files():
    """Verificar archivos de log"""
    try:
        log_file = Path(settings.LOG_FILE)
        if log_file.exists():
            # Verificar que el archivo sea escribible
            with open(log_file, 'a') as f:
                f.write("")
            logger.info("✅ Archivos de log: OK")
            return True
        else:
            logger.warning("⚠️ Archivo de log no existe")
            return True
    except Exception as e:
        logger.error(f"❌ Verificación de logs: ERROR - {e}")
        return False

def main():
    """Función principal de health check"""
    logger.info("🔍 Iniciando health check del backend...")
    
    checks = [
        ("Base de Datos", check_database),
        ("Redis", check_redis),
        ("API Endpoints", check_api_endpoints),
        ("Espacio en Disco", check_disk_space),
        ("Memoria", check_memory_usage),
        ("Archivos de Log", check_log_files),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"❌ Error en check {name}: {e}")
            results.append((name, False))
    
    # Resumen
    successful_checks = sum(1 for _, result in results if result)
    total_checks = len(results)
    
    logger.info(f"📊 Resumen: {successful_checks}/{total_checks} checks exitosos")
    
    if successful_checks == total_checks:
        logger.info("✅ Todos los servicios están funcionando correctamente")
        sys.exit(0)
    else:
        failed_checks = [name for name, result in results if not result]
        logger.error(f"❌ Servicios con problemas: {', '.join(failed_checks)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 