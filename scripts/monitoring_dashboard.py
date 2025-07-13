#!/usr/bin/env python3
"""
Dashboard de Monitoreo en Tiempo Real - Sistema de Gimnasio v6
Interfaz web para monitoreo en tiempo real del sistema
"""

import os
import sys
import time
import json
import asyncio
import aiohttp
import psutil
import docker
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealTimeMonitor:
    """Monitor en tiempo real del sistema"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = {}
        self.alerts = []
        self.services_status = {}
        self.last_update = None
        self.docker_client = None
        
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"No se pudo conectar a Docker: {e}")
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory
            memory = psutil.virtual_memory()
            
            # Disk
            disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            
            # Load average
            load_avg = psutil.getloadavg()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency": cpu_freq.current if cpu_freq else 0
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "load_average": {
                    "1min": load_avg[0],
                    "5min": load_avg[1],
                    "15min": load_avg[2]
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo métricas del sistema: {e}")
            return {}
    
    async def get_docker_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de Docker"""
        if not self.docker_client:
            return {}
        
        try:
            containers = self.docker_client.containers.list()
            metrics = {}
            
            for container in containers:
                try:
                    stats = container.stats(stream=False)
                    
                    # Calcular uso de CPU
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                               stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                  stats['precpu_stats']['system_cpu_usage']
                    
                    cpu_percent = 0
                    if system_delta > 0:
                        cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                    
                    # Calcular uso de memoria
                    memory_usage = stats['memory_stats']['usage']
                    memory_limit = stats['memory_stats']['limit']
                    memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
                    
                    metrics[container.name] = {
                        "status": container.status,
                        "cpu_percent": cpu_percent,
                        "memory_usage": memory_usage,
                        "memory_limit": memory_limit,
                        "memory_percent": memory_percent,
                        "network_rx": stats['networks']['eth0']['rx_bytes'] if 'networks' in stats else 0,
                        "network_tx": stats['networks']['eth0']['tx_bytes'] if 'networks' in stats else 0
                    }
                except Exception as e:
                    logger.warning(f"Error obteniendo métricas del contenedor {container.name}: {e}")
                    metrics[container.name] = {"status": "error", "error": str(e)}
            
            return metrics
        except Exception as e:
            logger.error(f"Error obteniendo métricas de Docker: {e}")
            return {}
    
    async def check_service_health(self) -> Dict[str, Any]:
        """Verificar salud de los servicios"""
        services = {
            "backend": "http://localhost:8000/health",
            "frontend": "http://localhost:3000/health",
            "database": "http://localhost:5432",
            "redis": "http://localhost:6379",
            "nginx": "http://localhost:80"
        }
        
        health_status = {}
        
        async with aiohttp.ClientSession() as session:
            for service, url in services.items():
                try:
                    async with session.get(url, timeout=5) as response:
                        health_status[service] = {
                            "status": "healthy" if response.status == 200 else "unhealthy",
                            "response_time": response.headers.get('X-Response-Time', 'N/A'),
                            "status_code": response.status
                        }
                except Exception as e:
                    health_status[service] = {
                        "status": "down",
                        "error": str(e),
                        "status_code": None
                    }
        
        return health_status
    
    async def get_application_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de la aplicación"""
        try:
            async with aiohttp.ClientSession() as session:
                # Métricas del backend
                backend_metrics = {}
                try:
                    async with session.get("http://localhost:8000/metrics", timeout=5) as response:
                        if response.status == 200:
                            text = await response.text()
                            # Parsear métricas básicas
                            for line in text.split('\n'):
                                if line.startswith('gym_'):
                                    parts = line.split()
                                    if len(parts) >= 2:
                                        metric_name = parts[0]
                                        metric_value = float(parts[1])
                                        backend_metrics[metric_name] = metric_value
                except Exception as e:
                    logger.warning(f"Error obteniendo métricas del backend: {e}")
                
                # Métricas de Prometheus (si está disponible)
                prometheus_metrics = {}
                try:
                    async with session.get("http://localhost:9090/api/v1/query?query=up", timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data['status'] == 'success':
                                for result in data['data']['result']:
                                    service = result['metric']['job']
                                    status = result['value'][1]
                                    prometheus_metrics[service] = int(status)
                except Exception as e:
                    logger.warning(f"Error obteniendo métricas de Prometheus: {e}")
                
                return {
                    "backend": backend_metrics,
                    "prometheus": prometheus_metrics
                }
        except Exception as e:
            logger.error(f"Error obteniendo métricas de la aplicación: {e}")
            return {}
    
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """Verificar alertas activas"""
        alerts = []
        
        # Alertas del sistema
        system_metrics = await self.get_system_metrics()
        if system_metrics:
            # CPU alta
            if system_metrics.get('cpu', {}).get('percent', 0) > 80:
                alerts.append({
                    "severity": "warning",
                    "title": "CPU Usage High",
                    "message": f"CPU usage is {system_metrics['cpu']['percent']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Memoria alta
            if system_metrics.get('memory', {}).get('percent', 0) > 85:
                alerts.append({
                    "severity": "warning",
                    "title": "Memory Usage High",
                    "message": f"Memory usage is {system_metrics['memory']['percent']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Disco lleno
            if system_metrics.get('disk', {}).get('percent', 0) > 90:
                alerts.append({
                    "severity": "critical",
                    "title": "Disk Space Critical",
                    "message": f"Disk usage is {system_metrics['disk']['percent']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Alertas de servicios
        health_status = await self.check_service_health()
        for service, status in health_status.items():
            if status.get('status') == 'down':
                alerts.append({
                    "severity": "critical",
                    "title": f"{service.title()} Service Down",
                    "message": f"Service {service} is not responding",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    async def update_metrics(self):
        """Actualizar todas las métricas"""
        logger.info("Actualizando métricas...")
        
        # Obtener métricas en paralelo
        tasks = [
            self.get_system_metrics(),
            self.get_docker_metrics(),
            self.check_service_health(),
            self.get_application_metrics(),
            self.check_alerts()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.metrics = {
            "system": results[0] if not isinstance(results[0], Exception) else {},
            "docker": results[1] if not isinstance(results[1], Exception) else {},
            "health": results[2] if not isinstance(results[2], Exception) else {},
            "application": results[3] if not isinstance(results[3], Exception) else {}
        }
        
        self.alerts = results[4] if not isinstance(results[4], Exception) else []
        self.last_update = datetime.now()
        
        logger.info("Métricas actualizadas")

class WebDashboard:
    """Dashboard web para monitoreo"""
    
    def __init__(self, monitor: RealTimeMonitor):
        self.monitor = monitor
        self.html_template = self.load_template()
    
    def load_template(self) -> str:
        """Cargar plantilla HTML"""
        return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Gimnasio - Dashboard de Monitoreo</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status-bar {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        .metric-card {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            margin: 10px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .chart-container {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
            backdrop-filter: blur(10px);
        }
        .alert {
            background: rgba(255, 99, 71, 0.8);
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            border-left: 5px solid #ff6347;
        }
        .alert.warning {
            background: rgba(255, 165, 0, 0.8);
            border-left-color: #ffa500;
        }
        .alert.info {
            background: rgba(0, 191, 255, 0.8);
            border-left-color: #00bfff;
        }
        .service-status {
            display: flex;
            align-items: center;
            margin: 5px 0;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .status-healthy { background: #00ff00; }
        .status-unhealthy { background: #ffa500; }
        .status-down { background: #ff0000; }
        .refresh-button {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .refresh-button:hover {
            background: rgba(255,255,255,0.3);
        }
        .last-update {
            font-size: 0.9em;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏋️ Sistema de Gimnasio - Dashboard de Monitoreo</h1>
            <p>Monitoreo en tiempo real del sistema de gestión de gimnasio</p>
        </div>
        
        <div class="status-bar">
            <div>
                <strong>Última actualización:</strong> <span id="last-update">Cargando...</span>
            </div>
            <button class="refresh-button" onclick="refreshData()">🔄 Actualizar</button>
        </div>
        
        <div class="metric-grid">
            <div class="metric-card">
                <h3>💻 CPU</h3>
                <div id="cpu-usage">Cargando...</div>
            </div>
            <div class="metric-card">
                <h3>🧠 Memoria</h3>
                <div id="memory-usage">Cargando...</div>
            </div>
            <div class="metric-card">
                <h3>💾 Disco</h3>
                <div id="disk-usage">Cargando...</div>
            </div>
            <div class="metric-card">
                <h3>🌐 Red</h3>
                <div id="network-usage">Cargando...</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>📊 Métricas del Sistema</h3>
            <canvas id="systemChart" width="400" height="200"></canvas>
        </div>
        
        <div class="metric-grid">
            <div class="metric-card">
                <h3>🐳 Contenedores Docker</h3>
                <div id="docker-status">Cargando...</div>
            </div>
            <div class="metric-card">
                <h3>🔧 Estado de Servicios</h3>
                <div id="service-status">Cargando...</div>
            </div>
        </div>
        
        <div class="metric-card">
            <h3>🚨 Alertas Activas</h3>
            <div id="alerts">Cargando...</div>
        </div>
        
        <div class="chart-container">
            <h3>📈 Métricas de la Aplicación</h3>
            <canvas id="appChart" width="400" height="200"></canvas>
        </div>
    </div>
    
    <script>
        let systemChart, appChart;
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function formatPercent(value) {
            return value.toFixed(1) + '%';
        }
        
        function updateMetrics(data) {
            // Actualizar métricas del sistema
            if (data.system) {
                document.getElementById('cpu-usage').innerHTML = 
                    `<strong>${formatPercent(data.system.cpu.percent)}</strong> (${data.system.cpu.count} cores)`;
                
                document.getElementById('memory-usage').innerHTML = 
                    `<strong>${formatPercent(data.system.memory.percent)}</strong> (${formatBytes(data.system.memory.used)} / ${formatBytes(data.system.memory.total)})`;
                
                document.getElementById('disk-usage').innerHTML = 
                    `<strong>${formatPercent(data.system.disk.percent)}</strong> (${formatBytes(data.system.disk.used)} / ${formatBytes(data.system.disk.total)})`;
                
                document.getElementById('network-usage').innerHTML = 
                    `<strong>↓ ${formatBytes(data.system.network.bytes_recv)}</strong> / <strong>↑ ${formatBytes(data.system.network.bytes_sent)}</strong>`;
            }
            
            // Actualizar estado de Docker
            if (data.docker) {
                let dockerHtml = '';
                for (const [container, info] of Object.entries(data.docker)) {
                    const statusClass = info.status === 'running' ? 'status-healthy' : 'status-down';
                    dockerHtml += `
                        <div class="service-status">
                            <div class="status-indicator ${statusClass}"></div>
                            <strong>${container}</strong>: ${info.status} (CPU: ${info.cpu_percent?.toFixed(1) || 'N/A'}%, Mem: ${info.memory_percent?.toFixed(1) || 'N/A'}%)
                        </div>
                    `;
                }
                document.getElementById('docker-status').innerHTML = dockerHtml;
            }
            
            // Actualizar estado de servicios
            if (data.health) {
                let serviceHtml = '';
                for (const [service, info] of Object.entries(data.health)) {
                    const statusClass = info.status === 'healthy' ? 'status-healthy' : 
                                      info.status === 'unhealthy' ? 'status-unhealthy' : 'status-down';
                    serviceHtml += `
                        <div class="service-status">
                            <div class="status-indicator ${statusClass}"></div>
                            <strong>${service}</strong>: ${info.status} (${info.status_code || 'N/A'})
                        </div>
                    `;
                }
                document.getElementById('service-status').innerHTML = serviceHtml;
            }
            
            // Actualizar alertas
            if (data.alerts) {
                let alertsHtml = '';
                if (data.alerts.length === 0) {
                    alertsHtml = '<p>✅ No hay alertas activas</p>';
                } else {
                    data.alerts.forEach(alert => {
                        alertsHtml += `
                            <div class="alert ${alert.severity}">
                                <strong>${alert.title}</strong><br>
                                ${alert.message}<br>
                                <small>${new Date(alert.timestamp).toLocaleString()}</small>
                            </div>
                        `;
                    });
                }
                document.getElementById('alerts').innerHTML = alertsHtml;
            }
            
            // Actualizar última actualización
            document.getElementById('last-update').textContent = new Date().toLocaleString();
        }
        
        function updateCharts(data) {
            // Gráfico del sistema
            if (data.system && systemChart) {
                systemChart.data.labels.push(new Date().toLocaleTimeString());
                systemChart.data.datasets[0].data.push(data.system.cpu.percent);
                systemChart.data.datasets[1].data.push(data.system.memory.percent);
                systemChart.data.datasets[2].data.push(data.system.disk.percent);
                
                // Mantener solo los últimos 20 puntos
                if (systemChart.data.labels.length > 20) {
                    systemChart.data.labels.shift();
                    systemChart.data.datasets.forEach(dataset => dataset.data.shift());
                }
                
                systemChart.update('none');
            }
            
            // Gráfico de la aplicación
            if (data.application && appChart) {
                const backendMetrics = data.application.backend || {};
                const userCount = backendMetrics.gym_active_users_total || 0;
                const classCount = backendMetrics.gym_total_classes || 0;
                
                appChart.data.labels.push(new Date().toLocaleTimeString());
                appChart.data.datasets[0].data.push(userCount);
                appChart.data.datasets[1].data.push(classCount);
                
                if (appChart.data.labels.length > 20) {
                    appChart.data.labels.shift();
                    appChart.data.datasets.forEach(dataset => dataset.data.shift());
                }
                
                appChart.update('none');
            }
        }
        
        function initCharts() {
            const systemCtx = document.getElementById('systemChart').getContext('2d');
            systemChart = new Chart(systemCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU %',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    }, {
                        label: 'Memoria %',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        tension: 0.1
                    }, {
                        label: 'Disco %',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
            
            const appCtx = document.getElementById('appChart').getContext('2d');
            appChart = new Chart(appCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Usuarios Activos',
                        data: [],
                        borderColor: 'rgb(255, 159, 64)',
                        backgroundColor: 'rgba(255, 159, 64, 0.2)',
                        tension: 0.1
                    }, {
                        label: 'Clases Activas',
                        data: [],
                        borderColor: 'rgb(153, 102, 255)',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        async function refreshData() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                updateMetrics(data);
                updateCharts(data);
            } catch (error) {
                console.error('Error actualizando datos:', error);
            }
        }
        
        // Inicializar
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
            refreshData();
            // Actualizar cada 30 segundos
            setInterval(refreshData, 30000);
        });
    </script>
</body>
</html>
        """
    
    def get_html(self) -> str:
        """Obtener HTML del dashboard"""
        return self.html_template

