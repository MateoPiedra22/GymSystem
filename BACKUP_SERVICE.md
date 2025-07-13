# Servicio de Backup Automático - Sistema de Gimnasio v6

## 📋 Descripción General

El servicio de backup automático es un componente crítico del sistema que garantiza la protección de datos mediante backups programados de PostgreSQL, Redis y archivos del sistema. El servicio está completamente containerizado y se ejecuta de forma autónoma.

## 🏗️ Arquitectura

### Componentes
- **Contenedor de Backup**: Alpine Linux con herramientas de backup
- **PostgreSQL**: Backup completo de la base de datos
- **Redis**: Backup del estado de la caché
- **Archivos**: Backup de uploads y archivos multimedia
- **Encriptación**: Soporte opcional para encriptación GPG
- **Programación**: Cron para ejecución automática

### Estructura de Archivos
```
docker/backup/
├── Dockerfile              # Imagen del contenedor
├── backup_script.sh        # Script principal de backup
├── restore_script.sh       # Script de restauración
└── entrypoint.sh          # Punto de entrada del contenedor
```

## ⚙️ Configuración

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `POSTGRES_HOST` | Host de PostgreSQL | `postgres` |
| `POSTGRES_PORT` | Puerto de PostgreSQL | `5432` |
| `POSTGRES_DB` | Nombre de la base de datos | `gym_secure_db` |
| `POSTGRES_USER` | Usuario de PostgreSQL | `gym_secure_user` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | **Requerida** |
| `REDIS_HOST` | Host de Redis | `redis` |
| `REDIS_PORT` | Puerto de Redis | `6379` |
| `REDIS_PASSWORD` | Contraseña de Redis | Opcional |
| `BACKUP_SCHEDULE` | Programación cron | `0 2 * * *` |
| `BACKUP_RETENTION_DAYS` | Días de retención | `90` |
| `ENCRYPTION_KEY` | Clave de encriptación | Opcional |
| `TZ` | Zona horaria | `America/Argentina/Buenos_Aires` |

### Programación de Backups

El servicio utiliza cron para programar los backups:

```bash
# Backup diario a las 2:00 AM
0 2 * * * /usr/local/bin/backup_script.sh full

# Cleanup semanal (domingo a las 3:00 AM)
0 3 * * 0 /usr/local/bin/backup_script.sh cleanup
```

## 🚀 Uso del Servicio

### Iniciar el Servicio

```bash
# Iniciar solo el servicio de backup
docker-compose --profile production up backup

# Iniciar todo el sistema con backup
docker-compose --profile production up -d
```

### Comandos Manuales

#### Ejecutar Backup Manual
```bash
# Backup completo
docker exec gym_backup /usr/local/bin/backup_script.sh full

# Solo PostgreSQL
docker exec gym_backup /usr/local/bin/backup_script.sh postgresql

# Solo Redis
docker exec gym_backup /usr/local/bin/backup_script.sh redis

# Solo archivos
docker exec gym_backup /usr/local/bin/backup_script.sh files
```

#### Listar Backups
```bash
docker exec gym_backup /usr/local/bin/backup_script.sh list
```

#### Limpiar Backups Antiguos
```bash
docker exec gym_backup /usr/local/bin/backup_script.sh cleanup
```

## 🔄 Restauración de Datos

### Comandos de Restauración

#### Restaurar PostgreSQL
```bash
docker exec gym_backup /usr/local/bin/restore_script.sh postgresql /backups/postgresql_backup_20231201_120000.sql.gz.gpg
```

#### Restaurar Redis
```bash
# 1. Restaurar backup
docker exec gym_backup /usr/local/bin/restore_script.sh redis /backups/redis_backup_20231201_120000.rdb.gz.gpg

# 2. Reiniciar Redis
docker restart gym_redis
```

#### Restaurar Archivos
```bash
docker exec gym_backup /usr/local/bin/restore_script.sh files /backups/files_backup_20231201_120000.tar.gz.gpg /data
```

#### Verificar Integridad
```bash
docker exec gym_backup /usr/local/bin/restore_script.sh verify /backups/postgresql_backup_20231201_120000.sql.gz.gpg
```

#### Información de Backup
```bash
docker exec gym_backup /usr/local/bin/restore_script.sh info /backups/postgresql_backup_20231201_120000.sql.gz.gpg
```

## 📁 Estructura de Backups

### Ubicación
Los backups se almacenan en el directorio `./backups/` del host.

### Nomenclatura
- **PostgreSQL**: `postgresql_backup_YYYYMMDD_HHMMSS.sql.gz[.gpg]`
- **Redis**: `redis_backup_YYYYMMDD_HHMMSS.rdb.gz[.gpg]`
- **Archivos**: `files_backup_YYYYMMDD_HHMMSS.tar.gz[.gpg]`

