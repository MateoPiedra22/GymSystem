# 📡 Documentación de API - Sistema de Gestión de Gimnasio v6

**API REST completa y optimizada para la gestión integral de gimnasios**

## 🌟 Introducción

La API del Sistema de Gestión de Gimnasio v6 está construida con **FastAPI** y proporciona endpoints completos para todas las funcionalidades del sistema. Está diseñada siguiendo principios REST, con documentación automática y validación de datos.

### 🔗 URLs Base

- **Desarrollo**: `http://localhost:8000`
- **Producción**: `https://api.tu-gimnasio.com`
- **Documentación interactiva**: `/docs`
- **Esquema OpenAPI**: `/openapi.json`

### 🏗️ Arquitectura de la API

```
┌─────────────────┐
│   API Gateway   │ ← Rate Limiting, CORS, Auth
├─────────────────┤
│   Middleware    │ ← Logging, Error Handling
├─────────────────┤
│   Routers       │ ← Endpoints organizados
├─────────────────┤
│   Services      │ ← Lógica de negocio
├─────────────────┤
│   Models        │ ← ORM y Base de datos
└─────────────────┘
```

## 🔐 Autenticación

### JWT Bearer Token

La API utiliza **JSON Web Tokens (JWT)** para autenticación. Todos los endpoints protegidos requieren un token válido.

#### **Login**
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "tu_password"
}
```

**Respuesta exitosa:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user-id-123",
    "username": "admin",
    "nombre": "Administrador",
    "es_admin": true
  }
}
```

#### **Usar Token**
```http
GET /api/usuarios
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### **Renovar Token**
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### **Logout**
```http
POST /auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 👥 Usuarios

### **Listar Usuarios**
```http
GET /api/usuarios?page=1&size=50&search=juan&activo=true
Authorization: Bearer <token>
```

**Parámetros de consulta:**
- `page` (int, opcional): Número de página (default: 1)
- `size` (int, opcional): Elementos por página (default: 50, max: 100)
- `search` (string, opcional): Búsqueda en nombre, apellido, email
- `activo` (boolean, opcional): Filtrar por estado activo
- `plan` (string, opcional): Filtrar por tipo de plan

**Respuesta:**
```json
{
  "items": [
    {
      "id": "user-123",
      "nombre": "Juan",
      "apellido": "Pérez",
      "email": "juan.perez@email.com",
      "telefono": "+34 600 123 456",
      "username": "juan.perez",
      "fecha_nacimiento": "1990-05-15",
      "genero": "M",
      "esta_activo": true,
      "es_admin": false,
      "fecha_registro": "2024-01-15T10:30:00Z",
      "ultimo_acceso": "2024-01-20T14:22:00Z",
      "plan": {
        "id": "plan-123",
        "nombre": "Premium",
        "precio": 49.99
      },
      "stats": {
        "asistencias_mes": 12,
        "clases_reservadas": 3
      }
    }
  ],
  "total": 156,
  "page": 1,
  "size": 50,
  "pages": 4
}
```

### **Obtener Usuario**
```http
GET /api/usuarios/{user_id}
Authorization: Bearer <token>
```

### **Crear Usuario**
```http
POST /api/usuarios
Authorization: Bearer <token>
Content-Type: application/json

{
  "nombre": "María",
  "apellido": "García",
  "email": "maria.garcia@email.com",
  "telefono": "+34 600 654 321",
  "username": "maria.garcia",
  "password": "password_segura",
  "fecha_nacimiento": "1985-10-20",
  "genero": "F",
  "direccion": "Calle Principal 123",
  "ciudad": "Madrid",
  "codigo_postal": "28001",
  "plan_id": "plan-123",
  "datos_medicos": {
    "altura": 165,
    "peso": 60,
    "alergias": "Ninguna",
    "condiciones": "Ninguna"
  }
}
```

**Respuesta:**
```json
{
  "id": "user-456",
  "nombre": "María",
  "apellido": "García",
  "email": "maria.garcia@email.com",
  "username": "maria.garcia",
  "fecha_registro": "2024-01-20T15:30:00Z",
  "esta_activo": true,
  "message": "Usuario creado exitosamente"
}
```

### **Actualizar Usuario**
```http
PUT /api/usuarios/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "telefono": "+34 600 999 888",
  "plan_id": "plan-456"
}
```

### **Eliminar Usuario**
```http
DELETE /api/usuarios/{user_id}
Authorization: Bearer <token>
```

## 🏃‍♀️ Clases

