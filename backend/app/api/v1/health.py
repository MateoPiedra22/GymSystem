from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from datetime import datetime
from ...services.health_service import health_service, HealthStatus
from ...core.auth import get_current_user
from ...models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/status")
async def get_health_status(
    detailed: bool = False,
    current_user: Optional[User] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get system health status
    
    - **detailed**: Include detailed metrics and checks
    - Requires authentication for detailed view
    """
    try:
        # Allow basic health check without authentication
        if detailed and not current_user:
            raise HTTPException(status_code=401, detail="Authentication required for detailed health status")
        
        # Check if user has admin privileges for detailed view
        if detailed and current_user and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required for detailed health status")
        
        status = await health_service.get_health_status(detailed=detailed)
        
        return {
            "success": True,
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health status")

@router.get("/quick")
async def quick_health_check() -> Dict[str, Any]:
    """
    Quick health check endpoint for load balancers and monitoring tools
    Returns simple OK/ERROR status
    """
    try:
        is_healthy = health_service.is_healthy()
        
        if is_healthy:
            return {
                "status": "OK",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=503, detail="Service Unavailable")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick health check: {e}")
        raise HTTPException(status_code=503, detail="Service Unavailable")

@router.get("/detailed")
async def get_detailed_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed health information including all checks and metrics
    Requires admin authentication
    """
    try:
        # Check admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        status = await health_service.get_health_status(detailed=True)
        
        return {
            "success": True,
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get detailed health information")

@router.get("/trends")
async def get_health_trends(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get health trends analysis
    Requires admin authentication
    """
    try:
        # Check admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        trends = health_service.get_trends()
        
        return {
            "success": True,
            "data": trends,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health trends")

@router.post("/monitoring/start")
async def start_health_monitoring(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start background health monitoring
    Requires admin authentication
    """
    try:
        # Check admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        # Start monitoring in background
        background_tasks.add_task(health_service.start_monitoring)
        
        return {
            "success": True,
            "message": "Health monitoring started",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting health monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to start health monitoring")

@router.post("/monitoring/stop")
async def stop_health_monitoring(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Stop background health monitoring
    Requires admin authentication
    """
    try:
        # Check admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        # Stop monitoring in background
        background_tasks.add_task(health_service.stop_monitoring)
        
        return {
            "success": True,
            "message": "Health monitoring stopped",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping health monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop health monitoring")

@router.get("/components")
async def get_component_status(
    component: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get status of specific system components
    
    - **component**: Specific component to check (database, redis, file_system, etc.)
    - If no component specified, returns all components
    """
    try:
        # Check admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        # Get detailed health status
        status = await health_service.get_health_status(detailed=True)
        
        if component:
            # Filter for specific component
            component_checks = [
                check for check in status['data']['checks']
                if check['component'] == component
            ]
            
            if not component_checks:
                raise HTTPException(status_code=404, detail=f"Component '{component}' not found")
            
            return {
                "success": True,
                "data": {
                    "component": component,
                    "checks": component_checks
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Return all components
            components = {}
            for check in status['data']['checks']:
                comp_name = check['component']
                if comp_name not in components:
                    components[comp_name] = []
                components[comp_name].append(check)
            
            return {
                "success": True,
                "data": {
                    "components": components,
                    "total_components": len(components)
                },
                "timestamp": datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting component status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get component status")

@router.get("/metrics")
async def get_system_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current system metrics
    Requires admin authentication
    """
    try:
        # Check admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        # Get detailed health status for metrics
        status = await health_service.get_health_status(detailed=True)
        
        return {
            "success": True,
            "data": {
                "metrics": status['data']['metrics'],
                "summary": status['data']['summary']
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

@router.get("/recommendations")
async def get_health_recommendations(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get health recommendations based on current system status
    Requires admin authentication
    """
    try:
        # Check admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        # Get health status with recommendations
        status = await health_service.get_health_status(detailed=True)
        
        return {
            "success": True,
            "data": {
                "recommendations": status['data']['recommendations'],
                "overall_status": status['data']['status'],
                "critical_issues": [
                    check for check in status['data']['checks']
                    if check['status'] == 'critical'
                ],
                "warning_issues": [
                    check for check in status['data']['checks']
                    if check['status'] == 'warning'
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health recommendations")

@router.get("/history")
async def get_health_history(
    hours: int = 24,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get health check history
    
    - **hours**: Number of hours of history to retrieve (default: 24)
    """
    try:
        # Check admin privileges
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        # Validate hours parameter
        if hours < 1 or hours > 168:  # Max 1 week
            raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
        
        history = health_service.monitor.get_health_history(hours=hours)
        
        return {
            "success": True,
            "data": {
                "history": history,
                "total_entries": len(history),
                "hours_requested": hours
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health history")

# Health check endpoint for external monitoring (no auth required)
@router.get("/ping")
async def ping() -> Dict[str, str]:
    """
    Simple ping endpoint for external monitoring
    Returns basic service availability
    """
    return {
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
        "service": "gym-system-api"
    }

# Readiness probe endpoint
@router.get("/ready")
async def readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint
    Checks if the service is ready to accept traffic
    """
    try:
        # Perform basic health check
        is_healthy = health_service.is_healthy()
        
        if is_healthy:
            return {
                "status": "ready",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=503, detail="Service not ready")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in readiness probe: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

# Liveness probe endpoint
@router.get("/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint
    Checks if the service is alive
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }