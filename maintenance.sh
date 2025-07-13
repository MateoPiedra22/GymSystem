#!/bin/bash
# Script de mantenimiento para el Sistema de Gimnasio

# Importar módulos
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/maintenance/modules/ui.sh"
source "${SCRIPT_DIR}/maintenance/modules/status.sh"
source "${SCRIPT_DIR}/maintenance/modules/services.sh"
source "${SCRIPT_DIR}/maintenance/modules/backup.sh"
source "${SCRIPT_DIR}/maintenance/modules/update.sh"
source "${SCRIPT_DIR}/maintenance/modules/ssl.sh"
source "${SCRIPT_DIR}/maintenance/modules/cleanup.sh"
source "${SCRIPT_DIR}/maintenance/modules/stats.sh"
source "${SCRIPT_DIR}/maintenance/modules/troubleshoot.sh"

# Configuración
BACKUP_DIR="/home/gymapp/backups"
APP_DIR="/home/gymapp/gym-system"
APP_USER="gymapp"

# Programa principal
function main() {
    while true; do
        show_menu
        handle_menu_choice
    done
}

# Manejar la elección del menú
function handle_menu_choice() {
    case $choice in
        1) check_system_status ;;
        2) restart_all_services ;;
        3) view_logs_menu ;;
        4) create_database_backup ;;
        5) update_application ;;
        6) renew_ssl_certificate ;;
        7) clean_old_logs ;;
        8) show_system_stats ;;
        9) troubleshoot_system ;;
        0) echo "👋 ¡Hasta luego!"; exit 0 ;;
        *) echo "❌ Opción inválida. Intenta de nuevo." ;;
    esac
    
    echo ""
    read -p "Presiona Enter para continuar..."
}

# Ejecutar script principal
main "$@" 