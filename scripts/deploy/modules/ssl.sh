#!/bin/bash

# Módulo SSL para Scripts de Despliegue
# Genera certificados SSL para desarrollo y valida certificados para producción

# Generar certificados SSL para desarrollo
generate_ssl_certs() {
    if [[ "$ENVIRONMENT" != "development" ]]; then
        return 0
    fi
    
    log "🔐 Generando certificados SSL para desarrollo..."
    
    mkdir -p nginx/ssl
    
    # Generar certificado y clave si no existen
    if [[ ! -f nginx/ssl/cert.pem ]] || [[ ! -f nginx/ssl/key.pem ]]; then
        generate_self_signed_cert
    fi
    
    # Generar dhparam si no existe
    if [[ ! -f nginx/ssl/dhparam.pem ]]; then
        generate_dhparam
    fi
    
    success "Certificados SSL configurados"
}

# Generar certificado autofirmado
generate_self_signed_cert() {
    log "📜 Generando certificado autofirmado..."
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=MX/ST=State/L=City/O=Gym System/CN=localhost" \
        2>/dev/null || warning "No se pudieron generar certificados SSL"
    
    if [[ -f nginx/ssl/cert.pem ]] && [[ -f nginx/ssl/key.pem ]]; then
        debug "Certificado autofirmado generado"
    else
        warning "Error al generar certificado autofirmado"
    fi
}

# Generar parámetros Diffie-Hellman
generate_dhparam() {
    log "🔑 Generando parámetros Diffie-Hellman..."
    
    openssl dhparam -out nginx/ssl/dhparam.pem 2048 2>/dev/null || warning "No se pudo generar dhparam"
    
    if [[ -f nginx/ssl/dhparam.pem ]]; then
        debug "Parámetros DH generados"
    else
        warning "Error al generar parámetros DH"
    fi
}

# Validar certificados SSL para producción
validate_ssl_certs() {
    if [[ "$ENVIRONMENT" != "production" ]]; then
        return 0
    fi
    
    log "🔒 Validando certificados SSL para producción..."
    
    local cert_file="nginx/ssl/cert.pem"
    local key_file="nginx/ssl/key.pem"
    local errors=0
    
    # Verificar que existan los archivos
    if [[ ! -f "$cert_file" ]]; then
        error "Certificado SSL no encontrado: $cert_file"
        errors=$((errors + 1))
    fi
    
    if [[ ! -f "$key_file" ]]; then
        error "Clave privada SSL no encontrada: $key_file"
        errors=$((errors + 1))
    fi
    
    # Verificar formato del certificado
    if [[ -f "$cert_file" ]]; then
        if ! openssl x509 -in "$cert_file" -text -noout &>/dev/null; then
            error "Certificado SSL inválido: $cert_file"
            errors=$((errors + 1))
        else
            debug "Certificado SSL válido"
        fi
    fi
    
    # Verificar formato de la clave
    if [[ -f "$key_file" ]]; then
        if ! openssl rsa -in "$key_file" -check &>/dev/null; then
            error "Clave privada SSL inválida: $key_file"
            errors=$((errors + 1))
        else
            debug "Clave privada SSL válida"
        fi
    fi
    
    # Verificar fecha de expiración
    if [[ -f "$cert_file" ]]; then
        local expiry_date=$(openssl x509 -in "$cert_file" -enddate -noout | cut -d= -f2)
        local expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null || echo "0")
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [[ $days_until_expiry -lt 30 ]]; then
            warning "Certificado SSL expira en $days_until_expiry días"
        else
            debug "Certificado SSL válido por $days_until_expiry días"
        fi
    fi
    
    if [[ $errors -gt 0 ]]; then
        error "Errores en certificados SSL detectados"
        return 1
    fi
    
    success "Certificados SSL validados"
    return 0
} 