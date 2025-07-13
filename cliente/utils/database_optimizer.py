"""
Optimizador de Base de Datos Avanzado
Sistema de Gestión de Gimnasio v6 - Fase 4

Implementa optimizaciones avanzadas para la base de datos local:
- Índices automáticos
- Consultas preparadas
- Pool de conexiones
- Limpieza automática
- Monitoreo de rendimiento
- Compresión de datos
"""

import sqlite3
import logging
import threading
import time
import json
import os
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import queue
import weakref

from utils.performance_monitor import get_performance_monitor, monitor_ui_function

logger = logging.getLogger(__name__)

class ConnectionPool:
    """Pool de conexiones para optimizar acceso a base de datos"""
    
    def __init__(self, db_path: str, max_connections: int = 10, timeout: int = 30):
        self.db_path = db_path
        self.max_connections = max_connections
        self.timeout = timeout
        
        # Pool de conexiones
        self.connections = queue.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.connection_lock = threading.Lock()
        
        # Estadísticas
        self.stats = {
            "connections_created": 0,
            "connections_reused": 0,
            "connections_timeout": 0,
            "total_queries": 0,
            "avg_query_time": 0.0
        }
        
        # Inicializar conexiones
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Inicializar pool con conexiones básicas"""
        try:
            for _ in range(min(3, self.max_connections)):
                conn = self._create_connection()
                if conn:
                    self.connections.put(conn)
                    self.stats["connections_created"] += 1
                    
        except Exception as e:
            logger.error(f"Error inicializando pool de conexiones: {e}")
            
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Crear nueva conexión"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            
            # Configurar conexión para mejor rendimiento
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            return conn
            
        except Exception as e:
            logger.error(f"Error creando conexión: {e}")
            return None
            
    def get_connection(self) -> Optional[sqlite3.Connection]:
        """Obtener conexión del pool"""
        try:
            # Intentar obtener conexión existente
            try:
                conn = self.connections.get_nowait()
                self.stats["connections_reused"] += 1
                return conn
            except queue.Empty:
                pass
                
            # Crear nueva conexión si es posible
            with self.connection_lock:
                if self.active_connections < self.max_connections:
                    conn = self._create_connection()
                    if conn:
                        self.active_connections += 1
                        self.stats["connections_created"] += 1
                        return conn
                        
            # Esperar por una conexión disponible
            try:
                conn = self.connections.get(timeout=5)
                self.stats["connections_reused"] += 1
                return conn
            except queue.Empty:
                self.stats["connections_timeout"] += 1
                logger.warning("Timeout esperando conexión del pool")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo conexión: {e}")
            return None
            
    def return_connection(self, conn: sqlite3.Connection):
        """Devolver conexión al pool"""
        try:
            if conn:
                # Verificar que la conexión esté válida
                try:
                    conn.execute("SELECT 1")
                    self.connections.put(conn)
                except sqlite3.Error:
                    # Conexión inválida, crear nueva
                    conn.close()
                    with self.connection_lock:
                        self.active_connections -= 1
                        
        except Exception as e:
            logger.error(f"Error devolviendo conexión: {e}")
            
    def close_all(self):
        """Cerrar todas las conexiones"""
        try:
            while not self.connections.empty():
                conn = self.connections.get_nowait()
                conn.close()
                
            with self.connection_lock:
                self.active_connections = 0
                
        except Exception as e:
            logger.error(f"Error cerrando pool: {e}")

class QueryAnalyzer:
    """Analizador de consultas para optimización automática"""
    
    def __init__(self):
        self.query_patterns = defaultdict(int)
        self.slow_queries = deque(maxlen=100)
        self.index_suggestions = []
        
    def analyze_query(self, query: str, execution_time: float) -> Dict[str, Any]:
        """Analizar consulta para optimización"""
        try:
            analysis = {
                "query": query,
                "execution_time": execution_time,
                "pattern": self._extract_pattern(query),
                "suggestions": []
            }
            
            # Registrar patrón
            pattern = analysis["pattern"]
            self.query_patterns[pattern] += 1
            
            # Detectar consultas lentas
            if execution_time > 1.0:  # Más de 1 segundo
                self.slow_queries.append(analysis)
                
            # Generar sugerencias
            analysis["suggestions"] = self._generate_suggestions(query, execution_time)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analizando consulta: {e}")
            return {"query": query, "execution_time": execution_time, "suggestions": []}
            
    def _extract_pattern(self, query: str) -> str:
        """Extraer patrón de la consulta"""
        try:
            # Simplificar consulta para identificar patrón
            query_lower = query.lower().strip()
            
            # Identificar tipo de consulta
            if query_lower.startswith("select"):
                return "SELECT"
            elif query_lower.startswith("insert"):
                return "INSERT"
            elif query_lower.startswith("update"):
                return "UPDATE"
            elif query_lower.startswith("delete"):
                return "DELETE"
            else:
                return "OTHER"
                
        except Exception as e:
            logger.error(f"Error extrayendo patrón: {e}")
            return "UNKNOWN"
            
    def _generate_suggestions(self, query: str, execution_time: float) -> List[str]:
        """Generar sugerencias de optimización"""
        suggestions = []
        
        try:
            query_lower = query.lower()
            
            # Sugerir índices para WHERE
            if "where" in query_lower and execution_time > 0.1:
                # Identificar columnas en WHERE
                where_start = query_lower.find("where")
                if where_start != -1:
                    where_clause = query_lower[where_start:]
                    # Buscar columnas comunes
                    for col in ["id", "user_id", "created_at", "updated_at", "status"]:
                        if col in where_clause:
                            suggestions.append(f"Considerar índice en columna '{col}'")
                            
            # Sugerir LIMIT para SELECT grandes
            if query_lower.startswith("select") and "limit" not in query_lower:
                suggestions.append("Considerar agregar LIMIT para consultas grandes")
                
            # Sugerir optimización de JOINs
            if "join" in query_lower and execution_time > 0.5:
                suggestions.append("Revisar optimización de JOINs")
                
            # Sugerir índices para ORDER BY
            if "order by" in query_lower and execution_time > 0.2:
                suggestions.append("Considerar índices para columnas en ORDER BY")
                
        except Exception as e:
            logger.error(f"Error generando sugerencias: {e}")
            
        return suggestions
        
    def get_optimization_report(self) -> Dict[str, Any]:
        """Obtener reporte de optimización"""
        try:
            return {
                "query_patterns": dict(self.query_patterns),
                "slow_queries_count": len(self.slow_queries),
                "slow_queries": list(self.slow_queries)[-10:],  # Últimas 10
                "index_suggestions": self.index_suggestions
            }
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return {}

class PreparedStatementManager:
    """Gestor de statements preparados"""
    
    def __init__(self):
        self.prepared_statements = {}
        self.statement_stats = defaultdict(lambda: {"count": 0, "total_time": 0.0})
        
    def prepare(self, name: str, query: str, conn: sqlite3.Connection):
        """Preparar statement"""
        try:
            if name not in self.prepared_statements:
                self.prepared_statements[name] = {
                    "query": query,
                    "connection": conn
                }
                logger.info(f"Statement preparado: {name}")
                
        except Exception as e:
            logger.error(f"Error preparando statement {name}: {e}")
            
    def execute(self, name: str, params: Tuple = None) -> Optional[sqlite3.Cursor]:
        """Ejecutar statement preparado"""
        try:
            if name in self.prepared_statements:
                start_time = time.time()
                
                stmt_info = self.prepared_statements[name]
                cursor = stmt_info["connection"].cursor()
                result = cursor.execute(stmt_info["query"], params or ())
                
                # Actualizar estadísticas
                execution_time = time.time() - start_time
                self.statement_stats[name]["count"] += 1
                self.statement_stats[name]["total_time"] += execution_time
                
                return result
                
        except Exception as e:
            logger.error(f"Error ejecutando statement {name}: {e}")
            return None
            
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de statements"""
        try:
            stats = {}
            for name, stat in self.statement_stats.items():
                if stat["count"] > 0:
                    stats[name] = {
                        "count": stat["count"],
                        "avg_time": stat["total_time"] / stat["count"],
                        "total_time": stat["total_time"]
                    }
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