### **Listar Clases**
```http
GET /api/clases?fecha=2024-01-20&instructor=juan&disponible=true
Authorization: Bearer <token>
```

**Parámetros:**
- `fecha` (date, opcional): Filtrar por fecha (YYYY-MM-DD)
- `instructor` (string, opcional): Filtrar por instructor
- `disponible` (boolean, opcional): Solo clases con cupos disponibles
- `tipo` (string, opcional): Tipo de clase

**Respuesta:**
```json
{
  "items": [
    {
      "id": "clase-123",
      "nombre": "Yoga Avanzado",
      "descripcion": "Clase de yoga para nivel avanzado",
      "tipo": "yoga",
      "fecha": "2024-01-20",
      "hora_inicio": "09:00",
      "hora_fin": "10:30",
      "duracion_minutos": 90,
      "capacidad_maxima": 15,
      "inscritos": 12,
      "disponibles": 3,
      "precio": 25.00,
      "instructor": {
        "id": "emp-123",
        "nombre": "Ana",
        "apellido": "López",
        "especialidad": "Yoga"
      },
      "sala": "Sala 1",
      "equipamiento": ["esterillas", "bloques"],
      "nivel": "avanzado",
      "estado": "programada"
    }
  ],
  "total": 24,
  "page": 1,
  "size": 50
}
```

### **Crear Clase**
```http
POST /api/clases
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "nombre": "HIIT Matutino",
  "descripcion": "Entrenamiento de alta intensidad",
  "tipo": "hiit",
  "fecha": "2024-01-25",
  "hora_inicio": "07:00",
  "hora_fin": "08:00",
  "capacidad_maxima": 20,
  "precio": 30.00,
  "instructor_id": "emp-456",
  "sala": "Sala 2",
  "equipamiento": ["pesas", "mancuernas"],
  "nivel": "intermedio",
  "recurrente": true,
  "dias_semana": ["lunes", "miércoles", "viernes"],
  "fecha_fin_recurrencia": "2024-03-31"
}
```

### **Inscribirse a Clase**
```http
POST /api/clases/{clase_id}/inscribir
Authorization: Bearer <token>
Content-Type: application/json

{
  "usuario_id": "user-123",
  "notas": "Primera vez en esta clase"
}
```

### **Cancelar Inscripción**
```http
DELETE /api/clases/{clase_id}/inscripcion/{usuario_id}
Authorization: Bearer <token>
```

## 📅 Asistencias

### **Registrar Asistencia**
```http
POST /api/asistencias
Authorization: Bearer <token>
Content-Type: application/json

{
  "usuario_id": "user-123",
  "clase_id": "clase-456",
  "tipo": "entrada",
  "fecha": "2024-01-20T09:05:00Z",
  "notas": "Llegó 5 minutos tarde"
}
```

### **Listar Asistencias**
```http
GET /api/asistencias?usuario_id=user-123&fecha_desde=2024-01-01&fecha_hasta=2024-01-31
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "items": [
    {
      "id": "asist-123",
      "usuario": {
        "id": "user-123",
        "nombre": "Juan Pérez"
      },
      "clase": {
        "id": "clase-456",
        "nombre": "Yoga Avanzado",
        "fecha": "2024-01-20",
        "hora_inicio": "09:00"
      },
      "fecha": "2024-01-20T09:05:00Z",
      "tipo": "entrada",
      "duracion_minutos": 85,
      "notas": "Llegó 5 minutos tarde"
    }
  ],
  "estadisticas": {
    "total_asistencias": 15,
    "promedio_semanal": 3.75,
    "clases_favoritas": ["Yoga Avanzado", "HIIT Matutino"]
  }
}
```

## 💰 Pagos

### **Listar Pagos**
```http
GET /api/pagos?usuario_id=user-123&estado=pendiente
Authorization: Bearer <token>
```

### **Procesar Pago**
```http
POST /api/pagos
Authorization: Bearer <token>
Content-Type: application/json

{
  "usuario_id": "user-123",
  "concepto": "mensualidad",
  "monto": 49.99,
  "metodo_pago": "tarjeta",
  "referencia": "CARD-123456",
  "fecha_vencimiento": "2024-02-20",
  "descuento": 5.00,
  "detalles": {
    "plan": "Premium",
    "periodo": "2024-02"
  }
}
```

