#!/usr/bin/env python3
"""
Script optimizado para crear índices de base de datos y mejorar el rendimiento
Este script analiza la base de datos y crea índices estratégicos para optimizar consultas
"""
import os
import sys
import logging
import time
from typing import List, Dict, Optional
from contextlib import contextmanager

# Agregar directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import get_db, SessionLocal

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("database_optimizer")

class DatabaseOptimizer:
    """Optimizador de base de datos para mejorar rendimiento"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.metadata = MetaData()
        
    @contextmanager
    def get_connection(self):
        """Context manager para manejar conexiones de base de datos"""
        connection = self.engine.connect()
        try:
            yield connection
        except Exception as e:
            connection.rollback()
            logger.error(f"Error en conexión de base de datos: {e}")
            raise
        finally:
            connection.close()
    
    def analyze_query_performance(self) -> Dict[str, any]:
        """Analiza el rendimiento de consultas frecuentes"""
        logger.info("Analizando rendimiento de consultas...")
        
        performance_queries = [
            {
                'name': 'usuarios_activos',
                'query': 'SELECT COUNT(*) FROM usuarios WHERE esta_activo = true',
                'description': 'Consulta de usuarios activos'
            },
            {
                'name': 'pagos_mes_actual',
                'query': '''
                    SELECT COUNT(*) FROM pagos 
                    WHERE DATE_TRUNC('month', fecha_pago) = DATE_TRUNC('month', CURRENT_DATE)
                ''',
                'description': 'Pagos del mes actual'
            },
            {
                'name': 'asistencias_semana',
                'query': '''
                    SELECT COUNT(*) FROM asistencias 
                    WHERE fecha_hora_entrada >= CURRENT_DATE - INTERVAL '7 days'
                ''',
                'description': 'Asistencias de la última semana'
            },
            {
                'name': 'clases_horarios',
                'query': '''
                    SELECT c.nombre, h.dia, h.hora_inicio, COUNT(u.id) as participantes
                    FROM clases c
                    JOIN horarios_clases h ON c.id = h.clase_id
                    LEFT JOIN usuarios_horarios uh ON h.id = uh.horario_id
                    LEFT JOIN usuarios u ON uh.usuario_id = u.id
                    GROUP BY c.nombre, h.dia, h.hora_inicio
                    LIMIT 10
                ''',
                'description': 'Clases con horarios y participantes'
            }
        ]
        
        results = {}
        
        try:
            with self.get_connection() as conn:
                for query_info in performance_queries:
                    start_time = time.time()
                    
                    try:
                        result = conn.execute(text(query_info['query']))
                        execution_time = time.time() - start_time
                        
                        results[query_info['name']] = {
                            'execution_time': execution_time,
                            'description': query_info['description'],
                            'status': 'success'
                        }
                        
                        logger.info(f"Query '{query_info['name']}': {execution_time:.3f}s")
                        
                    except Exception as e:
                        results[query_info['name']] = {
                            'execution_time': None,
                            'description': query_info['description'],
                            'status': 'error',
                            'error': str(e)
                        }
                        logger.error(f"Error en query '{query_info['name']}': {e}")
                        
        except Exception as e:
            logger.error(f"Error al analizar rendimiento: {e}")
            
        return results
    
    def create_performance_indexes(self) -> bool:
        """Crea índices optimizados para mejorar rendimiento"""
        logger.info("Creando índices de rendimiento...")
        
        # Índices estratégicos basados en patrones de consulta comunes
        indexes = [
            # Índices para usuarios
            {
                'name': 'idx_usuarios_activos',
                'table': 'usuarios',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_activos ON usuarios(esta_activo) WHERE esta_activo = true',
                'description': 'Índice para usuarios activos'
            },
            {
                'name': 'idx_usuarios_email_lower',
                'table': 'usuarios',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_email_lower ON usuarios(LOWER(email))',
                'description': 'Índice para búsquedas de email insensibles a mayúsculas'
            },
            {
                'name': 'idx_usuarios_nombre_completo',
                'table': 'usuarios',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_nombre_completo ON usuarios(nombre, apellido)',
                'description': 'Índice compuesto para búsquedas por nombre completo'
            },
            {
                'name': 'idx_usuarios_ultimo_acceso',
                'table': 'usuarios',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_ultimo_acceso ON usuarios(ultimo_acceso DESC) WHERE ultimo_acceso IS NOT NULL',
                'description': 'Índice para último acceso de usuarios'
            },
            
            # Índices para pagos
            {
                'name': 'idx_pagos_usuario_fecha',
                'table': 'pagos',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_usuario_fecha ON pagos(usuario_id, fecha_pago DESC)',
                'description': 'Índice compuesto para pagos por usuario y fecha'
            },
            {
                'name': 'idx_pagos_estado_fecha',
                'table': 'pagos',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_estado_fecha ON pagos(estado, fecha_pago DESC)',
                'description': 'Índice para pagos por estado y fecha'
            },
            {
                'name': 'idx_pagos_vencimiento',
                'table': 'pagos',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_vencimiento ON pagos(fecha_vencimiento) WHERE fecha_vencimiento IS NOT NULL',
                'description': 'Índice para fechas de vencimiento'
            },
            {
                'name': 'idx_pagos_mes_ano',
                'table': 'pagos',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_mes_ano ON pagos(DATE_TRUNC(\'month\', fecha_pago))',
                'description': 'Índice para reportes mensuales de pagos'
            },
            
            # Índices para asistencias
            {
                'name': 'idx_asistencias_usuario_fecha',
                'table': 'asistencias',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asistencias_usuario_fecha ON asistencias(usuario_id, fecha_hora_entrada DESC)',
                'description': 'Índice compuesto para asistencias por usuario y fecha'
            },
            {
                'name': 'idx_asistencias_fecha_entrada',
                'table': 'asistencias',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asistencias_fecha_entrada ON asistencias(DATE(fecha_hora_entrada))',
                'description': 'Índice para asistencias por día'
            },
            {
                'name': 'idx_asistencias_semana',
                'table': 'asistencias',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asistencias_semana ON asistencias(fecha_hora_entrada) WHERE fecha_hora_entrada >= CURRENT_DATE - INTERVAL \'30 days\'',
                'description': 'Índice parcial para asistencias recientes'
            },
            
            # Índices para clases y horarios
            {
                'name': 'idx_horarios_dia_hora',
                'table': 'horarios_clases',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horarios_dia_hora ON horarios_clases(dia, hora_inicio)',
                'description': 'Índice para horarios por día y hora'
            },
            {
                'name': 'idx_horarios_instructor',
                'table': 'horarios_clases',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horarios_instructor ON horarios_clases(instructor_id) WHERE instructor_id IS NOT NULL',
                'description': 'Índice para horarios por instructor'
            },
            {
                'name': 'idx_horarios_capacidad',
                'table': 'horarios_clases',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horarios_capacidad ON horarios_clases(plazas_disponibles) WHERE plazas_disponibles > 0',
                'description': 'Índice para horarios con plazas disponibles'
            },
            
            # Índices para empleados
            {
                'name': 'idx_empleados_estado_depto',
                'table': 'empleados',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_empleados_estado_depto ON empleados(estado, departamento)',
                'description': 'Índice compuesto para empleados por estado y departamento'
            },
            {
                'name': 'idx_empleados_fecha_ingreso',
                'table': 'empleados',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_empleados_fecha_ingreso ON empleados(fecha_ingreso DESC)',
                'description': 'Índice para empleados por fecha de ingreso'
            },
            
            # Índices para rutinas
            {
                'name': 'idx_rutinas_usuario',
                'table': 'rutinas',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rutinas_usuario ON rutinas(usuario_id) WHERE usuario_id IS NOT NULL',
                'description': 'Índice para rutinas por usuario'
            },
            {
                'name': 'idx_rutinas_nivel',
                'table': 'rutinas',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rutinas_nivel ON rutinas(nivel)',
                'description': 'Índice para rutinas por nivel de dificultad'
            },
            
            # Índices para tipos de cuota
            {
                'name': 'idx_tipos_cuota_activos',
                'table': 'tipos_cuota',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tipos_cuota_activos ON tipos_cuota(esta_activo) WHERE esta_activo = true',
                'description': 'Índice para tipos de cuota activos'
            },
            
            # Índices para multimedia
            {
                'name': 'idx_multimedia_tipo_activo',
                'table': 'multimedia',
                'query': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_multimedia_tipo_activo ON multimedia(tipo, esta_activo) WHERE esta_activo = true',
                'description': 'Índice para multimedia activo por tipo'
            }
        ]
        
        success_count = 0
        total_count = len(indexes)
        
        try:
            with self.get_connection() as conn:
                for index in indexes:
                    try:
                        logger.info(f"Creando índice: {index['name']}")
                        start_time = time.time()
                        
                        conn.execute(text(index['query']))
                        conn.commit()
                        
                        execution_time = time.time() - start_time
                        success_count += 1
                        
                        logger.info(f"✓ Índice '{index['name']}' creado en {execution_time:.3f}s")
                        
                    except SQLAlchemyError as e:
                        if "already exists" in str(e).lower():
                            logger.info(f"Índice '{index['name']}' ya existe")
                            success_count += 1
                        else:
                            logger.error(f"Error creando índice '{index['name']}': {e}")
                    except Exception as e:
                        logger.error(f"Error inesperado creando índice '{index['name']}': {e}")
                        
        except Exception as e:
            logger.error(f"Error al conectar con la base de datos: {e}")
            return False
        
        logger.info(f"Proceso completado: {success_count}/{total_count} índices creados/verificados")
        return success_count > 0
    
    def analyze_table_statistics(self) -> Dict[str, any]:
        """Analiza estadísticas de las tablas principales"""
        logger.info("Analizando estadísticas de tablas...")
        
        tables_to_analyze = [
            'usuarios', 'pagos', 'asistencias', 'clases', 
            'horarios_clases', 'rutinas', 'empleados', 'tipos_cuota'
        ]
        
        statistics = {}
        
        try:
            with self.get_connection() as conn:
                for table in tables_to_analyze:
                    try:
                        # Obtener estadísticas básicas
                        count_query = f"SELECT COUNT(*) as total FROM {table}"
                        result = conn.execute(text(count_query)).fetchone()
                        
                        statistics[table] = {
                            'total_rows': result[0] if result else 0,
                            'status': 'success'
                        }
                        
                        # Analizar tabla si tiene muchos registros
                        if statistics[table]['total_rows'] > 1000:
                            analyze_query = f"ANALYZE {table}"
                            conn.execute(text(analyze_query))
                            conn.commit()
                            logger.info(f"Tabla '{table}' analizada para optimización")
                        
                    except Exception as e:
                        statistics[table] = {
                            'total_rows': 0,
                            'status': 'error',
                            'error': str(e)
                        }
                        logger.error(f"Error analizando tabla '{table}': {e}")
                        
        except Exception as e:
            logger.error(f"Error al analizar estadísticas: {e}")
            
        return statistics
    
    def create_maintenance_views(self) -> bool:
        """Crea vistas para facilitar el mantenimiento y reportes"""
        logger.info("Creando vistas de mantenimiento...")
        
        views = [
            {
                'name': 'v_usuarios_resumen',
                'query': '''
                    CREATE OR REPLACE VIEW v_usuarios_resumen AS
                    SELECT 
                        u.id,
                        u.username,
                        u.email,
                        u.nombre || ' ' || u.apellido as nombre_completo,
                        u.esta_activo,
                        u.fecha_registro,
                        COUNT(DISTINCT p.id) as total_pagos,
                        COUNT(DISTINCT a.id) as total_asistencias,
                        MAX(a.fecha_hora_entrada) as ultima_asistencia
                    FROM usuarios u
                    LEFT JOIN pagos p ON u.id = p.usuario_id
                    LEFT JOIN asistencias a ON u.id = a.usuario_id
                    GROUP BY u.id, u.username, u.email, u.nombre, u.apellido, u.esta_activo, u.fecha_registro
                ''',
                'description': 'Vista resumen de usuarios con estadísticas'
            },
            {
                'name': 'v_pagos_mensuales',
                'query': '''
                    CREATE OR REPLACE VIEW v_pagos_mensuales AS
                    SELECT 
                        DATE_TRUNC('month', fecha_pago) as mes,
                        COUNT(*) as total_pagos,
                        SUM(monto_final) as total_ingresos,
                        AVG(monto_final) as promedio_pago,
                        COUNT(DISTINCT usuario_id) as usuarios_pagaron
                    FROM pagos
                    WHERE estado = 'PAGADO'
                    GROUP BY DATE_TRUNC('month', fecha_pago)
                    ORDER BY mes DESC
                ''',
                'description': 'Vista de pagos agrupados por mes'
            },
            {
                'name': 'v_asistencias_diarias',
                'query': '''
                    CREATE OR REPLACE VIEW v_asistencias_diarias AS
                    SELECT 
                        DATE(fecha_hora_entrada) as fecha,
                        COUNT(*) as total_asistencias,
                        COUNT(DISTINCT usuario_id) as usuarios_unicos,
                        EXTRACT(dow FROM fecha_hora_entrada) as dia_semana
                    FROM asistencias
                    GROUP BY DATE(fecha_hora_entrada), EXTRACT(dow FROM fecha_hora_entrada)
                    ORDER BY fecha DESC
                ''',
                'description': 'Vista de asistencias agrupadas por día'
            }
        ]
        
        success_count = 0
        
        try:
            with self.get_connection() as conn:
                for view in views:
                    try:
                        logger.info(f"Creando vista: {view['name']}")
                        conn.execute(text(view['query']))
                        conn.commit()
                        success_count += 1
                        logger.info(f"✓ Vista '{view['name']}' creada")
                        
                    except Exception as e:
                        logger.error(f"Error creando vista '{view['name']}': {e}")
                        
        except Exception as e:
            logger.error(f"Error al crear vistas: {e}")
            return False
        
        logger.info(f"Vistas creadas: {success_count}/{len(views)}")
        return success_count > 0

def main():
    """Función principal del optimizador"""
    logger.info("=== Iniciando optimización de base de datos ===")
    
    try:
        # Crear optimizador
        engine = create_engine(settings.DATABASE_URI)
        optimizer = DatabaseOptimizer(engine)
        
        # Análisis inicial
        logger.info("1. Analizando rendimiento actual...")
        performance_before = optimizer.analyze_query_performance()
        
        # Estadísticas de tablas
        logger.info("2. Analizando estadísticas de tablas...")
        table_stats = optimizer.analyze_table_statistics()
        
        # Crear índices
        logger.info("3. Creando índices de rendimiento...")
        indexes_created = optimizer.create_performance_indexes()
        
        # Crear vistas de mantenimiento
        logger.info("4. Creando vistas de mantenimiento...")
        views_created = optimizer.create_maintenance_views()
        
        # Análisis final
        logger.info("5. Analizando rendimiento después de optimización...")
        performance_after = optimizer.analyze_query_performance()
        
        # Resumen final
        logger.info("\n=== RESUMEN DE OPTIMIZACIÓN ===")
        logger.info(f"Índices creados: {'✓' if indexes_created else '✗'}")
        logger.info(f"Vistas creadas: {'✓' if views_created else '✗'}")
        
        logger.info("\nEstadísticas de tablas:")
        for table, stats in table_stats.items():
            if stats['status'] == 'success':
                logger.info(f"  {table}: {stats['total_rows']:,} registros")
            else:
                logger.info(f"  {table}: Error - {stats.get('error', 'Desconocido')}")
        
        logger.info("\nRendimiento de consultas (antes → después):")
        for query_name in performance_before.keys():
            before = performance_before.get(query_name, {})
            after = performance_after.get(query_name, {})
            
            if before.get('status') == 'success' and after.get('status') == 'success':
                before_time = before.get('execution_time', 0)
                after_time = after.get('execution_time', 0)
                improvement = ((before_time - after_time) / before_time * 100) if before_time > 0 else 0
                
                logger.info(f"  {query_name}: {before_time:.3f}s → {after_time:.3f}s ({improvement:+.1f}%)")
            else:
                logger.info(f"  {query_name}: Error en medición")
        
        logger.info("\n=== Optimización completada ===")
        
    except Exception as e:
        logger.error(f"Error durante la optimización: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 