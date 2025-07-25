from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import ssl
import asyncio
import aiofiles
import jinja2
from pathlib import Path
import logging
from enum import Enum
import json
import base64
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from ..core.database import Base, get_db
from ..core.config import settings
from .config_service import get_config_service
import os

logger = logging.getLogger(__name__)

class EmailPriority(Enum):
    """Email priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EmailStatus(Enum):
    """Email delivery status"""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"

class EmailType(Enum):
    """Email types for categorization"""
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

@dataclass
class EmailAttachment:
    """Email attachment data"""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"
    content_id: Optional[str] = None  # For inline attachments

@dataclass
class EmailTemplate:
    """Email template data"""
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    variables: List[str] = field(default_factory=list)
    category: EmailType = EmailType.CUSTOM
    description: Optional[str] = None

@dataclass
class EmailMessage:
    """Email message data"""
    to: Union[str, List[str]]
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    cc: Optional[Union[str, List[str]]] = None
    bcc: Optional[Union[str, List[str]]] = None
    reply_to: Optional[str] = None
    attachments: List[EmailAttachment] = field(default_factory=list)
    priority: EmailPriority = EmailPriority.NORMAL
    email_type: EmailType = EmailType.CUSTOM
    template_variables: Optional[Dict[str, Any]] = None
    tracking_enabled: bool = True
    scheduled_at: Optional[datetime] = None

class EmailLogModel(Base):
    """Email log database model"""
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    to_email = Column(String(255), nullable=False, index=True)
    cc_emails = Column(JSON, nullable=True)
    bcc_emails = Column(JSON, nullable=True)
    subject = Column(String(500), nullable=False)
    email_type = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    tracking_id = Column(String(100), unique=True, index=True)
    template_name = Column(String(100), nullable=True)
    email_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailTemplateModel(Base):
    """Email template database model"""
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailService:
    """Advanced email service with templates, tracking, and bulk sending"""
    
    def __init__(self):
        self.smtp_server = None
        self.smtp_port = None
        self.smtp_username = None
        self.smtp_password = None
        self.use_tls = True
        self.from_email = None
        self.from_name = None
        self.template_env = None
        self.templates_dir = Path("templates/email")
        self.tracking_domain = None
        self.max_retries = 3
        self.retry_delay = 60  # seconds
        self._initialize_config()
        self._setup_templates()
    
    def _initialize_config(self):
        """Initialize email configuration from settings and config service"""
        try:
            # Get email configuration
            email_config = get_config_service().get_category_configs("email")
            
            self.smtp_server = email_config.get("smtp_server", settings.SMTP_HOST)
            self.smtp_port = int(email_config.get("smtp_port", settings.SMTP_PORT or 587))
            self.smtp_username = email_config.get("smtp_username", settings.SMTP_USER)
            self.smtp_password = email_config.get("smtp_password", settings.SMTP_PASSWORD)
            self.use_tls = email_config.get("use_tls", settings.SMTP_TLS)
            self.from_email = email_config.get("from_email", settings.GYM_EMAIL or "noreply@gymsystem.com")
            self.from_name = email_config.get("from_name", settings.GYM_NAME or "Gym Management System")
            self.tracking_domain = email_config.get("tracking_domain", settings.GYM_WEBSITE or "localhost")
            
        except Exception as e:
            logger.warning(f"Failed to load email config: {e}")
            # Fallback to environment variables
            self.smtp_server = settings.SMTP_HOST
            self.smtp_port = settings.SMTP_PORT or 587
            self.smtp_username = settings.SMTP_USER
            self.smtp_password = settings.SMTP_PASSWORD
            self.from_email = settings.GYM_EMAIL or "noreply@gymsystem.com"
            self.from_name = settings.GYM_NAME or "Gym Management System"
    
    def _setup_templates(self):
        """Setup Jinja2 template environment"""
        try:
            # Create templates directory if it doesn't exist
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            
            # Setup Jinja2 environment
            self.template_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(self.templates_dir)),
                autoescape=jinja2.select_autoescape(['html', 'xml'])
            )
            
            # Create default templates if they don't exist
            self._create_default_templates()
            
        except Exception as e:
            logger.error(f"Failed to setup email templates: {e}")
    
    def _create_default_templates(self):
        """Create default email templates"""
        default_templates = {
            "welcome.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome to {{ gym_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .footer { padding: 20px; text-align: center; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to {{ gym_name }}!</h1>
        </div>
        <div class="content">
            <h2>Hello {{ first_name }}!</h2>
            <p>Welcome to our fitness community! We're excited to have you join us on your fitness journey.</p>
            <p>Your membership details:</p>
            <ul>
                <li><strong>Membership Type:</strong> {{ membership_type }}</li>
                <li><strong>Start Date:</strong> {{ start_date }}</li>
                <li><strong>Member ID:</strong> {{ member_id }}</li>
            </ul>
            <p>Get started by exploring our facilities and booking your first class!</p>
            <a href="{{ dashboard_url }}" class="button">Go to Dashboard</a>
        </div>
        <div class="footer">
            <p>{{ gym_name }} | {{ gym_address }} | {{ gym_phone }}</p>
        </div>
    </div>
</body>
</html>
            """,
            
            "payment_reminder.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Payment Reminder</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #dc3545; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .footer { padding: 20px; text-align: center; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; }
        .amount { font-size: 24px; font-weight: bold; color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Payment Reminder</h1>
        </div>
        <div class="content">
            <h2>Hello {{ first_name }},</h2>
            <p>This is a friendly reminder that your payment is due.</p>
            <p><strong>Amount Due:</strong> <span class="amount">${{ amount }}</span></p>
            <p><strong>Due Date:</strong> {{ due_date }}</p>
            <p><strong>Description:</strong> {{ description }}</p>
            <p>Please make your payment as soon as possible to avoid any service interruption.</p>
            <a href="{{ payment_url }}" class="button">Pay Now</a>
        </div>
        <div class="footer">
            <p>{{ gym_name }} | {{ gym_address }} | {{ gym_phone }}</p>
        </div>
    </div>
</body>
</html>
            """,
            
            "class_reminder.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Class Reminder</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #28a745; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .footer { padding: 20px; text-align: center; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; }
        .class-info { background: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Class Reminder</h1>
        </div>
        <div class="content">
            <h2>Hello {{ first_name }},</h2>
            <p>Don't forget about your upcoming class!</p>
            <div class="class-info">
                <h3>{{ class_name }}</h3>
                <p><strong>Date:</strong> {{ class_date }}</p>
                <p><strong>Time:</strong> {{ start_time }} - {{ end_time }}</p>
                <p><strong>Instructor:</strong> {{ instructor_name }}</p>
                <p><strong>Location:</strong> {{ location }}</p>
            </div>
            <p>We look forward to seeing you there!</p>
            <a href="{{ class_url }}" class="button">View Class Details</a>
        </div>
        <div class="footer">
            <p>{{ gym_name }} | {{ gym_address }} | {{ gym_phone }}</p>
        </div>
    </div>
</body>
</html>
            """
        }
        
        for filename, content in default_templates.items():
            template_path = self.templates_dir / filename
            if not template_path.exists():
                try:
                    template_path.write_text(content, encoding='utf-8')
                    logger.info(f"Created default template: {filename}")
                except Exception as e:
                    logger.error(f"Failed to create template {filename}: {e}")
    
    async def send_email(self, message: EmailMessage) -> Dict[str, Any]:
        """Send a single email"""
        try:
            # Validate configuration
            if not self._is_configured():
                return {
                    "success": False,
                    "error": "Email service not configured"
                }
            
            # Generate tracking ID
            tracking_id = self._generate_tracking_id()
            
            # Create MIME message
            mime_message = await self._create_mime_message(message, tracking_id)
            
            # Send email
            await self._send_smtp_email(mime_message, message.to)
            
            # Log email
            await self._log_email(message, tracking_id, EmailStatus.SENT)
            
            return {
                "success": True,
                "tracking_id": tracking_id,
                "message": "Email sent successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            await self._log_email(message, tracking_id if 'tracking_id' in locals() else None, 
                                EmailStatus.FAILED, str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_bulk_emails(self, messages: List[EmailMessage], 
                             batch_size: int = 50) -> Dict[str, Any]:
        """Send multiple emails in batches"""
        results = {
            "total": len(messages),
            "sent": 0,
            "failed": 0,
            "errors": []
        }
        
        # Process in batches
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            
            # Send batch concurrently
            tasks = [self.send_email(message) for message in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results["failed"] += 1
                    results["errors"].append({
                        "index": i + j,
                        "error": str(result)
                    })
                elif result.get("success"):
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "index": i + j,
                        "error": result.get("error", "Unknown error")
                    })
            
            # Add delay between batches to avoid rate limiting
            if i + batch_size < len(messages):
                await asyncio.sleep(1)
        
        return results
    
    async def send_template_email(self, template_name: str, to: Union[str, List[str]], 
                                variables: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Send email using a template"""
        try:
            # Get template
            template = await self.get_template(template_name)
            if not template:
                return {
                    "success": False,
                    "error": f"Template '{template_name}' not found"
                }
            
            # Render template
            rendered = await self._render_template(template, variables)
            
            # Create message
            message = EmailMessage(
                to=to,
                subject=rendered["subject"],
                html_content=rendered["html_content"],
                text_content=rendered.get("text_content"),
                email_type=template.category,
                template_variables=variables,
                **kwargs
            )
            
            # Send email
            return await self.send_email(message)
            
        except Exception as e:
            logger.error(f"Failed to send template email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_template(self, template: EmailTemplate) -> bool:
        """Create or update an email template"""
        try:
            db = next(get_db())
            
            # Check if template exists
            existing = db.query(EmailTemplateModel).filter(
                EmailTemplateModel.name == template.name
            ).first()
            
            if existing:
                # Update existing template
                existing.subject = template.subject
                existing.html_content = template.html_content
                existing.text_content = template.text_content
                existing.variables = template.variables
                existing.category = template.category.value
                existing.description = template.description
                existing.updated_at = datetime.utcnow()
            else:
                # Create new template
                new_template = EmailTemplateModel(
                    name=template.name,
                    subject=template.subject,
                    html_content=template.html_content,
                    text_content=template.text_content,
                    variables=template.variables,
                    category=template.category.value,
                    description=template.description
                )
                db.add(new_template)
            
            db.commit()
            
            # Save template file
            template_path = self.templates_dir / f"{template.name}.html"
            template_path.write_text(template.html_content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return False
        finally:
            db.close()
    
    async def get_template(self, name: str) -> Optional[EmailTemplate]:
        """Get email template by name"""
        try:
            db = next(get_db())
            
            template_model = db.query(EmailTemplateModel).filter(
                EmailTemplateModel.name == name,
                EmailTemplateModel.is_active == True
            ).first()
            
            if template_model:
                return EmailTemplate(
                    name=template_model.name,
                    subject=template_model.subject,
                    html_content=template_model.html_content,
                    text_content=template_model.text_content,
                    variables=template_model.variables or [],
                    category=EmailType(template_model.category),
                    description=template_model.description
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get template: {e}")
            return None
        finally:
            db.close()
    
    async def get_email_statistics(self, start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get email statistics"""
        try:
            db = next(get_db())
            
            # Build query
            query = db.query(EmailLogModel)
            
            if start_date:
                query = query.filter(EmailLogModel.created_at >= start_date)
            if end_date:
                query = query.filter(EmailLogModel.created_at <= end_date)
            
            # Get total counts
            total_emails = query.count()
            sent_emails = query.filter(EmailLogModel.status == EmailStatus.SENT.value).count()
            failed_emails = query.filter(EmailLogModel.status == EmailStatus.FAILED.value).count()
            delivered_emails = query.filter(EmailLogModel.status == EmailStatus.DELIVERED.value).count()
            opened_emails = query.filter(EmailLogModel.opened_at.isnot(None)).count()
            clicked_emails = query.filter(EmailLogModel.clicked_at.isnot(None)).count()
            
            # Calculate rates
            success_rate = (sent_emails / total_emails * 100) if total_emails > 0 else 0
            delivery_rate = (delivered_emails / sent_emails * 100) if sent_emails > 0 else 0
            open_rate = (opened_emails / delivered_emails * 100) if delivered_emails > 0 else 0
            click_rate = (clicked_emails / delivered_emails * 100) if delivered_emails > 0 else 0
            
            # Get statistics by type
            type_stats = {}
            for email_type in EmailType:
                type_count = query.filter(EmailLogModel.email_type == email_type.value).count()
                if type_count > 0:
                    type_stats[email_type.value] = type_count
            
            return {
                "total_emails": total_emails,
                "sent_emails": sent_emails,
                "failed_emails": failed_emails,
                "delivered_emails": delivered_emails,
                "opened_emails": opened_emails,
                "clicked_emails": clicked_emails,
                "success_rate": round(success_rate, 2),
                "delivery_rate": round(delivery_rate, 2),
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "type_statistics": type_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get email statistics: {e}")
            return {}
        finally:
            db.close()
    
    def _is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return all([
            self.smtp_server,
            self.smtp_port,
            self.smtp_username,
            self.smtp_password,
            self.from_email
        ])
    
    def _generate_tracking_id(self) -> str:
        """Generate unique tracking ID for email"""
        import uuid
        return str(uuid.uuid4())
    
    async def _create_mime_message(self, message: EmailMessage, tracking_id: str) -> MIMEMultipart:
        """Create MIME message from EmailMessage"""
        mime_message = MIMEMultipart('alternative')
        
        # Set headers
        mime_message['From'] = f"{self.from_name} <{self.from_email}>"
        mime_message['To'] = message.to if isinstance(message.to, str) else ', '.join(message.to)
        mime_message['Subject'] = message.subject
        
        if message.cc:
            mime_message['Cc'] = message.cc if isinstance(message.cc, str) else ', '.join(message.cc)
        
        if message.reply_to:
            mime_message['Reply-To'] = message.reply_to
        
        # Set priority
        if message.priority == EmailPriority.HIGH:
            mime_message['X-Priority'] = '2'
            mime_message['X-MSMail-Priority'] = 'High'
        elif message.priority == EmailPriority.URGENT:
            mime_message['X-Priority'] = '1'
            mime_message['X-MSMail-Priority'] = 'High'
        
        # Add tracking pixel to HTML content
        html_content = message.html_content
        if html_content and message.tracking_enabled and self.tracking_domain:
            tracking_pixel = f'<img src="https://{self.tracking_domain}/api/v1/email/track/open/{tracking_id}" width="1" height="1" style="display:none;">'
            html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
        
        # Add text content
        if message.text_content:
            text_part = MIMEText(message.text_content, 'plain', 'utf-8')
            mime_message.attach(text_part)
        
        # Add HTML content
        if html_content:
            html_part = MIMEText(html_content, 'html', 'utf-8')
            mime_message.attach(html_part)
        
        # Add attachments
        for attachment in message.attachments:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.content)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment.filename}'
            )
            if attachment.content_id:
                part.add_header('Content-ID', f'<{attachment.content_id}>')
            mime_message.attach(part)
        
        return mime_message
    
    async def _send_smtp_email(self, mime_message: MIMEMultipart, to_addresses: Union[str, List[str]]):
        """Send email via SMTP"""
        # Convert to list if string
        if isinstance(to_addresses, str):
            to_addresses = [to_addresses]
        
        # Create SMTP connection
        if self.use_tls:
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls(context=context)
        else:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        
        try:
            # Login and send
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(mime_message, to_addrs=to_addresses)
        finally:
            server.quit()
    
    async def _render_template(self, template: EmailTemplate, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render email template with variables"""
        try:
            # Render subject
            subject_template = self.template_env.from_string(template.subject)
            rendered_subject = subject_template.render(**variables)
            
            # Render HTML content
            html_template = self.template_env.from_string(template.html_content)
            rendered_html = html_template.render(**variables)
            
            # Render text content if available
            rendered_text = None
            if template.text_content:
                text_template = self.template_env.from_string(template.text_content)
                rendered_text = text_template.render(**variables)
            
            return {
                "subject": rendered_subject,
                "html_content": rendered_html,
                "text_content": rendered_text
            }
            
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            raise
    
    async def _log_email(self, message: EmailMessage, tracking_id: Optional[str], 
                        status: EmailStatus, error_message: Optional[str] = None):
        """Log email to database"""
        try:
            db = next(get_db())
            
            # Convert recipients to list
            to_list = message.to if isinstance(message.to, list) else [message.to]
            cc_list = message.cc if isinstance(message.cc, list) else ([message.cc] if message.cc else None)
            bcc_list = message.bcc if isinstance(message.bcc, list) else ([message.bcc] if message.bcc else None)
            
            # Create log entry for each recipient
            for to_email in to_list:
                log_entry = EmailLogModel(
                    to_email=to_email,
                    cc_emails=cc_list,
                    bcc_emails=bcc_list,
                    subject=message.subject,
                    email_type=message.email_type.value,
                    priority=message.priority.value,
                    status=status.value,
                    error_message=error_message,
                    tracking_id=tracking_id,
                    email_metadata={
                        "template_variables": message.template_variables,
                        "tracking_enabled": message.tracking_enabled,
                        "scheduled_at": message.scheduled_at.isoformat() if message.scheduled_at else None
                    }
                )
                
                if status == EmailStatus.SENT:
                    log_entry.sent_at = datetime.utcnow()
                
                db.add(log_entry)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log email: {e}")
        finally:
            db.close()
    
    # Convenience methods for common email types
    async def send_welcome_email(self, user_email: str, user_name: str, 
                               membership_details: Dict[str, Any]) -> Dict[str, Any]:
        """Send welcome email to new member"""
        variables = {
            "first_name": user_name,
            "gym_name": get_config_service().get_config("business_name", "Gym Management System"),
            "membership_type": membership_details.get("type", "Standard"),
            "start_date": membership_details.get("start_date", datetime.now().strftime("%Y-%m-%d")),
            "member_id": membership_details.get("member_id", "N/A"),
            "dashboard_url": f"https://{self.tracking_domain}/dashboard",
            "gym_address": get_config_service().get_config("business_address", ""),
            "gym_phone": get_config_service().get_config("business_phone", "")
        }
        
        return await self.send_template_email(
            template_name="welcome",
            to=user_email,
            variables=variables,
            email_type=EmailType.WELCOME
        )
    
    async def send_payment_reminder(self, user_email: str, user_name: str, 
                                  payment_details: Dict[str, Any]) -> Dict[str, Any]:
        """Send payment reminder email"""
        variables = {
            "first_name": user_name,
            "amount": payment_details.get("amount", "0.00"),
            "due_date": payment_details.get("due_date", ""),
            "description": payment_details.get("description", "Membership fee"),
            "payment_url": f"https://{self.tracking_domain}/payments",
            "gym_name": get_config_service().get_config("business_name", "Gym Management System"),
            "gym_address": get_config_service().get_config("business_address", ""),
            "gym_phone": get_config_service().get_config("business_phone", "")
        }
        
        return await self.send_template_email(
            template_name="payment_reminder",
            to=user_email,
            variables=variables,
            email_type=EmailType.PAYMENT_REMINDER,
            priority=EmailPriority.HIGH
        )
    
    async def send_class_reminder(self, user_email: str, user_name: str, 
                                class_details: Dict[str, Any]) -> Dict[str, Any]:
        """Send class reminder email"""
        variables = {
            "first_name": user_name,
            "class_name": class_details.get("name", ""),
            "class_date": class_details.get("date", ""),
            "start_time": class_details.get("start_time", ""),
            "end_time": class_details.get("end_time", ""),
            "instructor_name": class_details.get("instructor", ""),
            "location": class_details.get("location", ""),
            "class_url": f"https://{self.tracking_domain}/classes/{class_details.get('id', '')}",
            "gym_name": get_config_service().get_config("business_name", "Gym Management System"),
            "gym_address": get_config_service().get_config("business_address", ""),
            "gym_phone": get_config_service().get_config("business_phone", "")
        }
        
        return await self.send_template_email(
            template_name="class_reminder",
            to=user_email,
            variables=variables,
            email_type=EmailType.CLASS_REMINDER
        )

# Global email service instance
email_service = EmailService()