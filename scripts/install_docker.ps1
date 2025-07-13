# Script para instalar Docker Desktop en Windows
# Ejecutar como Administrador

Write-Host "🚀 Instalando Docker Desktop para Windows..." -ForegroundColor Green

# Verificar si Docker ya está instalado
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "✅ Docker ya está instalado!" -ForegroundColor Green
    docker --version
    exit 0
}

# Verificar si WSL2 está habilitado
Write-Host "📋 Verificando WSL2..." -ForegroundColor Yellow
$wslStatus = wsl --status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  WSL2 no está habilitado. Habilitando..." -ForegroundColor Yellow
    
    # Habilitar características de Windows
    Write-Host "🔧 Habilitando características de Windows..." -ForegroundColor Yellow
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    
    Write-Host "🔄 Reinicia tu computadora y ejecuta este script nuevamente." -ForegroundColor Red
    Write-Host "💡 Después del reinicio, ejecuta: wsl --set-default-version 2" -ForegroundColor Cyan
    exit 1
}

# Descargar Docker Desktop
Write-Host "📥 Descargando Docker Desktop..." -ForegroundColor Yellow
$dockerUrl = "https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe"
$installerPath = "$env:TEMP\DockerDesktopInstaller.exe"

try {
    Invoke-WebRequest -Uri $dockerUrl -OutFile $installerPath
    Write-Host "✅ Descarga completada!" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al descargar Docker Desktop" -ForegroundColor Red
    Write-Host "🔗 Descarga manual desde: https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
    exit 1
}

# Instalar Docker Desktop
Write-Host "🔧 Instalando Docker Desktop..." -ForegroundColor Yellow
Start-Process -FilePath $installerPath -ArgumentList "install --quiet" -Wait

# Limpiar archivo temporal
Remove-Item $installerPath -Force

Write-Host "✅ Instalación completada!" -ForegroundColor Green
Write-Host "🔄 Reinicia tu computadora para completar la instalación." -ForegroundColor Yellow
Write-Host "💡 Después del reinicio, abre Docker Desktop desde el menú inicio." -ForegroundColor Cyan

Write-Host "`n📋 Pasos siguientes:" -ForegroundColor Green
Write-Host "1. Reinicia tu computadora" -ForegroundColor White
Write-Host "2. Abre Docker Desktop desde el menú inicio" -ForegroundColor White
Write-Host "3. Acepta los términos y condiciones" -ForegroundColor White
Write-Host "4. Ejecuta el script de configuración del proyecto" -ForegroundColor White 