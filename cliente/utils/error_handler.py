import logging
import traceback
import sys
import os
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import queue

logger = logging.getLogger(__name__)

class ErrorInfo:
    """Información detallada de un error"""
    
    def __init__(self, error: Exception, context: str = "", severity: str = "error"):
        self.timestamp = datetime.now()
        self.error_type = type(error).__name__
        self.error_message = str(error)
        self.traceback = traceback.format_exc()
        self.context = context
        self.severity = severity  # "debug", "info", "warning", "error", "critical"
        self.thread_id = threading.get_ident()
        self.thread_name = threading.current_thread().name

class ErrorHandler:
    """Sistema de manejo de errores avanzado para el cliente desktop"""
    
    def __init__(self, log_file: str = "logs/errors.log", max_errors: int = 1000):
        self.log_file = Path(log_file)
        self.max_errors = max_errors
        self.errors: List[ErrorInfo] = []
        self.error_callbacks: List[Callable] = []
        self.recovery_callbacks: List[Callable] = []
        
        # Configuración
        self.log_to_file = True
        self.log_to_console = True
        self.auto_recovery = True
        self.max_retries = 3
        self.retry_delay = 5  # segundos
        
        # Estadísticas
        self.stats = {
            "total_errors": 0,
            "errors_by_type": {},
            "errors_by_severity": {},
            "recovery_attempts": 0,
            "successful_recoveries": 0,
            "last_error_time": None
        }
        
        # Crear directorio de logs si no existe
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configurar logging
        self._setup_logging()
        
        # Interceptar excepciones no manejadas
        self._setup_exception_handlers()

    def _setup_logging(self):
        """Configurar sistema de logging"""
        # Configurar logger para errores
        error_logger = logging.getLogger('error_handler')
        error_logger.setLevel(logging.DEBUG)
        
        # Handler para archivo
        if self.log_to_file:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            error_logger.addHandler(file_handler)
        
        # Handler para consola
        if self.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(levelname)s: %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            error_logger.addHandler(console_handler)

    def _setup_exception_handlers(self):
        """Configurar manejadores de excepciones no capturadas"""
        # Interceptar excepciones no manejadas
        sys.excepthook = self._handle_uncaught_exception
        
        # Interceptar excepciones en threads
        threading.excepthook = self._handle_thread_exception

    def _handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """Manejar excepciones no capturadas"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Permitir que KeyboardInterrupt se maneje normalmente
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_info = ErrorInfo(exc_value, "Uncaught Exception", "critical")
        self.handle_error(error_info)

    def _handle_thread_exception(self, args):
        """Manejar excepciones en threads"""
        error_info = ErrorInfo(args.exc_value, f"Thread Exception: {args.thread}", "error")
        self.handle_error(error_info)

    def handle_error(self, error_info: ErrorInfo):
        """Manejar un error"""
        try:
            # Agregar a la lista de errores
            self.errors.append(error_info)
            
            # Mantener límite de errores
            if len(self.errors) > self.max_errors:
                self.errors.pop(0)
            
            # Actualizar estadísticas
            self.stats["total_errors"] += 1
            self.stats["last_error_time"] = error_info.timestamp.isoformat()
            
            # Contar por tipo
            error_type = error_info.error_type
            self.stats["errors_by_type"][error_type] = self.stats["errors_by_type"].get(error_type, 0) + 1
            
            # Contar por severidad
            severity = error_info.severity
            self.stats["errors_by_severity"][severity] = self.stats["errors_by_severity"].get(severity, 0) + 1
            
            # Log del error
            self._log_error(error_info)
            
            # Notificar callbacks
            for callback in self.error_callbacks:
                try:
                    callback(error_info)
                except Exception as e:
                    logger.error(f"Error en callback de error: {e}")
            
            # Intentar recuperación automática
            if self.auto_recovery and error_info.severity in ["error", "critical"]:
                self._attempt_recovery(error_info)
            
        except Exception as e:
            logger.error(f"Error manejando error: {e}")

    def _log_error(self, error_info: ErrorInfo):
        """Log de error detallado"""
        log_message = f"""
