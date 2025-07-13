# 🔧 Configuración de Entornos - Sistema de Gestión de Gimnasio v6.0

## 📋 Descripción General

Este documento explica cómo configurar correctamente los entornos para el Sistema de Gestión de Gimnasio v6.0, incluyendo desarrollo local, staging y producción.

## 📁 Archivos de Configuración Disponibles

### 🟢 Archivos de Plantilla (Seguros para Git)
- `.env.example` - Plantilla completa con todas las variables
- `.env.production.example` - Configuración optimizada para producción
- `.env.development` - Configuración para contenedores de desarrollo

### 🔴 Archivos Locales (NO incluir en Git)
- `.env` - Configuración local activa
- `.env.local` - Configuración específica de máquina
- `.env.production` - Configuración real de producción

## ⚙️ Configuración para Desarrollo Local

### 1. Configuración Básica

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar configuraciones según necesidades
nano .env
```

### 2. Variables Críticas a Personalizar

```bash
# Generar claves secretas únicas
python -c "import secrets; print('GYM_SECRET_KEY=' + secrets.token_urlsafe(64))"
python -c "import secrets; print('GYM_JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"
python -c "import secrets; print('GYM_BACKUP_KEY=' + secrets.token_urlsafe(32))"
```

### 3. Configuración de Base de Datos

```bash
# PostgreSQL Local
GYM_DB_HOST=localhost
GYM_DB_PORT=5432
GYM_DB_NAME=gym_dev_db
GYM_DB_USER=gym_dev_user
GYM_DB_PASSWORD=your_secure_password
```

### 4. Configuración de Redis

```bash
# Redis Local
GYM_REDIS_HOST=localhost
GYM_REDIS_PORT=6379
GYM_REDIS_PASSWORD=your_redis_password
```

## 🐳 Configuración para Docker

### 1. Desarrollo con Docker Compose

```bash
# Usar archivo de desarrollo
cp .env.development .env

# Ejecutar con Docker Compose
docker-compose up -d
```

### 2. Variables Específicas de Docker

```bash
# Configuraciones para contenedores
GYM_ALLOWED_HOSTS=localhost,127.0.0.1,backend,frontend
GYM_CORS_ORIGINS=["http://localhost:3000", "http://frontend:3000"]
```

## 🚀 Configuración para Producción

### ⚠️ IMPORTANTE: Seguridad en Producción

**NUNCA usar archivos .env en producción. Usar:**
- Variables de entorno del sistema
- Gestores de secretos (AWS Secrets Manager, Azure Key Vault, etc.)
- Kubernetes Secrets
- Docker Secrets

### 1. Variables de Entorno del Sistema

```bash
# Establecer en el sistema operativo
export GYM_SECRET_KEY="your_production_secret_key"
export GYM_JWT_SECRET_KEY="your_production_jwt_key"
export GYM_DB_PASSWORD="your_production_db_password"
```

### 2. Docker Secrets (Recomendado)

```yaml
# docker-compose.yml para producción
services:
  backend:
    secrets:
      - gym_secret_key
      - gym_jwt_secret
      - db_password

secrets:
  gym_secret_key:
    external: true
  gym_jwt_secret:
    external: true
  db_password:
    external: true
```

### 3. Configuraciones Críticas de Producción

```bash
# Seguridad obligatoria
GYM_ENV=production
GYM_DEBUG=false
GYM_FORCE_HTTPS=true
GYM_SECURE_COOKIES=true
GYM_SAMESITE_COOKIES=strict

# Restricciones de seguridad
GYM_ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
GYM_CORS_ORIGINS=["https://tu-dominio.com"]
GYM_RATE_LIMIT=30
GYM_MAX_LOGIN_ATTEMPTS=3
GYM_SESSION_TIMEOUT=15
```

## 🛡️ Checklist de Seguridad

### ✅ Desarrollo
- [ ] Archivo `.env` no está en Git
- [ ] Claves secretas generadas únicamente
- [ ] Rate limiting deshabilitado para desarrollo
- [ ] Debug habilitado solo en desarrollo

### ✅ Producción
- [ ] NO usar archivos .env
- [ ] Todas las claves generadas con herramientas seguras
- [ ] HTTPS forzado
- [ ] Cookies seguras habilitadas
- [ ] Rate limiting estricto
- [ ] Hosts y CORS restringidos
- [ ] Logs de auditoría habilitados
- [ ] Backups automáticos configurados

## 🔧 Herramientas para Generar Secretos

### Python (Recomendado)
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### OpenSSL
```bash
openssl rand -base64 64
```

### pwgen (Linux/Mac)
```bash
pwgen -s 64 1
```

### Node.js
```javascript
require('crypto').randomBytes(64).toString('base64');
```

## 📊 Variables por Categoría

### 🔐 Seguridad y Autenticación
- `GYM_SECRET_KEY` - Clave principal de la aplicación
- `GYM_JWT_SECRET_KEY` - Clave para tokens JWT
- `GYM_BACKUP_KEY` - Clave para encriptación de backups

### 🗄️ Base de Datos
- `GYM_DB_HOST` - Host de PostgreSQL
- `GYM_DB_PORT` - Puerto de PostgreSQL
- `GYM_DB_NAME` - Nombre de la base de datos
- `GYM_DB_USER` - Usuario de la base de datos
- `GYM_DB_PASSWORD` - Contraseña de la base de datos

### 📱 Cache y Sesiones
- `GYM_REDIS_HOST` - Host de Redis
- `GYM_REDIS_PORT` - Puerto de Redis
- `GYM_REDIS_PASSWORD` - Contraseña de Redis

### 🌐 Configuración Web
- `BACKEND_PORT` - Puerto del backend
- `FRONTEND_PORT` - Puerto del frontend
- `NEXT_PUBLIC_API_URL` - URL pública de la API

### 🔒 Configuración de Seguridad
- `GYM_FORCE_HTTPS` - Forzar HTTPS
- `GYM_SECURE_COOKIES` - Cookies seguras
- `GYM_RATE_LIMIT` - Límite de requests por minuto
- `GYM_MAX_LOGIN_ATTEMPTS` - Máximo intentos de login

### 📈 Monitoreo y Métricas
- `PROMETHEUS_PORT` - Puerto de Prometheus
- `GRAFANA_PORT` - Puerto de Grafana
- `GYM_PROMETHEUS_METRICS` - Habilitar métricas

## 🚨 Solución de Problemas

### Error: "Environment variable not found"
```bash
# Verificar que .env existe
ls -la .env

# Verificar formato del archivo
cat .env | grep -v ^# | grep -v ^$
```

### Error: "Database connection failed"
```bash
# Verificar configuración de DB
echo $GYM_DB_HOST
echo $GYM_DB_PORT

# Probar conexión manual
psql -h $GYM_DB_HOST -p $GYM_DB_PORT -U $GYM_DB_USER -d $GYM_DB_NAME
```

### Error: "Redis connection failed"
```bash
# Verificar Redis
redis-cli -h $GYM_REDIS_HOST -p $GYM_REDIS_PORT ping
```

## 📞 Soporte

Para problemas con la configuración:
1. Verificar que todas las variables requeridas están definidas
2. Comprobar formato y sintaxis del archivo .env
3. Revisar logs de la aplicación para errores específicos
4. Consultar la documentación del docker-compose.yml

---

**Nota:** Este archivo se actualiza automáticamente. Para cambios específicos, consultar la documentación oficial del proyecto. 