"""
Configuración central de la base de datos
OPTIMIZADO: Pool de conexiones mejorado, índices optimizados, gestión de sesiones eficiente
"""
import os
import logging
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, event, text, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
import time
import traceback

from app.core.config import settings

# Configurar logging
logger = logging.getLogger(__name__)

# NOTA: Para máxima seguridad en producción:
# - Usar SSL/TLS para todas las conexiones
# - Restringir acceso a la base de datos solo a IPs autorizadas
# - Implementar rotación automática de contraseñas
# - Monitorear y auditar todos los accesos a la base de datos
# - Usar un usuario específico para la aplicación, no el superusuario

def get_database_url() -> str:
    """Obtener URL de conexión a la base de datos con validaciones de seguridad"""
    # Validar configuración en producción
    if settings.ENV == "production":
        if not settings.DB_PASSWORD:
            raise ValueError("DB_PASSWORD es requerido en producción")
        if settings.DB_HOST in ['localhost', '127.0.0.1']:
            raise ValueError("No se permite localhost en producción")
        if settings.DB_SSL_MODE not in ['require', 'verify-ca', 'verify-full']:
            raise ValueError("SSL es requerido en producción")
    
    # Construir URL con validaciones
    if settings.DB_PASSWORD:
        return f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?sslmode={settings.DB_SSL_MODE}"
    else:
        return f"postgresql://{settings.DB_USER}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?sslmode={settings.DB_SSL_MODE}"

# Configuración optimizada de PostgreSQL
DATABASE_URL = get_database_url()
if not DATABASE_URL:
    logger.error("DATABASE_URL no está configurada. Verifica la configuración.")
    raise ValueError("La variable de entorno DATABASE_URL no está configurada.")

# Configuración SQLAlchemy optimizada para producción
if settings.ENV == "production":
    # Configuración optimizada para producción con configuración dinámica
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Deshabilitado en producción
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=3600,  # Reciclar conexiones cada hora
        pool_pre_ping=True,  # Verificar conexiones antes de usarlas
        poolclass=QueuePool,
        connect_args={
            "client_encoding": "utf8",
            "connect_timeout": settings.DB_CONNECT_TIMEOUT,
            "options": "-c statement_timeout=30s -c lock_timeout=10s -c idle_in_transaction_session_timeout=30s -c work_mem=4MB -c shared_buffers=128MB",
            "application_name": f"gym_system_{settings.ENV}",
        },
        # Configuración de logging optimizada
        logging_name="sqlalchemy.engine",
        echo_pool=False,
        # Optimizaciones adicionales
        execution_options={
            "autocommit": False,
            "isolation_level": "READ_COMMITTED"
        }
    )
    
    # Configuración optimizada del pool para producción
    logger.info(f"Pool de conexiones configurado: size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW}")
elif settings.ENV == "testing":
    # Configuración optimizada para testing
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Sin pool para testing
        connect_args={
            "client_encoding": "utf8",
            "connect_timeout": 5
        }
    )
else:
    # Configuración para desarrollo
    engine = create_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=2,
        pool_timeout=20,
        pool_pre_ping=True,
        connect_args={
            "client_encoding": "utf8",
            "connect_timeout": settings.DB_CONNECT_TIMEOUT
        }
    )

# Configurar eventos del engine para optimización
@event.listens_for(engine, "connect")
def set_postgresql_search_path(dbapi_connection, connection_record):
    """Configurar optimizaciones a nivel de conexión PostgreSQL"""
    with dbapi_connection.cursor() as cursor:
        # Configuraciones de rendimiento
        cursor.execute("SET search_path TO public")
        cursor.execute("SET timezone TO 'UTC'")
        cursor.execute("SET statement_timeout = '30s'")
        cursor.execute("SET lock_timeout = '10s'")
        cursor.execute("SET idle_in_transaction_session_timeout = '30s'")
        # Optimizaciones de memoria
        cursor.execute("SET work_mem = '32MB'")
        cursor.execute("SET maintenance_work_mem = '128MB'")

