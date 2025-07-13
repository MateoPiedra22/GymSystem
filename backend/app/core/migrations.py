"""
Sistema de Migraciones de Base de Datos Optimizado
Sistema de Gestión de Gimnasio v6

Este módulo gestiona migraciones de base de datos con versionado
y aplicación segura de optimizaciones.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text, DDL, MetaData, Table, Column, String, Integer, DateTime, Boolean
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Removed circular import - will import engine locally when needed
from app.core.config import settings

logger = logging.getLogger(__name__)

# ===============================
# TABLA DE MIGRACIONES
# ===============================

class MigrationManager:
    """Gestor de migraciones de base de datos"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.metadata = MetaData()
        self.migrations_table = self._create_migrations_table()
        
    def _create_migrations_table(self) -> Table:
        """Crea la tabla de control de migraciones"""
        
        migrations_table = Table(
            'schema_migrations',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('version', String(50), unique=True, nullable=False),
            Column('name', String(255), nullable=False),
            Column('applied_at', DateTime, default=datetime.utcnow),
            Column('execution_time_ms', Integer),
            Column('success', Boolean, default=True),
            Column('error_message', String(1000)),
            extend_existing=True
        )
        
        # Crear tabla si no existe
        try:
            self.metadata.create_all(self.engine, tables=[migrations_table])
            logger.info("Tabla de migraciones inicializada")
        except Exception as e:
            logger.error(f"Error creando tabla de migraciones: {e}")
            
        return migrations_table
    
    def get_applied_migrations(self) -> List[str]:
        """Obtiene lista de migraciones ya aplicadas"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT version FROM schema_migrations WHERE success = true ORDER BY applied_at")
                )
                return [row[0] for row in result]
        except Exception:
            return []
    
    def record_migration(self, version: str, name: str, execution_time_ms: int, 
                        success: bool = True, error_message: Optional[str] = None) -> None:
        """Registra una migración aplicada"""
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO schema_migrations (version, name, applied_at, execution_time_ms, success, error_message)
                        VALUES (:version, :name, :applied_at, :execution_time_ms, :success, :error_message)
                    """),
                    {
                        'version': version,
                        'name': name,
                        'applied_at': datetime.utcnow(),
                        'execution_time_ms': execution_time_ms,
                        'success': success,
                        'error_message': error_message
                    }
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error registrando migración: {e}")

# ===============================
# DEFINICIÓN DE MIGRACIONES
# ===============================

class Migration:
    """Clase base para migraciones"""
    
    def __init__(self, version: str, name: str):
        self.version = version
        self.name = name
        
    def up(self, engine: Engine) -> None:
        """Aplicar migración"""
        raise NotImplementedError
        
    def down(self, engine: Engine) -> None:
        """Revertir migración (opcional)"""
        pass

class Migration_001_BasicIndexes(Migration):
    """Migración 001: Índices básicos de rendimiento"""
    
    def __init__(self):
        super().__init__("001", "Basic Performance Indexes")
    
    def up(self, engine: Engine) -> None:
        """Crear índices básicos de rendimiento"""
        
        indexes = [
            # Índices esenciales para consultas frecuentes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_email_activo ON usuarios(email, esta_activo);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_username ON usuarios(username);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asistencias_usuario_fecha ON asistencias(usuario_id, fecha_hora_entrada);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_usuario_estado ON pagos(usuario_id, estado);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_fecha_pago ON pagos(fecha_pago);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horarios_dia_activo ON horarios_clases(dia, esta_activo);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_empleados_estado ON empleados(estado);",
        ]
        
        with engine.connect() as conn:
            for idx_sql in indexes:
                try:
                    conn.execute(text(idx_sql))
                    logger.info(f"Índice creado: {idx_sql[:50]}...")
                except Exception as e:
                    logger.warning(f"Error creando índice: {e}")
            conn.commit()

