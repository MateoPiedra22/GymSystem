#!/bin/bash
# =============================================================================
# Health Check Maestro - Sistema de Gestión de Gimnasio v6.0
# =============================================================================
# 
# Este script ejecuta verificaciones de salud para todos los servicios
# del sistema y proporciona un resumen general del estado.
#
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
TIMEOUT=30
VERBOSE=false
OUTPUT_FORMAT="text"
SERVICES_TO_CHECK="postgres redis backend frontend nginx"
MAX_RETRIES=3
RETRY_DELAY=5

# Función para mostrar ayuda
show_help() {
    cat << EOF
Health Check Maestro - Sistema de Gestión de Gimnasio v6.0

USO:
    $0 [OPCIONES]

OPCIONES:
    -h, --help          Mostrar esta ayuda
    -v, --verbose       Modo verboso
    -t, --timeout SEC   Timeout en segundos (defecto: 30)
    -f, --format FMT    Formato de salida: text, json (defecto: text)
    -s, --services SVC  Servicios a verificar (defecto: todos)

EJEMPLOS:
    $0                              # Verificar todos los servicios
    $0 --verbose                    # Verificación verbosa
    $0 --format json               # Salida en formato JSON
    $0 --services "postgres redis" # Solo verificar DB y Redis

SERVICIOS DISPONIBLES:
    - postgres  : Base de datos PostgreSQL
    - redis     : Cache y sesiones Redis
    - backend   : API FastAPI
    - frontend  : Frontend Next.js
    - nginx     : Proxy reverso Nginx

EOF
}

# Procesar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -f|--format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -s|--services)
            SERVICES_TO_CHECK="$2"
            shift 2
            ;;
        *)
            echo "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Función para logging
log() {
    local level=$1
    shift
    local message="$*"
    
    case $level in
        INFO)
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        WARN)
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        ERROR)
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        SUCCESS)
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
    esac
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para verificar PostgreSQL
check_postgres() {
    local result=""
    local status="UNKNOWN"
    
    if command_exists docker; then
        # Verificar si el contenedor está corriendo
        if docker ps --format "table {{.Names}}" | grep -q "gym_postgres"; then
            # Verificar health check del contenedor
            local health=$(docker inspect --format='{{.State.Health.Status}}' gym_postgres 2>/dev/null || echo "none")
            
            if [ "$health" = "healthy" ]; then
                status="HEALTHY"
                result="PostgreSQL container is healthy"
            elif [ "$health" = "starting" ]; then
                status="STARTING"
                result="PostgreSQL container is starting"
            else
                status="UNHEALTHY"
                result="PostgreSQL container health check failed"
            fi
        else
            status="DOWN"
            result="PostgreSQL container is not running"
        fi
    else
        # Verificar conexión directa
        if command_exists pg_isready; then
            local db_host=${GYM_DB_HOST:-localhost}
            local db_port=${GYM_DB_PORT:-5432}
            local db_user=${GYM_DB_USER:-gym_secure_user}
            local db_name=${GYM_DB_NAME:-gym_secure_db}
            
            if timeout $TIMEOUT pg_isready -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" >/dev/null 2>&1; then
                status="HEALTHY"
                result="PostgreSQL is accepting connections"
            else
                status="UNHEALTHY"
                result="PostgreSQL is not responding"
            fi
        else
            status="UNKNOWN"
            result="Cannot verify PostgreSQL (pg_isready not available)"
        fi
    fi
    
    echo "$status|$result"
}

# Función para verificar Redis
check_redis() {
    local result=""
    local status="UNKNOWN"
    
    if command_exists docker; then
        # Verificar si el contenedor está corriendo
        if docker ps --format "table {{.Names}}" | grep -q "gym_redis"; then
            # Verificar health check del contenedor
            local health=$(docker inspect --format='{{.State.Health.Status}}' gym_redis 2>/dev/null || echo "none")
            
            if [ "$health" = "healthy" ]; then
                status="HEALTHY"
                result="Redis container is healthy"
            elif [ "$health" = "starting" ]; then
                status="STARTING"
                result="Redis container is starting"
            else
                status="UNHEALTHY"
                result="Redis container health check failed"
            fi
        else
            status="DOWN"
            result="Redis container is not running"
        fi
    else
        # Verificar conexión directa
        if command_exists redis-cli; then
            local redis_host=${GYM_REDIS_HOST:-localhost}
            local redis_port=${GYM_REDIS_PORT:-6379}
            local redis_password=${GYM_REDIS_PASSWORD:-}
            
            local cmd="redis-cli -h $redis_host -p $redis_port"
            if [ -n "$redis_password" ]; then
                cmd="$cmd -a $redis_password"
            fi
            
            if timeout $TIMEOUT $cmd ping 2>/dev/null | grep -q "PONG"; then
                status="HEALTHY"
                result="Redis is responding to ping"
            else
                status="UNHEALTHY"
                result="Redis is not responding"
            fi
        else
            status="UNKNOWN"
            result="Cannot verify Redis (redis-cli not available)"
        fi
    fi
    
    echo "$status|$result"
}

