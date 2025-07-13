# Script de Detención del Sistema de Gimnasio
# Ejecutar este script para detener todos los servicios

Write-Host "🛑 Deteniendo Sistema de Gimnasio..." -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan

# Navegar al directorio del proyecto
$projectDir = Split-Path -Parent $PSScriptRoot
Set-Location $projectDir

# Detener servicios
Write-Host "`n🛑 Deteniendo servicios..." -ForegroundColor Yellow
try {
    docker-compose down
    Write-Host "✅ Servicios detenidos correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al detener servicios" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 ¡Sistema detenido!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "💡 Para iniciar el sistema: .\scripts\start_gym_system.ps1" -ForegroundColor Yellow 