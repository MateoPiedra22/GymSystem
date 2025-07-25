from fastapi import APIRouter, Depends, HTTPException, Query, Path, UploadFile, File
from fastapi.responses import Response
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.auth import get_current_user, require_admin_access
from ...models.user import User
from ...services.email_service import (
    email_service,
    EmailMessage,
    EmailTemplate,
    EmailAttachment,
    EmailPriority,
    EmailType,
    EmailStatus
)
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
import logging
import base64

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["email"])

# Pydantic models for request/response
class EmailPriorityEnum(str, Enum):
    """Email priority enum for API"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EmailTypeEnum(str, Enum):
    """Email type enum for API"""
    WELCOME = "welcome"
    PAYMENT_REMINDER = "payment_reminder"
    CLASS_REMINDER = "class_reminder"
    MEMBERSHIP_EXPIRY = "membership_expiry"
    PASSWORD_RESET = "password_reset"
    VERIFICATION = "verification"
    NEWSLETTER = "newsletter"
    PROMOTION = "promotion"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    CUSTOM = "custom"

class EmailAttachmentRequest(BaseModel):
    """Request model for email attachment"""
    filename: str = Field(..., description="Attachment filename")
    content: str = Field(..., description="Base64 encoded file content")
    content_type: str = Field("application/octet-stream", description="MIME content type")
    content_id: Optional[str] = Field(None, description="Content ID for inline attachments")

class EmailRequest(BaseModel):
    """Request model for sending emails"""
    to: Union[EmailStr, List[EmailStr]] = Field(..., description="Recipient email address(es)")
    subject: str = Field(..., description="Email subject")
    html_content: Optional[str] = Field(None, description="HTML email content")
    text_content: Optional[str] = Field(None, description="Plain text email content")
    cc: Optional[Union[EmailStr, List[EmailStr]]] = Field(None, description="CC recipients")
    bcc: Optional[Union[EmailStr, List[EmailStr]]] = Field(None, description="BCC recipients")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to address")
    attachments: Optional[List[EmailAttachmentRequest]] = Field(None, description="Email attachments")
    priority: EmailPriorityEnum = Field(EmailPriorityEnum.NORMAL, description="Email priority")
    email_type: EmailTypeEnum = Field(EmailTypeEnum.CUSTOM, description="Email type")
    tracking_enabled: bool = Field(True, description="Enable email tracking")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule email for later")

class TemplateEmailRequest(BaseModel):
    """Request model for template-based emails"""
    template_name: str = Field(..., description="Template name")
    to: Union[EmailStr, List[EmailStr]] = Field(..., description="Recipient email address(es)")
    variables: Dict[str, Any] = Field(..., description="Template variables")
    cc: Optional[Union[EmailStr, List[EmailStr]]] = Field(None, description="CC recipients")
    bcc: Optional[Union[EmailStr, List[EmailStr]]] = Field(None, description="BCC recipients")
    priority: EmailPriorityEnum = Field(EmailPriorityEnum.NORMAL, description="Email priority")
    tracking_enabled: bool = Field(True, description="Enable email tracking")

class BulkEmailRequest(BaseModel):
    """Request model for bulk emails"""
    recipients: List[EmailStr] = Field(..., description="List of recipient email addresses")
    subject: str = Field(..., description="Email subject")
    html_content: Optional[str] = Field(None, description="HTML email content")
    text_content: Optional[str] = Field(None, description="Plain text email content")
    priority: EmailPriorityEnum = Field(EmailPriorityEnum.NORMAL, description="Email priority")
    email_type: EmailTypeEnum = Field(EmailTypeEnum.CUSTOM, description="Email type")
    tracking_enabled: bool = Field(True, description="Enable email tracking")

class EmailTemplateRequest(BaseModel):
    """Request model for creating email templates"""
    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Email subject template")
    html_content: str = Field(..., description="HTML content template")
    text_content: Optional[str] = Field(None, description="Text content template")
    variables: List[str] = Field(default_factory=list, description="Template variables")
    category: EmailTypeEnum = Field(EmailTypeEnum.CUSTOM, description="Template category")
    description: Optional[str] = Field(None, description="Template description")

class WelcomeEmailRequest(BaseModel):
    """Request model for welcome emails"""
    user_email: EmailStr = Field(..., description="User email address")
    user_name: str = Field(..., description="User name")
    membership_type: str = Field(..., description="Membership type")
    start_date: str = Field(..., description="Membership start date")
    member_id: str = Field(..., description="Member ID")

class PaymentReminderRequest(BaseModel):
    """Request model for payment reminder emails"""
    user_email: EmailStr = Field(..., description="User email address")
    user_name: str = Field(..., description="User name")
    amount: str = Field(..., description="Payment amount")
    due_date: str = Field(..., description="Payment due date")
    description: str = Field("Membership fee", description="Payment description")

class ClassReminderRequest(BaseModel):
    """Request model for class reminder emails"""
    user_email: EmailStr = Field(..., description="User email address")
    user_name: str = Field(..., description="User name")
    class_name: str = Field(..., description="Class name")
    class_date: str = Field(..., description="Class date")
    start_time: str = Field(..., description="Class start time")
    end_time: str = Field(..., description="Class end time")
    instructor_name: str = Field(..., description="Instructor name")
    location: str = Field(..., description="Class location")
    class_id: Optional[int] = Field(None, description="Class ID")

class EmailResponse(BaseModel):
    """Response model for email operations"""
    success: bool
    message: str
    tracking_id: Optional[str] = None
    errors: Optional[List[str]] = None

class BulkEmailResponse(BaseModel):
    """Response model for bulk email operations"""
    success: bool
    total: int
    sent: int
    failed: int
    errors: Optional[List[Dict[str, Any]]] = None

class EmailStatisticsResponse(BaseModel):
    """Response model for email statistics"""
    total_emails: int
    sent_emails: int
    failed_emails: int
    delivered_emails: int
    opened_emails: int
    clicked_emails: int
    success_rate: float
    delivery_rate: float
    open_rate: float
    click_rate: float
    type_statistics: Dict[str, int]

class EmailTemplateResponse(BaseModel):
    """Response model for email templates"""
    id: int
    name: str
    subject: str
    category: str
    description: Optional[str]
    variables: List[str]
    created_at: str
    updated_at: str

@router.post(
    "/send",
    response_model=EmailResponse,
    summary="Send email",
    description="Send a single email message."
)
async def send_email(
    request: EmailRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a single email"""
    try:
        # Convert attachments
        attachments = []
        if request.attachments:
            for att_req in request.attachments:
                try:
                    content = base64.b64decode(att_req.content)
                    attachment = EmailAttachment(
                        filename=att_req.filename,
                        content=content,
                        content_type=att_req.content_type,
                        content_id=att_req.content_id
                    )
                    attachments.append(attachment)
                except Exception as e:
                    logger.error(f"Failed to decode attachment {att_req.filename}: {e}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid attachment: {att_req.filename}"
                    )
        
        # Create email message
        message = EmailMessage(
            to=request.to,
            subject=request.subject,
            html_content=request.html_content,
            text_content=request.text_content,
            cc=request.cc,
            bcc=request.bcc,
            reply_to=request.reply_to,
            attachments=attachments,
            priority=EmailPriority(request.priority.value),
            email_type=EmailType(request.email_type.value),
            tracking_enabled=request.tracking_enabled,
            scheduled_at=request.scheduled_at
        )
        
        # Send email
        result = await email_service.send_email(message)
        
        if result["success"]:
            return EmailResponse(
                success=True,
                message="Email sent successfully",
                tracking_id=result.get("tracking_id")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to send email")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error sending email"
        )

