#!/bin/bash

# Módulo de Validación para Scripts de Despliegue
# Valida configuraciones de producción y certificados SSL

# Validar configuración de producción
validate_production_config() {
    if [[ "$ENVIRONMENT" != "production" ]]; then
        return 0
    fi
    
    log "🔒 Validando configuración de producción..."
    
    local env_file=".env.${ENVIRONMENT}"
    local errors=0
    
    # Verificar claves de seguridad
    if ! validate_security_keys "$env_file"; then
        errors=$((errors + 1))
    fi
    
    # Verificar certificados SSL
    if ! validate_ssl_certs; then
        errors=$((errors + 1))
    fi
    
    # Verificar configuraciones críticas
    if ! validate_critical_configs "$env_file"; then
        errors=$((errors + 1))
    fi
    
    if [[ $errors -gt 0 ]]; then
        error "Errores de configuración detectados. Corrige antes de continuar."
        exit 1
    fi
    
    success "Configuración de producción validada"
}

# Validar claves de seguridad
validate_security_keys() {
    local env_file="$1"
    
    log "🔑 Validando claves de seguridad..."
    
    local errors=0
    
    # Verificar valores por defecto
    if grep -q "CAMBIAR" "$env_file"; then
        error "Hay valores por defecto que deben cambiarse en $env_file"
        errors=$((errors + 1))
    fi
    
    # Verificar SECRET_KEY
    if grep -q "SECRET_KEY=.*default.*" "$env_file" || grep -q "SECRET_KEY=.*changeme.*" "$env_file"; then
        error "SECRET_KEY debe ser cambiada en $env_file"
        errors=$((errors + 1))
    fi
    
    # Verificar JWT_SECRET_KEY
    if grep -q "JWT_SECRET_KEY=.*default.*" "$env_file" || grep -q "JWT_SECRET_KEY=.*changeme.*" "$env_file"; then
        error "JWT_SECRET_KEY debe ser cambiada en $env_file"
        errors=$((errors + 1))
    fi
    
    # Verificar contraseñas de base de datos
    if grep -q "GYM_DB_PASSWORD=.*password.*" "$env_file" || grep -q "GYM_DB_PASSWORD=.*changeme.*" "$env_file"; then
        error "GYM_DB_PASSWORD debe ser cambiada en $env_file"
        errors=$((errors + 1))
    fi
    
    if [[ $errors -gt 0 ]]; then
        return 1
    fi
    
    debug "Claves de seguridad validadas"
    return 0
}

# Validar configuraciones críticas
validate_critical_configs() {
    local env_file="$1"
    
    log "⚙️  Validando configuraciones críticas..."
    
    local errors=0
    
    # Verificar DEBUG en producción
    if grep -q "DEBUG=true" "$env_file"; then
        error "DEBUG debe ser false en producción"
        errors=$((errors + 1))
    fi
    
    # Verificar ALLOWED_HOSTS
    if ! grep -q "ALLOWED_HOSTS=.*" "$env_file"; then
        error "ALLOWED_HOSTS debe estar configurado"
        errors=$((errors + 1))
    fi
    
    # Verificar CORS_ORIGINS
    if ! grep -q "CORS_ORIGINS=.*" "$env_file"; then
        error "CORS_ORIGINS debe estar configurado"
        errors=$((errors + 1))
    fi
    
    # Verificar configuración de logs
    if ! grep -q "LOG_LEVEL=.*" "$env_file"; then
        warning "LOG_LEVEL no está configurado, usando INFO por defecto"
    fi
    
    if [[ $errors -gt 0 ]]; then
        return 1
    fi
    
    debug "Configuraciones críticas validadas"
    return 0
}

# Validar configuración de staging
validate_staging_config() {
    if [[ "$ENVIRONMENT" != "staging" ]]; then
        return 0
    fi
    
    log "🔍 Validando configuración de staging..."
    
    local env_file=".env.${ENVIRONMENT}"
    local warnings=0
    
    # Verificar que no esté en modo debug
    if grep -q "DEBUG=true" "$env_file"; then
        warning "DEBUG está habilitado en staging"
        warnings=$((warnings + 1))
    fi
    
    # Verificar configuración de base de datos
    if ! validate_database_config "$env_file"; then
        warnings=$((warnings + 1))
    fi
    
    if [[ $warnings -gt 0 ]]; then
        warning "Advertencias en configuración de staging"
    fi
    
    success "Configuración de staging validada"
}

# Validar configuración de base de datos
validate_database_config() {
    local env_file="$1"
    
    log "🗄️  Validando configuración de base de datos..."
    
    local errors=0
    
    # Verificar variables de base de datos
    local required_vars=("GYM_DB_HOST" "GYM_DB_PORT" "GYM_DB_NAME" "GYM_DB_USER" "GYM_DB_PASSWORD")
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$env_file"; then
            error "Variable $var no está configurada"
            errors=$((errors + 1))
        fi
    done
    
    # Verificar configuración de Redis
    if ! grep -q "REDIS_URL=" "$env_file"; then
        warning "REDIS_URL no está configurado"
    fi
    
    if [[ $errors -gt 0 ]]; then
        return 1
    fi
    
    debug "Configuración de base de datos validada"
    return 0
}

# Validar configuración de desarrollo
validate_development_config() {
    if [[ "$ENVIRONMENT" != "development" ]]; then
        return 0
    fi
    
    log "🔧 Validando configuración de desarrollo..."
    
    local env_file=".env.${ENVIRONMENT}"
    
    # Verificar que DEBUG esté habilitado
    if ! grep -q "DEBUG=true" "$env_file"; then
        warning "DEBUG no está habilitado en desarrollo"
    fi
    
    # Verificar configuración de base de datos
    validate_database_config "$env_file" || warning "Problemas en configuración de base de datos"
    
    success "Configuración de desarrollo validada"
}

# Validar configuración general
validate_general_config() {
    log "🔍 Validando configuración general..."
    
    local env_file=".env.${ENVIRONMENT}"
    
    # Verificar que el archivo existe
    if [[ ! -f "$env_file" ]]; then
        error "Archivo de configuración $env_file no encontrado"
        return 1
    fi
    
    # Verificar sintaxis básica
    if ! validate_env_syntax "$env_file"; then
        error "Errores de sintaxis en $env_file"
        return 1
    fi
    
    debug "Configuración general validada"
    return 0
}

# Validar sintaxis del archivo .env
validate_env_syntax() {
    local env_file="$1"
    
    # Verificar líneas mal formateadas
    local malformed_lines=$(grep -E "^[^#].*=.*[[:space:]]" "$env_file" || true)
    
    if [[ -n "$malformed_lines" ]]; then
        error "Líneas mal formateadas en $env_file:"
        echo "$malformed_lines"
        return 1
    fi
    
    return 0
} 