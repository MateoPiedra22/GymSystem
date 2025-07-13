#!/bin/bash

# Módulo de Servicios para Scripts de Despliegue
# Inicia, verifica y muestra información de los servicios Docker

# Inicializar servicios
start_services() {
    log "🚀 Iniciando servicios..."
    
    # Iniciar servicios en orden
    start_core_services
    
    # Servicios adicionales según perfil
    start_additional_services
    
    success "Servicios iniciados"
}

# Iniciar servicios core
start_core_services() {
    log "🔧 Iniciando servicios core..."
    
    docker-compose up -d postgres redis
    sleep 5
    
    docker-compose up -d backend
    sleep 10
    
    docker-compose up -d frontend
    sleep 5
    
    debug "Servicios core iniciados"
}

# Iniciar servicios adicionales según perfil
start_additional_services() {
    log "🔧 Iniciando servicios adicionales..."
    
    if [[ "$COMPOSE_PROFILES" == *"production"* ]]; then
        docker-compose up -d nginx backup
        debug "Servicios de producción iniciados"
    fi
    
    if [[ "$COMPOSE_PROFILES" == *"monitoring"* ]]; then
        docker-compose up -d prometheus grafana
        debug "Servicios de monitoreo iniciados"
    fi
    
    if [[ "$COMPOSE_PROFILES" == *"tools"* ]]; then
        docker-compose up -d pgadmin
        debug "Servicios de herramientas iniciados"
    fi
}

# Verificar estado de servicios
check_services() {
    log "🔍 Verificando estado de servicios..."
    
    local failed_services=()
    
    # Verificar cada servicio
    while IFS= read -r service; do
        if [[ -n "$service" ]]; then
            if ! is_service_running "$service"; then
                failed_services+=("$service")
            fi
        fi
    done < <(docker-compose config --services)
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        handle_failed_services "${failed_services[@]}"
    fi
    
    success "Todos los servicios están funcionando"
}

# Verificar si un servicio está corriendo
is_service_running() {
    local service="$1"
    local status=$(docker-compose ps --services --filter "status=running" | grep "^${service}$" || true)
    [[ -n "$status" ]]
}

# Manejar servicios fallidos
handle_failed_services() {
    local failed_services=("$@")
    
    error "Servicios con problemas: ${failed_services[*]}"
    
    # Mostrar logs de servicios fallidos
    for service in "${failed_services[@]}"; do
        show_service_logs "$service"
    done
    
    # Mostrar estado general
    show_services_status
    
    exit 1
}

# Mostrar logs de un servicio
show_service_logs() {
    local service="$1"
    
    warning "Logs de $service:"
    docker-compose logs --tail=20 "$service" || true
    echo ""
}

# Mostrar estado general de servicios
show_services_status() {
    log "📊 Estado general de servicios:"
    docker-compose ps
}

# Mostrar información de servicios
show_service_info() {
    log "📊 Información de servicios:"
    
    echo ""
    echo "🌐 URLs de acceso:"
    show_access_urls
    
    echo ""
    echo "🗄️  Base de datos:"
    show_database_info
    
    echo ""
    echo "📁 Directorios de datos:"
    show_data_directories
}

# Mostrar URLs de acceso
show_access_urls() {
    case $ENVIRONMENT in
        "development")
            echo "  Frontend:    http://localhost:${FRONTEND_PORT:-3000}"
            echo "  Backend API: http://localhost:${BACKEND_PORT:-8000}"
            echo "  Docs API:    http://localhost:${BACKEND_PORT:-8000}/docs"
            echo "  pgAdmin:     http://localhost:5050"
            ;;
        "staging"|"production")
            echo "  Aplicación:  https://localhost (Puerto ${HTTPS_PORT:-443})"
            echo "  API:         https://localhost/api"
            echo "  Docs:        https://localhost/docs"
            
            if [[ "$COMPOSE_PROFILES" == *"monitoring"* ]]; then
                echo "  Prometheus:  http://localhost:${PROMETHEUS_PORT:-9090}"
                echo "  Grafana:     http://localhost:${GRAFANA_PORT:-3001}"
            fi
            ;;
    esac
}

# Mostrar información de base de datos
show_database_info() {
    echo "  Host: localhost:${GYM_DB_PORT:-5432}"
    echo "  Base: ${GYM_DB_NAME:-gym_management}"
    echo "  Usuario: ${GYM_DB_USER:-gymuser}"
}

# Mostrar directorios de datos
show_data_directories() {
    echo "  Logs:    ./logs"
    echo "  Uploads: ./uploads"
    echo "  Backups: ./backups"
    echo "  Data:    ./data"
}

# Verificar salud de servicios
check_services_health() {
    log "🏥 Verificando salud de servicios..."
    
    local health_checks=(
        "backend:http://localhost:${BACKEND_PORT:-8000}/health"
        "frontend:http://localhost:${FRONTEND_PORT:-3000}"
    )
    
    local failed_checks=()
    
    for check in "${health_checks[@]}"; do
        local service="${check%%:*}"
        local url="${check##*:}"
        
        if ! check_service_health "$url"; then
            failed_checks+=("$service")
        fi
    done
    
    if [[ ${#failed_checks[@]} -gt 0 ]]; then
        warning "Servicios con problemas de salud: ${failed_checks[*]}"
        return 1
    fi
    
    success "Todos los servicios están saludables"
    return 0
}

# Verificar salud de un servicio específico
check_service_health() {
    local url="$1"
    
    if curl -f -s "$url" &>/dev/null; then
        debug "Servicio saludable: $url"
        return 0
    else
        debug "Servicio no responde: $url"
        return 1
    fi
} 