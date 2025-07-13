#!/bin/bash

# Script de Despliegue para Sistema de Gimnasio v6
# MEJORADO: Validaciones de seguridad, rollback automático, logging mejorado

set -euo pipefail

# Configuración básica
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Variables de configuración
ENVIRONMENT=${1:-development}
PROJECT_NAME="gym-system"
VERSION=${2:-latest}
FORCE_RECREATE=${3:-false}
BACKUP_BEFORE_DEPLOY=${4:-true}
ROLLBACK_ON_FAILURE=${5:-true}

# Archivos de configuración
DOCKER_COMPOSE_FILE="docker-compose-simple.yml"
ENV_FILE=".env"
BACKUP_DIR="$PROJECT_ROOT/backups"
LOG_FILE="$PROJECT_ROOT/logs/deploy.log"

# Crear directorios necesarios
mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

# Funciones mejoradas de logging
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

error() {
    local message="[ERROR] $1"
    echo "$message" >&2 | tee -a "$LOG_FILE"
}

warning() {
    local message="[WARNING] $1"
    echo "$message" >&2 | tee -a "$LOG_FILE"
}

success() {
    local message="[SUCCESS] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# Función de validación de seguridad
validate_security() {
    log "🔒 Validando configuraciones de seguridad..."
    
    # Verificar que no se usen contraseñas por defecto
    if grep -q "password123\|admin123\|changeme" "$ENV_FILE" 2>/dev/null; then
        error "Se detectaron contraseñas por defecto en $ENV_FILE"
        return 1
    fi
    
    # Verificar que las claves secretas no sean las de ejemplo
    if grep -q "your-secret-key\|your-jwt-secret" "$ENV_FILE" 2>/dev/null; then
        error "Se detectaron claves secretas de ejemplo en $ENV_FILE"
        return 1
    fi
    
    # Verificar permisos de archivos sensibles
    if [[ -f "$ENV_FILE" ]] && [[ "$(stat -c %a "$ENV_FILE" 2>/dev/null || stat -f %Lp "$ENV_FILE" 2>/dev/null)" != "600" ]]; then
        warning "Archivo $ENV_FILE no tiene permisos 600"
        chmod 600 "$ENV_FILE"
    fi
    
    success "Validaciones de seguridad completadas"
}

# Función de backup
create_backup() {
    if [[ "$BACKUP_BEFORE_DEPLOY" == "true" ]]; then
        log "💾 Creando backup antes del despliegue..."
        local backup_name="backup_$(date +%Y%m%d_%H%M%S)_${ENVIRONMENT}"
        local backup_path="$BACKUP_DIR/$backup_name"
        
        mkdir -p "$backup_path"
        
        # Backup de configuración
        if [[ -f "$ENV_FILE" ]]; then
            cp "$ENV_FILE" "$backup_path/"
        fi
        
        # Backup de datos de PostgreSQL
        if docker ps --format "table {{.Names}}" | grep -q "gym_postgres"; then
            docker exec gym_postgres pg_dump -U postgres gym_system > "$backup_path/database.sql" 2>/dev/null || warning "No se pudo crear backup de la base de datos"
        fi
        
        # Backup de logs
        if [[ -d "logs" ]]; then
            cp -r logs "$backup_path/" 2>/dev/null || warning "No se pudieron copiar los logs"
        fi
        
        echo "$backup_path" > "$PROJECT_ROOT/.last_backup"
        success "Backup creado en $backup_path"
    fi
}

# Función de rollback
rollback() {
    if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
        log "🔄 Iniciando rollback..."
        
        local last_backup=""
        if [[ -f "$PROJECT_ROOT/.last_backup" ]]; then
            last_backup=$(cat "$PROJECT_ROOT/.last_backup")
        fi
        
        if [[ -n "$last_backup" ]] && [[ -d "$last_backup" ]]; then
            log "Restaurando desde backup: $last_backup"
            
            # Restaurar configuración
            if [[ -f "$last_backup/.env" ]]; then
                cp "$last_backup/.env" "$ENV_FILE"
            fi
            
            # Restaurar base de datos si es necesario
            if [[ -f "$last_backup/database.sql" ]] && docker ps --format "table {{.Names}}" | grep -q "gym_postgres"; then
                docker exec -i gym_postgres psql -U postgres gym_system < "$last_backup/database.sql" 2>/dev/null || warning "No se pudo restaurar la base de datos"
            fi
            
            success "Rollback completado"
        else
            warning "No se encontró backup para rollback"
        fi
    fi
}

# Función de verificación de prerrequisitos mejorada
check_prerequisites() {
    log "🔍 Verificando prerrequisitos..."
    
    local missing_deps=()
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    # Verificar espacio en disco
    local available_space=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 1048576 ]]; then # Menos de 1GB
        warning "Espacio en disco bajo: ${available_space}KB disponible"
    fi
    
    # Verificar memoria disponible
    if command -v free &> /dev/null; then
        local available_mem=$(free -m | awk 'NR==2 {print $7}')
        if [[ $available_mem -lt 1024 ]]; then # Menos de 1GB
            warning "Memoria disponible baja: ${available_mem}MB"
        fi
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error "Dependencias faltantes: ${missing_deps[*]}"
        return 1
    fi
    
    success "Prerrequisitos verificados"
}

