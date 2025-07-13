# 🌐 Configuración de Nginx - Sistema de Gestión de Gimnasio v6.0

## 📋 Descripción General

Nginx actúa como reverse proxy y load balancer para el Sistema de Gestión de Gimnasio, proporcionando:
- **Reverse Proxy** para backend FastAPI y frontend Next.js
- **SSL/TLS Termination** con configuración segura
- **Rate Limiting** y protección DDoS
- **Caching** inteligente para optimización
- **Compresión** para reducir ancho de banda
- **Security Headers** para protección avanzada

## 🗂️ Estructura de Archivos

```
nginx/
├── nginx.conf              # Configuración principal
├── conf.d/
│   └── default.conf        # Configuración del sitio
├── snippets/
│   ├── ssl.conf            # Configuración SSL reutilizable
│   └── security.conf       # Headers de seguridad
└── ssl/
    ├── cert.pem           # Certificado SSL
    ├── key.pem            # Clave privada
    ├── chain.pem          # Cadena de certificados
    └── dhparam.pem        # Parámetros Diffie-Hellman
```

## ⚙️ Configuración Principal (nginx.conf)

### Optimizaciones de Performance
- **Worker Processes:** Auto-detección de CPU cores
- **Worker Connections:** 2048 conexiones por worker
- **Keepalive:** Optimizado para reducir latencia
- **Buffers:** Configurados para manejar requests grandes

### Compresión Avanzada
- **Gzip:** Habilitado con nivel 6 para balance performance/compresión
- **Brotli:** Preparado para algoritmo de compresión superior
- **Tipos MIME:** Cobertura completa de archivos web modernos

### Caching Inteligente
- **Proxy Cache:** Cache para responses del backend
- **FastCGI Cache:** Cache para contenido dinámico
- **Static File Cache:** Cache agresivo para archivos estáticos

## 🔄 Configuración del Sitio (default.conf)

### Upstreams Configurados

#### Backend API
```nginx
upstream backend_api {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

#### Frontend Next.js
```nginx
upstream frontend_app {
    least_conn;
    server frontend:3000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

### Routing y Proxy

| Ruta | Destino | Descripción |
|------|---------|-------------|
| `/api/*` | Backend API | Endpoints de la API REST |
| `/api/auth/*` | Backend API | Autenticación (rate limit estricto) |
| `/uploads/*` | Static Files | Archivos subidos por usuarios |
| `/ws` | Backend API | WebSockets para tiempo real |
| `/_next/*` | Frontend | Archivos de build de Next.js |
| `/*` | Frontend | Páginas de la aplicación SPA |

### Rate Limiting

| Zona | Límite | Burst | Uso |
|------|--------|-------|-----|
| `login` | 5 req/min | 5 | Endpoints de autenticación |
| `api` | 10 req/s | 20 | API general |
| `general` | 20 req/s | 30 | Páginas web |
| `static` | 50 req/s | 10 | Archivos estáticos |

## 🔒 Configuración de Seguridad

### Headers de Seguridad Implementados

```nginx
# Prevención de clickjacking
X-Frame-Options: SAMEORIGIN

# Prevención de MIME sniffing
X-Content-Type-Options: nosniff

# Protección XSS
X-XSS-Protection: 1; mode=block

# Política de referrer
Referrer-Policy: strict-origin-when-cross-origin

# Política de contenido (CSP)
Content-Security-Policy: [política específica]

# HSTS para HTTPS
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

### Bloqueos de Seguridad
- **Archivos Sensibles:** `.htaccess`, `.env`, archivos de configuración
- **Scripts Ejecutables:** PHP, Python, etc. en directorio uploads
- **Directorios Ocultos:** Archivos que empiecen con punto
- **Extensiones Peligrosas:** Archivos ejecutables y de configuración

## 🔐 Configuración SSL/TLS

### Protocolos Soportados
- **TLS 1.2** y **TLS 1.3** únicamente
- **Cifrados Seguros:** Solo algoritmos modernos y seguros
- **Perfect Forward Secrecy:** Habilitado con parámetros DH

### Características SSL
- **OCSP Stapling:** Verificación rápida de certificados
- **Session Resumption:** Optimización de handshakes SSL
- **HSTS:** Forzar HTTPS en navegadores compatibles

### Generación de Certificados para Desarrollo

```bash
# Generar certificados auto-firmados
./scripts/generate_ssl_certs.sh

# Certificado para dominio específico
./scripts/generate_ssl_certs.sh -d "gimnasio.local"

# Certificado wildcard
./scripts/generate_ssl_certs.sh -d "*.gimnasio.local" --validity 730
```

## 📊 Monitoreo y Logging

### Logs Configurados

| Archivo | Contenido | Formato |
|---------|-----------|---------|
| `access.log` | Requests HTTP | Detallado con métricas |
| `error.log` | Errores Nginx | Nivel WARNING |
| `gym.access.log` | Aplicación específica | Formato personalizado |
| `uploads.access.log` | Archivos subidos | Seguimiento de uploads |

### Métricas Disponibles

```nginx
# Status de Nginx (solo localhost)
location /nginx_status {
    stub_status on;
    allow 127.0.0.1;
    deny all;
}
```

### Health Checks

```nginx
# Health check para load balancers
location /health {
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}
```

## 🚀 Deployment y Configuración

### Desarrollo Local

1. **Generar Certificados SSL:**
   ```bash
   ./scripts/generate_ssl_certs.sh
   ```

2. **Iniciar con Docker Compose:**
   ```bash
   docker-compose up nginx
   ```

3. **Verificar Configuración:**
   ```bash
   docker exec gym_nginx nginx -t
   ```

### Producción

1. **Usar Certificados Válidos:**
   - Let's Encrypt con Certbot
   - Certificados comerciales
   - Certificados de CA empresarial

2. **Configurar DNS:**
   - Apuntar dominio a IP del servidor
   - Configurar subdominios si es necesario

3. **Optimizar para Carga:**
   ```nginx
   # Aumentar workers para producción
   worker_processes auto;
   worker_connections 4096;
   
   # Aumentar límites de rate limiting
   limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;
   ```

## 🔧 Configuración Avanzada

### Load Balancing (Múltiples Instancias)

```nginx
upstream backend_api {
    least_conn;
    server backend1:8000 max_fails=3 fail_timeout=30s weight=1;
    server backend2:8000 max_fails=3 fail_timeout=30s weight=1;
    server backend3:8000 max_fails=3 fail_timeout=30s weight=2;
    
    # Health checks activos (Nginx Plus)
    # health_check interval=30s fails=3 passes=2;
}
```

### Caching Avanzado

```nginx
# Cache por tipo de contenido
location ~* \.(jpg|jpeg|png|gif|webp)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    proxy_cache gym_cache;
    proxy_cache_valid 200 1y;
}

