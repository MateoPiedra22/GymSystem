import asyncio
import logging
from typing import Callable, Any, Dict, List, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
import time

logger = logging.getLogger(__name__)

class BackgroundTask:
    def __init__(self, func: Callable, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.id = f"{func.__name__}_{int(time.time())}"
        self.status = "pending"
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None

class BackgroundTaskManager:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, BackgroundTask] = {}
        self.task_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self.lock = threading.Lock()
        
        # Estadísticas
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "pending_tasks": 0,
            "running_tasks": 0
        }

    def start(self):
        """Iniciar el gestor de tareas en segundo plano"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("Gestor de tareas en segundo plano iniciado")

    def stop(self):
        """Detener el gestor de tareas en segundo plano"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.executor.shutdown(wait=True)
        logger.info("Gestor de tareas en segundo plano detenido")

    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """Enviar una tarea para ejecución en segundo plano"""
        task = BackgroundTask(func, *args, **kwargs)
        
        with self.lock:
            self.tasks[task.id] = task
            self.stats["total_tasks"] += 1
            self.stats["pending_tasks"] += 1
        
        self.task_queue.put(task)
        logger.info(f"Tarea enviada: {task.id}")
        return task.id

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtener el estado de una tarea"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                return {
                    "id": task.id,
                    "status": task.status,
                    "result": task.result,
                    "error": str(task.error) if task.error else None,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
        return None

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Obtener todas las tareas"""
        with self.lock:
            return [
                {
                    "id": task.id,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
                for task in self.tasks.values()
            ]

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del gestor de tareas"""
        with self.lock:
            return self.stats.copy()

    def cancel_task(self, task_id: str) -> bool:
        """Cancelar una tarea pendiente"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status == "pending":
                    task.status = "cancelled"
                    self.stats["pending_tasks"] -= 1
                    logger.info(f"Tarea cancelada: {task_id}")
                    return True
        return False

    def clear_completed_tasks(self, max_age_hours: int = 24):
        """Limpiar tareas completadas antiguas"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        tasks_to_remove = []
        
        with self.lock:
            for task_id, task in self.tasks.items():
                if (task.status in ["completed", "failed", "cancelled"] and 
                    task.completed_at and task.completed_at < cutoff_time):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
        
        logger.info(f"Limpiadas {len(tasks_to_remove)} tareas antiguas")

    def _worker_loop(self):
        """Bucle principal del worker"""
        while self.running:
            try:
                # Obtener tarea de la cola con timeout
                try:
                    task = self.task_queue.get(timeout=1)
                except queue.Empty:
                    continue

                # Actualizar estado
                with self.lock:
                    task.status = "running"
                    task.started_at = datetime.now()
                    self.stats["pending_tasks"] -= 1
                    self.stats["running_tasks"] += 1

                # Ejecutar tarea
                try:
                    logger.info(f"Ejecutando tarea: {task.id}")
                    task.result = self.executor.submit(task.func, *task.args, **task.kwargs).result()
                    task.status = "completed"
                    logger.info(f"Tarea completada: {task.id}")
                except Exception as e:
                    task.status = "failed"
                    task.error = e
                    logger.error(f"Error en tarea {task.id}: {e}")
                finally:
                    task.completed_at = datetime.now()
                    
                    # Actualizar estadísticas
                    with self.lock:
                        self.stats["running_tasks"] -= 1
                        if task.status == "completed":
                            self.stats["completed_tasks"] += 1
                        elif task.status == "failed":
                            self.stats["failed_tasks"] += 1

            except Exception as e:
                logger.error(f"Error en worker loop: {e}")

# Instancia global del gestor de tareas
task_manager = BackgroundTaskManager()

# Decorador para tareas en segundo plano
def background_task(func: Callable) -> Callable:
    """Decorador para ejecutar funciones como tareas en segundo plano"""
    def wrapper(*args, **kwargs):
        return task_manager.submit_task(func, *args, **kwargs)
    return wrapper

# Tareas predefinidas útiles
def cleanup_old_files():
    """Limpiar archivos antiguos del sistema"""
    try:
        import os
        from pathlib import Path
        
        uploads_dir = Path("uploads")
        if uploads_dir.exists():
            cutoff_time = datetime.now() - timedelta(days=30)
            deleted_count = 0
            
            for file_path in uploads_dir.rglob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
            
            logger.info(f"Limpiados {deleted_count} archivos antiguos")
            return {"deleted_files": deleted_count}
    except Exception as e:
        logger.error(f"Error limpiando archivos: {e}")
        raise

def generate_backup():
    """Generar backup de la base de datos"""
    try:
        import subprocess
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{timestamp}.sql"
        
        # Comando para PostgreSQL
        cmd = [
            "pg_dump",
            "-h", "localhost",
            "-U", "postgres",
            "-d", "gym_system",
            "-f", f"backups/{backup_file}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Backup generado: {backup_file}")
            return {"backup_file": backup_file, "status": "success"}
        else:
            raise Exception(f"Error en backup: {result.stderr}")
    except Exception as e:
        logger.error(f"Error generando backup: {e}")
        raise

def send_notifications():
    """Enviar notificaciones pendientes"""
    try:
        # Simular envío de notificaciones
        logger.info("Enviando notificaciones...")
        time.sleep(2)  # Simular trabajo
        return {"notifications_sent": 10}
    except Exception as e:
        logger.error(f"Error enviando notificaciones: {e}")
        raise

def update_statistics():
    """Actualizar estadísticas del sistema"""
    try:
        # Simular actualización de estadísticas
        logger.info("Actualizando estadísticas...")
        time.sleep(1)  # Simular trabajo
        
        # Cachear estadísticas básicas
        from app.core.cache import cache_manager, CacheKeys
        basic_stats = {
            "total_usuarios": 150,
            "total_clases": 25,
            "total_pagos": 1200,
            "ingresos_mes": 15000
        }
        cache_manager.set(CacheKeys.kpis(), basic_stats, expire=3600)  # 1 hora
        
        logger.info("Estadísticas actualizadas")
        return basic_stats
    except Exception as e:
        logger.error(f"Error actualizando estadísticas: {e}")
        raise

# Programar tareas recurrentes
def schedule_recurring_tasks():
    """Programar tareas que se ejecutan periódicamente"""
    def schedule_task(func, interval_seconds):
        def wrapper():
            while task_manager.running:
                try:
                    func()
                except Exception as e:
                    logger.error(f"Error en tarea recurrente {func.__name__}: {e}")
                time.sleep(interval_seconds)
        
        task_manager.submit_task(wrapper)
    
    # Tareas diarias
    schedule_task(cleanup_old_files, 24 * 60 * 60)  # Cada 24 horas
    schedule_task(generate_backup, 24 * 60 * 60)    # Cada 24 horas
    
    # Tareas cada hora
    schedule_task(send_notifications, 60 * 60)      # Cada hora
    schedule_task(update_statistics, 60 * 60)       # Cada hora 