class Migration_002_DatabaseFunctions(Migration):
    """Migración 002: Funciones de base de datos"""
    
    def __init__(self):
        super().__init__("002", "Database Functions")
    
    def up(self, engine: Engine) -> None:
        """Crear funciones de base de datos"""
        
        functions = [
            # Función para calcular edad
            """
            CREATE OR REPLACE FUNCTION calcular_edad(fecha_nacimiento DATE)
            RETURNS INTEGER AS $$
            BEGIN
                IF fecha_nacimiento IS NULL THEN
                    RETURN NULL;
                END IF;
                RETURN EXTRACT(YEAR FROM AGE(fecha_nacimiento));
            END;
            $$ LANGUAGE plpgsql IMMUTABLE;
            """,
            
            # Función para calcular IMC
            """
            CREATE OR REPLACE FUNCTION calcular_imc(peso_gramos INTEGER, altura_cm INTEGER)
            RETURNS DECIMAL(5,2) AS $$
            BEGIN
                IF peso_gramos IS NULL OR altura_cm IS NULL OR altura_cm = 0 THEN
                    RETURN NULL;
                END IF;
                RETURN ROUND((peso_gramos / 1000.0) / POWER(altura_cm / 100.0, 2), 2);
            END;
            $$ LANGUAGE plpgsql IMMUTABLE;
            """,
            
            # Función para generar números de recibo
            """
            CREATE OR REPLACE FUNCTION generar_numero_recibo()
            RETURNS TEXT AS $$
            DECLARE
                nuevo_numero TEXT;
                contador INTEGER;
            BEGIN
                SELECT COALESCE(MAX(CAST(SUBSTRING(numero_recibo FROM '[0-9]+') AS INTEGER)), 0) + 1
                INTO contador
                FROM pagos
                WHERE numero_recibo ~ '^REC[0-9]+$';
                
                nuevo_numero := 'REC' || LPAD(contador::TEXT, 8, '0');
                
                RETURN nuevo_numero;
            END;
            $$ LANGUAGE plpgsql;
            """,
        ]
        
        with engine.connect() as conn:
            for func_sql in functions:
                try:
                    conn.execute(text(func_sql))
                    logger.info("Función de BD creada")
                except Exception as e:
                    logger.warning(f"Error creando función: {e}")
            conn.commit()

class Migration_003_Triggers(Migration):
    """Migración 003: Triggers automáticos"""
    
    def __init__(self):
        super().__init__("003", "Automated Triggers")
    
    def up(self, engine: Engine) -> None:
        """Crear triggers automáticos"""
        
        triggers = [
            # Trigger para actualizar última modificación
            """
            CREATE OR REPLACE FUNCTION actualizar_ultima_modificacion()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.ultima_modificacion = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """,
            
            # Trigger para generar número de recibo
            """
            CREATE OR REPLACE FUNCTION trigger_generar_numero_recibo()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.numero_recibo IS NULL OR NEW.numero_recibo = '' THEN
                    NEW.numero_recibo := generar_numero_recibo();
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """,
        ]
        
        # Aplicar triggers a tablas
        trigger_applications = [
            "DROP TRIGGER IF EXISTS trg_usuarios_ultima_modificacion ON usuarios;",
            """CREATE TRIGGER trg_usuarios_ultima_modificacion
               BEFORE UPDATE ON usuarios FOR EACH ROW
               EXECUTE FUNCTION actualizar_ultima_modificacion();""",
               
            "DROP TRIGGER IF EXISTS trg_asistencias_ultima_modificacion ON asistencias;",
            """CREATE TRIGGER trg_asistencias_ultima_modificacion
               BEFORE UPDATE ON asistencias FOR EACH ROW
               EXECUTE FUNCTION actualizar_ultima_modificacion();""",
               
            "DROP TRIGGER IF EXISTS trg_pagos_ultima_modificacion ON pagos;",
            """CREATE TRIGGER trg_pagos_ultima_modificacion
               BEFORE UPDATE ON pagos FOR EACH ROW
               EXECUTE FUNCTION actualizar_ultima_modificacion();""",
               
            "DROP TRIGGER IF EXISTS trg_pagos_numero_recibo ON pagos;",
            """CREATE TRIGGER trg_pagos_numero_recibo
               BEFORE INSERT ON pagos FOR EACH ROW
               EXECUTE FUNCTION trigger_generar_numero_recibo();""",
        ]
        
        with engine.connect() as conn:
            # Crear funciones de trigger
            for trigger_sql in triggers:
                try:
                    conn.execute(text(trigger_sql))
                    logger.info("Función de trigger creada")
                except Exception as e:
                    logger.warning(f"Error creando función de trigger: {e}")
            
            # Aplicar triggers
            for app_sql in trigger_applications:
                try:
                    conn.execute(text(app_sql))
                    logger.info("Trigger aplicado")
                except Exception as e:
                    logger.warning(f"Error aplicando trigger: {e}")
            
            conn.commit()

