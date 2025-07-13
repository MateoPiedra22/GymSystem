"""
Optimizaciones Avanzadas de Base de Datos
Sistema de Gestión de Gimnasio v6

Este módulo contiene optimizaciones específicas para mejorar el rendimiento
y escalabilidad de la base de datos PostgreSQL.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import Index, DDL, event, text, MetaData, Table, Column, String, Integer, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from app.core.database import Base, get_db_session
from app.core.config import settings

logger = logging.getLogger(__name__)

# ===============================
# ÍNDICES OPTIMIZADOS ESPECÍFICOS
# ===============================

class DatabaseOptimizer:
    """Clase para gestionar optimizaciones de base de datos"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.metadata = MetaData()
        
    def create_performance_indexes(self) -> None:
        """Crea índices optimizados para consultas frecuentes"""
        
        indexes = [
            # === ÍNDICES PARA USUARIOS ===
            # Búsquedas frecuentes por email, username y estado
            Index('idx_usuarios_email_activo', 'usuarios.email', 'usuarios.esta_activo'),
            Index('idx_usuarios_username_activo', 'usuarios.username', 'usuarios.esta_activo'),
            Index('idx_usuarios_fecha_registro', 'usuarios.fecha_registro'),
            Index('idx_usuarios_ultimo_acceso', 'usuarios.ultimo_acceso'),
            
            # Búsquedas por datos personales
            Index('idx_usuarios_nombre_apellido', 'usuarios.nombre', 'usuarios.apellido'),
            Index('idx_usuarios_telefono', 'usuarios.telefono'),
            Index('idx_usuarios_sync_id', 'usuarios.sync_id'),
            
            # === ÍNDICES PARA ASISTENCIAS ===
            # Consultas de asistencias por usuario y fecha
            Index('idx_asistencias_usuario_fecha', 'asistencias.usuario_id', 'asistencias.fecha_hora_entrada'),
            Index('idx_asistencias_clase_fecha', 'asistencias.clase_id', 'asistencias.fecha_hora_entrada'),
            Index('idx_asistencias_fecha_entrada', 'asistencias.fecha_hora_entrada'),
            Index('idx_asistencias_fecha_salida', 'asistencias.fecha_hora_salida'),
            
            # Índice compuesto para reportes de asistencias
            Index('idx_asistencias_reporte', 'asistencias.usuario_id', 'asistencias.fecha_hora_entrada', 'asistencias.fecha_hora_salida'),
            
            # === ÍNDICES PARA PAGOS ===
            # Consultas de pagos por usuario y estado
            Index('idx_pagos_usuario_estado', 'pagos.usuario_id', 'pagos.estado'),
            Index('idx_pagos_fecha_estado', 'pagos.fecha_pago', 'pagos.estado'),
            Index('idx_pagos_numero_recibo', 'pagos.numero_recibo'),
            Index('idx_pagos_fecha_vencimiento', 'pagos.fecha_vencimiento'),
            Index('idx_pagos_metodo_pago', 'pagos.metodo_pago'),
            
            # Índices para reportes financieros
            Index('idx_pagos_reporte_mes', 'pagos.fecha_pago', 'pagos.monto_final', 'pagos.estado'),
            Index('idx_pagos_concepto_fecha', 'pagos.concepto', 'pagos.fecha_pago'),
            
            # === ÍNDICES PARA CLASES ===
            # Búsquedas de clases por estado y nivel
            Index('idx_clases_activa_nivel', 'clases.esta_activa', 'clases.nivel'),
            Index('idx_clases_nombre_activa', 'clases.nombre', 'clases.esta_activa'),
            Index('idx_clases_duracion', 'clases.duracion_minutos'),
            
            # === ÍNDICES PARA HORARIOS DE CLASES ===
            # Consultas de horarios por día y estado
            Index('idx_horarios_dia_activo', 'horarios_clases.dia', 'horarios_clases.esta_activo'),
            Index('idx_horarios_clase_dia', 'horarios_clases.clase_id', 'horarios_clases.dia'),
            Index('idx_horarios_instructor', 'horarios_clases.instructor_id'),
            Index('idx_horarios_hora_inicio', 'horarios_clases.hora_inicio'),
            
            # Índice compuesto para programación de clases
            Index('idx_horarios_programacion', 'horarios_clases.dia', 'horarios_clases.hora_inicio', 'horarios_clases.esta_activo'),
            
            # === ÍNDICES PARA EMPLEADOS ===
            # Búsquedas de empleados por estado y departamento
            Index('idx_empleados_estado_dpto', 'empleados.estado', 'empleados.departamento'),
            Index('idx_empleados_numero', 'empleados.numero_empleado'),
            Index('idx_empleados_email', 'empleados.email'),
            Index('idx_empleados_dni', 'empleados.dni'),
            Index('idx_empleados_cargo', 'empleados.cargo'),
            Index('idx_empleados_fecha_ingreso', 'empleados.fecha_ingreso'),
            
            # === ÍNDICES PARA NÓMINAS ===
            # Consultas de nóminas por empleado y período
            Index('idx_nominas_empleado_periodo', 'nominas.empleado_id', 'nominas.anio', 'nominas.mes'),
            Index('idx_nominas_fecha_pago', 'nominas.fecha_pago'),
            Index('idx_nominas_estado', 'nominas.estado'),
            
            # === ÍNDICES PARA TIPOS DE CUOTA ===
            # Búsquedas de tipos de cuota por estado y visibilidad
            Index('idx_tipos_cuota_activo_visible', 'tipos_cuota.activo', 'tipos_cuota.visible_web'),
            Index('idx_tipos_cuota_codigo', 'tipos_cuota.codigo'),
            Index('idx_tipos_cuota_precio', 'tipos_cuota.precio'),
            Index('idx_tipos_cuota_duracion', 'tipos_cuota.duracion_dias'),
            
            # === ÍNDICES PARA SINCRONIZACIÓN ===
            # Optimización para sincronización P2P
            Index('idx_usuarios_sync_modificacion', 'usuarios.sync_id', 'usuarios.ultima_modificacion'),
            Index('idx_asistencias_sync_modificacion', 'asistencias.sync_id', 'asistencias.ultima_modificacion'),
            Index('idx_pagos_sync_modificacion', 'pagos.sync_id', 'pagos.ultima_modificacion'),
            Index('idx_clases_sync_modificacion', 'clases.sync_id', 'clases.ultima_modificacion'),
            Index('idx_horarios_sync_modificacion', 'horarios_clases.sync_id', 'horarios_clases.ultima_modificacion'),
            Index('idx_empleados_sync_modificacion', 'empleados.sync_id', 'empleados.ultima_modificacion'),
            
            # === ÍNDICES PARA REPORTES Y ANALYTICS ===
            # Optimización para KPIs y dashboard
            Index('idx_asistencias_analytics', 'asistencias.fecha_hora_entrada', 'asistencias.usuario_id', 'asistencias.clase_id'),
            Index('idx_pagos_analytics', 'pagos.fecha_pago', 'pagos.concepto', 'pagos.monto_final', 'pagos.estado'),
            Index('idx_usuarios_analytics', 'usuarios.fecha_registro', 'usuarios.esta_activo', 'usuarios.ultimo_acceso'),
            
            # === ÍNDICES PARCIALES PARA OPTIMIZACIÓN ===
            # Solo indexar registros activos para mejor rendimiento
            Index('idx_usuarios_activos_partial', 'usuarios.email', 'usuarios.username', 
                  postgresql_where=text('esta_activo = true')),
            Index('idx_clases_activas_partial', 'clases.nombre', 'clases.nivel',
                  postgresql_where=text('esta_activa = true')),
            Index('idx_horarios_activos_partial', 'horarios_clases.dia', 'horarios_clases.hora_inicio',
                  postgresql_where=text('esta_activo = true')),
            Index('idx_empleados_activos_partial', 'empleados.departamento', 'empleados.cargo',
                  postgresql_where=text("estado = 'ACTIVO'")),
            
            # === ÍNDICES PARA BÚSQUEDAS DE TEXTO ===
            # Búsquedas por nombre y descripción (GIN para mejor rendimiento)
            Index('idx_usuarios_nombre_gin', 'usuarios.nombre', 'usuarios.apellido', 
                  postgresql_using='gin', postgresql_ops={'nombre': 'gin_trgm_ops', 'apellido': 'gin_trgm_ops'}),
            Index('idx_clases_nombre_gin', 'clases.nombre', 'clases.descripcion',
                  postgresql_using='gin', postgresql_ops={'nombre': 'gin_trgm_ops', 'descripcion': 'gin_trgm_ops'}),
        ]
        
        # Crear índices
        for index in indexes:
            try:
                index.create(self.engine, checkfirst=True)
                logger.info(f"Índice creado: {index.name}")
            except Exception as e:
                logger.warning(f"Error creando índice {index.name}: {e}")
    
    def create_database_functions(self) -> None:
        """Crea funciones de base de datos para optimizar consultas comunes"""
        
        functions = [
            # === FUNCIÓN PARA CALCULAR EDAD ===
            DDL("""
            CREATE OR REPLACE FUNCTION calcular_edad(fecha_nacimiento DATE)
            RETURNS INTEGER AS $$
            BEGIN
                RETURN EXTRACT(YEAR FROM AGE(fecha_nacimiento));
            END;
            $$ LANGUAGE plpgsql IMMUTABLE;
            """),
            
            # === FUNCIÓN PARA CALCULAR IMC ===
            DDL("""
            CREATE OR REPLACE FUNCTION calcular_imc(peso_gramos INTEGER, altura_cm INTEGER)
            RETURNS DECIMAL(5,2) AS $$
            BEGIN
                IF peso_gramos IS NULL OR altura_cm IS NULL OR altura_cm = 0 THEN
                    RETURN NULL;
                END IF;
                RETURN ROUND((peso_gramos / 1000.0) / POWER(altura_cm / 100.0, 2), 2);
            END;
            $$ LANGUAGE plpgsql IMMUTABLE;
            """),
            
            # === FUNCIÓN PARA GENERAR NÚMEROS DE RECIBO ===
            DDL("""
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
            """),
            
            # === FUNCIÓN PARA CALCULAR DÍAS DE MORA ===
            DDL("""
            CREATE OR REPLACE FUNCTION calcular_dias_mora(fecha_vencimiento DATE)
            RETURNS INTEGER AS $$
            BEGIN
                IF fecha_vencimiento IS NULL THEN
                    RETURN 0;
                END IF;
                
                RETURN GREATEST(0, EXTRACT(DAY FROM (CURRENT_DATE - fecha_vencimiento))::INTEGER);
            END;
            $$ LANGUAGE plpgsql IMMUTABLE;
            """),
            
            # === FUNCIÓN PARA ESTADÍSTICAS DE ASISTENCIAS ===
            DDL("""
            CREATE OR REPLACE FUNCTION estadisticas_asistencias(
                fecha_inicio DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
                fecha_fin DATE DEFAULT CURRENT_DATE
            )
            RETURNS TABLE(
                fecha DATE,
                total_asistencias BIGINT,
                usuarios_unicos BIGINT,
                promedio_permanencia INTERVAL
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    DATE(a.fecha_hora_entrada) as fecha,
                    COUNT(*)::BIGINT as total_asistencias,
                    COUNT(DISTINCT a.usuario_id)::BIGINT as usuarios_unicos,
                    AVG(a.fecha_hora_salida - a.fecha_hora_entrada) as promedio_permanencia
                FROM asistencias a
                WHERE DATE(a.fecha_hora_entrada) BETWEEN fecha_inicio AND fecha_fin
                    AND a.fecha_hora_salida IS NOT NULL
                GROUP BY DATE(a.fecha_hora_entrada)
                ORDER BY fecha;
            END;
            $$ LANGUAGE plpgsql;
            """),
            
            # === FUNCIÓN PARA ACTUALIZAR PLAZAS DISPONIBLES ===
            DDL("""
            CREATE OR REPLACE FUNCTION actualizar_plazas_disponibles(horario_clase_id TEXT)
            RETURNS VOID AS $$
            BEGIN
                UPDATE horarios_clases 
                SET plazas_disponibles = capacidad_maxima - (
                    SELECT COUNT(*)
                    FROM inscripcion_horario
                    WHERE horario_id = horario_clase_id
                )
                WHERE id = horario_clase_id;
            END;
            $$ LANGUAGE plpgsql;
            """),
        ]
        
        # Ejecutar funciones
        for func in functions:
            try:
                func.execute(self.engine)
                logger.info("Función de BD creada exitosamente")
            except Exception as e:
                logger.warning(f"Error creando función de BD: {e}")
    
    def create_triggers(self) -> None:
        """Crea triggers para mantener consistencia de datos"""
        
        triggers = [
            # === TRIGGER PARA ACTUALIZAR ÚLTIMA MODIFICACIÓN ===
            DDL("""
            CREATE OR REPLACE FUNCTION actualizar_ultima_modificacion()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.ultima_modificacion = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """),
            
            # === TRIGGER PARA GENERAR NÚMERO DE RECIBO ===
            DDL("""
            CREATE OR REPLACE FUNCTION trigger_generar_numero_recibo()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.numero_recibo IS NULL OR NEW.numero_recibo = '' THEN
                    NEW.numero_recibo := generar_numero_recibo();
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """),
            
            # === TRIGGER PARA ACTUALIZAR PLAZAS DISPONIBLES ===
            DDL("""
            CREATE OR REPLACE FUNCTION trigger_actualizar_plazas()
            RETURNS TRIGGER AS $$
            BEGIN
                IF TG_OP = 'INSERT' THEN
                    PERFORM actualizar_plazas_disponibles(NEW.horario_id);
                ELSIF TG_OP = 'DELETE' THEN
                    PERFORM actualizar_plazas_disponibles(OLD.horario_id);
                END IF;
                RETURN COALESCE(NEW, OLD);
            END;
            $$ LANGUAGE plpgsql;
            """),
            
            # === TRIGGER PARA VALIDAR CAPACIDAD MÁXIMA ===
            DDL("""
            CREATE OR REPLACE FUNCTION validar_capacidad_maxima()
            RETURNS TRIGGER AS $$
            DECLARE
                inscripciones_actuales INTEGER;
                capacidad_maxima INTEGER;
            BEGIN
                SELECT COUNT(*), hc.capacidad_maxima
                INTO inscripciones_actuales, capacidad_maxima
                FROM inscripcion_horario ih
                JOIN horarios_clases hc ON hc.id = ih.horario_id
                WHERE ih.horario_id = NEW.horario_id
                GROUP BY hc.capacidad_maxima;
                
                IF inscripciones_actuales >= capacidad_maxima THEN
                    RAISE EXCEPTION 'La clase ha alcanzado su capacidad máxima de % participantes', capacidad_maxima;
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """),
        ]
        
        # Ejecutar triggers
        for trigger in triggers:
            try:
                trigger.execute(self.engine)
                logger.info("Trigger creado exitosamente")
            except Exception as e:
                logger.warning(f"Error creando trigger: {e}")
    
    def apply_triggers_to_tables(self) -> None:
        """Aplica triggers a las tablas correspondientes"""
        
        # Lista de tablas que necesitan trigger de última modificación
        tables_with_timestamp = [
            'usuarios', 'asistencias', 'pagos', 'clases', 'horarios_clases',
            'empleados', 'nominas', 'tipos_cuota', 'detalles_pago'
        ]
        
        trigger_applications = []
        
        # Aplicar trigger de última modificación
        for table in tables_with_timestamp:
            trigger_applications.append(
                DDL(f"""
                DROP TRIGGER IF EXISTS trg_{table}_ultima_modificacion ON {table};
                CREATE TRIGGER trg_{table}_ultima_modificacion
                    BEFORE UPDATE ON {table}
                    FOR EACH ROW
                    EXECUTE FUNCTION actualizar_ultima_modificacion();
                """)
            )
        
        # Aplicar trigger específicos
        trigger_applications.extend([
            # Trigger para número de recibo
            DDL("""
            DROP TRIGGER IF EXISTS trg_pagos_numero_recibo ON pagos;
            CREATE TRIGGER trg_pagos_numero_recibo
                BEFORE INSERT ON pagos
                FOR EACH ROW
                EXECUTE FUNCTION trigger_generar_numero_recibo();
            """),
            
            # Trigger para actualizar plazas disponibles
            DDL("""
            DROP TRIGGER IF EXISTS trg_inscripcion_plazas ON inscripcion_horario;
            CREATE TRIGGER trg_inscripcion_plazas
                AFTER INSERT OR DELETE ON inscripcion_horario
                FOR EACH ROW
                EXECUTE FUNCTION trigger_actualizar_plazas();
            """),
            
            # Trigger para validar capacidad máxima
            DDL("""
            DROP TRIGGER IF EXISTS trg_validar_capacidad ON inscripcion_horario;
            CREATE TRIGGER trg_validar_capacidad
                BEFORE INSERT ON inscripcion_horario
                FOR EACH ROW
                EXECUTE FUNCTION validar_capacidad_maxima();
            """),
        ])
        
        # Ejecutar aplicaciones de triggers
        for trigger_app in trigger_applications:
            try:
                trigger_app.execute(self.engine)
                logger.info("Trigger aplicado exitosamente")
            except Exception as e:
                logger.warning(f"Error aplicando trigger: {e}")
    
    def create_views(self) -> None:
        """Crea vistas optimizadas para consultas comunes"""
        
        views = [
            # === VISTA PARA ESTADÍSTICAS DE USUARIOS ===
            DDL("""
            CREATE OR REPLACE VIEW vista_estadisticas_usuarios AS
            SELECT 
                u.id,
                u.nombre,
                u.apellido,
                u.email,
                u.fecha_registro,
                u.ultimo_acceso,
                calcular_edad(u.fecha_nacimiento) as edad,
                calcular_imc(u.peso_inicial, u.altura) as imc,
                COUNT(DISTINCT a.id) as total_asistencias,
                COUNT(DISTINCT DATE(a.fecha_hora_entrada)) as dias_asistencia,
                SUM(p.monto_final) as total_pagado,
                COUNT(DISTINCT p.id) as total_pagos
            FROM usuarios u
            LEFT JOIN asistencias a ON u.id = a.usuario_id
            LEFT JOIN pagos p ON u.id = p.usuario_id AND p.estado = 'PAGADO'
            WHERE u.esta_activo = true
            GROUP BY u.id, u.nombre, u.apellido, u.email, u.fecha_registro, u.ultimo_acceso, u.fecha_nacimiento, u.peso_inicial, u.altura;
            """),
            
            # === VISTA PARA HORARIOS DETALLADOS ===
            DDL("""
            CREATE OR REPLACE VIEW vista_horarios_detallados AS
            SELECT 
                hc.id,
                hc.dia,
                hc.hora_inicio,
                hc.salon,
                hc.capacidad_maxima,
                hc.plazas_disponibles,
                c.nombre as clase_nombre,
                c.descripcion as clase_descripcion,
                c.duracion_minutos,
                c.nivel,
                e.nombre as instructor_nombre,
                e.apellido as instructor_apellido,
                COUNT(ih.usuario_id) as inscritos_actuales
            FROM horarios_clases hc
            JOIN clases c ON hc.clase_id = c.id
            JOIN empleados e ON hc.instructor_id = e.id
            LEFT JOIN inscripcion_horario ih ON hc.id = ih.horario_id
            WHERE hc.esta_activo = true AND c.esta_activa = true
            GROUP BY hc.id, hc.dia, hc.hora_inicio, hc.salon, hc.capacidad_maxima, hc.plazas_disponibles,
                     c.nombre, c.descripcion, c.duracion_minutos, c.nivel, e.nombre, e.apellido;
            """),
            
            # === VISTA PARA REPORTES FINANCIEROS ===
            DDL("""
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
            GROUP BY DATE_TRUNC('month', p.fecha_pago), p.concepto, p.metodo_pago;
            """),
            
            # === VISTA PARA ASISTENCIAS DIARIAS ===
            DDL("""
            CREATE OR REPLACE VIEW vista_asistencias_diarias AS
            SELECT 
                DATE(a.fecha_hora_entrada) as fecha,
                COUNT(*) as total_asistencias,
                COUNT(DISTINCT a.usuario_id) as usuarios_unicos,
                AVG(EXTRACT(EPOCH FROM (a.fecha_hora_salida - a.fecha_hora_entrada))/3600) as promedio_horas
            FROM asistencias a
            WHERE a.fecha_hora_entrada >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY DATE(a.fecha_hora_entrada)
            ORDER BY fecha DESC;
            """),
        ]
        
        # Ejecutar vistas
        for view in views:
            try:
                view.execute(self.engine)
                logger.info("Vista creada exitosamente")
            except Exception as e:
                logger.warning(f"Error creando vista: {e}")
    
    def optimize_postgresql_settings(self) -> None:
        """Optimiza configuraciones específicas de PostgreSQL"""
        
        optimizations = [
            # === HABILITAR EXTENSIONES ÚTILES ===
            DDL("CREATE EXTENSION IF NOT EXISTS pg_trgm;"),  # Para búsquedas de texto
            DDL("CREATE EXTENSION IF NOT EXISTS btree_gin;"),  # Para índices GIN en tipos básicos
            DDL("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"),  # Para estadísticas de queries
            
            # === CONFIGURAR PARÁMETROS DE RENDIMIENTO ===
            # Estas configuraciones se aplicarían a nivel de sesión
            DDL("SET work_mem = '64MB';"),
            DDL("SET effective_cache_size = '2GB';"),
            DDL("SET random_page_cost = 1.1;"),
            DDL("SET checkpoint_completion_target = 0.9;"),
        ]
        
        # Ejecutar optimizaciones
        for opt in optimizations:
            try:
                opt.execute(self.engine)
                logger.info("Optimización PostgreSQL aplicada")
            except Exception as e:
                logger.warning(f"Error aplicando optimización PostgreSQL: {e}")
    
    def create_partitions(self) -> None:
        """Crea particiones para tablas grandes (asistencias, pagos)"""
        
        partitions = [
            # === PARTICIÓN PARA ASISTENCIAS POR MES ===
            DDL("""
            -- Crear tabla padre para asistencias particionadas
            CREATE TABLE IF NOT EXISTS asistencias_particionadas (
                LIKE asistencias INCLUDING ALL
            ) PARTITION BY RANGE (fecha_hora_entrada);
            """),
            
            # === PARTICIÓN PARA PAGOS POR AÑO ===
            DDL("""
            -- Crear tabla padre para pagos particionados
            CREATE TABLE IF NOT EXISTS pagos_particionados (
                LIKE pagos INCLUDING ALL
            ) PARTITION BY RANGE (fecha_pago);
            """),
        ]
        
        # Crear particiones para los próximos 12 meses
        for i in range(12):
            partitions.append(
                DDL(f"""
                CREATE TABLE IF NOT EXISTS asistencias_{i+1:02d} 
                PARTITION OF asistencias_particionadas
                FOR VALUES FROM ('{2024}-{i+1:02d}-01') TO ('{2024}-{i+2:02d}-01');
                """)
            )
        
        # Ejecutar particiones (opcional para grandes volúmenes)
        if settings.ENABLE_PARTITIONING:
            for partition in partitions:
                try:
                    partition.execute(self.engine)
                    logger.info("Partición creada exitosamente")
                except Exception as e:
                    logger.warning(f"Error creando partición: {e}")
    
    def analyze_and_vacuum(self) -> None:
        """Ejecuta ANALYZE y VACUUM para optimizar estadísticas"""
        
        maintenance_queries = [
            "ANALYZE usuarios;",
            "ANALYZE asistencias;",
            "ANALYZE pagos;",
            "ANALYZE clases;",
            "ANALYZE horarios_clases;",
            "ANALYZE empleados;",
            "VACUUM ANALYZE usuarios;",
            "VACUUM ANALYZE asistencias;",
            "VACUUM ANALYZE pagos;",
        ]
        
        for query in maintenance_queries:
            try:
                self.engine.execute(text(query))
                logger.info(f"Mantenimiento ejecutado: {query}")
            except Exception as e:
                logger.warning(f"Error en mantenimiento: {e}")
    
    def apply_all_optimizations(self) -> None:
        """Aplica todas las optimizaciones de base de datos"""
        
        logger.info("Iniciando optimizaciones de base de datos...")
        
        # 1. Crear índices de rendimiento
        self.create_performance_indexes()
        
        # 2. Crear funciones de BD
        self.create_database_functions()
        
        # 3. Crear triggers
        self.create_triggers()
        
        # 4. Aplicar triggers a tablas
        self.apply_triggers_to_tables()
        
        # 5. Crear vistas optimizadas
        self.create_views()
        
        # 6. Optimizar configuraciones PostgreSQL
        self.optimize_postgresql_settings()
        
        # 7. Crear particiones (si está habilitado)
        self.create_partitions()
        
        # 8. Ejecutar mantenimiento
        self.analyze_and_vacuum()
        
        logger.info("Optimizaciones de base de datos completadas")

