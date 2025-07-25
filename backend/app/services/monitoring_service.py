from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import psutil
import time
import logging
import json
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy import func, text
from ..core.database import Base, get_db, engine
from ..core.config import settings
from .config_service import config_service
# import aioredis  # Commented out due to Python 3.13 compatibility issues
import aiofiles
from collections import defaultdict, deque
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"

class HealthStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class SystemMetric:
    """System metric data structure"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None
    description: Optional[str] = None

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric_name: str
    condition: str  # e.g., ">", "<", "==", "!="
    threshold: Union[int, float]
    severity: AlertSeverity
    duration: int  # seconds
    description: str
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_name: str
    metric_name: str
    current_value: Union[int, float]
    threshold: Union[int, float]
    severity: AlertSeverity
    status: AlertStatus
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

class SystemMetricModel(Base):
    """System metrics database model"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    metric_type = Column(String(20), nullable=False)
    unit = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AlertModel(Base):
    """Alerts database model"""
    __tablename__ = "system_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(100), unique=True, nullable=False, index=True)
    rule_name = Column(String(100), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    
    current_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    
    triggered_at = Column(DateTime, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    alert_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HealthCheckModel(Base):
    """Health check results database model"""
    __tablename__ = "health_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    check_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    response_time_ms = Column(Float, nullable=True)
    
    details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    checked_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MonitoringService:
    """Comprehensive system monitoring service"""
    
    def __init__(self):
        self.metrics_buffer = deque(maxlen=10000)  # In-memory metrics buffer
        self.alerts_cache = {}  # Active alerts cache
        self.alert_rules = {}  # Alert rules cache
        self.health_checks = {}  # Health check functions
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Metric aggregation windows
        self.metric_windows = {
            "1m": deque(maxlen=60),
            "5m": deque(maxlen=300),
            "15m": deque(maxlen=900),
            "1h": deque(maxlen=3600)
        }
        
        self._load_alert_rules()
        self._register_default_health_checks()
    
    async def start_monitoring(self):
        """Start the monitoring service"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting monitoring service")
        
        # Start background tasks
        asyncio.create_task(self._collect_system_metrics())
        asyncio.create_task(self._process_alerts())
        asyncio.create_task(self._run_health_checks())
        asyncio.create_task(self._cleanup_old_data())
    
    async def stop_monitoring(self):
        """Stop the monitoring service"""
        self.is_running = False
        logger.info("Stopping monitoring service")
    
    async def record_metric(self, metric: SystemMetric):
        """Record a system metric"""
        try:
            # Add to buffer
            self.metrics_buffer.append(metric)
            
            # Add to time windows
            for window in self.metric_windows.values():
                window.append(metric)
            
            # Persist to database (async)
            asyncio.create_task(self._persist_metric(metric))
            
            # Check alert rules
            await self._check_alert_rules(metric)
            
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
    
    async def get_metrics(self, metric_name: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: int = 1000) -> List[Dict[str, Any]]:
        """Get metrics from database"""
        try:
            db = next(get_db())
            
            query = db.query(SystemMetricModel)
            
            if metric_name:
                query = query.filter(SystemMetricModel.name == metric_name)
            if start_time:
                query = query.filter(SystemMetricModel.timestamp >= start_time)
            if end_time:
                query = query.filter(SystemMetricModel.timestamp <= end_time)
            
            metrics = query.order_by(SystemMetricModel.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "metric_type": metric.metric_type,
                    "unit": metric.unit,
                    "description": metric.description,
                    "tags": metric.tags or {},
                    "timestamp": metric.timestamp.isoformat()
                }
                for metric in metrics
            ]
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return []
        finally:
            db.close()
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            health_results = {}
            overall_status = HealthStatus.HEALTHY
            
            # Run all health checks
            for check_name, check_func in self.health_checks.items():
                try:
                    start_time = time.time()
                    result = await check_func()
                    response_time = (time.time() - start_time) * 1000
                    
                    health_results[check_name] = {
                        "status": result.get("status", HealthStatus.UNKNOWN.value),
                        "response_time_ms": response_time,
                        "details": result.get("details", {}),
                        "error": result.get("error")
                    }
                    
                    # Update overall status
                    check_status = HealthStatus(result.get("status", HealthStatus.UNKNOWN.value))
                    if check_status == HealthStatus.CRITICAL:
                        overall_status = HealthStatus.CRITICAL
                    elif check_status == HealthStatus.WARNING and overall_status != HealthStatus.CRITICAL:
                        overall_status = HealthStatus.WARNING
                    
                    # Persist health check result
                    await self._persist_health_check(check_name, result, response_time)
                    
                except Exception as e:
                    logger.error(f"Health check {check_name} failed: {e}")
                    health_results[check_name] = {
                        "status": HealthStatus.CRITICAL.value,
                        "error": str(e)
                    }
                    overall_status = HealthStatus.CRITICAL
            
            return {
                "overall_status": overall_status.value,
                "checks": health_results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                "overall_status": HealthStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # Database stats
            db_stats = await self._get_database_stats()
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
                },
                "memory": {
                    "total_bytes": memory.total,
                    "available_bytes": memory.available,
                    "used_bytes": memory.used,
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total_bytes": disk.total,
                    "free_bytes": disk.free,
                    "used_bytes": disk.used,
                    "usage_percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "process": {
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads()
                },
                "database": db_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {"error": str(e)}
    
    async def get_alerts(self, status: Optional[AlertStatus] = None,
                        severity: Optional[AlertSeverity] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get system alerts"""
        try:
            db = next(get_db())
            
            query = db.query(AlertModel)
            
            if status:
                query = query.filter(AlertModel.status == status.value)
            if severity:
                query = query.filter(AlertModel.severity == severity.value)
            
            alerts = query.order_by(AlertModel.triggered_at.desc()).limit(limit).all()
            
            return [
                {
                    "alert_id": alert.alert_id,
                    "rule_name": alert.rule_name,
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                    "severity": alert.severity,
                    "status": alert.status,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                    "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    "acknowledged_by": alert.acknowledged_by,
                    "description": alert.description,
                    "tags": alert.tags or {}
                }
                for alert in alerts
            ]
            
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []
        finally:
            db.close()
    
    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            db = next(get_db())
            
            alert = db.query(AlertModel).filter(
                AlertModel.alert_id == alert_id
            ).first()
            
            if alert:
                alert.status = AlertStatus.ACKNOWLEDGED.value
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by = user_id
                db.commit()
                
                # Update cache
                if alert_id in self.alerts_cache:
                    self.alerts_cache[alert_id].status = AlertStatus.ACKNOWLEDGED
                    self.alerts_cache[alert_id].acknowledged_at = datetime.utcnow()
                    self.alerts_cache[alert_id].acknowledged_by = user_id
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return False
        finally:
            db.close()
    
    async def get_performance_metrics(self, window: str = "1h") -> Dict[str, Any]:
        """Get aggregated performance metrics"""
        try:
            if window not in self.metric_windows:
                window = "1h"
            
            metrics_data = list(self.metric_windows[window])
            
            # Group metrics by name
            grouped_metrics = defaultdict(list)
            for metric in metrics_data:
                grouped_metrics[metric.name].append(metric.value)
            
            # Calculate aggregations
            aggregated = {}
            for name, values in grouped_metrics.items():
                if values:
                    aggregated[name] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "latest": values[-1] if values else 0
                    }
            
            return {
                "window": window,
                "metrics": aggregated,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    async def _collect_system_metrics(self):
        """Background task to collect system metrics"""
        while self.is_running:
            try:
                # Collect CPU metrics
                cpu_percent = psutil.cpu_percent()
                await self.record_metric(SystemMetric(
                    name="cpu_usage_percent",
                    value=cpu_percent,
                    metric_type=MetricType.GAUGE,
                    timestamp=datetime.utcnow(),
                    unit="percent",
                    description="CPU usage percentage"
                ))
                
                # Collect memory metrics
                memory = psutil.virtual_memory()
                await self.record_metric(SystemMetric(
                    name="memory_usage_percent",
                    value=memory.percent,
                    metric_type=MetricType.GAUGE,
                    timestamp=datetime.utcnow(),
                    unit="percent",
                    description="Memory usage percentage"
                ))
                
                # Collect disk metrics
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                await self.record_metric(SystemMetric(
                    name="disk_usage_percent",
                    value=disk_percent,
                    metric_type=MetricType.GAUGE,
                    timestamp=datetime.utcnow(),
                    unit="percent",
                    description="Disk usage percentage"
                ))
                
                # Collect database metrics
                db_stats = await self._get_database_stats()
                if db_stats.get("connection_count"):
                    await self.record_metric(SystemMetric(
                        name="database_connections",
                        value=db_stats["connection_count"],
                        metric_type=MetricType.GAUGE,
                        timestamp=datetime.utcnow(),
                        unit="count",
                        description="Active database connections"
                    ))
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _process_alerts(self):
        """Background task to process alerts"""
        while self.is_running:
            try:
                # Check for resolved alerts
                current_time = datetime.utcnow()
                resolved_alerts = []
                
                for alert_id, alert in self.alerts_cache.items():
                    if alert.status == AlertStatus.ACTIVE:
                        # Check if alert should be resolved
                        # This is a simplified check - in practice, you'd re-evaluate the condition
                        if (current_time - alert.triggered_at).total_seconds() > 300:  # 5 minutes
                            alert.status = AlertStatus.RESOLVED
                            alert.resolved_at = current_time
                            resolved_alerts.append(alert_id)
                
                # Update resolved alerts in database
                for alert_id in resolved_alerts:
                    await self._update_alert_status(alert_id, AlertStatus.RESOLVED)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error processing alerts: {e}")
                await asyncio.sleep(120)  # Wait longer on error
    
    async def _run_health_checks(self):
        """Background task to run health checks"""
        while self.is_running:
            try:
                await self.get_system_health()
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error running health checks: {e}")
                await asyncio.sleep(600)  # Wait longer on error
    
    async def _cleanup_old_data(self):
        """Background task to cleanup old monitoring data"""
        while self.is_running:
            try:
                # Clean up old metrics (keep last 7 days)
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                
                db = next(get_db())
                
                # Delete old metrics
                db.query(SystemMetricModel).filter(
                    SystemMetricModel.timestamp < cutoff_date
                ).delete()
                
                # Delete old health checks
                db.query(HealthCheckModel).filter(
                    HealthCheckModel.checked_at < cutoff_date
                ).delete()
                
                # Delete resolved alerts older than 30 days
                alert_cutoff = datetime.utcnow() - timedelta(days=30)
                db.query(AlertModel).filter(
                    AlertModel.status == AlertStatus.RESOLVED.value,
                    AlertModel.resolved_at < alert_cutoff
                ).delete()
                
                db.commit()
                db.close()
                
                await asyncio.sleep(86400)  # Run daily
                
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    def _load_alert_rules(self):
        """Load alert rules from configuration"""
        try:
            # Default alert rules
            default_rules = [
                AlertRule(
                    name="high_cpu_usage",
                    metric_name="cpu_usage_percent",
                    condition=">",
                    threshold=80.0,
                    severity=AlertSeverity.HIGH,
                    duration=300,  # 5 minutes
                    description="CPU usage is above 80%"
                ),
                AlertRule(
                    name="high_memory_usage",
                    metric_name="memory_usage_percent",
                    condition=">",
                    threshold=85.0,
                    severity=AlertSeverity.HIGH,
                    duration=300,
                    description="Memory usage is above 85%"
                ),
                AlertRule(
                    name="high_disk_usage",
                    metric_name="disk_usage_percent",
                    condition=">",
                    threshold=90.0,
                    severity=AlertSeverity.CRITICAL,
                    duration=60,
                    description="Disk usage is above 90%"
                )
            ]
            
            for rule in default_rules:
                self.alert_rules[rule.name] = rule
            
        except Exception as e:
            logger.error(f"Failed to load alert rules: {e}")
    
    def _register_default_health_checks(self):
        """Register default health check functions"""
        self.health_checks["database"] = self._check_database_health
        self.health_checks["disk_space"] = self._check_disk_space
        self.health_checks["memory"] = self._check_memory_health
        self.health_checks["cpu"] = self._check_cpu_health
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            db = next(get_db())
            
            # Simple query to test connection
            result = db.execute(text("SELECT 1")).fetchone()
            
            if result:
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "details": {"connection": "ok"}
                }
            else:
                return {
                    "status": HealthStatus.CRITICAL.value,
                    "details": {"connection": "failed"}
                }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "error": str(e)
            }
        finally:
            db.close()
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space health"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            if usage_percent > 95:
                status = HealthStatus.CRITICAL
            elif usage_percent > 85:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.HEALTHY
            
            return {
                "status": status.value,
                "details": {
                    "usage_percent": usage_percent,
                    "free_gb": disk.free / (1024**3),
                    "total_gb": disk.total / (1024**3)
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "error": str(e)
            }
    
    async def _check_memory_health(self) -> Dict[str, Any]:
        """Check memory health"""
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent > 95:
                status = HealthStatus.CRITICAL
            elif memory.percent > 85:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.HEALTHY
            
            return {
                "status": status.value,
                "details": {
                    "usage_percent": memory.percent,
                    "available_gb": memory.available / (1024**3),
                    "total_gb": memory.total / (1024**3)
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "error": str(e)
            }
    
    async def _check_cpu_health(self) -> Dict[str, Any]:
        """Check CPU health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent > 95:
                status = HealthStatus.CRITICAL
            elif cpu_percent > 80:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.HEALTHY
            
            return {
                "status": status.value,
                "details": {
                    "usage_percent": cpu_percent,
                    "cpu_count": psutil.cpu_count()
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL.value,
                "error": str(e)
            }
    
    async def _get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            db = next(get_db())
            
            # Get connection count (PostgreSQL specific)
            result = db.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )).fetchone()
            
            connection_count = result[0] if result else 0
            
            return {
                "connection_count": connection_count,
                "status": "connected"
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            db.close()
    
    async def _persist_metric(self, metric: SystemMetric):
        """Persist metric to database"""
        try:
            db = next(get_db())
            
            metric_model = SystemMetricModel(
                name=metric.name,
                value=metric.value,
                metric_type=metric.metric_type.value,
                unit=metric.unit,
                description=metric.description,
                tags=metric.tags,
                timestamp=metric.timestamp
            )
            
            db.add(metric_model)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to persist metric: {e}")
        finally:
            db.close()
    
    async def _persist_health_check(self, check_name: str, result: Dict[str, Any], response_time: float):
        """Persist health check result to database"""
        try:
            db = next(get_db())
            
            health_check = HealthCheckModel(
                check_name=check_name,
                status=result.get("status", HealthStatus.UNKNOWN.value),
                response_time_ms=response_time,
                details=result.get("details"),
                error_message=result.get("error"),
                checked_at=datetime.utcnow()
            )
            
            db.add(health_check)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to persist health check: {e}")
        finally:
            db.close()
    
    async def _check_alert_rules(self, metric: SystemMetric):
        """Check if metric triggers any alert rules"""
        for rule_name, rule in self.alert_rules.items():
            if rule.metric_name == metric.name and rule.enabled:
                triggered = False
                
                if rule.condition == ">" and metric.value > rule.threshold:
                    triggered = True
                elif rule.condition == "<" and metric.value < rule.threshold:
                    triggered = True
                elif rule.condition == "==" and metric.value == rule.threshold:
                    triggered = True
                elif rule.condition == "!=" and metric.value != rule.threshold:
                    triggered = True
                
                if triggered:
                    await self._trigger_alert(rule, metric)
    
    async def _trigger_alert(self, rule: AlertRule, metric: SystemMetric):
        """Trigger an alert"""
        try:
            alert_id = f"{rule.name}_{int(time.time())}"
            
            alert = Alert(
                id=alert_id,
                rule_name=rule.name,
                metric_name=metric.name,
                current_value=metric.value,
                threshold=rule.threshold,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                triggered_at=datetime.utcnow(),
                description=rule.description,
                tags=rule.tags
            )
            
            # Add to cache
            self.alerts_cache[alert_id] = alert
            
            # Persist to database
            await self._persist_alert(alert)
            
            logger.warning(f"Alert triggered: {rule.name} - {rule.description}")
            
        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")
    
    async def _persist_alert(self, alert: Alert):
        """Persist alert to database"""
        try:
            db = next(get_db())
            
            alert_model = AlertModel(
                alert_id=alert.id,
                rule_name=alert.rule_name,
                metric_name=alert.metric_name,
                current_value=alert.current_value,
                threshold=alert.threshold,
                severity=alert.severity.value,
                status=alert.status.value,
                triggered_at=alert.triggered_at,
                description=alert.description,
                tags=alert.tags
            )
            
            db.add(alert_model)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to persist alert: {e}")
        finally:
            db.close()
    
    async def _update_alert_status(self, alert_id: str, status: AlertStatus):
        """Update alert status in database"""
        try:
            db = next(get_db())
            
            alert = db.query(AlertModel).filter(
                AlertModel.alert_id == alert_id
            ).first()
            
            if alert:
                alert.status = status.value
                if status == AlertStatus.RESOLVED:
                    alert.resolved_at = datetime.utcnow()
                db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update alert status: {e}")
        finally:
            db.close()

# Global monitoring service instance
monitoring_service = MonitoringService()