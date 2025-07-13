#!/bin/bash

# Módulo de Ambiente para Scripts de Despliegue
# Configura variables de entorno y perfiles según el ambiente de despliegue

# Configurar variables de ambiente
setup_environment() {
    local env_file=".env.${ENVIRONMENT}"
    
    log "🔧 Configurando ambiente: $ENVIRONMENT"
    
    # Verificar que existe el archivo de configuración
    if [[ ! -f "$env_file" ]]; then
        if [[ -f "${env_file}.example" ]]; then
            warning "Archivo $env_file no encontrado, copiando desde example"
            cp "${env_file}.example" "$env_file"
            warning "IMPORTANTE: Edita $env_file con tus configuraciones específicas"
        else
            error "Archivo de configuración $env_file no encontrado"
            error "Crea el archivo $env_file basado en .env.example"
            exit 1
        fi
    fi
    
    # Crear directorios necesarios
    create_directories
    
    # Configurar permisos
    setup_permissions
    
    # Exportar variables
    export $(grep -v '^#' "$env_file" | xargs)
    export COMPOSE_FILE="docker-compose.yml"
    
    success "Ambiente configurado: $ENVIRONMENT"
}

# Crear directorios necesarios
create_directories() {
    log "📁 Creando directorios necesarios..."
    
    mkdir -p {logs,uploads,backups,data/{postgres,redis,prometheus,grafana}}
    
    # Crear directorios específicos por ambiente
    case $ENVIRONMENT in
        "production")
            mkdir -p {ssl,monitoring,backups/{daily,weekly,monthly}}
            ;;
        "staging")
            mkdir -p {ssl,backups/daily}
            ;;
        "development")
            mkdir -p {ssl,backups}
            ;;
    esac
    
    debug "Directorios creados"
}

# Configurar permisos
setup_permissions() {
    log "🔐 Configurando permisos..."
    
    # PostgreSQL
    sudo chown -R 999:999 data/postgres 2>/dev/null || true
    sudo chmod -R 750 data/postgres 2>/dev/null || true
    
    # Grafana
    sudo chown -R 472:472 data/grafana 2>/dev/null || true
    sudo chmod -R 750 data/grafana 2>/dev/null || true
    
    # Prometheus
    sudo chown -R 65534:65534 data/prometheus 2>/dev/null || true
    sudo chmod -R 750 data/prometheus 2>/dev/null || true
    
    # Logs
    chmod -R 755 logs 2>/dev/null || true
    
    # Uploads
    chmod -R 755 uploads 2>/dev/null || true
    
    debug "Permisos configurados"
}

# Configurar perfiles según ambiente
setup_profiles() {
    log "📋 Configurando perfiles para $ENVIRONMENT..."
    
    case $ENVIRONMENT in
        "development")
            export COMPOSE_PROFILES="tools"
            ;;
        "staging")
            export COMPOSE_PROFILES="tools,production"
            ;;
        "production")
            export COMPOSE_PROFILES="production,monitoring"
            ;;
        *)
            error "Ambiente no válido: $ENVIRONMENT"
            error "Ambientes válidos: development, staging, production"
            exit 1
            ;;
    esac
    
    success "Perfiles configurados: $COMPOSE_PROFILES"
} 