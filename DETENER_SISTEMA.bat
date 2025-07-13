@echo off
chcp 65001 >nul

echo ========================================================
echo   SISTEMA DE GIMNASIO - DETENCION
echo ========================================================
echo.

echo Deteniendo todos los servicios...
docker-compose -f docker-compose-simple.yml down

echo.
echo Limpiando recursos no utilizados...
docker system prune -f

echo.
echo ========================================================
echo SISTEMA DETENIDO
echo ========================================================
echo.
echo Todos los servicios han sido detenidos correctamente.
echo.
echo Para volver a iniciar el sistema:
echo INSTALAR_SISTEMA.bat
echo.
pause 