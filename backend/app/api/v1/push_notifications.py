from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.auth import get_current_user, require_admin_access
from ...models.user import User
from ...services.push_notification_service import (
    push_notification_service,
    PushNotificationPayload,
    DeviceType,
    PushProvider,
    NotificationPriority
)
from pydantic import BaseModel, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/push-notifications", tags=["push-notifications"])

# Pydantic models for request/response
class DeviceTypeEnum(str, Enum):
    """Device type enum for API"""
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    DESKTOP = "desktop"

class PushProviderEnum(str, Enum):
    """Push provider enum for API"""
    FCM = "fcm"
    APNS = "apns"
    WEB_PUSH = "web_push"
    EXPO = "expo"

class NotificationPriorityEnum(str, Enum):
    """Notification priority enum for API"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class DeviceRegistrationRequest(BaseModel):
    """Request model for device registration"""
    token: str = Field(..., description="Device token for push notifications")
    device_type: DeviceTypeEnum = Field(..., description="Type of device")
    provider: PushProviderEnum = Field(..., description="Push notification provider")
    app_version: Optional[str] = Field(None, description="Application version")
    os_version: Optional[str] = Field(None, description="Operating system version")
    device_model: Optional[str] = Field(None, description="Device model")

class DeviceUnregistrationRequest(BaseModel):
    """Request model for device unregistration"""
    token: str = Field(..., description="Device token to unregister")

class PushNotificationRequest(BaseModel):
    """Request model for sending push notifications"""
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data payload")
    icon: Optional[str] = Field(None, description="Notification icon URL")
    image: Optional[str] = Field(None, description="Notification image URL")
    badge: Optional[int] = Field(None, description="Badge count")
    sound: Optional[str] = Field(None, description="Notification sound")
    click_action: Optional[str] = Field(None, description="Action when notification is clicked")
    tag: Optional[str] = Field(None, description="Notification tag")
    priority: NotificationPriorityEnum = Field(NotificationPriorityEnum.NORMAL, description="Notification priority")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")
    collapse_key: Optional[str] = Field(None, description="Collapse key for grouping")
    device_types: Optional[List[DeviceTypeEnum]] = Field(None, description="Target device types")

class BulkNotificationRequest(BaseModel):
    """Request model for bulk push notifications"""
    user_ids: List[int] = Field(..., description="List of user IDs to send notifications to")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data payload")
    icon: Optional[str] = Field(None, description="Notification icon URL")
    image: Optional[str] = Field(None, description="Notification image URL")
    priority: NotificationPriorityEnum = Field(NotificationPriorityEnum.NORMAL, description="Notification priority")
    device_types: Optional[List[DeviceTypeEnum]] = Field(None, description="Target device types")

class DeviceResponse(BaseModel):
    """Response model for device information"""
    id: int
    device_type: str
    provider: str
    app_version: Optional[str]
    os_version: Optional[str]
    device_model: Optional[str]
    created_at: str
    last_used: Optional[str]

class NotificationResponse(BaseModel):
    """Response model for notification sending"""
    success: bool
    sent_count: int
    failed_count: Optional[int] = None
    message: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None

class NotificationStatisticsResponse(BaseModel):
    """Response model for notification statistics"""
    total_sent: int
    successful: int
    failed: int
    delivered: int
    clicked: int
    success_rate: float
    delivery_rate: float
    click_rate: float
    provider_stats: Dict[str, Dict[str, int]]
    device_stats: Dict[str, int]
    active_devices: int

@router.post(
    "/devices/register",
    summary="Register device for push notifications",
    description="Register a device to receive push notifications for the current user."
)
async def register_device(
    request: DeviceRegistrationRequest,
    current_user: User = Depends(get_current_user)
):
    """Register a device for push notifications"""
    try:
        # Convert enum values to service enums
        device_type = DeviceType(request.device_type.value)
        provider = PushProvider(request.provider.value)
        
        success = await push_notification_service.register_device(
            user_id=current_user.id,
            token=request.token,
            device_type=device_type,
            provider=provider,
            app_version=request.app_version,
            os_version=request.os_version,
            device_model=request.device_model
        )
        
        if success:
            return {
                "success": True,
                "message": "Device registered successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to register device"
            )
        
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error registering device"
        )

@router.post(
    "/devices/unregister",
    summary="Unregister device from push notifications",
    description="Unregister a device from receiving push notifications."
)
async def unregister_device(
    request: DeviceUnregistrationRequest,
    current_user: User = Depends(get_current_user)
):
    """Unregister a device from push notifications"""
    try:
        success = await push_notification_service.unregister_device(
            user_id=current_user.id,
            token=request.token
        )
        
        if success:
            return {
                "success": True,
                "message": "Device unregistered successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not found"
            )
        
    except Exception as e:
        logger.error(f"Error unregistering device: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error unregistering device"
        )

@router.get(
    "/devices",
    response_model=List[DeviceResponse],
    summary="Get user's registered devices",
    description="Get list of devices registered for push notifications for the current user."
)
async def get_user_devices(
    current_user: User = Depends(get_current_user)
):
    """Get user's registered devices"""
    try:
        devices = await push_notification_service.get_user_devices(current_user.id)
        return devices
        
    except Exception as e:
        logger.error(f"Error getting user devices: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving devices"
        )

