from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from ..core.database import Base, get_db
from ..core.config import settings
from .config_service import get_config_service
from .email_service import email_service, EmailType
from .whatsapp_service import whatsapp_service, MessageCategory as WhatsAppCategory
from .push_notification_service import push_notification_service
from ..models.user import User

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """Available notification channels"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"

class NotificationType(Enum):
    """Types of notifications"""
    WELCOME = "welcome"
    PAYMENT_REMINDER = "payment_reminder"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    CLASS_REMINDER = "class_reminder"
    CLASS_CANCELLATION = "class_cancellation"
    MEMBERSHIP_EXPIRY = "membership_expiry"
    MEMBERSHIP_RENEWAL = "membership_renewal"
    PROMOTION = "promotion"
    ANNOUNCEMENT = "announcement"
    SYSTEM_ALERT = "system_alert"
    SECURITY_ALERT = "security_alert"
    BIRTHDAY = "birthday"
    ACHIEVEMENT = "achievement"
    WORKOUT_REMINDER = "workout_reminder"
    CUSTOM = "custom"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class NotificationStatus(Enum):
    """Notification delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

@dataclass
class NotificationTemplate:
    """Notification template configuration"""
    type: NotificationType
    channels: List[NotificationChannel]
    priority: NotificationPriority = NotificationPriority.NORMAL
    delay_minutes: int = 0
    retry_attempts: int = 3
    expiry_hours: int = 24
    personalization: Dict[str, Any] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NotificationContent:
    """Notification content for different channels"""
    title: str
    message: str
    email_subject: Optional[str] = None
    email_template: Optional[str] = None
    whatsapp_template: Optional[str] = None
    push_data: Optional[Dict[str, Any]] = None
    attachments: List[str] = field(default_factory=list)
    action_url: Optional[str] = None
    action_text: Optional[str] = None

@dataclass
class NotificationRecipient:
    """Notification recipient information"""
    user_id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    push_tokens: List[str] = field(default_factory=list)
    preferred_channels: List[NotificationChannel] = field(default_factory=list)
    timezone: str = "UTC"
    language: str = "en"

@dataclass
class NotificationRequest:
    """Complete notification request"""
    type: NotificationType
    recipients: List[NotificationRecipient]
    content: NotificationContent
    channels: List[NotificationChannel]
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    template_params: Dict[str, Any] = field(default_factory=dict)

