#!/bin/bash

# Módulo de Interfaz de Usuario para Script de Mantenimiento
# Proporciona funciones para mostrar menús y manejar la interfaz

# Mostrar menú principal
function show_menu() {
    echo ""
    echo "🔧 MANTENIMIENTO DEL SISTEMA DE GIMNASIO"
    echo "========================================"
    echo ""
    echo "1. 📊 Ver estado del sistema"
    echo "2. 🔄 Reiniciar servicios"
    echo "3. 📝 Ver logs en tiempo real"
    echo "4. 💾 Hacer backup de la base de datos"
    echo "5. 🔄 Actualizar la aplicación"
    echo "6. 🔒 Renovar certificado SSL"
    echo "7. 🧹 Limpiar logs antiguos"
    echo "8. 📈 Ver estadísticas del sistema"
    echo "9. 🚨 Resolver problemas comunes"
    echo "0. ❌ Salir"
    echo ""
    read -p "Elige una opción [0-9]: " choice
}

# Mostrar menú de logs
function show_logs_menu() {
    echo "📝 Logs en tiempo real"
    echo "====================="
    echo ""
    echo "Elige qué logs ver:"
    echo "1. Backend API"
    echo "2. Frontend Web"
    echo "3. Nginx"
    echo "4. PostgreSQL"
    echo "5. Todos juntos"
    echo "6. Volver al menú principal"
    echo ""
    read -p "Opción [1-6]: " log_choice
}

# Mostrar menú de estadísticas
function show_stats_menu() {
    echo "📈 Estadísticas del Sistema"
    echo "=========================="
    echo ""
    echo "Elige qué estadísticas ver:"
    echo "1. Estado general del sistema"
    echo "2. Uso de recursos (CPU, RAM, Disco)"
    echo "3. Procesos del gimnasio"
    echo "4. Conexiones de red"
    echo "5. Información del servidor"
    echo "6. Volver al menú principal"
    echo ""
    read -p "Opción [1-6]: " stats_choice
}

# Mostrar menú de troubleshooting
function show_troubleshoot_menu() {
    echo "🚨 Resolver Problemas Comunes"
    echo "============================="
    echo ""
    echo "Elige qué verificar:"
    echo "1. Verificar puertos y servicios"
    echo "2. Verificar logs de errores"
    echo "3. Verificar permisos de archivos"
    echo "4. Verificar conectividad de base de datos"
    echo "5. Aplicar soluciones automáticas"
    echo "6. Volver al menú principal"
    echo ""
    read -p "Opción [1-6]: " troubleshoot_choice
}

# Mostrar encabezado de sección
function show_section_header() {
    local title="$1"
    echo ""
    echo "$title"
    echo "$(printf '=%.0s' {1..${#title}})"
    echo ""
}

# Mostrar mensaje de progreso
function show_progress() {
    local message="$1"
    echo -n "$message... "
}

# Mostrar mensaje de éxito
function show_success() {
    echo "✅ $1"
}

# Mostrar mensaje de error
function show_error() {
    echo "❌ $1"
}

# Mostrar mensaje de advertencia
function show_warning() {
    echo "⚠️  $1"
}

# Mostrar mensaje informativo
function show_info() {
    echo "ℹ️  $1"
}

# Mostrar separador
function show_separator() {
    echo "----------------------------------------"
}

# Mostrar confirmación
function confirm_action() {
    local message="$1"
    echo ""
    read -p "$message (s/N): " confirm
    [[ "$confirm" =~ ^[Ss]$ ]]
}

# Mostrar ayuda
function show_help() {
    echo ""
    echo "🔧 AYUDA - SCRIPT DE MANTENIMIENTO"
    echo "=================================="
    echo ""
    echo "Este script te permite realizar tareas de mantenimiento"
    echo "en el Sistema de Gimnasio de forma fácil y segura."
    echo ""
    echo "OPCIONES DISPONIBLES:"
    echo "1. Ver estado del sistema - Muestra el estado actual de todos los servicios"
    echo "2. Reiniciar servicios - Reinicia todos los servicios del sistema"
    echo "3. Ver logs en tiempo real - Permite ver logs de diferentes servicios"
    echo "4. Hacer backup de la base de datos - Crea una copia de seguridad"
    echo "5. Actualizar la aplicación - Descarga e instala actualizaciones"
    echo "6. Renovar certificado SSL - Renueva el certificado SSL automáticamente"
    echo "7. Limpiar logs antiguos - Elimina logs y backups antiguos"
    echo "8. Ver estadísticas del sistema - Muestra información detallada del servidor"
    echo "9. Resolver problemas comunes - Diagnóstica y resuelve problemas automáticamente"
    echo ""
    echo "PRECAUCIÓN: Algunas opciones pueden requerir privilegios de administrador."
    echo ""
} 