class DatabaseOptimizer:
    """Optimizador principal de base de datos"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Componentes
        self.connection_pool = ConnectionPool(db_path)
        self.query_analyzer = QueryAnalyzer()
        self.statement_manager = PreparedStatementManager()
        
        # Performance monitor
        self.performance_monitor = get_performance_monitor()
        
        # Configuración
        self.auto_vacuum = True
        self.auto_analyze = True
        self.compression_enabled = True
        
        # Timers para mantenimiento
        self.maintenance_timer = None
        self.cleanup_timer = None
        
        # Inicializar optimizaciones
        self._initialize_optimizations()
        
    def _initialize_optimizations(self):
        """Inicializar optimizaciones de base de datos"""
        try:
            conn = self.connection_pool.get_connection()
            if conn:
                # Configurar base de datos para rendimiento
                conn.execute("PRAGMA auto_vacuum=INCREMENTAL")
                conn.execute("PRAGMA optimize")
                conn.execute("PRAGMA analysis_limit=1000")
                
                # Crear índices automáticos si no existen
                self._create_automatic_indexes(conn)
                
                # Preparar statements comunes
                self._prepare_common_statements(conn)
                
                self.connection_pool.return_connection(conn)
                
            logger.info("Optimizaciones de base de datos inicializadas")
            
        except Exception as e:
            logger.error(f"Error inicializando optimizaciones: {e}")
            
    def _create_automatic_indexes(self, conn: sqlite3.Connection):
        """Crear índices automáticos para mejorar rendimiento"""
        try:
            # Índices para tablas principales
            indexes = [
                ("usuarios", "email"),
                ("usuarios", "created_at"),
                ("usuarios", "status"),
                ("clases", "fecha"),
                ("clases", "instructor_id"),
                ("asistencias", "usuario_id"),
                ("asistencias", "fecha"),
                ("pagos", "usuario_id"),
                ("pagos", "fecha"),
                ("empleados", "email"),
                ("empleados", "status")
            ]
            
            for table, column in indexes:
                index_name = f"idx_{table}_{column}"
                try:
                    conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
                except sqlite3.Error as e:
                    logger.warning(f"No se pudo crear índice {index_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error creando índices automáticos: {e}")
            
    def _prepare_common_statements(self, conn: sqlite3.Connection):
        """Preparar statements comunes"""
        try:
            common_queries = {
                "get_user_by_id": "SELECT * FROM usuarios WHERE id = ?",
                "get_users_by_status": "SELECT * FROM usuarios WHERE status = ? LIMIT ?",
                "get_classes_by_date": "SELECT * FROM clases WHERE fecha >= ? AND fecha <= ?",
                "get_attendance_by_user": "SELECT * FROM asistencias WHERE usuario_id = ? ORDER BY fecha DESC",
                "get_payments_by_user": "SELECT * FROM pagos WHERE usuario_id = ? ORDER BY fecha DESC",
                "get_employees_active": "SELECT * FROM empleados WHERE status = 'activo'"
            }
            
            for name, query in common_queries.items():
                self.statement_manager.prepare(name, query, conn)
                
        except Exception as e:
            logger.error(f"Error preparando statements comunes: {e}")
            
    @monitor_ui_function("database_query")
    def execute_query(self, query: str, params: Tuple = None, use_prepared: bool = False) -> Optional[List[Dict[str, Any]]]:
        """Ejecutar consulta optimizada"""
        try:
            start_time = time.time()
            
            conn = self.connection_pool.get_connection()
            if not conn:
                return None
                
            try:
                cursor = conn.cursor()
                
                if use_prepared and query in self.statement_manager.prepared_statements:
                    result = self.statement_manager.execute(query, params)
                else:
                    result = cursor.execute(query, params or ())
                    
                if result:
                    # Obtener resultados
                    columns = [description[0] for description in result.description]
                    rows = result.fetchall()
                    
                    # Convertir a lista de diccionarios
                    results = []
                    for row in rows:
                        results.append(dict(zip(columns, row)))
                        
                    # Analizar consulta
                    execution_time = time.time() - start_time
                    analysis = self.query_analyzer.analyze_query(query, execution_time)
                    
                    # Actualizar estadísticas
                    self.connection_pool.stats["total_queries"] += 1
                    
                    # Cachear resultados si es apropiado
                    if len(results) > 0 and execution_time > 0.1:
                        self._cache_results(query, results)
                        
                    return results
                    
            finally:
                self.connection_pool.return_connection(conn)
                
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
            return None
            
    def _cache_results(self, query: str, results: List[Dict[str, Any]]):
        """Cachear resultados de consulta"""
        try:
            if self.compression_enabled:
                # Comprimir resultados
                compressed_data = self.performance_monitor.compress_data(results)
                cache_key = f"query_cache_{hash(query)}"
                self.performance_monitor.cache_compressed(cache_key, compressed_data)
                
        except Exception as e:
            logger.error(f"Error cacheando resultados: {e}")
            
    def optimize_database(self):
        """Ejecutar optimizaciones de base de datos"""
        try:
            conn = self.connection_pool.get_connection()
            if not conn:
                return
                
            try:
                # VACUUM para optimizar espacio
                conn.execute("VACUUM")
                
                # ANALYZE para actualizar estadísticas
                conn.execute("ANALYZE")
                
                # Optimizar configuración
                conn.execute("PRAGMA optimize")
                
                # Limpiar datos antiguos
                self._cleanup_old_data(conn)
                
                logger.info("Optimización de base de datos completada")
                
            finally:
                self.connection_pool.return_connection(conn)
                
        except Exception as e:
            logger.error(f"Error optimizando base de datos: {e}")
            
    def _cleanup_old_data(self, conn: sqlite3.Connection):
        """Limpiar datos antiguos"""
        try:
            # Limpiar logs antiguos (más de 30 días)
            conn.execute("""
                DELETE FROM logs 
                WHERE created_at < datetime('now', '-30 days')
            """)
            
            # Limpiar backups temporales antiguos
            conn.execute("""
                DELETE FROM temp_backups 
                WHERE created_at < datetime('now', '-7 days')
            """)
            
            # Limpiar sesiones expiradas
            conn.execute("""
                DELETE FROM user_sessions 
                WHERE expires_at < datetime('now')
            """)
            
        except sqlite3.Error as e:
            logger.warning(f"Error limpiando datos antiguos: {e}")
            
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de rendimiento"""
        try:
            return {
                "connection_pool": self.connection_pool.stats,
                "query_analysis": self.query_analyzer.get_optimization_report(),
                "prepared_statements": self.statement_manager.get_stats(),
                "database_size_mb": self._get_database_size(),
                "optimization_status": {
                    "auto_vacuum": self.auto_vacuum,
                    "auto_analyze": self.auto_analyze,
                    "compression_enabled": self.compression_enabled
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
            
    def _get_database_size(self) -> float:
        """Obtener tamaño de la base de datos en MB"""
        try:
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)
                return size_bytes / (1024 * 1024)
            return 0.0
        except Exception as e:
            logger.error(f"Error obteniendo tamaño de BD: {e}")
            return 0.0
            
    def export_optimization_report(self, filename: str):
        """Exportar reporte de optimización"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "database_path": self.db_path,
                "performance_stats": self.get_performance_stats(),
                "optimization_suggestions": self._generate_optimization_suggestions()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Reporte de optimización exportado a {filename}")
            
        except Exception as e:
            logger.error(f"Error exportando reporte: {e}")
            
    def _generate_optimization_suggestions(self) -> List[str]:
        """Generar sugerencias de optimización"""
        suggestions = []
        
        try:
            stats = self.get_performance_stats()
            
            # Sugerencias basadas en estadísticas
            if stats.get("connection_pool", {}).get("connections_timeout", 0) > 10:
                suggestions.append("Considerar aumentar el tamaño del pool de conexiones")
                
            if stats.get("query_analysis", {}).get("slow_queries_count", 0) > 5:
                suggestions.append("Revisar consultas lentas y optimizar índices")
                
            db_size = stats.get("database_size_mb", 0)
            if db_size > 100:
                suggestions.append("Considerar limpieza de datos antiguos para reducir tamaño")
                
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generando sugerencias: {e}")
            return []
            
    def start_maintenance_timers(self):
        """Iniciar timers de mantenimiento"""
        try:
            # Timer para optimización automática (cada 6 horas)
            self.maintenance_timer = threading.Timer(21600, self._maintenance_cycle)
            self.maintenance_timer.daemon = True
            self.maintenance_timer.start()
            
            # Timer para limpieza (cada 24 horas)
            self.cleanup_timer = threading.Timer(86400, self._cleanup_cycle)
            self.cleanup_timer.daemon = True
            self.cleanup_timer.start()
            
            logger.info("Timers de mantenimiento iniciados")
            
        except Exception as e:
            logger.error(f"Error iniciando timers: {e}")
            
    def _maintenance_cycle(self):
        """Ciclo de mantenimiento automático"""
        try:
            logger.info("Iniciando ciclo de mantenimiento automático")
            
            # Optimizar base de datos
            self.optimize_database()
            
            # Reiniciar timer
            self.maintenance_timer = threading.Timer(21600, self._maintenance_cycle)
            self.maintenance_timer.daemon = True
            self.maintenance_timer.start()
            
        except Exception as e:
            logger.error(f"Error en ciclo de mantenimiento: {e}")
            
    def _cleanup_cycle(self):
        """Ciclo de limpieza automática"""
        try:
            logger.info("Iniciando ciclo de limpieza automática")
            
            conn = self.connection_pool.get_connection()
            if conn:
                try:
                    self._cleanup_old_data(conn)
                finally:
                    self.connection_pool.return_connection(conn)
                    
            # Reiniciar timer
            self.cleanup_timer = threading.Timer(86400, self._cleanup_cycle)
            self.cleanup_timer.daemon = True
            self.cleanup_timer.start()
            
        except Exception as e:
            logger.error(f"Error en ciclo de limpieza: {e}")
            
    def close(self):
        """Cerrar optimizador"""
        try:
            # Detener timers
            if self.maintenance_timer:
                self.maintenance_timer.cancel()
            if self.cleanup_timer:
                self.cleanup_timer.cancel()
                
            # Cerrar pool de conexiones
            self.connection_pool.close_all()
            
            logger.info("Optimizador de base de datos cerrado")
            
        except Exception as e:
            logger.error(f"Error cerrando optimizador: {e}")

# Instancia global del optimizador
_database_optimizer: Optional[DatabaseOptimizer] = None

def get_database_optimizer(db_path: str = None) -> DatabaseOptimizer:
    """Obtener instancia global del optimizador de base de datos"""
    global _database_optimizer
    if _database_optimizer is None and db_path:
        _database_optimizer = DatabaseOptimizer(db_path)
        _database_optimizer.start_maintenance_timers()
    return _database_optimizer

def close_database_optimizer():
    """Cerrar optimizador de base de datos"""
    global _database_optimizer
    if _database_optimizer:
        _database_optimizer.close()
        _database_optimizer = None 