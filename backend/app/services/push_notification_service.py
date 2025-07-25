from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import logging
import asyncio
import aiohttp
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from ..core.database import get_db, Base
from ..models.user import User
import uuid
from collections import defaultdict
import os
from cryptography.fernet import Fernet
import base64
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PushProvider(Enum):
    """Push notification providers"""
    FCM = "fcm"  # Firebase Cloud Messaging
    APNS = "apns"  # Apple Push Notification Service
    WEB_PUSH = "web_push"  # Web Push Protocol
    EXPO = "expo"  # Expo Push Notifications

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class DeviceType(Enum):
    """Device types for push notifications"""
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    DESKTOP = "desktop"

@dataclass
class PushNotificationPayload:
    """Push notification payload structure"""
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    image: Optional[str] = None
    badge: Optional[int] = None
    sound: Optional[str] = None
    click_action: Optional[str] = None
    tag: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    ttl: Optional[int] = None  # Time to live in seconds
    collapse_key: Optional[str] = None

@dataclass
class DeviceToken:
    """Device token information"""
    token: str
    device_type: DeviceType
    provider: PushProvider
    user_id: int
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    device_model: Optional[str] = None
    is_active: bool = True
    last_used: Optional[datetime] = None

class PushDeviceModel(Base):
    """Database model for push notification devices"""
    __tablename__ = "push_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(Text, nullable=False, index=True)
    device_type = Column(String(20), nullable=False)
    provider = Column(String(20), nullable=False)
    app_version = Column(String(50), nullable=True)
    os_version = Column(String(50), nullable=True)
    device_model = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    
