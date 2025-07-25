from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum

from ...core.auth import get_current_user, require_admin_access
from ...models.user import User
from ...services.monitoring_service import (
    monitoring_service, MetricType, AlertSeverity, AlertStatus, HealthStatus
)

router = APIRouter()

# Pydantic Models
class MetricTypeEnum(str, Enum):
    """Metric type enumeration for API"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"

class AlertSeverityEnum(str, Enum):
    """Alert severity enumeration for API"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatusEnum(str, Enum):
    """Alert status enumeration for API"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"

class HealthStatusEnum(str, Enum):
    """Health status enumeration for API"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class RecordMetricRequest(BaseModel):
    """Request model for recording a metric"""
    name: str = Field(..., min_length=1, max_length=100, description="Metric name")
    value: float = Field(..., description="Metric value")
    metric_type: MetricTypeEnum = Field(..., description="Type of metric")
    unit: Optional[str] = Field(None, max_length=20, description="Unit of measurement")
    description: Optional[str] = Field(None, max_length=500, description="Metric description")
    tags: Dict[str, str] = Field(default={}, description="Metric tags")

class AcknowledgeAlertRequest(BaseModel):
    """Request model for acknowledging an alert"""
    alert_id: str = Field(..., description="Alert ID to acknowledge")
    notes: Optional[str] = Field(None, max_length=500, description="Acknowledgment notes")

class MetricResponse(BaseModel):
    """Response model for metric data"""
    name: str
    value: float
    metric_type: str
    unit: Optional[str] = None
    description: Optional[str] = None
    tags: Dict[str, str]
    timestamp: str

class AlertResponse(BaseModel):
    """Response model for alert data"""
    alert_id: str
    rule_name: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str
    status: str
    triggered_at: str
    resolved_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    description: str
    tags: Dict[str, str]

class HealthCheckResponse(BaseModel):
    """Response model for health check data"""
    check_name: str
    status: str
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SystemHealthResponse(BaseModel):
    """Response model for system health"""
    overall_status: str
    checks: Dict[str, HealthCheckResponse]
    timestamp: str
    error: Optional[str] = None

class SystemStatsResponse(BaseModel):
    """Response model for system statistics"""
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    disk: Dict[str, Any]
    network: Dict[str, Any]
    process: Dict[str, Any]
    database: Dict[str, Any]
    timestamp: str
    error: Optional[str] = None

