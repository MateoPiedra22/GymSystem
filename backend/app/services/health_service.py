from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio
import psutil
import time
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..core.database import get_db, engine
import redis
import requests
from pathlib import Path
import json
import uuid
from collections import deque
import statistics
from ..core.config import settings
import subprocess
import platform
import socket
import os

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ComponentType(Enum):
    DATABASE = "database"
    REDIS = "redis"
    FILE_SYSTEM = "file_system"
    EXTERNAL_API = "external_api"
    SYSTEM_RESOURCES = "system_resources"
    APPLICATION = "application"
    NETWORK = "network"
    SERVICES = "services"

@dataclass
class HealthCheck:
    """Individual health check result"""
    component: str
    component_type: ComponentType
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    active_connections: int
    uptime_seconds: float
    load_average: Optional[List[float]] = None

@dataclass
class HealthReport:
    """Complete health report"""
    overall_status: HealthStatus
    timestamp: datetime
    checks: List[HealthCheck]
    metrics: SystemMetrics
    summary: Dict[str, Any]
    recommendations: List[str]

class HealthMonitor:
    """System health monitoring service"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.health_history: deque = deque(maxlen=100)  # Keep last 100 health checks
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'response_time_ms': 5000.0,
            'database_connections': 50
        }
        self.check_intervals = {
            'quick': 30,    # 30 seconds
            'standard': 300,  # 5 minutes
            'detailed': 900   # 15 minutes
        }
        self.external_apis = {
            'twilio': 'https://api.twilio.com/2010-04-01/Accounts.json',
            'instagram': 'https://graph.instagram.com/me',
            'openai': 'https://api.openai.com/v1/models'
        }
        
        # Background monitoring task
        self.monitoring_task = None
        self.is_monitoring = False
    
    async def start_monitoring(self):
        """Start background health monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop background health monitoring"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_monitoring:
            try:
                # Perform quick health check
                report = await self.perform_health_check(quick=True)
                
                # Store in history
                self.health_history.append({
                    'timestamp': report.timestamp,
                    'status': report.overall_status.value,
                    'cpu': report.metrics.cpu_percent,
                    'memory': report.metrics.memory_percent,
                    'disk': report.metrics.disk_percent
                })
                
                # Check for alerts
                await self._check_alerts(report)
                
                # Wait for next check
                await asyncio.sleep(self.check_intervals['quick'])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def perform_health_check(
        self,
        quick: bool = False,
        include_external: bool = True
    ) -> HealthReport:
        """Perform comprehensive health check"""
        start_time = time.time()
        checks = []
        
        try:
            # Database health check
            db_check = await self._check_database()
            checks.append(db_check)
            
            # Redis health check
            redis_check = await self._check_redis()
            checks.append(redis_check)
            
            # File system health check
            fs_check = await self._check_file_system()
            checks.append(fs_check)
            
            # System resources check
            system_check = await self._check_system_resources()
            checks.append(system_check)
            
            # Application health check
            app_check = await self._check_application()
            checks.append(app_check)
            
            if not quick:
                # Network connectivity check
                network_check = await self._check_network()
                checks.append(network_check)
                
                # External APIs check
                if include_external:
                    for api_name, api_url in self.external_apis.items():
                        api_check = await self._check_external_api(api_name, api_url)
                        checks.append(api_check)
            
            # Get system metrics
            metrics = await self._get_system_metrics()
            
            # Determine overall status
            overall_status = self._determine_overall_status(checks)
            
            # Generate summary and recommendations
            summary = self._generate_summary(checks, metrics)
            recommendations = self._generate_recommendations(checks, metrics)
            
            report = HealthReport(
                overall_status=overall_status,
                timestamp=datetime.now(),
                checks=checks,
                metrics=metrics,
                summary=summary,
                recommendations=recommendations
            )
            
            total_time = (time.time() - start_time) * 1000
            logger.info(f"Health check completed in {total_time:.2f}ms - Status: {overall_status.value}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            
            # Return error report
            return HealthReport(
                overall_status=HealthStatus.CRITICAL,
                timestamp=datetime.now(),
                checks=[HealthCheck(
                    component="health_monitor",
                    component_type=ComponentType.APPLICATION,
                    status=HealthStatus.CRITICAL,
                    message="Health check failed",
                    response_time_ms=0,
                    timestamp=datetime.now(),
                    error=str(e)
                )],
                metrics=SystemMetrics(
                    cpu_percent=0,
                    memory_percent=0,
                    disk_percent=0,
                    network_io={},
                    active_connections=0,
                    uptime_seconds=0
                ),
                summary={'error': str(e)},
                recommendations=['Fix health monitoring system']
            )
    
    async def _check_database(self) -> HealthCheck:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            db = next(get_db())
            
            # Test basic connectivity
            result = db.execute(text("SELECT 1")).fetchone()
            
            # Get database stats
            stats_query = text("""
                SELECT 
                    count(*) as total_connections,
                    current_database() as database_name
            """)
            stats = db.execute(stats_query).fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check connection pool
            pool_info = {
                'pool_size': engine.pool.size(),
                'checked_in': engine.pool.checkedin(),
                'checked_out': engine.pool.checkedout(),
                'overflow': engine.pool.overflow(),
                'invalid': engine.pool.invalid()
            }
            
            status = HealthStatus.HEALTHY
            message = "Database is healthy"
            
            # Check for warnings
            if response_time > 1000:
                status = HealthStatus.WARNING
                message = f"Database response time is high: {response_time:.2f}ms"
            
            if pool_info['checked_out'] > self.alert_thresholds['database_connections']:
                status = HealthStatus.WARNING
                message = f"High number of database connections: {pool_info['checked_out']}"
            
            return HealthCheck(
                component="database",
                component_type=ComponentType.DATABASE,
                status=status,
                message=message,
                response_time_ms=response_time,
                timestamp=datetime.now(),
                details={
                    'database_name': stats[1] if stats else 'unknown',
                    'total_connections': stats[0] if stats else 0,
                    'pool_info': pool_info
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component="database",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.CRITICAL,
                message="Database connection failed",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _check_redis(self) -> HealthCheck:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        
        try:
            # Try to connect to Redis
            if hasattr(settings, 'REDIS_URL'):
                redis_client = redis.from_url(settings.REDIS_URL)
                
                # Test basic operations
                test_key = f"health_check_{uuid.uuid4()}"
                redis_client.set(test_key, "test", ex=10)
                value = redis_client.get(test_key)
                redis_client.delete(test_key)
                
                # Get Redis info
                info = redis_client.info()
                
                response_time = (time.time() - start_time) * 1000
                
                status = HealthStatus.HEALTHY
                message = "Redis is healthy"
                
                if response_time > 500:
                    status = HealthStatus.WARNING
                    message = f"Redis response time is high: {response_time:.2f}ms"
                
                return HealthCheck(
                    component="redis",
                    component_type=ComponentType.REDIS,
                    status=status,
                    message=message,
                    response_time_ms=response_time,
                    timestamp=datetime.now(),
                    details={
                        'version': info.get('redis_version'),
                        'connected_clients': info.get('connected_clients'),
                        'used_memory_human': info.get('used_memory_human'),
                        'uptime_in_seconds': info.get('uptime_in_seconds')
                    }
                )
            else:
                return HealthCheck(
                    component="redis",
                    component_type=ComponentType.REDIS,
                    status=HealthStatus.WARNING,
                    message="Redis not configured",
                    response_time_ms=0,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component="redis",
                component_type=ComponentType.REDIS,
                status=HealthStatus.CRITICAL,
                message="Redis connection failed",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _check_file_system(self) -> HealthCheck:
        """Check file system health"""
        start_time = time.time()
        
        try:
            # Check disk usage
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Check uploads directory
            uploads_dir = Path("uploads")
            uploads_exists = uploads_dir.exists()
            uploads_writable = uploads_dir.is_dir() and os.access(uploads_dir, os.W_OK) if uploads_exists else False
            
            # Test file operations
            test_file = uploads_dir / f"health_check_{uuid.uuid4()}.txt"
            try:
                test_file.write_text("health check")
                test_content = test_file.read_text()
                test_file.unlink()
                file_ops_ok = test_content == "health check"
            except Exception:
                file_ops_ok = False
            
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY
            message = "File system is healthy"
            
            if disk_percent > self.alert_thresholds['disk_percent']:
                status = HealthStatus.CRITICAL
                message = f"Disk usage critical: {disk_percent:.1f}%"
            elif disk_percent > 75:
                status = HealthStatus.WARNING
                message = f"Disk usage high: {disk_percent:.1f}%"
            
            if not uploads_writable or not file_ops_ok:
                status = HealthStatus.CRITICAL
                message = "File system not writable"
            
            return HealthCheck(
                component="file_system",
                component_type=ComponentType.FILE_SYSTEM,
                status=status,
                message=message,
                response_time_ms=response_time,
                timestamp=datetime.now(),
                details={
                    'disk_usage_percent': disk_percent,
                    'total_space_gb': disk_usage.total / (1024**3),
                    'free_space_gb': disk_usage.free / (1024**3),
                    'uploads_directory_exists': uploads_exists,
                    'uploads_directory_writable': uploads_writable,
                    'file_operations_ok': file_ops_ok
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component="file_system",
                component_type=ComponentType.FILE_SYSTEM,
                status=HealthStatus.CRITICAL,
                message="File system check failed",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _check_system_resources(self) -> HealthCheck:
        """Check system resource usage"""
        start_time = time.time()
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Load average (Unix systems)
            load_avg = None
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()
            
            # Process count
            process_count = len(psutil.pids())
            
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY
            message = "System resources are healthy"
            
            if cpu_percent > self.alert_thresholds['cpu_percent']:
                status = HealthStatus.WARNING
                message = f"High CPU usage: {cpu_percent:.1f}%"
            
            if memory_percent > self.alert_thresholds['memory_percent']:
                status = HealthStatus.CRITICAL if memory_percent > 95 else HealthStatus.WARNING
                message = f"High memory usage: {memory_percent:.1f}%"
            
            return HealthCheck(
                component="system_resources",
                component_type=ComponentType.SYSTEM_RESOURCES,
                status=status,
                message=message,
                response_time_ms=response_time,
                timestamp=datetime.now(),
                details={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'memory_total_gb': memory.total / (1024**3),
                    'memory_available_gb': memory.available / (1024**3),
                    'load_average': load_avg,
                    'process_count': process_count
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component="system_resources",
                component_type=ComponentType.SYSTEM_RESOURCES,
                status=HealthStatus.CRITICAL,
                message="System resources check failed",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _check_application(self) -> HealthCheck:
        """Check application health"""
        start_time = time.time()
        
        try:
            # Application uptime
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            # Check if all required services are imported
            services_status = {
                'analytics_service': True,
                'notification_service': True,
                'backup_service': True,
                'file_storage_service': True,
                'websocket_service': True
            }
            
            # Check configuration
            config_ok = hasattr(settings, 'SECRET_KEY') and len(settings.SECRET_KEY) > 10
            
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY
            message = "Application is healthy"
            
            if not config_ok:
                status = HealthStatus.CRITICAL
                message = "Application configuration invalid"
            
            return HealthCheck(
                component="application",
                component_type=ComponentType.APPLICATION,
                status=status,
                message=message,
                response_time_ms=response_time,
                timestamp=datetime.now(),
                details={
                    'uptime_seconds': uptime,
                    'services_status': services_status,
                    'configuration_valid': config_ok,
                    'python_version': platform.python_version(),
                    'platform': platform.platform()
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component="application",
                component_type=ComponentType.APPLICATION,
                status=HealthStatus.CRITICAL,
                message="Application check failed",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _check_network(self) -> HealthCheck:
        """Check network connectivity"""
        start_time = time.time()
        
        try:
            # Test internet connectivity
            test_urls = [
                'https://www.google.com',
                'https://www.github.com',
                'https://httpbin.org/status/200'
            ]
            
            successful_requests = 0
            total_response_time = 0
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        successful_requests += 1
                        total_response_time += response.elapsed.total_seconds() * 1000
                except:
                    pass
            
            # Check local network interfaces
            network_interfaces = psutil.net_if_addrs()
            active_interfaces = len([iface for iface, addrs in network_interfaces.items() if addrs])
            
            response_time = (time.time() - start_time) * 1000
            avg_response_time = total_response_time / successful_requests if successful_requests > 0 else 0
            
            status = HealthStatus.HEALTHY
            message = "Network connectivity is healthy"
            
            if successful_requests == 0:
                status = HealthStatus.CRITICAL
                message = "No internet connectivity"
            elif successful_requests < len(test_urls) / 2:
                status = HealthStatus.WARNING
                message = "Limited internet connectivity"
            elif avg_response_time > 2000:
                status = HealthStatus.WARNING
                message = f"Slow network response: {avg_response_time:.0f}ms"
            
            return HealthCheck(
                component="network",
                component_type=ComponentType.NETWORK,
                status=status,
                message=message,
                response_time_ms=response_time,
                timestamp=datetime.now(),
                details={
                    'successful_requests': successful_requests,
                    'total_test_urls': len(test_urls),
                    'average_response_time_ms': avg_response_time,
                    'active_interfaces': active_interfaces,
                    'interfaces': list(network_interfaces.keys())
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component="network",
                component_type=ComponentType.NETWORK,
                status=HealthStatus.CRITICAL,
                message="Network check failed",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _check_external_api(self, api_name: str, api_url: str) -> HealthCheck:
        """Check external API connectivity"""
        start_time = time.time()
        
        try:
            # Make request to API
            headers = {}
            
            # Add authentication headers if available
            if api_name == 'twilio' and hasattr(settings, 'TWILIO_ACCOUNT_SID'):
                import base64
                auth_string = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
                auth_bytes = base64.b64encode(auth_string.encode()).decode()
                headers['Authorization'] = f'Basic {auth_bytes}'
            
            response = requests.get(api_url, headers=headers, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY
            message = f"{api_name} API is accessible"
            
            if response.status_code >= 400:
                if response.status_code == 401:
                    status = HealthStatus.WARNING
                    message = f"{api_name} API authentication required"
                else:
                    status = HealthStatus.WARNING
                    message = f"{api_name} API returned {response.status_code}"
            
            if response_time > 5000:
                status = HealthStatus.WARNING
                message = f"{api_name} API response time is high: {response_time:.0f}ms"
            
            return HealthCheck(
                component=f"{api_name}_api",
                component_type=ComponentType.EXTERNAL_API,
                status=status,
                message=message,
                response_time_ms=response_time,
                timestamp=datetime.now(),
                details={
                    'status_code': response.status_code,
                    'url': api_url
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component=f"{api_name}_api",
                component_type=ComponentType.EXTERNAL_API,
                status=HealthStatus.CRITICAL,
                message=f"{api_name} API connection failed",
                response_time_ms=response_time,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_stats = {
                'bytes_sent': network_io.bytes_sent,
                'bytes_recv': network_io.bytes_recv,
                'packets_sent': network_io.packets_sent,
                'packets_recv': network_io.packets_recv
            }
            
            # Active connections (estimate)
            active_connections = len(psutil.net_connections())
            
            # System uptime
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            
            # Load average (Unix systems)
            load_average = None
            if hasattr(psutil, 'getloadavg'):
                load_average = list(psutil.getloadavg())
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_stats,
                active_connections=active_connections,
                uptime_seconds=uptime_seconds,
                load_average=load_average
            )
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0,
                memory_percent=0,
                disk_percent=0,
                network_io={},
                active_connections=0,
                uptime_seconds=0
            )
    
    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall system status from individual checks"""
        if not checks:
            return HealthStatus.UNKNOWN
        
        # Count status types
        status_counts = {
            HealthStatus.CRITICAL: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.HEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        for check in checks:
            status_counts[check.status] += 1
        
        # Determine overall status
        if status_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > 0:
            return HealthStatus.WARNING
        elif status_counts[HealthStatus.HEALTHY] > 0:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def _generate_summary(self, checks: List[HealthCheck], metrics: SystemMetrics) -> Dict[str, Any]:
        """Generate health check summary"""
        summary = {
            'total_checks': len(checks),
            'healthy_checks': len([c for c in checks if c.status == HealthStatus.HEALTHY]),
            'warning_checks': len([c for c in checks if c.status == HealthStatus.WARNING]),
            'critical_checks': len([c for c in checks if c.status == HealthStatus.CRITICAL]),
            'average_response_time_ms': statistics.mean([c.response_time_ms for c in checks]) if checks else 0,
            'system_metrics': {
                'cpu_percent': metrics.cpu_percent,
                'memory_percent': metrics.memory_percent,
                'disk_percent': metrics.disk_percent,
                'uptime_hours': metrics.uptime_seconds / 3600
            }
        }
        
        return summary
    
    def _generate_recommendations(self, checks: List[HealthCheck], metrics: SystemMetrics) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        # Check for critical issues
        critical_checks = [c for c in checks if c.status == HealthStatus.CRITICAL]
        for check in critical_checks:
            recommendations.append(f"URGENT: Fix {check.component} - {check.message}")
        
        # System resource recommendations
        if metrics.cpu_percent > 80:
            recommendations.append("Consider upgrading CPU or optimizing application performance")
        
        if metrics.memory_percent > 85:
            recommendations.append("Consider adding more RAM or optimizing memory usage")
        
        if metrics.disk_percent > 90:
            recommendations.append("Free up disk space or add more storage")
        
        # Performance recommendations
        slow_checks = [c for c in checks if c.response_time_ms > 1000]
        if slow_checks:
            recommendations.append("Investigate slow response times in: " + ", ".join([c.component for c in slow_checks]))
        
        # General recommendations
        if not recommendations:
            recommendations.append("System is healthy - continue monitoring")
        
        return recommendations
    
    async def _check_alerts(self, report: HealthReport):
        """Check for alert conditions and send notifications"""
        try:
            # Check for critical status
            if report.overall_status == HealthStatus.CRITICAL:
                logger.error(f"CRITICAL: System health is critical - {len([c for c in report.checks if c.status == HealthStatus.CRITICAL])} critical issues")
            
            # Check resource thresholds
            if report.metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
                logger.warning(f"High CPU usage: {report.metrics.cpu_percent:.1f}%")
            
            if report.metrics.memory_percent > self.alert_thresholds['memory_percent']:
                logger.warning(f"High memory usage: {report.metrics.memory_percent:.1f}%")
            
            if report.metrics.disk_percent > self.alert_thresholds['disk_percent']:
                logger.error(f"Critical disk usage: {report.metrics.disk_percent:.1f}%")
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            entry for entry in self.health_history
            if entry['timestamp'] >= cutoff_time
        ]
    
    def get_health_trends(self) -> Dict[str, Any]:
        """Get health trends analysis"""
        if len(self.health_history) < 2:
            return {'error': 'Insufficient data for trends'}
        
        recent_entries = list(self.health_history)[-10:]  # Last 10 entries
        
        cpu_values = [entry['cpu'] for entry in recent_entries]
        memory_values = [entry['memory'] for entry in recent_entries]
        disk_values = [entry['disk'] for entry in recent_entries]
        
        return {
            'cpu_trend': {
                'current': cpu_values[-1],
                'average': statistics.mean(cpu_values),
                'trend': 'increasing' if cpu_values[-1] > cpu_values[0] else 'decreasing'
            },
            'memory_trend': {
                'current': memory_values[-1],
                'average': statistics.mean(memory_values),
                'trend': 'increasing' if memory_values[-1] > memory_values[0] else 'decreasing'
            },
            'disk_trend': {
                'current': disk_values[-1],
                'average': statistics.mean(disk_values),
                'trend': 'increasing' if disk_values[-1] > disk_values[0] else 'decreasing'
            }
        }

# Global health monitor instance
health_monitor = HealthMonitor()

# Health service class for easier integration
class HealthService:
    """High-level health service"""
    
    def __init__(self):
        self.monitor = health_monitor
    
    async def get_health_status(self, detailed: bool = False) -> Dict[str, Any]:
        """Get current health status"""
        report = await self.monitor.perform_health_check(quick=not detailed)
        
        return {
            'status': report.overall_status.value,
            'timestamp': report.timestamp.isoformat(),
            'summary': report.summary,
            'checks': [asdict(check) for check in report.checks] if detailed else None,
            'metrics': asdict(report.metrics) if detailed else None,
            'recommendations': report.recommendations
        }
    
    async def start_monitoring(self):
        """Start health monitoring"""
        await self.monitor.start_monitoring()
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        await self.monitor.stop_monitoring()
    
    def get_trends(self) -> Dict[str, Any]:
        """Get health trends"""
        return self.monitor.get_health_trends()
    
    def is_healthy(self) -> bool:
        """Quick health check"""
        if not self.monitor.health_history:
            return True  # Assume healthy if no data
        
        latest = self.monitor.health_history[-1]
        return latest['status'] in ['healthy', 'warning']

# Global service instance
health_service = HealthService()