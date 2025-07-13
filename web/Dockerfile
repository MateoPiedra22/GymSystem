# =============================================================================
# DOCKERFILE PARA FRONTEND WEB
# Sistema de Gestión de Gimnasio v6.0 - Optimizado para Producción
# =============================================================================

# ============================================================================
# STAGE 1: Base - Configuración común
# ============================================================================
FROM node:18-alpine as base

# Metadatos
LABEL maintainer="Sistema de Gimnasio v6"
LABEL description="Frontend Next.js para sistema de gestión de gimnasio"
LABEL version="6.0"

# Variables de entorno
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Instalar dependencias del sistema
RUN apk add --no-cache \
    wget \
    curl \
    dumb-init \
    && rm -rf /var/cache/apk/*

# ============================================================================
# STAGE 2: Builder - Construir aplicación
# ============================================================================
FROM base as builder

# Argumentos de construcción
ARG NODE_ENV=production
ARG NEXT_PUBLIC_API_URL

# Crear usuario no-root para seguridad
RUN addgroup -g 1001 -S gymapp && \
    adduser -S gymapp -u 1001

# Crear directorio de trabajo
WORKDIR /app

# Asegurar que la carpeta .next existe antes de cambiar de usuario
RUN mkdir -p .next

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias con cache optimizado
RUN npm ci --only=production && \
    npm cache clean --force

# Copiar código fuente
COPY --chown=gymapp:gymapp . .

# Cambiar a usuario no-root
USER gymapp

# Construir aplicación optimizada
RUN npm run build

# ============================================================================
# STAGE 3: Production - Imagen final optimizada
# ============================================================================
FROM base as production

# Crear usuario no-root para seguridad
RUN addgroup -g 1001 -S gymapp && \
    adduser -S gymapp -u 1001

# Crear directorio de trabajo
WORKDIR /app

# Crear directorios necesarios con permisos correctos
RUN mkdir -p /app/logs /app/.next/cache && \
    chown -R gymapp:gymapp /app && \
    chmod -R 755 /app && \
    chmod 750 /app/logs

# Copiar archivos necesarios desde builder
COPY --from=builder --chown=gymapp:gymapp /app/public ./public
COPY --from=builder --chown=gymapp:gymapp /app/.next ./.next
COPY --from=builder --chown=gymapp:gymapp /app/node_modules ./node_modules
COPY --from=builder --chown=gymapp:gymapp /app/package*.json ./

# Cambiar a usuario no-root para seguridad
USER gymapp

# Exponer puerto
EXPOSE 3000

# Configurar health check mejorado
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Configurar punto de entrada con dumb-init
ENTRYPOINT ["dumb-init", "--"]
CMD ["npm", "start"]

# ============================================================================
# STAGE 4: Development - Para desarrollo local
# ============================================================================
FROM base as development

# Cambiar a root temporalmente para instalar herramientas de desarrollo
USER root

# Instalar herramientas de desarrollo
RUN npm install -g \
    nodemon \
    eslint \
    prettier

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias incluyendo devDependencies
RUN npm install

# Copiar código fuente
COPY . .

# Cambiar a usuario no-root
USER gymapp

# Exponer puerto
EXPOSE 3000

# Configurar punto de entrada para desarrollo
CMD ["npm", "run", "dev"] 