class Migration_004_OptimizedViews(Migration):
    """Migración 004: Vistas optimizadas"""
    
    def __init__(self):
        super().__init__("004", "Optimized Views")
    
    def up(self, engine: Engine) -> None:
        """Crear vistas optimizadas"""
        
        views = [
            # Vista para estadísticas de usuarios
            """
            CREATE OR REPLACE VIEW vista_estadisticas_usuarios AS
            SELECT 
                u.id,
                u.nombre,
                u.apellido,
                u.email,
                u.fecha_registro,
                u.ultimo_acceso,
                CASE 
                    WHEN u.fecha_nacimiento IS NOT NULL 
                    THEN calcular_edad(u.fecha_nacimiento)
                    ELSE NULL 
                END as edad,
                CASE 
                    WHEN u.peso_inicial IS NOT NULL AND u.altura IS NOT NULL 
                    THEN calcular_imc(u.peso_inicial, u.altura)
                    ELSE NULL 
                END as imc,
                COUNT(DISTINCT a.id) as total_asistencias,
                COUNT(DISTINCT DATE(a.fecha_hora_entrada)) as dias_asistencia,
                COALESCE(SUM(p.monto_final), 0) as total_pagado,
                COUNT(DISTINCT p.id) as total_pagos
            FROM usuarios u
            LEFT JOIN asistencias a ON u.id = a.usuario_id
            LEFT JOIN pagos p ON u.id = p.usuario_id AND p.estado = 'PAGADO'
            WHERE u.esta_activo = true
            GROUP BY u.id, u.nombre, u.apellido, u.email, u.fecha_registro, 
                     u.ultimo_acceso, u.fecha_nacimiento, u.peso_inicial, u.altura;
            """,
            
            # Vista para asistencias diarias
            """
            CREATE OR REPLACE VIEW vista_asistencias_diarias AS
            SELECT 
                DATE(a.fecha_hora_entrada) as fecha,
                COUNT(*) as total_asistencias,
                COUNT(DISTINCT a.usuario_id) as usuarios_unicos,
                CASE 
                    WHEN COUNT(CASE WHEN a.fecha_hora_salida IS NOT NULL THEN 1 END) > 0
                    THEN AVG(EXTRACT(EPOCH FROM (a.fecha_hora_salida - a.fecha_hora_entrada))/3600) 
                    ELSE NULL 
                END as promedio_horas
            FROM asistencias a
            WHERE a.fecha_hora_entrada >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY DATE(a.fecha_hora_entrada)
            ORDER BY fecha DESC;
            """,
            
            # Vista para reportes financieros
            """
            CREATE OR REPLACE VIEW vista_reportes_financieros AS
            SELECT 
                DATE_TRUNC('month', p.fecha_pago) as mes,
                p.concepto,
                p.metodo_pago,
                COUNT(*) as total_transacciones,
                SUM(p.monto_final) as total_ingresos,
                AVG(p.monto_final) as promedio_transaccion,
                COUNT(DISTINCT p.usuario_id) as usuarios_unicos
            FROM pagos p
            WHERE p.estado = 'PAGADO'
            GROUP BY DATE_TRUNC('month', p.fecha_pago), p.concepto, p.metodo_pago
            ORDER BY mes DESC;
            """,
        ]
        
        with engine.connect() as conn:
            for view_sql in views:
                try:
                    conn.execute(text(view_sql))
                    logger.info("Vista optimizada creada")
                except Exception as e:
                    logger.warning(f"Error creando vista: {e}")
            conn.commit()

