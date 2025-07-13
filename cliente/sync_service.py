"""
Servicio de sincronización para el cliente de escritorio
Maneja la sincronización bidireccional entre cliente y servidor
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import threading
import queue

import requests
from requests.exceptions import ConnectionError, Timeout
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from PyQt6.QtCore import QThread, pyqtSignal, QMutex
from PyQt6.QtWidgets import QProgressBar, QLabel

from utils.config_manager import ConfigManager
from utils.secure_storage import SecureStorage

class ConnectionManager:
    """Maneja la conectividad y sesión HTTP"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """Configura la sesión HTTP con headers y timeout"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'GymSystem-Desktop/6.0.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        self.session.timeout = 30
        
        # Configurar retry automático
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout))
    )
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Realiza una petición HTTP con reintentos exponenciales"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error en petición {method} {endpoint}: {str(e)}")
            raise
    
    def check_connection(self) -> bool:
        """Verifica la conectividad con el servidor"""
        try:
            self.make_request('GET', '/api/health')
            return True
        except Exception:
            return False

class ChangeDetector:
    """Detecta y compara cambios entre datos locales y del servidor"""
    
    @staticmethod
    def identify_changes(local_data: List[Dict], server_data: List[Dict]) -> List[Dict]:
        """Identifica cambios entre datos locales y del servidor"""
        changes = []
        
        # Crear índices para comparación rápida
        local_index = {item.get('id'): item for item in local_data}
        server_index = {item.get('id'): item for item in server_data}
        
        # Elementos nuevos en local
        for item_id, item in local_index.items():
            if item_id not in server_index:
                changes.append({
                    'action': 'create',
                    'data': item
                })
        
        # Elementos modificados
        for item_id, local_item in local_index.items():
            if item_id in server_index:
                server_item = server_index[item_id]
                if ChangeDetector.has_changes(local_item, server_item):
                    changes.append({
                        'action': 'update',
                        'id': item_id,
                        'data': local_item
                    })
        
        # Elementos eliminados en servidor
        for item_id, server_item in server_index.items():
            if item_id not in local_index:
                changes.append({
                    'action': 'delete',
                    'id': item_id
                })
        
        return changes
    
    @staticmethod
    def has_changes(local_item: Dict, server_item: Dict) -> bool:
        """Compara dos elementos para detectar cambios"""
        # Comparar campos relevantes (excluir campos de auditoría)
        exclude_fields = {'created_at', 'updated_at', 'sync_id'}
        
        for key, value in local_item.items():
            if key not in exclude_fields and key in server_item:
                if value != server_item[key]:
                    return True
        
        return False

