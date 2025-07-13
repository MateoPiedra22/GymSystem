#!/usr/bin/env python3
"""
Script de Optimización de Base de Datos - Sistema de Gimnasio v6
Analiza y optimiza consultas, índices y configuración de PostgreSQL
"""

import os
import sys
import json
import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import logging
import argparse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Optimizador de base de datos PostgreSQL"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "optimizations": {},
            "recommendations": [],
            "summary": {
                "total_checks": 0,
                "optimizations_applied": 0,
                "recommendations_generated": 0
            }
        }
    
    def connect(self):
        """Conectar a la base de datos"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config.get("host", "localhost"),
                port=self.db_config.get("port", "5432"),
                database=self.db_config.get("database", "gym_system"),
                user=self.db_config.get("user", "postgres"),
                password=self.db_config.get("password", "")
            )
            logger.info("✅ Conexión a base de datos establecida")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a la base de datos: {e}")
            return False
    
    def disconnect(self):
        """Desconectar de la base de datos"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Conexión a base de datos cerrada")
    
    def run_full_optimization(self) -> Dict[str, Any]:
        """Ejecutar optimización completa de la base de datos"""
        logger.info("🔍 Iniciando optimización completa de base de datos...")
        
        if not self.connect():
            return self.results
        
        try:
            # Análisis de tablas y índices
            self.analyze_table_statistics()
            self.analyze_index_usage()
            self.analyze_slow_queries()
            self.analyze_table_bloat()
            self.analyze_vacuum_status()
            self.analyze_connection_usage()
            self.analyze_lock_contention()
            
            # Generar recomendaciones
            self.generate_optimization_recommendations()
            
            # Aplicar optimizaciones automáticas
            self.apply_automatic_optimizations()
            
        finally:
            self.disconnect()
        
        return self.results
    
    def analyze_table_statistics(self):
        """Analizar estadísticas de tablas"""
        logger.info("📊 Analizando estadísticas de tablas...")
        
        query = """
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation,
            most_common_vals,
            most_common_freqs
        FROM pg_stats 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, tablename, attname;
        """
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query)
                stats = cursor.fetchall()
                
                # Analizar distribución de datos
                for stat in stats:
                    table_name = f"{stat['schemaname']}.{stat['tablename']}"
                    column_name = stat['attname']
                    
                    # Verificar si la columna tiene buena distribución
                    if stat['n_distinct'] > 0:
                        distinct_ratio = stat['n_distinct'] / self._get_table_row_count(table_name)
                        
                        if distinct_ratio < 0.1:  # Menos del 10% de valores únicos
                            self._add_recommendation(
                                "low_cardinality",
                                f"Columna {column_name} en {table_name} tiene baja cardinalidad",
                                f"Considerar agregar índice o revisar diseño de datos"
                            )
                        
                        if stat['correlation'] and abs(stat['correlation']) > 0.9:
                            self._add_recommendation(
                                "high_correlation",
                                f"Columna {column_name} en {table_name} tiene alta correlación",
                                f"Considerar índice para mejorar consultas de rango"
                            )
                
                self._add_optimization_result("table_statistics", "PASSED", f"Analizadas {len(stats)} columnas")
                
        except Exception as e:
            logger.error(f"Error analizando estadísticas de tablas: {e}")
            self._add_optimization_result("table_statistics", "FAILED", str(e))
    
    def analyze_index_usage(self):
        """Analizar uso de índices"""
        logger.info("🔍 Analizando uso de índices...")
        
        # Consulta para índices no utilizados
        unused_indexes_query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch
        FROM pg_stat_user_indexes 
        WHERE idx_scan = 0 
        AND schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, tablename;
        """
        
        # Consulta para índices con bajo uso
        low_usage_query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size
        FROM pg_stat_user_indexes 
        WHERE idx_scan < 10 
        AND schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY idx_scan ASC;
        """
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Índices no utilizados
                cursor.execute(unused_indexes_query)
                unused_indexes = cursor.fetchall()
                
                for index in unused_indexes:
                    self._add_recommendation(
                        "unused_index",
                        f"Índice no utilizado: {index['indexname']} en {index['schemaname']}.{index['tablename']}",
                        f"Considerar eliminar el índice para mejorar rendimiento de escritura"
                    )
                
                # Índices con bajo uso
                cursor.execute(low_usage_query)
                low_usage_indexes = cursor.fetchall()
                
                for index in low_usage_indexes:
                    self._add_recommendation(
                        "low_usage_index",
                        f"Índice con bajo uso: {index['indexname']} ({index['idx_scan']} scans)",
                        f"Revisar si el índice es necesario o puede ser optimizado"
                    )
                
                self._add_optimization_result("index_usage", "PASSED", 
                    f"Encontrados {len(unused_indexes)} índices no utilizados, {len(low_usage_indexes)} con bajo uso")
                
        except Exception as e:
            logger.error(f"Error analizando uso de índices: {e}")
            self._add_optimization_result("index_usage", "FAILED", str(e))
    
    def analyze_slow_queries(self):
        """Analizar consultas lentas"""
        logger.info("⏱️ Analizando consultas lentas...")
        
        # Consulta para obtener estadísticas de consultas
        slow_queries_query = """
        SELECT 
            query,
            calls,
            total_time,
            mean_time,
            rows,
            shared_blks_hit,
            shared_blks_read,
            shared_blks_written,
            shared_blks_dirtied,
            temp_blks_read,
            temp_blks_written,
            blk_read_time,
            blk_write_time
        FROM pg_stat_statements 
        WHERE mean_time > 100  -- Consultas que toman más de 100ms en promedio
        ORDER BY mean_time DESC 
        LIMIT 20;
        """
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(slow_queries_query)
                slow_queries = cursor.fetchall()
                
                for query in slow_queries:
                    # Analizar patrones en consultas lentas
                    query_text = query['query'].lower()
                    
                    if 'select *' in query_text:
                        self._add_recommendation(
                            "select_star",
                            f"Consulta lenta usa SELECT * (promedio: {query['mean_time']:.2f}ms)",
                            "Especificar solo las columnas necesarias"
                        )
                    
                    if 'order by' in query_text and 'limit' not in query_text:
                        self._add_recommendation(
                            "order_without_limit",
                            f"Consulta con ORDER BY sin LIMIT (promedio: {query['mean_time']:.2f}ms)",
                            "Agregar LIMIT para reducir resultados"
                        )
                    
                    if query['shared_blks_read'] > query['shared_blks_hit'] * 0.1:
                        self._add_recommendation(
                            "high_disk_reads",
                            f"Consulta con muchas lecturas de disco (promedio: {query['mean_time']:.2f}ms)",
                            "Revisar índices y estadísticas de tablas"
                        )
                
                self._add_optimization_result("slow_queries", "PASSED", 
                    f"Analizadas {len(slow_queries)} consultas lentas")
                
        except Exception as e:
            logger.error(f"Error analizando consultas lentas: {e}")
            self._add_optimization_result("slow_queries", "FAILED", str(e))
    
    def analyze_table_bloat(self):
        """Analizar bloat (fragmentación) de tablas"""
        logger.info("📦 Analizando bloat de tablas...")
        
        bloat_query = """
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation,
            most_common_vals,
            most_common_freqs
        FROM pg_stats 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, tablename, attname;
        """
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(bloat_query)
                stats = cursor.fetchall()
                
                # Verificar tablas que necesitan VACUUM
                vacuum_needed_query = """
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    n_live_tup,
                    n_dead_tup,
                    last_vacuum,
                    last_autovacuum
                FROM pg_stat_user_tables 
                WHERE n_dead_tup > n_live_tup * 0.1  -- Más del 10% de filas muertas
                ORDER BY n_dead_tup DESC;
                """
                
                cursor.execute(vacuum_needed_query)
                tables_needing_vacuum = cursor.fetchall()
                
                for table in tables_needing_vacuum:
                    table_name = f"{table['schemaname']}.{table['tablename']}"
                    dead_ratio = table['n_dead_tup'] / (table['n_live_tup'] + table['n_dead_tup'])
                    
                    self._add_recommendation(
                        "vacuum_needed",
                        f"Tabla {table_name} necesita VACUUM ({dead_ratio:.1%} filas muertas)",
                        f"Ejecutar VACUUM ANALYZE en {table_name}"
                    )
                
                self._add_optimization_result("table_bloat", "PASSED", 
                    f"Encontradas {len(tables_needing_vacuum)} tablas que necesitan VACUUM")
                
        except Exception as e:
            logger.error(f"Error analizando bloat de tablas: {e}")
            self._add_optimization_result("table_bloat", "FAILED", str(e))
    
    def analyze_vacuum_status(self):
        """Analizar estado de VACUUM"""
        logger.info("🧹 Analizando estado de VACUUM...")
        
        vacuum_status_query = """
        SELECT 
            schemaname,
            tablename,
            last_vacuum,
            last_autovacuum,
            vacuum_count,
            autovacuum_count,
            n_tup_ins,
            n_tup_upd,
            n_tup_del,
            n_live_tup,
            n_dead_tup
        FROM pg_stat_user_tables 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY n_dead_tup DESC;
        """
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(vacuum_status_query)
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = f"{table['schemaname']}.{table['tablename']}"
                    
                    # Verificar si autovacuum está funcionando
                    if table['last_autovacuum'] is None and table['n_dead_tup'] > 0:
                        self._add_recommendation(
                            "autovacuum_disabled",
                            f"Autovacuum no ha ejecutado en {table_name}",
                            "Verificar configuración de autovacuum"
                        )
                    
                    # Verificar si necesita VACUUM manual
                    if table['n_dead_tup'] > table['n_live_tup'] * 0.2:  # Más del 20%
                        self._add_recommendation(
                            "manual_vacuum_needed",
                            f"Tabla {table_name} necesita VACUUM manual urgente",
                            f"Ejecutar VACUUM FULL en {table_name}"
                        )
                
                self._add_optimization_result("vacuum_status", "PASSED", 
                    f"Analizadas {len(tables)} tablas")
                
        except Exception as e:
            logger.error(f"Error analizando estado de VACUUM: {e}")
            self._add_optimization_result("vacuum_status", "FAILED", str(e))
    
    def analyze_connection_usage(self):
        """Analizar uso de conexiones"""
        logger.info("🔌 Analizando uso de conexiones...")
        
        connection_query = """
        SELECT 
            state,
            count(*) as connection_count,
            application_name,
            client_addr,
            backend_start,
            state_change
        FROM pg_stat_activity 
        WHERE datname = current_database()
        GROUP BY state, application_name, client_addr, backend_start, state_change
        ORDER BY connection_count DESC;
        """
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(connection_query)
                connections = cursor.fetchall()
                
                # Obtener configuración de conexiones
                cursor.execute("SHOW max_connections;")
                max_connections = cursor.fetchone()[0]
                
                total_connections = sum(conn['connection_count'] for conn in connections)
                active_connections = sum(conn['connection_count'] for conn in connections if conn['state'] == 'active')
                
                # Verificar uso de conexiones
                connection_usage = total_connections / int(max_connections)
                
                if connection_usage > 0.8:  # Más del 80%
                    self._add_recommendation(
                        "high_connection_usage",
                        f"Alto uso de conexiones ({connection_usage:.1%})",
                        "Considerar aumentar max_connections o optimizar conexiones"
                    )
                
                # Verificar conexiones inactivas
                idle_connections = sum(conn['connection_count'] for conn in connections if conn['state'] == 'idle')
                if idle_connections > active_connections * 2:
                    self._add_recommendation(
                        "idle_connections",
                        f"Muchas conexiones inactivas ({idle_connections} vs {active_connections} activas)",
                        "Revisar configuración de pool de conexiones"
                    )
                
                self._add_optimization_result("connection_usage", "PASSED", 
                    f"Total: {total_connections}, Activas: {active_connections}, Inactivas: {idle_connections}")
                
        except Exception as e:
            logger.error(f"Error analizando uso de conexiones: {e}")
            self._add_optimization_result("connection_usage", "FAILED", str(e))
    
    def analyze_lock_contention(self):
        """Analizar contención de locks"""
        logger.info("🔒 Analizando contención de locks...")
        
        lock_query = """
        SELECT 
            l.mode,
            l.granted,
            l.pid,
            l.locktype,
            l.database,
            l.relation,
            l.page,
            l.tuple,
            l.virtualxid,
            l.transactionid,
            l.classid,
            l.objid,
            l.objsubid,
            l.virtualtransaction,
            a.usename,
            a.application_name,
            a.client_addr,
            a.state,
            a.query_start,
            a.state_change
        FROM pg_locks l
        JOIN pg_stat_activity a ON l.pid = a.pid
        WHERE l.database = (SELECT oid FROM pg_database WHERE datname = current_database())
        ORDER BY l.granted, l.mode;
        """
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(lock_query)
                locks = cursor.fetchall()
                
                # Analizar locks bloqueados
                blocked_locks = [lock for lock in locks if not lock['granted']]
                
                if blocked_locks:
                    self._add_recommendation(
                        "blocked_locks",
                        f"Encontrados {len(blocked_locks)} locks bloqueados",
                        "Revisar transacciones largas y deadlocks"
                    )
                    
                    # Mostrar detalles de locks bloqueados
                    for lock in blocked_locks[:5]:  # Solo los primeros 5
                        self._add_recommendation(
                            "blocked_lock_detail",
                            f"Lock bloqueado: {lock['mode']} en PID {lock['pid']}",
                            f"Revisar query: {lock.get('query_start', 'N/A')}"
                        )
                
                # Verificar locks de tabla
                table_locks = [lock for lock in locks if lock['locktype'] == 'relation']
                if len(table_locks) > 10:
                    self._add_recommendation(
                        "many_table_locks",
                        f"Muchos locks de tabla ({len(table_locks)})",
                        "Revisar transacciones concurrentes"
                    )
                
                self._add_optimization_result("lock_contention", "PASSED", 
                    f"Total locks: {len(locks)}, Bloqueados: {len(blocked_locks)}")
                
        except Exception as e:
            logger.error(f"Error analizando contención de locks: {e}")
            self._add_optimization_result("lock_contention", "FAILED", str(e))
    
    def generate_optimization_recommendations(self):
        """Generar recomendaciones de optimización"""
        logger.info("💡 Generando recomendaciones de optimización...")
        
        # Agrupar recomendaciones por tipo
        recommendations_by_type = {}
        for rec in self.results["recommendations"]:
            rec_type = rec["type"]
            if rec_type not in recommendations_by_type:
                recommendations_by_type[rec_type] = []
            recommendations_by_type[rec_type].append(rec)
        
        # Generar resumen de recomendaciones
        for rec_type, recs in recommendations_by_type.items():
            self._add_optimization_result(
                f"recommendations_{rec_type}",
                "INFO",
                f"{len(recs)} recomendaciones de tipo {rec_type}"
            )
        
        self.results["summary"]["recommendations_generated"] = len(self.results["recommendations"])
    
    def apply_automatic_optimizations(self):
        """Aplicar optimizaciones automáticas"""
        logger.info("⚡ Aplicando optimizaciones automáticas...")
        
        optimizations_applied = 0
        
        try:
            with self.connection.cursor() as cursor:
                # Actualizar estadísticas de tablas
                cursor.execute("ANALYZE;")
                self._add_optimization_result("auto_analyze", "APPLIED", "Estadísticas actualizadas")
                optimizations_applied += 1
                
                # Ejecutar VACUUM en tablas pequeñas
                cursor.execute("""
                    SELECT schemaname, tablename 
                    FROM pg_stat_user_tables 
                    WHERE n_dead_tup > 0 
                    AND n_live_tup < 10000
                    LIMIT 5;
                """)
                small_tables = cursor.fetchall()
                
                for table in small_tables:
                    table_name = f"{table[0]}.{table[1]}"
                    cursor.execute(f"VACUUM ANALYZE {table_name};")
                    self._add_optimization_result("auto_vacuum", "APPLIED", f"VACUUM en {table_name}")
                    optimizations_applied += 1
                
                self.connection.commit()
                
        except Exception as e:
            logger.error(f"Error aplicando optimizaciones automáticas: {e}")
            self.connection.rollback()
        
        self.results["summary"]["optimizations_applied"] = optimizations_applied
    
    def _get_table_row_count(self, table_name: str) -> int:
        """Obtener número de filas de una tabla"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                return cursor.fetchone()[0]
        except:
            return 1000  # Valor por defecto
    
    def _add_optimization_result(self, check_name: str, status: str, message: str):
        """Agregar resultado de optimización"""
        self.results["optimizations"][check_name] = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.results["summary"]["total_checks"] += 1
    
    def _add_recommendation(self, rec_type: str, message: str, suggestion: str):
        """Agregar recomendación"""
        self.results["recommendations"].append({
            "type": rec_type,
            "message": message,
            "suggestion": suggestion,
            "timestamp": datetime.now().isoformat()
        })
    
    def save_report(self, output_file: str = None):
        """Guardar reporte de optimización"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"database_optimization_{timestamp}.json"
        
        output_path = Path(__file__).parent.parent / "reports" / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Reporte guardado en: {output_path}")
        return output_path
    
    def print_summary(self):
        """Imprimir resumen de la optimización"""
        summary = self.results["summary"]
        
        print("\n" + "="*60)
        print("🗄️ RESUMEN DE OPTIMIZACIÓN DE BASE DE DATOS")
        print("="*60)
        print(f"📊 Total de verificaciones: {summary['total_checks']}")
        print(f"⚡ Optimizaciones aplicadas: {summary['optimizations_applied']}")
        print(f"💡 Recomendaciones generadas: {summary['recommendations_generated']}")
        print("="*60)
        
        # Mostrar optimizaciones aplicadas
        applied_optimizations = [
            (name, opt) for name, opt in self.results["optimizations"].items()
            if opt["status"] == "APPLIED"
        ]
        
        if applied_optimizations:
            print("\n⚡ OPTIMIZACIONES APLICADAS:")
            for name, opt in applied_optimizations:
                print(f"  • {opt['message']}")
        
        # Mostrar recomendaciones importantes
        important_recommendations = [
            rec for rec in self.results["recommendations"]
            if rec["type"] in ["unused_index", "vacuum_needed", "manual_vacuum_needed", "blocked_locks"]
        ]
        
        if important_recommendations:
            print("\n💡 RECOMENDACIONES IMPORTANTES:")
            for rec in important_recommendations[:10]:  # Solo las primeras 10
                print(f"  • {rec['message']}")
                print(f"    Sugerencia: {rec['suggestion']}")
                print()