@router.post(
    "/send",
    response_model=NotificationResponse,
    summary="Send push notification to current user",
    description="Send a push notification to the current user's devices."
)
async def send_notification_to_self(
    request: PushNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """Send push notification to current user"""
    try:
        # Convert enum values
        priority = NotificationPriority(request.priority.value)
        device_types = [DeviceType(dt.value) for dt in request.device_types] if request.device_types else None
        
        # Create payload
        payload = PushNotificationPayload(
            title=request.title,
            body=request.body,
            data=request.data,
            icon=request.icon,
            image=request.image,
            badge=request.badge,
            sound=request.sound,
            click_action=request.click_action,
            tag=request.tag,
            priority=priority,
            ttl=request.ttl,
            collapse_key=request.collapse_key
        )
        
        result = await push_notification_service.send_notification(
            user_id=current_user.id,
            payload=payload,
            device_types=device_types
        )
        
        return NotificationResponse(
            success=result["success"],
            sent_count=result.get("sent_count", 0),
            failed_count=result.get("failed_count", 0),
            message="Notification sent successfully" if result["success"] else result.get("error"),
            results=result.get("results")
        )
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error sending notification"
        )

@router.post(
    "/send/{user_id}",
    response_model=NotificationResponse,
    summary="Send push notification to specific user",
    description="Send a push notification to a specific user. Requires admin privileges."
)
async def send_notification_to_user(
    user_id: int = Path(..., description="Target user ID"),
    request: PushNotificationRequest = ...,
    current_user: User = Depends(require_admin_access)
):
    """Send push notification to specific user (admin only)"""
    try:
        # Convert enum values
        priority = NotificationPriority(request.priority.value)
        device_types = [DeviceType(dt.value) for dt in request.device_types] if request.device_types else None
        
        # Create payload
        payload = PushNotificationPayload(
            title=request.title,
            body=request.body,
            data=request.data,
            icon=request.icon,
            image=request.image,
            badge=request.badge,
            sound=request.sound,
            click_action=request.click_action,
            tag=request.tag,
            priority=priority,
            ttl=request.ttl,
            collapse_key=request.collapse_key
        )
        
        result = await push_notification_service.send_notification(
            user_id=user_id,
            payload=payload,
            device_types=device_types
        )
        
        return NotificationResponse(
            success=result["success"],
            sent_count=result.get("sent_count", 0),
            failed_count=result.get("failed_count", 0),
            message="Notification sent successfully" if result["success"] else result.get("error"),
            results=result.get("results")
        )
        
    except Exception as e:
        logger.error(f"Error sending notification to user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error sending notification"
        )

@router.post(
    "/send/bulk",
    response_model=NotificationResponse,
    summary="Send bulk push notifications",
    description="Send push notifications to multiple users. Requires admin privileges."
)
async def send_bulk_notifications(
    request: BulkNotificationRequest,
    current_user: User = Depends(require_admin_access)
):
    """Send bulk push notifications (admin only)"""
    try:
        # Validate user count
        if len(request.user_ids) > 10000:
            raise HTTPException(
                status_code=400,
                detail="Cannot send to more than 10,000 users at once"
            )
        
        # Convert enum values
        priority = NotificationPriority(request.priority.value)
        device_types = [DeviceType(dt.value) for dt in request.device_types] if request.device_types else None
        
        # Create payload
        payload = PushNotificationPayload(
            title=request.title,
            body=request.body,
            data=request.data,
            icon=request.icon,
            image=request.image,
            priority=priority
        )
        
        result = await push_notification_service.send_bulk_notifications(
            user_ids=request.user_ids,
            payload=payload,
            device_types=device_types
        )
        
        return NotificationResponse(
            success=result["success"],
            sent_count=result.get("total_sent", 0),
            failed_count=result.get("total_failed", 0),
            message=f"Bulk notification sent to {result.get('total_users', 0)} users",
            results=result.get("results")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending bulk notifications: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error sending bulk notifications"
        )

@router.get(
    "/statistics",
    response_model=NotificationStatisticsResponse,
    summary="Get push notification statistics",
    description="Get comprehensive push notification statistics. Requires admin privileges."
)
async def get_notification_statistics(
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
    """Get push notification statistics"""
    try:
        stats = await push_notification_service.get_notification_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return NotificationStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting notification statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving statistics"
        )