# Función para verificar Backend
check_backend() {
    local result=""
    local status="UNKNOWN"
    
    if command_exists docker; then
        # Verificar si el contenedor está corriendo
        if docker ps --format "table {{.Names}}" | grep -q "gym_backend"; then
            # Verificar health check del contenedor
            local health=$(docker inspect --format='{{.State.Health.Status}}' gym_backend 2>/dev/null || echo "none")
            
            if [ "$health" = "healthy" ]; then
                status="HEALTHY"
                result="Backend container is healthy"
            elif [ "$health" = "starting" ]; then
                status="STARTING"
                result="Backend container is starting"
            else
                # Ejecutar health check interno
                if docker exec gym_backend python /app/scripts/healthcheck.py >/dev/null 2>&1; then
                    status="HEALTHY"
                    result="Backend internal health check passed"
                else
                    status="UNHEALTHY"
                    result="Backend health check failed"
                fi
            fi
        else
            status="DOWN"
            result="Backend container is not running"
        fi
    else
        # Verificar mediante HTTP
        local backend_url="http://localhost:${BACKEND_PORT:-8000}"
        
        if command_exists curl; then
            if timeout $TIMEOUT curl -f "$backend_url/health" >/dev/null 2>&1; then
                status="HEALTHY"
                result="Backend API is responding"
            else
                status="UNHEALTHY"
                result="Backend API is not responding"
            fi
        else
            status="UNKNOWN"
            result="Cannot verify Backend (curl not available)"
        fi
    fi
    
    echo "$status|$result"
}

# Función para verificar Frontend
check_frontend() {
    local result=""
    local status="UNKNOWN"
    
    if command_exists docker; then
        # Verificar si el contenedor está corriendo
        if docker ps --format "table {{.Names}}" | grep -q "gym_frontend"; then
            # Verificar health check del contenedor
            local health=$(docker inspect --format='{{.State.Health.Status}}' gym_frontend 2>/dev/null || echo "none")
            
            if [ "$health" = "healthy" ]; then
                status="HEALTHY"
                result="Frontend container is healthy"
            elif [ "$health" = "starting" ]; then
                status="STARTING"
                result="Frontend container is starting"
            else
                # Ejecutar health check interno
                if docker exec gym_frontend node /app/scripts/healthcheck.js >/dev/null 2>&1; then
                    status="HEALTHY"
                    result="Frontend internal health check passed"
                else
                    status="UNHEALTHY"
                    result="Frontend health check failed"
                fi
            fi
        else
            status="DOWN"
            result="Frontend container is not running"
        fi
    else
        # Verificar mediante HTTP
        local frontend_url="http://localhost:${FRONTEND_PORT:-3000}"
        
        if command_exists curl; then
            if timeout $TIMEOUT curl -f "$frontend_url" >/dev/null 2>&1; then
                status="HEALTHY"
                result="Frontend is responding"
            else
                status="UNHEALTHY"
                result="Frontend is not responding"
            fi
        else
            status="UNKNOWN"
            result="Cannot verify Frontend (curl not available)"
        fi
    fi
    
    echo "$status|$result"
}

# Función para verificar Nginx
check_nginx() {
    local result=""
    local status="UNKNOWN"
    
    if command_exists docker; then
        # Verificar si el contenedor está corriendo
        if docker ps --format "table {{.Names}}" | grep -q "gym_nginx"; then
            # Verificar health check del contenedor
            local health=$(docker inspect --format='{{.State.Health.Status}}' gym_nginx 2>/dev/null || echo "none")
            
            if [ "$health" = "healthy" ]; then
                status="HEALTHY"
                result="Nginx container is healthy"
            elif [ "$health" = "starting" ]; then
                status="STARTING"
                result="Nginx container is starting"
            else
                status="UNHEALTHY"
                result="Nginx container health check failed"
            fi
        else
            status="DOWN"
            result="Nginx container is not running"
        fi
    else
        # Verificar mediante HTTP
        local nginx_url="http://localhost:${HTTP_PORT:-80}"
        
        if command_exists curl; then
            if timeout $TIMEOUT curl -f "$nginx_url" >/dev/null 2>&1; then
                status="HEALTHY"
                result="Nginx is responding"
            else
                status="UNHEALTHY"
                result="Nginx is not responding"
            fi
        else
            status="UNKNOWN"
            result="Cannot verify Nginx (curl not available)"
        fi
    fi
    
    echo "$status|$result"
}