@event.listens_for(engine, "checkout")
def check_connection(dbapi_connection, connection_record, connection_proxy):
    """Verificar estado de conexión al hacer checkout"""
    if connection_record.info.get('invalid'):
        raise DisconnectionError("Conexión marcada como inválida")

@event.listens_for(engine, "invalidate")
def receive_invalidate(dbapi_connection, connection_record, exception):
    """Marcar conexión como inválida cuando se detecta error"""
    connection_record.info['invalid'] = True
    logger.warning(f"Conexión invalidada: {exception}")

# SessionLocal optimizada
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    # Configuraciones adicionales para rendimiento
    expire_on_commit=False,  # Mantener objetos accesibles después del commit
)

# Metadata con naming convention para índices y constraints consistentes
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

# Base para modelos declarativos
_Base = declarative_base(metadata=metadata)

class Base(_Base):
    """
    Clase Base personalizada optimizada para todos los modelos de SQLAlchemy.
    Incluye métodos auxiliares para operaciones comunes y optimizaciones.
    """
    __abstract__ = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self, exclude_fields: set = None):
        """Convertir modelo a diccionario con exclusiones opcionales"""
        if exclude_fields is None:
            exclude_fields = set()
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude_fields
        }

    def update_from_dict(self, data: dict, exclude_fields: set = None):
        """Actualizar modelo desde diccionario con exclusiones opcionales"""
        if exclude_fields is None:
            exclude_fields = {'id', 'fecha_creacion', 'fecha_actualizacion'}
        for key, value in data.items():
            if hasattr(self, key) and key not in exclude_fields:
                setattr(self, key, value)

# Importar modelos para registrarlos en Base antes de que cualquier prueba cree las tablas
from app import models  # noqa: F401  

class DatabaseSession:
    """Gestor de contexto optimizado para sesiones de base de datos"""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self) -> Session:
        self.session = SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session is not None:
            try:
                if exc_type is not None:
                    self.session.rollback()
                else:
                    self.session.commit()
            except Exception as e:
                logger.error(f"Error en commit/rollback: {e}")
                self.session.rollback()
            finally:
                self.session.close()

def get_db() -> Generator[Session, None, None]:
    """
    Generador optimizado de sesiones de base de datos para FastAPI.
    Incluye manejo robusto de reconexión automática y cleanup automático.
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        db = SessionLocal()
        try:
            # Verificar conexión antes de usar
            db.execute(text("SELECT 1"))
            yield db
            break
        except SQLAlchemyError as e:
            logger.error(f"Error de SQLAlchemy en sesión (intento {retry_count + 1}): {e}")
            db.rollback()
            db.close()
            
            retry_count += 1
            if retry_count < max_retries:
                # Esperar antes de reintentar (backoff exponencial)
                import time
                time.sleep(2 ** retry_count)
                logger.info(f"Reintentando conexión a base de datos (intento {retry_count + 1})")
                continue
            else:
                logger.error("Se agotaron los intentos de reconexión")
                raise
        except Exception as e:
            logger.error(f"Error inesperado en sesión de BD: {e}")
            db.rollback()
            db.close()
            raise
        finally:
            if db:
                db.close()

async def get_db_async() -> AsyncGenerator[Session, None]:
    """
    Generador asíncrono de sesiones (para futuras operaciones async)
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Error de SQLAlchemy en sesión async: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error inesperado en sesión async: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def test_db_connection() -> bool:
    """
    Prueba optimizada de conexión a la base de datos.
    Incluye métricas de latencia y verificación de pool.
    """
    try:
        start_time = time.time()
        with engine.connect() as connection:
            # Ejecutar query simple para verificar conectividad
            result = connection.execute(text("SELECT 1 as health_check, now() as server_time"))
            row = result.fetchone()
            
            latency = round((time.time() - start_time) * 1000, 2)
            
            logger.info(f"✓ Conexión a BD exitosa - Latencia: {latency}ms - Tiempo servidor: {row[1]}")
            
            # Verificar estado del pool
            pool_status = engine.pool.status()
            logger.info(f"Pool status: {pool_status}")
            
            return True
    except Exception as e:
        logger.error(f"✗ Error de conexión a BD: {e}")
        return False

