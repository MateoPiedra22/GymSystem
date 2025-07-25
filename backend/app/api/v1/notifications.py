from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.auth import get_current_user, require_admin_access
from ...models.user import User
from ...services.notification_service import (
    notification_service, NotificationChannel, NotificationType, NotificationPriority,
    NotificationContent, NotificationRecipient, NotificationRequest
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Pydantic models for requests and responses
class NotificationContentRequest(BaseModel):
    """Request model for notification content"""
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    email_subject: Optional[str] = Field(None, description="Email subject (if different from title)")
    email_template: Optional[str] = Field(None, description="Email template name")
    whatsapp_template: Optional[str] = Field(None, description="WhatsApp template name")
    push_data: Optional[Dict[str, Any]] = Field(None, description="Additional push notification data")
    action_url: Optional[str] = Field(None, description="Action URL for notification")
    action_text: Optional[str] = Field(None, description="Action button text")

class NotificationRecipientRequest(BaseModel):
    """Request model for notification recipient"""
    user_id: int = Field(..., description="User ID")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    preferred_channels: List[NotificationChannel] = Field(default=[], description="Preferred channels")
    timezone: str = Field(default="UTC", description="User timezone")
    language: str = Field(default="en", description="User language")

class SendNotificationRequest(BaseModel):
    """Request model for sending notifications"""
    type: NotificationType = Field(..., description="Notification type")
    recipients: List[NotificationRecipientRequest] = Field(..., description="Notification recipients")
    content: NotificationContentRequest = Field(..., description="Notification content")
    channels: List[NotificationChannel] = Field(..., description="Channels to send through")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="Notification priority")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule notification for later")
    expires_at: Optional[datetime] = Field(None, description="Notification expiry time")
    template_params: Dict[str, Any] = Field(default={}, description="Template parameters")
    
    @validator('recipients')
    def validate_recipients(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one recipient is required')
        return v
    
    @validator('channels')
    def validate_channels(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one channel is required')
        return v

class BulkNotificationRequest(BaseModel):
    """Request model for bulk notifications"""
    user_ids: List[int] = Field(..., description="List of user IDs")
    notification_type: NotificationType = Field(..., description="Notification type")
    content: NotificationContentRequest = Field(..., description="Notification content")
    channels: List[NotificationChannel] = Field(..., description="Channels to send through")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="Notification priority")
    template_params: Dict[str, Any] = Field(default={}, description="Template parameters")
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one user ID is required')
        if len(v) > 1000:
            raise ValueError('Maximum 1000 users allowed per bulk notification')
        return v

class WelcomeNotificationRequest(BaseModel):
    """Request model for welcome notifications"""
    user_id: int = Field(..., description="User ID")

class PaymentReminderRequest(BaseModel):
    """Request model for payment reminder notifications"""
    user_id: int = Field(..., description="User ID")
    amount: float = Field(..., description="Payment amount")
    due_date: datetime = Field(..., description="Payment due date")

class ClassReminderRequest(BaseModel):
    """Request model for class reminder notifications"""
    user_id: int = Field(..., description="User ID")
    class_name: str = Field(..., description="Class name")
    class_time: datetime = Field(..., description="Class time")

class MembershipExpiryRequest(BaseModel):
    """Request model for membership expiry notifications"""
    user_id: int = Field(..., description="User ID")
    expiry_date: datetime = Field(..., description="Membership expiry date")

class NotificationPreferencesRequest(BaseModel):
    """Request model for updating notification preferences"""
    email_enabled: bool = Field(default=True, description="Enable email notifications")
    whatsapp_enabled: bool = Field(default=True, description="Enable WhatsApp notifications")
    push_enabled: bool = Field(default=True, description="Enable push notifications")
    sms_enabled: bool = Field(default=False, description="Enable SMS notifications")
    in_app_enabled: bool = Field(default=True, description="Enable in-app notifications")
    
    welcome_enabled: bool = Field(default=True, description="Enable welcome notifications")
    payment_reminders_enabled: bool = Field(default=True, description="Enable payment reminders")
    class_reminders_enabled: bool = Field(default=True, description="Enable class reminders")
    promotions_enabled: bool = Field(default=True, description="Enable promotion notifications")
    announcements_enabled: bool = Field(default=True, description="Enable announcements")
    security_alerts_enabled: bool = Field(default=True, description="Enable security alerts")
    
    quiet_hours_start: str = Field(default="22:00", description="Quiet hours start time (HH:MM)")
    quiet_hours_end: str = Field(default="08:00", description="Quiet hours end time (HH:MM)")
    timezone: str = Field(default="UTC", description="User timezone")
    max_daily_notifications: int = Field(default=10, description="Maximum daily notifications")
    max_weekly_promotions: int = Field(default=3, description="Maximum weekly promotions")
    
    @validator('quiet_hours_start', 'quiet_hours_end')
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, '%H:%M')
            return v
        except ValueError:
            raise ValueError('Time must be in HH:MM format')

