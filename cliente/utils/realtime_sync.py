"""
Sistema de Sincronización en Tiempo Real
Sistema de Gestión de Gimnasio v6 - Fase 5.1

Implementa sincronización en tiempo real usando WebSockets:
- WebSockets para actualizaciones instantáneas
- Conflict resolution avanzado
- Sincronización selectiva
- Compresión de datos en tiempo real
- Monitoreo de estado de conexión
"""

import asyncio
import websockets
import json
import logging
import threading
import time
import zlib
import hashlib
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import queue

from utils.performance_monitor import get_performance_monitor, monitor_ui_function

logger = logging.getLogger(__name__)

class SyncStatus(Enum):
    """Estados de sincronización"""
    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    SYNCING = "syncing"
    CONFLICT = "conflict"
    ERROR = "error"

class ConflictResolution(Enum):
    """Estrategias de resolución de conflictos"""
    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    MERGE = "merge"
    MANUAL = "manual"
    TIMESTAMP = "timestamp"

@dataclass
class SyncOperation:
    """Operación de sincronización"""
    id: str
    table: str
    operation: str  # CREATE, UPDATE, DELETE
    data: Dict[str, Any]
    timestamp: datetime
    user_id: str
    device_id: str
    version: int
    checksum: str
    compressed: bool = False

@dataclass
class ConflictData:
    """Datos de conflicto"""
    operation_id: str
    local_data: Dict[str, Any]
    remote_data: Dict[str, Any]
    conflict_type: str
    resolution: Optional[ConflictResolution] = None
    resolved_at: Optional[datetime] = None

