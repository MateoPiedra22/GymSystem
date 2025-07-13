# Script de Despliegue para Sistema de Gimnasio v6 - Windows PowerShell

param(
    [string]$Environment = "development",
    [string]$Version = "latest",
    [bool]$ForceRecreate = $false,
    [switch]$Help
)

# Importar módulos
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\deploy\modules\logging.ps1"
. "$ScriptDir\deploy\modules\prerequisites.ps1"
. "$ScriptDir\deploy\modules\environment.ps1"
. "$ScriptDir\deploy\modules\ssl.ps1"
. "$ScriptDir\deploy\modules\database.ps1"
. "$ScriptDir\deploy\modules\services.ps1"
. "$ScriptDir\deploy\modules\validation.ps1"
. "$ScriptDir\deploy\modules\build.ps1"

# Configuración
$ProjectName = "gym-system"
$ValidEnvironments = @("development", "staging", "production")

# Función principal
function Main {
    # Mostrar ayuda si se solicita
    if ($Help) {
        Show-Help
        return
    }
    
    Write-Log "🎯 Iniciando despliegue del Sistema de Gimnasio v6"
    Write-Log "   Ambiente: $Environment"
    Write-Log "   Versión: $Version"
    Write-Log "   Proyecto: $ProjectName"
    
    try {
        # Ejecutar pasos
        Test-Prerequisites
        Set-Environment $Environment
        Set-Profiles $Environment
        New-SSLCertificates $Environment
        Test-ProductionConfig $Environment
        Build-Images $ForceRecreate
        Start-Services
        Start-Sleep -Seconds 10
        Test-Services
        Show-ServiceInfo $Environment
        
        Write-Log "🎉 Despliegue completado exitosamente" -Level "Success"
        
        if ($Environment -eq "production") {
            Write-Log "RECORDATORIO: Configura tu dominio, SSL y firewall apropiadamente" -Level "Warning"
        }
    }
    catch {
        Write-Log "Error durante el despliegue: $_" -Level "Error"
        Write-Log "Deteniendo servicios..." -Level "Warning"
        docker-compose down
        exit 1
    }
}

# Función para mostrar ayuda
function Show-Help {
    Write-Host @"
Script de Despliegue - Sistema de Gimnasio v6 (Windows)

USO: .\scripts\deploy.ps1 [PARAMETROS]
PARAMETROS:
    -Environment        Ambiente de despliegue (development|staging|production)
    -Version           Versión a desplegar
    -ForceRecreate     Forzar recreación de containers
    -Help              Mostrar esta ayuda

EJEMPLOS:
    .\scripts\deploy.ps1                                    # Desarrollo
    .\scripts\deploy.ps1 -Environment development          # Desarrollo explícito
    .\scripts\deploy.ps1 -Environment staging -Version v6.1.0    # Staging con versión específica
    .\scripts\deploy.ps1 -Environment production -ForceRecreate   # Producción forzando recreación

PREREQUISITOS:
    - Docker Desktop para Windows instalado y corriendo
    - Archivo .env.{AMBIENTE} configurado
    - Certificados SSL (para production)
"@
}

# Ejecutar script principal
Main 