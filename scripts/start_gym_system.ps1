# Script de Inicio del Sistema de Gimnasio
# Ejecutar este script para iniciar todos los servicios

Write-Host "🏋️  Iniciando Sistema de Gimnasio..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

# Verificar que Docker esté ejecutándose
Write-Host "`n🔍 Verificando Docker..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker está ejecutándose" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker no está ejecutándose" -ForegroundColor Red
    Write-Host "💡 Abre Docker Desktop y ejecuta este script nuevamente" -ForegroundColor Cyan
    exit 1
}

# Navegar al directorio del proyecto
$projectDir = Split-Path -Parent $PSScriptRoot
Set-Location $projectDir

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
Start-Sleep -Seconds 15

# Verificar estado
Write-Host "`n🔍 Verificando estado de los servicios..." -ForegroundColor Yellow
docker-compose ps

Write-Host "`n🎉 ¡Sistema iniciado!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "📱 Aplicación Web: http://localhost:3000" -ForegroundColor White
Write-Host "🔧 API Backend: http://localhost:8000" -ForegroundColor White
Write-Host "📊 Monitoreo: http://localhost:3001" -ForegroundColor White

Write-Host "`n💡 Para detener el sistema: .\scripts\stop_gym_system.ps1" -ForegroundColor Yellow 