class ConflictResolver:
    """Resolvedor de conflictos avanzado"""
    
    def __init__(self):
        self.resolution_strategies = {
            "usuarios": ConflictResolution.TIMESTAMP,
            "clases": ConflictResolution.SERVER_WINS,
            "asistencias": ConflictResolution.MERGE,
            "pagos": ConflictResolution.SERVER_WINS,
            "empleados": ConflictResolution.TIMESTAMP,
            "default": ConflictResolution.MANUAL
        }
        
        self.conflict_history = deque(maxlen=1000)
        self.auto_resolve_enabled = True
        
    def detect_conflict(self, local_op: SyncOperation, remote_op: SyncOperation) -> Optional[ConflictData]:
        """Detectar conflicto entre operaciones"""
        try:
            if local_op.table != remote_op.table:
                return None
                
            # Verificar si es el mismo registro
            if local_op.data.get('id') != remote_op.data.get('id'):
                return None
                
            # Verificar si hay conflicto real
            if local_op.operation == remote_op.operation:
                # Misma operación, verificar si los datos son diferentes
                if self._data_different(local_op.data, remote_op.data):
                    return ConflictData(
                        operation_id=f"{local_op.id}_{remote_op.id}",
                        local_data=local_op.data,
                        remote_data=remote_op.data,
                        conflict_type="data_conflict"
                    )
            else:
                # Operaciones diferentes, potencial conflicto
                return ConflictData(
                    operation_id=f"{local_op.id}_{remote_op.id}",
                    local_data=local_op.data,
                    remote_data=remote_op.data,
                    conflict_type="operation_conflict"
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error detectando conflicto: {e}")
            return None
            
    def _data_different(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> bool:
        """Verificar si dos conjuntos de datos son diferentes"""
        try:
            # Ignorar campos de metadatos
            ignore_fields = {'updated_at', 'version', 'checksum', 'device_id'}
            
            clean_data1 = {k: v for k, v in data1.items() if k not in ignore_fields}
            clean_data2 = {k: v for k, v in data2.items() if k not in ignore_fields}
            
            return clean_data1 != clean_data2
            
        except Exception as e:
            logger.error(f"Error comparando datos: {e}")
            return True
            
    def resolve_conflict(self, conflict: ConflictData, table: str) -> Dict[str, Any]:
        """Resolver conflicto usando estrategia apropiada"""
        try:
            strategy = self.resolution_strategies.get(table, self.resolution_strategies["default"])
            
            if strategy == ConflictResolution.SERVER_WINS:
                return self._server_wins_resolution(conflict)
            elif strategy == ConflictResolution.CLIENT_WINS:
                return self._client_wins_resolution(conflict)
            elif strategy == ConflictResolution.MERGE:
                return self._merge_resolution(conflict)
            elif strategy == ConflictResolution.TIMESTAMP:
                return self._timestamp_resolution(conflict)
            else:
                return self._manual_resolution(conflict)
                
        except Exception as e:
            logger.error(f"Error resolviendo conflicto: {e}")
            return conflict.remote_data
            
    def _server_wins_resolution(self, conflict: ConflictData) -> Dict[str, Any]:
        """Resolución: servidor gana"""
        conflict.resolution = ConflictResolution.SERVER_WINS
        conflict.resolved_at = datetime.now()
        return conflict.remote_data
        
    def _client_wins_resolution(self, conflict: ConflictData) -> Dict[str, Any]:
        """Resolución: cliente gana"""
        conflict.resolution = ConflictResolution.CLIENT_WINS
        conflict.resolved_at = datetime.now()
        return conflict.local_data
        
    def _merge_resolution(self, conflict: ConflictData) -> Dict[str, Any]:
        """Resolución: merge de datos"""
        try:
            merged_data = conflict.local_data.copy()
            
            # Merge de campos específicos
            for key, remote_value in conflict.remote_data.items():
                if key not in merged_data:
                    merged_data[key] = remote_value
                elif isinstance(remote_value, (int, float)) and isinstance(merged_data[key], (int, float)):
                    # Para campos numéricos, usar el máximo
                    merged_data[key] = max(merged_data[key], remote_value)
                elif isinstance(remote_value, str) and isinstance(merged_data[key], str):
                    # Para strings, usar el más largo (asumiendo más información)
                    merged_data[key] = remote_value if len(remote_value) > len(merged_data[key]) else merged_data[key]
                    
            conflict.resolution = ConflictResolution.MERGE
            conflict.resolved_at = datetime.now()
            return merged_data
            
        except Exception as e:
            logger.error(f"Error en merge resolution: {e}")
            return conflict.remote_data
            
    def _timestamp_resolution(self, conflict: ConflictData) -> Dict[str, Any]:
        """Resolución basada en timestamp"""
        try:
            local_timestamp = conflict.local_data.get('updated_at')
            remote_timestamp = conflict.remote_data.get('updated_at')
            
            if local_timestamp and remote_timestamp:
                # Comparar timestamps
                if isinstance(local_timestamp, str):
                    local_timestamp = datetime.fromisoformat(local_timestamp.replace('Z', '+00:00'))
                if isinstance(remote_timestamp, str):
                    remote_timestamp = datetime.fromisoformat(remote_timestamp.replace('Z', '+00:00'))
                    
                if local_timestamp > remote_timestamp:
                    conflict.resolution = ConflictResolution.CLIENT_WINS
                    conflict.resolved_at = datetime.now()
                    return conflict.local_data
                else:
                    conflict.resolution = ConflictResolution.SERVER_WINS
                    conflict.resolved_at = datetime.now()
                    return conflict.remote_data
            else:
                # Fallback a servidor gana
                return self._server_wins_resolution(conflict)
                
        except Exception as e:
            logger.error(f"Error en timestamp resolution: {e}")
            return conflict.remote_data
            
    def _manual_resolution(self, conflict: ConflictData) -> Dict[str, Any]:
        """Resolución manual (requiere intervención del usuario)"""
        conflict.resolution = ConflictResolution.MANUAL
        conflict.resolved_at = datetime.now()
        # Por ahora, usar servidor como fallback
        return conflict.remote_data
        
    def add_conflict_to_history(self, conflict: ConflictData):
        """Agregar conflicto al historial"""
        self.conflict_history.append(conflict)
        
    def get_conflict_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de conflictos"""
        try:
            resolution_counts = defaultdict(int)
            table_counts = defaultdict(int)
            
            for conflict in self.conflict_history:
                if conflict.resolution:
                    resolution_counts[conflict.resolution.value] += 1
                table_counts[conflict.conflict_type] += 1
                
            return {
                "total_conflicts": len(self.conflict_history),
                "resolution_distribution": dict(resolution_counts),
                "conflict_types": dict(table_counts),
                "auto_resolve_enabled": self.auto_resolve_enabled
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de conflictos: {e}")
            return {}

class DataCompressor:
    """Compresor de datos en tiempo real"""
    
    def __init__(self):
        self.compression_level = 6
        self.min_size_for_compression = 1024  # 1KB
        self.compression_stats = {
            "compressed_messages": 0,
            "uncompressed_messages": 0,
            "total_compression_ratio": 0.0
        }
        
    def compress_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprimir datos si es beneficioso"""
        try:
            data_str = json.dumps(data, default=str)
            
            if len(data_str) < self.min_size_for_compression:
                self.compression_stats["uncompressed_messages"] += 1
                return {
                    "compressed": False,
                    "data": data,
                    "checksum": self._calculate_checksum(data_str)
                }
                
            # Comprimir datos
            compressed_data = zlib.compress(data_str.encode('utf-8'), self.compression_level)
            
            # Calcular ratio de compresión
            original_size = len(data_str)
            compressed_size = len(compressed_data)
            compression_ratio = compressed_size / original_size
            
            # Solo usar compresión si es beneficioso (ratio < 0.9)
            if compression_ratio < 0.9:
                self.compression_stats["compressed_messages"] += 1
                self.compression_stats["total_compression_ratio"] += compression_ratio
                
                return {
                    "compressed": True,
                    "data": compressed_data.hex(),
                    "checksum": self._calculate_checksum(data_str),
                    "original_size": original_size,
                    "compressed_size": compressed_size
                }
            else:
                self.compression_stats["uncompressed_messages"] += 1
                return {
                    "compressed": False,
                    "data": data,
                    "checksum": self._calculate_checksum(data_str)
                }
                
        except Exception as e:
            logger.error(f"Error comprimiendo datos: {e}")
            return {"compressed": False, "data": data, "checksum": ""}
            
    def decompress_data(self, compressed_package: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Descomprimir datos"""
        try:
            if not compressed_package.get("compressed", False):
                return compressed_package.get("data")
                
            # Descomprimir datos
            compressed_hex = compressed_package["data"]
            compressed_data = bytes.fromhex(compressed_hex)
            decompressed_data = zlib.decompress(compressed_data)
            
            # Verificar checksum
            expected_checksum = compressed_package.get("checksum", "")
            actual_checksum = self._calculate_checksum(decompressed_data.decode('utf-8'))
            
            if expected_checksum != actual_checksum:
                logger.error("Checksum no coincide en datos descomprimidos")
                return None
                
            return json.loads(decompressed_data)
            
        except Exception as e:
            logger.error(f"Error descomprimiendo datos: {e}")
            return None
            
    def _calculate_checksum(self, data: str) -> str:
        """Calcular checksum de datos"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
        
    def get_compression_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de compresión"""
        try:
            total_messages = (self.compression_stats["compressed_messages"] + 
                            self.compression_stats["uncompressed_messages"])
            
            avg_compression_ratio = 0.0
            if self.compression_stats["compressed_messages"] > 0:
                avg_compression_ratio = (self.compression_stats["total_compression_ratio"] / 
                                       self.compression_stats["compressed_messages"])
                
            return {
                "total_messages": total_messages,
                "compressed_messages": self.compression_stats["compressed_messages"],
                "uncompressed_messages": self.compression_stats["uncompressed_messages"],
                "compression_rate": (self.compression_stats["compressed_messages"] / total_messages * 100) if total_messages > 0 else 0,
                "avg_compression_ratio": avg_compression_ratio
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de compresión: {e}")
            return {}

class RealtimeSyncManager:
    """Gestor principal de sincronización en tiempo real"""
    
    def __init__(self, api_client, config_manager):
        self.api_client = api_client
        self.config = config_manager
        self.performance_monitor = get_performance_monitor()
        
        # Componentes
        self.conflict_resolver = ConflictResolver()
        self.data_compressor = DataCompressor()
        
        # Estado de conexión
        self.status = SyncStatus.DISCONNECTED
        self.websocket = None
        self.connection_thread = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # segundos
        
        # Colas de operaciones
        self.pending_operations = queue.Queue()
        self.sync_queue = queue.Queue()
        
        # Callbacks
        self.status_callbacks: List[Callable] = []
        self.data_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.conflict_callbacks: List[Callable] = []
        
        # Estadísticas
        self.sync_stats = {
            "operations_sent": 0,
            "operations_received": 0,
            "conflicts_resolved": 0,
            "last_sync": None,
            "connection_uptime": 0
        }
        
        # Configuración
        self.websocket_url = self.config.get("websocket_url", "ws://localhost:8000/ws")
        self.sync_enabled = self.config.get("realtime_sync_enabled", True)
        self.selective_sync = self.config.get("selective_sync_enabled", True)
        
        # Tablas para sincronización selectiva
        self.sync_tables = self.config.get("sync_tables", [
            "usuarios", "clases", "asistencias", "pagos", "empleados"
        ])
        
        # Inicializar
        if self.sync_enabled:
            self._start_sync_manager()
            
    def _start_sync_manager(self):
        """Iniciar gestor de sincronización"""
        try:
            self.connection_thread = threading.Thread(target=self._connection_loop, daemon=True)
            self.connection_thread.start()
            
            # Thread para procesar operaciones
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            
            logger.info("Gestor de sincronización en tiempo real iniciado")
            
        except Exception as e:
            logger.error(f"Error iniciando gestor de sincronización: {e}")
            
    def _connection_loop(self):
        """Bucle principal de conexión WebSocket"""
        while self.sync_enabled:
            try:
                if self.status == SyncStatus.DISCONNECTED:
                    self._connect_websocket()
                    
                if self.websocket:
                    self._handle_websocket_messages()
                    
            except Exception as e:
                logger.error(f"Error en bucle de conexión: {e}")
                self._handle_connection_error()
                
            time.sleep(1)
            
    def _connect_websocket(self):
        """Conectar WebSocket"""
        try:
            self._update_status(SyncStatus.CONNECTING)
            
            # Crear conexión WebSocket
            import websocket
            
            # Configurar headers de autenticación
            headers = {
                "Authorization": f"Bearer {self.api_client.get_token()}",
                "User-Agent": "GymSystem-Client/6.0"
            }
            
            # Crear conexión WebSocket
            self.websocket = websocket.WebSocketApp(
                self.websocket_url,
                header=headers,
                on_open=self._on_websocket_open,
                on_message=self._on_websocket_message,
                on_error=self._on_websocket_error,
                on_close=self._on_websocket_close
            )
            
            # Ejecutar en thread separado
            self.websocket.run_forever()
            
        except Exception as e:
            logger.error(f"Error conectando WebSocket: {e}")
            self._handle_connection_error()
            
    def _on_websocket_open(self, ws):
        """Callback cuando WebSocket se abre"""
        try:
            self._update_status(SyncStatus.CONNECTED)
            self.reconnect_attempts = 0
            self.sync_stats["connection_uptime"] = time.time()
            
            # Enviar mensaje de autenticación
            auth_message = {
                "type": "auth",
                "user_id": self.api_client.get_user_id(),
                "device_id": self.config.get("device_id", "unknown"),
                "capabilities": {
                    "compression": True,
                    "selective_sync": self.selective_sync,
                    "tables": self.sync_tables
                }
            }
            
            self._send_message(auth_message)
            logger.info("WebSocket conectado y autenticado")
            
        except Exception as e:
            logger.error(f"Error en apertura de WebSocket: {e}")
            
    def _on_websocket_message(self, ws, message):
        """Callback cuando se recibe mensaje WebSocket"""
        try:
            # Descomprimir mensaje si es necesario
            data = json.loads(message)
            
            if data.get("compressed", False):
                decompressed_data = self.data_compressor.decompress_data(data)
                if decompressed_data:
                    data = decompressed_data
                else:
                    logger.error("Error descomprimiendo mensaje")
                    return
                    
            # Procesar mensaje
            self._process_incoming_message(data)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje WebSocket: {e}")
            
    def _on_websocket_error(self, ws, error):
        """Callback cuando hay error en WebSocket"""
        logger.error(f"Error en WebSocket: {error}")
        self._handle_connection_error()
        
    def _on_websocket_close(self, ws, close_status_code, close_msg):
        """Callback cuando WebSocket se cierra"""
        logger.info(f"WebSocket cerrado: {close_status_code} - {close_msg}")
        self._update_status(SyncStatus.DISCONNECTED)
        
    def _handle_websocket_messages(self):
        """Manejar mensajes WebSocket"""
        try:
            if self.websocket:
                # El WebSocket maneja los mensajes automáticamente
                pass
        except Exception as e:
            logger.error(f"Error manejando mensajes WebSocket: {e}")
            
    def _handle_connection_error(self):
        """Manejar errores de conexión"""
        try:
            self._update_status(SyncStatus.ERROR)
            
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                self._update_status(SyncStatus.RECONNECTING)
                
                # Esperar antes de reconectar
                time.sleep(self.reconnect_delay * self.reconnect_attempts)
                
                # Intentar reconectar
                self._connect_websocket()
            else:
                logger.error("Máximo número de intentos de reconexión alcanzado")
                self._update_status(SyncStatus.DISCONNECTED)
                
        except Exception as e:
            logger.error(f"Error manejando error de conexión: {e}")
            
    def _send_message(self, message: Dict[str, Any]):
        """Enviar mensaje por WebSocket"""
        try:
            if self.websocket and self.status == SyncStatus.CONNECTED:
                # Comprimir mensaje si es beneficioso
                compressed_message = self.data_compressor.compress_data(message)
                
                # Enviar mensaje
                self.websocket.send(json.dumps(compressed_message))
                
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            
    def _process_incoming_message(self, message: Dict[str, Any]):
        """Procesar mensaje entrante"""
        try:
            message_type = message.get("type")
            
            if message_type == "sync_operation":
                self._handle_sync_operation(message)
            elif message_type == "conflict":
                self._handle_conflict_message(message)
            elif message_type == "status":
                self._handle_status_message(message)
            elif message_type == "ping":
                self._handle_ping_message(message)
            else:
                logger.warning(f"Tipo de mensaje desconocido: {message_type}")
                
        except Exception as e:
            logger.error(f"Error procesando mensaje entrante: {e}")
            
    def _handle_sync_operation(self, message: Dict[str, Any]):
        """Manejar operación de sincronización"""
        try:
            operation_data = message.get("operation", {})
            
            # Crear objeto de operación
            operation = SyncOperation(
                id=operation_data.get("id"),
                table=operation_data.get("table"),
                operation=operation_data.get("operation"),
                data=operation_data.get("data", {}),
                timestamp=datetime.fromisoformat(operation_data.get("timestamp")),
                user_id=operation_data.get("user_id"),
                device_id=operation_data.get("device_id"),
                version=operation_data.get("version", 1),
                checksum=operation_data.get("checksum", "")
            )
            
            # Verificar si es para sincronización selectiva
            if self.selective_sync and operation.table not in self.sync_tables:
                return
                
            # Procesar operación
            self._process_sync_operation(operation)
            
            # Actualizar estadísticas
            self.sync_stats["operations_received"] += 1
            
        except Exception as e:
            logger.error(f"Error manejando operación de sincronización: {e}")
            
    def _process_sync_operation(self, operation: SyncOperation):
        """Procesar operación de sincronización"""
        try:
            # Verificar si hay conflicto
            local_operation = self._get_local_operation(operation)
            
            if local_operation:
                conflict = self.conflict_resolver.detect_conflict(local_operation, operation)
                
                if conflict:
                    # Resolver conflicto automáticamente
                    resolved_data = self.conflict_resolver.resolve_conflict(conflict, operation.table)
                    
                    # Aplicar datos resueltos
                    self._apply_sync_operation(operation.table, resolved_data)
                    
                    # Notificar conflicto resuelto
                    self._notify_conflict_resolved(conflict)
                    
                    self.sync_stats["conflicts_resolved"] += 1
                else:
                    # No hay conflicto, aplicar directamente
                    self._apply_sync_operation(operation.table, operation.data)
            else:
                # No hay operación local, aplicar directamente
                self._apply_sync_operation(operation.table, operation.data)
                
        except Exception as e:
            logger.error(f"Error procesando operación de sincronización: {e}")
            
    def _get_local_operation(self, remote_operation: SyncOperation) -> Optional[SyncOperation]:
        """Obtener operación local correspondiente"""
        # Implementación básica - buscar en cache local
        # En una implementación real, esto buscaría en la base de datos local
        return None
        
    def _apply_sync_operation(self, table: str, data: Dict[str, Any]):
        """Aplicar operación de sincronización"""
        try:
            # Notificar callbacks de datos
            for callback in self.data_callbacks[table]:
                try:
                    callback(table, data)
                except Exception as e:
                    logger.error(f"Error en callback de datos: {e}")
                    
            # Notificar callbacks generales
            for callback in self.data_callbacks["*"]:
                try:
                    callback(table, data)
                except Exception as e:
                    logger.error(f"Error en callback general: {e}")
                    
        except Exception as e:
            logger.error(f"Error aplicando operación de sincronización: {e}")
            
    def _handle_conflict_message(self, message: Dict[str, Any]):
        """Manejar mensaje de conflicto"""
        try:
            conflict_data = message.get("conflict", {})
            
            # Notificar callbacks de conflicto
            for callback in self.conflict_callbacks:
                try:
                    callback(conflict_data)
                except Exception as e:
                    logger.error(f"Error en callback de conflicto: {e}")
                    
        except Exception as e:
            logger.error(f"Error manejando mensaje de conflicto: {e}")
            
    def _handle_status_message(self, message: Dict[str, Any]):
        """Manejar mensaje de estado"""
        try:
            status_data = message.get("status", {})
            logger.info(f"Estado del servidor: {status_data}")
            
        except Exception as e:
            logger.error(f"Error manejando mensaje de estado: {e}")
            
    def _handle_ping_message(self, message: Dict[str, Any]):
        """Manejar mensaje ping"""
        try:
            # Responder con pong
            pong_message = {
                "type": "pong",
                "timestamp": datetime.now().isoformat(),
                "client_id": self.config.get("device_id", "unknown")
            }
            
            self._send_message(pong_message)
            
        except Exception as e:
            logger.error(f"Error manejando ping: {e}")
            
    def _sync_loop(self):
        """Bucle de sincronización"""
        while self.sync_enabled:
            try:
                # Procesar operaciones pendientes
                while not self.pending_operations.empty():
                    operation = self.pending_operations.get_nowait()
                    self._send_sync_operation(operation)
                    
                time.sleep(0.1)  # 100ms
                
            except Exception as e:
                logger.error(f"Error en bucle de sincronización: {e}")
                time.sleep(1)
                
    def _send_sync_operation(self, operation: SyncOperation):
        """Enviar operación de sincronización"""
        try:
            if self.status == SyncStatus.CONNECTED:
                message = {
                    "type": "sync_operation",
                    "operation": asdict(operation)
                }
                
                self._send_message(message)
                self.sync_stats["operations_sent"] += 1
                
        except Exception as e:
            logger.error(f"Error enviando operación de sincronización: {e}")
            
    def _update_status(self, new_status: SyncStatus):
        """Actualizar estado de conexión"""
        try:
            old_status = self.status
            self.status = new_status
            
            # Notificar callbacks de estado
            for callback in self.status_callbacks:
                try:
                    callback(new_status, old_status)
                except Exception as e:
                    logger.error(f"Error en callback de estado: {e}")
                    
            logger.info(f"Estado de sincronización: {old_status.value} -> {new_status.value}")
            
        except Exception as e:
            logger.error(f"Error actualizando estado: {e}")
            
    def _notify_conflict_resolved(self, conflict: ConflictData):
        """Notificar conflicto resuelto"""
        try:
            self.conflict_resolver.add_conflict_to_history(conflict)
            
            # Notificar callbacks de conflicto
            for callback in self.conflict_callbacks:
                try:
                    callback(conflict)
                except Exception as e:
                    logger.error(f"Error en callback de conflicto resuelto: {e}")
                    
        except Exception as e:
            logger.error(f"Error notificando conflicto resuelto: {e}")
            
    # API Pública
    
    def add_status_callback(self, callback: Callable[[SyncStatus, SyncStatus], None]):
        """Agregar callback para cambios de estado"""
        self.status_callbacks.append(callback)
        
    def add_data_callback(self, table: str, callback: Callable[[str, Dict[str, Any]], None]):
        """Agregar callback para datos de tabla específica"""
        self.data_callbacks[table].append(callback)
        
    def add_conflict_callback(self, callback: Callable[[ConflictData], None]):
        """Agregar callback para conflictos"""
        self.conflict_callbacks.append(callback)
        
    def send_operation(self, table: str, operation: str, data: Dict[str, Any]):
        """Enviar operación de sincronización"""
        try:
            operation_obj = SyncOperation(
                id=f"{table}_{int(time.time() * 1000)}",
                table=table,
                operation=operation,
                data=data,
                timestamp=datetime.now(),
                user_id=self.api_client.get_user_id(),
                device_id=self.config.get("device_id", "unknown"),
                version=1,
                checksum=self._calculate_data_checksum(data)
            )
            
            self.pending_operations.put(operation_obj)
            
        except Exception as e:
            logger.error(f"Error enviando operación: {e}")
            
    def _calculate_data_checksum(self, data: Dict[str, Any]) -> str:
        """Calcular checksum de datos"""
        try:
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.md5(data_str.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Error calculando checksum: {e}")
            return ""
            
    def get_status(self) -> SyncStatus:
        """Obtener estado actual"""
        return self.status
        
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de sincronización"""
        try:
            uptime = 0
            if self.sync_stats["connection_uptime"] > 0:
                uptime = time.time() - self.sync_stats["connection_uptime"]
                
            return {
                "status": self.status.value,
                "operations_sent": self.sync_stats["operations_sent"],
                "operations_received": self.sync_stats["operations_received"],
                "conflicts_resolved": self.sync_stats["conflicts_resolved"],
                "connection_uptime": uptime,
                "reconnect_attempts": self.reconnect_attempts,
                "compression_stats": self.data_compressor.get_compression_stats(),
                "conflict_stats": self.conflict_resolver.get_conflict_stats()
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
            
    def enable_selective_sync(self, tables: List[str]):
        """Habilitar sincronización selectiva"""
        self.selective_sync = True
        self.sync_tables = tables
        self.config.set("sync_tables", tables)
        
    def disable_selective_sync(self):
        """Deshabilitar sincronización selectiva"""
        self.selective_sync = False
        self.sync_tables = []
        
    def stop(self):
        """Detener sincronización"""
        try:
            self.sync_enabled = False
            
            if self.websocket:
                self.websocket.close()
                
            logger.info("Sincronización en tiempo real detenida")
            
        except Exception as e:
            logger.error(f"Error deteniendo sincronización: {e}")

# Instancia global del gestor de sincronización
_realtime_sync_manager: Optional[RealtimeSyncManager] = None

def get_realtime_sync_manager(api_client=None, config_manager=None) -> Optional[RealtimeSyncManager]:
    """Obtener instancia global del gestor de sincronización en tiempo real"""
    global _realtime_sync_manager
    if _realtime_sync_manager is None and api_client and config_manager:
        _realtime_sync_manager = RealtimeSyncManager(api_client, config_manager)
    return _realtime_sync_manager

def stop_realtime_sync_manager():
    """Detener gestor de sincronización en tiempo real"""
    global _realtime_sync_manager
    if _realtime_sync_manager:
        _realtime_sync_manager.stop()
        _realtime_sync_manager = None 