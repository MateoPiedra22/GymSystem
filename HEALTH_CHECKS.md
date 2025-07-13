# 🏥 Sistema de Health Checks - Gimnasio v6.0

## 📋 Descripción General

El sistema de health checks está diseñado para monitorear la salud y disponibilidad de todos los servicios del Sistema de Gestión de Gimnasio v6.0. Proporciona verificaciones automatizadas y reportes detallados del estado del sistema.

## 🔧 Componentes del Sistema

### 1. Scripts de Health Check Individuales

#### 🐍 Backend Health Check (`backend/scripts/healthcheck.py`)
**Verificaciones realizadas:**
- ✅ **API FastAPI:** Respuesta del endpoint `/health`
- ✅ **Base de Datos PostgreSQL:** Conectividad y consultas básicas
- ✅ **Redis:** Conectividad y operaciones de lectura/escritura
- ✅ **Espacio en Disco:** Disponibilidad y uso del almacenamiento
- ✅ **Memoria:** Uso de memoria del sistema
- ✅ **Tablas de Base de Datos:** Verificación de tablas críticas

**Uso:**
```bash
# Ejecutar en contenedor Docker
docker exec gym_backend python /app/scripts/healthcheck.py

# Ejecutar directamente
cd backend && python scripts/healthcheck.py
```

**Salida JSON:**
```json
{
  "overall_status": "healthy",
  "timestamp": 1706889600.123,
  "check_duration": 2.456,
  "checks": {
    "api": {
      "status": "healthy",
      "response_time": 0.234,
      "status_code": 200
    },
    "database": {
      "status": "healthy",
      "response_time": 0.123,
      "tables_found": 3,
      "expected_tables": 3
    }
  },
  "version": "6.0.0",
  "environment": "production"
}
```

#### 🌐 Frontend Health Check (`web/scripts/healthcheck.js`)
**Verificaciones realizadas:**
- ✅ **Servidor Next.js:** Respuesta del servidor
- ✅ **API Backend:** Conectividad con el backend
- ✅ **Archivos de Build:** Verificación de archivos críticos
- ✅ **Memoria Node.js:** Uso de memoria del proceso
- ✅ **Variables de Entorno:** Verificación de configuración

**Uso:**
```bash
# Ejecutar en contenedor Docker
docker exec gym_frontend node /app/scripts/healthcheck.js

# Ejecutar directamente
cd web && node scripts/healthcheck.js
```

#### 🔄 Health Check Maestro (`scripts/health_check_all.sh`)
**Verificaciones realizadas:**
- ✅ **PostgreSQL:** Estado del contenedor y conectividad
- ✅ **Redis:** Estado del contenedor y operaciones
- ✅ **Backend:** Health checks internos y API
- ✅ **Frontend:** Health checks internos y respuesta
- ✅ **Nginx:** Estado del contenedor y proxy

**Uso:**
```bash
# Verificar todos los servicios
./scripts/health_check_all.sh

# Verificación verbosa
./scripts/health_check_all.sh --verbose

# Salida en JSON
./scripts/health_check_all.sh --format json

# Verificar servicios específicos
./scripts/health_check_all.sh --services "postgres redis"
```

### 2. Health Checks de Docker Compose

Los health checks están integrados en el `docker-compose.yml`:

#### PostgreSQL
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${GYM_DB_USER} -d ${GYM_DB_NAME}"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

#### Redis
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
  interval: 10s
  timeout: 3s
  retries: 5
