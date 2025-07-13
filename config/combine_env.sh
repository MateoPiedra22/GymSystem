#!/bin/bash
# Script para combinar archivos de configuración por funcionalidad
# Uso: bash config/combine_env.sh [ambiente]

set -euo pipefail

# Configuración
ENVIRONMENT=${1:-development}
CONFIG_DIR="config/env"
OUTPUT_FILE=".env.${ENVIRONMENT}"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función de logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Verificar que existe el directorio de configuración
check_config_dir() {
    if [[ ! -d "$CONFIG_DIR" ]]; then
        error "Directorio de configuración no encontrado: $CONFIG_DIR"
        exit 1
    fi
}

# Crear archivo de configuración combinado
create_combined_env() {
    log "🔧 Creando archivo de configuración: $OUTPUT_FILE"
    
    # Crear encabezado
    cat > "$OUTPUT_FILE" << EOF
# =============================================================================
# ARCHIVO DE CONFIGURACIÓN COMBINADO
# Sistema de Gestión de Gimnasio v6.0
# Ambiente: $ENVIRONMENT
# Generado automáticamente el $(date '+%Y-%m-%d %H:%M:%S')
# =============================================================================
# Este archivo se genera combinando los archivos de config/env/
# Para modificar configuraciones específicas, edita los archivos individuales
# =============================================================================

EOF
    
    # Combinar archivos base
    local base_files=(
        "base.env"
        "database.env"
        "security.env"
        "services.env"
        "backup.env"
        "monitoring.env"
    )
    
    for file in "${base_files[@]}"; do
        local file_path="$CONFIG_DIR/$file"
        if [[ -f "$file_path" ]]; then
            log "Agregando configuración: $file"
            echo "" >> "$OUTPUT_FILE"
            echo "# =============================================================================" >> "$OUTPUT_FILE"
            echo "# CONFIGURACIÓN DE: $file" >> "$OUTPUT_FILE"
            echo "# =============================================================================" >> "$OUTPUT_FILE"
            cat "$file_path" >> "$OUTPUT_FILE"
        else
            warning "Archivo no encontrado: $file_path"
        fi
    done
    
    # Agregar configuraciones específicas del ambiente
    add_environment_specific_config
    
    success "Archivo de configuración creado: $OUTPUT_FILE"
}

# Agregar configuraciones específicas del ambiente
add_environment_specific_config() {
    echo "" >> "$OUTPUT_FILE"
    echo "# =============================================================================" >> "$OUTPUT_FILE"
    echo "# CONFIGURACIONES ESPECÍFICAS DEL AMBIENTE: $ENVIRONMENT" >> "$OUTPUT_FILE"
    echo "# =============================================================================" >> "$OUTPUT_FILE"
    
    case $ENVIRONMENT in
        "production")
            cat >> "$OUTPUT_FILE" << 'EOF'
# Configuraciones de producción
GYM_DEBUG=false
GYM_FORCE_HTTPS=true
GYM_SECURE_COOKIES=true
GYM_SECURITY_HEADERS=true
GYM_RATE_LIMITING=true
LOG_LEVEL=info
EOF
            ;;
        "staging")
            cat >> "$OUTPUT_FILE" << 'EOF'
# Configuraciones de staging
GYM_DEBUG=false
GYM_FORCE_HTTPS=false
GYM_SECURE_COOKIES=false
GYM_SECURITY_HEADERS=true
GYM_RATE_LIMITING=true
LOG_LEVEL=info
EOF
            ;;
        "development")
            cat >> "$OUTPUT_FILE" << 'EOF'
# Configuraciones de desarrollo
GYM_DEBUG=true
GYM_FORCE_HTTPS=false
GYM_SECURE_COOKIES=false
GYM_SECURITY_HEADERS=false
GYM_RATE_LIMITING=false
LOG_LEVEL=debug
EOF
            ;;
    esac
}

# Validar archivo generado
validate_generated_file() {
    log "🔍 Validando archivo generado..."
    
    if [[ ! -f "$OUTPUT_FILE" ]]; then
        error "Archivo de configuración no fue creado"
        return 1
    fi
    
    local line_count=$(wc -l < "$OUTPUT_FILE")
    log "Archivo generado con $line_count líneas"
    
    # Verificar variables críticas
    local critical_vars=("GYM_ENV" "GYM_SECRET_KEY" "GYM_DB_NAME" "BACKEND_PORT")
    local missing_vars=()
    
    for var in "${critical_vars[@]}"; do
        if ! grep -q "^${var}=" "$OUTPUT_FILE"; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        warning "Variables críticas faltantes: ${missing_vars[*]}"
        return 1
    fi
    
    success "Archivo de configuración validado"
    return 0
}

# Mostrar información del archivo generado
show_file_info() {
    echo ""
    echo "📊 Información del archivo generado:"
    echo "  Archivo: $OUTPUT_FILE"
    echo "  Tamaño: $(du -h "$OUTPUT_FILE" | cut -f1)"
    echo "  Líneas: $(wc -l < "$OUTPUT_FILE")"
    echo ""
    echo "🔧 Para usar este archivo:"
    echo "  export \$(grep -v '^#' $OUTPUT_FILE | xargs)"
    echo "  o"
    echo "  source $OUTPUT_FILE"
    echo ""
}

# Función principal
main() {
    log "🚀 Iniciando generación de configuración para ambiente: $ENVIRONMENT"
    
    check_config_dir
    create_combined_env
    validate_generated_file
    show_file_info
    
    success "Configuración completada para ambiente: $ENVIRONMENT"
}

# Ejecutar script principal
main "$@" 