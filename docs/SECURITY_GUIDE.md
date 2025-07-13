# 🔒 Guía de Seguridad - Sistema de Gestión de Gimnasio v6.0

## 📋 Índice

1. [Configuración de Seguridad](#configuración-de-seguridad)
2. [Claves Secretas](#claves-secretas)
3. [Configuración de Producción](#configuración-de-producción)
4. [Docker Security](#docker-security)
5. [Nginx Security](#nginx-security)
6. [Validación de Seguridad](#validación-de-seguridad)
7. [Monitoreo y Logs](#monitoreo-y-logs)
8. [Backup y Recuperación](#backup-y-recuperación)
9. [Checklist de Seguridad](#checklist-de-seguridad)
10. [Auditoría de Seguridad](#auditoría-de-seguridad)

## 🔧 Configuración de Seguridad

### Variables de Entorno Críticas

El sistema utiliza las siguientes variables de entorno críticas que **DEBEN** ser configuradas de forma segura:

```bash
# Claves secretas (generar con el script de seguridad)
GYM_SECRET_KEY=clave_secreta_generada_con_secrets_token_urlsafe_64
GYM_JWT_SECRET_KEY=clave_jwt_generada_con_secrets_token_urlsafe_64
GYM_BACKUP_KEY=clave_backup_generada_con_secrets_token_urlsafe_32

# Contraseñas de servicios (mínimo 16 caracteres, incluir mayúsculas, minúsculas, números y símbolos)
GYM_DB_PASSWORD=contraseña_segura_de_al_menos_16_caracteres_con_símbolos
GYM_REDIS_PASSWORD=contraseña_redis_segura_de_al_menos_16_caracteres
GRAFANA_PASSWORD=contraseña_grafana_segura_con_símbolos

# Configuración de sesiones
GYM_SESSION_SECRET=clave_sesión_generada_con_secrets_token_urlsafe_32
GYM_COOKIE_SECRET=clave_cookie_generada_con_secrets_token_urlsafe_32
```

### Configuración de Seguridad por Entorno

#### Desarrollo
```bash
GYM_ENV=development
GYM_DEBUG=true
GYM_FORCE_HTTPS=false
GYM_SECURE_COOKIES=false
GYM_SAMESITE_COOKIES=lax
GYM_RATE_LIMIT=200
GYM_MAX_LOGIN_ATTEMPTS=10
GYM_PASSWORD_MIN_LENGTH=8
GYM_PASSWORD_REQUIRE_SPECIAL=true
```

#### Producción
```bash
GYM_ENV=production
GYM_DEBUG=false
GYM_FORCE_HTTPS=true
GYM_SECURE_COOKIES=true
GYM_SAMESITE_COOKIES=strict
GYM_RATE_LIMIT=60
GYM_MAX_LOGIN_ATTEMPTS=3
GYM_PASSWORD_MIN_LENGTH=12
GYM_PASSWORD_REQUIRE_SPECIAL=true
GYM_SESSION_TIMEOUT=3600
GYM_JWT_EXPIRE_MINUTES=30
```

## 🔐 Claves Secretas

### Generación de Claves Seguras

**IMPORTANTE**: Nunca uses claves por defecto en producción. Usa el script de generación:

```bash
# Generar claves seguras
python scripts/generate_secure_keys.py --output production_keys.env

# O generar claves individuales
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Validación de Fortaleza de Claves

```python
# Ejemplo de validación de contraseña
def validate_password_strength(password: str) -> bool:
    if len(password) < 12:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    if not any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
        return False
    return True
```

### Rotación de Claves

- **Frecuencia**: Cada 90 días
- **Proceso**: 
  1. Generar nuevas claves
  2. Actualizar configuración
  3. Reiniciar servicios
  4. Invalidar sesiones existentes
  5. Verificar funcionamiento
  6. Documentar cambio

### Almacenamiento Seguro

- **Desarrollo**: Archivos `.env` locales con permisos 600
- **Producción**: Gestor de secretos (HashiCorp Vault, AWS Secrets Manager, etc.)
- **Nunca**: Subir claves a control de versiones
- **Backup**: Encriptar claves de backup

## 🚀 Configuración de Producción

### Configuración de Base de Datos

```bash
# PostgreSQL
GYM_DB_SSL_MODE=require
GYM_DB_POOL_SIZE=20
GYM_DB_MAX_OVERFLOW=10
GYM_DB_STATEMENT_TIMEOUT=30000
GYM_DB_IDLE_IN_TRANSACTION_TIMEOUT=60000
GYM_DB_CONNECTION_LIMIT=100
GYM_DB_MAX_CONNECTIONS=200

# Redis
GYM_REDIS_PASSWORD=contraseña_segura_con_símbolos
REDIS_MAX_MEMORY=512mb
REDIS_MAX_MEMORY_POLICY=allkeys-lru
REDIS_TIMEOUT=300
REDIS_TCP_KEEPALIVE=300
```

### Configuración de CORS

```bash
# Producción - Solo dominios específicos
GYM_CORS_ORIGINS=["https://your-domain.com","https://www.your-domain.com"]
GYM_CORS_ALLOW_CREDENTIALS=true
GYM_CORS_MAX_AGE=86400

# NO usar en producción
GYM_CORS_ORIGINS=["*"]  # ❌ PELIGROSO
```

### Configuración de Rate Limiting

```bash
# API general
GYM_RATE_LIMIT=60  # 60 requests por minuto
GYM_RATE_LIMIT_BURST=20  # 20 requests en burst

# Login específico
GYM_MAX_LOGIN_ATTEMPTS=3
GYM_LOCKOUT_TIME=30  # 30 minutos
GYM_LOGIN_RATE_LIMIT=5  # 5 intentos por minuto

# Uploads
GYM_MAX_UPLOAD_SIZE=10485760  # 10MB
GYM_ALLOWED_UPLOAD_TYPES=["image/jpeg","image/png","image/gif","application/pdf"]
```

### Configuración de Sesiones

```bash
# Sesiones seguras
GYM_SESSION_TIMEOUT=3600  # 1 hora
GYM_SESSION_RENEWAL=true
GYM_SESSION_ABSOLUTE_TIMEOUT=86400  # 24 horas
GYM_SESSION_CLEANUP_INTERVAL=3600  # 1 hora
```

## 🐳 Docker Security

### Configuración de Contenedores

```yaml
# docker-compose.yml
services:
  backend:
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
      - /var/cache:noexec,nosuid,size=50m
    deploy:
      resources:
        limits:
          memory: 2g
          cpus: '2.0'
        reservations:
          memory: 512m
          cpus: '0.5'
    environment:
      - PYTHONHASHSEED=random
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
```

### Usuario No-Root

```dockerfile
# Dockerfile
RUN groupadd -r gymapp && useradd -r -g gymapp -s /bin/bash gymapp
RUN chown -R gymapp:gymapp /app
USER gymapp
WORKDIR /app
```

### Health Checks

```yaml
healthcheck:
  test: ["CMD", "python", "/app/healthcheck.py"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

### Escaneo de Vulnerabilidades

```bash
# Escanear imágenes de Docker
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image gym-system-backend:latest

# Escanear archivos de configuración
docker run --rm -v $(pwd):/workspace aquasec/trivy config /workspace
```

## 🔒 Nginx Security

### Headers de Seguridad

```nginx
# Headers obligatorios
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none';" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
```

### Rate Limiting

```nginx
# Zonas de rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;
limit_req_zone $binary_remote_addr zone=static:10m rate=50r/s;

# Aplicar rate limiting
location /api/ {
    limit_req zone=api burst=20 nodelay;
    limit_req_status 429;
}

location /api/auth/login {
    limit_req zone=login burst=5 nodelay;
    limit_req_status 429;
}

location /api/upload/ {
    limit_req zone=upload burst=5 nodelay;
    limit_req_status 429;
}
```

### Bloqueo de Archivos Sensibles

```nginx
# Bloquear archivos sensibles
location ~ /\. {
    deny all;
    access_log off;
    log_not_found off;
}

location ~ ~$ {
    deny all;
    access_log off;
    log_not_found off;
}

location ~ \.(env|log|sql|bak|backup|old|tmp)$ {
    deny all;
    access_log off;
    log_not_found off;
}
```

### Configuración SSL/TLS

```nginx
# Configuración SSL moderna
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;
```

## 🔍 Validación de Seguridad

### Scripts de Validación

```bash
# Validar configuración de seguridad
python scripts/security_validation.py

# Auditar dependencias
npm audit
pip-audit

# Escanear vulnerabilidades
python scripts/security_audit.py
```

### Checklist de Validación

- [ ] Todas las claves secretas han sido cambiadas
- [ ] Contraseñas cumplen criterios de fortaleza
- [ ] SSL/TLS configurado correctamente
- [ ] Headers de seguridad implementados
- [ ] Rate limiting configurado
- [ ] Logs de seguridad habilitados
- [ ] Backup automático configurado
- [ ] Monitoreo de seguridad activo

## 📊 Monitoreo y Logs

### Configuración de Logs

```bash
# Logs de seguridad
GYM_SECURITY_LOG_LEVEL=INFO
GYM_AUDIT_LOG_ENABLED=true
GYM_LOG_RETENTION_DAYS=90
GYM_LOG_ROTATION_SIZE=100MB

# Logs de aplicación
GYM_APP_LOG_LEVEL=INFO
GYM_ACCESS_LOG_ENABLED=true
GYM_ERROR_LOG_ENABLED=true
```

### Monitoreo de Seguridad

```yaml
# Prometheus alerts
groups:
  - name: security_alerts
    rules:
      - alert: FailedLoginAttempts
        expr: rate(login_failures_total[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Múltiples intentos de login fallidos"
          
      - alert: UnauthorizedAccess
        expr: rate(unauthorized_requests_total[5m]) > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Accesos no autorizados detectados"
```

## 💾 Backup y Recuperación

### Configuración de Backup

```bash
# Backup automático
GYM_BACKUP_ENABLED=true
GYM_BACKUP_SCHEDULE="0 2 * * *"  # Diario a las 2 AM
GYM_BACKUP_RETENTION_DAYS=30
GYM_BACKUP_ENCRYPTION=true
GYM_BACKUP_COMPRESSION=true
```

### Script de Backup

```bash
#!/bin/bash
# Backup seguro con encriptación
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql.gpg"
pg_dump -h localhost -U postgres gym_system | \
gpg --encrypt --recipient backup-key --output "backups/$BACKUP_FILE"
```

## ✅ Checklist de Seguridad

### Pre-Despliegue
- [ ] Claves secretas generadas y configuradas
- [ ] Contraseñas de servicios cambiadas
- [ ] SSL/TLS configurado
- [ ] Headers de seguridad implementados
- [ ] Rate limiting configurado
- [ ] Logs de seguridad habilitados
- [ ] Backup configurado
- [ ] Monitoreo configurado

### Post-Despliegue
- [ ] Verificar funcionamiento de SSL
- [ ] Probar rate limiting
- [ ] Verificar logs de seguridad
- [ ] Probar backup y restauración
- [ ] Verificar monitoreo
- [ ] Documentar configuración

### Mantenimiento
- [ ] Rotar claves cada 90 días
- [ ] Actualizar dependencias mensualmente
- [ ] Revisar logs de seguridad semanalmente
- [ ] Probar backup mensualmente
- [ ] Auditar accesos mensualmente

## 🔍 Auditoría de Seguridad

### Herramientas de Auditoría

```bash
# Escaneo de vulnerabilidades
nmap -sV -sC -p- your-domain.com
nikto -h your-domain.com
sqlmap -u "https://your-domain.com/api/users" --batch

# Análisis de código
bandit -r /path/to/code
safety check
npm audit
```

### Reporte de Auditoría

```markdown
# Reporte de Auditoría de Seguridad

## Resumen Ejecutivo
- Fecha de auditoría: [FECHA]
- Alcance: [SISTEMAS AUDITADOS]
- Hallazgos críticos: [NÚMERO]
- Hallazgos altos: [NÚMERO]
- Hallazgos medios: [NÚMERO]

## Hallazgos Críticos
1. [DESCRIPCIÓN]
   - Riesgo: [RIESGO]
   - Recomendación: [RECOMENDACIÓN]
   - Fecha límite: [FECHA]

## Recomendaciones
1. [RECOMENDACIÓN]
2. [RECOMENDACIÓN]
3. [RECOMENDACIÓN]

## Conclusión
[CONCLUSIÓN GENERAL]
```

---

**IMPORTANTE**: Esta guía debe ser revisada y actualizada regularmente. La seguridad es un proceso continuo, no un evento único. 