def load_db_config() -> Dict[str, str]:
    """Cargar configuración de base de datos desde variables de entorno"""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "gym_system"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "")
    }

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Optimizador de Base de Datos - Sistema de Gimnasio v6")
    parser.add_argument("--config", help="Archivo de configuración JSON")
    parser.add_argument("--output", help="Archivo de salida para el reporte")
    parser.add_argument("--apply", action="store_true", help="Aplicar optimizaciones automáticas")
    
    args = parser.parse_args()
    
    print("🗄️ Optimizador de Base de Datos - Sistema de Gimnasio v6")
    print("="*60)
    
    # Cargar configuración
    if args.config:
        with open(args.config, 'r') as f:
            db_config = json.load(f)
    else:
        db_config = load_db_config()
    
    # Crear optimizador
    optimizer = DatabaseOptimizer(db_config)
    
    try:
        # Ejecutar optimización
        results = optimizer.run_full_optimization()
        
        # Imprimir resumen
        optimizer.print_summary()
        
        # Guardar reporte
        report_file = optimizer.save_report(args.output)
        
        print(f"\n📄 Reporte detallado guardado en: {report_file}")
        print("\n✅ Optimización completada exitosamente")
        
        # Retornar código de salida
        if results["summary"]["optimizations_applied"] > 0:
            sys.exit(0)  # Optimizaciones aplicadas
        elif results["summary"]["recommendations_generated"] > 0:
            sys.exit(1)  # Solo recomendaciones
        else:
            sys.exit(2)  # Sin optimizaciones necesarias
            
    except Exception as e:
        logger.error(f"Error durante la optimización: {e}")
        print(f"\n❌ Error durante la optimización: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 