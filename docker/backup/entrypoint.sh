#!/bin/bash
# =============================================================================
# ENTRYPOINT PARA SERVICIO DE BACKUP
# Sistema de Gestión de Gimnasio v6.0
# =============================================================================

set -euo pipefail

# Configuración
BACKUP_DIR="/backup/data"
LOG_FILE="/backup/entrypoint.log"
CRON_FILE="/etc/crontabs/root"

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función de error
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Función para iniciar servidor HTTP simple
start_http_server() {
    log "Iniciando servidor HTTP para health checks..."
    
    # Crear script de health check
    cat > /backup/health_server.py << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
from datetime import datetime

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Verificar estado del servicio
            backup_dir = "/backup/data"
            backup_files = []
            
            if os.path.exists(backup_dir):
                backup_files = [f for f in os.listdir(backup_dir) if f.startswith('gym_backup_')]
            
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "backup",
                "backup_files_count": len(backup_files),
                "backup_dir": backup_dir,
                "backup_dir_exists": os.path.exists(backup_dir)
            }
            
            self.wfile.write(json.dumps(health_data, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
    
    def log_message(self, format, *args):
        # Silenciar logs del servidor
        pass

if __name__ == "__main__":
    PORT = 8080
    with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
        print(f"Health check server running on port {PORT}")
        httpd.serve_forever()
EOF
    
    # Ejecutar servidor en background
    python3 /backup/health_server.py &
    HTTP_SERVER_PID=$!
    
    log "Servidor HTTP iniciado con PID: $HTTP_SERVER_PID"
}

# Función para configurar cron
setup_cron() {
    local schedule="${BACKUP_SCHEDULE:-0 2 * * *}"
    
    log "Configurando cron con schedule: $schedule"
    
    # Crear directorio de cron si no existe
    mkdir -p /etc/crontabs
    
    # Configurar cron job
    echo "$schedule /backup/backup_script.sh >> /backup/cron.log 2>&1" > "$CRON_FILE"
    
    # Hacer el archivo ejecutable
    chmod +x "$CRON_FILE"
    
    log "Cron configurado exitosamente"
}

# Función para verificar configuración
verify_configuration() {
    log "Verificando configuración..."
    
    # Verificar variables de entorno requeridas
    local required_vars=(
        "GYM_DB_HOST"
        "GYM_DB_NAME"
        "GYM_DB_USER"
        "GYM_DB_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error_exit "Variable de entorno requerida no definida: $var"
        fi
    done
    
    # Verificar conectividad a la base de datos
    log "Verificando conectividad a la base de datos..."
    
    if ! PGPASSWORD="$GYM_DB_PASSWORD" pg_isready \
        -h "$GYM_DB_HOST" \
        -p "${GYM_DB_PORT:-5432}" \
        -U "$GYM_DB_USER" \
        -d "$GYM_DB_NAME" \
        -t 30 > /dev/null 2>&1; then
        error_exit "No se puede conectar a la base de datos"
    fi
    
    log "Conectividad a la base de datos verificada"
    
    # Crear directorio de backup si no existe
    mkdir -p "$BACKUP_DIR"
    
    # Verificar permisos de escritura
    if [[ ! -w "$BACKUP_DIR" ]]; then
        error_exit "No hay permisos de escritura en el directorio de backup"
    fi
    
    log "Configuración verificada exitosamente"
}

# Función para ejecutar backup manual
run_manual_backup() {
    log "Ejecutando backup manual..."
    
    if /backup/backup_script.sh; then
        log "Backup manual completado exitosamente"
    else
        error_exit "Error en backup manual"
    fi
}

# Función para listar backups
list_backups() {
    log "Listando backups disponibles..."
    
    if [[ -d "$BACKUP_DIR" ]]; then
        echo "Backups en $BACKUP_DIR:"
        find "$BACKUP_DIR" -name "gym_backup_*" -type f | sort -r | while read file; do
            size=$(stat -c%s "$file" 2>/dev/null || echo "0")
            date=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1 || echo "unknown")
            echo "  $(basename "$file") - $(numfmt --to=iec $size) - $date"
        done
    else
        echo "Directorio de backup no existe: $BACKUP_DIR"
    fi
}

# Función para limpiar backups antiguos
cleanup_backups() {
    local retention_days="${BACKUP_RETENTION_DAYS:-30}"
    
    log "Limpiando backups más antiguos de $retention_days días..."
    
    if [[ -d "$BACKUP_DIR" ]]; then
        find "$BACKUP_DIR" -name "gym_backup_*" -type f -mtime +$retention_days -delete
        log "Limpieza completada"
    else
        log "Directorio de backup no existe, saltando limpieza"
    fi
}

# Función para mostrar ayuda
show_help() {
    cat << EOF
Uso: $0 [COMANDO]

COMANDOS:
    start           Iniciar servicio de backup (modo daemon)
    backup          Ejecutar backup manual
    list            Listar backups disponibles
    cleanup         Limpiar backups antiguos
    help            Mostrar esta ayuda

VARIABLES DE ENTORNO:
    BACKUP_SCHEDULE         Schedule de cron (default: 0 2 * * *)
    BACKUP_RETENTION_DAYS   Días de retención (default: 30)
    BACKUP_ENCRYPTION_KEY   Clave de encriptación (opcional)
    AWS_ACCESS_KEY_ID       Clave AWS para S3 (opcional)
    AWS_SECRET_ACCESS_KEY   Secreto AWS para S3 (opcional)
    AWS_S3_BUCKET           Bucket S3 para backups (opcional)
    AWS_REGION              Región AWS (default: us-east-1)

EJEMPLOS:
    $0 start
    $0 backup
    $0 list
    $0 cleanup
EOF
}

# Función principal
main() {
    local command="${1:-start}"
    
    case "$command" in
        "start")
            log "=== INICIANDO SERVICIO DE BACKUP ==="
            
            # Verificar configuración
            verify_configuration
            
            # Configurar cron
            setup_cron
            
            # Iniciar servidor HTTP
            start_http_server
            
            # Ejecutar backup inicial si es la primera vez
            if [[ ! -f "$BACKUP_DIR/.initialized" ]]; then
                log "Primera ejecución, creando backup inicial..."
                run_manual_backup
                touch "$BACKUP_DIR/.initialized"
            fi
            
            # Iniciar cron daemon
            log "Iniciando cron daemon..."
            crond -f -d 8 &
            CRON_PID=$!
            
            log "Servicio de backup iniciado exitosamente"
            log "Cron PID: $CRON_PID"
            log "HTTP Server PID: $HTTP_SERVER_PID"
            
            # Esperar señales
            trap 'log "Recibida señal de terminación, cerrando..."; kill $CRON_PID $HTTP_SERVER_PID 2>/dev/null; exit 0' TERM INT
            
            # Mantener el proceso vivo
            while true; do
                sleep 60
                
                # Verificar que los procesos estén vivos
                if ! kill -0 $CRON_PID 2>/dev/null; then
                    log "ERROR: Cron daemon murió, reiniciando..."
                    crond -f -d 8 &
                    CRON_PID=$!
                fi
                
                if ! kill -0 $HTTP_SERVER_PID 2>/dev/null; then
                    log "ERROR: HTTP server murió, reiniciando..."
                    start_http_server
                fi
            done
            ;;
        
        "backup")
            verify_configuration
            run_manual_backup
            ;;
        
        "list")
            list_backups
            ;;
        
        "cleanup")
            cleanup_backups
            ;;
        
        "help"|"-h"|"--help")
            show_help
            ;;
        
        *)
            log "Comando desconocido: $command"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@" 