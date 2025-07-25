from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import aiohttp
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from ..core.database import Base, get_db
from ..core.config import settings
from .config_service import get_config_service
import base64
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """WhatsApp message types"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"
    STICKER = "sticker"

class MessageStatus(Enum):
    """WhatsApp message status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    REJECTED = "rejected"

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class MessageCategory(Enum):
    """Message categories for tracking"""
    WELCOME = "welcome"
    PAYMENT_REMINDER = "payment_reminder"
    CLASS_REMINDER = "class_reminder"
    MEMBERSHIP_EXPIRY = "membership_expiry"
    PROMOTION = "promotion"
    NOTIFICATION = "notification"
    SUPPORT = "support"
    MARKETING = "marketing"
    SYSTEM = "system"
    CUSTOM = "custom"

@dataclass
class WhatsAppMedia:
    """WhatsApp media attachment"""
    media_type: MessageType
    url: Optional[str] = None
    filename: Optional[str] = None
    caption: Optional[str] = None
    content: Optional[bytes] = None
    mime_type: Optional[str] = None

@dataclass
class WhatsAppContact:
    """WhatsApp contact information"""
    name: str
    phone: str
    email: Optional[str] = None
    organization: Optional[str] = None

@dataclass
class WhatsAppLocation:
    """WhatsApp location information"""
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None

@dataclass
class WhatsAppButton:
    """WhatsApp interactive button"""
    id: str
    title: str
    type: str = "reply"

@dataclass
class WhatsAppInteractive:
    """WhatsApp interactive message"""
    type: str  # "button" or "list"
    header: Optional[str] = None
    body: str = ""
    footer: Optional[str] = None
    buttons: List[WhatsAppButton] = field(default_factory=list)
    list_items: Optional[List[Dict[str, Any]]] = None

@dataclass
class WhatsAppTemplate:
    """WhatsApp template message"""
    name: str
    language: str = "en"
    parameters: List[str] = field(default_factory=list)
    header_parameters: Optional[List[str]] = None
    body_parameters: Optional[List[str]] = None
    button_parameters: Optional[List[str]] = None

@dataclass
class WhatsAppMessage:
    """WhatsApp message data"""
    to: str  # Phone number with country code
    message_type: MessageType
    content: Optional[str] = None
    media: Optional[WhatsAppMedia] = None
    contact: Optional[WhatsAppContact] = None
    location: Optional[WhatsAppLocation] = None
    interactive: Optional[WhatsAppInteractive] = None
    template: Optional[WhatsAppTemplate] = None
    priority: MessagePriority = MessagePriority.NORMAL
    category: MessageCategory = MessageCategory.CUSTOM
    scheduled_at: Optional[datetime] = None
    reply_to: Optional[str] = None
    context_message_id: Optional[str] = None