class Migration_005_AdvancedIndexes(Migration):
    """Migración 005: Índices avanzados y de texto"""
    
    def __init__(self):
        super().__init__("005", "Advanced Indexes")
    
    def up(self, engine: Engine) -> None:
        """Crear índices avanzados"""
        
        # Habilitar extensiones primero
        extensions = [
            "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            "CREATE EXTENSION IF NOT EXISTS btree_gin;",
        ]
        
        # Índices avanzados
        advanced_indexes = [
            # Índices parciales para registros activos
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_activos_partial ON usuarios(email, username) WHERE esta_activo = true;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clases_activas_partial ON clases(nombre, nivel) WHERE esta_activa = true;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horarios_activos_partial ON horarios_clases(dia, hora_inicio) WHERE esta_activo = true;",
            
            # Índices compuestos para reportes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asistencias_reporte ON asistencias(usuario_id, fecha_hora_entrada, fecha_hora_salida);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_reporte_mes ON pagos(fecha_pago, monto_final, estado);",
            
            # Índices para sincronización
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_sync ON usuarios(sync_id, ultima_modificacion);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asistencias_sync ON asistencias(sync_id, ultima_modificacion);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_sync ON pagos(sync_id, ultima_modificacion);",
        ]
        
        with engine.connect() as conn:
            # Crear extensiones
            for ext_sql in extensions:
                try:
                    conn.execute(text(ext_sql))
                    logger.info("Extensión habilitada")
                except Exception as e:
                    logger.warning(f"Error habilitando extensión: {e}")
            
            # Crear índices avanzados
            for idx_sql in advanced_indexes:
                try:
                    conn.execute(text(idx_sql))
                    logger.info("Índice avanzado creado")
                except Exception as e:
                    logger.warning(f"Error creando índice avanzado: {e}")
            
            conn.commit()

# ===============================
# LISTA DE MIGRACIONES
# ===============================

MIGRATIONS = [
    Migration_001_BasicIndexes(),
    Migration_002_DatabaseFunctions(),
    Migration_003_Triggers(),
    Migration_004_OptimizedViews(),
    Migration_005_AdvancedIndexes(),
]

# ===============================
# FUNCIONES PRINCIPALES
# ===============================

def run_migrations(engine: Engine) -> None:
    """Ejecuta todas las migraciones pendientes"""
    
    logger.info("Iniciando proceso de migraciones...")
    
    manager = MigrationManager(engine)
    applied_migrations = manager.get_applied_migrations()
    
    for migration in MIGRATIONS:
        if migration.version not in applied_migrations:
            logger.info(f"Aplicando migración {migration.version}: {migration.name}")
            
            start_time = datetime.utcnow()
            success = True
            error_message = None
            
            try:
                migration.up(engine)
                logger.info(f"Migración {migration.version} aplicada exitosamente")
                
            except Exception as e:
                success = False
                error_message = str(e)
                logger.error(f"Error aplicando migración {migration.version}: {e}")
            
            finally:
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                manager.record_migration(
                    migration.version, 
                    migration.name, 
                    execution_time, 
                    success, 
                    error_message
                )
        else:
            logger.info(f"Migración {migration.version} ya aplicada")
    
    logger.info("Proceso de migraciones completado")

