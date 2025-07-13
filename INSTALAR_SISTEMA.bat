@echo off
chcp 65001 >nul
echo.
echo ========================================
echo  SISTEMA DE GESTIÓN DE GIMNASIO v6.0
echo  INSTALADOR AUTOMÁTICO - DOCKER
echo ========================================
echo.

:: Verificar si Docker está instalado
echo [1/8] Verificando Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Docker no está instalado o no está en el PATH
    echo Por favor, instala Docker Desktop desde: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✅ Docker encontrado: 
docker --version

:: Verificar si Docker Compose está disponible
echo.
echo [2/8] Verificando Docker Compose...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Docker Compose no está disponible
    echo Por favor, asegúrate de que Docker Desktop esté completamente instalado
    pause
    exit /b 1
)
echo ✅ Docker Compose encontrado:
docker-compose --version

:: Verificar si Docker está ejecutándose
echo.
echo [3/8] Verificando que Docker esté ejecutándose...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Docker no está ejecutándose
    echo Por favor, inicia Docker Desktop y espera a que esté listo
    pause
    exit /b 1
)
echo ✅ Docker está ejecutándose correctamente

:: Verificar archivos de configuración
echo.
echo [4/8] Verificando archivos de configuración...
if not exist ".env" (
    echo ❌ ERROR: Archivo .env no encontrado
    echo Por favor, asegúrate de tener el archivo .env en el directorio raíz
    pause
    exit /b 1
)
if not exist "docker-compose.yml" (
    echo ❌ ERROR: Archivo docker-compose.yml no encontrado
    pause
    exit /b 1
)
if not exist "web\Dockerfile" (
    echo ❌ ERROR: Dockerfile del frontend no encontrado
    pause
    exit /b 1
)
if not exist "backend\Dockerfile" (
    echo ❌ ERROR: Dockerfile del backend no encontrado
    pause
    exit /b 1
)
echo ✅ Todos los archivos de configuración encontrados

:: Detener contenedores existentes
echo.
echo [5/8] Deteniendo contenedores existentes...
docker-compose down --remove-orphans >nul 2>&1
echo ✅ Contenedores detenidos

:: Limpiar imágenes y volúmenes (opcional)
echo.
set /p limpiar="¿Deseas limpiar imágenes y volúmenes existentes? (s/N): "
if /i "%limpiar%"=="s" (
    echo Limpiando imágenes y volúmenes...
    docker system prune -f >nul 2>&1
    docker volume prune -f >nul 2>&1
    echo ✅ Limpieza completada
) else (
    echo Saltando limpieza...
)

:: Construir y levantar servicios
echo.
echo [6/8] Construyendo y levantando servicios...
echo ⏳ Esto puede tomar varios minutos en la primera ejecución...
echo.

:: Construir imágenes
echo Construyendo imagen del backend...
docker-compose build backend
if %errorlevel% neq 0 (
    echo ❌ ERROR: Fallo al construir el backend
    pause
    exit /b 1
)

echo Construyendo imagen del frontend...
docker-compose build frontend
if %errorlevel% neq 0 (
    echo ❌ ERROR: Fallo al construir el frontend
    pause
    exit /b 1
)

:: Levantar servicios
echo Levantando todos los servicios...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ ERROR: Fallo al levantar los servicios
    pause
    exit /b 1
)

:: Esperar a que los servicios estén listos
echo.
echo [7/8] Esperando a que los servicios estén listos...
timeout /t 30 /nobreak >nul

:: Verificar estado de los servicios
echo.
echo [8/8] Verificando estado de los servicios...

:: Verificar PostgreSQL
echo Verificando PostgreSQL...
docker-compose exec -T postgres pg_isready -U gym_user >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL: Funcionando
) else (
    echo ⚠️  PostgreSQL: En proceso de inicio
)

:: Verificar Redis
echo Verificando Redis...
docker-compose exec -T redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Redis: Funcionando
) else (
    echo ⚠️  Redis: En proceso de inicio
)

:: Verificar Backend
echo Verificando Backend API...
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend API: Funcionando
) else (
    echo ⚠️  Backend API: En proceso de inicio
)

:: Verificar Frontend
echo Verificando Frontend Web...
curl -f http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend Web: Funcionando
) else (
    echo ⚠️  Frontend Web: En proceso de inicio
)

:: Verificar Nginx
echo Verificando Nginx...
curl -f http://localhost/nginx-health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Nginx: Funcionando
) else (
    echo ⚠️  Nginx: En proceso de inicio
)

:: Mostrar información final
echo.
echo ========================================
echo  ✅ INSTALACIÓN COMPLETADA
echo ========================================
echo.
echo 🌐 ACCESO AL SISTEMA:
echo    Frontend Web: http://localhost:3000
echo    Backend API:  http://localhost:8000
echo    Nginx Proxy:  http://localhost
echo.
echo 📊 MONITOREO:
echo    Health Check: http://localhost/health
echo    Nginx Status: http://localhost/nginx-health
echo.
echo 🛠️  COMANDOS ÚTILES:
echo    Ver logs: docker-compose logs -f
echo    Detener:   docker-compose down
echo    Reiniciar: docker-compose restart
echo    Estado:    docker-compose ps
echo.
echo 📝 NOTAS:
echo    - El sistema puede tardar unos minutos en estar completamente operativo
echo    - Los datos se almacenan en volúmenes Docker persistentes
echo    - Para desarrollo, usa: docker-compose -f docker-compose.dev.yml up
echo.
echo Presiona cualquier tecla para abrir el sistema en el navegador...
pause >nul

:: Abrir navegador
start http://localhost:3000

echo.
echo ¡Sistema iniciado correctamente!
pause 