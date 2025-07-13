#!/bin/bash
# =============================================================================
# SCRIPT DE RESTAURACIÓN DE BACKUP
# Sistema de Gestión de Gimnasio v6.0
# =============================================================================

set -euo pipefail

# Configuración
BACKUP_DIR="/backup/data"
LOG_FILE="/backup/restore.log"

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función de error
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Función de ayuda
show_help() {
    cat << EOF
Uso: $0 [OPCIONES] <archivo_backup>

OPCIONES:
    -h, --help          Mostrar esta ayuda
    -d, --database      Restaurar solo base de datos
    -f, --files         Restaurar solo archivos
    -e, --encrypted     El backup está encriptado
    -k, --key KEY       Clave de encriptación
    -y, --yes           Confirmar sin preguntar

EJEMPLOS:
    $0 gym_backup_20241201_120000.sql
    $0 -d gym_backup_20241201_120000.sql.enc -e -k "mi_clave"
    $0 -f gym_backup_20241201_120000_files.tar.gz
EOF
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

# Variables globales
RESTORE_DATABASE=false
RESTORE_FILES=false
IS_ENCRYPTED=false
ENCRYPTION_KEY=""
AUTO_CONFIRM=false
BACKUP_FILE=""

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--database)
            RESTORE_DATABASE=true
            shift
            ;;
        -f|--files)
            RESTORE_FILES=true
            shift
            ;;
        -e|--encrypted)
            IS_ENCRYPTED=true
            shift
            ;;
        -k|--key)
            ENCRYPTION_KEY="$2"
            shift 2
            ;;
        -y|--yes)
            AUTO_CONFIRM=true
            shift
            ;;
        -*)
            error_exit "Opción desconocida: $1"
            ;;
        *)
            BACKUP_FILE="$1"
            shift
            ;;
    esac
done

# Si no se especificó tipo, restaurar ambos
if [[ "$RESTORE_DATABASE" == false && "$RESTORE_FILES" == false ]]; then
    RESTORE_DATABASE=true
    RESTORE_FILES=true
fi

# Verificar que se proporcionó archivo de backup
if [[ -z "$BACKUP_FILE" ]]; then
    error_exit "Debe especificar un archivo de backup"
fi

# Función para desencriptar archivo
decrypt_file() {
    local input_file="$1"
    local output_file="${input_file%.enc}"
    
    if [[ "$IS_ENCRYPTED" == true ]]; then
        if [[ -z "$ENCRYPTION_KEY" ]]; then
            error_exit "Clave de encriptación requerida para archivos encriptados"
        fi
        
        log "Desencriptando archivo..."
        
        openssl enc -aes-256-cbc \
            -d \
            -in "$input_file" \
            -out "$output_file" \
            -pass pass:"$ENCRYPTION_KEY" \
            2>> "$LOG_FILE"
        
        if [[ $? -eq 0 ]]; then
            log "Archivo desencriptado: $output_file"
            echo "$output_file"
        else
            error_exit "Error al desencriptar archivo"
        fi
    else
        echo "$input_file"
    fi
}

# Función para restaurar base de datos
restore_database() {
    local backup_file="$1"
    
    log "Iniciando restauración de base de datos..."
    
    # Verificar que el archivo existe
    if [[ ! -f "$backup_file" ]]; then
        error_exit "Archivo de backup no encontrado: $backup_file"
    fi
    
    # Desencriptar si es necesario
    local decrypted_file=$(decrypt_file "$backup_file")
    
    # Crear backup de la base de datos actual antes de restaurar
    local safety_backup="${BACKUP_DIR}/safety_backup_$(date +%Y%m%d_%H%M%S).sql"
    log "Creando backup de seguridad antes de restaurar..."
    
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
        > "$safety_backup" 2>> "$LOG_FILE"
    
    if [[ $? -ne 0 ]]; then
        log "WARNING: No se pudo crear backup de seguridad"
    else
        log "Backup de seguridad creado: $safety_backup"
    fi
    
    # Restaurar base de datos
    log "Restaurando base de datos desde: $decrypted_file"
    
    PGPASSWORD="$GYM_DB_PASSWORD" psql \
        -h "$GYM_DB_HOST" \
        -p "${GYM_DB_PORT:-5432}" \
        -U "$GYM_DB_USER" \
        -d "$GYM_DB_NAME" \
        -f "$decrypted_file" \
        2>> "$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log "✅ Base de datos restaurada exitosamente"
    else
        error_exit "Error al restaurar base de datos"
    fi
    
    # Limpiar archivo desencriptado temporal
    if [[ "$IS_ENCRYPTED" == true ]]; then
        rm -f "$decrypted_file"
    fi
}

