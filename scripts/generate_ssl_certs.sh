#!/bin/bash

# =============================================================================
# SCRIPT DE GENERACIÓN DE CERTIFICADOS SSL
# Sistema de Gestión de Gimnasio v6.0
# =============================================================================

set -euo pipefail

# Configuración
DOMAIN=${1:-"localhost"}
EMAIL=${2:-"admin@${DOMAIN}"}
CERT_DIR="nginx/ssl"
KEY_SIZE=4096
DAYS_VALID=365

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funciones de logging
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Verificar prerrequisitos
check_prerequisites() {
    log "Verificando prerrequisitos..."
    
    if ! command -v openssl &> /dev/null; then
        error "OpenSSL no está instalado"
        exit 1
    fi
    
    if ! command -v mkcert &> /dev/null; then
        warn "mkcert no está instalado, usando OpenSSL directamente"
    fi
    
    log "✓ Prerrequisitos verificados"
}

# Crear directorio de certificados
create_cert_dir() {
    log "Creando directorio de certificados..."
    
    if [ ! -d "$CERT_DIR" ]; then
        mkdir -p "$CERT_DIR"
        chmod 700 "$CERT_DIR"
        log "✓ Directorio creado: $CERT_DIR"
    else
        log "✓ Directorio ya existe: $CERT_DIR"
    fi
}

# Generar certificado autofirmado con OpenSSL
generate_self_signed_cert() {
    log "Generando certificado autofirmado para $DOMAIN..."
    
    # Generar clave privada
    openssl genrsa -out "$CERT_DIR/private.key" $KEY_SIZE
    
    # Crear archivo de configuración para el certificado
    cat > "$CERT_DIR/openssl.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = MX
ST = Estado
L = Ciudad
O = GymSystem
OU = IT
CN = $DOMAIN

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = *.$DOMAIN
DNS.3 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
    
    # Generar certificado
    openssl req -new -x509 -key "$CERT_DIR/private.key" \
        -out "$CERT_DIR/certificate.crt" \
        -days $DAYS_VALID \
        -config "$CERT_DIR/openssl.conf"
    
    # Generar archivo de configuración para Nginx
    cat > "$CERT_DIR/ssl.conf" << EOF
# Configuración SSL para Nginx
ssl_certificate $CERT_DIR/certificate.crt;
ssl_certificate_key $CERT_DIR/private.key;

# Configuración de seguridad SSL
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# Configuración de seguridad adicional
ssl_stapling on;
ssl_stapling_verify on;
add_header Strict-Transport-Security "max-age=63072000" always;
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
EOF
    
    log "✓ Certificado autofirmado generado"
}

# Generar certificado con Let's Encrypt (si está disponible)
generate_letsencrypt_cert() {
    if command -v certbot &> /dev/null; then
        log "Generando certificado con Let's Encrypt..."
        
        # Verificar que el dominio sea público
        if [[ "$DOMAIN" == "localhost" || "$DOMAIN" == "127.0.0.1" ]]; then
            warn "Let's Encrypt no funciona con localhost, usando certificado autofirmado"
            return
        fi
        
        # Generar certificado con certbot
        certbot certonly --standalone \
            --email "$EMAIL" \
            --agree-tos \
            --no-eff-email \
            --domains "$DOMAIN" \
            --cert-path "$CERT_DIR/certificate.crt" \
            --key-path "$CERT_DIR/private.key"
        
        log "✓ Certificado Let's Encrypt generado"
    else
        warn "certbot no está instalado, usando certificado autofirmado"
    fi
}

# Verificar certificado
verify_cert() {
    log "Verificando certificado..."
    
    if [ -f "$CERT_DIR/certificate.crt" ] && [ -f "$CERT_DIR/private.key" ]; then
        # Verificar que el certificado y la clave coincidan
        CERT_MODULUS=$(openssl x509 -noout -modulus -in "$CERT_DIR/certificate.crt" | openssl md5)
        KEY_MODULUS=$(openssl rsa -noout -modulus -in "$CERT_DIR/private.key" | openssl md5)
        
        if [ "$CERT_MODULUS" = "$KEY_MODULUS" ]; then
            log "✓ Certificado y clave privada coinciden"
        else
            error "✗ Certificado y clave privada no coinciden"
            exit 1
        fi
        
        # Mostrar información del certificado
        log "Información del certificado:"
        openssl x509 -in "$CERT_DIR/certificate.crt" -text -noout | grep -E "(Subject:|Not Before|Not After|DNS:|IP Address:)"
        
    else
        error "✗ Archivos de certificado no encontrados"
        exit 1
    fi
}

# Configurar permisos
set_permissions() {
    log "Configurando permisos..."
    
    chmod 600 "$CERT_DIR/private.key"
    chmod 644 "$CERT_DIR/certificate.crt"
    chmod 644 "$CERT_DIR/ssl.conf"
    
    log "✓ Permisos configurados"
}

# Función principal
main() {
    log "🚀 Iniciando generación de certificados SSL para $DOMAIN"
    
    check_prerequisites
    create_cert_dir
    
    # Intentar Let's Encrypt primero, fallback a autofirmado
    if [[ "$DOMAIN" != "localhost" && "$DOMAIN" != "127.0.0.1" ]]; then
        generate_letsencrypt_cert
    fi
    
    # Si no se generó con Let's Encrypt, usar autofirmado
    if [ ! -f "$CERT_DIR/certificate.crt" ]; then
        generate_self_signed_cert
    fi
    
    verify_cert
    set_permissions
    
    log "🎉 Certificados SSL generados exitosamente"
    log "📁 Ubicación: $CERT_DIR"
    log "🔧 Configuración Nginx: $CERT_DIR/ssl.conf"
    
    if [[ "$DOMAIN" == "localhost" || "$DOMAIN" == "127.0.0.1" ]]; then
        warn "⚠️  Certificado autofirmado generado para desarrollo local"
        warn "   Para producción, configure un dominio real y use Let's Encrypt"
    fi
}

# Mostrar ayuda
show_help() {
    cat << EOF
Script de Generación de Certificados SSL - Sistema de Gimnasio v6

USO: $0 [DOMINIO] [EMAIL]
ARGUMENTOS:
    DOMINIO    Dominio para el certificado (default: localhost)
    EMAIL      Email para Let's Encrypt (default: admin@DOMINIO)

EJEMPLOS:
    $0                              # localhost (autofirmado)
    $0 example.com                  # Dominio público
    $0 example.com admin@example.com # Con email específico

PREREQUISITOS:
    - OpenSSL instalado
    - certbot (opcional, para Let's Encrypt)
    - mkcert (opcional, para desarrollo local)
EOF
}

# Manejar argumentos
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

# Ejecutar función principal
main "$@" 