# Sistema de Monitoreo - Sistema de Gimnasio v6

## 📋 Descripción General

El sistema de monitoreo proporciona visibilidad completa sobre el rendimiento, salud y estado de todos los componentes del sistema de gimnasio. Utiliza Prometheus para la recolección de métricas y Grafana para la visualización y alertas.

## 🏗️ Arquitectura del Monitoreo

### Componentes Principales
- **Prometheus**: Recolector y almacén de métricas
- **Grafana**: Visualización y dashboards
- **Exporters**: Agentes que exponen métricas de servicios específicos
- **Alertas**: Sistema de notificaciones automáticas

### Servicios Monitoreados
- **Backend FastAPI**: Métricas de aplicación y rendimiento
- **PostgreSQL**: Métricas de base de datos
- **Redis**: Métricas de caché
- **Nginx**: Métricas de proxy y acceso
- **Sistema**: Métricas de infraestructura
- **Contenedores**: Métricas de Docker

## ⚙️ Configuración

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `PROMETHEUS_PORT` | Puerto de Prometheus | `9090` |
| `GRAFANA_PORT` | Puerto de Grafana | `3001` |
| `GRAFANA_USERNAME` | Usuario de Grafana | `admin` |
| `GRAFANA_PASSWORD` | Contraseña de Grafana | **Requerida** |

### Puertos de Servicios
- **Prometheus**: 9090
- **Grafana**: 3001
- **PostgreSQL Exporter**: 9187
- **Redis Exporter**: 9121
- **Node Exporter**: 9100
- **cAdvisor**: 8080

## 🚀 Iniciar el Sistema de Monitoreo

### Iniciar Todo el Sistema con Monitoreo
```bash
# Iniciar sistema completo con monitoreo
docker-compose --profile production --profile monitoring up -d

# Verificar servicios
docker-compose --profile monitoring ps
```

### Iniciar Solo Monitoreo
```bash
# Iniciar solo servicios de monitoreo
docker-compose --profile monitoring up -d

# Verificar estado
docker-compose --profile monitoring ps
```

### Acceso a Interfaces
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/GRAFANA_PASSWORD)

## 📊 Métricas Disponibles

### Backend FastAPI
- **Request Rate**: Peticiones por segundo
- **Response Time**: Tiempo de respuesta (p50, p95, p99)
- **Error Rate**: Tasa de errores HTTP
- **Active Connections**: Conexiones activas
- **Memory Usage**: Uso de memoria del proceso
- **CPU Usage**: Uso de CPU del proceso

### PostgreSQL
- **Active Connections**: Conexiones activas por base de datos
- **Transaction Rate**: Transacciones por segundo
- **Query Performance**: Tiempo de consultas
- **Lock Statistics**: Estadísticas de bloqueos
- **Buffer Hit Ratio**: Ratio de aciertos en buffer
- **WAL Statistics**: Estadísticas de Write-Ahead Log

### Redis
- **Memory Usage**: Uso de memoria
- **Connected Clients**: Clientes conectados
- **Command Statistics**: Estadísticas de comandos
- **Keyspace Hits/Misses**: Ratio de aciertos
- **Network I/O**: Entrada/salida de red
- **Slow Log**: Consultas lentas

### Nginx
- **Request Rate**: Peticiones por segundo
- **Response Codes**: Códigos de respuesta HTTP
- **Upstream Response Time**: Tiempo de respuesta de upstream
- **Active Connections**: Conexiones activas
- **Reading/Writing/Waiting**: Estados de conexiones

### Sistema (Node Exporter)
- **CPU Usage**: Uso de CPU por core
- **Memory Usage**: Uso de memoria RAM
- **Disk Usage**: Uso de disco por filesystem
- **Network I/O**: Entrada/salida de red
- **Load Average**: Carga del sistema
- **File Descriptors**: Descriptores de archivo abiertos

### Contenedores (cAdvisor)
- **Container CPU**: Uso de CPU por contenedor
- **Container Memory**: Uso de memoria por contenedor
- **Container Network**: Red por contenedor
- **Container Disk**: I/O de disco por contenedor
- **Container Restarts**: Reinicios de contenedores

