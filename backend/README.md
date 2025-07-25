# GymSystem Backend API

Sistema de gestión integral para gimnasios - API Backend desarrollada con FastAPI.

## Características

- **Autenticación y Autorización**: JWT tokens, roles y permisos
- **Gestión de Usuarios**: Registro, perfil, verificación de email
- **Membresías**: Tipos, suscripciones, renovaciones, congelamiento
- **Ejercicios**: Catálogo completo con categorías y dificultades
- **Rutinas**: Plantillas y asignaciones personalizadas
- **Clases**: Programación, reservas y asistencia
- **Empleados**: Gestión de personal, horarios y nómina
- **Pagos**: Procesamiento, facturación y reportes
- **Reportes**: Analytics completos y exportación de datos
- **Middleware**: Seguridad, logging, rate limiting
- **Base de Datos**: PostgreSQL con SQLAlchemy ORM

## Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para base de datos
- **PostgreSQL**: Base de datos relacional
- **Pydantic**: Validación de datos
- **JWT**: Autenticación con tokens
- **Alembic**: Migraciones de base de datos
- **Uvicorn**: Servidor ASGI
- **Redis**: Cache y tareas en segundo plano
- **Celery**: Procesamiento asíncrono

## Instalación

### Prerrequisitos

- Python 3.8+
- PostgreSQL 12+
- Redis (opcional, para cache y tareas)

### Configuración del Entorno

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd gym-system-v6/backend
```

2. **Crear entorno virtual**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Configurar base de datos**
```bash
# Crear base de datos PostgreSQL
createdb gymsystem

# Ejecutar migraciones
alembic upgrade head
```

### Variables de Entorno Principales

```env
# Base de datos
DATABASE_URL=postgresql://username:password@localhost:5432/gymsystem

# Seguridad
SECRET_KEY=your-super-secret-key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Ejecución

### Desarrollo
```bash
# Ejecutar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# O usando el script principal
python -m app.main
```

### Producción
```bash
# Con Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Con Docker
docker build -t gymsystem-api .
docker run -p 8000:8000 gymsystem-api
```

## Estructura del Proyecto

```
backend/
├── app/
│   ├── api/                 # Endpoints de la API
│   │   ├── auth.py         # Autenticación
│   │   ├── users.py        # Gestión de usuarios
│   │   ├── memberships.py  # Membresías
│   │   ├── exercises.py    # Ejercicios
│   │   ├── routines.py     # Rutinas
│   │   ├── classes.py      # Clases
│   │   ├── employees.py    # Empleados
│   │   ├── payments.py     # Pagos
│   │   └── reports.py      # Reportes
│   ├── core/               # Configuración central
│   │   ├── config.py       # Configuraciones
│   │   ├── database.py     # Conexión a BD
│   │   ├── auth.py         # Autenticación
│   │   ├── middleware.py   # Middleware personalizado
│   │   └── utils.py        # Utilidades
│   ├── models/             # Modelos de datos
│   ├── schemas/            # Esquemas Pydantic
│   └── main.py             # Aplicación principal
├── alembic/                # Migraciones
├── tests/                  # Pruebas
├── requirements.txt        # Dependencias
├── .env.example           # Variables de entorno
└── README.md              # Documentación
```

## API Endpoints

### Autenticación
- `POST /api/v1/auth/register` - Registro de usuario
- `POST /api/v1/auth/login` - Inicio de sesión
- `POST /api/v1/auth/refresh` - Renovar token
- `POST /api/v1/auth/logout` - Cerrar sesión
- `POST /api/v1/auth/forgot-password` - Recuperar contraseña
- `POST /api/v1/auth/reset-password` - Restablecer contraseña

### Usuarios
- `GET /api/v1/users` - Listar usuarios
- `GET /api/v1/users/{id}` - Obtener usuario
- `POST /api/v1/users` - Crear usuario
- `PUT /api/v1/users/{id}` - Actualizar usuario
- `DELETE /api/v1/users/{id}` - Eliminar usuario

