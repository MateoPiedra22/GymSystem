# Módulo de Prerequisitos para Scripts de Despliegue PowerShell
# Verifica que todas las herramientas necesarias estén instaladas y funcionando

# Verificar prerequisitos
function Test-Prerequisites {
    Write-Log "🔍 Verificando prerequisitos..."
    
    # Verificar Docker
    if (-not (Test-Docker)) {
        Write-Error "Docker no está instalado o no está corriendo"
        Write-Error "Instala Docker Desktop desde: https://docs.docker.com/desktop/install/windows/"
        exit 1
    }
    
    # Verificar Docker Compose
    if (-not (Test-DockerCompose)) {
        Write-Error "Docker Compose no está instalado"
        Write-Error "Instala Docker Compose desde: https://docs.docker.com/compose/install/"
        exit 1
    }
    
    # Verificar versiones
    Show-VersionInfo
    
    # Verificar espacio en disco
    Test-DiskSpace
    
    Write-Success "Prerequisitos verificados"
}

# Verificar Docker
function Test-Docker {
    try {
        docker version | Out-Null
        Write-Success "Docker encontrado"
        return $true
    }
    catch {
        Write-Error "Docker no está instalado o no está corriendo"
        return $false
    }
}

# Verificar Docker Compose
function Test-DockerCompose {
    try {
        docker-compose version | Out-Null
        Write-Success "Docker Compose encontrado"
        return $true
    }
    catch {
        Write-Error "Docker Compose no está instalado"
        return $false
    }
}

# Mostrar información de versiones
function Show-VersionInfo {
    try {
        $dockerVersion = (docker --version) -replace "Docker version ", ""
        Write-Info "Docker versión: $dockerVersion"
        
        $composeVersion = (docker-compose --version) -replace "docker-compose version ", ""
        Write-Info "Docker Compose versión: $composeVersion"
    }
    catch {
        Write-Warning "No se pudo obtener información de versiones"
    }
}

# Verificar espacio en disco
function Test-DiskSpace {
    try {
        $drive = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
        $availableGB = [math]::Round($drive.FreeSpace / 1GB, 2)
        $requiredGB = 5
        
        if ($availableGB -lt $requiredGB) {
            Write-Warning "Espacio en disco bajo: ${availableGB}GB disponible, ${requiredGB}GB recomendados"
        }
        else {
            Write-Debug "Espacio en disco OK: ${availableGB}GB disponible"
        }
    }
    catch {
        Write-Warning "No se pudo verificar espacio en disco"
    }
}

# Verificar conectividad de red
function Test-NetworkConnectivity {
    Write-Log "🌐 Verificando conectividad de red..."
    
    try {
        $testUrl = "https://www.google.com"
        $response = Invoke-WebRequest -Uri $testUrl -UseBasicParsing -TimeoutSec 10
        Write-Debug "Conectividad de red OK"
        return $true
    }
    catch {
        Write-Warning "Problemas de conectividad de red detectados"
        return $false
    }
}

# Verificar permisos de administrador
function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        Write-Warning "El script no se está ejecutando como administrador"
        Write-Warning "Algunas operaciones pueden requerir privilegios elevados"
    }
    else {
        Write-Debug "Ejecutando con privilegios de administrador"
    }
    
    return $isAdmin
} 