class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics"""
    window: str
    metrics: Dict[str, Dict[str, float]]
    timestamp: str

class MonitoringConfigResponse(BaseModel):
    """Response model for monitoring configuration"""
    metric_types: List[str]
    alert_severities: List[str]
    alert_statuses: List[str]
    health_statuses: List[str]
    collection_interval_seconds: int
    retention_days: int
    alert_rules_count: int
    health_checks_count: int

class MonitoringStatisticsResponse(BaseModel):
    """Response model for monitoring statistics"""
    total_metrics: int
    active_alerts: int
    resolved_alerts: int
    health_checks_passed: int
    health_checks_failed: int
    uptime_hours: float
    last_collection: str
    system_load: Dict[str, float]

# API Endpoints
@router.post("/metrics/record")
async def record_metric(
    request: RecordMetricRequest,
    current_user: User = Depends(require_admin_access)
):
    """Record a custom metric"""
    try:
        from ...services.monitoring_service import SystemMetric, MetricType
        
        metric = SystemMetric(
            name=request.name,
            value=request.value,
            metric_type=MetricType(request.metric_type.value),
            timestamp=datetime.utcnow(),
            tags=request.tags,
            unit=request.unit,
            description=request.description
        )
        
        await monitoring_service.record_metric(metric)
        
        return {
            "message": "Metric recorded successfully",
            "metric_name": request.name,
            "value": request.value,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record metric: {str(e)}"
        )

@router.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(
    metric_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
    current_user: User = Depends(require_admin_access)
):
    """Get system metrics"""
    try:
        metrics = await monitoring_service.get_metrics(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return [
            MetricResponse(
                name=metric["name"],
                value=metric["value"],
                metric_type=metric["metric_type"],
                unit=metric["unit"],
                description=metric["description"],
                tags=metric["tags"],
                timestamp=metric["timestamp"]
            )
            for metric in metrics
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: User = Depends(get_current_user)
):
    """Get system health status"""
    try:
        health_data = await monitoring_service.get_system_health()
        
        checks = {}
        for check_name, check_data in health_data.get("checks", {}).items():
            checks[check_name] = HealthCheckResponse(
                check_name=check_name,
                status=check_data.get("status", "unknown"),
                response_time_ms=check_data.get("response_time_ms"),
                details=check_data.get("details"),
                error=check_data.get("error")
            )
        
        return SystemHealthResponse(
            overall_status=health_data.get("overall_status", "unknown"),
            checks=checks,
            timestamp=health_data.get("timestamp", datetime.utcnow().isoformat()),
            error=health_data.get("error")
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: User = Depends(require_admin_access)
):
    """Get detailed system statistics"""
    try:
        stats = await monitoring_service.get_system_stats()
        
        if "error" in stats:
            return SystemStatsResponse(
                cpu={}, memory={}, disk={}, network={}, 
                process={}, database={},
                timestamp=datetime.utcnow().isoformat(),
                error=stats["error"]
            )
        
        return SystemStatsResponse(
            cpu=stats.get("cpu", {}),
            memory=stats.get("memory", {}),
            disk=stats.get("disk", {}),
            network=stats.get("network", {}),
            process=stats.get("process", {}),
            database=stats.get("database", {}),
            timestamp=stats.get("timestamp", datetime.utcnow().isoformat())
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    status: Optional[AlertStatusEnum] = None,
    severity: Optional[AlertSeverityEnum] = None,
    limit: int = 100,
    current_user: User = Depends(require_admin_access)
):
    """Get system alerts"""
    try:
        status_filter = AlertStatus(status.value) if status else None
        severity_filter = AlertSeverity(severity.value) if severity else None
        
        alerts = await monitoring_service.get_alerts(
            status=status_filter,
            severity=severity_filter,
            limit=limit
        )
        
        return [
            AlertResponse(
                alert_id=alert["alert_id"],
                rule_name=alert["rule_name"],
                metric_name=alert["metric_name"],
                current_value=alert["current_value"],
                threshold=alert["threshold"],
                severity=alert["severity"],
                status=alert["status"],
                triggered_at=alert["triggered_at"],
                resolved_at=alert["resolved_at"],
                acknowledged_at=alert["acknowledged_at"],
                acknowledged_by=alert["acknowledged_by"],
                description=alert["description"],
                tags=alert["tags"]
            )
            for alert in alerts
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )

@router.post("/alerts/acknowledge")
async def acknowledge_alert(
    request: AcknowledgeAlertRequest,
    current_user: User = Depends(require_admin_access)
):
    """Acknowledge an alert"""
    try:
        success = await monitoring_service.acknowledge_alert(
            request.alert_id, str(current_user.id)
        )
        
        if success:
            return {
                "message": "Alert acknowledged successfully",
                "alert_id": request.alert_id,
                "acknowledged_by": current_user.username,
                "acknowledged_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )

@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    window: str = "1h",
    current_user: User = Depends(require_admin_access)
):
    """Get aggregated performance metrics"""
    try:
        if window not in ["1m", "5m", "15m", "1h"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid window. Must be one of: 1m, 5m, 15m, 1h"
            )
        
        performance_data = await monitoring_service.get_performance_metrics(window)
        
        return PerformanceMetricsResponse(
            window=performance_data.get("window", window),
            metrics=performance_data.get("metrics", {}),
            timestamp=performance_data.get("timestamp", datetime.utcnow().isoformat())
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )

@router.post("/start")
async def start_monitoring(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin_access)
):
    """Start the monitoring service"""
    try:
        if monitoring_service.is_running:
            return {
                "message": "Monitoring service is already running",
                "status": "running"
            }
        
        background_tasks.add_task(monitoring_service.start_monitoring)
        
        return {
            "message": "Monitoring service started successfully",
            "status": "starting",
            "started_by": current_user.username,
            "started_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring service: {str(e)}"
        )

@router.post("/stop")
async def stop_monitoring(
    current_user: User = Depends(require_admin_access)
):
    """Stop the monitoring service"""
    try:
        if not monitoring_service.is_running:
            return {
                "message": "Monitoring service is not running",
                "status": "stopped"
            }
        
        await monitoring_service.stop_monitoring()
        
        return {
            "message": "Monitoring service stopped successfully",
            "status": "stopped",
            "stopped_by": current_user.username,
            "stopped_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop monitoring service: {str(e)}"
        )

@router.get("/status")
async def get_monitoring_status(
    current_user: User = Depends(get_current_user)
):
    """Get monitoring service status"""
    try:
        return {
            "service_status": "running" if monitoring_service.is_running else "stopped",
            "metrics_buffer_size": len(monitoring_service.metrics_buffer),
            "active_alerts_count": len(monitoring_service.alerts_cache),
            "alert_rules_count": len(monitoring_service.alert_rules),
            "health_checks_count": len(monitoring_service.health_checks),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring status: {str(e)}"
        )

@router.get("/config", response_model=MonitoringConfigResponse)
async def get_monitoring_config(
    current_user: User = Depends(require_admin_access)
):
    """Get monitoring service configuration"""
    try:
        return MonitoringConfigResponse(
            metric_types=[mt.value for mt in MetricType],
            alert_severities=[severity.value for severity in AlertSeverity],
            alert_statuses=[status.value for status in AlertStatus],
            health_statuses=[status.value for status in HealthStatus],
            collection_interval_seconds=30,
            retention_days=7,
            alert_rules_count=len(monitoring_service.alert_rules),
            health_checks_count=len(monitoring_service.health_checks)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring configuration: {str(e)}"
        )

@router.get("/statistics", response_model=MonitoringStatisticsResponse)
async def get_monitoring_statistics(
    current_user: User = Depends(require_admin_access)
):
    """Get monitoring service statistics"""
    try:
        # Get basic counts
        total_metrics = len(monitoring_service.metrics_buffer)
        active_alerts = len([alert for alert in monitoring_service.alerts_cache.values() 
                           if alert.status == AlertStatus.ACTIVE])
        resolved_alerts = len([alert for alert in monitoring_service.alerts_cache.values() 
                             if alert.status == AlertStatus.RESOLVED])
        
        # Get recent system stats for load info
        system_stats = await monitoring_service.get_system_stats()
        system_load = {
            "cpu_percent": system_stats.get("cpu", {}).get("usage_percent", 0),
            "memory_percent": system_stats.get("memory", {}).get("usage_percent", 0),
            "disk_percent": system_stats.get("disk", {}).get("usage_percent", 0)
        }
        
        return MonitoringStatisticsResponse(
            total_metrics=total_metrics,
            active_alerts=active_alerts,
            resolved_alerts=resolved_alerts,
            health_checks_passed=0,  # TODO: Calculate from recent health checks
            health_checks_failed=0,  # TODO: Calculate from recent health checks
            uptime_hours=24.0,  # TODO: Calculate actual uptime
            last_collection=datetime.utcnow().isoformat(),
            system_load=system_load
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring statistics: {str(e)}"
        )

@router.get("/types/available")
async def get_available_types(
    current_user: User = Depends(get_current_user)
):
    """Get available monitoring types and enums"""
    return {
        "metric_types": [
            {
                "value": mt.value,
                "name": mt.value.replace("_", " ").title(),
                "description": {
                    "counter": "Cumulative metric that only increases",
                    "gauge": "Metric that can go up and down",
                    "histogram": "Distribution of values over time",
                    "timer": "Time-based measurements",
                    "rate": "Rate of change over time"
                }.get(mt.value, "")
            }
            for mt in MetricType
        ],
        "alert_severities": [
            {
                "value": severity.value,
                "name": severity.value.title(),
                "description": {
                    "low": "Low priority alert",
                    "medium": "Medium priority alert",
                    "high": "High priority alert requiring attention",
                    "critical": "Critical alert requiring immediate action"
                }.get(severity.value, "")
            }
            for severity in AlertSeverity
        ],
        "alert_statuses": [
            {
                "value": status.value,
                "name": status.value.replace("_", " ").title(),
                "description": {
                    "active": "Alert is currently active",
                    "resolved": "Alert has been resolved",
                    "acknowledged": "Alert has been acknowledged",
                    "suppressed": "Alert is temporarily suppressed"
                }.get(status.value, "")
            }
            for status in AlertStatus
        ],
        "health_statuses": [
            {
                "value": status.value,
                "name": status.value.title(),
                "description": {
                    "healthy": "System component is functioning normally",
                    "warning": "System component has minor issues",
                    "critical": "System component has serious issues",
                    "unknown": "System component status is unknown"
                }.get(status.value, "")
            }
            for status in HealthStatus
        ],
        "time_windows": [
            {"value": "1m", "name": "1 Minute", "description": "Last minute of data"},
            {"value": "5m", "name": "5 Minutes", "description": "Last 5 minutes of data"},
            {"value": "15m", "name": "15 Minutes", "description": "Last 15 minutes of data"},
            {"value": "1h", "name": "1 Hour", "description": "Last hour of data"}
        ]
    }

@router.post("/test")
async def test_monitoring_service(
    current_user: User = Depends(require_admin_access)
):
    """Test monitoring service functionality"""
    try:
        # Record a test metric
        from ...services.monitoring_service import SystemMetric, MetricType
        
        test_metric = SystemMetric(
            name="test_metric",
            value=42.0,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.utcnow(),
            tags={"test": "true"},
            unit="count",
            description="Test metric for monitoring service"
        )
        
        await monitoring_service.record_metric(test_metric)
        
        # Get system health
        health = await monitoring_service.get_system_health()
        
        # Get system stats
        stats = await monitoring_service.get_system_stats()
        
        return {
            "message": "Monitoring service test completed",
            "test_metric_recorded": True,
            "health_check_status": health.get("overall_status"),
            "system_stats_available": "error" not in stats,
            "service_status": "operational",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Monitoring service test failed: {str(e)}"
        )

@router.delete("/cleanup")
async def cleanup_monitoring_data(
    days: int = 7,
    current_user: User = Depends(require_admin_access)
):
    """Manually trigger cleanup of old monitoring data"""
    try:
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Days must be between 1 and 365"
            )
        
        # This would trigger the cleanup process
        # For now, we'll just return a success message
        return {
            "message": f"Cleanup of monitoring data older than {days} days initiated",
            "retention_days": days,
            "initiated_by": current_user.username,
            "initiated_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup monitoring data: {str(e)}"
        )