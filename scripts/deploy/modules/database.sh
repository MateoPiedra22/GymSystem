#!/bin/bash

# Módulo de Base de Datos para Scripts de Despliegue
# Inicializa y verifica la conexión a PostgreSQL

# Inicializar base de datos
init_database() {
    log "🗄️  Inicializando base de datos..."
    
    # Esperar a que PostgreSQL esté listo
    docker-compose up -d postgres redis
    
    # Esperar conexión
    wait_for_postgres
    
    # Verificar conexión
    test_database_connection
    
    success "Base de datos inicializada"
}

# Esperar a que PostgreSQL esté listo
wait_for_postgres() {
    local max_attempts=30
    local attempt=1
    
    log "⏳ Esperando que PostgreSQL esté listo..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose exec -T postgres pg_isready -U "${GYM_DB_USER:-gymuser}" &>/dev/null; then
            debug "PostgreSQL está listo"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "PostgreSQL no responde después de $max_attempts intentos"
            error "Verifica los logs: docker-compose logs postgres"
            exit 1
        fi
        
        log "Esperando PostgreSQL... (intento $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
}

# Verificar conexión a la base de datos
test_database_connection() {
    log "🔍 Verificando conexión a la base de datos..."
    
    # Verificar que la base de datos existe
    if ! docker-compose exec -T postgres psql -U "${GYM_DB_USER:-gymuser}" -d "${GYM_DB_NAME:-gym_management}" -c "SELECT 1;" &>/dev/null; then
        warning "Base de datos ${GYM_DB_NAME:-gym_management} no existe, creándola..."
        create_database
    fi
    
    # Verificar tablas principales
    check_database_tables
    
    debug "Conexión a base de datos verificada"
}

# Crear base de datos si no existe
create_database() {
    log "📝 Creando base de datos..."
    
    docker-compose exec -T postgres psql -U "${GYM_DB_USER:-gymuser}" -c "CREATE DATABASE ${GYM_DB_NAME:-gym_management};" 2>/dev/null || warning "Error al crear base de datos"
    
    debug "Base de datos creada"
}

# Verificar tablas principales
check_database_tables() {
    log "📊 Verificando tablas principales..."
    
    local required_tables=("usuarios" "empleados" "clases" "asistencias" "pagos")
    local missing_tables=()
    
    for table in "${required_tables[@]}"; do
        if ! docker-compose exec -T postgres psql -U "${GYM_DB_USER:-gymuser}" -d "${GYM_DB_NAME:-gym_management}" -c "SELECT 1 FROM $table LIMIT 1;" &>/dev/null; then
            missing_tables+=("$table")
        fi
    done
    
    if [[ ${#missing_tables[@]} -gt 0 ]]; then
        warning "Tablas faltantes: ${missing_tables[*]}"
        warning "Ejecuta las migraciones: python init_database.py"
    else
        debug "Todas las tablas principales existen"
    fi
}

# Verificar estado de la base de datos
check_database_health() {
    log "🏥 Verificando salud de la base de datos..."
    
    # Verificar conexión
    if ! docker-compose exec -T postgres pg_isready -U "${GYM_DB_USER:-gymuser}" &>/dev/null; then
        error "PostgreSQL no está respondiendo"
        return 1
    fi
    
    # Verificar espacio en disco
    check_database_disk_space
    
    # Verificar conexiones activas
    check_active_connections
    
    success "Base de datos saludable"
    return 0
}

# Verificar espacio en disco de la base de datos
check_database_disk_space() {
    local disk_usage=$(docker-compose exec -T postgres psql -U "${GYM_DB_USER:-gymuser}" -d "${GYM_DB_NAME:-gym_management}" -c "SELECT pg_size_pretty(pg_database_size('${GYM_DB_NAME:-gym_management}'));" 2>/dev/null | tail -n 1 | xargs)
    
    if [[ -n "$disk_usage" ]]; then
        debug "Tamaño de base de datos: $disk_usage"
    fi
}

# Verificar conexiones activas
check_active_connections() {
    local active_connections=$(docker-compose exec -T postgres psql -U "${GYM_DB_USER:-gymuser}" -d "${GYM_DB_NAME:-gym_management}" -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | tail -n 1 | xargs)
    
    if [[ -n "$active_connections" ]] && [[ "$active_connections" -gt 0 ]]; then
        debug "Conexiones activas: $active_connections"
    fi
} 