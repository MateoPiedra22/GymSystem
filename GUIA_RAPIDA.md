# 🏋️ Sistema de Gestión de Gimnasio - Guía Rápida

## 🚀 Instalación y Uso

### Requisitos Previos
- Docker Desktop instalado y ejecutándose
- Windows 10/11

### Instalación Automática
1. **Ejecutar el script de instalación:**
   ```
   INSTALAR_SISTEMA.bat
   ```

2. **Esperar a que termine la instalación** (puede tomar 2-3 minutos)

3. **Acceder al sistema:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Documentación API: http://localhost:8000/docs

### Credenciales por Defecto
- **Usuario:** admin@migimnasio.com
- **Contraseña:** admin123

## 📋 Comandos Útiles

### Ver Estado del Sistema
```
VER_ESTADO.bat
```

### Detener el Sistema
```
DETENER_SISTEMA.bat
```

### Ver Logs en Tiempo Real
```
docker-compose -f docker-compose-simple.yml logs -f
```

### Reiniciar un Servicio Específico
```
docker-compose -f docker-compose-simple.yml restart backend
docker-compose -f docker-compose-simple.yml restart frontend
```

## 🔧 Solución de Problemas

### El Backend No Inicia
1. Verificar que Docker esté ejecutándose
2. Ejecutar `VER_ESTADO.bat` para ver logs
3. Si persiste, reiniciar el servicio:
   ```
   docker-compose -f docker-compose-simple.yml restart backend
   ```

### El Frontend No Carga
1. Verificar que el backend esté funcionando
2. Reiniciar el frontend:
   ```
   docker-compose -f docker-compose-simple.yml restart frontend
   ```

### Problemas de Base de Datos
1. Verificar que PostgreSQL esté ejecutándose:
   ```
   docker-compose -f docker-compose-simple.yml ps
   ```
2. Si no está, reiniciar:
   ```
   docker-compose -f docker-compose-simple.yml restart postgres
   ```

## 📊 Servicios Incluidos

- **Frontend:** Next.js con React (puerto 3000)
- **Backend:** FastAPI con Python (puerto 8000)
- **Base de Datos:** PostgreSQL (puerto 5432)
- **Cache:** Redis (puerto 6379)
- **Proxy:** Nginx (puertos 80/443)

## 🔒 Seguridad

- Todas las contraseñas están configuradas por defecto
- En producción, cambiar las claves secretas
- El sistema incluye rate limiting y validación de entrada

## 📞 Soporte

Si tienes problemas:
1. Ejecutar `VER_ESTADO.bat` para diagnóstico
2. Revisar los logs con el comando de logs
3. Reiniciar el servicio problemático
4. Si persiste, detener y reinstalar con `INSTALAR_SISTEMA.bat` 