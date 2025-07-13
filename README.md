# 🏋️ Sistema de Gestión de Gimnasio v6.0

Sistema completo de gestión para gimnasios con sincronización P2P, incluyendo versión web moderna con Next.js, API REST robusta y base de datos PostgreSQL.

## 🚀 Características Principales

### 🌐 **Frontend Web (Next.js)**
- **Dashboard Moderno**: Interfaz ultra moderna con diseño responsive
- **Gestión Completa**: Usuarios, clases, pagos, asistencias, empleados, rutinas
- **Reportes Avanzados**: Gráficos interactivos y análisis en tiempo real
- **Sistema de Temas**: Modo claro/oscuro automático
- **PWA Ready**: Aplicación web progresiva
- **Optimizado**: SSR, cache inteligente, lazy loading

### 🔧 **Backend API (FastAPI)**
- **API REST Completa**: Endpoints para todos los recursos
- **Autenticación JWT**: Sistema seguro de login
- **Base de Datos PostgreSQL**: Escalable y robusta
- **Cache Redis**: Rendimiento optimizado
- **Documentación Automática**: Swagger/OpenAPI
- **Validaciones**: Zod schemas para datos seguros

### 🗄️ **Base de Datos**
- **PostgreSQL 15**: Base de datos principal
- **Redis**: Cache y sesiones
- **Migraciones Automáticas**: Alembic
- **Backup Automático**: Sistema de respaldos

### 🔄 **Sincronización P2P**
- **Red Distribuida**: Sincronización entre nodos
- **Offline First**: Funciona sin conexión
- **Conflict Resolution**: Resolución automática de conflictos
- **Real-time**: Actualizaciones en tiempo real

## 🐳 Instalación con Docker

### Requisitos Previos
- Docker Desktop (Windows/Mac) o Docker Engine (Linux)
- Docker Compose
- Mínimo 4GB RAM disponible
- 10GB espacio libre

### Instalación Rápida

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/gym-system-v6.git
cd gym-system-v6
```

2. **Ejecutar instalador automático**
```bash
# Windows
INSTALAR_SISTEMA.bat

# Linux/Mac
./install-production.sh
```

3. **Acceder al sistema**
- Frontend Web: http://localhost:3000
- Backend API: http://localhost:8000
- Nginx Proxy: http://localhost

### Instalación Manual

1. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

2. **Construir y levantar servicios**
```bash
# Producción
docker-compose up -d

# Desarrollo
docker-compose -f docker-compose.dev.yml up -d
```

3. **Verificar estado**
```bash
docker-compose ps
docker-compose logs -f
```

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Redis         │    │   Volumes       │
│   (Reverse      │    │   (Cache)       │    │   (Data)        │
│    Proxy)       │    │   Port: 6379    │    │                 │
│   Port: 80/443  │    └─────────────────┘    └─────────────────┘
└─────────────────┘
```

## 📁 Estructura del Proyecto

```
gym-system-v6/
├── web/                          # Frontend Next.js
│   ├── app/                      # App Router (Next.js 13+)
│   │   ├── components/           # Componentes reutilizables
│   │   ├── hooks/                # Hooks personalizados
│   │   ├── types/                # Tipos TypeScript
│   │   ├── utils/                # Utilidades
│   │   ├── styles/               # Estilos CSS
│   │   └── [pages]/              # Páginas de la aplicación
│   ├── Dockerfile                # Configuración Docker
│   ├── next.config.js            # Configuración Next.js
│   └── package.json              # Dependencias
├── backend/                      # Backend FastAPI
│   ├── app/                      # Código de la aplicación
│   ├── migrations/               # Migraciones de BD
│   ├── Dockerfile                # Configuración Docker
│   └── requirements.txt          # Dependencias Python
├── nginx/                        # Configuración Nginx
├── docker-compose.yml            # Orquestación Docker
├── docker-compose.dev.yml        # Configuración desarrollo
└── .env                          # Variables de entorno
```

## 🎯 Funcionalidades por Módulo

### 👥 **Gestión de Usuarios**
- ✅ CRUD completo de usuarios
- ✅ Gestión de membresías
- ✅ Historial de pagos
- ✅ Control de asistencia
- ✅ Objetivos y progreso
- ✅ Fotos y documentos

### 📅 **Gestión de Clases**
- ✅ Programación de clases
- ✅ Control de capacidad
- ✅ Inscripciones
- ✅ Asistencia por clase
- ✅ Instructores
- ✅ Calendario interactivo

