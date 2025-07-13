#!/bin/sh
set -e

echo "🚀 Iniciando aplicación Next.js..."

# Verificar variables de entorno críticas
if [ -z "$BACKEND_URL" ]; then
    echo "❌ ERROR: BACKEND_URL no configurado"
    exit 1
fi

if [ -z "$NEXT_PUBLIC_API_URL" ]; then
    echo "❌ ERROR: NEXT_PUBLIC_API_URL no configurado"
    exit 1
fi

# Verificar que las URLs sean válidas
if [[ ! "$BACKEND_URL" =~ ^https?:// ]]; then
    echo "❌ ERROR: BACKEND_URL debe ser una URL válida"
    exit 1
fi

if [[ ! "$NEXT_PUBLIC_API_URL" =~ ^https?:// ]]; then
    echo "❌ ERROR: NEXT_PUBLIC_API_URL debe ser una URL válida"
    exit 1
fi

echo "✅ Configuración validada"
echo "🎯 Iniciando servidor en puerto ${PORT:-3000}..."

# Iniciar aplicación
exec node server.js 