@router.post(
    "/send/template",
    response_model=EmailResponse,
    summary="Send template email",
    description="Send an email using a predefined template."
)
async def send_template_email(
    request: TemplateEmailRequest,
    current_user: User = Depends(get_current_user)
):
    """Send email using template"""
    try:
        result = await email_service.send_template_email(
            template_name=request.template_name,
            to=request.to,
            variables=request.variables,
            cc=request.cc,
            bcc=request.bcc,
            priority=EmailPriority(request.priority.value),
            tracking_enabled=request.tracking_enabled
        )
        
        if result["success"]:
            return EmailResponse(
                success=True,
                message="Template email sent successfully",
                tracking_id=result.get("tracking_id")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to send template email")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending template email: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error sending template email"
        )

@router.post(
    "/send/bulk",
    response_model=BulkEmailResponse,
    summary="Send bulk emails",
    description="Send emails to multiple recipients. Requires admin privileges."
)
async def send_bulk_emails(
    request: BulkEmailRequest,
    current_user: User = Depends(require_admin_access)
):
    """Send bulk emails (admin only)"""
    try:
        # Validate recipient count
        if len(request.recipients) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Cannot send to more than 1000 recipients at once"
            )
        
        # Create email messages
        messages = []
        for recipient in request.recipients:
            message = EmailMessage(
                to=recipient,
                subject=request.subject,
                html_content=request.html_content,
                text_content=request.text_content,
                priority=EmailPriority(request.priority.value),
                email_type=EmailType(request.email_type.value),
                tracking_enabled=request.tracking_enabled
            )
            messages.append(message)
        
        # Send bulk emails
        result = await email_service.send_bulk_emails(messages)
        
        return BulkEmailResponse(
            success=result["failed"] == 0,
            total=result["total"],
            sent=result["sent"],
            failed=result["failed"],
            errors=result.get("errors")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending bulk emails: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error sending bulk emails"
        )