### 💰 **Gestión de Pagos**
- ✅ Múltiples métodos de pago
- ✅ Facturación automática
- ✅ Recordatorios
- ✅ Reportes financieros
- ✅ Descuentos y promociones
- ✅ Estados de pago

### 📊 **Reportes y Analytics**
- ✅ Dashboard en tiempo real
- ✅ Gráficos interactivos
- ✅ Exportación de datos
- ✅ KPIs personalizables
- ✅ Análisis de tendencias
- ✅ Reportes automáticos

### 👨‍💼 **Gestión de Empleados**
- ✅ Información personal
- ✅ Horarios y turnos
- ✅ Nómina y comisiones
- ✅ Evaluaciones
- ✅ Certificaciones
- ✅ Control de acceso

## 🔧 Configuración Avanzada

### Variables de Entorno Principales

```bash
# Base de Datos
GYM_DB_NAME=gym_db
GYM_DB_USER=gym_user
GYM_DB_PASSWORD=secure_password

# Redis
GYM_REDIS_PASSWORD=redis_password

# Seguridad
GYM_SECRET_KEY=your_secret_key
GYM_JWT_SECRET_KEY=your_jwt_secret

# URLs
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Puertos
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### Comandos Docker Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar servicios
docker-compose restart

# Ver estado de contenedores
docker-compose ps

# Ejecutar comandos en contenedores
docker-compose exec backend python manage.py migrate
docker-compose exec frontend npm run build

# Backup de base de datos
docker-compose exec postgres pg_dump -U gym_user gym_db > backup.sql

# Restaurar backup
docker-compose exec -T postgres psql -U gym_user gym_db < backup.sql
```

## 🚀 Despliegue en Producción

### Configuración SSL/HTTPS
```bash
# Generar certificados SSL
./scripts/generate-ssl.sh

# Configurar dominio
DOMAIN=tu-gimnasio.com
SSL_EMAIL=admin@tu-gimnasio.com
```

### Monitoreo y Logs
```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Monitoreo con Prometheus
docker-compose -f docker-compose.monitoring.yml up -d

# Health checks
curl http://localhost/health
curl http://localhost/nginx-health
```

### Backup Automático
```bash
# Configurar backup automático
BACKUP_SCHEDULE="0 2 * * *"  # Diario a las 2 AM
BACKUP_RETENTION_DAYS=30

# Backup manual
docker-compose exec backup ./backup.sh
```

## 🛠️ Desarrollo

### Modo Desarrollo
```bash
# Levantar servicios de desarrollo
docker-compose -f docker-compose.dev.yml up -d

# Hot reload activado
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### Testing
```bash
# Tests del frontend
docker-compose exec frontend npm test

# Tests del backend
docker-compose exec backend pytest

# Tests de integración
docker-compose exec backend pytest tests/integration/
```

## 📈 Rendimiento y Escalabilidad

### Optimizaciones Implementadas
- ✅ **Frontend**: SSR, lazy loading, code splitting
- ✅ **Backend**: Async/await, connection pooling
- ✅ **Database**: Índices optimizados, queries eficientes
- ✅ **Cache**: Redis para sesiones y datos frecuentes
- ✅ **CDN**: Assets estáticos optimizados
- ✅ **Compression**: Gzip/Brotli habilitado

### Monitoreo de Recursos
```bash
# Ver uso de recursos
docker stats

# Logs de rendimiento
docker-compose logs backend | grep "performance"
docker-compose logs frontend | grep "build"
```

## 🔒 Seguridad

### Medidas Implementadas
- ✅ **Autenticación**: JWT con refresh tokens
- ✅ **Autorización**: Roles y permisos granulares
- ✅ **Validación**: Input sanitization y validation
- ✅ **HTTPS**: SSL/TLS obligatorio en producción
- ✅ **Headers**: Security headers configurados
- ✅ **Rate Limiting**: Protección contra ataques
- ✅ **Audit Log**: Registro de todas las acciones

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

- 📧 Email: soporte@gymsystem.com
- 📖 Documentación: [docs.gymsystem.com](https://docs.gymsystem.com)
- 🐛 Issues: [GitHub Issues](https://github.com/tu-usuario/gym-system-v6/issues)
- 💬 Discord: [Servidor de la comunidad](https://discord.gg/gymsystem)

## 🙏 Agradecimientos

- **Next.js** por el framework web
- **FastAPI** por el framework backend
- **PostgreSQL** por la base de datos
- **Docker** por la containerización
- **Tailwind CSS** por los estilos
- **Lucide React** por los íconos

---

**Sistema de Gestión de Gimnasio v6.0** - Desarrollado con ❤️ para la comunidad fitness
