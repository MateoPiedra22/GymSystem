#!/bin/bash

# Módulo de Prerequisitos para Scripts de Despliegue
# Verifica que todas las herramientas necesarias estén instaladas y funcionando

# Verificar prerequisitos
check_prerequisites() {
    log "🔍 Verificando prerequisitos..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado"
        error "Instala Docker desde: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está instalado"
        error "Instala Docker Compose desde: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Verificar que Docker esté corriendo
    if ! docker info &> /dev/null; then
        error "Docker no está corriendo"
        error "Inicia el servicio de Docker"
        exit 1
    fi
    
    # Verificar versión de Docker
    local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    info "Docker versión: $docker_version"
    
    # Verificar versión de Docker Compose
    local compose_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    info "Docker Compose versión: $compose_version"
    
    # Verificar espacio en disco
    check_disk_space
    
    success "Prerequisitos verificados"
}

# Verificar espacio en disco
check_disk_space() {
    local required_space=5  # GB requeridos
    local available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    
    if [[ $available_space -lt $required_space ]]; then
        warning "Espacio en disco bajo: ${available_space}GB disponible, ${required_space}GB recomendados"
    else
        debug "Espacio en disco OK: ${available_space}GB disponible"
    fi
} 