# Cache para API con invalidación
location /api/data/ {
    proxy_cache gym_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri$http_authorization";
    proxy_cache_bypass $http_cache_control;
}
```

### WebSocket Optimization

```nginx
location /ws {
    proxy_pass http://backend_api;
    
    # WebSocket headers
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # Timeouts largos para conexiones persistentes
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
    
    # Sin buffering para tiempo real
    proxy_buffering off;
}
```

## 🛠️ Solución de Problemas

### Problemas Comunes

#### ❌ "502 Bad Gateway"
**Causa:** Backend no disponible
**Solución:**
1. Verificar que los contenedores backend/frontend estén ejecutándose
2. Comprobar logs: `docker logs gym_nginx`
3. Verificar conectividad: `docker exec gym_nginx curl http://backend:8000/health`

#### ❌ "SSL Certificate Error"
**Causa:** Certificados inválidos o expirados
**Solución:**
1. Regenerar certificados: `./scripts/generate_ssl_certs.sh`
2. Verificar permisos de archivos SSL
3. Reiniciar Nginx: `docker restart gym_nginx`

#### ❌ "Rate Limit Exceeded"
**Causa:** Demasiadas requests desde una IP
**Solución:**
1. Verificar límites en `nginx.conf`
2. Ajustar rates según necesidades
3. Implementar whitelist para IPs confiables

### Debugging

#### Verificar Configuración
```bash
# Test de configuración
docker exec gym_nginx nginx -t

# Reload sin downtime
docker exec gym_nginx nginx -s reload

# Ver configuración activa
docker exec gym_nginx nginx -T
```

#### Logs en Tiempo Real
```bash
# Logs de acceso
docker exec gym_nginx tail -f /var/log/nginx/access.log

# Logs de error
docker exec gym_nginx tail -f /var/log/nginx/error.log

# Logs específicos de la app
docker exec gym_nginx tail -f /var/log/nginx/gym.access.log
```

## 📈 Optimización de Performance

### Tuning de Sistema

```bash
# Aumentar límites del sistema
echo "fs.file-max = 100000" >> /etc/sysctl.conf
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_tw_buckets = 1440000" >> /etc/sysctl.conf
```

### Configuración para Alto Tráfico

```nginx
# Configuración optimizada para alto tráfico
worker_processes auto;
worker_rlimit_nofile 100000;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

# Aumentar buffers
client_body_buffer_size 32k;
large_client_header_buffers 8 16k;
```

### Métricas de Performance

| Métrica | Objetivo | Monitoreo |
|---------|----------|-----------|
| Response Time | < 200ms | Logs de access |
| Throughput | 1000+ req/s | Nginx status |
| Error Rate | < 0.1% | Error logs |
| Cache Hit Rate | > 80% | Cache status |

## 🔍 Monitoring con Prometheus

```nginx
# Métricas para Prometheus (nginx-prometheus-exporter)
location /metrics {
    allow 127.0.0.1;
    allow 10.0.0.0/8;
    deny all;
    
    proxy_pass http://nginx-exporter:9113/metrics;
}
```

---

**Nota:** Esta configuración está optimizada para el Sistema de Gestión de Gimnasio v6.0 y proporciona un balance entre seguridad, performance y facilidad de mantenimiento. 