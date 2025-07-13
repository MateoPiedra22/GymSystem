"""
Configuración de logging para el sistema de gimnasio
MEJORADO: Rotación automática, compresión, limpieza de logs antiguos
"""
import os
import logging
import logging.handlers
import gzip
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import threading
import time

def compress_log_file(log_file: Path) -> None:
    """
    Comprime un archivo de log usando gzip
    
    Args:
        log_file: Ruta del archivo de log a comprimir
    """
    try:
        if log_file.exists() and log_file.stat().st_size > 0:
            with open(log_file, 'rb') as f_in:
                with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            log_file.unlink()  # Eliminar archivo original
    except Exception as e:
        logging.error(f"Error comprimiendo archivo de log {log_file}: {e}")

def cleanup_old_logs(log_dir: Path, max_days: int = 30) -> None:
    """
    Limpia logs antiguos
    
    Args:
        log_dir: Directorio de logs
        max_days: Días máximos a mantener
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=max_days)
        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                logging.info(f"Log antiguo eliminado: {log_file}")
    except Exception as e:
        logging.error(f"Error limpiando logs antiguos: {e}")

def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/gym_app.log",
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    compress_logs: bool = True,
    cleanup_days: int = 30
) -> None:
    """
    Configura el sistema de logging mejorado
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta del archivo de log
        log_format: Formato de los mensajes de log
        max_bytes: Tamaño máximo del archivo de log antes de rotar
        backup_count: Número de archivos de backup a mantener
        compress_logs: Si comprimir logs rotados
        cleanup_days: Días máximos a mantener logs
    """
    # Crear directorio de logs si no existe
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar nivel de logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configurar formato
    formatter = logging.Formatter(log_format)
    
    # Configurar handler de archivo con rotación mejorada
    class CompressedRotatingFileHandler(logging.handlers.RotatingFileHandler):
        def doRollover(self):
            super().doRollover()
            if compress_logs:
                # Comprimir el archivo anterior
                if self.backupCount > 0:
                    for i in range(self.backupCount - 1, 0, -1):
                        sfn = f"{self.baseFilename}.{i}"
                        dfn = f"{self.baseFilename}.{i + 1}"
                        if os.path.exists(sfn):
                            if os.path.exists(dfn):
                                os.remove(dfn)
                            os.rename(sfn, dfn)
                    dfn = f"{self.baseFilename}.1"
                    if os.path.exists(dfn):
                        compress_log_file(Path(dfn))
    
    file_handler = CompressedRotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)
    
    # Configurar handler de consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configurar loggers específicos
    loggers_to_configure = [
        'uvicorn',
        'uvicorn.access',
        'uvicorn.error',
        'sqlalchemy.engine',
        'sqlalchemy.pool',
        'fastapi',
        'app'
    ]
    
    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.setLevel(numeric_level)
        
        # Limpiar handlers existentes
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.propagate = False
    
    # Configurar limpieza automática de logs
    def auto_cleanup():
        while True:
            try:
                time.sleep(24 * 60 * 60)  # Ejecutar cada 24 horas
                cleanup_old_logs(log_dir, cleanup_days)
            except Exception as e:
                logging.error(f"Error en limpieza automática: {e}")
    
    cleanup_thread = threading.Thread(target=auto_cleanup, daemon=True)
    cleanup_thread.start()
    
    # Ejecutar limpieza inicial
    cleanup_old_logs(log_dir, cleanup_days)

def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)

def log_security_event(event_type: str, details: str, user_id: Optional[str] = None, ip_address: Optional[str] = None) -> None:
    """
    Registra eventos de seguridad
    
    Args:
        event_type: Tipo de evento (login_failed, unauthorized_access, etc.)
        details: Detalles del evento
        user_id: ID del usuario (opcional)
        ip_address: Dirección IP (opcional)
    """
    security_logger = get_logger('security')
    log_message = f"SECURITY_EVENT: {event_type} | {details}"
    if user_id:
        log_message += f" | User: {user_id}"
    if ip_address:
        log_message += f" | IP: {ip_address}"
    security_logger.warning(log_message)

def log_audit_event(action: str, resource: str, user_id: Optional[str] = None, details: Optional[str] = None) -> None:
    """
    Registra eventos de auditoría
    
    Args:
        action: Acción realizada (create, update, delete, view)
        resource: Recurso afectado
        user_id: ID del usuario (opcional)
        details: Detalles adicionales (opcional)
    """
    audit_logger = get_logger('audit')
    log_message = f"AUDIT: {action} | Resource: {resource}"
    if user_id:
        log_message += f" | User: {user_id}"
    if details:
        log_message += f" | Details: {details}"
    audit_logger.info(log_message)

# Configurar logging por defecto
setup_logging() 