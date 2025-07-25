from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.sql import func
from ..core.database import Base
import enum
from datetime import datetime

class Configuration(Base):
    """System configuration model"""
    __tablename__ = "configurations"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Gym basic information
    gym_name = Column(String(200), nullable=False, default="Mi Gimnasio")
    gym_description = Column(Text, nullable=True)
    gym_logo_url = Column(String(500), nullable=True)
    
    # Contact information
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Social media
    instagram_url = Column(String(200), nullable=True)
    facebook_url = Column(String(200), nullable=True)
    twitter_url = Column(String(200), nullable=True)
    youtube_url = Column(String(200), nullable=True)
    
    # Operating hours (JSON format)
    operating_hours = Column(JSON, nullable=True)  # {"monday": {"open": "06:00", "close": "22:00"}, ...}
    
    # Membership settings
    default_membership_duration = Column(Integer, default=30)  # days
    allow_membership_freeze = Column(Boolean, default=True)
    max_freeze_days = Column(Integer, default=30)
    
    # Payment settings
    currency = Column(String(3), default="USD")
    tax_rate = Column(Float, default=0.0)
    late_payment_fee = Column(Float, default=0.0)
    payment_grace_period = Column(Integer, default=5)  # days
    
    # Class settings
    max_class_capacity = Column(Integer, default=20)
    allow_class_waitlist = Column(Boolean, default=True)
    class_cancellation_hours = Column(Integer, default=2)  # hours before class
    
    # Notification settings
    enable_email_notifications = Column(Boolean, default=True)
    enable_sms_notifications = Column(Boolean, default=False)
    enable_whatsapp_notifications = Column(Boolean, default=False)
    
    # WhatsApp integration
    whatsapp_api_token = Column(String(500), nullable=True)
    whatsapp_phone_number = Column(String(20), nullable=True)
    whatsapp_business_account_id = Column(String(100), nullable=True)
    
    # Instagram integration
    instagram_access_token = Column(String(500), nullable=True)
    instagram_business_account_id = Column(String(100), nullable=True)
    
    # Theme and branding
    primary_color = Column(String(7), default="#3B82F6")  # Blue
    secondary_color = Column(String(7), default="#10B981")  # Green
    accent_color = Column(String(7), default="#F59E0B")  # Amber
    
    # UI settings
    theme_mode = Column(String(10), default="light")  # light, dark, auto
    language = Column(String(5), default="es")  # es, en
    timezone = Column(String(50), default="America/Mexico_City")
    
    # Security settings
    session_timeout = Column(Integer, default=480)  # minutes
    password_min_length = Column(Integer, default=8)
    require_password_complexity = Column(Boolean, default=True)
    max_login_attempts = Column(Integer, default=5)
    
    # Backup settings
    auto_backup_enabled = Column(Boolean, default=True)
    backup_frequency = Column(String(20), default="daily")  # daily, weekly, monthly
    backup_retention_days = Column(Integer, default=30)
    
    # Feature flags
    enable_member_app = Column(Boolean, default=True)
    enable_online_payments = Column(Boolean, default=False)
    enable_class_booking = Column(Boolean, default=True)
    enable_personal_training = Column(Boolean, default=True)
    enable_nutrition_tracking = Column(Boolean, default=False)
    enable_progress_photos = Column(Boolean, default=True)
    
    # Custom fields configuration (JSON)
    custom_member_fields = Column(JSON, nullable=True)
    custom_class_fields = Column(JSON, nullable=True)
    custom_payment_fields = Column(JSON, nullable=True)
    
    # Terms and policies
    terms_of_service = Column(Text, nullable=True)
    privacy_policy = Column(Text, nullable=True)
    cancellation_policy = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Configuration(id={self.id}, gym_name='{self.gym_name}')>"
    
    @property
    def is_whatsapp_configured(self):
        """Check if WhatsApp integration is configured"""
        return (self.whatsapp_api_token and 
                self.whatsapp_phone_number and 
                self.enable_whatsapp_notifications)
    
    @property
    def is_instagram_configured(self):
        """Check if Instagram integration is configured"""
        return (self.instagram_access_token and 
                self.instagram_business_account_id)
    
    @property
    def formatted_operating_hours(self):
        """Get formatted operating hours"""
        if not self.operating_hours:
            return "No configurado"
        
        days = {
            'monday': 'Lunes',
            'tuesday': 'Martes', 
            'wednesday': 'Miércoles',
            'thursday': 'Jueves',
            'friday': 'Viernes',
            'saturday': 'Sábado',
            'sunday': 'Domingo'
        }
        
        formatted = []
        for day, hours in self.operating_hours.items():
            if hours.get('open') and hours.get('close'):
                formatted.append(f"{days.get(day, day)}: {hours['open']} - {hours['close']}")
        
        return "\n".join(formatted)
    
    @classmethod
    def get_default_config(cls):
        """Get default configuration"""
        return {
            'gym_name': 'Mi Gimnasio',
            'currency': 'USD',
            'language': 'es',
            'timezone': 'America/Mexico_City',
            'theme_mode': 'light',
            'primary_color': '#3B82F6',
            'secondary_color': '#10B981',
            'accent_color': '#F59E0B',
            'operating_hours': {
                'monday': {'open': '06:00', 'close': '22:00'},
                'tuesday': {'open': '06:00', 'close': '22:00'},
                'wednesday': {'open': '06:00', 'close': '22:00'},
                'thursday': {'open': '06:00', 'close': '22:00'},
                'friday': {'open': '06:00', 'close': '22:00'},
                'saturday': {'open': '08:00', 'close': '20:00'},
                'sunday': {'open': '08:00', 'close': '18:00'}
            }
        }