@router.post(
    "/test",
    summary="Send test notification",
    description="Send a test push notification to the current user's devices."
)
async def send_test_notification(
    device_types: Optional[List[DeviceTypeEnum]] = Query(
        None,
        description="Target device types for test"
    ),
    current_user: User = Depends(get_current_user)
):
    """Send test notification to current user"""
    try:
        # Convert enum values
        target_device_types = [DeviceType(dt.value) for dt in device_types] if device_types else None
        
        # Create test payload
        payload = PushNotificationPayload(
            title="Test Notification",
            body=f"Hello {current_user.first_name or current_user.email}! This is a test notification.",
            data={
                "type": "test",
                "timestamp": datetime.utcnow().isoformat()
            },
            priority=NotificationPriority.NORMAL,
            icon="/static/icons/test.png"
        )
        
        result = await push_notification_service.send_notification(
            user_id=current_user.id,
            payload=payload,
            device_types=target_device_types
        )
        
        return {
            "success": result["success"],
            "message": "Test notification sent" if result["success"] else "Failed to send test notification",
            "sent_count": result.get("sent_count", 0),
            "failed_count": result.get("failed_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error sending test notification"
        )

@router.delete(
    "/devices/cleanup",
    summary="Clean up inactive devices",
    description="Remove inactive devices from push notification registry. Requires admin privileges."
)
async def cleanup_inactive_devices(
    days_inactive: int = Query(
        30,
        ge=1,
        le=365,
        description="Number of days of inactivity before cleanup"
    ),
    current_user: User = Depends(require_admin_access)
):
    """Clean up inactive devices"""
    try:
        cleaned_count = await push_notification_service.cleanup_inactive_devices(
            days_inactive=days_inactive
        )
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} inactive devices",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up devices: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error cleaning up devices"
        )

@router.get(
    "/providers",
    summary="Get available push providers",
    description="Get list of configured push notification providers."
)
async def get_push_providers(
    current_user: User = Depends(get_current_user)
):
    """Get available push notification providers"""
    try:
        providers = []
        
        # Check which providers are configured
        if push_notification_service.fcm_service:
            providers.append({
                "provider": "fcm",
                "name": "Firebase Cloud Messaging",
                "supported_platforms": ["android", "web"]
            })
        
        if push_notification_service.web_push_service:
            providers.append({
                "provider": "web_push",
                "name": "Web Push Protocol",
                "supported_platforms": ["web", "desktop"]
            })
        
        if push_notification_service.expo_service:
            providers.append({
                "provider": "expo",
                "name": "Expo Push Notifications",
                "supported_platforms": ["android", "ios"]
            })
        
        return {
            "providers": providers,
            "total_count": len(providers)
        }
        
    except Exception as e:
        logger.error(f"Error getting push providers: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving push providers"
        )

@router.get(
    "/templates",
    summary="Get notification templates",
    description="Get predefined notification templates for common use cases."
)
async def get_notification_templates(
    current_user: User = Depends(get_current_user)
):
    """Get notification templates"""
    try:
        templates = [
            {
                "id": "payment_reminder",
                "name": "Payment Reminder",
                "title": "Payment Reminder",
                "body": "Your payment of ${{amount}} is due on {{due_date}}",
                "icon": "/static/icons/payment.png",
                "priority": "high",
                "click_action": "/payments",
                "variables": ["amount", "due_date"]
            },
            {
                "id": "class_reminder",
                "name": "Class Reminder",
                "title": "Class Reminder",
                "body": "Your {{class_name}} class starts at {{start_time}}",
                "icon": "/static/icons/class.png",
                "priority": "normal",
                "click_action": "/classes",
                "variables": ["class_name", "start_time"]
            },
            {
                "id": "membership_expiry",
                "name": "Membership Expiry",
                "title": "Membership Expiring",
                "body": "Your membership expires on {{expiry_date}}",
                "icon": "/static/icons/membership.png",
                "priority": "high",
                "click_action": "/membership",
                "variables": ["expiry_date"]
            },
            {
                "id": "welcome",
                "name": "Welcome Message",
                "title": "Welcome to Our Gym!",
                "body": "Welcome {{name}}! We're excited to have you join our fitness community.",
                "icon": "/static/icons/welcome.png",
                "priority": "normal",
                "click_action": "/dashboard",
                "variables": ["name"]
            },
            {
                "id": "workout_complete",
                "name": "Workout Complete",
                "title": "Great Job!",
                "body": "You've completed your {{workout_name}} workout. Keep up the great work!",
                "icon": "/static/icons/workout.png",
                "priority": "normal",
                "click_action": "/workouts",
                "variables": ["workout_name"]
            },
            {
                "id": "goal_achieved",
                "name": "Goal Achieved",
                "title": "Congratulations!",
                "body": "You've achieved your goal: {{goal_name}}. Time to set a new challenge!",
                "icon": "/static/icons/achievement.png",
                "priority": "normal",
                "click_action": "/goals",
                "variables": ["goal_name"]
            }
        ]
        
        return {
            "templates": templates,
            "total_count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error getting notification templates: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving notification templates"
        )