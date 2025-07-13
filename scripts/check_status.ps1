# Script de Verificación de Estado - Sistema de Gimnasio
# Ejecutar este script para verificar que todo funcione correctamente

Write-Host "🔍 Verificando Estado del Sistema de Gimnasio..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

# Verificar Docker
Write-Host "`n🐳 Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker version --format "{{.Server.Version}}"
    Write-Host "✅ Docker está ejecutándose (Versión: $dockerVersion)" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker no está ejecutándose" -ForegroundColor Red
    exit 1
}

# Navegar al directorio del proyecto
$projectDir = Split-Path -Parent $PSScriptRoot
Set-Location $projectDir

# Verificar estado de contenedores
Write-Host "`n📦 Verificando contenedores..." -ForegroundColor Yellow
try {
    $containers = docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    Write-Host $containers -ForegroundColor White
} catch {
    Write-Host "❌ Error al verificar contenedores" -ForegroundColor Red
}

# Verificar puertos
Write-Host "`n🔌 Verificando puertos..." -ForegroundColor Yellow
$ports = @(
    @{Port=80; Service="Nginx HTTP"},
    @{Port=3000; Service="Frontend Web"},
    @{Port=8000; Service="Backend API"},
    @{Port=5432; Service="PostgreSQL"},
    @{Port=6379; Service="Redis"},
    @{Port=3001; Service="Grafana"},
    @{Port=9090; Service="Prometheus"}
)

foreach ($port in $ports) {
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $port.Port -InformationLevel Quiet
        if ($connection) {
            Write-Host "✅ Puerto $($port.Port) ($($port.Service)): Abierto" -ForegroundColor Green
        } else {
            Write-Host "❌ Puerto $($port.Port) ($($port.Service)): Cerrado" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Puerto $($port.Port) ($($port.Service)): Error" -ForegroundColor Red
    }
}

# Verificar uso de recursos
Write-Host "`n💾 Verificando uso de recursos..." -ForegroundColor Yellow
try {
    $stats = docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    Write-Host $stats -ForegroundColor White
} catch {
    Write-Host "❌ Error al verificar recursos" -ForegroundColor Red
}

# Verificar logs recientes
Write-Host "`n📋 Verificando logs recientes..." -ForegroundColor Yellow
try {
    $recentLogs = docker-compose logs --tail=5
    Write-Host $recentLogs -ForegroundColor Gray
} catch {
    Write-Host "❌ Error al verificar logs" -ForegroundColor Red
}

# Verificar conectividad web
Write-Host "`n🌐 Verificando conectividad web..." -ForegroundColor Yellow
$webUrls = @(
    @{Url="http://localhost:3000"; Service="Frontend"},
    @{Url="http://localhost:8000"; Service="Backend API"},
    @{Url="http://localhost:3001"; Service="Grafana"}
)

foreach ($url in $webUrls) {
    try {
        $response = Invoke-WebRequest -Uri $url.Url -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($url.Service) ($($url.Url)): Funcionando" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $($url.Service) ($($url.Url)): Estado $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($url.Service) ($($url.Url)): No disponible" -ForegroundColor Red
    }
}

# Verificar espacio en disco
Write-Host "`n💿 Verificando espacio en disco..." -ForegroundColor Yellow
try {
    $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
    $freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 2)
    $totalSpaceGB = [math]::Round($disk.Size / 1GB, 2)
    $usedPercent = [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 1)
    
    Write-Host "💾 Espacio libre: $freeSpaceGB GB de $totalSpaceGB GB ($usedPercent% usado)" -ForegroundColor White
    
    if ($freeSpaceGB -lt 10) {
        Write-Host "⚠️  Poco espacio libre. Considera limpiar archivos." -ForegroundColor Yellow
    } else {
        Write-Host "✅ Espacio en disco suficiente" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Error al verificar espacio en disco" -ForegroundColor Red
}

Write-Host "`n🎉 Verificación completada!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

Write-Host "`n💡 Comandos útiles:" -ForegroundColor Yellow
Write-Host "   Ver logs detallados: docker-compose logs -f" -ForegroundColor White
Write-Host "   Reiniciar servicios: docker-compose restart" -ForegroundColor White
Write-Host "   Hacer respaldo: .\scripts\backup_system.ps1" -ForegroundColor White 