# Función para restaurar archivos
restore_files() {
    local backup_file="$1"
    
    log "Iniciando restauración de archivos..."
    
    # Verificar que el archivo existe
    if [[ ! -f "$backup_file" ]]; then
        error_exit "Archivo de backup no encontrado: $backup_file"
    fi
    
    # Desencriptar si es necesario
    local decrypted_file=$(decrypt_file "$backup_file")
    
    # Crear backup de archivos actuales
    local safety_backup="${BACKUP_DIR}/safety_files_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    log "Creando backup de seguridad de archivos actuales..."
    
    if [[ -d "/app/uploads" ]]; then
        tar -czf "$safety_backup" -C /app uploads/ logs/ 2>> "$LOG_FILE" || true
        log "Backup de seguridad de archivos creado: $safety_backup"
    fi
    
    # Restaurar archivos
    log "Restaurando archivos desde: $decrypted_file"
    
    tar -xzf "$decrypted_file" -C /app 2>> "$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log "✅ Archivos restaurados exitosamente"
    else
        error_exit "Error al restaurar archivos"
    fi
    
    # Limpiar archivo desencriptado temporal
    if [[ "$IS_ENCRYPTED" == true ]]; then
        rm -f "$decrypted_file"
    fi
}

# Función para confirmar restauración
confirm_restore() {
    if [[ "$AUTO_CONFIRM" == true ]]; then
        return 0
    fi
    
    echo "⚠️  ADVERTENCIA: Esta operación sobrescribirá datos existentes"
    echo "Archivo de backup: $BACKUP_FILE"
    echo "Operaciones a realizar:"
    [[ "$RESTORE_DATABASE" == true ]] && echo "  - Restaurar base de datos"
    [[ "$RESTORE_FILES" == true ]] && echo "  - Restaurar archivos"
    echo ""
    
    read -p "¿Está seguro de que desea continuar? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Restauración cancelada por el usuario"
        exit 0
    fi
}

# Función para verificar integridad del backup
verify_backup() {
    local backup_file="$1"
    
    log "Verificando integridad del backup..."
    
    if [[ ! -f "$backup_file" ]]; then
        error_exit "Archivo de backup no encontrado: $backup_file"
    fi
    
    # Verificar tamaño del archivo
    local file_size=$(stat -c%s "$backup_file")
    if [[ $file_size -eq 0 ]]; then
        error_exit "Archivo de backup está vacío"
    fi
    
    log "Archivo de backup verificado: $(basename "$backup_file") ($(numfmt --to=iec $file_size))"
}

# Función principal
main() {
    log "=== INICIANDO RESTAURACIÓN DE BACKUP ==="
    
    # Verificar archivo de backup
    verify_backup "$BACKUP_FILE"
    
    # Confirmar restauración
    confirm_restore
    
    # Crear directorio de backup si no existe
    mkdir -p "$BACKUP_DIR"
    
    # Determinar tipo de backup basado en el nombre del archivo
    if [[ "$BACKUP_FILE" == *"_files"* ]]; then
        if [[ "$RESTORE_FILES" == true ]]; then
            restore_files "$BACKUP_FILE"
        else
            log "Archivo de backup de archivos detectado pero restauración de archivos no solicitada"
        fi
    else
        if [[ "$RESTORE_DATABASE" == true ]]; then
            restore_database "$BACKUP_FILE"
        else
            log "Archivo de backup de base de datos detectado pero restauración de base de datos no solicitada"
        fi
    fi
    
    log "=== RESTAURACIÓN COMPLETADA EXITOSAMENTE ==="
}

# Ejecutar función principal
main "$@" 