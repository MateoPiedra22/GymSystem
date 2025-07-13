#!/bin/sh

# Script de build personalizado para evitar errores de pre-renderizado
echo "🚀 Iniciando build personalizado..."

# Configurar variables de entorno para evitar pre-renderizado
export NODE_ENV=production
export NEXT_TELEMETRY_DISABLED=1

# Limpiar build anterior
echo "🧹 Limpiando build anterior..."
rm -rf .next

# Ejecutar build con configuración específica
echo "🔨 Ejecutando build..."
npx next build

echo "✅ Build completado exitosamente!" 