class NotificationLogModel(Base):
    """Notification log database model"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(20), nullable=False, index=True)
    priority = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    external_id = Column(String(100), nullable=True, index=True)  # ID from external service
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    notification_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotificationPreferenceModel(Base):
    """User notification preferences database model"""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    email_enabled = Column(Boolean, default=True)
    whatsapp_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    in_app_enabled = Column(Boolean, default=True)
    
    # Notification type preferences
    welcome_enabled = Column(Boolean, default=True)
    payment_reminders_enabled = Column(Boolean, default=True)
    class_reminders_enabled = Column(Boolean, default=True)
    promotions_enabled = Column(Boolean, default=True)
    announcements_enabled = Column(Boolean, default=True)
    security_alerts_enabled = Column(Boolean, default=True)
    
    # Timing preferences
    quiet_hours_start = Column(String(5), default="22:00")  # HH:MM format
    quiet_hours_end = Column(String(5), default="08:00")
    timezone = Column(String(50), default="UTC")
    
    # Frequency limits
    max_daily_notifications = Column(Integer, default=10)
    max_weekly_promotions = Column(Integer, default=3)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotificationTemplateModel(Base):
    """Notification template database model"""
    __tablename__ = "notification_template_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Channel configurations
    email_enabled = Column(Boolean, default=True)
    email_subject = Column(String(255), nullable=True)
    email_template = Column(String(100), nullable=True)
    
    whatsapp_enabled = Column(Boolean, default=True)
    whatsapp_template = Column(String(100), nullable=True)
    
    push_enabled = Column(Boolean, default=True)
    push_title = Column(String(255), nullable=True)
    push_body = Column(Text, nullable=True)
    
    # Default settings
    priority = Column(String(20), default="normal")
    delay_minutes = Column(Integer, default=0)
    retry_attempts = Column(Integer, default=3)
    expiry_hours = Column(Integer, default=24)
    
    # Template variables and conditions
    variables = Column(JSON, nullable=True)
    conditions = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotificationService:
    """Unified notification service for all channels"""
    
    def __init__(self):
        self.templates = {}
        self.rate_limits = {
            NotificationChannel.EMAIL: 100,  # per hour
            NotificationChannel.WHATSAPP: 80,  # per second
            NotificationChannel.PUSH: 1000,  # per minute
        }
        self._load_templates()
    
    def _load_templates(self):
        """Load notification templates from database"""
        try:
            db = next(get_db())
            
            templates = db.query(NotificationTemplateModel).filter(
                NotificationTemplateModel.is_active == True
            ).all()
            
            for template in templates:
                self.templates[template.type] = {
                    "name": template.name,
                    "description": template.description,
                    "email_enabled": template.email_enabled,
                    "email_subject": template.email_subject,
                    "email_template": template.email_template,
                    "whatsapp_enabled": template.whatsapp_enabled,
                    "whatsapp_template": template.whatsapp_template,
                    "push_enabled": template.push_enabled,
                    "push_title": template.push_title,
                    "push_body": template.push_body,
                    "priority": template.priority,
                    "delay_minutes": template.delay_minutes,
                    "retry_attempts": template.retry_attempts,
                    "expiry_hours": template.expiry_hours,
                    "variables": template.variables or {},
                    "conditions": template.conditions or {}
                }
            
        except Exception as e:
            logger.error(f"Failed to load notification templates: {e}")
        finally:
            db.close()
    
    async def send_notification(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send notification through specified channels"""
        results = {
            "total_recipients": len(request.recipients),
            "channels_used": request.channels,
            "results": {},
            "errors": []
        }
        
        try:
            # Check if notification should be delayed
            if request.scheduled_at and request.scheduled_at > datetime.utcnow():
                await self._schedule_notification(request)
                results["status"] = "scheduled"
                return results
            
            # Send through each channel
            for channel in request.channels:
                channel_results = await self._send_through_channel(
                    channel, request
                )
                results["results"][channel.value] = channel_results
            
            results["status"] = "sent"
            return results
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            results["errors"].append(str(e))
            results["status"] = "failed"
            return results
    
    async def send_welcome_notification(self, user: User) -> Dict[str, Any]:
        """Send welcome notification to new user"""
        recipient = NotificationRecipient(
            user_id=user.id,
            email=user.email,
            phone=getattr(user, 'phone', None),
            preferred_channels=[NotificationChannel.EMAIL, NotificationChannel.WHATSAPP]
        )
        
        content = NotificationContent(
            title="¡Bienvenido a nuestro gimnasio!",
            message=f"Hola {user.first_name}, bienvenido/a a nuestra comunidad fitness. Estamos emocionados de tenerte con nosotros.",
            email_subject="¡Bienvenido a nuestro gimnasio!",
            email_template="welcome"
        )
        
        request = NotificationRequest(
            type=NotificationType.WELCOME,
            recipients=[recipient],
            content=content,
            channels=[NotificationChannel.EMAIL, NotificationChannel.WHATSAPP],
            priority=NotificationPriority.HIGH,
            template_params={"user_name": user.first_name}
        )
        
        return await self.send_notification(request)
    
    async def send_payment_reminder(self, user: User, amount: float, 
                                  due_date: datetime) -> Dict[str, Any]:
        """Send payment reminder notification"""
        recipient = NotificationRecipient(
            user_id=user.id,
            email=user.email,
            phone=getattr(user, 'phone', None)
        )
        
        content = NotificationContent(
            title="Recordatorio de pago",
            message=f"Hola {user.first_name}, tienes un pago pendiente de ${amount:.2f} con vencimiento el {due_date.strftime('%d/%m/%Y')}.",
            email_subject="Recordatorio de pago - Gimnasio",
            email_template="payment_reminder"
        )
        
        request = NotificationRequest(
            type=NotificationType.PAYMENT_REMINDER,
            recipients=[recipient],
            content=content,
            channels=[NotificationChannel.EMAIL, NotificationChannel.WHATSAPP, NotificationChannel.PUSH],
            priority=NotificationPriority.HIGH,
            template_params={
                "user_name": user.first_name,
                "amount": f"${amount:.2f}",
                "due_date": due_date.strftime('%d/%m/%Y')
            }
        )
        
        return await self.send_notification(request)
    
    async def send_class_reminder(self, user: User, class_name: str, 
                                class_time: datetime) -> Dict[str, Any]:
        """Send class reminder notification"""
        recipient = NotificationRecipient(
            user_id=user.id,
            email=user.email,
            phone=getattr(user, 'phone', None)
        )
        
        content = NotificationContent(
            title="Recordatorio de clase",
            message=f"¡Hola {user.first_name}! Tu clase de {class_name} es hoy a las {class_time.strftime('%H:%M')}.",
            email_subject="Recordatorio de clase - Gimnasio",
            email_template="class_reminder"
        )
        
        request = NotificationRequest(
            type=NotificationType.CLASS_REMINDER,
            recipients=[recipient],
            content=content,
            channels=[NotificationChannel.PUSH, NotificationChannel.WHATSAPP],
            priority=NotificationPriority.NORMAL,
            template_params={
                "user_name": user.first_name,
                "class_name": class_name,
                "class_time": class_time.strftime('%H:%M')
            }
        )
        
        return await self.send_notification(request)
    
    async def send_membership_expiry_notice(self, user: User, 
                                          expiry_date: datetime) -> Dict[str, Any]:
        """Send membership expiry notice"""
        recipient = NotificationRecipient(
            user_id=user.id,
            email=user.email,
            phone=getattr(user, 'phone', None)
        )
        
        days_until_expiry = (expiry_date - datetime.utcnow()).days
        
        content = NotificationContent(
            title="Tu membresía vence pronto",
            message=f"Hola {user.first_name}, tu membresía vence en {days_until_expiry} días ({expiry_date.strftime('%d/%m/%Y')}). ¡Renueva ahora!",
            email_subject="Renovación de membresía - Gimnasio",
            email_template="membership_expiry"
        )
        
        request = NotificationRequest(
            type=NotificationType.MEMBERSHIP_EXPIRY,
            recipients=[recipient],
            content=content,
            channels=[NotificationChannel.EMAIL, NotificationChannel.WHATSAPP, NotificationChannel.PUSH],
            priority=NotificationPriority.HIGH,
            template_params={
                "user_name": user.first_name,
                "expiry_date": expiry_date.strftime('%d/%m/%Y'),
                "days_until_expiry": str(days_until_expiry)
            }
        )
        
        return await self.send_notification(request)
    
    async def send_bulk_notification(self, users: List[User], 
                                   notification_type: NotificationType,
                                   content: NotificationContent,
                                   channels: List[NotificationChannel],
                                   priority: NotificationPriority = NotificationPriority.NORMAL) -> Dict[str, Any]:
        """Send bulk notification to multiple users"""
        recipients = [
            NotificationRecipient(
                user_id=user.id,
                email=user.email,
                phone=getattr(user, 'phone', None)
            )
            for user in users
        ]
        
        request = NotificationRequest(
            type=notification_type,
            recipients=recipients,
            content=content,
            channels=channels,
            priority=priority
        )
        
        return await self.send_notification(request)
    
    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user notification preferences"""
        try:
            db = next(get_db())
            
            preferences = db.query(NotificationPreferenceModel).filter(
                NotificationPreferenceModel.user_id == user_id
            ).first()
            
            if preferences:
                return {
                    "email_enabled": preferences.email_enabled,
                    "whatsapp_enabled": preferences.whatsapp_enabled,
                    "push_enabled": preferences.push_enabled,
                    "sms_enabled": preferences.sms_enabled,
                    "in_app_enabled": preferences.in_app_enabled,
                    "welcome_enabled": preferences.welcome_enabled,
                    "payment_reminders_enabled": preferences.payment_reminders_enabled,
                    "class_reminders_enabled": preferences.class_reminders_enabled,
                    "promotions_enabled": preferences.promotions_enabled,
                    "announcements_enabled": preferences.announcements_enabled,
                    "security_alerts_enabled": preferences.security_alerts_enabled,
                    "quiet_hours_start": preferences.quiet_hours_start,
                    "quiet_hours_end": preferences.quiet_hours_end,
                    "timezone": preferences.timezone,
                    "max_daily_notifications": preferences.max_daily_notifications,
                    "max_weekly_promotions": preferences.max_weekly_promotions
                }
            else:
                # Return default preferences
                return {
                    "email_enabled": True,
                    "whatsapp_enabled": True,
                    "push_enabled": True,
                    "sms_enabled": False,
                    "in_app_enabled": True,
                    "welcome_enabled": True,
                    "payment_reminders_enabled": True,
                    "class_reminders_enabled": True,
                    "promotions_enabled": True,
                    "announcements_enabled": True,
                    "security_alerts_enabled": True,
                    "quiet_hours_start": "22:00",
                    "quiet_hours_end": "08:00",
                    "timezone": "UTC",
                    "max_daily_notifications": 10,
                    "max_weekly_promotions": 3
                }
                
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {}
        finally:
            db.close()
    
    async def update_user_preferences(self, user_id: int, 
                                    preferences: Dict[str, Any]) -> bool:
        """Update user notification preferences"""
        try:
            db = next(get_db())
            
            existing = db.query(NotificationPreferenceModel).filter(
                NotificationPreferenceModel.user_id == user_id
            ).first()
            
            if existing:
                # Update existing preferences
                for key, value in preferences.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                # Create new preferences
                new_preferences = NotificationPreferenceModel(
                    user_id=user_id,
                    **preferences
                )
                db.add(new_preferences)
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
            return False
        finally:
            db.close()
    
    async def get_notification_statistics(self, start_date: Optional[datetime] = None,
                                        end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            db = next(get_db())
            
            # Build query
            query = db.query(NotificationLogModel)
            
            if start_date:
                query = query.filter(NotificationLogModel.created_at >= start_date)
            if end_date:
                query = query.filter(NotificationLogModel.created_at <= end_date)
            
            # Get total counts
            total_notifications = query.count()
            sent_notifications = query.filter(NotificationLogModel.status == NotificationStatus.SENT.value).count()
            delivered_notifications = query.filter(NotificationLogModel.status == NotificationStatus.DELIVERED.value).count()
            failed_notifications = query.filter(NotificationLogModel.status == NotificationStatus.FAILED.value).count()
            
            # Calculate rates
            success_rate = (sent_notifications / total_notifications * 100) if total_notifications > 0 else 0
            delivery_rate = (delivered_notifications / sent_notifications * 100) if sent_notifications > 0 else 0
            
            # Get statistics by channel
            channel_stats = {}
            for channel in NotificationChannel:
                channel_count = query.filter(NotificationLogModel.channel == channel.value).count()
                if channel_count > 0:
                    channel_stats[channel.value] = channel_count
            
            # Get statistics by type
            type_stats = {}
            for notification_type in NotificationType:
                type_count = query.filter(NotificationLogModel.notification_type == notification_type.value).count()
                if type_count > 0:
                    type_stats[notification_type.value] = type_count
            
            return {
                "total_notifications": total_notifications,
                "sent_notifications": sent_notifications,
                "delivered_notifications": delivered_notifications,
                "failed_notifications": failed_notifications,
                "success_rate": round(success_rate, 2),
                "delivery_rate": round(delivery_rate, 2),
                "channel_statistics": channel_stats,
                "type_statistics": type_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification statistics: {e}")
            return {}
        finally:
            db.close()
    
    async def _send_through_channel(self, channel: NotificationChannel, 
                                  request: NotificationRequest) -> Dict[str, Any]:
        """Send notification through specific channel"""
        results = {
            "channel": channel.value,
            "sent": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            for recipient in request.recipients:
                # Check user preferences
                preferences = await self.get_user_preferences(recipient.user_id)
                if not self._should_send_notification(channel, request.type, preferences):
                    continue
                
                try:
                    if channel == NotificationChannel.EMAIL and recipient.email:
                        await self._send_email_notification(recipient, request)
                        results["sent"] += 1
                    
                    elif channel == NotificationChannel.WHATSAPP and recipient.phone:
                        await self._send_whatsapp_notification(recipient, request)
                        results["sent"] += 1
                    
                    elif channel == NotificationChannel.PUSH and recipient.push_tokens:
                        await self._send_push_notification(recipient, request)
                        results["sent"] += 1
                    
                    # Log successful notification
                    await self._log_notification(
                        recipient.user_id, channel, request, NotificationStatus.SENT
                    )
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "user_id": recipient.user_id,
                        "error": str(e)
                    })
                    
                    # Log failed notification
                    await self._log_notification(
                        recipient.user_id, channel, request, NotificationStatus.FAILED, str(e)
                    )
            
        except Exception as e:
            logger.error(f"Failed to send through {channel.value}: {e}")
            results["errors"].append(str(e))
        
        return results
    
    async def _send_email_notification(self, recipient: NotificationRecipient, 
                                     request: NotificationRequest):
        """Send email notification"""
        template_name = request.content.email_template or "default"
        
        await email_service.send_template_email(
            to_email=recipient.email,
            template_name=template_name,
            subject=request.content.email_subject or request.content.title,
            template_data=request.template_params,
            email_type=EmailType.NOTIFICATION
        )
    
    async def _send_whatsapp_notification(self, recipient: NotificationRecipient, 
                                        request: NotificationRequest):
        """Send WhatsApp notification"""
        category = WhatsAppCategory.NOTIFICATION
        if request.type == NotificationType.WELCOME:
            category = WhatsAppCategory.WELCOME
        elif request.type == NotificationType.PAYMENT_REMINDER:
            category = WhatsAppCategory.PAYMENT_REMINDER
        elif request.type == NotificationType.CLASS_REMINDER:
            category = WhatsAppCategory.CLASS_REMINDER
        
        await whatsapp_service.send_text_message(
            to=recipient.phone,
            text=request.content.message,
            category=category
        )
    
    async def _send_push_notification(self, recipient: NotificationRecipient, 
                                    request: NotificationRequest):
        """Send push notification"""
        for token in recipient.push_tokens:
            await push_notification_service.send_notification(
                device_token=token,
                title=request.content.title,
                body=request.content.message,
                data=request.content.push_data or {}
            )
    
    def _should_send_notification(self, channel: NotificationChannel, 
                                notification_type: NotificationType,
                                preferences: Dict[str, Any]) -> bool:
        """Check if notification should be sent based on user preferences"""
        # Check channel preference
        channel_key = f"{channel.value}_enabled"
        if not preferences.get(channel_key, True):
            return False
        
        # Check notification type preference
        type_key = f"{notification_type.value}_enabled"
        if not preferences.get(type_key, True):
            return False
        
        # Check quiet hours (for non-urgent notifications)
        # TODO: Implement quiet hours check
        
        return True
    
    async def _log_notification(self, user_id: int, channel: NotificationChannel,
                              request: NotificationRequest, status: NotificationStatus,
                              error_message: Optional[str] = None):
        """Log notification to database"""
        try:
            db = next(get_db())
            
            log_entry = NotificationLogModel(
                user_id=user_id,
                notification_type=request.type.value,
                channel=channel.value,
                priority=request.priority.value,
                status=status.value,
                title=request.content.title,
                content=request.content.message,
                error_message=error_message,
                scheduled_at=request.scheduled_at,
                expires_at=request.expires_at,
                notification_metadata=request.metadata
            )
            
            if status == NotificationStatus.SENT:
                log_entry.sent_at = datetime.utcnow()
            
            db.add(log_entry)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
        finally:
            db.close()
    
    async def _schedule_notification(self, request: NotificationRequest):
        """Schedule notification for later delivery"""
        # TODO: Implement notification scheduling
        # This could use Celery, APScheduler, or similar
        pass

# Global notification service instance
notification_service = NotificationService()