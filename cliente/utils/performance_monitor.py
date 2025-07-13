"""
Monitor de Rendimiento para Cliente Desktop
Sistema de Gestión de Gimnasio v6

Supervisa métricas de rendimiento del cliente desktop incluyendo:
- Uso de memoria y CPU
- Latencia de red y API
- Rendimiento de la interfaz
- Métricas de base de datos local
- Detección de memory leaks
- Optimización de consultas
- Virtualización y lazy loading
"""

import time
import psutil
import threading
import logging
import sys
import gc
import weakref
import tracemalloc
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import deque, defaultdict
import json
import os
import sqlite3
import zlib
import pickle
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class MemoryLeakDetector:
    """Detector de memory leaks avanzado"""
    
    def __init__(self):
        self.object_tracker = weakref.WeakSet()
        self.snapshot_times = []
        self.memory_snapshots = []
        self.leak_threshold = 10  # MB
        self.tracking_enabled = False
        
    def start_tracking(self):
        """Iniciar tracking de objetos"""
        self.tracking_enabled = True
        tracemalloc.start()
        logger.info("Tracking de memory leaks iniciado")
        
    def stop_tracking(self):
        """Detener tracking de objetos"""
        self.tracking_enabled = False
        tracemalloc.stop()
        logger.info("Tracking de memory leaks detenido")
        
    def take_snapshot(self):
        """Tomar snapshot de memoria"""
        if not self.tracking_enabled:
            return
            
        snapshot = tracemalloc.take_snapshot()
        self.memory_snapshots.append(snapshot)
        self.snapshot_times.append(time.time())
        
        # Mantener solo los últimos 10 snapshots
        if len(self.memory_snapshots) > 10:
            self.memory_snapshots.pop(0)
            self.snapshot_times.pop(0)
            
    def detect_leaks(self) -> List[Dict]:
        """Detectar memory leaks"""
        leaks = []
        
        if len(self.memory_snapshots) < 2:
            return leaks
            
        # Comparar snapshots
        old_snapshot = self.memory_snapshots[0]
        new_snapshot = self.memory_snapshots[-1]
        
        stats = new_snapshot.compare_to(old_snapshot, 'lineno')
        
        for stat in stats[:10]:  # Top 10
            if stat.size_diff > self.leak_threshold * 1024 * 1024:  # Convertir a bytes
                leaks.append({
                    'file': stat.traceback.format()[-1],
                    'size_diff_mb': stat.size_diff / (1024 * 1024),
                    'count_diff': stat.count_diff
                })
                
        return leaks