@router.post(
    "/send/welcome",
    response_model=EmailResponse,
    summary="Send welcome email",
    description="Send a welcome email to a new member."
)
async def send_welcome_email(
    request: WelcomeEmailRequest,
    current_user: User = Depends(require_admin_access)
):
    """Send welcome email"""
    try:
        membership_details = {
            "type": request.membership_type,
            "start_date": request.start_date,
            "member_id": request.member_id
        }
        
        result = await email_service.send_welcome_email(
            user_email=request.user_email,
            user_name=request.user_name,
            membership_details=membership_details
        )
        
        if result["success"]:
            return EmailResponse(
                success=True,
                message="Welcome email sent successfully",
                tracking_id=result.get("tracking_id")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to send welcome email")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error sending welcome email"
        )

@router.post(
    "/send/payment-reminder",
    response_model=EmailResponse,
    summary="Send payment reminder",
    description="Send a payment reminder email."
)
async def send_payment_reminder(
    request: PaymentReminderRequest,
    current_user: User = Depends(require_admin_access)
):
    """Send payment reminder email"""
    try:
        payment_details = {
            "amount": request.amount,
            "due_date": request.due_date,
            "description": request.description
        }
        
        result = await email_service.send_payment_reminder(
            user_email=request.user_email,
            user_name=request.user_name,
            payment_details=payment_details
        )
        
        if result["success"]:
            return EmailResponse(
                success=True,
                message="Payment reminder sent successfully",
                tracking_id=result.get("tracking_id")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to send payment reminder")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending payment reminder: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error sending payment reminder"
        )

@router.post(
    "/send/class-reminder",
    response_model=EmailResponse,
    summary="Send class reminder",
    description="Send a class reminder email."
)
async def send_class_reminder(
    request: ClassReminderRequest,
    current_user: User = Depends(require_admin_access)
):
    """Send class reminder email"""
    try:
        class_details = {
            "name": request.class_name,
            "date": request.class_date,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "instructor": request.instructor_name,
            "location": request.location,
            "id": request.class_id
        }
        
        result = await email_service.send_class_reminder(
            user_email=request.user_email,
            user_name=request.user_name,
            class_details=class_details
        )
        
        if result["success"]:
            return EmailResponse(
                success=True,
                message="Class reminder sent successfully",
                tracking_id=result.get("tracking_id")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to send class reminder")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending class reminder: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error sending class reminder"
        )

@router.post(
    "/templates",
    summary="Create email template",
    description="Create or update an email template. Requires admin privileges."
)
async def create_email_template(
    request: EmailTemplateRequest,
    current_user: User = Depends(require_admin_access)
):
    """Create email template"""
    try:
        template = EmailTemplate(
            name=request.name,
            subject=request.subject,
            html_content=request.html_content,
            text_content=request.text_content,
            variables=request.variables,
            category=EmailType(request.category.value),
            description=request.description
        )
        
        success = await email_service.create_template(template)
        
        if success:
            return {
                "success": True,
                "message": "Template created successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to create template"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error creating template"
        )

@router.get(
    "/templates/{template_name}",
    summary="Get email template",
    description="Get an email template by name."
)
async def get_email_template(
    template_name: str = Path(..., description="Template name"),
    current_user: User = Depends(get_current_user)
):
    """Get email template"""
    try:
        template = await email_service.get_template(template_name)
        
        if template:
            return {
                "name": template.name,
                "subject": template.subject,
                "html_content": template.html_content,
                "text_content": template.text_content,
                "variables": template.variables,
                "category": template.category.value,
                "description": template.description
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Template not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving template"
        )

