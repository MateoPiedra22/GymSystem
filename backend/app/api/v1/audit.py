from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.auth import get_current_user, require_admin_access
from ...models.user import User
from ...services.audit_service import (
    audit_service,
    AuditAction,
    AuditCategory,
    AuditLevel
)
from pydantic import BaseModel, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])

# Pydantic models for request/response
class AuditLogResponse(BaseModel):
    """Response model for audit log entries"""
    id: int
    event_id: str
    timestamp: str
    action: str
    category: str
    level: str
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    description: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None

class AuditStatisticsResponse(BaseModel):
    """Response model for audit statistics"""
    total_events: int
    successful_events: int
    failed_events: int
    success_rate: float
    action_counts: Dict[str, int]
    category_counts: Dict[str, int]
    level_counts: Dict[str, int]
    user_counts: Dict[str, int]
    performance_stats: Dict[str, Dict[str, float]]
    date_range: Dict[str, Optional[str]]

class CleanupResponse(BaseModel):
    """Response model for cleanup operations"""
    deleted_count: int
    message: str

class AuditActionEnum(str, Enum):
    """Enum for audit actions (for API documentation)"""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    MEMBERSHIP_CREATE = "membership_create"
    MEMBERSHIP_UPDATE = "membership_update"
    PAYMENT_CREATE = "payment_create"
    CLASS_CREATE = "class_create"
    CONFIG_UPDATE = "config_update"
    DATA_EXPORT = "data_export"
    SECURITY_BREACH_ATTEMPT = "security_breach_attempt"
    SYSTEM_START = "system_start"
    API_CALL = "api_call"

class AuditCategoryEnum(str, Enum):
    """Enum for audit categories (for API documentation)"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_ADMINISTRATION = "system_administration"
    SECURITY = "security"
    BUSINESS_OPERATION = "business_operation"
    SYSTEM_EVENT = "system_event"
    USER_ACTIVITY = "user_activity"
    API_USAGE = "api_usage"

class AuditLevelEnum(str, Enum):
    """Enum for audit levels (for API documentation)"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    DEBUG = "debug"

@router.get(
    "/logs",
    response_model=List[AuditLogResponse],
    summary="Get audit logs",
    description="Retrieve audit logs with optional filtering. Requires admin privileges."
)
async def get_audit_logs(
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for filtering logs (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for filtering logs (ISO format)"
    ),
    user_id: Optional[int] = Query(
        None,
        description="Filter by user ID"
    ),
    action: Optional[AuditActionEnum] = Query(
        None,
        description="Filter by action type"
    ),
    category: Optional[AuditCategoryEnum] = Query(
        None,
        description="Filter by category"
    ),
    level: Optional[AuditLevelEnum] = Query(
        None,
        description="Filter by severity level"
    ),
    resource_type: Optional[str] = Query(
        None,
        description="Filter by resource type"
    ),
    success: Optional[bool] = Query(
        None,
        description="Filter by success status"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of logs to return"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of logs to skip"
    ),
    current_user: User = Depends(require_admin_access)
):
    """Get audit logs with filtering options"""
    try:
        # Convert enum values to audit service enums
        audit_action = AuditAction(action.value) if action else None
        audit_category = AuditCategory(category.value) if category else None
        audit_level = AuditLevel(level.value) if level else None
        
        logs = await audit_service.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            action=audit_action,
            category=audit_category,
            level=audit_level,
            resource_type=resource_type,
            success=success,
            limit=limit,
            offset=offset
        )
        
        return logs
        
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving audit logs"
        )

@router.get(
    "/statistics",
    response_model=AuditStatisticsResponse,
    summary="Get audit statistics",
    description="Get comprehensive audit statistics and analytics. Requires admin privileges."
)
async def get_audit_statistics(
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for statistics (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for statistics (ISO format)"
    ),
    current_user: User = Depends(require_admin_access)
):
    """Get audit statistics and analytics"""
    try:
        stats = await audit_service.get_audit_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving audit statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving audit statistics"
        )

