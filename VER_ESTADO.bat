@echo off
chcp 65001 >nul

echo ========================================================
echo   SISTEMA DE GIMNASIO - ESTADO ACTUAL
echo ========================================================
echo.

echo Estado de los contenedores:
docker-compose -f docker-compose-simple.yml ps

echo.
echo ========================================================
echo LOGS RECIENTES
echo ========================================================
echo.

echo Logs del backend (ultimas 10 lineas):
docker-compose -f docker-compose-simple.yml logs --tail=10 backend

echo.
echo Logs del frontend (ultimas 10 lineas):
docker-compose -f docker-compose-simple.yml logs --tail=10 frontend

echo.
echo ========================================================
echo VERIFICACION DE SERVICIOS
echo ========================================================
echo.

echo Verificando backend...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend funcionando en http://localhost:8000
) else (
    echo ❌ Backend no responde
)

echo Verificando frontend...
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend funcionando en http://localhost:3000
) else (
    echo ❌ Frontend no responde
)

echo Verificando base de datos...
docker-compose -f docker-compose-simple.yml exec -T postgres pg_isready -U gym_user_prod >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Base de datos PostgreSQL funcionando
) else (
    echo ❌ Base de datos no responde
)

echo.
echo ========================================================
echo COMANDOS UTILES
echo ========================================================
echo.
echo Para ver logs en tiempo real:
echo docker-compose -f docker-compose-simple.yml logs -f
echo.
echo Para reiniciar un servicio:
echo docker-compose -f docker-compose-simple.yml restart [servicio]
echo.
echo Para detener el sistema:
echo DETENER_SISTEMA.bat
echo.
pause 