### Ejemplo de Estructura
```
backups/
├── postgresql_backup_20231201_020000.sql.gz.gpg
├── redis_backup_20231201_020000.rdb.gz.gpg
├── files_backup_20231201_020000.tar.gz.gpg
├── backup.log
├── cron.log
└── restore.log
```

## 🔐 Encriptación

### Configuración de Encriptación
Para activar la encriptación, configure la variable `ENCRYPTION_KEY`:

```bash
# En .env
ENCRYPTION_KEY=tu_clave_secreta_muy_larga_y_segura
```

### Características de Encriptación
- **Algoritmo**: AES256
- **Compresión**: Gzip antes de encriptar
- **Formato**: GPG simétrico
- **Verificación**: Integridad verificada automáticamente

## 📊 Monitoreo y Logs

### Logs Disponibles
- **backup.log**: Logs de operaciones de backup
- **cron.log**: Logs de ejecución programada
- **restore.log**: Logs de operaciones de restauración

### Ver Logs
```bash
# Logs de backup
docker exec gym_backup cat /backups/backup.log

# Logs de cron
docker exec gym_backup cat /backups/cron.log

# Logs de restauración
docker exec gym_backup cat /backups/restore.log
```

### Health Check
El servicio incluye health checks automáticos:
- Verificación de conectividad con PostgreSQL
- Verificación de conectividad con Redis
- Verificación de directorios de backup
- Verificación del proceso cron

## 🛠️ Mantenimiento

### Limpieza Automática
- **Backups**: Eliminados después de `BACKUP_RETENTION_DAYS` días
- **Logs**: Eliminados después de 7 días
- **Cleanup**: Ejecutado semanalmente

### Verificación de Espacio
```bash
# Verificar espacio usado
docker exec gym_backup du -sh /backups

# Verificar espacio disponible
docker exec gym_backup df -h /backups
```

### Rotación de Logs
Los logs se rotan automáticamente para evitar el llenado del disco.

## 🔧 Troubleshooting

### Problemas Comunes

#### Error de Conexión a PostgreSQL
```bash
# Verificar conectividad
docker exec gym_backup pg_isready -h postgres -p 5432 -U gym_secure_user -d gym_secure_db

# Verificar variables de entorno
docker exec gym_backup env | grep POSTGRES
```

#### Error de Conexión a Redis
```bash
# Verificar conectividad
docker exec gym_backup redis-cli -h redis -p 6379 ping

# Verificar variables de entorno
docker exec gym_backup env | grep REDIS
```

#### Backup Fallido
```bash
# Verificar logs
docker exec gym_backup tail -f /backups/backup.log

# Verificar permisos
docker exec gym_backup ls -la /backups
```

#### Restauración Fallida
```bash
# Verificar integridad del backup
docker exec gym_backup /usr/local/bin/restore_script.sh verify /backups/archivo_backup

# Verificar espacio disponible
docker exec gym_backup df -h
```

### Comandos de Diagnóstico

#### Estado del Servicio
```bash
# Verificar estado del contenedor
docker ps | grep gym_backup

# Verificar logs del contenedor
docker logs gym_backup

# Verificar procesos
docker exec gym_backup ps aux
```

#### Verificar Cron
```bash
# Verificar configuración de cron
docker exec gym_backup crontab -l

# Verificar logs de cron
docker exec gym_backup tail -f /backups/cron.log
```

## 📈 Métricas y Alertas

### Métricas Disponibles
- Tiempo de ejecución de backup
- Tamaño de backups
- Tasa de éxito/fallo
- Espacio utilizado
- Frecuencia de ejecución

### Alertas Recomendadas
- Backup fallido por más de 24 horas
- Espacio de backup > 80%
- Tiempo de backup > 1 hora
- Error de encriptación/desencriptación

## 🔄 Migración y Escalabilidad

### Migración de Backups
Para migrar backups a otro servidor:

```bash
# Copiar directorio de backups
rsync -avz ./backups/ usuario@servidor:/ruta/backups/

# Restaurar en nuevo servidor
docker exec gym_backup /usr/local/bin/restore_script.sh postgresql /backups/archivo_backup
```

### Escalabilidad
- **Almacenamiento**: Montar volúmenes externos
- **Redundancia**: Replicar backups a múltiples ubicaciones
- **Compresión**: Ajustar nivel de compresión según necesidades

## 📚 Referencias

### Documentación Relacionada
- [Docker Compose Configuration](docker-compose.yml)
- [Environment Setup](ENVIRONMENT_SETUP.md)
- [Health Checks](HEALTH_CHECKS.md)
- [Nginx Configuration](NGINX_CONFIGURATION.md)

### Enlaces Útiles
- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)
- [Redis Persistence](https://redis.io/topics/persistence)
- [GPG Encryption](https://gnupg.org/documentation/)
- [Cron Scheduling](https://crontab.guru/)

---

**Nota**: Este servicio es crítico para la protección de datos. Asegúrese de probar regularmente los procedimientos de restauración y mantener copias de seguridad en ubicaciones externas. 