async def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dashboard de Monitoreo en Tiempo Real")
    parser.add_argument("--port", type=int, default=8080, help="Puerto del servidor web")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host del servidor web")
    parser.add_argument("--config", type=str, default="monitoring_config.json", help="Archivo de configuración")
    
    args = parser.parse_args()
    
    # Cargar configuración
    config = {}
    if os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # Crear monitor
    monitor = RealTimeMonitor(config)
    dashboard = WebDashboard(monitor)
    
    # Inicializar métricas
    await monitor.update_metrics()
    
    # Crear servidor web simple
    from aiohttp import web
    
    async def handle_dashboard(request):
        return web.Response(text=dashboard.get_html(), content_type='text/html')
    
    async def handle_metrics(request):
        await monitor.update_metrics()
        return web.json_response({
            "system": monitor.metrics.get("system", {}),
            "docker": monitor.metrics.get("docker", {}),
            "health": monitor.metrics.get("health", {}),
            "application": monitor.metrics.get("application", {}),
            "alerts": monitor.alerts,
            "last_update": monitor.last_update.isoformat() if monitor.last_update else None
        })
    
    async def handle_health(request):
        return web.json_response({"status": "healthy"})
    
    # Configurar rutas
    app = web.Application()
    app.router.add_get('/', handle_dashboard)
    app.router.add_get('/api/metrics', handle_metrics)
    app.router.add_get('/health', handle_health)
    
    # Iniciar servidor
    logger.info(f"Iniciando dashboard en http://{args.host}:{args.port}")
    web.run_app(app, host=args.host, port=args.port)

if __name__ == "__main__":
    asyncio.run(main()) 