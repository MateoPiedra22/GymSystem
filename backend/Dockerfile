# =============================================================================
# DOCKERFILE PARA BACKEND FASTAPI
# Sistema de Gestión de Gimnasio v6.0
# =============================================================================

# ============================================================================
# STAGE 1: Base - Configuración común
# ============================================================================
FROM python:3.11-slim as base

# Metadatos
LABEL maintainer="Sistema de Gimnasio v6"
LABEL description="Backend FastAPI para sistema de gestión de gimnasio"
LABEL version="6.0"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# ============================================================================
# STAGE 2: Builder - Instalar dependencias
# ============================================================================
FROM base as builder

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libmagic1 \
    libmagic-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Crear entorno virtual y instalar dependencias
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ============================================================================
# STAGE 3: Production - Imagen final optimizada
# ============================================================================
FROM base as production

# Instalar solo dependencias runtime necesarias
RUN apt-get update && apt-get install -y \
    libpq5 \
    libmagic1 \
    ffmpeg \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no-root para seguridad
RUN groupadd -r gymapp && useradd -r -g gymapp -s /bin/bash gymapp

# Copiar entorno virtual desde builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Establecer directorio de trabajo
WORKDIR /app

# Crear directorios necesarios con permisos correctos
RUN mkdir -p /app/logs /app/uploads /app/backups /app/tmp && \
    chown -R gymapp:gymapp /app && \
    chmod -R 755 /app && \
    chmod 700 /app/backups && \
    chmod 700 /app/uploads && \
    chmod 750 /app/logs

# Copiar código de la aplicación
COPY --chown=gymapp:gymapp . .

# Copiar scripts y hacerlos ejecutables
COPY --chown=gymapp:gymapp scripts/docker-entrypoint.sh /app/entrypoint.sh
COPY --chown=gymapp:gymapp scripts/healthcheck.py /app/healthcheck.py
RUN chmod +x /app/entrypoint.sh /app/healthcheck.py

# Configurar variables de entorno de seguridad
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Cambiar a usuario no-root para seguridad
USER gymapp

# Exponer puerto
EXPOSE 8000

# Configurar health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python /app/healthcheck.py

# Configurar punto de entrada
ENTRYPOINT ["/app/entrypoint.sh"]

# ============================================================================
# STAGE 4: Development - Para desarrollo local
# ============================================================================
FROM production as development

# Cambiar a root temporalmente para instalar herramientas de desarrollo
USER root

# Instalar herramientas de desarrollo
RUN pip install \
    debugpy \
    pytest-xdist \
    black \
    flake8 \
    mypy

# Copiar entrypoint de desarrollo
COPY scripts/docker-entrypoint-dev.sh /app/entrypoint-dev.sh
RUN chmod +x /app/entrypoint-dev.sh

# Volver a usuario no-root
USER gymapp

# Usar entrypoint de desarrollo por defecto en esta stage
ENTRYPOINT ["/app/entrypoint-dev.sh"] 