class WhatsAppMessageModel(Base):
    """WhatsApp message log database model"""
    __tablename__ = "whatsapp_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    to_number = Column(String(20), nullable=False, index=True)
    message_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    whatsapp_message_id = Column(String(100), nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    template_name = Column(String(100), nullable=True)
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WhatsAppTemplateModel(Base):
    """WhatsApp template database model"""
    __tablename__ = "whatsapp_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    language = Column(String(10), nullable=False, default="en")
    header_text = Column(Text, nullable=True)
    body_text = Column(Text, nullable=False)
    footer_text = Column(Text, nullable=True)
    buttons = Column(JSON, nullable=True)
    parameters = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WhatsAppService:
    """Advanced WhatsApp Business API service"""
    
    def __init__(self):
        self.api_url = None
        self.access_token = None
        self.phone_number_id = None
        self.business_account_id = None
        self.webhook_verify_token = None
        self.app_secret = None
        self.api_version = "v18.0"
        self.max_retries = 3
        self.retry_delay = 60  # seconds
        self.rate_limit_per_second = 80  # WhatsApp Business API limit
        self.session = None
        self._initialize_config()
    
    def _initialize_config(self):
        """Initialize WhatsApp configuration"""
        try:
            # Get WhatsApp configuration
            whatsapp_config = get_config_service().get_category_configs("whatsapp")
            
            self.access_token = whatsapp_config.get("access_token", settings.WHATSAPP_API_TOKEN)
            self.phone_number_id = whatsapp_config.get("phone_number_id", settings.WHATSAPP_PHONE_NUMBER_ID)
            self.business_account_id = whatsapp_config.get("business_account_id", settings.WHATSAPP_BUSINESS_ACCOUNT_ID)
            self.webhook_verify_token = whatsapp_config.get("webhook_verify_token", settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN)
            self.app_secret = whatsapp_config.get("app_secret", settings.WHATSAPP_APP_SECRET)
            
            # Construct API URL
            if self.phone_number_id:
                self.api_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
            
        except Exception as e:
            logger.warning(f"Failed to load WhatsApp config: {e}")
            # Fallback to environment variables
            self.access_token = settings.WHATSAPP_API_TOKEN
            self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
            self.business_account_id = settings.WHATSAPP_BUSINESS_ACCOUNT_ID
            self.webhook_verify_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
            self.app_secret = settings.WHATSAPP_APP_SECRET
            
            if self.phone_number_id:
                self.api_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def send_message(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """Send a WhatsApp message"""
        try:
            # Validate configuration
            if not self._is_configured():
                return {
                    "success": False,
                    "error": "WhatsApp service not configured"
                }
            
            # Validate phone number
            if not self._validate_phone_number(message.to):
                return {
                    "success": False,
                    "error": "Invalid phone number format"
                }
            
            # Build message payload
            payload = await self._build_message_payload(message)
            
            # Send message via API
            result = await self._send_api_request(payload)
            
            # Log message
            await self._log_message(message, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            await self._log_message(message, {
                "success": False,
                "error": str(e)
            })
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_bulk_messages(self, messages: List[WhatsAppMessage], 
                               batch_size: int = 50) -> Dict[str, Any]:
        """Send multiple WhatsApp messages in batches"""
        results = {
            "total": len(messages),
            "sent": 0,
            "failed": 0,
            "errors": []
        }
        
        # Process in batches to respect rate limits
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            
            # Send batch with rate limiting
            batch_results = []
            for j, message in enumerate(batch):
                result = await self.send_message(message)
                batch_results.append(result)
                
                # Rate limiting: wait between messages
                if j < len(batch) - 1:
                    await asyncio.sleep(1.0 / self.rate_limit_per_second)
            
            # Process results
            for j, result in enumerate(batch_results):
                if result.get("success"):
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "index": i + j,
                        "error": result.get("error", "Unknown error")
                    })
            
            # Add delay between batches
            if i + batch_size < len(messages):
                await asyncio.sleep(2)
        
        return results
    
    async def send_template_message(self, to: str, template_name: str, 
                                  parameters: List[str], language: str = "en") -> Dict[str, Any]:
        """Send a WhatsApp template message"""
        template = WhatsAppTemplate(
            name=template_name,
            language=language,
            parameters=parameters
        )
        
        message = WhatsAppMessage(
            to=to,
            message_type=MessageType.TEMPLATE,
            template=template,
            category=MessageCategory.NOTIFICATION
        )
        
        return await self.send_message(message)
    
    async def send_text_message(self, to: str, text: str, 
                              category: MessageCategory = MessageCategory.CUSTOM) -> Dict[str, Any]:
        """Send a simple text message"""
        message = WhatsAppMessage(
            to=to,
            message_type=MessageType.TEXT,
            content=text,
            category=category
        )
        
        return await self.send_message(message)
    
    async def send_media_message(self, to: str, media: WhatsAppMedia, 
                               caption: Optional[str] = None) -> Dict[str, Any]:
        """Send a media message (image, document, audio, video)"""
        if caption:
            media.caption = caption
        
        message = WhatsAppMessage(
            to=to,
            message_type=media.media_type,
            media=media,
            category=MessageCategory.CUSTOM
        )
        
        return await self.send_message(message)
    
    async def send_interactive_message(self, to: str, interactive: WhatsAppInteractive) -> Dict[str, Any]:
        """Send an interactive message with buttons or list"""
        message = WhatsAppMessage(
            to=to,
            message_type=MessageType.INTERACTIVE,
            interactive=interactive,
            category=MessageCategory.CUSTOM
        )
        
        return await self.send_message(message)
    
    async def send_location_message(self, to: str, location: WhatsAppLocation) -> Dict[str, Any]:
        """Send a location message"""
        message = WhatsAppMessage(
            to=to,
            message_type=MessageType.LOCATION,
            location=location,
            category=MessageCategory.CUSTOM
        )
        
        return await self.send_message(message)
    
    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Get status of a sent message"""
        try:
            db = next(get_db())
            
            message_log = db.query(WhatsAppMessageModel).filter(
                WhatsAppMessageModel.whatsapp_message_id == message_id
            ).first()
            
            if message_log:
                return {
                    "message_id": message_id,
                    "status": message_log.status,
                    "sent_at": message_log.sent_at.isoformat() if message_log.sent_at else None,
                    "delivered_at": message_log.delivered_at.isoformat() if message_log.delivered_at else None,
                    "read_at": message_log.read_at.isoformat() if message_log.read_at else None,
                    "error_message": message_log.error_message
                }
            else:
                return {
                    "message_id": message_id,
                    "status": "not_found"
                }
                
        except Exception as e:
            logger.error(f"Failed to get message status: {e}")
            return {
                "message_id": message_id,
                "status": "error",
                "error": str(e)
            }
        finally:
            db.close()
    
    async def get_statistics(self, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get WhatsApp message statistics"""
        try:
            db = next(get_db())
            
            # Build query
            query = db.query(WhatsAppMessageModel)
            
            if start_date:
                query = query.filter(WhatsAppMessageModel.created_at >= start_date)
            if end_date:
                query = query.filter(WhatsAppMessageModel.created_at <= end_date)
            
            # Get total counts
            total_messages = query.count()
            sent_messages = query.filter(WhatsAppMessageModel.status == MessageStatus.SENT.value).count()
            delivered_messages = query.filter(WhatsAppMessageModel.status == MessageStatus.DELIVERED.value).count()
            read_messages = query.filter(WhatsAppMessageModel.status == MessageStatus.READ.value).count()
            failed_messages = query.filter(WhatsAppMessageModel.status == MessageStatus.FAILED.value).count()
            
            # Calculate rates
            success_rate = (sent_messages / total_messages * 100) if total_messages > 0 else 0
            delivery_rate = (delivered_messages / sent_messages * 100) if sent_messages > 0 else 0
            read_rate = (read_messages / delivered_messages * 100) if delivered_messages > 0 else 0
            
            # Get statistics by category
            category_stats = {}
            for category in MessageCategory:
                category_count = query.filter(WhatsAppMessageModel.category == category.value).count()
                if category_count > 0:
                    category_stats[category.value] = category_count
            
            # Get statistics by message type
            type_stats = {}
            for msg_type in MessageType:
                type_count = query.filter(WhatsAppMessageModel.message_type == msg_type.value).count()
                if type_count > 0:
                    type_stats[msg_type.value] = type_count
            
            return {
                "total_messages": total_messages,
                "sent_messages": sent_messages,
                "delivered_messages": delivered_messages,
                "read_messages": read_messages,
                "failed_messages": failed_messages,
                "success_rate": round(success_rate, 2),
                "delivery_rate": round(delivery_rate, 2),
                "read_rate": round(read_rate, 2),
                "category_statistics": category_stats,
                "type_statistics": type_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get WhatsApp statistics: {e}")
            return {}
        finally:
            db.close()
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhook from WhatsApp"""
        try:
            # Verify webhook signature if app secret is configured
            if self.app_secret:
                # TODO: Implement webhook signature verification
                pass
            
            # Process webhook data
            if "entry" in webhook_data:
                for entry in webhook_data["entry"]:
                    if "changes" in entry:
                        for change in entry["changes"]:
                            if change.get("field") == "messages":
                                await self._process_message_webhook(change["value"])
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Failed to handle webhook: {e}")
            return {"status": "error", "error": str(e)}
    
    def _is_configured(self) -> bool:
        """Check if WhatsApp service is properly configured"""
        return all([
            self.access_token,
            self.phone_number_id,
            self.api_url
        ])
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format"""
        # Remove any non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Should start with + and have 10-15 digits
        if cleaned.startswith('+') and 10 <= len(cleaned) - 1 <= 15:
            return True
        
        # If no +, assume it's a valid number and add +
        if cleaned.isdigit() and 10 <= len(cleaned) <= 15:
            return True
        
        return False
    
    def _normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number to international format"""
        # Remove any non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Add + if not present
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        
        return cleaned
    
    async def _build_message_payload(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """Build API payload for message"""
        payload = {
            "messaging_product": "whatsapp",
            "to": self._normalize_phone_number(message.to),
            "type": message.message_type.value
        }
        
        # Add context if replying to a message
        if message.context_message_id:
            payload["context"] = {
                "message_id": message.context_message_id
            }
        
        # Build message content based on type
        if message.message_type == MessageType.TEXT:
            payload["text"] = {
                "body": message.content
            }
        
        elif message.message_type == MessageType.TEMPLATE:
            if message.template:
                payload["template"] = {
                    "name": message.template.name,
                    "language": {
                        "code": message.template.language
                    }
                }
                
                if message.template.parameters:
                    payload["template"]["components"] = [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": param}
                                for param in message.template.parameters
                            ]
                        }
                    ]
        
        elif message.message_type == MessageType.INTERACTIVE:
            if message.interactive:
                interactive_payload = {
                    "type": message.interactive.type,
                    "body": {
                        "text": message.interactive.body
                    }
                }
                
                if message.interactive.header:
                    interactive_payload["header"] = {
                        "type": "text",
                        "text": message.interactive.header
                    }
                
                if message.interactive.footer:
                    interactive_payload["footer"] = {
                        "text": message.interactive.footer
                    }
                
                if message.interactive.type == "button" and message.interactive.buttons:
                    interactive_payload["action"] = {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": button.id,
                                    "title": button.title
                                }
                            }
                            for button in message.interactive.buttons
                        ]
                    }
                
                payload["interactive"] = interactive_payload
        
        elif message.message_type == MessageType.LOCATION:
            if message.location:
                payload["location"] = {
                    "latitude": message.location.latitude,
                    "longitude": message.location.longitude
                }
                
                if message.location.name:
                    payload["location"]["name"] = message.location.name
                
                if message.location.address:
                    payload["location"]["address"] = message.location.address
        
        elif message.message_type in [MessageType.IMAGE, MessageType.DOCUMENT, MessageType.AUDIO, MessageType.VIDEO]:
            if message.media:
                media_payload = {}
                
                if message.media.url:
                    media_payload["link"] = message.media.url
                elif message.media.content:
                    # Upload media first (implementation depends on your media storage)
                    # For now, we'll assume URL is provided
                    pass
                
                if message.media.caption and message.message_type in [MessageType.IMAGE, MessageType.DOCUMENT, MessageType.VIDEO]:
                    media_payload["caption"] = message.media.caption
                
                if message.media.filename and message.message_type == MessageType.DOCUMENT:
                    media_payload["filename"] = message.media.filename
                
                payload[message.message_type.value] = media_payload
        
        return payload
    
    async def _send_api_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to WhatsApp API"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        session = await self._get_session()
        
        try:
            async with session.post(self.api_url, json=payload, headers=headers) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    return {
                        "success": True,
                        "message_id": response_data.get("messages", [{}])[0].get("id"),
                        "whatsapp_id": response_data.get("messages", [{}])[0].get("id")
                    }
                else:
                    error_message = response_data.get("error", {}).get("message", "Unknown error")
                    return {
                        "success": False,
                        "error": error_message,
                        "status_code": response.status
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _log_message(self, message: WhatsAppMessage, result: Dict[str, Any]):
        """Log message to database"""
        try:
            db = next(get_db())
            
            status = MessageStatus.SENT if result.get("success") else MessageStatus.FAILED
            
            log_entry = WhatsAppMessageModel(
                to_number=self._normalize_phone_number(message.to),
                message_type=message.message_type.value,
                content=message.content,
                category=message.category.value,
                priority=message.priority.value,
                status=status.value,
                whatsapp_message_id=result.get("message_id"),
                error_message=result.get("error"),
                template_name=message.template.name if message.template else None,
                message_metadata={
                    "scheduled_at": message.scheduled_at.isoformat() if message.scheduled_at else None,
                    "reply_to": message.reply_to,
                    "context_message_id": message.context_message_id
                }
            )
            
            if status == MessageStatus.SENT:
                log_entry.sent_at = datetime.utcnow()
            
            db.add(log_entry)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log WhatsApp message: {e}")
        finally:
            db.close()
    
    async def _process_message_webhook(self, webhook_value: Dict[str, Any]):
        """Process incoming message webhook"""
        try:
            # Handle status updates
            if "statuses" in webhook_value:
                for status in webhook_value["statuses"]:
                    await self._update_message_status(status)
            
            # Handle incoming messages
            if "messages" in webhook_value:
                for message in webhook_value["messages"]:
                    await self._handle_incoming_message(message)
            
        except Exception as e:
            logger.error(f"Failed to process message webhook: {e}")
    
    async def _update_message_status(self, status_data: Dict[str, Any]):
        """Update message status from webhook"""
        try:
            db = next(get_db())
            
            message_id = status_data.get("id")
            status = status_data.get("status")
            timestamp = status_data.get("timestamp")
            
            if message_id and status:
                message_log = db.query(WhatsAppMessageModel).filter(
                    WhatsAppMessageModel.whatsapp_message_id == message_id
                ).first()
                
                if message_log:
                    message_log.status = status
                    message_log.updated_at = datetime.utcnow()
                    
                    if status == "delivered" and not message_log.delivered_at:
                        message_log.delivered_at = datetime.fromtimestamp(int(timestamp))
                    elif status == "read" and not message_log.read_at:
                        message_log.read_at = datetime.fromtimestamp(int(timestamp))
                    
                    db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update message status: {e}")
        finally:
            db.close()
    
    async def _handle_incoming_message(self, message_data: Dict[str, Any]):
        """Handle incoming message from user"""
        try:
            # Log incoming message for future processing
            logger.info(f"Received WhatsApp message: {message_data}")
            
            # Here you can implement auto-responses, chatbot logic, etc.
            # For now, we'll just log the message
            
        except Exception as e:
            logger.error(f"Failed to handle incoming message: {e}")
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    # Convenience methods for common message types
    async def send_welcome_message(self, phone: str, user_name: str) -> Dict[str, Any]:
        """Send welcome message to new member"""
        text = f"¡Hola {user_name}! 👋\n\nBienvenido/a a nuestro gimnasio. Estamos emocionados de tenerte como parte de nuestra comunidad fitness.\n\n💪 ¡Comencemos tu viaje hacia una vida más saludable!"
        
        return await self.send_text_message(
            to=phone,
            text=text,
            category=MessageCategory.WELCOME
        )
    
    async def send_payment_reminder(self, phone: str, user_name: str, 
                                  amount: str, due_date: str) -> Dict[str, Any]:
        """Send payment reminder message"""
        text = f"Hola {user_name},\n\n💳 Recordatorio de pago:\n\n💰 Monto: ${amount}\n📅 Fecha límite: {due_date}\n\nPor favor realiza tu pago para evitar la suspensión de servicios.\n\n¡Gracias!"
        
        return await self.send_text_message(
            to=phone,
            text=text,
            category=MessageCategory.PAYMENT_REMINDER
        )
    
    async def send_class_reminder(self, phone: str, user_name: str, 
                                class_name: str, class_time: str) -> Dict[str, Any]:
        """Send class reminder message"""
        text = f"¡Hola {user_name}! 🏃‍♀️\n\n⏰ Recordatorio de clase:\n\n🎯 Clase: {class_name}\n🕐 Hora: {class_time}\n\n¡Te esperamos! No olvides traer tu toalla y botella de agua.\n\n💪 ¡Vamos a entrenar!"
        
        return await self.send_text_message(
            to=phone,
            text=text,
            category=MessageCategory.CLASS_REMINDER
        )
    
    async def send_membership_expiry_notice(self, phone: str, user_name: str, 
                                          expiry_date: str) -> Dict[str, Any]:
        """Send membership expiry notice"""
        text = f"Hola {user_name},\n\n⚠️ Tu membresía vence pronto:\n\n📅 Fecha de vencimiento: {expiry_date}\n\nRenueva tu membresía para continuar disfrutando de todos nuestros servicios.\n\n¡Contáctanos para más información!"
        
        return await self.send_text_message(
            to=phone,
            text=text,
            category=MessageCategory.MEMBERSHIP_EXPIRY
        )

# Global WhatsApp service instance
whatsapp_service = WhatsAppService()