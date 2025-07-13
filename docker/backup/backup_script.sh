#!/bin/bash
# =============================================================================
# SCRIPT DE BACKUP AUTOMATIZADO
# Sistema de Gestión de Gimnasio v6.0
# =============================================================================

set -euo pipefail

# Configuración
BACKUP_DIR="/backup/data"
LOG_FILE="/backup/backup.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="gym_backup_${TIMESTAMP}"

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función de error
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Verificar variables de entorno requeridas
if [[ -z "${GYM_DB_HOST:-}" ]]; then
    error_exit "GYM_DB_HOST no está definido"
fi

if [[ -z "${GYM_DB_NAME:-}" ]]; then
    error_exit "GYM_DB_NAME no está definido"
fi

if [[ -z "${GYM_DB_USER:-}" ]]; then
    error_exit "GYM_DB_USER no está definido"
fi

if [[ -z "${GYM_DB_PASSWORD:-}" ]]; then
    error_exit "GYM_DB_PASSWORD no está definido"
fi

if [[ -z "${BACKUP_ENCRYPTION_KEY:-}" || ${#BACKUP_ENCRYPTION_KEY} -lt 32 ]]; then
    error_exit "BACKUP_ENCRYPTION_KEY no está definido o es inseguro (mínimo 32 caracteres). Aborta backup."
fi

# Función para crear backup de base de datos
create_database_backup() {
    log "Iniciando backup de base de datos..."
    
    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}.sql"
    
    # Crear backup con pg_dump
    PGPASSWORD="$GYM_DB_PASSWORD" pg_dump \
        -h "$GYM_DB_HOST" \
        -p "${GYM_DB_PORT:-5432}" \
        -U "$GYM_DB_USER" \
        -d "$GYM_DB_NAME" \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --no-owner \
        --no-privileges \
        > "$backup_file" 2>> "$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log "Backup de base de datos creado: $backup_file"
        echo "$backup_file"
    else
        error_exit "Error al crear backup de base de datos"
    fi
}

# Función para crear backup de archivos
create_files_backup() {
    log "Iniciando backup de archivos..."
    
    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}_files.tar.gz"
    
    # Crear backup de directorios importantes
    tar -czf "$backup_file" \
        -C /app \
        uploads/ \
        logs/ \
        2>> "$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log "Backup de archivos creado: $backup_file"
        echo "$backup_file"
    else
        error_exit "Error al crear backup de archivos"
    fi
}

# Función para encriptar backup
encrypt_backup() {
    local input_file="$1"
    local encrypted_file="${input_file}.enc"
    
    if [[ -n "${BACKUP_ENCRYPTION_KEY:-}" ]]; then
        log "Encriptando backup..."
        
        openssl enc -aes-256-cbc \
            -salt \
            -in "$input_file" \
            -out "$encrypted_file" \
            -pass pass:"$BACKUP_ENCRYPTION_KEY" \
            2>> "$LOG_FILE"
        
        if [[ $? -eq 0 ]]; then
            rm "$input_file"
            log "Backup encriptado: $encrypted_file"
            echo "$encrypted_file"
        else
            error_exit "Error al encriptar backup"
        fi
    else
        echo "$input_file"
    fi
}

# Función para subir a S3
upload_to_s3() {
    local file_path="$1"
    
    if [[ -n "${AWS_ACCESS_KEY_ID:-}" && -n "${AWS_SECRET_ACCESS_KEY:-}" && -n "${AWS_S3_BUCKET:-}" ]]; then
        log "Subiendo backup a S3..."
        
        aws s3 cp "$file_path" \
            "s3://${AWS_S3_BUCKET}/backups/$(basename "$file_path")" \
            --region "${AWS_REGION:-us-east-1}" \
            >> "$LOG_FILE" 2>&1
        
        if [[ $? -eq 0 ]]; then
            log "Backup subido exitosamente a S3"
        else
            log "WARNING: Error al subir backup a S3"
        fi
    else
        log "S3 no configurado, saltando upload"
    fi
}

# Función para limpiar backups antiguos
cleanup_old_backups() {
    local retention_days="${BACKUP_RETENTION_DAYS:-30}"
    
    log "Limpiando backups más antiguos de $retention_days días..."
    
    find "$BACKUP_DIR" -name "gym_backup_*" -type f -mtime +$retention_days -delete
    
    log "Limpieza completada"
}

# Función para verificar espacio en disco
check_disk_space() {
    local available_space=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    local required_space=1048576  # 1GB en KB
    
    if [[ $available_space -lt $required_space ]]; then
        error_exit "Espacio insuficiente en disco para backup"
    fi
    
    log "Espacio en disco suficiente: ${available_space}KB disponibles"
}

# Función principal
main() {
    log "=== INICIANDO BACKUP AUTOMATIZADO ==="
    
    # Verificar espacio en disco
    check_disk_space
    
    # Crear directorio de backup si no existe
    mkdir -p "$BACKUP_DIR"
    
    # Crear backups
    local db_backup_file=$(create_database_backup)
    local files_backup_file=$(create_files_backup)
    
    # Encriptar backups
    local encrypted_db_backup=$(encrypt_backup "$db_backup_file")
    local encrypted_files_backup=$(encrypt_backup "$files_backup_file")
    
    # Subir a S3
    upload_to_s3 "$encrypted_db_backup"
    upload_to_s3 "$encrypted_files_backup"
    
    # Limpiar backups antiguos
    cleanup_old_backups
    
    # Crear archivo de metadata
    local metadata_file="${BACKUP_DIR}/${BACKUP_NAME}_metadata.json"
    cat > "$metadata_file" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$(date -Iseconds)",
    "database_backup": "$(basename "$encrypted_db_backup")",
    "files_backup": "$(basename "$encrypted_files_backup")",
    "database_size": "$(stat -c%s "$encrypted_db_backup")",
    "files_size": "$(stat -c%s "$encrypted_files_backup")",
    "encrypted": "$([[ -n "${BACKUP_ENCRYPTION_KEY:-}" ]] && echo "true" || echo "false")",
    "s3_uploaded": "$([[ -n "${AWS_ACCESS_KEY_ID:-}" ]] && echo "true" || echo "false")"
}
EOF
    
    log "=== BACKUP COMPLETADO EXITOSAMENTE ==="
    log "Metadata guardada en: $metadata_file"
    
    # Mostrar resumen
    echo "Backup completado:"
    echo "  - Base de datos: $(basename "$encrypted_db_backup")"
    echo "  - Archivos: $(basename "$encrypted_files_backup")"
    echo "  - Metadata: $(basename "$metadata_file")"
}

# Ejecutar función principal
main "$@" 