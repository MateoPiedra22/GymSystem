#!/bin/bash
set -e

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🚀 Iniciando aplicación FastAPI..."

# Verificar variables de entorno críticas
if [ -z "$GYM_SECRET_KEY" ]; then
    log "❌ ERROR: GYM_SECRET_KEY no configurado"
    exit 1
fi

if [ -z "$GYM_DB_PASSWORD" ]; then
    log "❌ ERROR: GYM_DB_PASSWORD no configurado"
    exit 1
fi

if [ -z "$GYM_JWT_SECRET_KEY" ]; then
    log "❌ ERROR: GYM_JWT_SECRET_KEY no configurado"
    exit 1
fi

if [ -z "$GYM_BACKUP_KEY" ]; then
    log "❌ ERROR: GYM_BACKUP_KEY no configurado"
    exit 1
fi

# Verificar que las claves no sean valores por defecto
if [ "$GYM_SECRET_KEY" = "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION_USE_SECURE_RANDOM_GENERATOR" ]; then
    log "❌ ERROR: GYM_SECRET_KEY usa valor por defecto"
    exit 1
fi

if [ "$GYM_DB_PASSWORD" = "CHANGE_THIS_DB_PASSWORD_IN_PRODUCTION_USE_SECURE_PASSWORD" ]; then
    log "❌ ERROR: GYM_DB_PASSWORD usa valor por defecto"
    exit 1
fi

if [ "$GYM_JWT_SECRET_KEY" = "CHANGE_THIS_JWT_SECRET_IN_PRODUCTION_USE_SECURE_RANDOM_GENERATOR" ]; then
    log "❌ ERROR: GYM_JWT_SECRET_KEY usa valor por defecto"
    exit 1
fi

if [ "$GYM_BACKUP_KEY" = "CHANGE_THIS_BACKUP_KEY_IN_PRODUCTION_USE_SECURE_RANDOM_GENERATOR" ]; then
    log "❌ ERROR: GYM_BACKUP_KEY usa valor por defecto"
    exit 1
fi

# Esperar a que la base de datos esté disponible
log "⏳ Esperando base de datos..."
while ! nc -z ${GYM_DB_HOST:-db} ${GYM_DB_PORT:-5432}; do
    sleep 1
done
log "✅ Base de datos disponible"

# Inicializar base de datos y crear admin
log "🔄 Inicializando base de datos y verificando admin..."
python -c "
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('Iniciando proceso de inicialización de la base de datos desde entrypoint...')
from app.core.database import init_database
from app.scripts.create_admin import ensure_admin_exists

if not init_database():
    logger.error('Falló la inicialización de la base de datos. Abortando.')
    exit(1)

ensure_admin_exists()
logger.info('✅ Proceso de inicialización completado.')
"

# Verificar seguridad
log "🔍 Verificando configuración de seguridad..."
python security_check.py
SECURITY_EXIT_CODE=$?
if [ $SECURITY_EXIT_CODE -ne 0 ]; then
    log "❌ ERROR: La verificación de seguridad falló con problemas críticos (código: $SECURITY_EXIT_CODE)."
    log "➡️  Revisar los logs de la verificación para más detalles."
    exit $SECURITY_EXIT_CODE
else
    log "✅ Verificación de seguridad superada."
fi

# Iniciar aplicación
log "🎯 Iniciando servidor..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers ${WORKERS:-4} \
    --loop uvloop \
    --http httptools \
    --access-log \
    --log-level ${LOG_LEVEL:-info} 