**Respuesta:**
```json
{
  "id": "pago-789",
  "usuario_id": "user-123",
  "concepto": "mensualidad",
  "monto": 49.99,
  "descuento": 5.00,
  "total": 44.99,
  "metodo_pago": "tarjeta",
  "estado": "completado",
  "fecha_pago": "2024-01-20T16:30:00Z",
  "referencia": "CARD-123456",
  "recibo_url": "/api/pagos/789/recibo"
}
```

### **Generar Recibo**
```http
GET /api/pagos/{pago_id}/recibo
Authorization: Bearer <token>
Accept: application/pdf
```

## 👨‍🏫 Empleados

### **Listar Empleados**
```http
GET /api/empleados?tipo=instructor&activo=true
Authorization: Bearer <admin_token>
```

### **Crear Empleado**
```http
POST /api/empleados
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "nombre": "Carlos",
  "apellido": "Ruiz",
  "email": "carlos.ruiz@gimnasio.com",
  "telefono": "+34 600 111 222",
  "tipo_empleado": "instructor",
  "especialidades": ["crossfit", "funcional"],
  "salario": 2500.00,
  "fecha_contratacion": "2024-01-15",
  "horario": {
    "lunes": ["07:00-12:00", "16:00-21:00"],
    "martes": ["07:00-12:00"],
    "miércoles": ["07:00-12:00", "16:00-21:00"],
    "jueves": ["07:00-12:00"],
    "viernes": ["07:00-12:00", "16:00-21:00"]
  },
  "certificaciones": [
    {
      "nombre": "CrossFit Level 1",
      "fecha_obtencion": "2023-06-15",
      "fecha_vencimiento": "2025-06-15"
    }
  ]
}
```

## 📊 Reportes y Analytics

### **KPIs Principales**
```http
GET /api/reportes/kpis?periodo=mes&fecha=2024-01
Authorization: Bearer <admin_token>
```

**Respuesta:**
```json
{
  "periodo": "2024-01",
  "kpis": {
    "ingresos_mes": 15420.50,
    "nuevas_inscripciones_mes": 23,
    "usuarios_activos": 156,
    "tasa_retencion": 87.5,
    "ocupacion_promedio_clases": 78.3,
    "ingresos_por_usuario": 98.85,
    "clases_mas_populares": [
      {"nombre": "Yoga Avanzado", "asistencias": 145},
      {"nombre": "HIIT Matutino", "asistencias": 120}
    ],
    "horarios_pico": [
      {"hora": "18:00-19:00", "ocupacion": 95.2},
      {"hora": "19:00-20:00", "ocupacion": 89.1}
    ]
  },
  "comparacion_mes_anterior": {
    "ingresos": 8.5,
    "inscripciones": 15.0,
    "retencion": -2.1
  }
}
```

### **Datos para Gráficos**
```http
GET /api/reportes/graficos?tipo=ingresos&periodo=trimestre
Authorization: Bearer <admin_token>
```

**Respuesta:**
```json
{
  "ingresos_mensuales": {
    "labels": ["Oct 2023", "Nov 2023", "Dic 2023", "Ene 2024"],
    "values": [12450.30, 13680.75, 16230.50, 15420.50]
  },
  "asistencias_por_dia": {
    "labels": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
    "values": [145, 132, 158, 143, 167, 89, 45]
  },
  "metodos_pago": {
    "labels": ["Tarjeta", "Efectivo", "Transferencia"],
    "values": [65.2, 23.8, 11.0]
  },
  "nuevos_usuarios": {
    "labels": ["Semana 1", "Semana 2", "Semana 3", "Semana 4"],
    "values": [8, 6, 5, 4]
  }
}
```

### **Reporte de Asistencias**
```http
GET /api/reportes/asistencias?fecha_desde=2024-01-01&fecha_hasta=2024-01-31&formato=excel
Authorization: Bearer <admin_token>
```

### **Reporte de Ingresos**
```http
GET /api/reportes/ingresos?agrupacion=semanal&incluir_proyeccion=true
Authorization: Bearer <admin_token>
```

## 🏥 Health Check

### **Estado del Sistema**
```http
GET /health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T16:45:30Z",
  "version": "6.0.0",
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5.2,
      "connections": {
        "active": 8,
        "max": 20
      }
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 1.8,
      "memory_usage": "45MB"
    },
    "external_apis": {
      "payment_gateway": "healthy",
      "email_service": "healthy"
    }
  },
  "metrics": {
    "requests_per_minute": 234,
    "average_response_time_ms": 156,
    "error_rate": 0.02
  }
}
```

## 🔧 Configuración y Administración

