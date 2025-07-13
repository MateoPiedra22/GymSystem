#!/bin/bash

# Módulo de Logging para Scripts de Despliegue
# Proporciona funciones para mostrar mensajes con colores y timestamps

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función de logging básico
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Función para mensajes de éxito
success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

# Función para advertencias
warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

# Función para errores
error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Función para información detallada
info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] ℹ️  $1${NC}"
}

# Función para debug (solo si DEBUG está habilitado)
debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 DEBUG: $1${NC}"
    fi
} 