@router.get(
    "/logs/{event_id}",
    response_model=AuditLogResponse,
    summary="Get specific audit log",
    description="Retrieve a specific audit log by event ID. Requires admin privileges."
)
async def get_audit_log(
    event_id: str = Path(..., description="Event ID of the audit log"),
    current_user: User = Depends(require_admin_access)
):
    """Get a specific audit log by event ID"""
    try:
        logs = await audit_service.get_audit_logs(
            limit=1,
            offset=0
        )
        
        # Find log with matching event_id
        for log in logs:
            if log.get('event_id') == event_id:
                return log
        
        raise HTTPException(
            status_code=404,
            detail=f"Audit log with event ID {event_id} not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit log {event_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving audit log"
        )

@router.get(
    "/user/{user_id}/logs",
    response_model=List[AuditLogResponse],
    summary="Get user audit logs",
    description="Get audit logs for a specific user. Requires admin privileges."
)
async def get_user_audit_logs(
    user_id: int = Path(..., description="User ID"),
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for filtering logs (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for filtering logs (ISO format)"
    ),
    action: Optional[AuditActionEnum] = Query(
        None,
        description="Filter by action type"
    ),
    limit: int = Query(
        50,
        ge=1,
        le=500,
        description="Maximum number of logs to return"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of logs to skip"
    ),
    current_user: User = Depends(require_admin_access)
):
    """Get audit logs for a specific user"""
    try:
        audit_action = AuditAction(action.value) if action else None
        
        logs = await audit_service.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            action=audit_action,
            limit=limit,
            offset=offset
        )
        
        return logs
        
    except Exception as e:
        logger.error(f"Error retrieving user audit logs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving user audit logs"
        )

@router.get(
    "/security/events",
    response_model=List[AuditLogResponse],
    summary="Get security events",
    description="Get security-related audit events. Requires admin privileges."
)
async def get_security_events(
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for filtering events (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for filtering events (ISO format)"
    ),
    level: Optional[AuditLevelEnum] = Query(
        None,
        description="Filter by severity level"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Maximum number of events to return"
    ),
    current_user: User = Depends(require_admin_access)
):
    """Get security-related audit events"""
    try:
        audit_level = AuditLevel(level.value) if level else None
        
        logs = await audit_service.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            category=AuditCategory.SECURITY,
            level=audit_level,
            limit=limit,
            offset=0
        )
        
        return logs
        
    except Exception as e:
        logger.error(f"Error retrieving security events: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving security events"
        )

@router.get(
    "/performance/summary",
    summary="Get performance summary",
    description="Get performance metrics summary from audit logs. Requires admin privileges."
)
async def get_performance_summary(
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for performance data (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for performance data (ISO format)"
    ),
    current_user: User = Depends(require_admin_access)
):
    """Get performance metrics summary"""
    try:
        stats = await audit_service.get_audit_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        # Extract performance-related data
        performance_data = {
            'api_performance': stats.get('performance_stats', {}),
            'total_api_calls': stats.get('action_counts', {}).get('api_call', 0),
            'error_rate': (
                stats.get('failed_events', 0) / stats.get('total_events', 1) * 100
            ),
            'success_rate': stats.get('success_rate', 0),
            'date_range': stats.get('date_range', {})
        }
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Error retrieving performance summary: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving performance summary"
        )

@router.delete(
    "/cleanup",
    response_model=CleanupResponse,
    summary="Clean up old audit logs",
    description="Delete audit logs older than specified days. Requires admin privileges."
)
async def cleanup_audit_logs(
    days_to_keep: int = Query(
        90,
        ge=1,
        le=365,
        description="Number of days to keep audit logs"
    ),
    current_user: User = Depends(require_admin_access)
):
    """Clean up old audit logs"""
    try:
        deleted_count = await audit_service.cleanup_old_logs(days_to_keep)
        
        # Log the cleanup action
        audit_service.log(
            action=AuditAction.SYSTEM_EVENT,
            category=AuditCategory.SYSTEM_ADMINISTRATION,
            level=AuditLevel.INFO,
            description=f"Audit logs cleanup completed - deleted {deleted_count} logs older than {days_to_keep} days",
            metadata={
                'deleted_count': deleted_count,
                'days_to_keep': days_to_keep
            }
        )
        
        return CleanupResponse(
            deleted_count=deleted_count,
            message=f"Successfully deleted {deleted_count} audit logs older than {days_to_keep} days"
        )
        
    except Exception as e:
        logger.error(f"Error cleaning up audit logs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error cleaning up audit logs"
        )

