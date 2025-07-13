# Módulo de Logging para Scripts de Despliegue PowerShell
# Proporciona funciones para mostrar mensajes con colores y timestamps

# Función para logging con colores
function Write-Log {
    param($Message, $Level = "Info")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    switch ($Level) {
        "Success" { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green }
        "Warning" { Write-Host "[$timestamp] ⚠️  $Message" -ForegroundColor Yellow }
        "Error"   { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red }
        "Info"    { Write-Host "[$timestamp] ℹ️  $Message" -ForegroundColor Blue }
        "Debug"   { 
            if ($env:DEBUG -eq "true") {
                Write-Host "[$timestamp] 🔍 DEBUG: $Message" -ForegroundColor Yellow 
            }
        }
        default   { Write-Host "[$timestamp] $Message" -ForegroundColor Blue }
    }
}

# Función para mensajes de éxito
function Write-Success {
    param($Message)
    Write-Log $Message -Level "Success"
}

# Función para advertencias
function Write-Warning {
    param($Message)
    Write-Log $Message -Level "Warning"
}

# Función para errores
function Write-Error {
    param($Message)
    Write-Log $Message -Level "Error"
}

# Función para información detallada
function Write-Info {
    param($Message)
    Write-Log $Message -Level "Info"
}

# Función para debug
function Write-Debug {
    param($Message)
    Write-Log $Message -Level "Debug"
} 