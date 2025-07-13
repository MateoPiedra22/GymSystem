import os
import shutil
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
import zipfile
import hashlib

logger = logging.getLogger(__name__)

class BackupItem:
    """Elemento de backup individual"""
    
    def __init__(self, source_path: str, backup_type: str = "file"):
        self.source_path = source_path
        self.backup_type = backup_type  # "file", "directory", "database"
        self.last_backup = None
        self.backup_size = 0
        self.checksum = None
        self.enabled = True

class AutoBackup:
    """Sistema de backup automático para el cliente desktop"""
    
    def __init__(self, backup_dir: str = "backups", max_backups: int = 10):
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_items: Dict[str, BackupItem] = {}
        self.is_running = False
        self.backup_thread: Optional[threading.Thread] = None
        self.backup_interval = 3600  # 1 hora por defecto
        self.callbacks: List[Callable] = []
        
        # Configuración
        self.compress_backups = True
        self.verify_backups = True
        self.cleanup_old_backups = True
        self.backup_retention_days = 30
        
        # Estadísticas
        self.stats = {
            "total_backups": 0,
            "successful_backups": 0,
            "failed_backups": 0,
            "last_backup_time": None,
            "total_backup_size_mb": 0
        }
        
        # Crear directorio de backup si no existe
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Registrar elementos de backup por defecto
        self._register_default_items()

    def _register_default_items(self):
        """Registrar elementos de backup por defecto"""
        # Configuración del cliente
        config_path = "config/settings.json"
        if os.path.exists(config_path):
            self.add_backup_item(config_path, "config")
        
        # Logs
        logs_path = "logs"
        if os.path.exists(logs_path):
            self.add_backup_item(logs_path, "logs")
        
        # Datos locales
        data_path = "data"
        if os.path.exists(data_path):
            self.add_backup_item(data_path, "data")

    def add_backup_item(self, source_path: str, backup_type: str = "file") -> bool:
        """Agregar elemento para backup"""
        try:
            if not os.path.exists(source_path):
                logger.warning(f"Ruta de backup no existe: {source_path}")
                return False
            
            item = BackupItem(source_path, backup_type)
            self.backup_items[source_path] = item
            logger.info(f"Elemento de backup agregado: {source_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando elemento de backup: {e}")
            return False

    def remove_backup_item(self, source_path: str) -> bool:
        """Remover elemento de backup"""
        if source_path in self.backup_items:
            del self.backup_items[source_path]
            logger.info(f"Elemento de backup removido: {source_path}")
            return True
        return False

    def start_auto_backup(self, interval_hours: int = 1):
        """Iniciar backup automático"""
        if self.is_running:
            logger.warning("Backup automático ya está ejecutándose")
            return
        
        self.backup_interval = interval_hours * 3600
        self.is_running = True
        self.backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
        self.backup_thread.start()
        logger.info(f"Backup automático iniciado (intervalo: {interval_hours}h)")

    def stop_auto_backup(self):
        """Detener backup automático"""
        self.is_running = False
        if self.backup_thread:
            self.backup_thread.join(timeout=5)
        logger.info("Backup automático detenido")

    def _backup_loop(self):
        """Bucle principal de backup automático"""
        while self.is_running:
            try:
                # Ejecutar backup
                self.create_backup()
                
                # Limpiar backups antiguos
                if self.cleanup_old_backups:
                    self.cleanup_old_backups()
                
                # Esperar hasta el próximo backup
                time.sleep(self.backup_interval)
                
            except Exception as e:
                logger.error(f"Error en bucle de backup: {e}")
                time.sleep(300)  # Esperar 5 minutos antes de reintentar

    def create_backup(self, backup_name: str = None) -> Optional[str]:
        """Crear backup manual"""
        try:
            if not self.backup_items:
                logger.warning("No hay elementos configurados para backup")
                return None
            
            # Generar nombre de backup
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}"
            
            backup_path = self.backup_dir / backup_name
            
            # Crear directorio de backup
            backup_path.mkdir(exist_ok=True)
            
            backup_info = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "items": [],
                "total_size_mb": 0
            }
            
            total_size = 0
            successful_items = 0
            
            # Backup de cada elemento
            for source_path, item in self.backup_items.items():
                if not item.enabled:
                    continue
                
                try:
                    item_backup_path = backup_path / Path(source_path).name
                    
                    if item.backup_type == "file":
                        success, size = self._backup_file(source_path, item_backup_path)
                    elif item.backup_type == "directory":
                        success, size = self._backup_directory(source_path, item_backup_path)
                    else:
                        success, size = self._backup_file(source_path, item_backup_path)
                    
                    if success:
                        # Actualizar información del elemento
                        item.last_backup = datetime.now()
                        item.backup_size = size
                        item.checksum = self._calculate_checksum(item_backup_path)
                        
                        # Agregar a información del backup
                        backup_info["items"].append({
                            "source_path": source_path,
                            "backup_path": str(item_backup_path),
                            "size_mb": size,
                            "checksum": item.checksum,
                            "backup_type": item.backup_type
                        })
                        
                        total_size += size
                        successful_items += 1
                        
                        logger.info(f"Backup exitoso: {source_path} -> {item_backup_path}")
                    
                except Exception as e:
                    logger.error(f"Error en backup de {source_path}: {e}")
            
            # Comprimir backup si está habilitado
            if self.compress_backups and successful_items > 0:
                compressed_path = self._compress_backup(backup_path, backup_name)
                if compressed_path:
                    # Eliminar directorio sin comprimir
                    shutil.rmtree(backup_path)
                    backup_path = compressed_path
            
            # Guardar información del backup
            backup_info["total_size_mb"] = total_size
            backup_info["successful_items"] = successful_items
            backup_info["compressed"] = self.compress_backups
            
            info_file = backup_path.with_suffix('.json')
            with open(info_file, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            # Actualizar estadísticas
            self.stats["total_backups"] += 1
            self.stats["successful_backups"] += 1
            self.stats["last_backup_time"] = datetime.now().isoformat()
            self.stats["total_backup_size_mb"] += total_size
            
            # Notificar callbacks
            for callback in self.callbacks:
                try:
                    callback(backup_name, backup_info)
                except Exception as e:
                    logger.error(f"Error en callback de backup: {e}")
            
            logger.info(f"Backup completado: {backup_name} ({successful_items} elementos, {total_size:.2f}MB)")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            self.stats["failed_backups"] += 1
            return None

    def _backup_file(self, source_path: str, dest_path: Path) -> tuple[bool, float]:
        """Backup de archivo individual"""
        try:
            shutil.copy2(source_path, dest_path)
            size_mb = dest_path.stat().st_size / (1024 * 1024)
            return True, size_mb
        except Exception as e:
            logger.error(f"Error en backup de archivo {source_path}: {e}")
            return False, 0

    def _backup_directory(self, source_path: str, dest_path: Path) -> tuple[bool, float]:
        """Backup de directorio"""
        try:
            shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            size_mb = sum(f.stat().st_size for f in dest_path.rglob('*') if f.is_file()) / (1024 * 1024)
            return True, size_mb
        except Exception as e:
            logger.error(f"Error en backup de directorio {source_path}: {e}")
            return False, 0

    def _compress_backup(self, backup_path: Path, backup_name: str) -> Optional[Path]:
        """Comprimir backup en archivo ZIP"""
        try:
            zip_path = backup_path.with_suffix('.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in backup_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(backup_path)
                        zipf.write(file_path, arcname)
            
            return zip_path
            
        except Exception as e:
            logger.error(f"Error comprimiendo backup: {e}")
            return None

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcular checksum de archivo"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculando checksum: {e}")
            return ""

    def cleanup_old_backups(self, retention_days: int = None):
        """Limpiar backups antiguos"""
        if retention_days is None:
            retention_days = self.backup_retention_days
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        try:
            for backup_item in self.backup_dir.iterdir():
                if backup_item.is_dir() or backup_item.suffix in ['.zip', '.tar.gz']:
                    # Intentar obtener fecha del nombre del archivo
                    try:
                        if backup_item.name.startswith('backup_'):
                            date_str = backup_item.name.split('_')[1:3]  # YYYYMMDD_HHMMSS
                            if len(date_str) == 2:
                                backup_date = datetime.strptime(f"{date_str[0]}_{date_str[1]}", "%Y%m%d_%H%M%S")
                                if backup_date < cutoff_date:
                                    if backup_item.is_dir():
                                        shutil.rmtree(backup_item)
                                    else:
                                        backup_item.unlink()
                                    deleted_count += 1
                                    logger.info(f"Backup antiguo eliminado: {backup_item.name}")
                    except Exception as e:
                        logger.warning(f"No se pudo procesar fecha de backup {backup_item.name}: {e}")
            
            logger.info(f"Limpieza completada: {deleted_count} backups eliminados")
            
        except Exception as e:
            logger.error(f"Error en limpieza de backups: {e}")

    def restore_backup(self, backup_name: str, restore_path: str = None) -> bool:
        """Restaurar backup"""
        try:
            backup_path = self.backup_dir / backup_name
            
            # Buscar archivo comprimido
            if not backup_path.exists():
                zip_path = backup_path.with_suffix('.zip')
                if zip_path.exists():
                    backup_path = zip_path
                else:
                    logger.error(f"Backup no encontrado: {backup_name}")
                    return False
            
            # Crear directorio de restauración
            if restore_path is None:
                restore_path = f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            restore_dir = Path(restore_path)
            restore_dir.mkdir(exist_ok=True)
            
            # Extraer backup
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(restore_dir)
            else:
                shutil.copytree(backup_path, restore_dir, dirs_exist_ok=True)
            
            logger.info(f"Backup restaurado: {backup_name} -> {restore_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            return False

    def list_backups(self) -> List[Dict]:
        """Listar backups disponibles"""
        backups = []
        
        try:
            for backup_item in self.backup_dir.iterdir():
                if backup_item.is_dir() or backup_item.suffix in ['.zip', '.tar.gz']:
                    backup_info = {
                        "name": backup_item.name,
                        "path": str(backup_item),
                        "size_mb": backup_item.stat().st_size / (1024 * 1024),
                        "modified": datetime.fromtimestamp(backup_item.stat().st_mtime).isoformat(),
                        "type": "directory" if backup_item.is_dir() else "compressed"
                    }
                    
                    # Intentar cargar información adicional
                    info_file = backup_item.with_suffix('.json')
                    if info_file.exists():
                        try:
                            with open(info_file, 'r') as f:
                                additional_info = json.load(f)
                                backup_info.update(additional_info)
                        except Exception:
                            pass
                    
                    backups.append(backup_info)
            
            # Ordenar por fecha de modificación (más reciente primero)
            backups.sort(key=lambda x: x["modified"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listando backups: {e}")
        
        return backups

    def get_backup_stats(self) -> Dict:
        """Obtener estadísticas de backup"""
        return {
            "stats": self.stats.copy(),
            "backup_items": len(self.backup_items),
            "enabled_items": sum(1 for item in self.backup_items.values() if item.enabled),
            "auto_backup_running": self.is_running,
            "backup_interval_hours": self.backup_interval / 3600,
            "backup_directory": str(self.backup_dir),
            "max_backups": self.max_backups,
            "compression_enabled": self.compress_backups,
            "verification_enabled": self.verify_backups,
            "cleanup_enabled": self.cleanup_old_backups,
            "retention_days": self.backup_retention_days
        }

    def add_callback(self, callback: Callable):
        """Agregar callback para notificaciones de backup"""
        self.callbacks.append(callback)

    def remove_callback(self, callback: Callable):
        """Remover callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

# Instancia global del sistema de backup
auto_backup = AutoBackup()

# Funciones de utilidad
def start_auto_backup(interval_hours: int = 1):
    """Iniciar backup automático"""
    auto_backup.start_auto_backup(interval_hours)

def stop_auto_backup():
    """Detener backup automático"""
    auto_backup.stop_auto_backup()

def create_backup(backup_name: str = None) -> Optional[str]:
    """Crear backup manual"""
    return auto_backup.create_backup(backup_name)

def list_backups() -> List[Dict]:
    """Listar backups disponibles"""
    return auto_backup.list_backups()

def restore_backup(backup_name: str, restore_path: str = None) -> bool:
    """Restaurar backup"""
    return auto_backup.restore_backup(backup_name, restore_path)

def get_backup_stats() -> Dict:
    """Obtener estadísticas de backup"""
    return auto_backup.get_backup_stats()

def add_backup_item(source_path: str, backup_type: str = "file") -> bool:
    """Agregar elemento para backup"""
    return auto_backup.add_backup_item(source_path, backup_type)

def cleanup_old_backups(retention_days: int = 30):
    """Limpiar backups antiguos"""
    auto_backup.cleanup_old_backups(retention_days) 