@router.get(
    "/statistics",
    response_model=EmailStatisticsResponse,
    summary="Get email statistics",
    description="Get comprehensive email statistics. Requires admin privileges."
)
async def get_email_statistics(
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
    """Get email statistics"""
    try:
        stats = await email_service.get_email_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return EmailStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting email statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving statistics"
        )

@router.get(
    "/track/open/{tracking_id}",
    summary="Track email open",
    description="Track when an email is opened (tracking pixel endpoint)."
)
async def track_email_open(
    tracking_id: str = Path(..., description="Email tracking ID")
):
    """Track email open event"""
    try:
        # Update email log with open timestamp
        db = next(get_db())
        from ...services.email_service import EmailLogModel
        
        email_log = db.query(EmailLogModel).filter(
            EmailLogModel.tracking_id == tracking_id
        ).first()
        
        if email_log and not email_log.opened_at:
            email_log.opened_at = datetime.utcnow()
            email_log.status = EmailStatus.DELIVERED.value
            db.commit()
        
        # Return 1x1 transparent pixel
        pixel_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        
        return Response(
            content=pixel_data,
            media_type="image/png",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        logger.error(f"Error tracking email open: {e}")
        # Still return pixel even if tracking fails
        pixel_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        return Response(content=pixel_data, media_type="image/png")
    finally:
        db.close()

@router.get(
    "/test",
    summary="Send test email",
    description="Send a test email to the current user."
)
async def send_test_email(
    current_user: User = Depends(get_current_user)
):
    """Send test email to current user"""
    try:
        message = EmailMessage(
            to=current_user.email,
            subject="Test Email from Gym Management System",
            html_content="""
            <html>
            <body>
                <h2>Test Email</h2>
                <p>Hello {name}!</p>
                <p>This is a test email from the Gym Management System.</p>
                <p>If you received this email, the email service is working correctly.</p>
                <p>Timestamp: {timestamp}</p>
            </body>
            </html>
            """.format(
                name=current_user.first_name or current_user.email,
                timestamp=datetime.utcnow().isoformat()
            ),
            text_content=f"""
            Test Email
            
            Hello {current_user.first_name or current_user.email}!
            
            This is a test email from the Gym Management System.
            If you received this email, the email service is working correctly.
            
            Timestamp: {datetime.utcnow().isoformat()}
            """,
            email_type=EmailType.SYSTEM,
            priority=EmailPriority.NORMAL
        )
        
        result = await email_service.send_email(message)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Test email sent successfully",
                "tracking_id": result.get("tracking_id")
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to send test email")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error sending test email"
        )

@router.get(
    "/templates",
    summary="List email templates",
    description="Get list of available email templates."
)
async def list_email_templates(
    category: Optional[EmailTypeEnum] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user)
):
    """List email templates"""
    try:
        db = next(get_db())
        from ...services.email_service import EmailTemplateModel
        
        query = db.query(EmailTemplateModel).filter(
            EmailTemplateModel.is_active == True
        )
        
        if category:
            query = query.filter(EmailTemplateModel.category == category.value)
        
        templates = query.all()
        
        return {
            "templates": [
                {
                    "id": template.id,
                    "name": template.name,
                    "subject": template.subject,
                    "category": template.category,
                    "description": template.description,
                    "variables": template.variables or [],
                    "created_at": template.created_at.isoformat(),
                    "updated_at": template.updated_at.isoformat()
                }
                for template in templates
            ],
            "total_count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving templates"
        )
    finally:
        db.close()

@router.get(
    "/config",
    summary="Get email configuration",
    description="Get current email service configuration. Requires admin privileges."
)
async def get_email_config(
    current_user: User = Depends(require_admin_access)
):
    """Get email configuration"""
    try:
        return {
            "smtp_server": email_service.smtp_server,
            "smtp_port": email_service.smtp_port,
            "use_tls": email_service.use_tls,
            "from_email": email_service.from_email,
            "from_name": email_service.from_name,
            "tracking_domain": email_service.tracking_domain,
            "is_configured": email_service._is_configured(),
            "templates_directory": str(email_service.templates_dir)
        }
        
    except Exception as e:
        logger.error(f"Error getting email config: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving email configuration"
        )