class VirtualizationManager:
    """Gestor de virtualización para listas grandes"""
    
    def __init__(self):
        self.virtualized_widgets = {}
        self.chunk_size = 50
        self.preload_distance = 100
        
    def create_virtual_list(self, total_items: int, item_height: int, 
                           create_item_func: Callable, parent_widget=None):
        """Crear lista virtualizada"""
        from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout
        from PyQt6.QtCore import QTimer
        
        class VirtualListWidget(QWidget):
            def __init__(self):
                super().__init__()
                self.total_items = total_items
                self.item_height = item_height
                self.create_item_func = create_item_func
                self.visible_items = {}
                self.scroll_area = QScrollArea()
                self.content_widget = QWidget()
                self.setup_ui()
                
            def setup_ui(self):
                layout = QVBoxLayout(self)
                self.content_widget.setFixedHeight(self.total_items * self.item_height)
                self.scroll_area.setWidget(self.content_widget)
                self.scroll_area.setWidgetResizable(False)
                layout.addWidget(self.scroll_area)
                
                # Conectar scroll
                scroll_bar = self.scroll_area.verticalScrollBar()
                if scroll_bar:
                    scroll_bar.valueChanged.connect(self.on_scroll)
                
            def on_scroll(self, value):
                self.update_visible_items(value)
                
            def update_visible_items(self, scroll_value):
                # Calcular rango visible
                viewport = self.scroll_area.viewport()
                if not viewport:
                    return
                    
                viewport_height = viewport.height()
                start_index = max(0, scroll_value // self.item_height - 5)
                end_index = min(self.total_items, 
                               (scroll_value + viewport_height) // self.item_height + 5)
                
                # Limpiar items no visibles
                to_remove = []
                for index, widget in self.visible_items.items():
                    if index < start_index or index >= end_index:
                        to_remove.append(index)
                        
                for index in to_remove:
                    widget = self.visible_items.pop(index)
                    widget.deleteLater()
                    
                # Crear items visibles
                for index in range(start_index, end_index):
                    if index not in self.visible_items:
                        widget = self.create_item_func(index)
                        widget.setParent(self.content_widget)
                        widget.move(0, index * self.item_height)
                        widget.show()
                        self.visible_items[index] = widget
                        
        return VirtualListWidget()

class LazyLoadingManager:
    """Gestor de carga diferida"""
    
    def __init__(self):
        self.loaded_components = {}
        self.loading_queue = deque()
        self.max_concurrent_loads = 3
        self.loading_threads = []
        
    def register_component(self, component_id: str, load_func: Callable, 
                          dependencies: Optional[List[str]] = None):
        """Registrar componente para carga diferida"""
        self.loaded_components[component_id] = {
            'load_func': load_func,
            'dependencies': dependencies or [],
            'loaded': False,
            'instance': None,
            'loading': False
        }
        
    def load_component(self, component_id: str) -> Any:
        """Cargar componente de forma diferida"""
        if component_id not in self.loaded_components:
            raise ValueError(f"Componente {component_id} no registrado")
            
        component = self.loaded_components[component_id]
        
        if component['loaded'] and component['instance']:
            return component['instance']
            
        if component['loading']:
            # Esperar a que termine de cargar
            while component['loading']:
                time.sleep(0.1)
            return component['instance']
            
        # Cargar dependencias primero
        for dep in component['dependencies']:
            self.load_component(dep)
            
        # Marcar como cargando
        component['loading'] = True
        
        try:
            # Cargar componente
            component['instance'] = component['load_func']()
            component['loaded'] = True
            logger.info(f"Componente {component_id} cargado exitosamente")
            
        except Exception as e:
            logger.error(f"Error cargando componente {component_id}: {e}")
            component['instance'] = None
            
        finally:
            component['loading'] = False
            
        return component['instance']
        
    def preload_components(self, component_ids: List[str]):
        """Precargar componentes en background"""
        for component_id in component_ids:
            if component_id in self.loaded_components:
                self.loading_queue.append(component_id)
                
        # Iniciar threads de carga si no están corriendo
        if len(self.loading_threads) < self.max_concurrent_loads:
            thread = threading.Thread(target=self._load_queue_worker, daemon=True)
            thread.start()
            self.loading_threads.append(thread)
            
    def _load_queue_worker(self):
        """Worker para cargar componentes en background"""
        while self.loading_queue:
            try:
                component_id = self.loading_queue.popleft()
                self.load_component(component_id)
            except Exception as e:
                logger.error(f"Error en worker de carga: {e}")

class QueryOptimizer:
    """Optimizador de consultas de base de datos"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.query_cache = {}
        self.cache_size = 1000
        self.prepared_statements = {}
        
    def optimize_query(self, query: str, params: Optional[tuple] = None) -> str:
        """Optimizar consulta SQL"""
        # Analizar consulta
        query_lower = query.lower()
        
        # Agregar índices sugeridos
        if 'where' in query_lower and 'id' in query_lower:
            self._suggest_index(query)
            
        # Optimizar JOINs
        if 'join' in query_lower:
            query = self._optimize_joins(query)
            
        # Agregar LIMIT si no existe
        if 'limit' not in query_lower and 'select' in query_lower:
            query += ' LIMIT 1000'
            
        return query
        
    def _suggest_index(self, query: str):
        """Sugerir índices para consulta"""
        # Implementación básica de sugerencias de índices
        pass
        
    def _optimize_joins(self, query: str) -> str:
        """Optimizar JOINs en consulta"""
        # Implementación básica de optimización de JOINs
        return query
        
    def prepare_statement(self, query: str, name: str):
        """Preparar statement para reutilización"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # SQLite no tiene prepare() como método directo, usar execute con parámetros
            self.prepared_statements[name] = (query, cursor)
            conn.close()
        except Exception as e:
            logger.error(f"Error preparando statement {name}: {e}")
            
    def execute_prepared(self, name: str, params: Optional[tuple] = None):
        """Ejecutar statement preparado"""
        if name in self.prepared_statements:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                query, _ = self.prepared_statements[name]
                result = cursor.execute(query, params or ())
                conn.close()
                return result
            except Exception as e:
                logger.error(f"Error ejecutando statement preparado {name}: {e}")
        return None

class DataCompressor:
    """Compresor de datos en memoria"""
    
    def __init__(self):
        self.compression_level = 6
        self.compressed_cache = {}
        
    def compress_data(self, data: Any) -> bytes:
        """Comprimir datos"""
        try:
            # Serializar datos
            serialized = pickle.dumps(data)
            
            # Comprimir
            compressed = zlib.compress(serialized, self.compression_level)
            
            return compressed
        except Exception as e:
            logger.error(f"Error comprimiendo datos: {e}")
            return pickle.dumps(data)
            
    def decompress_data(self, compressed_data: bytes) -> Any:
        """Descomprimir datos"""
        try:
            # Intentar descomprimir
            try:
                decompressed = zlib.decompress(compressed_data)
                return pickle.loads(decompressed)
            except zlib.error:
                # Si falla, intentar como datos sin comprimir
                return pickle.loads(compressed_data)
                
        except Exception as e:
            logger.error(f"Error descomprimiendo datos: {e}")
            return None
            
    def cache_compressed(self, key: str, data: Any):
        """Cachear datos comprimidos"""
        compressed = self.compress_data(data)
        self.compressed_cache[key] = compressed
        
        # Limpiar cache si es muy grande
        if len(self.compressed_cache) > 1000:
            # Eliminar elementos más antiguos
            keys_to_remove = list(self.compressed_cache.keys())[:100]
            for k in keys_to_remove:
                del self.compressed_cache[k]
                
    def get_cached(self, key: str) -> Any:
        """Obtener datos del cache comprimido"""
        if key in self.compressed_cache:
            return self.decompress_data(self.compressed_cache[key])
        return None

class PerformanceMetrics:
    """Métricas de rendimiento del sistema"""
    
    def __init__(self):
        self.cpu_percent = 0.0
        self.memory_percent = 0.0
        self.memory_used_mb = 0.0
        self.memory_available_mb = 0.0
        self.disk_usage_percent = 0.0
        self.network_sent_mb = 0.0
        self.network_recv_mb = 0.0
        self.timestamp = datetime.now()
        
        # Nuevas métricas de optimización
        self.memory_leaks_detected = 0
        self.cache_hit_rate = 0.0
        self.query_execution_time = 0.0
        self.compression_ratio = 0.0
        self.lazy_loaded_components = 0

class PerformanceMonitor(QObject):
    """Monitor de rendimiento avanzado para el cliente desktop"""
    
    # Señal para advertencias de rendimiento
    performance_warning = pyqtSignal(str, dict)
    
    def __init__(self, max_history: int = 1000):
        super().__init__()
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_interval = 5.0  # segundos
        self.callbacks: List[Callable] = []
        
        # Nuevos componentes de optimización
        self.memory_leak_detector = MemoryLeakDetector()
        self.virtualization_manager = VirtualizationManager()
        self.lazy_loading_manager = LazyLoadingManager()
        self.query_optimizer = None  # Se inicializa cuando se conoce la DB
        self.data_compressor = DataCompressor()
        
        # Estadísticas
        self.stats = {
            "start_time": None,
            "total_samples": 0,
            "peak_cpu": 0.0,
            "peak_memory": 0.0,
            "avg_cpu": 0.0,
            "avg_memory": 0.0,
            "alerts": [],
            "memory_leaks": [],
            "optimization_stats": {
                "cache_hits": 0,
                "cache_misses": 0,
                "compressed_data_mb": 0,
                "lazy_loaded_components": 0,
                "virtualized_lists": 0
            }
        }
        
        # Umbrales de alerta
        self.thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0
        }
        
        # Configuración de logging
        self.log_performance = True
        self.log_interval = 60  # segundos
        self.last_log_time = time.time()

    def start_monitoring(self):
        """Iniciar monitoreo de rendimiento"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.stats["start_time"] = datetime.now()
            
            # Iniciar detección de memory leaks
            self.memory_leak_detector.start_tracking()
            
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Monitor de rendimiento avanzado iniciado")

    def stop_monitoring(self):
        """Detener monitoreo de rendimiento"""
        self.is_monitoring = False
        
        # Detener detección de memory leaks
        self.memory_leak_detector.stop_tracking()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Monitor de rendimiento detenido")

    def add_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """Agregar callback para notificaciones de métricas"""
        self.callbacks.append(callback)

    def remove_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """Remover callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def _monitor_loop(self):
        """Bucle principal de monitoreo"""
        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                self._process_metrics(metrics)
                self._check_thresholds(metrics)
                self._log_performance(metrics)
                
                # Detectar memory leaks cada 5 minutos
                if self.stats["total_samples"] % 60 == 0:
                    self._detect_memory_leaks()
                
                # Notificar callbacks
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logger.error(f"Error en callback de rendimiento: {e}")
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Error en monitoreo de rendimiento: {e}")
                time.sleep(self.monitor_interval)

    def _collect_metrics(self) -> PerformanceMetrics:
        """Recolectar métricas del sistema"""
        metrics = PerformanceMetrics()
        
        try:
            # CPU
            metrics.cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memoria
            memory = psutil.virtual_memory()
            metrics.memory_percent = memory.percent
            metrics.memory_used_mb = memory.used / (1024 * 1024)
            metrics.memory_available_mb = memory.available / (1024 * 1024)
            
            # Disco
            disk = psutil.disk_usage('/')
            metrics.disk_usage_percent = disk.percent
            
            # Red
            network = psutil.net_io_counters()
            metrics.network_sent_mb = network.bytes_sent / (1024 * 1024)
            metrics.network_recv_mb = network.bytes_recv / (1024 * 1024)
            
            # Métricas de optimización
            metrics.memory_leaks_detected = len(self.stats["memory_leaks"])
            
            # Calcular cache hit rate
            total_cache_ops = (self.stats["optimization_stats"]["cache_hits"] + 
                             self.stats["optimization_stats"]["cache_misses"])
            if total_cache_ops > 0:
                metrics.cache_hit_rate = (self.stats["optimization_stats"]["cache_hits"] / 
                                        total_cache_ops) * 100
                
            metrics.lazy_loaded_components = self.stats["optimization_stats"]["lazy_loaded_components"]
            
        except Exception as e:
            logger.error(f"Error recolectando métricas: {e}")
        
        return metrics

    def _process_metrics(self, metrics: PerformanceMetrics):
        """Procesar y almacenar métricas"""
        self.metrics_history.append(metrics)
        self.stats["total_samples"] += 1
        
        # Actualizar estadísticas
        if metrics.cpu_percent > self.stats["peak_cpu"]:
            self.stats["peak_cpu"] = metrics.cpu_percent
        
        if metrics.memory_percent > self.stats["peak_memory"]:
            self.stats["peak_memory"] = metrics.memory_percent
        
        # Calcular promedios
        if len(self.metrics_history) > 0:
            cpu_values = [m.cpu_percent for m in self.metrics_history]
            memory_values = [m.memory_percent for m in self.metrics_history]
            
            self.stats["avg_cpu"] = sum(cpu_values) / len(cpu_values)
            self.stats["avg_memory"] = sum(memory_values) / len(memory_values)

    def _detect_memory_leaks(self):
        """Detectar memory leaks"""
        try:
            self.memory_leak_detector.take_snapshot()
            leaks = self.memory_leak_detector.detect_leaks()
            
            if leaks:
                self.stats["memory_leaks"].extend(leaks)
                logger.warning(f"Detectados {len(leaks)} posibles memory leaks")
                
        except Exception as e:
            logger.error(f"Error detectando memory leaks: {e}")

    def _check_thresholds(self, metrics: PerformanceMetrics):
        """Verificar umbrales y generar alertas"""
        current_time = datetime.now()
        
        # CPU
        if metrics.cpu_percent >= self.thresholds["cpu_critical"]:
            self._add_alert("CRITICAL", f"CPU crítico: {metrics.cpu_percent:.1f}%", current_time)
        elif metrics.cpu_percent >= self.thresholds["cpu_warning"]:
            self._add_alert("WARNING", f"CPU alto: {metrics.cpu_percent:.1f}%", current_time)
        
        # Memoria
        if metrics.memory_percent >= self.thresholds["memory_critical"]:
            self._add_alert("CRITICAL", f"Memoria crítica: {metrics.memory_percent:.1f}%", current_time)
        elif metrics.memory_percent >= self.thresholds["memory_warning"]:
            self._add_alert("WARNING", f"Memoria alta: {metrics.memory_percent:.1f}%", current_time)
        
        # Disco
        if metrics.disk_usage_percent >= self.thresholds["disk_critical"]:
            self._add_alert("CRITICAL", f"Disco crítico: {metrics.disk_usage_percent:.1f}%", current_time)
        elif metrics.disk_usage_percent >= self.thresholds["disk_warning"]:
            self._add_alert("WARNING", f"Disco alto: {metrics.disk_usage_percent:.1f}%", current_time)

    def _add_alert(self, level: str, message: str, timestamp: datetime):
        """Agregar alerta"""
        alert = {
            "level": level,
            "message": message,
            "timestamp": timestamp.isoformat()
        }
        self.stats["alerts"].append(alert)
        
        # Mantener solo las últimas 100 alertas
        if len(self.stats["alerts"]) > 100:
            self.stats["alerts"] = self.stats["alerts"][-100:]
        
        logger.warning(f"Alerta de rendimiento [{level}]: {message}")

    def _log_performance(self, metrics: PerformanceMetrics):
        """Log de rendimiento"""
        if self.log_performance and time.time() - self.last_log_time >= self.log_interval:
            logger.info(f"Rendimiento - CPU: {metrics.cpu_percent:.1f}%, "
                       f"Memoria: {metrics.memory_percent:.1f}%, "
                       f"Cache Hit Rate: {metrics.cache_hit_rate:.1f}%")
            self.last_log_time = time.time()

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Obtener métricas actuales"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None

    def get_metrics_history(self, minutes: int = 60) -> List[PerformanceMetrics]:
        """Obtener historial de métricas"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if m.timestamp > cutoff_time]

    def get_performance_summary(self) -> Dict:
        """Obtener resumen de rendimiento"""
        if not self.metrics_history:
            return {}
        
        recent_metrics = self.get_metrics_history(30)  # Últimos 30 minutos
        
        if not recent_metrics:
            return {}
        
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        return {
            "current_cpu": cpu_values[-1] if cpu_values else 0,
            "current_memory": memory_values[-1] if memory_values else 0,
            "avg_cpu_30min": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            "avg_memory_30min": sum(memory_values) / len(memory_values) if memory_values else 0,
            "peak_cpu": max(cpu_values) if cpu_values else 0,
            "peak_memory": max(memory_values) if memory_values else 0,
            "memory_leaks": len(self.stats["memory_leaks"]),
            "cache_hit_rate": self.stats["optimization_stats"]["cache_hits"] / 
                            max(1, self.stats["optimization_stats"]["cache_hits"] + 
                                self.stats["optimization_stats"]["cache_misses"]) * 100,
            "optimization_stats": self.stats["optimization_stats"]
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calcular tendencia de valores"""
        if len(values) < 2:
            return "stable"
        
        recent_avg = sum(values[-5:]) / min(5, len(values))
        older_avg = sum(values[:-5]) / max(1, len(values) - 5)
        
        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"

    def export_metrics(self, filename: str):
        """Exportar métricas a archivo"""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "summary": self.get_performance_summary(),
                "alerts": self.stats["alerts"],
                "memory_leaks": self.stats["memory_leaks"],
                "optimization_stats": self.stats["optimization_stats"]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Métricas exportadas a {filename}")
            
        except Exception as e:
            logger.error(f"Error exportando métricas: {e}")

    def set_thresholds(self, **kwargs):
        """Establecer umbrales de alerta"""
        for key, value in kwargs.items():
            if key in self.thresholds:
                self.thresholds[key] = value

    def clear_alerts(self):
        """Limpiar alertas"""
        self.stats["alerts"] = []

    def get_system_info(self) -> Dict:
        """Obtener información del sistema"""
        try:
            return {
                "platform": sys.platform,
                "python_version": sys.version,
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_total_gb": psutil.disk_usage('/').total / (1024**3)
            }
        except Exception as e:
            logger.error(f"Error obteniendo información del sistema: {e}")
            return {}

    # Métodos de optimización
    def register_lazy_component(self, component_id: str, load_func: Callable, 
                               dependencies: Optional[List[str]] = None):
        """Registrar componente para carga diferida"""
        self.lazy_loading_manager.register_component(component_id, load_func, dependencies)
        
    def load_lazy_component(self, component_id: str) -> Any:
        """Cargar componente de forma diferida"""
        result = self.lazy_loading_manager.load_component(component_id)
        if result:
            self.stats["optimization_stats"]["lazy_loaded_components"] += 1
        return result
        
    def create_virtual_list(self, total_items: int, item_height: int, 
                           create_item_func: Callable, parent_widget=None):
        """Crear lista virtualizada"""
        result = self.virtualization_manager.create_virtual_list(
            total_items, item_height, create_item_func, parent_widget)
        self.stats["optimization_stats"]["virtualized_lists"] += 1
        return result
        
    def compress_data(self, data: Any) -> bytes:
        """Comprimir datos"""
        compressed = self.data_compressor.compress_data(data)
        if compressed:
            self.stats["optimization_stats"]["compressed_data_mb"] += len(compressed) / (1024 * 1024)
        return compressed
        
    def decompress_data(self, compressed_data: bytes) -> Any:
        """Descomprimir datos"""
        return self.data_compressor.decompress_data(compressed_data)
        
    def cache_compressed(self, key: str, data: Any):
        """Cachear datos comprimidos"""
        self.data_compressor.cache_compressed(key, data)
        self.stats["optimization_stats"]["cache_hits"] += 1
        
    def get_cached(self, key: str) -> Any:
        """Obtener datos del cache comprimido"""
        result = self.data_compressor.get_cached(key)
        if result:
            self.stats["optimization_stats"]["cache_hits"] += 1
        else:
            self.stats["optimization_stats"]["cache_misses"] += 1
        return result
        
    def setup_query_optimizer(self, db_path: str):
        """Configurar optimizador de consultas"""
        self.query_optimizer = QueryOptimizer(db_path)
        
    def optimize_query(self, query: str, params: Optional[tuple] = None) -> str:
        """Optimizar consulta SQL"""
        if self.query_optimizer:
            return self.query_optimizer.optimize_query(query, params)
        return query
        
    def force_garbage_collection(self):
        """Forzar garbage collection"""
        collected = gc.collect()
        logger.info(f"Garbage collection completado: {collected} objetos recolectados")
        return collected

# Instancia global del monitor
_performance_monitor: Optional[PerformanceMonitor] = None

def get_performance_monitor() -> PerformanceMonitor:
    """Obtener instancia global del monitor de rendimiento"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def start_performance_monitoring():
    """Iniciar monitoreo de rendimiento"""
    monitor = get_performance_monitor()
    monitor.start_monitoring()

def stop_performance_monitoring():
    """Detener monitoreo de rendimiento"""
    monitor = get_performance_monitor()
    monitor.stop_monitoring()

def get_performance_status() -> Dict:
    """Obtener estado de rendimiento"""
    monitor = get_performance_monitor()
    return monitor.get_performance_summary()

def add_performance_callback(callback: Callable[[PerformanceMetrics], None]):
    """Agregar callback de rendimiento"""
    monitor = get_performance_monitor()
    monitor.add_callback(callback)

def export_performance_data(filename: Optional[str] = None):
    """Exportar datos de rendimiento"""
    monitor = get_performance_monitor()
    if not filename:
        filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    monitor.export_metrics(filename)

# Decorador para monitorear funciones
def monitor_ui_function(function_name: str):
    """Decorador para monitorear rendimiento de funciones UI"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # ms
                
                # Registrar métrica si es lenta
                if execution_time > 100:  # Más de 100ms
                    logger.warning(f"Función UI lenta: {function_name} tomó {execution_time:.1f}ms")
                    
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Error en función UI {function_name} después de {execution_time:.1f}ms: {e}")
                raise
                
        return wrapper
    return decorator 