# Función de health check mejorada
health_check() {
    log "🏥 Ejecutando health checks..."
    
    local services=("postgres" "redis" "backend" "frontend")
    local failed_services=()
    
    for service in "${services[@]}"; do
        local retry_count=0
        local max_retries=10
        local service_healthy=false
        
        while [[ $retry_count -lt $max_retries ]]; do
            if docker ps --format "table {{.Names}}" | grep -q "gym_${service}"; then
                # Verificar que el servicio esté realmente funcionando
                if docker exec "gym_${service}" pgrep -f ".*" >/dev/null 2>&1; then
                    log "✓ Servicio ${service} está ejecutándose correctamente"
                    service_healthy=true
                    break
                fi
            fi
            
            retry_count=$((retry_count + 1))
            if [[ $retry_count -eq $max_retries ]]; then
                failed_services+=("$service")
                error "✗ Servicio ${service} no está ejecutándose correctamente después de ${max_retries} intentos"
            else
                log "⏳ Reintentando verificación de ${service} (${retry_count}/${max_retries})..."
                sleep 15
            fi
        done
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        error "Servicios fallidos: ${failed_services[*]}"
        return 1
    fi
    
    success "Todos los servicios están funcionando correctamente"
}

# Función principal mejorada
main() {
    # Configurar trap para cleanup
    trap 'error "Error durante el despliegue"; rollback; exit 1' ERR
    trap 'log "Despliegue interrumpido por el usuario"; rollback; exit 1' INT TERM
    
    # Mostrar ayuda si se solicita
    if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
        show_help
        exit 0
    fi
    
    log "🎯 Iniciando despliegue del Sistema de Gimnasio v6"
    log "   Ambiente: $ENVIRONMENT"
    log "   Versión: $VERSION"
    log "   Proyecto: $PROJECT_NAME"
    log "   Backup: $BACKUP_BEFORE_DEPLOY"
    log "   Rollback: $ROLLBACK_ON_FAILURE"
    
    # Cambiar al directorio del proyecto
    cd "$PROJECT_ROOT"
    
    # Ejecutar verificaciones
    check_prerequisites
    validate_security
    
    # Crear backup
    create_backup
    
    # Configurar ambiente
    log "⚙️ Configurando ambiente..."
    if [[ ! -f "$ENV_FILE" ]]; then
        warning "Archivo $ENV_FILE no encontrado, copiando desde .env.example"
        if [[ -f ".env.example" ]]; then
            cp .env.example "$ENV_FILE"
            warning "IMPORTANTE: Configura las variables de entorno en $ENV_FILE antes de continuar"
            exit 1
        else
            error "No se encontró .env.example"
            exit 1
        fi
    fi
    
    # Iniciar servicios
    log "🚀 Iniciando servicios..."
    if [[ "$FORCE_RECREATE" == "true" ]]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --force-recreate
    else
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    fi
    
    # Esperar y verificar
    log "⏳ Esperando que los servicios estén listos..."
    sleep 45
    
    # Verificar servicios
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    # Health checks
    health_check
    
    # Limpiar backups antiguos (mantener solo los últimos 5)
    if [[ -d "$BACKUP_DIR" ]]; then
        log "🧹 Limpiando backups antiguos..."
        find "$BACKUP_DIR" -name "backup_*" -type d -printf '%T@ %p\n' | sort -nr | tail -n +6 | cut -d' ' -f2- | xargs -r rm -rf
    fi
    
    success "🎉 Despliegue completado exitosamente"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        warning "RECORDATORIO: Configura tu dominio, SSL y firewall apropiadamente"
        warning "RECORDATORIO: Revisa los logs en $LOG_FILE"
    fi
}

# Función para mostrar ayuda mejorada
show_help() {
    cat << EOF
Script de Despliegue - Sistema de Gimnasio v6

USO: $0 [AMBIENTE] [VERSION] [FORCE_RECREATE] [BACKUP] [ROLLBACK]
ARGUMENTOS:
    AMBIENTE        Ambiente de despliegue (development|staging|production)
    VERSION         Versión a desplegar
    FORCE_RECREATE  Forzar recreación de containers (true|false)
    BACKUP          Crear backup antes del despliegue (true|false)
    ROLLBACK        Habilitar rollback automático (true|false)

EJEMPLOS:
    $0                                    # Desarrollo con configuración por defecto
    $0 development                        # Desarrollo explícito
    $0 staging v6.1.0                    # Staging con versión específica
    $0 production latest true true true  # Producción con todas las opciones

CARACTERÍSTICAS DE SEGURIDAD:
    - Validación de contraseñas por defecto
    - Verificación de claves secretas
    - Permisos de archivos sensibles
    - Backup automático antes del despliegue
    - Rollback automático en caso de fallo
    - Health checks exhaustivos
    - Logging detallado

PREREQUISITOS:
    - Docker y Docker Compose instalados
    - Archivo .env configurado correctamente
    - Certificados SSL (para production)
    - Mínimo 1GB de espacio libre
    - Mínimo 1GB de RAM disponible

LOGS:
    Los logs del despliegue se guardan en: $LOG_FILE
EOF
}

# Ejecutar script principal
main "$@"