## 📈 Dashboards de Grafana

### Dashboard Principal: "Sistema de Gimnasio v6 - Overview"
- **Estado de Servicios**: Indicadores UP/DOWN de todos los servicios
- **CPU y Memory Usage**: Gauges de uso de recursos del sistema
- **Request Rate**: Tasa de peticiones al backend
- **Response Time**: Tiempo de respuesta del backend
- **PostgreSQL Connections**: Conexiones activas a la base de datos
- **Redis Memory**: Uso de memoria de Redis
- **Error Rate**: Tasa de errores HTTP
- **Disk Usage**: Uso de disco por filesystem
- **Active Alerts**: Tabla de alertas activas

### Características de los Dashboards
- **Auto-refresh**: Actualización automática cada 30 segundos
- **Tema Oscuro**: Interfaz optimizada para monitoreo 24/7
- **Responsive**: Adaptable a diferentes tamaños de pantalla
- **Exportable**: Los dashboards se pueden exportar/importar

## 🚨 Sistema de Alertas

### Tipos de Alertas

#### Infraestructura
- **HighCPUUsage**: CPU > 80% por 5 minutos
- **HighMemoryUsage**: Memoria > 85% por 5 minutos
- **HighDiskUsage**: Disco > 85% por 5 minutos
- **ContainerDown**: Contenedor no responde por 1 minuto

#### Base de Datos
- **PostgreSQLDown**: PostgreSQL no disponible por 30 segundos
- **PostgreSQLHighConnections**: > 80 conexiones activas
- **PostgreSQLSlowQueries**: Consultas > 30 segundos
- **PostgreSQLDeadlocks**: Deadlocks detectados

#### Redis
- **RedisDown**: Redis no disponible por 30 segundos
- **RedisHighMemoryUsage**: Memoria > 80%
- **RedisHighConnections**: > 100 clientes conectados
- **RedisLowHitRate**: Tasa de aciertos < 80%

#### Backend
- **BackendDown**: Backend no responde por 30 segundos
- **BackendSlowResponse**: 95% de respuestas > 2 segundos
- **BackendHighErrorRate**: > 5% errores 5xx
- **BackendHighRequestRate**: > 1000 peticiones/minuto

#### Nginx
- **NginxDown**: Nginx no responde por 30 segundos
- **NginxHighErrorRate**: > 5% errores 5xx
- **NginxHighRequestRate**: > 2000 peticiones/minuto

#### Seguridad
- **HighFailedLogins**: > 10 intentos fallidos/minuto
- **UnauthorizedAccess**: > 5 peticiones 401/minuto
- **RateLimitExceeded**: Límites de tasa excedidos

#### Backup
- **BackupServiceDown**: Servicio de backup no disponible
- **BackupFailed**: No hay backup exitoso en 24 horas
- **BackupTooSlow**: Backup > 1 hora
- **BackupSizeTooLarge**: Backup > 1GB

### Configuración de Alertas
Las alertas están configuradas en `monitoring/alert_rules.yml` y se cargan automáticamente en Prometheus.

### Severidades
- **Critical**: Requiere atención inmediata
- **Warning**: Requiere atención pronto
- **Info**: Información importante

## 🔧 Configuración Avanzada

### Prometheus

#### Configuración de Retención
```yaml
# En prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'gym-system'
    environment: 'production'
```

#### Configuración de Almacenamiento
```yaml
# En docker-compose.yml
command:
  - '--storage.tsdb.retention.time=90d'  # Retención de 90 días
  - '--storage.tsdb.path=/prometheus'
```

### Grafana

#### Configuración de Seguridad
```yaml
# En docker-compose.yml
environment:
  GF_SECURITY_COOKIE_SECURE: "true"
  GF_SECURITY_COOKIE_SAMESITE: "strict"
  GF_SECURITY_STRICT_TRANSPORT_SECURITY: "true"
```

#### Plugins Instalados
- grafana-clock-panel
- grafana-simple-json-datasource

## 📊 Consultas PromQL Útiles