```

#### Backend
```yaml
healthcheck:
  test: ["CMD", "python", "/app/scripts/healthcheck.py"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

#### Frontend
```yaml
healthcheck:
  test: ["CMD", "node", "/app/scripts/healthcheck.js"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

#### Nginx
```yaml
healthcheck:
  test: ["CMD", "nginx", "-t"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## 📊 Estados y Códigos de Salida

### Estados de Health Check

| Estado | Descripción | Código de Salida |
|--------|-------------|------------------|
| `HEALTHY` | Servicio funcionando correctamente | 0 |
| `STARTING` | Servicio iniciando, temporalmente no disponible | 0 |
| `WARNING` | Servicio funcional con advertencias | 0 |
| `UNHEALTHY` | Servicio no funcional o con errores críticos | 1 |
| `UNKNOWN` | No se pudo determinar el estado | 1 |
| `DOWN` | Servicio completamente inaccesible | 1 |

### Interpretación de Resultados

#### ✅ Sistema Saludable
- Todos los servicios responden correctamente
- Latencias dentro de rangos aceptables
- Recursos disponibles suficientes

#### ⚠️ Sistema con Advertencias
- Servicios funcionando pero con problemas menores
- Latencias elevadas pero aceptables
- Uso de recursos alto pero no crítico

#### ❌ Sistema No Saludable
- Uno o más servicios no responden
- Errores críticos en componentes esenciales
- Recursos agotados o no disponibles

## 🔧 Configuración y Personalización

### Variables de Entorno para Health Checks

```bash
# Timeouts
HEALTH_CHECK_TIMEOUT=30
HEALTH_CHECK_INTERVAL=30

# Umbrales de rendimiento
HEALTH_CHECK_API_TIMEOUT=10000      # ms
HEALTH_CHECK_DB_TIMEOUT=5000        # ms
HEALTH_CHECK_REDIS_TIMEOUT=3000     # ms

# Umbrales de recursos
HEALTH_CHECK_MEMORY_WARNING=80      # %
HEALTH_CHECK_MEMORY_CRITICAL=95     # %
HEALTH_CHECK_DISK_WARNING=85        # %
HEALTH_CHECK_DISK_CRITICAL=95       # %

# URLs de verificación
HEALTH_CHECK_API_URL=http://localhost:8000/health
HEALTH_CHECK_FRONTEND_URL=http://localhost:3000
```

### Personalizar Verificaciones

#### Backend - Agregar Nueva Verificación
```python
async def check_custom_service(self) -> Dict[str, Any]:
    """Verificación personalizada"""
    try:
        # Lógica de verificación
        return {
            'status': 'healthy',
            'custom_metric': 'value'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

# Agregar a la lista de verificaciones en run_all_checks()
checks = [
    ('api', self.check_api_health()),
    ('database', self.check_database_health()),
    ('custom', self.check_custom_service()),  # Nueva verificación
    # ... otras verificaciones
]
```

#### Frontend - Agregar Nueva Verificación
```javascript
async checkCustomService() {
    try {
        // Lógica de verificación
        return {
            status: 'healthy',
            customMetric: 'value'
        };
    } catch (error) {
        return {
            status: 'unhealthy',
            error: error.message
        };
    }
}

// Agregar a la lista en runAllChecks()
const checks = [
    { name: 'nextjs', check: this.checkNextJSHealth() },
    { name: 'custom', check: this.checkCustomService() }, // Nueva verificación
    // ... otras verificaciones
];
```

## 🚨 Monitoreo y Alertas

### Integración con Sistemas de Monitoreo

#### Prometheus
Los health checks exponen métricas para Prometheus:
```prometheus
# Métricas disponibles
gym_health_check_status{service="backend",status="healthy"} 1
gym_health_check_response_time{service="backend"} 0.234
gym_health_check_last_success{service="backend"} 1706889600
```

#### Grafana
Dashboard recomendado con paneles para:
- Estado general del sistema
- Tiempos de respuesta por servicio
- Historial de disponibilidad
- Alertas de servicios críticos

#### Alertas por Email/Slack
```bash
# Script de ejemplo para alertas
#!/bin/bash
HEALTH_STATUS=$(./scripts/health_check_all.sh --format json | jq -r '.overall_status')

if [ "$HEALTH_STATUS" != "HEALTHY" ]; then
    # Enviar alerta
    curl -X POST \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"🚨 Sistema no saludable: $HEALTH_STATUS\"}" \
        $SLACK_WEBHOOK_URL
fi
```

### Configuración de Cron para Monitoreo Continuo

```bash
# Verificar cada 5 minutos
*/5 * * * * /path/to/gym-system/scripts/health_check_all.sh > /dev/null 2>&1

# Verificar cada hora con alertas
0 * * * * /path/to/gym-system/scripts/health_check_all.sh --format json | /path/to/alert_script.sh
```

## 🛠️ Solución de Problemas

### Problemas Comunes

#### ❌ "Database connection failed"
**Causa:** PostgreSQL no está disponible o credenciales incorrectas
**Solución:**
1. Verificar que el contenedor PostgreSQL esté ejecutándose
2. Comprobar variables de entorno de conexión
3. Verificar logs del contenedor: `docker logs gym_postgres`

#### ❌ "Redis connection failed"
**Causa:** Redis no está disponible o contraseña incorrecta
**Solución:**
1. Verificar que el contenedor Redis esté ejecutándose
2. Comprobar contraseña de Redis
3. Verificar logs del contenedor: `docker logs gym_redis`

#### ❌ "API timeout"
**Causa:** Backend sobrecargado o no responsivo
**Solución:**
1. Verificar logs del backend: `docker logs gym_backend`
2. Comprobar uso de CPU y memoria
3. Reiniciar el servicio si es necesario

#### ❌ "Frontend build files missing"
**Causa:** Build de Next.js incompleto o corrupto
**Solución:**
1. Reconstruir el contenedor frontend
2. Verificar variables de entorno de build
3. Comprobar logs de build de Next.js

### Debugging de Health Checks

#### Ejecutar Health Checks en Modo Debug
```bash
# Backend con logs detallados
docker exec gym_backend python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
exec(open('/app/scripts/healthcheck.py').read())
"

# Frontend con logs detallados
docker exec gym_frontend node -e "
console.log('Debug mode enabled');
require('/app/scripts/healthcheck.js');
"
```

#### Verificar Conectividad Manual
```bash
# PostgreSQL
docker exec gym_postgres pg_isready -U $GYM_DB_USER -d $GYM_DB_NAME

# Redis
docker exec gym_redis redis-cli ping

# Backend API
curl -v http://localhost:8000/health

# Frontend
curl -v http://localhost:3000
```

## 📈 Métricas y Rendimiento

### Métricas Clave Monitoreadas

| Métrica | Umbral Saludable | Umbral Advertencia | Umbral Crítico |
|---------|------------------|-------------------|----------------|
| Tiempo Respuesta API | < 500ms | 500ms - 2s | > 2s |
| Tiempo Respuesta DB | < 100ms | 100ms - 500ms | > 500ms |
| Tiempo Respuesta Redis | < 10ms | 10ms - 50ms | > 50ms |
| Uso de Memoria | < 70% | 70% - 85% | > 85% |
| Uso de Disco | < 80% | 80% - 90% | > 90% |
| CPU del Sistema | < 70% | 70% - 85% | > 85% |

### Optimización de Health Checks

1. **Cachear Resultados:** Evitar verificaciones muy frecuentes
2. **Timeouts Apropiados:** Balancear rapidez vs precisión
3. **Verificaciones Graduales:** Checks básicos antes que complejos
4. **Logs Estructurados:** JSON para facilitar parsing
5. **Métricas Históricas:** Tendencias para análisis predictivo

---

**Nota:** Este sistema de health checks está diseñado para proporcionar visibilidad completa del estado del sistema y facilitar el diagnóstico rápido de problemas. 