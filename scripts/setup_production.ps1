# Script de Configuración de Producción - Sistema de Gestión de Gimnasio v6.0
# Ejecutar como Administrador

param(
    [string]$GymName = "Mi Gimnasio",
    [string]$AdminEmail = "admin@gimnasio.com",
    [string]$AdminPassword = "admin123"
)

Write-Host "🏋️  Configurando Sistema de Gimnasio en Producción..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

# Verificar que Docker esté ejecutándose
Write-Host "`n🔍 Verificando Docker..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker está ejecutándose correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker no está ejecutándose" -ForegroundColor Red
    Write-Host "💡 Abre Docker Desktop y ejecuta este script nuevamente" -ForegroundColor Cyan
    exit 1
}

# Generar claves secretas seguras
Write-Host "`n🔐 Generando claves secretas..." -ForegroundColor Yellow
$secretKey = -join ((33..126) | Get-Random -Count 64 | ForEach-Object {[char]$_})
$jwtSecretKey = -join ((33..126) | Get-Random -Count 64 | ForEach-Object {[char]$_})
$backupKey = -join ((33..126) | Get-Random -Count 64 | ForEach-Object {[char]$_})

# Crear archivo .env para producción
Write-Host "📝 Creando archivo de configuración..." -ForegroundColor Yellow
$envContent = @"
# =============================================================================
# CONFIGURACIÓN DE PRODUCCIÓN - $GymName
# Sistema de Gestión de Gimnasio v6.0
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
GYM_ADMIN_EMAIL=$AdminEmail
GYM_ADMIN_PASSWORD=$AdminPassword
GYM_NAME="$GymName"
"@

# Guardar archivo .env
$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host "✅ Archivo .env creado correctamente" -ForegroundColor Green

# Crear directorios necesarios
Write-Host "`n📁 Creando directorios..." -ForegroundColor Yellow
$directories = @(
    "uploads",
    "logs",
    "backups",
    "data/postgres",
    "data/redis"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ Creado: $dir" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  Ya existe: $dir" -ForegroundColor Cyan
    }
}

# Construir y ejecutar los contenedores
Write-Host "`n🐳 Construyendo contenedores..." -ForegroundColor Yellow
try {
    docker-compose down
    docker-compose build --no-cache
    Write-Host "✅ Contenedores construidos correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al construir contenedores" -ForegroundColor Red
    exit 1
}

# Iniciar servicios
Write-Host "`n🚀 Iniciando servicios..." -ForegroundColor Yellow
try {
    docker-compose up -d
    Write-Host "✅ Servicios iniciados correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al iniciar servicios" -ForegroundColor Red
    exit 1
}

# Esperar a que los servicios estén listos
Write-Host "`n⏳ Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verificar estado de los servicios
Write-Host "`n🔍 Verificando estado de los servicios..." -ForegroundColor Yellow
docker-compose ps

# Crear usuario administrador
Write-Host "`n👤 Creando usuario administrador..." -ForegroundColor Yellow
try {
    docker-compose exec backend python scripts/create_admin.py
    Write-Host "✅ Usuario administrador creado" -ForegroundColor Green
} catch {
    Write-Host "⚠️  No se pudo crear el usuario administrador automáticamente" -ForegroundColor Yellow
    Write-Host "💡 Puedes crearlo manualmente más tarde" -ForegroundColor Cyan
}

# Mostrar información de acceso
Write-Host "`n🎉 ¡Configuración completada!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "📱 Aplicación Web: http://localhost:3000" -ForegroundColor White
Write-Host "🔧 API Backend: http://localhost:8000" -ForegroundColor White
Write-Host "📊 Grafana (Monitoreo): http://localhost:3001" -ForegroundColor White
Write-Host "📈 Prometheus (Métricas): http://localhost:9090" -ForegroundColor White
Write-Host "`n👤 Credenciales de Administrador:" -ForegroundColor Yellow
Write-Host "   Email: $AdminEmail" -ForegroundColor White
Write-Host "   Contraseña: $AdminPassword" -ForegroundColor White
Write-Host "`n💡 Comandos útiles:" -ForegroundColor Yellow
Write-Host "   Ver logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   Detener: docker-compose down" -ForegroundColor White
Write-Host "   Reiniciar: docker-compose restart" -ForegroundColor White
Write-Host "   Actualizar: docker-compose pull && docker-compose up -d" -ForegroundColor White

Write-Host "`n🔒 IMPORTANTE:" -ForegroundColor Red
Write-Host "   - Cambia las contraseñas por defecto" -ForegroundColor White
Write-Host "   - Configura un firewall" -ForegroundColor White
Write-Host "   - Haz respaldos regulares" -ForegroundColor White
Write-Host "   - Monitorea los logs regularmente" -ForegroundColor White 