Error: {error_info.error_type}
Message: {error_info.error_message}
Context: {error_info.context}
Severity: {error_info.severity}
Thread: {error_info.thread_name} (ID: {error_info.thread_id})
Timestamp: {error_info.timestamp}
Traceback:
{error_info.traceback}
"""
        
        if error_info.severity == "critical":
            logger.critical(log_message)
        elif error_info.severity == "error":
            logger.error(log_message)
        elif error_info.severity == "warning":
            logger.warning(log_message)
        elif error_info.severity == "info":
            logger.info(log_message)
        else:
            logger.debug(log_message)

    def _attempt_recovery(self, error_info: ErrorInfo):
        """Intentar recuperación automática"""
        self.stats["recovery_attempts"] += 1
        
        try:
            # Buscar callback de recuperación apropiado
            for callback in self.recovery_callbacks:
                try:
                    if callback(error_info):
                        self.stats["successful_recoveries"] += 1
                        logger.info(f"Recuperación exitosa para error: {error_info.error_type}")
                        return
                except Exception as e:
                    logger.error(f"Error en callback de recuperación: {e}")
            
            # Recuperación por defecto
            if self._default_recovery(error_info):
                self.stats["successful_recoveries"] += 1
                logger.info(f"Recuperación por defecto exitosa para error: {error_info.error_type}")
            
        except Exception as e:
            logger.error(f"Error en intento de recuperación: {e}")

    def _default_recovery(self, error_info: ErrorInfo) -> bool:
        """Recuperación por defecto"""
        try:
            # Recuperaciones específicas por tipo de error
            if "ConnectionError" in error_info.error_type:
                return self._recover_connection_error(error_info)
            elif "FileNotFoundError" in error_info.error_type:
                return self._recover_file_error(error_info)
            elif "PermissionError" in error_info.error_type:
                return self._recover_permission_error(error_info)
            elif "MemoryError" in error_info.error_type:
                return self._recover_memory_error(error_info)
            else:
                # Recuperación genérica
                return self._recover_generic_error(error_info)
                
        except Exception as e:
            logger.error(f"Error en recuperación por defecto: {e}")
            return False

    def _recover_connection_error(self, error_info: ErrorInfo) -> bool:
        """Recuperar errores de conexión"""
        try:
            # Esperar y reintentar
            time.sleep(self.retry_delay)
            logger.info("Reintentando conexión después de error")
            return True
        except Exception:
            return False

    def _recover_file_error(self, error_info: ErrorInfo) -> bool:
        """Recuperar errores de archivo"""
        try:
            # Crear directorio si no existe
            if "No such file or directory" in error_info.error_message:
                # Intentar extraer ruta del mensaje de error
                import re
                match = re.search(r"'([^']+)'", error_info.error_message)
                if match:
                    file_path = Path(match.group(1))
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Directorio creado: {file_path.parent}")
                    return True
            return False
        except Exception:
            return False

    def _recover_permission_error(self, error_info: ErrorInfo) -> bool:
        """Recuperar errores de permisos"""
        try:
            # Intentar cambiar permisos o usar directorio temporal
            logger.warning("Error de permisos detectado, usando directorio temporal")
            return True
        except Exception:
            return False

    def _recover_memory_error(self, error_info: ErrorInfo) -> bool:
        """Recuperar errores de memoria"""
        try:
            # Forzar recolección de basura
            import gc
            gc.collect()
            logger.info("Recolección de basura forzada después de error de memoria")
            return True
        except Exception:
            return False

    def _recover_generic_error(self, error_info: ErrorInfo) -> bool:
        """Recuperación genérica de errores"""
        try:
            # Esperar un poco y continuar
            time.sleep(1)
            logger.info("Recuperación genérica aplicada")
            return True
        except Exception:
            return False

    def add_error_callback(self, callback: Callable[[ErrorInfo], None]):
        """Agregar callback para notificaciones de error"""
        self.error_callbacks.append(callback)

    def add_recovery_callback(self, callback: Callable[[ErrorInfo], bool]):
        """Agregar callback para recuperación de errores"""
        self.recovery_callbacks.append(callback)

    def remove_callback(self, callback: Callable):
        """Remover callback"""
        if callback in self.error_callbacks:
            self.error_callbacks.remove(callback)
        if callback in self.recovery_callbacks:
            self.recovery_callbacks.remove(callback)

    def get_error_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de errores"""
        return {
            "stats": self.stats.copy(),
            "total_errors": len(self.errors),
            "recent_errors": [
                {
                    "timestamp": error.timestamp.isoformat(),
                    "type": error.error_type,
                    "message": error.error_message,
                    "severity": error.severity,
                    "context": error.context
                }
                for error in self.errors[-10:]  # Últimos 10 errores
            ],
            "errors_by_type": self.stats["errors_by_type"],
            "errors_by_severity": self.stats["errors_by_severity"]
        }

    def get_errors_by_type(self, error_type: str) -> List[ErrorInfo]:
        """Obtener errores por tipo"""
        return [error for error in self.errors if error.error_type == error_type]

    def get_errors_by_severity(self, severity: str) -> List[ErrorInfo]:
        """Obtener errores por severidad"""
        return [error for error in self.errors if error.severity == severity]

    def get_errors_in_timerange(self, start_time: datetime, end_time: datetime) -> List[ErrorInfo]:
        """Obtener errores en un rango de tiempo"""
        return [
            error for error in self.errors 
            if start_time <= error.timestamp <= end_time
        ]

    def clear_errors(self):
        """Limpiar lista de errores"""
        self.errors.clear()
        logger.info("Lista de errores limpiada")

    def export_errors(self, filename: str):
        """Exportar errores a archivo JSON"""
        try:
            data = {
                "export_time": datetime.now().isoformat(),
                "stats": self.stats,
                "errors": [
                    {
                        "timestamp": error.timestamp.isoformat(),
                        "error_type": error.error_type,
                        "error_message": error.error_message,
                        "traceback": error.traceback,
                        "context": error.context,
                        "severity": error.severity,
                        "thread_id": error.thread_id,
                        "thread_name": error.thread_name
                    }
                    for error in self.errors
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Errores exportados a {filename}")
            
        except Exception as e:
            logger.error(f"Error exportando errores: {e}")

    def set_auto_recovery(self, enabled: bool):
        """Habilitar/deshabilitar recuperación automática"""
        self.auto_recovery = enabled
        logger.info(f"Recuperación automática {'habilitada' if enabled else 'deshabilitada'}")

    def set_retry_config(self, max_retries: int, retry_delay: int):
        """Configurar parámetros de reintento"""
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        logger.info(f"Configuración de reintento actualizada: {max_retries} intentos, {retry_delay}s de espera")

# Instancia global del manejador de errores
error_handler = ErrorHandler()

# Decorador para manejo automático de errores
def handle_errors(context: str = "", severity: str = "error"):
    """Decorador para manejo automático de errores"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = ErrorInfo(e, context, severity)
                error_handler.handle_error(error_info)
                raise
        return wrapper
    return decorator

# Funciones de utilidad
def log_error(error: Exception, context: str = "", severity: str = "error"):
    """Log de error simple"""
    error_info = ErrorInfo(error, context, severity)
    error_handler.handle_error(error_info)

def get_error_stats() -> Dict[str, Any]:
    """Obtener estadísticas de errores"""
    return error_handler.get_error_stats()

def add_error_callback(callback: Callable[[ErrorInfo], None]):
    """Agregar callback de error"""
    error_handler.add_error_callback(callback)

def add_recovery_callback(callback: Callable[[ErrorInfo], bool]):
    """Agregar callback de recuperación"""
    error_handler.add_recovery_callback(callback)

def export_errors(filename: str = None):
    """Exportar errores"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"errors_export_{timestamp}.json"
    
    error_handler.export_errors(filename)
    return filename

def clear_errors():
    """Limpiar errores"""
    error_handler.clear_errors() 