### Métricas de Sistema
```promql
# CPU Usage
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory Usage
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100

# Disk Usage
(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100
```

### Métricas de Aplicación
```promql
# Request Rate
rate(http_requests_total{job="gym-backend"}[5m])

# Response Time 95th percentile
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="gym-backend"}[5m]))

# Error Rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100
```

### Métricas de Base de Datos
```promql
# Active Connections
pg_stat_database_numbackends

# Transaction Rate
rate(pg_stat_database_xact_commit[5m]) + rate(pg_stat_database_xact_rollback[5m])
```

### Métricas de Redis
```promql
# Memory Usage
redis_memory_used_bytes / redis_memory_max_bytes * 100

# Hit Rate
rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) * 100
```

## 🛠️ Mantenimiento

### Backup de Configuración
```bash
# Backup de configuración de Prometheus
cp monitoring/prometheus.yml backups/prometheus.yml.$(date +%Y%m%d)

# Backup de configuración de Grafana
cp -r monitoring/grafana backups/grafana.$(date +%Y%m%d)
```

### Limpieza de Datos
```bash
# Limpiar datos antiguos de Prometheus (desde dentro del contenedor)
docker exec gym_prometheus wget --post-data='' http://localhost:9090/api/v1/admin/tsdb/clean_tombstones
```

### Actualización de Dashboards
```bash
# Los dashboards se actualizan automáticamente cada 30 segundos
# Para forzar actualización, reiniciar Grafana:
docker-compose restart grafana
```

## 🔍 Troubleshooting

### Problemas Comunes

#### Prometheus No Recolecta Métricas
```bash
# Verificar estado de Prometheus
docker exec gym_prometheus wget -qO- http://localhost:9090/api/v1/targets

# Verificar configuración
docker exec gym_prometheus promtool check config /etc/prometheus/prometheus.yml
```

#### Grafana No Muestra Datos
```bash
# Verificar datasource
curl -u admin:GRAFANA_PASSWORD http://localhost:3001/api/datasources

# Verificar logs
docker logs gym_grafana
```

#### Exporters No Funcionan
```bash
# Verificar PostgreSQL Exporter
curl http://localhost:9187/metrics | grep pg_up

# Verificar Redis Exporter
curl http://localhost:9121/metrics | grep redis_up
```

### Comandos de Diagnóstico

#### Verificar Métricas
```bash
# Métricas de Prometheus
curl http://localhost:9090/api/v1/query?query=up

# Métricas de Node Exporter
curl http://localhost:9100/metrics

# Métricas de cAdvisor
curl http://localhost:8080/metrics
```

#### Verificar Alertas
```bash
# Alertas activas
curl http://localhost:9090/api/v1/alerts

# Reglas de alertas
curl http://localhost:9090/api/v1/rules
```

## 📈 Escalabilidad

### Configuración para Producción
- **Retención**: Aumentar a 1 año para análisis histórico
- **Almacenamiento**: Usar volúmenes externos para persistencia
- **Recursos**: Aumentar límites de memoria y CPU
- **Backup**: Configurar backup automático de datos de Prometheus

### Configuración para Alta Disponibilidad
- **Prometheus**: Configurar replicación
- **Grafana**: Usar múltiples instancias con load balancer
- **Alertas**: Configurar múltiples alert managers
- **Exporters**: Usar service discovery para escalabilidad

## 📚 Referencias

### Documentación Relacionada
- [Docker Compose Configuration](docker-compose.yml)
- [Backup Service](BACKUP_SERVICE.md)
- [Health Checks](HEALTH_CHECKS.md)
- [Environment Setup](ENVIRONMENT_SETUP.md)

### Enlaces Útiles
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Reference](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Node Exporter](https://github.com/prometheus/node_exporter)
- [PostgreSQL Exporter](https://github.com/prometheus-community/postgres_exporter)
- [Redis Exporter](https://github.com/oliver006/redis_exporter)

---

**Nota**: El sistema de monitoreo es esencial para mantener la salud y rendimiento del sistema. Asegúrese de revisar regularmente las métricas y configurar alertas apropiadas para su entorno. 