# Response models
class NotificationResponse(BaseModel):
    """Response model for notification sending"""
    total_recipients: int
    channels_used: List[str]
    status: str
    results: Dict[str, Any]
    errors: List[str] = []

class NotificationPreferencesResponse(BaseModel):
    """Response model for notification preferences"""
    email_enabled: bool
    whatsapp_enabled: bool
    push_enabled: bool
    sms_enabled: bool
    in_app_enabled: bool
    welcome_enabled: bool
    payment_reminders_enabled: bool
    class_reminders_enabled: bool
    promotions_enabled: bool
    announcements_enabled: bool
    security_alerts_enabled: bool
    quiet_hours_start: str
    quiet_hours_end: str
    timezone: str
    max_daily_notifications: int
    max_weekly_promotions: int

class NotificationStatisticsResponse(BaseModel):
    """Response model for notification statistics"""
    total_notifications: int
    sent_notifications: int
    delivered_notifications: int
    failed_notifications: int
    success_rate: float
    delivery_rate: float
    channel_statistics: Dict[str, int]
    type_statistics: Dict[str, int]

# API Endpoints
@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a notification through specified channels"""
    try:
        # Convert request to service objects
        recipients = [
            NotificationRecipient(
                user_id=r.user_id,
                email=r.email,
                phone=r.phone,
                preferred_channels=r.preferred_channels,
                timezone=r.timezone,
                language=r.language
            )
            for r in request.recipients
        ]
        
        content = NotificationContent(
            title=request.content.title,
            message=request.content.message,
            email_subject=request.content.email_subject,
            email_template=request.content.email_template,
            whatsapp_template=request.content.whatsapp_template,
            push_data=request.content.push_data,
            action_url=request.content.action_url,
            action_text=request.content.action_text
        )
        
        notification_request = NotificationRequest(
            type=request.type,
            recipients=recipients,
            content=content,
            channels=request.channels,
            priority=request.priority,
            scheduled_at=request.scheduled_at,
            expires_at=request.expires_at,
            template_params=request.template_params
        )
        
        result = await notification_service.send_notification(notification_request)
        
        return NotificationResponse(
            total_recipients=result["total_recipients"],
            channels_used=[c.value for c in request.channels],
            status=result["status"],
            results=result["results"],
            errors=result.get("errors", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

@router.post("/send/bulk", response_model=NotificationResponse)
async def send_bulk_notification(
    request: BulkNotificationRequest,
    current_user: User = Depends(require_admin_access)
):
    """Send bulk notification to multiple users (Admin only)"""
    try:
        # Get users from database
        db = next(get_db())
        users = db.query(User).filter(User.id.in_(request.user_ids)).all()
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No users found with provided IDs"
            )
        
        content = NotificationContent(
            title=request.content.title,
            message=request.content.message,
            email_subject=request.content.email_subject,
            email_template=request.content.email_template,
            whatsapp_template=request.content.whatsapp_template,
            push_data=request.content.push_data,
            action_url=request.content.action_url,
            action_text=request.content.action_text
        )
        
        result = await notification_service.send_bulk_notification(
            users=users,
            notification_type=request.notification_type,
            content=content,
            channels=request.channels,
            priority=request.priority
        )
        
        return NotificationResponse(
            total_recipients=result["total_recipients"],
            channels_used=[c.value for c in request.channels],
            status=result["status"],
            results=result["results"],
            errors=result.get("errors", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send bulk notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk notification: {str(e)}"
        )
    finally:
        db.close()

@router.post("/send/welcome", response_model=NotificationResponse)
async def send_welcome_notification(
    request: WelcomeNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """Send welcome notification to a user"""
    try:
        # Get user from database
        db = next(get_db())
        user = db.query(User).filter(User.id == request.user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        result = await notification_service.send_welcome_notification(user)
        
        return NotificationResponse(
            total_recipients=result["total_recipients"],
            channels_used=result["channels_used"],
            status=result["status"],
            results=result["results"],
            errors=result.get("errors", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send welcome notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send welcome notification: {str(e)}"
        )
    finally:
        db.close()

@router.post("/send/payment-reminder", response_model=NotificationResponse)
async def send_payment_reminder(
    request: PaymentReminderRequest,
    current_user: User = Depends(get_current_user)
):
    """Send payment reminder notification"""
    try:
        # Get user from database
        db = next(get_db())
        user = db.query(User).filter(User.id == request.user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        result = await notification_service.send_payment_reminder(
            user=user,
            amount=request.amount,
            due_date=request.due_date
        )
        
        return NotificationResponse(
            total_recipients=result["total_recipients"],
            channels_used=result["channels_used"],
            status=result["status"],
            results=result["results"],
            errors=result.get("errors", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send payment reminder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send payment reminder: {str(e)}"
        )
    finally:
        db.close()

@router.post("/send/class-reminder", response_model=NotificationResponse)
async def send_class_reminder(
    request: ClassReminderRequest,
    current_user: User = Depends(get_current_user)
):
    """Send class reminder notification"""
    try:
        # Get user from database
        db = next(get_db())
        user = db.query(User).filter(User.id == request.user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        result = await notification_service.send_class_reminder(
            user=user,
            class_name=request.class_name,
            class_time=request.class_time
        )
        
        return NotificationResponse(
            total_recipients=result["total_recipients"],
            channels_used=result["channels_used"],
            status=result["status"],
            results=result["results"],
            errors=result.get("errors", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send class reminder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send class reminder: {str(e)}"
        )
    finally:
        db.close()

@router.post("/send/membership-expiry", response_model=NotificationResponse)
async def send_membership_expiry_notice(
    request: MembershipExpiryRequest,
    current_user: User = Depends(get_current_user)
):
    """Send membership expiry notice"""
    try:
        # Get user from database
        db = next(get_db())
        user = db.query(User).filter(User.id == request.user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        result = await notification_service.send_membership_expiry_notice(
            user=user,
            expiry_date=request.expiry_date
        )
        
        return NotificationResponse(
            total_recipients=result["total_recipients"],
            channels_used=result["channels_used"],
            status=result["status"],
            results=result["results"],
            errors=result.get("errors", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send membership expiry notice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send membership expiry notice: {str(e)}"
        )
    finally:
        db.close()

@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get current user's notification preferences"""
    try:
        preferences = await notification_service.get_user_preferences(current_user.id)
        return NotificationPreferencesResponse(**preferences)
        
    except Exception as e:
        logger.error(f"Failed to get notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )

@router.put("/preferences", response_model=Dict[str, str])
async def update_notification_preferences(
    request: NotificationPreferencesRequest,
    current_user: User = Depends(get_current_user)
):
    """Update current user's notification preferences"""
    try:
        preferences_dict = request.dict()
        success = await notification_service.update_user_preferences(
            current_user.id, preferences_dict
        )
        
        if success:
            return {"message": "Notification preferences updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )

@router.get("/preferences/{user_id}", response_model=NotificationPreferencesResponse)
async def get_user_notification_preferences(
    user_id: int,
    current_user: User = Depends(require_admin_access)
):
    """Get notification preferences for a specific user (Admin only)"""
    try:
        preferences = await notification_service.get_user_preferences(user_id)
        return NotificationPreferencesResponse(**preferences)
        
    except Exception as e:
        logger.error(f"Failed to get user notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user preferences: {str(e)}"
        )

@router.get("/statistics", response_model=NotificationStatisticsResponse)
async def get_notification_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(require_admin_access)
):
    """Get notification statistics (Admin only)"""
    try:
        stats = await notification_service.get_notification_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return NotificationStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get notification statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

@router.get("/channels")
async def get_notification_channels(
    current_user: User = Depends(get_current_user)
):
    """Get available notification channels and types"""
    return {
        "channels": [channel.value for channel in NotificationChannel],
        "types": [notification_type.value for notification_type in NotificationType],
        "priorities": [priority.value for priority in NotificationPriority]
    }

@router.post("/test")
async def send_test_notification(
    channel: NotificationChannel,
    current_user: User = Depends(get_current_user)
):
    """Send a test notification to current user"""
    try:
        recipient = NotificationRecipient(
            user_id=current_user.id,
            email=current_user.email,
            phone=getattr(current_user, 'phone', None)
        )
        
        content = NotificationContent(
            title="🧪 Notificación de prueba",
            message=f"Hola {current_user.first_name}, esta es una notificación de prueba del sistema. ¡Todo funciona correctamente!",
            email_subject="Notificación de prueba - Gimnasio"
        )
        
        request = NotificationRequest(
            type=NotificationType.CUSTOM,
            recipients=[recipient],
            content=content,
            channels=[channel],
            priority=NotificationPriority.NORMAL,
            template_params={"user_name": current_user.first_name}
        )
        
        result = await notification_service.send_notification(request)
        
        return {
            "message": "Test notification sent",
            "channel": channel.value,
            "status": result["status"]
        }
        
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {str(e)}"
        )