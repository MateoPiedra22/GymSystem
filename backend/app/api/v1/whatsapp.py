from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.auth import get_current_user, require_admin_access
from ...models.user import User
from ...services.whatsapp_service import (
    whatsapp_service, MessageType, MessageStatus, MessagePriority, MessageCategory,
    WhatsAppMessage, WhatsAppMedia, WhatsAppContact, WhatsAppLocation,
    WhatsAppInteractive, WhatsAppButton, WhatsAppTemplate
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

# Pydantic models for requests and responses
class WhatsAppTextRequest(BaseModel):
    """Request model for sending text messages"""
    to: str = Field(..., description="Phone number with country code")
    message: str = Field(..., description="Text message content")
    category: MessageCategory = Field(default=MessageCategory.CUSTOM)
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    
    @validator('to')
    def validate_phone(cls, v):
        # Basic phone validation
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if not cleaned or len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v

class WhatsAppTemplateRequest(BaseModel):
    """Request model for sending template messages"""
    to: str = Field(..., description="Phone number with country code")
    template_name: str = Field(..., description="Template name")
    parameters: List[str] = Field(default=[], description="Template parameters")
    language: str = Field(default="en", description="Template language")
    
    @validator('to')
    def validate_phone(cls, v):
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if not cleaned or len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v

class WhatsAppMediaRequest(BaseModel):
    """Request model for sending media messages"""
    to: str = Field(..., description="Phone number with country code")
    media_type: MessageType = Field(..., description="Media type")
    media_url: str = Field(..., description="Media URL")
    caption: Optional[str] = Field(None, description="Media caption")
    filename: Optional[str] = Field(None, description="File name for documents")
    
    @validator('to')
    def validate_phone(cls, v):
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if not cleaned or len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v
    
    @validator('media_type')
    def validate_media_type(cls, v):
        if v not in [MessageType.IMAGE, MessageType.DOCUMENT, MessageType.AUDIO, MessageType.VIDEO]:
            raise ValueError('Invalid media type')
        return v

class WhatsAppLocationRequest(BaseModel):
    """Request model for sending location messages"""
    to: str = Field(..., description="Phone number with country code")
    latitude: float = Field(..., description="Location latitude")
    longitude: float = Field(..., description="Location longitude")
    name: Optional[str] = Field(None, description="Location name")
    address: Optional[str] = Field(None, description="Location address")
    
    @validator('to')
    def validate_phone(cls, v):
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if not cleaned or len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v

class WhatsAppButtonModel(BaseModel):
    """Button model for interactive messages"""
    id: str = Field(..., description="Button ID")
    title: str = Field(..., description="Button title")
    type: str = Field(default="reply", description="Button type")

class WhatsAppInteractiveRequest(BaseModel):
    """Request model for sending interactive messages"""
    to: str = Field(..., description="Phone number with country code")
    type: str = Field(..., description="Interactive type (button or list)")
    header: Optional[str] = Field(None, description="Message header")
    body: str = Field(..., description="Message body")
    footer: Optional[str] = Field(None, description="Message footer")
    buttons: List[WhatsAppButtonModel] = Field(default=[], description="Interactive buttons")
    
    @validator('to')
    def validate_phone(cls, v):
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if not cleaned or len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v
    
    @validator('type')
    def validate_type(cls, v):
        if v not in ["button", "list"]:
            raise ValueError('Interactive type must be "button" or "list"')
        return v

class WhatsAppBulkRequest(BaseModel):
    """Request model for sending bulk messages"""
    phone_numbers: List[str] = Field(..., description="List of phone numbers")
    message: str = Field(..., description="Text message content")
    category: MessageCategory = Field(default=MessageCategory.MARKETING)
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    batch_size: int = Field(default=50, description="Batch size for sending")
    
    @validator('phone_numbers')
    def validate_phones(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one phone number is required')
        if len(v) > 1000:
            raise ValueError('Maximum 1000 phone numbers allowed')
        
        for phone in v:
            cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
            if not cleaned or len(cleaned) < 10:
                raise ValueError(f'Invalid phone number format: {phone}')
        return v

class WhatsAppWelcomeRequest(BaseModel):
    """Request model for sending welcome messages"""
    phone: str = Field(..., description="Phone number with country code")
    user_name: str = Field(..., description="User name")
    
    @validator('phone')
    def validate_phone(cls, v):
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if not cleaned or len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v

class WhatsAppPaymentReminderRequest(BaseModel):
    """Request model for sending payment reminders"""
    phone: str = Field(..., description="Phone number with country code")
    user_name: str = Field(..., description="User name")
    amount: str = Field(..., description="Payment amount")
    due_date: str = Field(..., description="Payment due date")
    
    @validator('phone')
    def validate_phone(cls, v):
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if not cleaned or len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v

class WhatsAppClassReminderRequest(BaseModel):
    """Request model for sending class reminders"""
    phone: str = Field(..., description="Phone number with country code")
    user_name: str = Field(..., description="User name")
    class_name: str = Field(..., description="Class name")
    class_time: str = Field(..., description="Class time")
    
    @validator('phone')
    def validate_phone(cls, v):
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if not cleaned or len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v

class WhatsAppMembershipExpiryRequest(BaseModel):
    """Request model for sending membership expiry notices"""
    phone: str = Field(..., description="Phone number with country code")
    user_name: str = Field(..., description="User name")
    expiry_date: str = Field(..., description="Membership expiry date")
    
    @validator('phone')
    def validate_phone(cls, v):
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if not cleaned or len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v

# Response models
class WhatsAppMessageResponse(BaseModel):
    """Response model for message sending"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None

class WhatsAppBulkResponse(BaseModel):
    """Response model for bulk message sending"""
    total: int
    sent: int
    failed: int
    errors: List[Dict[str, Any]] = []

class WhatsAppStatusResponse(BaseModel):
    """Response model for message status"""
    message_id: str
    status: str
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None
    error_message: Optional[str] = None

class WhatsAppStatisticsResponse(BaseModel):
    """Response model for WhatsApp statistics"""
    total_messages: int
    sent_messages: int
    delivered_messages: int
    read_messages: int
    failed_messages: int
    success_rate: float
    delivery_rate: float
    read_rate: float
    category_statistics: Dict[str, int]
    type_statistics: Dict[str, int]

# API Endpoints
@router.post("/send/text", response_model=WhatsAppMessageResponse)
async def send_text_message(
    request: WhatsAppTextRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a text message via WhatsApp"""
    try:
        result = await whatsapp_service.send_text_message(
            to=request.to,
            text=request.message,
            category=request.category
        )
        
        return WhatsAppMessageResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp text message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.post("/send/template", response_model=WhatsAppMessageResponse)
async def send_template_message(
    request: WhatsAppTemplateRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a template message via WhatsApp"""
    try:
        result = await whatsapp_service.send_template_message(
            to=request.to,
            template_name=request.template_name,
            parameters=request.parameters,
            language=request.language
        )
        
        return WhatsAppMessageResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp template message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send template message: {str(e)}"
        )

@router.post("/send/media", response_model=WhatsAppMessageResponse)
async def send_media_message(
    request: WhatsAppMediaRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a media message via WhatsApp"""
    try:
        media = WhatsAppMedia(
            media_type=request.media_type,
            url=request.media_url,
            caption=request.caption,
            filename=request.filename
        )
        
        result = await whatsapp_service.send_media_message(
            to=request.to,
            media=media,
            caption=request.caption
        )
        
        return WhatsAppMessageResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp media message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send media message: {str(e)}"
        )

@router.post("/send/location", response_model=WhatsAppMessageResponse)
async def send_location_message(
    request: WhatsAppLocationRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a location message via WhatsApp"""
    try:
        location = WhatsAppLocation(
            latitude=request.latitude,
            longitude=request.longitude,
            name=request.name,
            address=request.address
        )
        
        result = await whatsapp_service.send_location_message(
            to=request.to,
            location=location
        )
        
        return WhatsAppMessageResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp location message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send location message: {str(e)}"
        )

@router.post("/send/interactive", response_model=WhatsAppMessageResponse)
async def send_interactive_message(
    request: WhatsAppInteractiveRequest,
    current_user: User = Depends(get_current_user)
):
    """Send an interactive message via WhatsApp"""
    try:
        buttons = [
            WhatsAppButton(
                id=btn.id,
                title=btn.title,
                type=btn.type
            )
            for btn in request.buttons
        ]
        
        interactive = WhatsAppInteractive(
            type=request.type,
            header=request.header,
            body=request.body,
            footer=request.footer,
            buttons=buttons
        )
        
        result = await whatsapp_service.send_interactive_message(
            to=request.to,
            interactive=interactive
        )
        
        return WhatsAppMessageResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp interactive message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send interactive message: {str(e)}"
        )

@router.post("/send/bulk", response_model=WhatsAppBulkResponse)
async def send_bulk_messages(
    request: WhatsAppBulkRequest,
    current_user: User = Depends(require_admin_access)
):
    """Send bulk messages via WhatsApp (Admin only)"""
    try:
        messages = [
            WhatsAppMessage(
                to=phone,
                message_type=MessageType.TEXT,
                content=request.message,
                category=request.category,
                priority=request.priority
            )
            for phone in request.phone_numbers
        ]
        
        result = await whatsapp_service.send_bulk_messages(
            messages=messages,
            batch_size=request.batch_size
        )
        
        return WhatsAppBulkResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send bulk WhatsApp messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk messages: {str(e)}"
        )

@router.post("/send/welcome", response_model=WhatsAppMessageResponse)
async def send_welcome_message(
    request: WhatsAppWelcomeRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a welcome message to new member"""
    try:
        result = await whatsapp_service.send_welcome_message(
            phone=request.phone,
            user_name=request.user_name
        )
        
        return WhatsAppMessageResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp welcome message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send welcome message: {str(e)}"
        )

@router.post("/send/payment-reminder", response_model=WhatsAppMessageResponse)
async def send_payment_reminder(
    request: WhatsAppPaymentReminderRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a payment reminder message"""
    try:
        result = await whatsapp_service.send_payment_reminder(
            phone=request.phone,
            user_name=request.user_name,
            amount=request.amount,
            due_date=request.due_date
        )
        
        return WhatsAppMessageResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp payment reminder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send payment reminder: {str(e)}"
        )

@router.post("/send/class-reminder", response_model=WhatsAppMessageResponse)
async def send_class_reminder(
    request: WhatsAppClassReminderRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a class reminder message"""
    try:
        result = await whatsapp_service.send_class_reminder(
            phone=request.phone,
            user_name=request.user_name,
            class_name=request.class_name,
            class_time=request.class_time
        )
        
        return WhatsAppMessageResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp class reminder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send class reminder: {str(e)}"
        )

@router.post("/send/membership-expiry", response_model=WhatsAppMessageResponse)
async def send_membership_expiry_notice(
    request: WhatsAppMembershipExpiryRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a membership expiry notice"""
    try:
        result = await whatsapp_service.send_membership_expiry_notice(
            phone=request.phone,
            user_name=request.user_name,
            expiry_date=request.expiry_date
        )
        
        return WhatsAppMessageResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp membership expiry notice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send membership expiry notice: {str(e)}"
        )

@router.get("/status/{message_id}", response_model=WhatsAppStatusResponse)
async def get_message_status(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a sent WhatsApp message"""
    try:
        result = await whatsapp_service.get_message_status(message_id)
        return WhatsAppStatusResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to get WhatsApp message status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get message status: {str(e)}"
        )

@router.get("/statistics", response_model=WhatsAppStatisticsResponse)
async def get_whatsapp_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(require_admin_access)
):
    """Get WhatsApp message statistics (Admin only)"""
    try:
        result = await whatsapp_service.get_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return WhatsAppStatisticsResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to get WhatsApp statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

@router.post("/webhook")
async def whatsapp_webhook(
    webhook_data: Dict[str, Any]
):
    """Handle WhatsApp webhook events"""
    try:
        result = await whatsapp_service.handle_webhook(webhook_data)
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Failed to handle WhatsApp webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle webhook: {str(e)}"
        )

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    """Verify WhatsApp webhook"""
    try:
        if (hub_mode == "subscribe" and 
            hub_verify_token == whatsapp_service.webhook_verify_token):
            return int(hub_challenge)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid verification token"
            )
            
    except Exception as e:
        logger.error(f"Failed to verify WhatsApp webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify webhook: {str(e)}"
        )