class ConflictResolver:
    """Maneja la resolución de conflictos de sincronización"""
    
    def __init__(self, conflict_policy: str = "ask"):
        self.conflict_policy = conflict_policy
    
    def check_conflict(self, entity_type: str, operation: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Verifica si hay conflictos en una operación"""
        # Implementar lógica de detección de conflictos
        # Por ahora retorna None (sin conflictos)
        return None
    
    def resolve_conflicts(self, resolutions: List[Dict[str, Any]]) -> bool:
        """Resuelve conflictos según la política configurada"""
        try:
            for resolution in resolutions:
                entity_type = resolution.get('entity_type')
                operation = resolution.get('operation')
                data = resolution.get('data')
                
                if self.conflict_policy == "server_wins":
                    # Aplicar cambios del servidor
                    pass
                elif self.conflict_policy == "client_wins":
                    # Mantener cambios locales
                    pass
                elif self.conflict_policy == "ask":
                    # Solicitar intervención del usuario
                    pass
            
            return True
        except Exception as e:
            logging.error(f"Error resolviendo conflictos: {e}")
            return False

class SyncQueue:
    """Maneja la cola de cambios pendientes de sincronización"""
    
    def __init__(self):
        self.queue = queue.Queue()
        self._lock = threading.Lock()
    
    def enqueue_change(self, entity_type: str, operation: str, data: Dict[str, Any]):
        """Añade un cambio a la cola"""
        change = {
            "entity_type": entity_type,
            "operation": operation,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "synced": False
        }
        
        self.queue.put(change)
    
    def get_pending_changes(self) -> List[Dict[str, Any]]:
        """Obtiene todos los cambios pendientes"""
        changes = []
        while not self.queue.empty():
            try:
                change = self.queue.get_nowait()
                changes.append(change)
            except queue.Empty:
                break
        return changes
    
    def size(self) -> int:
        """Obtiene el tamaño de la cola"""
        return self.queue.qsize()
    
    def clear(self):
        """Limpia la cola"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

class SyncService(QThread):
    """
    Servicio de sincronización con reintentos exponenciales y feedback de progreso
    """
    progress_updated = pyqtSignal(int, str)  # porcentaje, mensaje
    sync_completed = pyqtSignal(bool, str)   # éxito, mensaje
    data_updated = pyqtSignal(str, list)     # tipo, datos

    def __init__(self, config_manager: ConfigManager, secure_storage: SecureStorage):
        super().__init__()
        self.config_manager = config_manager
        self.secure_storage = secure_storage
        self.mutex = QMutex()
        self.is_running = False
        self.base_url = self.config_manager.get('backend_url', 'http://localhost:8000')
        
        # Componentes especializados
        self.connection_manager = ConnectionManager(self.base_url)
        self.change_detector = ChangeDetector()
        self.conflict_resolver = ConflictResolver(
            self.config_manager.get("conflict_policy", "ask")
        )
        self.sync_queue = SyncQueue()
        
        # Bloqueo para sincronización
        self.sync_lock = threading.Lock()
        
        # Timestamp de última sincronización
        self.last_sync = self.load_last_sync()
        
        # Configurar registro
        self.logger = logging.getLogger("sync_service")
        
        # Estado actual
        self.status = {
            "conectado": True,
            "ultima_sync": self.last_sync,
            "elementos_pendientes": 0,
            "conflictos": 0,
            "sync_en_progreso": False,
            "progreso_sync": 0,
            "modo_offline": False
        }

    def setup_session(self):
        """Configura la sesión HTTP con headers y timeout"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'GymSystem-Desktop/6.0.0'
        })
        self.session.timeout = 30

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout))
    )
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """
        Realiza una petición HTTP con reintentos exponenciales
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error en petición {method} {endpoint}: {str(e)}")
            raise

    def sync_data(self, data_type: str, local_data: List[Dict], endpoint: str) -> bool:
        """
        Sincroniza datos locales con el servidor
        """
        try:
            self.progress_updated.emit(0, f"Sincronizando {data_type}...")
            
            # Obtener datos del servidor
            response = self.make_request('GET', endpoint)
            server_data = response.json()
            
            self.progress_updated.emit(30, f"Comparando {data_type}...")
            
            # Identificar cambios
            changes = self.identify_changes(local_data, server_data)
            
            if not changes:
                self.progress_updated.emit(100, f"{data_type} ya está sincronizado")
                return True
            
            self.progress_updated.emit(50, f"Aplicando cambios en {data_type}...")
            
            # Aplicar cambios
            for change in changes:
                if change['action'] == 'create':
                    self.make_request('POST', endpoint, change['data'])
                elif change['action'] == 'update':
                    self.make_request('PUT', f"{endpoint}/{change['id']}", change['data'])
                elif change['action'] == 'delete':
                    self.make_request('DELETE', f"{endpoint}/{change['id']}")
            
            self.progress_updated.emit(100, f"{data_type} sincronizado exitosamente")
            return True
            
        except Exception as e:
            logging.error(f"Error sincronizando {data_type}: {str(e)}")
            self.progress_updated.emit(0, f"Error en {data_type}: {str(e)}")
            return False

    def identify_changes(self, local_data: List[Dict], server_data: List[Dict]) -> List[Dict]:
        """
        Identifica cambios entre datos locales y del servidor
        """
        changes = []
        
        # Crear índices para comparación rápida
        local_index = {item.get('id'): item for item in local_data}
        server_index = {item.get('id'): item for item in server_data}
        
        # Elementos nuevos en local
        for item_id, item in local_index.items():
            if item_id not in server_index:
                changes.append({
                    'action': 'create',
                    'data': item
                })
        
        # Elementos modificados
        for item_id, local_item in local_index.items():
            if item_id in server_index:
                server_item = server_index[item_id]
                if self.has_changes(local_item, server_item):
                    changes.append({
                        'action': 'update',
                        'id': item_id,
                        'data': local_item
                    })
        
        # Elementos eliminados en servidor
        for item_id, server_item in server_index.items():
            if item_id not in local_index:
                changes.append({
                    'action': 'delete',
                    'id': item_id
                })
        
        return changes

    def has_changes(self, local_item: Dict, server_item: Dict) -> bool:
        """
        Compara dos elementos para detectar cambios
        """
        # Comparar campos relevantes (excluir campos de auditoría)
        exclude_fields = {'created_at', 'updated_at', 'sync_id'}
        
        for key, value in local_item.items():
            if key not in exclude_fields and key in server_item:
                if value != server_item[key]:
                    return True
        
        return False

    def run(self):
        """
        Ejecuta la sincronización completa
        """
        self.mutex.lock()
        self.is_running = True
        self.mutex.unlock()
        
        try:
            self.progress_updated.emit(0, "Iniciando sincronización...")
            
            # Verificar conectividad
            try:
                self.make_request('GET', '/api/health')
            except Exception as e:
                self.sync_completed.emit(False, f"No se puede conectar al servidor: {str(e)}")
                return
            
            self.progress_updated.emit(10, "Conectado al servidor")
            
            # Sincronizar cada tipo de dato
            sync_tasks = [
                ('usuarios', '/api/usuarios'),
                ('empleados', '/api/empleados'),
                ('clases', '/api/clases'),
                ('asistencias', '/api/asistencias'),
                ('pagos', '/api/pagos'),
                ('rutinas', '/api/rutinas'),
                ('tipos_cuota', '/api/tipos-cuota')
            ]
            
            total_tasks = len(sync_tasks)
            completed_tasks = 0
            
            for data_type, endpoint in sync_tasks:
                try:
                    # Obtener datos locales (simulado)
                    local_data = self.get_local_data(data_type)
                    
                    success = self.sync_data(data_type, local_data, endpoint)
                    if success:
                        completed_tasks += 1
                        progress = int((completed_tasks / total_tasks) * 80) + 10
                        self.progress_updated.emit(progress, f"Completado: {data_type}")
                    else:
                        self.sync_completed.emit(False, f"Error sincronizando {data_type}")
                        return
                        
                except Exception as e:
                    logging.error(f"Error en sincronización de {data_type}: {str(e)}")
                    self.sync_completed.emit(False, f"Error en {data_type}: {str(e)}")
                    return
            
            self.progress_updated.emit(100, "Sincronización completada")
            self.sync_completed.emit(True, "Sincronización exitosa")
            
        except Exception as e:
            logging.error(f"Error general en sincronización: {str(e)}")
            self.sync_completed.emit(False, f"Error general: {str(e)}")
        
        finally:
            self.mutex.lock()
            self.is_running = False
            self.mutex.unlock()

    def get_local_data(self, data_type: str) -> List[Dict]:
        """
        Obtiene datos locales desde almacenamiento local
        """
        try:
            # Obtener datos del almacenamiento seguro
            data = self.secure_storage.get_data(f"local_{data_type}")
            if data:
                return data
            else:
                # Si no hay datos, retornar lista vacía
                return []
        except Exception as e:
            self.logger.error(f"Error obteniendo datos locales de {data_type}: {e}")
            return []

    def stop_sync(self):
        """
        Detiene la sincronización
        """
        self.mutex.lock()
        self.is_running = False
        self.mutex.unlock()
        self.wait()

    def is_syncing(self) -> bool:
        """
        Verifica si la sincronización está en curso
        """
        self.mutex.lock()
        running = self.is_running
        self.mutex.unlock()
        return running

    def load_last_sync(self) -> datetime:
        """
        Carga el timestamp de la última sincronización
        
        Returns:
            Timestamp de la última sincronización o datetime actual si no existe
        """
        sync_info_path = os.path.join(os.path.dirname(self.base_url), "sync_info.json")
        
        if os.path.exists(sync_info_path):
            try:
                with open(sync_info_path, 'r') as f:
                    sync_data = json.load(f)
                    return datetime.fromisoformat(sync_data.get("last_sync", datetime.now().isoformat()))
            except (json.JSONDecodeError, ValueError, KeyError):
                pass
        
        return datetime.now()
    
    def save_last_sync(self, timestamp: Optional[datetime] = None):
        """
        Guarda el timestamp de la última sincronización
        
        Args:
            timestamp: Timestamp a guardar (por defecto, ahora)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.last_sync = timestamp
        self.status["ultima_sync"] = timestamp
        
        sync_info_path = os.path.join(os.path.dirname(self.base_url), "sync_info.json")
        
        try:
            sync_data = {"last_sync": timestamp.isoformat()}
            
            with open(sync_info_path, 'w') as f:
                json.dump(sync_data, f)
        
        except Exception as e:
            self.logger.error(f"Error guardando información de sincronización: {str(e)}")
    
    def enqueue_change(self, entity_type: str, operation: str, data: Dict[str, Any]):
        """
        Añade un cambio a la cola de sincronización
        
        Args:
            entity_type: Tipo de entidad (usuarios, clases, etc.)
            operation: Tipo de operación (create, update, delete)
            data: Datos de la operación
        """
        change = {
            "entity_type": entity_type,
            "operation": operation,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "synced": False
        }
        
        self.sync_queue.put(change)
        self.status["elementos_pendientes"] = self.sync_queue.qsize()
        
        # Si sincronización automática está habilitada, intentar sincronizar
        if self.config_manager.get("auto_sync", True) and not self.status["sync_en_progreso"]:
            threading.Thread(target=self.sync, daemon=True).start()
    
    def sync(self, force: bool = False) -> bool:
        """
        Realiza la sincronización con el servidor
        
        Args:
            force: Si es True, fuerza la sincronización aunque no haya cambios pendientes
        
        Returns:
            True si la sincronización fue exitosa, False en caso contrario
        """
        # Evitar sincronizaciones simultáneas
        if not self.sync_lock.acquire(blocking=False):
            return False
        
        try:
            # Marcar como en progreso
            self.status["sync_en_progreso"] = True
            self.status["progreso_sync"] = 0
            
            # Verificar conexión con el servidor
            if not self._check_server_connection():
                self.status["conectado"] = False
                self.status["modo_offline"] = True
                self.status["sync_en_progreso"] = False
                return False
            
            # Restablecer modo online si estaba en offline
            self.status["conectado"] = True
            self.status["modo_offline"] = False
            
            # Etapa 1: Obtener cambios del servidor (pull)
            self.status["progreso_sync"] = 10
            server_changes = self._pull_changes()
            
            # Etapa 2: Procesar cambios del servidor
            self.status["progreso_sync"] = 30
            conflicts = self._process_server_changes(server_changes)
            
            # Etapa 3: Enviar cambios locales al servidor (push)
            self.status["progreso_sync"] = 50
            local_changes = self._get_pending_changes()
            push_results = self._push_changes(local_changes)
            
            # Etapa 4: Actualizar estado local según resultados
            self.status["progreso_sync"] = 80
            self._update_local_status(push_results)
            
            # Etapa 5: Resolver conflictos si es necesario
            self.status["progreso_sync"] = 90
            if conflicts:
                self.status["conflictos"] = len(conflicts)
            else:
                self.status["conflictos"] = 0
            
            # Actualizar timestamp de última sincronización
            self.save_last_sync()
            
            # Actualizar estado
            self.status["elementos_pendientes"] = self.sync_queue.qsize()
            self.status["sync_en_progreso"] = False
            self.status["progreso_sync"] = 100
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error durante la sincronización: {str(e)}")
            self.status["sync_en_progreso"] = False
            return False
        
        finally:
            self.sync_lock.release()
    
    def _check_server_connection(self) -> bool:
        """
        Verifica la conexión con el servidor
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            # Intenta hacer una petición simple al servidor
            response = self.make_request('GET', '/api/health')
            return response.get("status") == "ok"
        
        except (ConnectionError, Timeout):
            return False
        
        except Exception as e:
            self.logger.error(f"Error verificando conexión con el servidor: {str(e)}")
            return False
    
    def _pull_changes(self) -> List[Dict[str, Any]]:
        """
        Obtiene cambios desde el servidor
        
        Returns:
            Lista de cambios del servidor
        """
        try:
            # Convertir timestamp a string para la API
            last_sync_str = self.last_sync.isoformat()
            
            # Llamar a la API para obtener cambios
            response = self.make_request('GET', '/api/changes', {"since": last_sync_str})
            
            # Procesar y devolver cambios
            return response.json().get("changes", [])
        
        except Exception as e:
            self.logger.error(f"Error obteniendo cambios del servidor: {str(e)}")
            return []
    
    def _process_server_changes(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Procesa los cambios recibidos del servidor
        
        Args:
            changes: Lista de cambios del servidor
        
        Returns:
            Lista de conflictos detectados
        """
        conflicts = []
        
        for change in changes:
            try:
                entity_type = change.get("entity_type")
                operation = change.get("operation")
                data = change.get("data", {})
                
                # Verificar si hay conflictos locales
                conflict = self._check_conflict(entity_type, operation, data)
                
                if conflict:
                    # Agregar a lista de conflictos
                    conflicts.append({
                        "server_change": change,
                        "local_change": conflict,
                        "resolved": False
                    })
                else:
                    # Aplicar cambio localmente
                    self._apply_server_change(entity_type, operation, data)
            
            except Exception as e:
                self.logger.error(f"Error procesando cambio del servidor: {str(e)}")
        
        return conflicts
    
    def _check_conflict(self, entity_type: str, operation: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Verifica si hay conflictos con cambios locales
        
        Args:
            entity_type: Tipo de entidad
            operation: Tipo de operación
            data: Datos de la operación
        
        Returns:
            Cambio local en conflicto o None si no hay conflicto
        """
        # Implementación simplificada para demo
        # En una implementación real, verificaría en la base de datos local
        return None
    
    def _apply_server_change(self, entity_type: str, operation: str, data: Dict[str, Any]):
        """
        Aplica un cambio del servidor localmente
        
        Args:
            entity_type: Tipo de entidad
            operation: Tipo de operación
            data: Datos de la operación
        """
        # Implementación simplificada para demo
        # En una implementación real, aplicaría el cambio a la base de datos local
        pass
    
    def _get_pending_changes(self) -> List[Dict[str, Any]]:
        """
        Obtiene los cambios locales pendientes de sincronización
        
        Returns:
            Lista de cambios locales
        """
        changes = []
        
        # Extraer todos los elementos de la cola sin vaciarla
        temp_queue = queue.Queue()
        try:
            while True:
                change = self.sync_queue.get_nowait()
                changes.append(change)
                temp_queue.put(change)
        except queue.Empty:
            pass
        
        # Restaurar la cola
        try:
            while True:
                self.sync_queue.put(temp_queue.get_nowait())
        except queue.Empty:
            pass
        
        return changes
    
    def _push_changes(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Envía cambios locales al servidor
        
        Args:
            changes: Lista de cambios locales
        
        Returns:
            Resultados de la operación
        """
        if not changes:
            return {"success": True, "processed": 0, "failed": 0, "details": []}
        
        try:
            # Llamar a la API para enviar cambios
            response = self.make_request('POST', '/api/changes', {"changes": changes})
            return response.json()
        
        except Exception as e:
            self.logger.error(f"Error enviando cambios al servidor: {str(e)}")
            return {"success": False, "processed": 0, "failed": len(changes), "details": []}
    
    def _update_local_status(self, push_results: Dict[str, Any]):
        """
        Actualiza el estado local según los resultados del push
        
        Args:
            push_results: Resultados de la operación de push
        """
        if push_results.get("success", False):
            # Procesar resultados exitosos
            processed = push_results.get("processed", 0)
            details = push_results.get("details", [])
            
            # Eliminar de la cola los cambios sincronizados exitosamente
            for _ in range(processed):
                try:
                    self.sync_queue.get_nowait()
                except queue.Empty:
                    break
        
        # Actualizar contador de elementos pendientes
        self.status["elementos_pendientes"] = self.sync_queue.qsize()
    
    def resolve_conflicts(self, resolutions: List[Dict[str, Any]]) -> bool:
        """
        Resuelve conflictos según las decisiones proporcionadas
        
        Args:
            resolutions: Lista de resoluciones de conflictos
                Cada resolución debe tener:
                - conflict_id: ID del conflicto
                - resolution: "local", "server" o "manual"
                - manual_data: Datos manuales si resolution="manual"
        
        Returns:
            True si todas las resoluciones fueron exitosas, False en caso contrario
        """
        # Implementación simplificada para demo
        # En una implementación real, aplicaría las resoluciones
        # y actualizaría tanto la base de datos local como el servidor
        
        # Sincronización real con el servidor
        try:
            # Preparar datos para sincronización
            sync_data = {
                "cliente_id": self.config_manager.get("client_id", "desktop_client"),
                "timestamp": datetime.utcnow().isoformat(),
                "items": self.sync_queue.get_pending_items()
            }
            
            # Enviar datos al servidor
            response = self.api_client._make_request('POST', '/sync/push', data=sync_data)
            
            if response and 'data' in response:
                # Procesar respuesta del servidor
                resultados = response['data'].get('resultados', [])
                for resultado in resultados:
                    if resultado.get('estado') == 'SINCRONIZADO':
                        # Marcar como sincronizado
                        self.sync_queue.mark_synced(resultado['id'])
                    elif resultado.get('estado') == 'CONFLICTO':
                        # Agregar a conflictos
                        self.conflict_resolver.add_conflict(resultado)
                
                # Actualizar estado
                self.status["elementos_pendientes"] = self.sync_queue.get_pending_count()
                self.status["conflictos"] = self.conflict_resolver.get_conflict_count()
                self.status["ultima_sync"] = datetime.now()
                
                return True
            else:
                logger.error("Respuesta inválida del servidor en sincronización")
                return False
                
        except Exception as e:
            logger.error(f"Error en sincronización: {e}")
            return False
        self.status["conflictos"] = 0
        return True
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual de la sincronización
        
        Returns:
            Estado actual de sincronización
        """
        return self.status
    
    def toggle_offline_mode(self, enabled: bool) -> bool:
        """
        Activa o desactiva el modo offline
        
        Args:
            enabled: True para activar, False para desactivar
        
        Returns:
            True si la operación fue exitosa, False en caso contrario
        """
        self.status["modo_offline"] = enabled
        return True
