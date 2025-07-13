# Script para crear archivo .env - Sistema de Gimnasio
# Este script genera la configuración automáticamente

try {
    # Generar claves secretas seguras
    $secretKey = -join ((33..126) | Get-Random -Count 64 | ForEach-Object {[char]$_})
    $jwtSecretKey = -join ((33..126) | Get-Random -Count 64 | ForEach-Object {[char]$_})
    $backupKey = -join ((33..126) | Get-Random -Count 64 | ForEach-Object {[char]$_})
    
    # Crear contenido del archivo .env
    $envContent = @"
# =============================================================================
# CONFIGURACION AUTOMATICA - SISTEMA DE GIMNASIO
# =============================================================================

# Configuración General
GYM_ENV=production
GYM_DEBUG=false
BUILD_TARGET=production
NODE_ENV=production

# Configuración de Idioma y Zona Horaria
TZ=America/Mexico_City
LANG=es_ES.UTF-8
LC_ALL=es_ES.UTF-8

# Configuración de Logs
LOG_LEVEL=info
GYM_AUDIT_LOG=true

# Configuración de Base de Datos PostgreSQL
GYM_DB_NAME=gym_db_prod
GYM_DB_USER=gym_user_prod
GYM_DB_PASSWORD=gym_secure_password_2024!
GYM_DB_PORT=5432
GYM_DB_SSL_MODE=prefer

# Configuración de Redis
GYM_REDIS_PASSWORD=redis_secure_password_2024!
REDIS_PORT=6379

# Configuración del Backend
BACKEND_PORT=8000
BACKEND_WORKERS=4
BACKEND_MEMORY_LIMIT=1g
GYM_METRICS_PORT=9000

# Configuración del Frontend
FRONTEND_PORT=3000
FRONTEND_MEMORY_LIMIT=512m
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Configuración de Nginx
HTTP_PORT=80
HTTPS_PORT=443

# Claves Secretas Generadas Automáticamente
GYM_SECRET_KEY=$secretKey
GYM_JWT_SECRET_KEY=$jwtSecretKey
GYM_BACKUP_KEY=$backupKey

# Configuración de Seguridad
GYM_FORCE_HTTPS=false
GYM_SECURE_COOKIES=false
GYM_SAMESITE_COOKIES=lax
GYM_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100
GYM_CORS_ORIGINS=["http://localhost:3000","http://192.168.1.100:3000"]
GYM_SECURITY_HEADERS=true
GYM_RATE_LIMITING=true
GYM_RATE_LIMIT=100
GYM_MAX_LOGIN_ATTEMPTS=5
GYM_LOCKOUT_TIME=15
GYM_SESSION_TIMEOUT=60

# Configuración de Archivos
GYM_MAX_UPLOAD_SIZE=10485760
GYM_MAX_REQUEST_SIZE=20971520
GYM_ALLOWED_EXTENSIONS=["jpg","jpeg","png","pdf","doc","docx"]

# Configuración de Monitoreo
GYM_PROMETHEUS_METRICS=true
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
GRAFANA_USERNAME=admin
GRAFANA_PASSWORD=gym_admin_password_2024!

# Configuración del Administrador
GYM_ADMIN_EMAIL=admin@migimnasio.com
GYM_ADMIN_PASSWORD=admin123
GYM_NAME=Mi Gimnasio
"@
    
    # Guardar archivo .env
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-Host "Archivo .env creado correctamente" -ForegroundColor Green
    exit 0
    
} catch {
    Write-Host "Error al crear archivo .env: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 