# =============================================================================
# DOCKERFILE PARA SERVICIO DE BACKUP
# Sistema de Gestión de Gimnasio v6.0
# =============================================================================

FROM postgres:15

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    wget \
    tar \
    gzip \
    openssl \
    python3 \
    python3-pip \
    && pip3 install --no-cache-dir \
    boto3 \
    psycopg2-binary \
    cryptography \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /backup

# Copiar scripts de backup
COPY backup_script.sh /backup/
COPY restore_script.sh /backup/
COPY entrypoint.sh /backup/

# Hacer ejecutables los scripts
RUN chmod +x /backup/*.sh

# Crear directorio para backups
RUN mkdir -p /backup/data

# Variables de entorno por defecto
ENV BACKUP_SCHEDULE="0 2 * * *"
ENV BACKUP_RETENTION_DAYS=30
ENV BACKUP_ENCRYPTION_KEY=""
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""
ENV AWS_S3_BUCKET=""
ENV AWS_REGION="us-east-1"

# Exponer puerto para health check
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando por defecto
CMD ["/backup/entrypoint.sh"] 