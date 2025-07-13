# 🏋️ Guía Completa: Sistema de Gimnasio en Producción

## 📋 Índice
1. [Requisitos Previos](#requisitos-previos)
2. [Instalación Paso a Paso](#instalación-paso-a-paso)
3. [Configuración Inicial](#configuración-inicial)
4. [Uso Diario](#uso-diario)
5. [Mantenimiento](#mantenimiento)
6. [Solución de Problemas](#solución-de-problemas)
7. [Comandos Útiles](#comandos-útiles)

---

## 🔧 Requisitos Previos

### Lo que necesitas:
- **Windows 10 o 11** (actualizado)
- **Mínimo 8GB de RAM** (recomendado 16GB)
- **Mínimo 50GB de espacio libre** en disco
- **Conexión a internet** para la instalación inicial

### Lo que NO necesitas:
- ❌ Conocimientos técnicos avanzados
- ❌ Servidor web
- ❌ Dominio de internet
- ❌ Configuraciones complejas

---

## 🚀 Instalación Paso a Paso

### Paso 1: Instalar Docker Desktop

1. **Abrir PowerShell como Administrador**
   - Presiona `Windows + X`
   - Selecciona "Windows PowerShell (Administrador)"

2. **Ejecutar el script de instalación**
   ```powershell
   cd "C:\Users\mateo\OneDrive\Escritorio\gym-system-v6"
   .\scripts\install_docker.ps1
   ```

3. **Reiniciar la computadora** cuando te lo indique

4. **Abrir Docker Desktop**
   - Busca "Docker Desktop" en el menú inicio
   - Ábrelo y acepta los términos

### Paso 2: Configurar el Sistema

1. **Ejecutar el script de configuración**
   ```powershell
   .\scripts\setup_production.ps1 -GymName "Mi Gimnasio" -AdminEmail "admin@migimnasio.com" -AdminPassword "mi_contraseña_segura"
   ```

2. **Esperar a que termine** (puede tomar 10-15 minutos)

3. **Verificar que todo funcione**
   - Abre tu navegador
   - Ve a: `http://localhost:3000`
   - Deberías ver la pantalla de login

---

## ⚙️ Configuración Inicial

### Primer Acceso

1. **Iniciar sesión**
   - Email: `admin@migimnasio.com` (o el que configuraste)
   - Contraseña: `mi_contraseña_segura` (o la que configuraste)

2. **Cambiar contraseña**
   - Ve a Configuración → Perfil
   - Cambia la contraseña por una más segura

3. **Configurar el gimnasio**
   - Ve a Configuración → General
   - Completa la información de tu gimnasio
   - Sube el logo si lo tienes

### Configuración de Red Local

Para acceder desde otras computadoras en tu red:

1. **Obtener la IP de tu computadora**
   ```powershell
   ipconfig
   ```
   Busca la línea "IPv4 Address" (ejemplo: 192.168.1.100)

2. **Acceder desde otras computadoras**
   - En cualquier computadora de tu red
   - Abre el navegador
   - Ve a: `http://192.168.1.100:3000`

---

## 📱 Uso Diario

### Iniciar el Sistema

**Opción 1: Automático (Recomendado)**
- El sistema se inicia automáticamente con Windows
- No necesitas hacer nada

**Opción 2: Manual**
```powershell
cd "C:\Users\mateo\OneDrive\Escritorio\gym-system-v6"
docker-compose up -d
```

### Detener el Sistema

```powershell
cd "C:\Users\mateo\OneDrive\Escritorio\gym-system-v6"
docker-compose down
```

### Verificar Estado

```powershell
docker-compose ps
```
Todos los servicios deben mostrar "Up" en estado.

---

## 🔧 Mantenimiento

### Respaldo Diario

**Automático (Recomendado)**
```powershell
# Crear tarea programada para respaldo diario
.\scripts\backup_system.ps1
```

**Manual**
```powershell
# Respaldo completo
.\scripts\backup_system.ps1

# Respaldo con logs
.\scripts\backup_system.ps1 -IncludeLogs
```

### Actualizar el Sistema

```powershell
# Detener servicios
docker-compose down

# Actualizar imágenes
docker-compose pull

# Reiniciar servicios
docker-compose up -d
```

### Limpiar Espacio

```powershell
# Limpiar contenedores no usados
docker system prune -f

# Limpiar imágenes no usadas
docker image prune -f
```

---

## 🚨 Solución de Problemas

### El sistema no inicia

1. **Verificar Docker**
   ```powershell
   docker version
   ```

2. **Verificar puertos**
   - Asegúrate que los puertos 80, 3000, 8000 no estén en uso
   - Cierra otros programas que usen estos puertos

3. **Reiniciar Docker**
   - Cierra Docker Desktop
   - Ábrelo nuevamente
   - Espera 1-2 minutos

4. **Reiniciar servicios**
   ```powershell
   docker-compose restart
   ```

### No puedo acceder desde otras computadoras

1. **Verificar firewall**
   - Abre "Firewall de Windows Defender"
   - Permite Docker Desktop

2. **Verificar IP**
   ```powershell
   ipconfig
   ```

3. **Probar conectividad**
   - Desde otra computadora: `ping 192.168.1.100`

### Error de base de datos

1. **Verificar logs**
   ```powershell
   docker-compose logs postgres
   ```

2. **Reiniciar base de datos**
   ```powershell
   docker-compose restart postgres
   ```

3. **Restaurar respaldo**
   ```powershell
   # Detener servicios
   docker-compose down
   
   # Restaurar base de datos
   docker-compose exec -T postgres psql -U gym_user_prod gym_db_prod < backups/ultimo_respaldo.sql
   
   # Reiniciar servicios
   docker-compose up -d
   ```

---

## 💻 Comandos Útiles

### Ver Logs
```powershell
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Estado de Servicios
```powershell
# Ver estado
docker-compose ps

# Ver uso de recursos
docker stats
```

### Reiniciar Servicios
```powershell
# Todos los servicios
docker-compose restart

# Servicio específico
docker-compose restart backend
docker-compose restart frontend
```

### Acceso a Contenedores
```powershell
# Acceder al backend
docker-compose exec backend bash

# Acceder a la base de datos
docker-compose exec postgres psql -U gym_user_prod gym_db_prod
```

---

## 📞 Soporte

### Información del Sistema
- **Versión**: 6.0
- **Base de datos**: PostgreSQL 15
- **Frontend**: Next.js
- **Backend**: FastAPI (Python)

### URLs Importantes
- **Aplicación**: http://localhost:3000
- **API**: http://localhost:8000
- **Monitoreo**: http://localhost:3001
- **Métricas**: http://localhost:9090

### Archivos Importantes
- **Configuración**: `.env`
- **Docker**: `docker-compose.yml`
- **Respaldos**: `backups/`
- **Logs**: `logs/`

---

## 🔒 Seguridad

### Recomendaciones
1. **Cambia las contraseñas por defecto**
2. **Haz respaldos regulares**
3. **Mantén Windows actualizado**
4. **Usa un antivirus actualizado**
5. **No compartas las credenciales**

### Firewall
- Permite Docker Desktop en el firewall
- Bloquea puertos innecesarios
- Usa una red WiFi segura

---

## 📈 Monitoreo

### Ver Métricas
- **Grafana**: http://localhost:3001
  - Usuario: `admin`
  - Contraseña: `gym_admin_password_2024!`

### Alertas
El sistema monitorea automáticamente:
- Uso de CPU y memoria
- Estado de la base de datos
- Errores del sistema
- Espacio en disco

---

## 🎯 Consejos Finales

1. **Prueba todo antes de usar en producción**
2. **Haz respaldos antes de actualizaciones**
3. **Mantén un registro de cambios**
4. **Capacita a tu personal**
5. **Ten un plan de contingencia**

---

**¡Tu sistema de gimnasio está listo para usar! 🎉**

Si tienes problemas, revisa esta guía primero. La mayoría de problemas se resuelven con los comandos básicos que te proporcioné. 