# Zurka Gym System - Sistema de Administración para Gimnasios

## Descripción

Zurka Gym System es un sistema administrativo especializado para gimnasios con autenticación dual para Dueños y Profesores. Desarrollado con arquitectura moderna usando Python (FastAPI) en el backend y React + TypeScript en el frontend.

## Características Principales

- **Backend**: Python con FastAPI
- **Frontend**: React 18 + TypeScript + Vite
- **Desktop**: Integración con Tauri
- **Base de Datos**: PostgreSQL con SQLAlchemy
- **Styling**: Tailwind CSS + Shadcn/ui
- **Estado**: Zustand
- **Mensajería**: WhatsApp Web API automática
- **Integración**: Instagram Basic Display

## Módulos del Sistema

1. **Dashboard** - Panel de control con +16 KPIs y +12 gráficos
2. **Usuarios** - Gestión completa de miembros
3. **Pagos** - Sistema de facturación y cuotas
4. **Rutinas** - Sistema avanzado con plantillas
5. **Clases** - Programación y reservas
6. **Ejercicios** - Biblioteca completa
7. **Empleados** - Gestión de personal
8. **Comunidad** - Mensajería e Instagram
9. **Configuración** - Personalización total

## Roles de Usuario

- **Dueño**: Control completo del sistema con contraseña maestra
- **Profesor**: Acceso operativo con selección de perfil individual

### Autenticación

#### Acceso de Dueño
- **Contraseña Maestra**: `0000` (por defecto)
- **Acceso**: Completo a todos los módulos del sistema
- **Configuración**: Puede gestionar usuarios, empleados y configuración del gimnasio

#### Acceso de Profesor
- **Método**: Selección de perfil desde lista de profesores
- **Contraseña**: Gestionada individualmente desde el módulo de Usuarios
- **Acceso**: Operativo a rutinas, clases, ejercicios y reportes

### Cambiar Contraseña Maestra

Para cambiar la contraseña maestra del Dueño, modifica el valor en:
```typescript
// frontend/src/store/authStore.ts
if (credentials.password === '0000') { // Cambiar '0000' por nueva contraseña
```

**⚠️ Importante**: Mantén la contraseña maestra segura y cámbiala regularmente.

## Estructura del Proyecto

```
gymsystem/
├── backend/          # API Python FastAPI
├── frontend/         # React + TypeScript
├── member-app/       # Frontend para miembros
├── desktop/          # Configuración Tauri
├── docs/             # Documentación
└── scripts/          # Scripts de desarrollo
```

## Instalación y Desarrollo

### Requisitos
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### Configuración

1. **Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Frontend**:
```bash
cd frontend
npm install
npm run dev
```

3. **Desktop**:
```bash
cd desktop
npm install
npm run tauri dev
```

## Funcionalidades Avanzadas

- ✅ Mensajería WhatsApp automática
- ✅ Personalización completa de marca
- ✅ Arquitectura modular independiente
- ✅ Sistema de rutinas con IA
- ✅ Integración Instagram
- ✅ Dashboard con KPIs avanzados
- ✅ Frontend dual (admin/miembro)
- ✅ Tipos de cuota flexibles
- ✅ Autenticación dual (Dueño/Profesor)
- ✅ Sistema sin lazy loading para mejor rendimiento
- ✅ Interfaz administrativa especializada

## Licencia

Propietario - Todos los derechos reservados