def rollback_migration(engine: Engine, version: str) -> None:
    """Revierte una migración específica (si implementa down())"""
    
    logger.info(f"Revirtiendo migración {version}...")
    
    migration = next((m for m in MIGRATIONS if m.version == version), None)
    if migration and hasattr(migration, 'down'):
        try:
            migration.down(engine)
            
            # Marcar como revertida en la tabla
            with engine.connect() as conn:
                conn.execute(
                    text("DELETE FROM schema_migrations WHERE version = :version"),
                    {'version': version}
                )
                conn.commit()
                
            logger.info(f"Migración {version} revertida exitosamente")
            
        except Exception as e:
            logger.error(f"Error revirtiendo migración {version}: {e}")
    else:
        logger.warning(f"Migración {version} no encontrada o no implementa rollback")

def get_migration_status(engine: Engine) -> Dict[str, Any]:
    """Obtiene el estado de todas las migraciones"""
    
    manager = MigrationManager(engine)
    applied_migrations = manager.get_applied_migrations()
    
    status = {
        'total_migrations': len(MIGRATIONS),
        'applied_count': len(applied_migrations),
        'pending_count': len(MIGRATIONS) - len(applied_migrations),
        'migrations': []
    }
    
    for migration in MIGRATIONS:
        migration_status = {
            'version': migration.version,
            'name': migration.name,
            'applied': migration.version in applied_migrations
        }
        status['migrations'].append(migration_status)
    
    return status

# ===============================
# FUNCIONES DE MANTENIMIENTO
# ===============================

def analyze_database_performance(engine: Engine) -> Dict[str, Any]:
    """Analiza el rendimiento de la base de datos"""
    
    performance_data = {}
    
    try:
        with engine.connect() as conn:
            # Estadísticas de tablas
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows,
                    last_vacuum,
                    last_analyze
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC;
            """))
            
            performance_data['table_stats'] = [dict(row) for row in result]
            
            # Uso de índices
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch,
                    CASE 
                        WHEN idx_tup_read > 0 
                        THEN round((idx_tup_fetch::numeric / idx_tup_read) * 100, 2)
                        ELSE 0 
                    END as efficiency_pct
                FROM pg_stat_user_indexes
                WHERE idx_tup_read > 0
                ORDER BY idx_tup_read DESC
                LIMIT 20;
            """))
            
            performance_data['index_usage'] = [dict(row) for row in result]
            
            # Queries más lentos (si pg_stat_statements está habilitado)
            try:
                result = conn.execute(text("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements
                    ORDER BY mean_time DESC
                    LIMIT 10;
                """))
                
                performance_data['slow_queries'] = [dict(row) for row in result]
            except:
                performance_data['slow_queries'] = []
                
    except Exception as e:
        logger.error(f"Error analizando rendimiento: {e}")
        performance_data['error'] = str(e)
    
    return performance_data

def vacuum_analyze_all(engine: Engine) -> None:
    """Ejecuta VACUUM ANALYZE en todas las tablas principales"""
    
    tables = ['usuarios', 'asistencias', 'pagos', 'clases', 'horarios_clases', 'empleados']
    
    logger.info("Iniciando mantenimiento de base de datos...")
    
    with engine.connect() as conn:
        for table in tables:
            try:
                conn.execute(text(f"VACUUM ANALYZE {table};"))
                logger.info(f"VACUUM ANALYZE completado para {table}")
            except Exception as e:
                logger.warning(f"Error en VACUUM ANALYZE para {table}: {e}")
        
        conn.commit()
    
    logger.info("Mantenimiento de base de datos completado")

# ===============================
# INICIALIZACIÓN AUTOMÁTICA
# ===============================

async def initialize_database_optimizations():
    """Inicializa optimizaciones de base de datos al arrancar la aplicación"""
    
    try:
        # Ejecutar migraciones
        run_migrations(engine)
        
        # Ejecutar mantenimiento básico
        vacuum_analyze_all(engine)
        
        logger.info("Optimizaciones de base de datos inicializadas")
        
    except Exception as e:
        logger.error(f"Error inicializando optimizaciones de BD: {e}") 