@router.post("/test")
async def send_test_message(
    phone: str,
    current_user: User = Depends(require_admin_access)
):
    """Send a test message (Admin only)"""
    try:
        result = await whatsapp_service.send_text_message(
            to=phone,
            text="🧪 Este es un mensaje de prueba del sistema de WhatsApp del gimnasio. ¡Todo funciona correctamente!",
            category=MessageCategory.SYSTEM
        )
        
        return WhatsAppMessageResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp test message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test message: {str(e)}"
        )

@router.get("/config")
async def get_whatsapp_config(
    current_user: User = Depends(require_admin_access)
):
    """Get WhatsApp service configuration (Admin only)"""
    try:
        config = {
            "is_configured": whatsapp_service._is_configured(),
            "phone_number_id": whatsapp_service.phone_number_id,
            "business_account_id": whatsapp_service.business_account_id,
            "api_version": whatsapp_service.api_version,
            "rate_limit_per_second": whatsapp_service.rate_limit_per_second,
            "max_retries": whatsapp_service.max_retries
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to get WhatsApp config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )

@router.get("/message-types")
async def get_message_types(
    current_user: User = Depends(get_current_user)
):
    """Get available WhatsApp message types"""
    return {
        "message_types": [msg_type.value for msg_type in MessageType],
        "message_categories": [category.value for category in MessageCategory],
        "message_priorities": [priority.value for priority in MessagePriority],
        "message_statuses": [status.value for status in MessageStatus]
    }