### **Configuración del Sistema**
```http
GET /api/admin/config
Authorization: Bearer <admin_token>
```

```http
PUT /api/admin/config
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "gimnasio": {
    "nombre": "FitGym Premium",
    "direccion": "Av. Principal 123",
    "telefono": "+34 91 123 4567",
    "email": "info@fitgym.com",
    "horarios": {
      "lunes_viernes": "06:00-23:00",
      "sabado": "08:00-22:00",
      "domingo": "09:00-21:00"
    }
  },
  "pagos": {
    "metodos_aceptados": ["tarjeta", "efectivo", "transferencia"],
    "descuento_maximo": 20.0,
    "dias_gracia": 5
  },
  "clases": {
    "reserva_maxima_dias": 7,
    "cancelacion_horas_minimas": 2,
    "lista_espera_activa": true
  }
}
```

## 📡 WebSockets (Tiempo Real)

### **Conexión WebSocket**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/token_aqui');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Actualización en tiempo real:', data);
};
```

**Eventos disponibles:**
- `nueva_inscripcion`: Nueva inscripción a clase
- `pago_recibido`: Pago procesado
- `clase_actualizada`: Cambios en clase
- `usuario_asistencia`: Nueva asistencia registrada

## 🚨 Códigos de Error

### **Códigos HTTP Estándar**

| Código | Descripción | Ejemplo |
|--------|-------------|---------|
| 200 | OK | Operación exitosa |
| 201 | Created | Recurso creado |
| 400 | Bad Request | Datos inválidos |
| 401 | Unauthorized | Token inválido |
| 403 | Forbidden | Sin permisos |
| 404 | Not Found | Recurso no encontrado |
| 422 | Validation Error | Error de validación |
| 429 | Too Many Requests | Rate limit excedido |
| 500 | Internal Error | Error del servidor |

### **Estructura de Errores**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Los datos enviados no son válidos",
    "details": [
      {
        "field": "email",
        "message": "El formato del email no es válido"
      }
    ],
    "timestamp": "2024-01-20T16:45:30Z",
    "request_id": "req-123456"
  }
}
```

## 🔄 Rate Limiting

La API implementa rate limiting para prevenir abuso:

- **Usuarios autenticados**: 1000 requests/hora
- **Endpoints de login**: 10 intentos/minuto
- **Endpoints públicos**: 100 requests/hora
- **Endpoints de reportes**: 60 requests/hora

Headers de respuesta:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642687200
```

## 🧪 Testing de la API

### **Ejemplos con cURL**

```bash
# Obtener token
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

# Listar usuarios
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/usuarios"

# Crear usuario
curl -X POST "http://localhost:8000/api/usuarios" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Test User",
    "email": "test@example.com",
    "username": "testuser"
  }'
```

### **Colección Postman**

Importar la colección desde: [`docs/postman/gym-api.json`](postman/gym-api.json)

### **Tests Automatizados**

```bash
# Ejecutar tests de API
pytest tests/test_api/ -v

# Tests de performance
pytest tests/test_performance.py -m api

# Tests de seguridad
pytest tests/test_security.py -m api
```

## 📱 SDKs y Clientes

### **JavaScript/TypeScript**
```typescript
import { GymAPI } from '@gym-system/api-client';

const client = new GymAPI({
  baseURL: 'http://localhost:8000',
  token: 'your-token-here'
});

// Listar usuarios
const users = await client.usuarios.list({
  page: 1,
  size: 20
});

// Crear usuario
const newUser = await client.usuarios.create({
  nombre: 'Juan',
  email: 'juan@email.com'
});
```

### **Python**
```python
from gym_api_client import GymClient

client = GymClient(
    base_url='http://localhost:8000',
    token='your-token-here'
)

# Listar usuarios
users = client.usuarios.list(page=1, size=20)

# Crear usuario
new_user = client.usuarios.create({
    'nombre': 'Juan',
    'email': 'juan@email.com'
})
```

## 🔮 Próximas Versiones

### **v6.1**
- GraphQL endpoint
- Webhooks para eventos
- API de métricas avanzadas

### **v6.2**
- Multi-tenancy
- API para móviles optimizada
- Integración con wearables

---

## 📞 Soporte

- **Documentación**: [/docs](http://localhost:8000/docs)
- **Issues**: [GitHub](https://github.com/tu-usuario/gym-system-v6/issues)
- **Email**: api-support@gym-system.com

---

*Documentación generada automáticamente con OpenAPI 3.0*
