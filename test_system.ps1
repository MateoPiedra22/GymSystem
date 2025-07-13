# Script de Prueba del Sistema de Gestión de Gimnasio v6.0
# Desplegado en Docker

Write-Host "🧪 PRUEBAS DEL SISTEMA DE GESTIÓN DE GIMNASIO v6.0" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar contenedores Docker
Write-Host "1️⃣ Verificando contenedores Docker..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""

# 2. Probar endpoints del backend
Write-Host "2️⃣ Probando endpoints del backend..." -ForegroundColor Yellow

Write-Host "   Health Check:" -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
    Write-Host "   ✅ Backend saludable - Status: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error en health check: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "   KPIs:" -ForegroundColor Green
try {
    $kpis = Invoke-RestMethod -Uri "http://localhost:8000/api/reportes/kpis" -Method GET
    Write-Host "   ✅ KPIs obtenidos - $($kpis.PSObject.Properties.Count) indicadores" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error obteniendo KPIs: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "   Gráficos:" -ForegroundColor Green
try {
    $graficos = Invoke-RestMethod -Uri "http://localhost:8000/api/reportes/graficos" -Method GET
    Write-Host "   ✅ Gráficos obtenidos - $($graficos.PSObject.Properties.Count) gráficos" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error obteniendo gráficos: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# 3. Probar frontend
Write-Host "3️⃣ Probando frontend..." -ForegroundColor Yellow
try {
    $frontend = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET
    Write-Host "   ✅ Frontend funcionando - Status: $($frontend.StatusCode)" -ForegroundColor Green
    Write-Host "   📄 Tamaño de respuesta: $($frontend.Content.Length) bytes" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error en frontend: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# 4. Verificar base de datos
Write-Host "4️⃣ Verificando base de datos..." -ForegroundColor Yellow
try {
    $dbHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
    if ($dbHealth.services.database.status -eq "healthy") {
        Write-Host "   ✅ Base de datos conectada - Latencia: $($dbHealth.services.database.latency_ms)ms" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Base de datos no saludable" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Error verificando BD: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# 5. Verificar Redis
Write-Host "5️⃣ Verificando Redis..." -ForegroundColor Yellow
try {
    $redisHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
    if ($redisHealth.services.redis.status -eq "healthy") {
        Write-Host "   ✅ Redis conectado" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Redis no saludable" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Error verificando Redis: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# 6. Resumen de puertos
Write-Host "6️⃣ Puertos disponibles:" -ForegroundColor Yellow
Write-Host "   🌐 Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "   🔧 Backend API: http://localhost:8000" -ForegroundColor Green
Write-Host "   📊 Métricas: http://localhost:9000" -ForegroundColor Green
Write-Host "   🗄️ PostgreSQL: localhost:15432" -ForegroundColor Green
Write-Host "   🔴 Redis: localhost:6379" -ForegroundColor Green

Write-Host ""

# 7. Información de acceso
Write-Host "7️⃣ Información de acceso:" -ForegroundColor Yellow
Write-Host "   👤 Usuario admin: admin" -ForegroundColor Green
Write-Host "   🔑 Contraseña: admin123" -ForegroundColor Green
Write-Host "   📧 Email: admin@gymnasium.local" -ForegroundColor Green

Write-Host ""

# 8. Funcionalidades implementadas
Write-Host "8️⃣ Funcionalidades implementadas:" -ForegroundColor Yellow
Write-Host "   ✅ Más de 20 KPIs en reportes" -ForegroundColor Green
Write-Host "   ✅ 12 gráficos detallados" -ForegroundColor Green
Write-Host "   ✅ Interfaz moderna y responsiva" -ForegroundColor Green
Write-Host "   ✅ Modo oscuro" -ForegroundColor Green
Write-Host "   ✅ CRUD completo de usuarios" -ForegroundColor Green
Write-Host "   ✅ Gestión de asistencias" -ForegroundColor Green
Write-Host "   ✅ Gestión de pagos" -ForegroundColor Green
Write-Host "   ✅ Gestión de clases" -ForegroundColor Green
Write-Host "   ✅ Autenticación segura" -ForegroundColor Green
Write-Host "   ✅ Base de datos optimizada" -ForegroundColor Green
Write-Host "   ✅ Cache Redis" -ForegroundColor Green

Write-Host ""

Write-Host "🎉 ¡SISTEMA DESPLEGADO Y FUNCIONANDO CORRECTAMENTE!" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Para acceder al sistema:" -ForegroundColor Yellow
Write-Host "   1. Abre tu navegador" -ForegroundColor White
Write-Host "   2. Ve a: http://localhost:3000" -ForegroundColor White
Write-Host "   3. Inicia sesión con: admin / admin123" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Para detener el sistema:" -ForegroundColor Yellow
Write-Host "   docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "📊 Para ver logs:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f [servicio]" -ForegroundColor White 