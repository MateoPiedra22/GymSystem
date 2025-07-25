# Guía de Despliegue - GymSystem v6

## 📋 Resumen del Sistema

Este proyecto es un sistema completo de gestión de gimnasio con:
- **Frontend**: React + TypeScript + Vite (para Vercel)
- **Backend**: FastAPI + SQLAlchemy (para Railway)
- **Base de Datos**: PostgreSQL (Railway)

## ✅ Estado del Proyecto

### ✅ Backend (Listo para Producción)
- ✅ FastAPI configurado correctamente
- ✅ Todos los endpoints habilitados
- ✅ Middleware de seguridad activado
- ✅ Configuración de CORS para Vercel
- ✅ Configuración de Railway lista
- ✅ Dockerfile optimizado
- ✅ Variables de entorno configuradas

### ✅ Frontend (Listo para Producción)
- ✅ React + TypeScript + Vite
- ✅ Configuración de Vercel lista
- ✅ Variables de entorno de producción configuradas
- ✅ Build optimizado con chunks
- ✅ Proxy configurado para desarrollo

## 🚀 Paso a Paso para Despliegue

### 1. Preparar el Repositorio

```bash
# 1. Asegúrate de estar en el directorio del proyecto
cd gym-system-v6

# 2. Agregar todos los archivos al repositorio
git add .

# 3. Hacer commit de los cambios
git commit -m "feat: Sistema listo para producción - Backend y Frontend configurados"

# 4. Subir al repositorio
git push origin main
```

### 2. Desplegar Backend en Railway

#### 2.1 Crear Proyecto en Railway
1. Ve a [railway.app](https://railway.app)
2. Inicia sesión con GitHub
3. Haz clic en "New Project"
4. Selecciona "Deploy from GitHub repo"
5. Conecta tu repositorio `gym-system-v6`

#### 2.2 Configurar Variables de Entorno en Railway

En el dashboard de Railway, ve a Variables y agrega:

```env
# Configuración Básica
ENVIRONMENT=production
DEBUG=false
PROJECT_NAME=GymSystem

# Base de Datos (Railway la genera automáticamente)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Seguridad (GENERA UNA CLAVE SECRETA FUERTE)
SECRET_KEY=tu-clave-secreta-super-segura-aqui-cambiar-en-produccion

# CORS (Actualizar con tu dominio de Vercel)
ALLOWED_ORIGINS=https://gym-system-v6-frontend.vercel.app,http://localhost:3000,http://localhost:5173

# Configuración del Gimnasio
GYM_NAME=Tu Gimnasio
GYM_EMAIL=contacto@tugimnasio.com
GYM_PHONE=+54123456789
DEFAULT_COUNTRY_CODE=+54
```

#### 2.3 Agregar Base de Datos PostgreSQL
1. En Railway, haz clic en "+ New"
2. Selecciona "Database" → "PostgreSQL"
3. Railway automáticamente conectará la base de datos

#### 2.4 Configurar Dominio Personalizado (Opcional)
1. Ve a Settings → Domains
2. Genera un dominio de Railway o conecta tu dominio personalizado
3. Anota la URL (ej: `https://gym-system-v6-production.up.railway.app`)

### 3. Desplegar Frontend en Vercel

#### 3.1 Crear Proyecto en Vercel
1. Ve a [vercel.com](https://vercel.com)
2. Inicia sesión con GitHub
3. Haz clic en "New Project"
4. Importa tu repositorio `gym-system-v6`

#### 3.2 Configurar el Proyecto
- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build:prod`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

#### 3.3 Configurar Variables de Entorno en Vercel

En Vercel Settings → Environment Variables:

```env
# API Configuration (Usar la URL de Railway)
VITE_API_URL=https://gym-system-v6-production.up.railway.app
VITE_API_VERSION=v1

# App Configuration
VITE_APP_NAME=GymSystem
VITE_APP_VERSION=1.0.0

# Production Configuration
VITE_DEV_MODE=false
VITE_DEBUG=false

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_NOTIFICATIONS=true

# UI Configuration
VITE_THEME=light
VITE_PRIMARY_COLOR=#1e40af
VITE_SECONDARY_COLOR=#059669

# Security
VITE_SECURE_MODE=true

# Environment
NODE_ENV=production
```

#### 3.4 Configurar Dominio Personalizado (Opcional)
1. Ve a Settings → Domains
2. Agrega tu dominio personalizado
3. Anota la URL (ej: `https://gym-system-v6-frontend.vercel.app`)

### 4. Actualizar Configuraciones Cruzadas

#### 4.1 Actualizar CORS en Railway
Ve a Railway → Variables de Entorno y actualiza:
```env
ALLOWED_ORIGINS=https://tu-dominio-vercel.vercel.app,http://localhost:3000,http://localhost:5173
```

#### 4.2 Actualizar API URL en Vercel
Ve a Vercel → Settings → Environment Variables y actualiza:
```env
VITE_API_URL=https://tu-dominio-railway.up.railway.app
```

### 5. Verificar el Despliegue

#### 5.1 Verificar Backend
1. Ve a tu URL de Railway
2. Verifica que `/health` responda correctamente
3. Verifica que `/docs` muestre la documentación (solo en desarrollo)

#### 5.2 Verificar Frontend
1. Ve a tu URL de Vercel
2. Verifica que la aplicación cargue correctamente
3. Verifica que puedas hacer login/registro

#### 5.3 Verificar Conexión
1. Desde el frontend, intenta hacer una petición a la API
2. Verifica que no haya errores de CORS
3. Verifica que los datos se muestren correctamente

## 🔧 Comandos Útiles

### Desarrollo Local
```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
pnpm install
pnpm run dev
```

### Producción Local (Simular)
```bash
# Backend
cd backend
python start.py

# Frontend
cd frontend
pnpm run build:prod
pnpm run preview
```

## 🛠️ Solución de Problemas

### Error de CORS
- Verifica que `ALLOWED_ORIGINS` en Railway incluya tu dominio de Vercel
- Asegúrate de que no haya espacios extra en las URLs

### Error 500 en Backend
- Verifica los logs en Railway
- Asegúrate de que todas las variables de entorno estén configuradas
- Verifica que la base de datos esté conectada

### Error de Build en Frontend
- Verifica que `VITE_API_URL` esté configurado
- Asegúrate de que el comando de build sea `npm run build:prod`
- Verifica que el directorio de salida sea `dist`

### Error de Conexión a la Base de Datos
- Verifica que `DATABASE_URL` esté configurado en Railway
- Asegúrate de que el servicio PostgreSQL esté ejecutándose
- Verifica que las migraciones se hayan ejecutado

## 📝 Notas Importantes

1. **Seguridad**: Cambia `SECRET_KEY` por una clave fuerte y única
2. **Dominios**: Actualiza las URLs cuando tengas dominios personalizados
3. **Monitoreo**: Configura alertas en Railway y Vercel
4. **Backups**: Configura backups automáticos de la base de datos
5. **SSL**: Tanto Railway como Vercel proporcionan SSL automáticamente

## 🎉 ¡Listo!

Tu sistema GymSystem v6 está ahora desplegado en producción:
- ✅ Backend en Railway con PostgreSQL
- ✅ Frontend en Vercel
- ✅ Configuración de CORS correcta
- ✅ Variables de entorno configuradas
- ✅ SSL habilitado automáticamente

¡Tu gimnasio ya puede usar el sistema completo!