# Función principal de verificación
run_health_checks() {
    local overall_status="HEALTHY"
    local checks_data=""
    local total_checks=0
    local healthy_checks=0
    local unhealthy_checks=0
    local starting_checks=0
    local unknown_checks=0
    
    log INFO "Iniciando verificación de salud del sistema..."
    log INFO "Timeout configurado: ${TIMEOUT}s"
    log INFO "Servicios a verificar: $SERVICES_TO_CHECK"
    echo ""
    
    # Ejecutar verificaciones para cada servicio
    for service in $SERVICES_TO_CHECK; do
        local check_result=""
        local service_status=""
        local service_message=""
        
        case $service in
            postgres)
                check_result=$(check_postgres)
                ;;
            redis)
                check_result=$(check_redis)
                ;;
            backend)
                check_result=$(check_backend)
                ;;
            frontend)
                check_result=$(check_frontend)
                ;;
            nginx)
                check_result=$(check_nginx)
                ;;
            *)
                log WARN "Servicio desconocido: $service"
                continue
                ;;
        esac
        
        # Parsear resultado
        service_status=$(echo "$check_result" | cut -d'|' -f1)
        service_message=$(echo "$check_result" | cut -d'|' -f2-)
        
        # Contar estados
        total_checks=$((total_checks + 1))
        case $service_status in
            HEALTHY)
                healthy_checks=$((healthy_checks + 1))
                log SUCCESS "$service: $service_message"
                ;;
            STARTING)
                starting_checks=$((starting_checks + 1))
                log WARN "$service: $service_message"
                ;;
            UNHEALTHY|DOWN)
                unhealthy_checks=$((unhealthy_checks + 1))
                overall_status="UNHEALTHY"
                log ERROR "$service: $service_message"
                ;;
            UNKNOWN)
                unknown_checks=$((unknown_checks + 1))
                log WARN "$service: $service_message"
                ;;
        esac
        
        # Agregar a datos de checks
        if [ -n "$checks_data" ]; then
            checks_data="$checks_data,"
        fi
        checks_data="$checks_data{\"service\":\"$service\",\"status\":\"$service_status\",\"message\":\"$service_message\"}"
        
        if [ "$VERBOSE" = true ]; then
            echo "  Detalles: $service_message"
        fi
    done
    
    # Determinar estado general
    if [ $unhealthy_checks -gt 0 ]; then
        overall_status="UNHEALTHY"
    elif [ $starting_checks -gt 0 ]; then
        overall_status="STARTING"
    elif [ $unknown_checks -gt 0 ] && [ $healthy_checks -eq 0 ]; then
        overall_status="UNKNOWN"
    fi
    
    # Mostrar resumen
    echo ""
    log INFO "=== RESUMEN DE VERIFICACIÓN ==="
    log INFO "Total de servicios verificados: $total_checks"
    log SUCCESS "Servicios saludables: $healthy_checks"
    log WARN "Servicios iniciando: $starting_checks"
    log ERROR "Servicios no saludables: $unhealthy_checks"
    log WARN "Servicios con estado desconocido: $unknown_checks"
    echo ""
    
    case $overall_status in
        HEALTHY)
            log SUCCESS "🎉 ESTADO GENERAL: SISTEMA SALUDABLE"
            ;;
        STARTING)
            log WARN "⏳ ESTADO GENERAL: SISTEMA INICIANDO"
            ;;
        UNHEALTHY)
            log ERROR "❌ ESTADO GENERAL: SISTEMA NO SALUDABLE"
            ;;
        UNKNOWN)
            log WARN "❓ ESTADO GENERAL: ESTADO DESCONOCIDO"
            ;;
    esac
    
    # Salida en JSON si se solicita
    if [ "$OUTPUT_FORMAT" = "json" ]; then
        echo ""
        echo "{"
        echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\","
        echo "  \"overall_status\": \"$overall_status\","
        echo "  \"summary\": {"
        echo "    \"total\": $total_checks,"
        echo "    \"healthy\": $healthy_checks,"
        echo "    \"starting\": $starting_checks,"
        echo "    \"unhealthy\": $unhealthy_checks,"
        echo "    \"unknown\": $unknown_checks"
        echo "  },"
        echo "  \"checks\": [$checks_data],"
        echo "  \"version\": \"6.0.0\""
        echo "}"
    fi
    
    # Código de salida
    case $overall_status in
        HEALTHY|STARTING)
            exit 0
            ;;
        *)
            exit 1
            ;;
    esac
}

# Verificar dependencias básicas
if ! command_exists docker && ! command_exists curl; then
    log ERROR "Se requiere docker o curl para ejecutar las verificaciones"
    exit 1
fi

# Ejecutar verificaciones
run_health_checks 