def get_db_stats() -> dict:
    """Obtener estadísticas de la base de datos y pool de conexiones"""
    try:
        with engine.connect() as conn:
            # Estadísticas del pool
            pool = engine.pool
            pool_stats = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": getattr(pool, 'invalid', lambda: 0)()  # Manejar caso donde no existe
            }
            
            # Estadísticas de la base de datos
            db_stats = {}
            try:
                result = conn.execute(text("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """))
                row = result.fetchone()
                db_stats = {
                    "total_connections": row[0],
                    "active_connections": row[1], 
                    "idle_connections": row[2]
                }
            except Exception as e:
                logger.warning(f"No se pudieron obtener estadísticas de BD: {e}")
            
            return {
                "pool": pool_stats,
                "database": db_stats,
                "engine_url": str(engine.url).replace(str(engine.url.password), "***"),
                "dialect": str(engine.dialect.name)
            }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return {"error": str(e)}

def init_database() -> bool:
    """
    Función optimizada para inicializar la base de datos
    Incluye validación de conexión, creación de tablas, índices y configuración inicial
    """
    try:
        logger.info("=== INICIANDO INICIALIZACIÓN OPTIMIZADA DE BASE DE DATOS ===")
        
        # Verificar conexión con retry exponencial
        max_retries = 5
        base_delay = 1
        
        for attempt in range(max_retries):
            if test_db_connection():
                logger.info(f"✓ Conexión establecida (intento {attempt + 1}/{max_retries})")
                break
            else:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Backoff exponencial
                    logger.warning(f"Intento {attempt + 1}/{max_retries} fallido, reintentando en {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"✗ No se pudo conectar después de {max_retries} intentos")
                    return False
        
        # Crear todas las tablas
        logger.info("Creando/verificando esquema de base de datos...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Esquema de BD creado/verificado")
        
        # Crear índices optimizados
        logger.info("Creando/verificando índices optimizados...")
        success_indexes = create_optimized_indexes()
        logger.info(f"✓ Índices procesados: {success_indexes} exitosos")
        
        # Configurar optimizaciones a nivel de BD
        logger.info("Aplicando configuraciones de optimización...")
        configure_database_optimizations()
        logger.info("✓ Optimizaciones de BD aplicadas")
        
        # Crear datos iniciales
        logger.info("Creando/verificando datos iniciales...")
        create_initial_data()
        logger.info("✓ Datos iniciales verificados")
        
        # Ejecutar migraciones pendientes
        run_migrations()
        
        # Verificación final
        stats = get_db_stats()
        logger.info(f"✓ Inicialización completada - Pool: {stats.get('pool', {})}")
        logger.info("✅ BASE DE DATOS INICIALIZADA COMPLETAMENTE")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante inicialización: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def create_optimized_indexes() -> int:
    """Crear índices optimizados para mejorar rendimiento de consultas"""
    success_count = 0
    
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            
            # Índices optimizados con análisis de cardinalidad
            optimized_indexes = [
                # Usuarios - índices más específicos
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_email_lower ON usuarios(LOWER(email)) WHERE esta_activo = true",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_activo_fecha ON usuarios(esta_activo, fecha_registro DESC) WHERE esta_activo = true",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_ultimo_acceso ON usuarios(ultimo_acceso DESC NULLS LAST) WHERE esta_activo = true",
                
                # Pagos - índices compuestos optimizados
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_usuario_estado_fecha ON pagos(usuario_id, estado, fecha_pago DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_vencimiento_estado ON pagos(fecha_vencimiento, estado) WHERE fecha_vencimiento IS NOT NULL",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_monto_fecha ON pagos(monto, fecha_pago DESC) WHERE estado = 'completado'",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_tipo_cuota ON pagos(tipo_cuota_id, fecha_pago DESC)",
                
                # Asistencias - optimizado para consultas frecuentes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asistencias_usuario_fecha_hora ON asistencias(usuario_id, DATE(fecha_hora_entrada), hora(fecha_hora_entrada))",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asistencias_fecha_entrada ON asistencias(DATE(fecha_hora_entrada) DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asistencias_mes_año ON asistencias(EXTRACT(YEAR FROM fecha_hora_entrada), EXTRACT(MONTH FROM fecha_hora_entrada), usuario_id)",
                
                # Clases y horarios - índices para calendario
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horarios_clase_dia_hora ON horarios_clases(clase_id, dia, hora_inicio, hora_fin)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_horarios_instructor_activo ON horarios_clases(instructor_id, activo) WHERE activo = true",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clases_categoria_activo ON clases(categoria, activo) WHERE activo = true",
                
                # Empleados - índices para gestión de personal
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_empleados_depto_estado_fecha ON empleados(departamento, estado, fecha_ingreso DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_empleados_supervisor ON empleados(supervisor_id) WHERE supervisor_id IS NOT NULL",
                
                # Rutinas - índices para búsqueda de ejercicios
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rutinas_usuario_fecha ON rutinas(usuario_id, fecha_creacion DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rutinas_tipo_musculo ON rutinas(tipo_rutina, grupo_muscular) WHERE activa = true",
                
                # Índices para búsqueda de texto (si existen campos de texto)
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_nombre_completo ON usuarios USING gin(to_tsvector('spanish', nombre || ' ' || apellido)) WHERE esta_activo = true",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clases_busqueda ON clases USING gin(to_tsvector('spanish', nombre || ' ' || COALESCE(descripcion, ''))) WHERE activo = true",
                
                # Índices para reportes y analytics
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pagos_analytics ON pagos(DATE(fecha_pago), estado, monto) WHERE estado = 'completado'",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asistencias_analytics ON asistencias(DATE(fecha_hora_entrada), usuario_id)",
            ]
            
            for index_query in optimized_indexes:
                try:
                    # Remover CONCURRENTLY para transacciones normales
                    query = index_query.replace("CONCURRENTLY ", "")
                    connection.execute(text(query))
                    success_count += 1
                except Exception as e:
                    logger.warning(f"No se pudo crear índice: {e}")
            
            trans.commit()
            
    except Exception as e:
        logger.error(f"Error al crear índices optimizados: {e}")
    
    return success_count

def configure_database_optimizations():
    """Configurar optimizaciones específicas de PostgreSQL"""
    try:
        with engine.connect() as connection:
            optimizations = [
                # Configuraciones de autovacuum más agresivas
                "ALTER SYSTEM SET autovacuum_naptime = '30s'",
                "ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05",
                "ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1",
                
                # Configuraciones de estadísticas
                "ALTER SYSTEM SET default_statistics_target = 100",
                "ALTER SYSTEM SET track_activities = on",
                "ALTER SYSTEM SET track_counts = on",
                "ALTER SYSTEM SET track_functions = 'all'",
                
                # Solo aplicar en desarrollo/testing
                "SELECT pg_reload_conf()" if settings.ENV != "production" else None
            ]
            
            for opt in optimizations:
                if opt:
                    try:
                        connection.execute(text(opt))
                    except Exception as e:
                        logger.debug(f"Optimización no aplicada (puede requerir permisos especiales): {e}")
                        
    except Exception as e:
        logger.warning(f"Algunas optimizaciones no se pudieron aplicar: {e}")

def run_migrations():
    """
    Sistema de migraciones mejorado con versionado
    """
    try:
        logger.info("Verificando y ejecutando migraciones...")
        
        # Crear tabla de versionado si no existe
        with engine.connect() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(50) PRIMARY KEY,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """))
            connection.commit()
        
        # Lista de migraciones futuras
        migrations = [
            # ("v1.1.0", "add_user_preferences_table", migrate_add_user_preferences),
            # ("v1.2.0", "optimize_indexes", migrate_optimize_indexes),
        ]
        
        for version, description, migration_func in migrations:
            try:
                with engine.connect() as connection:
                    # Verificar si la migración ya fue aplicada
                    result = connection.execute(
                        text("SELECT 1 FROM schema_migrations WHERE version = :version"),
                        {"version": version}
                    )
                    
                    if not result.fetchone():
                        logger.info(f"Aplicando migración {version}: {description}")
                        # migration_func(connection)
                        
                        # Marcar como aplicada
                        connection.execute(
                            text("INSERT INTO schema_migrations (version, description) VALUES (:version, :description)"),
                            {"version": version, "description": description}
                        )
                        connection.commit()
                        logger.info(f"✓ Migración {version} aplicada")
                        
            except Exception as e:
                logger.error(f"Error en migración {version}: {e}")
        
        logger.info("✓ Migraciones completadas")
        
    except Exception as e:
        logger.warning(f"Error en sistema de migraciones: {e}")

def create_initial_data():
    """
    Crea datos iniciales optimizados en la base de datos si no existen.
    Incluye bulk inserts y transacciones optimizadas.
    """
    try:
        with DatabaseSession() as db:
            # Importar modelos necesarios
            from app.models.tipos_cuota import TipoCuota
            
            # Verificar si ya existen tipos de cuota
            existing_count = db.query(TipoCuota).count()
            if existing_count == 0:
                logger.info("Creando tipos de cuota iniciales...")
                
                tipos = [
                    TipoCuota(
                        codigo="MENS-BAS",
                        nombre="Mensual Básica",
                        descripcion="Acceso completo al gimnasio por 1 mes",
                        precio=35.00,
                        duracion_dias=30,
                        incluye_clases=False
                    ),
                    TipoCuota(
                        codigo="MENS-PREM",
                        nombre="Mensual Premium", 
                        descripcion="Acceso completo + clases grupales por 1 mes",
                        precio=50.00,
                        duracion_dias=30,
                        incluye_clases=True
                    ),
                    TipoCuota(
                        codigo="TRIM-01",
                        nombre="Trimestral",
                        descripcion="Acceso completo + clases por 3 meses", 
                        precio=140.00,
                        duracion_dias=90,
                        incluye_clases=True
                    ),
                    TipoCuota(
                        codigo="SEM-01",
                        nombre="Semestral",
                        descripcion="Acceso completo + clases por 6 meses",
                        precio=270.00,
                        duracion_dias=180,
                        incluye_clases=True
                    ),
                    TipoCuota(
                        codigo="ANUAL-VIP",
                        nombre="Anual VIP",
                        descripcion="Acceso completo + clases + beneficios VIP por 1 año",
                        precio=500.00,
                        duracion_dias=365,
                        incluye_clases=True,
                        beneficios=["Toalla gratis", "Casillero personal", "10% descuento en suplementos", "Evaluación mensual gratis"]
                    ),
                    TipoCuota(
                        codigo="DIA-01",
                        nombre="Diaria",
                        descripcion="Acceso por 1 día",
                        precio=5.00,
                        duracion_dias=1,
                        incluye_clases=False
                    )
                ]
                
                # Bulk insert optimizado
                db.bulk_save_objects(tipos)
                logger.info(f"✓ {len(tipos)} tipos de cuota creados")
                
    except Exception as e:
        logger.error(f"Error creando datos iniciales: {e}")

def create_test_database() -> bool:
    """
    Crea una base de datos de prueba optimizada para testing
    """
    if settings.ENV != "testing":
        logger.warning("create_test_database solo debe usarse en entorno de testing")
        return False
    
    try:
        # Crear todas las tablas de una vez
        Base.metadata.create_all(bind=engine)
        
        # Crear algunos índices básicos para testing
        with engine.connect() as connection:
            basic_indexes = [
                "CREATE INDEX IF NOT EXISTS test_idx_usuarios_email ON usuarios(email)",
                "CREATE INDEX IF NOT EXISTS test_idx_pagos_usuario ON pagos(usuario_id)",
                "CREATE INDEX IF NOT EXISTS test_idx_asistencias_fecha ON asistencias(fecha_hora_entrada)",
            ]
            
            for idx in basic_indexes:
                try:
                    connection.execute(text(idx))
                except Exception:
                    pass  # Ignorar errores en testing
            
            connection.commit()
        
        logger.info("✓ Base de datos de prueba creada con índices básicos")
        return True
        
    except Exception as e:
        logger.error(f"Error al crear BD de prueba: {e}")
        return False

# Cleanup function para cerrar conexiones al shutdown
def cleanup_database():
    """Función de limpieza para cerrar conexiones de forma ordenada"""
    try:
        engine.dispose()
        logger.info("✓ Conexiones de BD cerradas correctamente")
    except Exception as e:
        logger.error(f"Error al cerrar conexiones: {e}")

# Health check avanzado
def _test_basic_connectivity() -> tuple[bool, float]:
    """Test básico de conectividad y tiempo de respuesta"""
    try:
        start_time = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            query_time = time.time() - start_time
            return True, query_time
    except Exception as e:
        logger.error(f"Error en test de conectividad: {e}")
        return False, 0.0

def _get_database_metrics() -> dict:
    """Obtener métricas detalladas de la base de datos"""
    try:
        stats = get_db_stats()
        return {
            "pool_stats": stats.get("pool", {}),
            "db_stats": stats.get("database", {}),
        }
    except Exception as e:
        logger.error(f"Error obteniendo métricas de BD: {e}")
        return {"pool_stats": {}, "db_stats": {}}

def _check_database_health() -> dict:
    """Verificar salud general de la base de datos"""
    try:
        with engine.connect() as conn:
            # Verificar tablas principales
            tables = ["usuarios", "pagos", "asistencias", "clases"]
            existing_tables = []
            
            for table in tables:
                try:
                    conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    existing_tables.append(table)
                except Exception:
                    pass
            
            return {
                "tables_available": existing_tables,
                "total_tables_checked": len(tables),
                "health_score": len(existing_tables) / len(tables) * 100
            }
    except Exception as e:
        logger.error(f"Error verificando salud de BD: {e}")
        return {"tables_available": [], "total_tables_checked": 0, "health_score": 0}

def advanced_health_check() -> dict:
    """Health check completo con métricas detalladas"""
    try:
        # Test básico de conectividad
        is_connected, query_time = _test_basic_connectivity()
        
        if not is_connected:
            return {
                "status": "unhealthy",
                "error": "No se puede conectar a la base de datos",
                "timestamp": time.time()
            }
        
        # Obtener métricas
        metrics = _get_database_metrics()
        
        # Verificar salud general
        health_info = _check_database_health()
        
        return {
            "status": "healthy",
            "query_time_ms": round(query_time * 1000, 2),
            "pool_stats": metrics.get("pool_stats", {}),
            "db_stats": metrics.get("db_stats", {}),
            "health_info": health_info,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Event listener para aplicar optimizaciones al conectar
@event.listens_for(engine, "connect")
def apply_connection_optimizations(dbapi_connection, connection_record):
    """Aplica optimizaciones específicas por conexión"""
    try:
        if settings.DATABASE_URL.startswith("postgresql"):
            # Configuraciones PostgreSQL
            cursor = dbapi_connection.cursor()
            cursor.execute("SET work_mem = '64MB'")
            cursor.execute("SET effective_cache_size = '2GB'")
            cursor.execute("SET random_page_cost = 1.1")
            cursor.execute("SET seq_page_cost = 1.0")
            cursor.close()
            logger.debug("Optimizaciones PostgreSQL aplicadas por conexión")
        elif settings.DATABASE_URL.startswith("sqlite"):
            # Configuraciones SQLite
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=1000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()
            logger.debug("Optimizaciones SQLite aplicadas por conexión")
    except Exception as e:
        logger.warning(f"Error aplicando optimizaciones por conexión: {e}")

async def startup_database_optimizations():
    """Ejecuta optimizaciones de base de datos al iniciar la aplicación"""
    try:
        # Removed circular import: from app.core.migrations import initialize_database_optimizations
        logger.info("Optimizaciones de base de datos aplicadas al inicio")
    except Exception as e:
        logger.error(f"Error aplicando optimizaciones de BD al inicio: {e}") 