### Membresías
- `GET /api/v1/memberships` - Listar membresías
- `POST /api/v1/memberships` - Crear membresía
- `PUT /api/v1/memberships/{id}` - Actualizar membresía
- `POST /api/v1/memberships/{id}/renew` - Renovar membresía
- `POST /api/v1/memberships/{id}/freeze` - Congelar membresía

### Ejercicios
- `GET /api/v1/exercises` - Listar ejercicios
- `POST /api/v1/exercises` - Crear ejercicio
- `GET /api/v1/exercises/categories` - Categorías
- `GET /api/v1/exercises/muscles` - Grupos musculares

### Clases
- `GET /api/v1/classes` - Listar clases
- `POST /api/v1/classes` - Crear clase
- `POST /api/v1/classes/{id}/reserve` - Reservar clase
- `DELETE /api/v1/classes/{id}/cancel` - Cancelar reserva

### Pagos
- `GET /api/v1/payments` - Listar pagos
- `POST /api/v1/payments` - Procesar pago
- `GET /api/v1/payments/stats` - Estadísticas
- `GET /api/v1/payments/revenue-report` - Reporte de ingresos

### Reportes
- `GET /api/v1/reports/membership-report` - Reporte de membresías
- `GET /api/v1/reports/payment-report` - Reporte de pagos
- `GET /api/v1/reports/attendance-report` - Reporte de asistencia
- `GET /api/v1/reports/export/{type}` - Exportar datos

## Documentación de la API

Cuando el servidor esté ejecutándose, puedes acceder a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Autenticación

La API utiliza JWT (JSON Web Tokens) para autenticación:

1. **Registro/Login**: Obtén un token de acceso
2. **Headers**: Incluye `Authorization: Bearer <token>` en las peticiones
3. **Refresh**: Usa el refresh token para obtener nuevos access tokens

### Ejemplo de uso

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/v1/auth/login', {
    'email': 'user@example.com',
    'password': 'password123'
})
token = response.json()['access_token']

# Usar token en peticiones
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8000/api/v1/users/me', headers=headers)
```

## Roles y Permisos

- **OWNER**: Acceso completo al sistema
- **ADMIN**: Gestión administrativa
- **MANAGER**: Gestión operativa
- **TRAINER**: Gestión de clases y rutinas
- **STAFF**: Operaciones básicas
- **MEMBER**: Usuario final

## Base de Datos

### Migraciones

```bash
# Crear nueva migración
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1
```

### Modelos Principales

- **User**: Usuarios del sistema
- **Membership**: Membresías y suscripciones
- **MembershipType**: Tipos de membresía
- **Exercise**: Catálogo de ejercicios
- **Routine**: Rutinas de entrenamiento
- **Class**: Clases programadas
- **Employee**: Personal del gimnasio
- **Payment**: Transacciones y pagos
- **Invoice**: Facturación

## Testing

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar con cobertura
pytest --cov=app

# Ejecutar pruebas específicas
pytest tests/test_auth.py
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/gymsystem
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=gymsystem
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    
volumes:
  postgres_data:
```

## Monitoreo y Logs

- **Health Check**: `GET /health`
- **Logs**: Configurados con loguru
- **Métricas**: Middleware de logging personalizado
- **Rate Limiting**: Protección contra abuso

## Seguridad

- **HTTPS**: Recomendado en producción
- **CORS**: Configurado para dominios específicos
- **Headers de Seguridad**: X-Frame-Options, CSP, etc.
- **Validación de Entrada**: Pydantic schemas
- **Rate Limiting**: Protección contra ataques
- **SQL Injection**: Protegido por SQLAlchemy ORM

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Para soporte técnico o preguntas:
- Email: soporte@gymsystem.com
- Documentación: [docs.gymsystem.com](https://docs.gymsystem.com)
- Issues: [GitHub Issues](https://github.com/tu-usuario/gym-system-v6/issues)