@router.get(
    "/actions",
    summary="Get available audit actions",
    description="Get list of all available audit actions. Requires admin privileges."
)
async def get_audit_actions(
    current_user: User = Depends(require_admin_access)
):
    """Get list of available audit actions"""
    try:
        actions = [
            {
                'value': action.value,
                'name': action.name,
                'description': action.value.replace('_', ' ').title()
            }
            for action in AuditAction
        ]
        
        return {
            'actions': actions,
            'total_count': len(actions)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving audit actions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving audit actions"
        )

@router.get(
    "/categories",
    summary="Get available audit categories",
    description="Get list of all available audit categories. Requires admin privileges."
)
async def get_audit_categories(
    current_user: User = Depends(require_admin_access)
):
    """Get list of available audit categories"""
    try:
        categories = [
            {
                'value': category.value,
                'name': category.name,
                'description': category.value.replace('_', ' ').title()
            }
            for category in AuditCategory
        ]
        
        return {
            'categories': categories,
            'total_count': len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving audit categories: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving audit categories"
        )

@router.get(
    "/export",
    summary="Export audit logs",
    description="Export audit logs in various formats. Requires admin privileges."
)
async def export_audit_logs(
    format: str = Query(
        "json",
        pattern="^(json|csv)$",
        description="Export format (json or csv)"
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for export (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for export (ISO format)"
    ),
    category: Optional[AuditCategoryEnum] = Query(
        None,
        description="Filter by category"
    ),
    limit: int = Query(
        10000,
        ge=1,
        le=50000,
        description="Maximum number of logs to export"
    ),
    current_user: User = Depends(require_admin_access)
):
    """Export audit logs in specified format"""
    try:
        audit_category = AuditCategory(category.value) if category else None
        
        logs = await audit_service.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            category=audit_category,
            limit=limit,
            offset=0
        )
        
        # Log the export action
        audit_service.log(
            action=AuditAction.DATA_EXPORT,
            category=AuditCategory.SYSTEM_ADMINISTRATION,
            level=AuditLevel.INFO,
            description=f"Audit logs exported in {format} format",
            metadata={
                'export_format': format,
                'exported_count': len(logs),
                'date_range': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            }
        )
        
        if format == "json":
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content={
                    'logs': logs,
                    'metadata': {
                        'exported_at': datetime.utcnow().isoformat(),
                        'total_count': len(logs),
                        'format': format
                    }
                },
                headers={
                    'Content-Disposition': f'attachment; filename="audit_logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json"'
                }
            )
        
        elif format == "csv":
            import csv
            import io
            from fastapi.responses import StreamingResponse
            
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    'timestamp', 'action', 'category', 'level', 'user_email',
                    'ip_address', 'resource_type', 'resource_id', 'description',
                    'success', 'error_message', 'duration_ms'
                ]
            )
            
            writer.writeheader()
            for log in logs:
                # Flatten the log for CSV export
                csv_row = {
                    'timestamp': log.get('timestamp'),
                    'action': log.get('action'),
                    'category': log.get('category'),
                    'level': log.get('level'),
                    'user_email': log.get('user_email'),
                    'ip_address': log.get('ip_address'),
                    'resource_type': log.get('resource_type'),
                    'resource_id': log.get('resource_id'),
                    'description': log.get('description'),
                    'success': log.get('success'),
                    'error_message': log.get('error_message'),
                    'duration_ms': log.get('duration_ms')
                }
                writer.writerow(csv_row)
            
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={
                    'Content-Disposition': f'attachment; filename="audit_logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv"'
                }
            )
        
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error exporting audit logs"
        )