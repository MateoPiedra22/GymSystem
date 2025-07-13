# Script de Respaldo Automático - Sistema de Gestión de Gimnasio v6.0

param(
    [string]$BackupPath = "backups",
    [switch]$IncludeLogs = $false
)

Write-Host "💾 Iniciando respaldo del sistema..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

# Crear directorio de respaldo si no existe
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupDir = "$BackupPath\backup_$timestamp"

if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Write-Host "✅ Directorio de respaldo creado: $backupDir" -ForegroundColor Green
}

# Respaldo de la base de datos
Write-Host "`n🗄️  Respaldando base de datos..." -ForegroundColor Yellow
try {
    docker-compose exec -T postgres pg_dump -U gym_user_prod gym_db_prod > "$backupDir\database_backup.sql"
    Write-Host "✅ Base de datos respaldada" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al respaldar base de datos" -ForegroundColor Red
}

# Respaldo de archivos subidos
Write-Host "📁 Respaldando archivos..." -ForegroundColor Yellow
try {
    if (Test-Path "uploads") {
        Copy-Item -Path "uploads" -Destination "$backupDir\uploads" -Recurse -Force
        Write-Host "✅ Archivos respaldados" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Error al respaldar archivos" -ForegroundColor Red
}

# Respaldo de logs (opcional)
if ($IncludeLogs) {
    Write-Host "📋 Respaldando logs..." -ForegroundColor Yellow
    try {
        if (Test-Path "logs") {
            Copy-Item -Path "logs" -Destination "$backupDir\logs" -Recurse -Force
            Write-Host "✅ Logs respaldados" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Error al respaldar logs" -ForegroundColor Red
    }
}

# Respaldo de configuración
Write-Host "⚙️  Respaldando configuración..." -ForegroundColor Yellow
try {
    Copy-Item -Path ".env" -Destination "$backupDir\env_backup.txt" -Force
    Copy-Item -Path "docker-compose.yml" -Destination "$backupDir\docker-compose_backup.yml" -Force
    Write-Host "✅ Configuración respaldada" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al respaldar configuración" -ForegroundColor Red
}

# Crear archivo de información del respaldo
$backupInfo = @"
Respaldo del Sistema de Gimnasio
Fecha: $(Get-Date)
Versión: 6.0
Contenido:
- Base de datos PostgreSQL
- Archivos subidos
- Configuración del sistema
$(if ($IncludeLogs) { "- Logs del sistema" })

Para restaurar:
1. Detener servicios: docker-compose down
2. Restaurar base de datos: docker-compose exec -T postgres psql -U gym_user_prod gym_db_prod < database_backup.sql
3. Restaurar archivos: Copiar carpeta uploads
4. Reiniciar servicios: docker-compose up -d
"@

$backupInfo | Out-File -FilePath "$backupDir\README.txt" -Encoding UTF8

# Comprimir respaldo
Write-Host "`n🗜️  Comprimiendo respaldo..." -ForegroundColor Yellow
try {
    $zipPath = "$BackupPath\backup_$timestamp.zip"
    Compress-Archive -Path "$backupDir\*" -DestinationPath $zipPath -Force
    Remove-Item -Path $backupDir -Recurse -Force
    Write-Host "✅ Respaldo comprimido: $zipPath" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al comprimir respaldo" -ForegroundColor Red
}

# Limpiar respaldos antiguos (mantener solo los últimos 7 días)
Write-Host "`n🧹 Limpiando respaldos antiguos..." -ForegroundColor Yellow
$oldBackups = Get-ChildItem -Path $BackupPath -Filter "backup_*.zip" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
foreach ($backup in $oldBackups) {
    Remove-Item $backup.FullName -Force
    Write-Host "🗑️  Eliminado: $($backup.Name)" -ForegroundColor Yellow
}

Write-Host "`n🎉 ¡Respaldo completado!" -ForegroundColor Green
Write-Host "📁 Ubicación: $zipPath" -ForegroundColor White
Write-Host "📊 Tamaño: $((Get-Item $zipPath).Length / 1MB) MB" -ForegroundColor White

Write-Host "`n💡 Consejos:" -ForegroundColor Yellow
Write-Host "   - Guarda el archivo de respaldo en un lugar seguro" -ForegroundColor White
Write-Host "   - Haz respaldos diarios automáticos" -ForegroundColor White
Write-Host "   - Prueba la restauración periódicamente" -ForegroundColor White 