class NotificationTemplate(Base):
    """Notification templates for automated messages"""
    __tablename__ = "notification_templates"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Template details
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # email, sms, whatsapp
    event = Column(String(100), nullable=False)  # membership_expiry, class_reminder, etc.
    
    # Content
    subject = Column(String(200), nullable=True)  # For email
    message = Column(Text, nullable=False)
    
    # Settings
    is_active = Column(Boolean, default=True)
    send_hours_before = Column(Integer, nullable=True)  # For reminders
    
    # Variables available (JSON)
    available_variables = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationTemplate(id={self.id}, name='{self.name}', type='{self.type}')>"
    
    @property
    def formatted_message(self):
        """Get message with variable placeholders"""
        return self.message.replace('{{', '{').replace('}}', '}')
    
    @classmethod
    def get_default_templates(cls):
        """Get default notification templates"""
        return [
            {
                'name': 'Bienvenida Nuevo Miembro',
                'type': 'whatsapp',
                'event': 'member_welcome',
                'message': '¡Hola {{name}}! 👋 Bienvenido/a a {{gym_name}}. Tu membresía está activa hasta {{expiry_date}}. ¡Nos vemos en el gym! 💪',
                'available_variables': ['name', 'gym_name', 'expiry_date']
            },
            {
                'name': 'Recordatorio Vencimiento',
                'type': 'whatsapp', 
                'event': 'membership_expiry_reminder',
                'message': 'Hola {{name}}, tu membresía en {{gym_name}} vence el {{expiry_date}}. ¡Renueva para seguir entrenando! 🏋️‍♂️',
                'send_hours_before': 72,
                'available_variables': ['name', 'gym_name', 'expiry_date']
            },
            {
                'name': 'Recordatorio de Clase',
                'type': 'whatsapp',
                'event': 'class_reminder',
                'message': '¡Hola {{name}}! Te recordamos tu clase de {{class_name}} hoy a las {{class_time}}. ¡Te esperamos! 🧘‍♀️',
                'send_hours_before': 2,
                'available_variables': ['name', 'class_name', 'class_time', 'trainer_name']
            }
        ]

class SystemLog(Base):
    """System activity logs"""
    __tablename__ = "system_logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Log details
    level = Column(String(10), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    category = Column(String(50), nullable=False)  # auth, payment, notification, etc.
    message = Column(Text, nullable=False)
    
    # Context
    user_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Additional data (JSON)
    extra_data = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level='{self.level}', category='{self.category}')>"
    
    @classmethod
    def log_info(cls, category, message, user_id=None, extra_data=None):
        """Create info log entry"""
        return cls(
            level="INFO",
            category=category,
            message=message,
            user_id=user_id,
            extra_data=extra_data
        )
    
    @classmethod
    def log_error(cls, category, message, user_id=None, extra_data=None):
        """Create error log entry"""
        return cls(
            level="ERROR",
            category=category,
            message=message,
            user_id=user_id,
            extra_data=extra_data
        )