class PushNotificationLogModel(Base):
    """Database model for push notification logs"""
    __tablename__ = "push_notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("push_devices.id"), nullable=True)
    provider = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    payload = Column(Text, nullable=True)  # JSON
    status = Column(String(20), nullable=False, index=True)  # sent, delivered, failed, clicked
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    delivered_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    
class FCMService:
    """Firebase Cloud Messaging service"""
    
    def __init__(self, server_key: str, project_id: Optional[str] = None):
        self.server_key = server_key
        self.project_id = project_id
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.fcm_v1_url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send" if project_id else None
    
    async def send_notification(
        self,
        token: str,
        payload: PushNotificationPayload
    ) -> Dict[str, Any]:
        """Send FCM notification"""
        try:
            headers = {
                "Authorization": f"key={self.server_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare FCM payload
            fcm_payload = {
                "to": token,
                "notification": {
                    "title": payload.title,
                    "body": payload.body
                },
                "data": payload.data or {},
                "priority": "high" if payload.priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL] else "normal"
            }
            
            # Add optional fields
            if payload.icon:
                fcm_payload["notification"]["icon"] = payload.icon
            if payload.image:
                fcm_payload["notification"]["image"] = payload.image
            if payload.sound:
                fcm_payload["notification"]["sound"] = payload.sound
            if payload.click_action:
                fcm_payload["notification"]["click_action"] = payload.click_action
            if payload.tag:
                fcm_payload["notification"]["tag"] = payload.tag
            if payload.ttl:
                fcm_payload["time_to_live"] = payload.ttl
            if payload.collapse_key:
                fcm_payload["collapse_key"] = payload.collapse_key
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.fcm_url,
                    headers=headers,
                    json=fcm_payload
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get("success", 0) > 0:
                        return {
                            "success": True,
                            "message_id": result.get("results", [{}])[0].get("message_id"),
                            "response": result
                        }
                    else:
                        error = result.get("results", [{}])[0].get("error", "Unknown error")
                        return {
                            "success": False,
                            "error": error,
                            "response": result
                        }
        
        except Exception as e:
            logger.error(f"FCM notification error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_batch_notifications(
        self,
        tokens: List[str],
        payload: PushNotificationPayload
    ) -> Dict[str, Any]:
        """Send batch FCM notifications"""
        try:
            headers = {
                "Authorization": f"key={self.server_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare FCM payload for batch
            fcm_payload = {
                "registration_ids": tokens,
                "notification": {
                    "title": payload.title,
                    "body": payload.body
                },
                "data": payload.data or {},
                "priority": "high" if payload.priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL] else "normal"
            }
            
            # Add optional fields
            if payload.icon:
                fcm_payload["notification"]["icon"] = payload.icon
            if payload.image:
                fcm_payload["notification"]["image"] = payload.image
            if payload.sound:
                fcm_payload["notification"]["sound"] = payload.sound
            if payload.ttl:
                fcm_payload["time_to_live"] = payload.ttl
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.fcm_url,
                    headers=headers,
                    json=fcm_payload
                ) as response:
                    result = await response.json()
                    
                    return {
                        "success": response.status == 200,
                        "response": result,
                        "success_count": result.get("success", 0),
                        "failure_count": result.get("failure", 0)
                    }
        
        except Exception as e:
            logger.error(f"FCM batch notification error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

class WebPushService:
    """Web Push Protocol service"""
    
    def __init__(self, vapid_private_key: str, vapid_public_key: str, vapid_subject: str):
        self.vapid_private_key = vapid_private_key
        self.vapid_public_key = vapid_public_key
        self.vapid_subject = vapid_subject
    
    async def send_notification(
        self,
        subscription: Dict[str, Any],
        payload: PushNotificationPayload
    ) -> Dict[str, Any]:
        """Send web push notification"""
        try:
            from pywebpush import webpush, WebPushException
            
            # Prepare web push payload
            web_payload = {
                "title": payload.title,
                "body": payload.body,
                "data": payload.data or {},
                "requireInteraction": payload.priority == NotificationPriority.CRITICAL
            }
            
            # Add optional fields
            if payload.icon:
                web_payload["icon"] = payload.icon
            if payload.image:
                web_payload["image"] = payload.image
            if payload.badge:
                web_payload["badge"] = payload.badge
            if payload.tag:
                web_payload["tag"] = payload.tag
            if payload.click_action:
                web_payload["actions"] = [{
                    "action": "open",
                    "title": "Open",
                    "url": payload.click_action
                }]
            
            # Send notification
            response = webpush(
                subscription_info=subscription,
                data=json.dumps(web_payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": self.vapid_subject
                },
                ttl=payload.ttl or 86400  # 24 hours default
            )
            
            return {
                "success": True,
                "response": response
            }
        
        except WebPushException as e:
            logger.error(f"Web push notification error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Web push notification error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

class ExpoService:
    """Expo Push Notifications service"""
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.expo_url = "https://exp.host/--/api/v2/push/send"
    
    async def send_notification(
        self,
        token: str,
        payload: PushNotificationPayload
    ) -> Dict[str, Any]:
        """Send Expo notification"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            
            # Prepare Expo payload
            expo_payload = {
                "to": token,
                "title": payload.title,
                "body": payload.body,
                "data": payload.data or {},
                "priority": "high" if payload.priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL] else "normal"
            }
            
            # Add optional fields
            if payload.sound:
                expo_payload["sound"] = payload.sound
            if payload.badge:
                expo_payload["badge"] = payload.badge
            if payload.ttl:
                expo_payload["ttl"] = payload.ttl
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.expo_url,
                    headers=headers,
                    json=expo_payload
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get("data", {}).get("status") == "ok":
                        return {
                            "success": True,
                            "ticket_id": result.get("data", {}).get("id"),
                            "response": result
                        }
                    else:
                        error = result.get("data", {}).get("message", "Unknown error")
                        return {
                            "success": False,
                            "error": error,
                            "response": result
                        }
        
        except Exception as e:
            logger.error(f"Expo notification error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

class PushNotificationService:
    """Comprehensive push notification service"""
    
    def __init__(self):
        # Initialize providers
        self.fcm_service = None
        self.web_push_service = None
        self.expo_service = None
        
        # Configuration
        self.max_batch_size = 1000
        self.retry_attempts = 3
        self.retry_delay = 5  # seconds
        
        # Statistics
        self.stats = {
            "sent": 0,
            "delivered": 0,
            "failed": 0,
            "clicked": 0
        }
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize push notification providers"""
        try:
            # FCM configuration
            fcm_server_key = os.getenv("FCM_SERVER_KEY")
            fcm_project_id = os.getenv("FCM_PROJECT_ID")
            if fcm_server_key:
                self.fcm_service = FCMService(fcm_server_key, fcm_project_id)
            
            # Web Push configuration
            vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
            vapid_public_key = os.getenv("VAPID_PUBLIC_KEY")
            vapid_subject = os.getenv("VAPID_SUBJECT")
            if all([vapid_private_key, vapid_public_key, vapid_subject]):
                self.web_push_service = WebPushService(
                    vapid_private_key, vapid_public_key, vapid_subject
                )
            
            # Expo configuration
            expo_access_token = os.getenv("EXPO_ACCESS_TOKEN")
            self.expo_service = ExpoService(expo_access_token)
            
        except Exception as e:
            logger.error(f"Error initializing push providers: {e}")
    
    async def register_device(
        self,
        user_id: int,
        token: str,
        device_type: DeviceType,
        provider: PushProvider,
        app_version: Optional[str] = None,
        os_version: Optional[str] = None,
        device_model: Optional[str] = None
    ) -> bool:
        """Register a device for push notifications"""
        try:
            db = next(get_db())
            
            # Check if device already exists
            existing_device = db.query(PushDeviceModel).filter(
                PushDeviceModel.user_id == user_id,
                PushDeviceModel.token == token
            ).first()
            
            if existing_device:
                # Update existing device
                existing_device.device_type = device_type.value
                existing_device.provider = provider.value
                existing_device.app_version = app_version
                existing_device.os_version = os_version
                existing_device.device_model = device_model
                existing_device.is_active = True
                existing_device.last_used = datetime.utcnow()
            else:
                # Create new device
                new_device = PushDeviceModel(
                    user_id=user_id,
                    token=token,
                    device_type=device_type.value,
                    provider=provider.value,
                    app_version=app_version,
                    os_version=os_version,
                    device_model=device_model,
                    is_active=True,
                    last_used=datetime.utcnow()
                )
                db.add(new_device)
            
            db.commit()
            logger.info(f"Device registered for user {user_id}: {device_type.value} - {provider.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            return False
    
    async def unregister_device(self, user_id: int, token: str) -> bool:
        """Unregister a device from push notifications"""
        try:
            db = next(get_db())
            
            device = db.query(PushDeviceModel).filter(
                PushDeviceModel.user_id == user_id,
                PushDeviceModel.token == token
            ).first()
            
            if device:
                device.is_active = False
                db.commit()
                logger.info(f"Device unregistered for user {user_id}: {token}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error unregistering device: {e}")
            return False
    
    async def send_notification(
        self,
        user_id: int,
        payload: PushNotificationPayload,
        device_types: Optional[List[DeviceType]] = None
    ) -> Dict[str, Any]:
        """Send push notification to user's devices"""
        try:
            db = next(get_db())
            
            # Get user's active devices
            query = db.query(PushDeviceModel).filter(
                PushDeviceModel.user_id == user_id,
                PushDeviceModel.is_active == True
            )
            
            if device_types:
                device_type_values = [dt.value for dt in device_types]
                query = query.filter(PushDeviceModel.device_type.in_(device_type_values))
            
            devices = query.all()
            
            if not devices:
                return {
                    "success": False,
                    "error": "No active devices found for user",
                    "sent_count": 0
                }
            
            # Group devices by provider
            devices_by_provider = defaultdict(list)
            for device in devices:
                devices_by_provider[device.provider].append(device)
            
            results = []
            total_sent = 0
            total_failed = 0
            
            # Send notifications for each provider
            for provider, provider_devices in devices_by_provider.items():
                provider_results = await self._send_to_provider(
                    provider, provider_devices, payload
                )
                results.extend(provider_results)
                
                # Count results
                for result in provider_results:
                    if result["success"]:
                        total_sent += 1
                    else:
                        total_failed += 1
            
            # Update statistics
            self.stats["sent"] += total_sent
            self.stats["failed"] += total_failed
            
            return {
                "success": total_sent > 0,
                "sent_count": total_sent,
                "failed_count": total_failed,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {
                "success": False,
                "error": str(e),
                "sent_count": 0
            }
    
    async def send_bulk_notifications(
        self,
        user_ids: List[int],
        payload: PushNotificationPayload,
        device_types: Optional[List[DeviceType]] = None
    ) -> Dict[str, Any]:
        """Send push notifications to multiple users"""
        try:
            results = []
            total_sent = 0
            total_failed = 0
            
            # Process users in batches
            batch_size = 100
            for i in range(0, len(user_ids), batch_size):
                batch_user_ids = user_ids[i:i + batch_size]
                
                # Send notifications concurrently for this batch
                batch_tasks = [
                    self.send_notification(user_id, payload, device_types)
                    for user_id in batch_user_ids
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for user_id, result in zip(batch_user_ids, batch_results):
                    if isinstance(result, Exception):
                        results.append({
                            "user_id": user_id,
                            "success": False,
                            "error": str(result)
                        })
                        total_failed += 1
                    else:
                        results.append({
                            "user_id": user_id,
                            **result
                        })
                        total_sent += result.get("sent_count", 0)
                        total_failed += result.get("failed_count", 0)
            
            return {
                "success": total_sent > 0,
                "total_users": len(user_ids),
                "total_sent": total_sent,
                "total_failed": total_failed,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error sending bulk notifications: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_to_provider(
        self,
        provider: str,
        devices: List[PushDeviceModel],
        payload: PushNotificationPayload
    ) -> List[Dict[str, Any]]:
        """Send notifications to devices of a specific provider"""
        results = []
        
        try:
            if provider == PushProvider.FCM.value and self.fcm_service:
                # Send FCM notifications
                for device in devices:
                    result = await self._send_with_retry(
                        self.fcm_service.send_notification,
                        device.token,
                        payload
                    )
                    
                    # Log notification
                    await self._log_notification(
                        device, payload, result
                    )
                    
                    results.append({
                        "device_id": device.id,
                        "token": device.token[:10] + "...",  # Truncate for security
                        "provider": provider,
                        **result
                    })
            
            elif provider == PushProvider.WEB_PUSH.value and self.web_push_service:
                # Send Web Push notifications
                for device in devices:
                    # Parse subscription from token (assuming it's JSON)
                    try:
                        subscription = json.loads(device.token)
                        result = await self._send_with_retry(
                            self.web_push_service.send_notification,
                            subscription,
                            payload
                        )
                    except json.JSONDecodeError:
                        result = {
                            "success": False,
                            "error": "Invalid subscription format"
                        }
                    
                    # Log notification
                    await self._log_notification(
                        device, payload, result
                    )
                    
                    results.append({
                        "device_id": device.id,
                        "token": "web_subscription",
                        "provider": provider,
                        **result
                    })
            
            elif provider == PushProvider.EXPO.value and self.expo_service:
                # Send Expo notifications
                for device in devices:
                    result = await self._send_with_retry(
                        self.expo_service.send_notification,
                        device.token,
                        payload
                    )
                    
                    # Log notification
                    await self._log_notification(
                        device, payload, result
                    )
                    
                    results.append({
                        "device_id": device.id,
                        "token": device.token[:10] + "...",
                        "provider": provider,
                        **result
                    })
            
            else:
                # Provider not configured or supported
                for device in devices:
                    results.append({
                        "device_id": device.id,
                        "token": device.token[:10] + "...",
                        "provider": provider,
                        "success": False,
                        "error": f"Provider {provider} not configured"
                    })
        
        except Exception as e:
            logger.error(f"Error sending to provider {provider}: {e}")
            for device in devices:
                results.append({
                    "device_id": device.id,
                    "token": device.token[:10] + "...",
                    "provider": provider,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _send_with_retry(
        self,
        send_func,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Send notification with retry logic"""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                result = await send_func(*args, **kwargs)
                if result.get("success"):
                    return result
                
                last_error = result.get("error", "Unknown error")
                
                # Don't retry for certain errors
                if "invalid" in last_error.lower() or "not found" in last_error.lower():
                    break
                
            except Exception as e:
                last_error = str(e)
            
            # Wait before retry
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        return {
            "success": False,
            "error": last_error,
            "attempts": self.retry_attempts
        }
    
    async def _log_notification(
        self,
        device: PushDeviceModel,
        payload: PushNotificationPayload,
        result: Dict[str, Any]
    ):
        """Log notification attempt"""
        try:
            db = next(get_db())
            
            log_entry = PushNotificationLogModel(
                user_id=device.user_id,
                device_id=device.id,
                provider=device.provider,
                title=payload.title,
                body=payload.body,
                payload=json.dumps(asdict(payload)),
                status="sent" if result.get("success") else "failed",
                error_message=result.get("error"),
                sent_at=datetime.utcnow()
            )
            
            db.add(log_entry)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
    
    async def get_user_devices(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's registered devices"""
        try:
            db = next(get_db())
            
            devices = db.query(PushDeviceModel).filter(
                PushDeviceModel.user_id == user_id,
                PushDeviceModel.is_active == True
            ).all()
            
            return [
                {
                    "id": device.id,
                    "device_type": device.device_type,
                    "provider": device.provider,
                    "app_version": device.app_version,
                    "os_version": device.os_version,
                    "device_model": device.device_model,
                    "created_at": device.created_at.isoformat(),
                    "last_used": device.last_used.isoformat() if device.last_used else None
                }
                for device in devices
            ]
            
        except Exception as e:
            logger.error(f"Error getting user devices: {e}")
            return []
    
    async def get_notification_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get push notification statistics"""
        try:
            db = next(get_db())
            
            query = db.query(PushNotificationLogModel)
            
            if start_date:
                query = query.filter(PushNotificationLogModel.sent_at >= start_date)
            if end_date:
                query = query.filter(PushNotificationLogModel.sent_at <= end_date)
            
            logs = query.all()
            
            # Calculate statistics
            total_sent = len(logs)
            successful = len([log for log in logs if log.status == "sent"])
            failed = len([log for log in logs if log.status == "failed"])
            delivered = len([log for log in logs if log.delivered_at is not None])
            clicked = len([log for log in logs if log.clicked_at is not None])
            
            # Group by provider
            provider_stats = defaultdict(lambda: {"sent": 0, "failed": 0})
            for log in logs:
                if log.status == "sent":
                    provider_stats[log.provider]["sent"] += 1
                else:
                    provider_stats[log.provider]["failed"] += 1
            
            # Group by device type
            device_stats = defaultdict(int)
            device_query = db.query(PushDeviceModel).filter(
                PushDeviceModel.is_active == True
            )
            devices = device_query.all()
            for device in devices:
                device_stats[device.device_type] += 1
            
            return {
                "total_sent": total_sent,
                "successful": successful,
                "failed": failed,
                "delivered": delivered,
                "clicked": clicked,
                "success_rate": (successful / total_sent * 100) if total_sent > 0 else 0,
                "delivery_rate": (delivered / successful * 100) if successful > 0 else 0,
                "click_rate": (clicked / delivered * 100) if delivered > 0 else 0,
                "provider_stats": dict(provider_stats),
                "device_stats": dict(device_stats),
                "active_devices": len(devices)
            }
            
        except Exception as e:
            logger.error(f"Error getting notification statistics: {e}")
            return {}
    
    async def cleanup_inactive_devices(self, days_inactive: int = 30) -> int:
        """Clean up inactive devices"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
            
            db = next(get_db())
            
            # Count devices to be cleaned
            count = db.query(PushDeviceModel).filter(
                PushDeviceModel.last_used < cutoff_date,
                PushDeviceModel.is_active == True
            ).count()
            
            # Deactivate inactive devices
            db.query(PushDeviceModel).filter(
                PushDeviceModel.last_used < cutoff_date,
                PushDeviceModel.is_active == True
            ).update({"is_active": False})
            
            db.commit()
            
            logger.info(f"Cleaned up {count} inactive devices")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive devices: {e}")
            return 0

# Global push notification service instance
push_notification_service = PushNotificationService()

# Convenience functions for common notification types
async def send_payment_reminder_push(user_id: int, amount: float, due_date: datetime):
    """Send payment reminder push notification"""
    payload = PushNotificationPayload(
        title="Payment Reminder",
        body=f"Your payment of ${amount:.2f} is due on {due_date.strftime('%Y-%m-%d')}",
        data={
            "type": "payment_reminder",
            "amount": amount,
            "due_date": due_date.isoformat()
        },
        priority=NotificationPriority.HIGH,
        icon="/static/icons/payment.png",
        click_action="/payments"
    )
    
    return await push_notification_service.send_notification(user_id, payload)

async def send_class_reminder_push(user_id: int, class_name: str, start_time: datetime):
    """Send class reminder push notification"""
    payload = PushNotificationPayload(
        title="Class Reminder",
        body=f"Your {class_name} class starts at {start_time.strftime('%H:%M')}",
        data={
            "type": "class_reminder",
            "class_name": class_name,
            "start_time": start_time.isoformat()
        },
        priority=NotificationPriority.NORMAL,
        icon="/static/icons/class.png",
        click_action="/classes"
    )
    
    return await push_notification_service.send_notification(user_id, payload)

async def send_membership_expiry_push(user_id: int, expiry_date: datetime):
    """Send membership expiry push notification"""
    payload = PushNotificationPayload(
        title="Membership Expiring",
        body=f"Your membership expires on {expiry_date.strftime('%Y-%m-%d')}",
        data={
            "type": "membership_expiry",
            "expiry_date": expiry_date.isoformat()
        },
        priority=NotificationPriority.HIGH,
        icon="/static/icons/membership.png",
        click_action="/membership"
    )
    
    return await push_notification_service.send_notification(user_id, payload)