# ===============================
# FUNCIONES DE UTILIDAD
# ===============================

def get_database_statistics(engine: Engine) -> Dict[str, Any]:
    """Obtiene estadísticas de la base de datos"""
    
    stats = {}
    
    try:
        with engine.connect() as conn:
            # Estadísticas de tablas
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC;
            """))
            
            stats['table_stats'] = [dict(row) for row in result]
            
            # Estadísticas de índices
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE idx_tup_read > 0
                ORDER BY idx_tup_read DESC;
            """))
            
            stats['index_stats'] = [dict(row) for row in result]
            
            # Tamaño de tablas
            result = conn.execute(text("""
                SELECT 
                    tablename,
                    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(tablename::regclass) DESC;
            """))
            
            stats['table_sizes'] = [dict(row) for row in result]
            
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        stats['error'] = str(e)
    
    return stats

def optimize_database_on_startup(engine: Engine) -> None:
    """Ejecuta optimizaciones al iniciar la aplicación"""
    
    try:
        optimizer = DatabaseOptimizer(engine)
        optimizer.apply_all_optimizations()
        logger.info("Base de datos optimizada al iniciar")
    except Exception as e:
        logger.error(f"Error optimizando base de datos: {e}")

# ===============================
# EVENTOS DE SQLALCHEMY
# ===============================

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configura pragmas para SQLite (desarrollo)"""
    if hasattr(dbapi_connection, 'execute'):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

@event.listens_for(Engine, "connect")
def set_postgresql_settings(dbapi_connection, connection_record):
    """Configura settings para PostgreSQL (producción)"""
    if hasattr(dbapi_connection, 'set_session'):
        dbapi_connection.set_session(
            isolation_level='READ_COMMITTED',
            readonly=False,
            deferrable=False,
            autocommit=False
        ) 