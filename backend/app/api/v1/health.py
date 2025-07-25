from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import logging
import psutil
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/status")
async def get_health_status() -> Dict[str, Any]:
    """
    Get basic system health status
    """
    try:
        # Basic system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "uptime": psutil.boot_time()
            },
            "environment": os.environ.get('ENVIRONMENT', 'production'),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health status")

@router.get("/quick")
async def quick_health_check() -> Dict[str, Any]:
    """
    Quick health check endpoint for load balancers and monitoring tools
    Returns simple OK status
    """
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "service": "GymSystem API"
    }

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
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/live")
async def liveness_probe() -> Dict[str, Any]:
    """
    Liveness probe endpoint for Kubernetes/Docker health checks
    Checks if the service is alive and responding
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }