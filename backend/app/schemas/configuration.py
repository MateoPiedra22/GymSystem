from pydantic import BaseModel, validator, Field, EmailStr, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

# Configuration schemas
class ConfigurationBase(BaseModel):
    """Base configuration schema"""
    gym_name: str = Field(..., min_length=1, max_length=200)
    gym_description: Optional[str] = None
    gym_logo_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    operating_hours: Optional[Dict[str, Dict[str, str]]] = None
    default_membership_duration: int = Field(30, ge=1, le=365)
    allow_membership_freeze: bool = True
    max_freeze_days: int = Field(30, ge=1, le=365)
    currency: str = Field("USD", min_length=3, max_length=3)
    tax_rate: float = Field(0.0, ge=0, le=1)
    late_payment_fee: float = Field(0.0, ge=0)
    payment_grace_period: int = Field(5, ge=0, le=30)
    max_class_capacity: int = Field(20, ge=1, le=200)
    allow_class_waitlist: bool = True
    class_cancellation_hours: int = Field(2, ge=0, le=48)
    enable_email_notifications: bool = True
    enable_sms_notifications: bool = False
    enable_whatsapp_notifications: bool = False
    whatsapp_api_token: Optional[str] = None
    whatsapp_phone_number: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None
    instagram_access_token: Optional[str] = None
    instagram_business_account_id: Optional[str] = None
    primary_color: str = Field("#3B82F6", pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: str = Field("#10B981", pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: str = Field("#F59E0B", pattern=r'^#[0-9A-Fa-f]{6}$')
    theme_mode: str = Field("light", pattern=r'^(light|dark|auto)$')
    language: str = Field("es", pattern=r'^(es|en)$')
    timezone: str = Field("America/Mexico_City", min_length=1)
    session_timeout: int = Field(480, ge=30, le=1440)
    password_min_length: int = Field(8, ge=6, le=20)
    require_password_complexity: bool = True
    max_login_attempts: int = Field(5, ge=3, le=10)
    auto_backup_enabled: bool = True
    backup_frequency: str = Field("daily", pattern=r'^(daily|weekly|monthly)$')
    backup_retention_days: int = Field(30, ge=7, le=365)
    enable_member_app: bool = True
    enable_online_payments: bool = False
    enable_class_booking: bool = True
    enable_personal_training: bool = True
    enable_nutrition_tracking: bool = False
    enable_progress_photos: bool = True
    custom_member_fields: Optional[Dict[str, Any]] = None
    custom_class_fields: Optional[Dict[str, Any]] = None
    custom_payment_fields: Optional[Dict[str, Any]] = None
    terms_of_service: Optional[str] = None
    privacy_policy: Optional[str] = None
    cancellation_policy: Optional[str] = None
    
    @validator('gym_name')
    def validate_gym_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Gym name cannot be empty')
        return v.strip()
    
    @validator('currency')
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError('Currency must be a 3-letter code')
        return v.upper()
    
    @validator('tax_rate')
    def validate_tax_rate(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Tax rate must be between 0 and 1')
        return v
    
    @validator('operating_hours')
    def validate_operating_hours(cls, v):
        if v:
            valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day, hours in v.items():
                if day not in valid_days:
                    raise ValueError(f'Invalid day: {day}')
                if not isinstance(hours, dict) or 'open' not in hours or 'close' not in hours:
                    raise ValueError(f'Invalid hours format for {day}')
        return v
    
    @validator('primary_color', 'secondary_color', 'accent_color')
    def validate_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be in hex format (#RRGGBB)')
        return v.upper()

class ConfigurationCreate(ConfigurationBase):
    """Schema for creating configuration"""
    pass

class ConfigurationUpdate(BaseModel):
    """Schema for updating configuration"""
    gym_name: Optional[str] = None
    gym_description: Optional[str] = None
    gym_logo_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    operating_hours: Optional[Dict[str, Dict[str, str]]] = None
    default_membership_duration: Optional[int] = Field(None, ge=1, le=365)
    allow_membership_freeze: Optional[bool] = None
    max_freeze_days: Optional[int] = Field(None, ge=1, le=365)
    currency: Optional[str] = None
    tax_rate: Optional[float] = Field(None, ge=0, le=1)
    late_payment_fee: Optional[float] = Field(None, ge=0)
    payment_grace_period: Optional[int] = Field(None, ge=0, le=30)
    max_class_capacity: Optional[int] = Field(None, ge=1, le=200)
    allow_class_waitlist: Optional[bool] = None
    class_cancellation_hours: Optional[int] = Field(None, ge=0, le=48)
    enable_email_notifications: Optional[bool] = None
    enable_sms_notifications: Optional[bool] = None
    enable_whatsapp_notifications: Optional[bool] = None
    whatsapp_api_token: Optional[str] = None
    whatsapp_phone_number: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None
    instagram_access_token: Optional[str] = None
    instagram_business_account_id: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    theme_mode: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    session_timeout: Optional[int] = Field(None, ge=30, le=1440)
    password_min_length: Optional[int] = Field(None, ge=6, le=20)
    require_password_complexity: Optional[bool] = None
    max_login_attempts: Optional[int] = Field(None, ge=3, le=10)
    auto_backup_enabled: Optional[bool] = None
    backup_frequency: Optional[str] = None
    backup_retention_days: Optional[int] = Field(None, ge=7, le=365)
    enable_member_app: Optional[bool] = None
    enable_online_payments: Optional[bool] = None
    enable_class_booking: Optional[bool] = None
    enable_personal_training: Optional[bool] = None
    enable_nutrition_tracking: Optional[bool] = None
    enable_progress_photos: Optional[bool] = None
    custom_member_fields: Optional[Dict[str, Any]] = None
    custom_class_fields: Optional[Dict[str, Any]] = None
    custom_payment_fields: Optional[Dict[str, Any]] = None
    terms_of_service: Optional[str] = None
    privacy_policy: Optional[str] = None
    cancellation_policy: Optional[str] = None

class ConfigurationResponse(BaseModel):
    """Schema for configuration response"""
    id: int
    gym_name: str
    gym_description: Optional[str]
    gym_logo_url: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    instagram_url: Optional[str]
    facebook_url: Optional[str]
    twitter_url: Optional[str]
    youtube_url: Optional[str]
    operating_hours: Optional[Dict[str, Dict[str, str]]]
    default_membership_duration: int
    allow_membership_freeze: bool
    max_freeze_days: int
    currency: str
    tax_rate: float
    late_payment_fee: float
    payment_grace_period: int
    max_class_capacity: int
    allow_class_waitlist: bool
    class_cancellation_hours: int
    enable_email_notifications: bool
    enable_sms_notifications: bool
    enable_whatsapp_notifications: bool
    whatsapp_api_token: Optional[str]
    whatsapp_phone_number: Optional[str]
    whatsapp_business_account_id: Optional[str]
    instagram_access_token: Optional[str]
    instagram_business_account_id: Optional[str]
    primary_color: str
    secondary_color: str
    accent_color: str
    theme_mode: str
    language: str
    timezone: str
    session_timeout: int
    password_min_length: int
    require_password_complexity: bool
    max_login_attempts: int
    auto_backup_enabled: bool
    backup_frequency: str
    backup_retention_days: int
    enable_member_app: bool
    enable_online_payments: bool
    enable_class_booking: bool
    enable_personal_training: bool
    enable_nutrition_tracking: bool
    enable_progress_photos: bool
    custom_member_fields: Optional[Dict[str, Any]]
    custom_class_fields: Optional[Dict[str, Any]]
    custom_payment_fields: Optional[Dict[str, Any]]
    terms_of_service: Optional[str]
    privacy_policy: Optional[str]
    cancellation_policy: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed properties
    is_whatsapp_configured: bool
    is_instagram_configured: bool
    formatted_operating_hours: str
    
    class Config:
        from_attributes = True

# Notification Template schemas
class NotificationTemplateBase(BaseModel):
    """Base notification template schema"""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern=r'^(email|sms|whatsapp)$')
    event: str = Field(..., min_length=1, max_length=100)
    subject: Optional[str] = None
    message: str = Field(..., min_length=1)
    is_active: bool = True
    send_hours_before: Optional[int] = Field(None, ge=0, le=168)
    available_variables: Optional[List[str]] = []
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Template name cannot be empty')
        return v.strip()
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()
    
    @validator('subject')
    def validate_subject(cls, v, values):
        if values.get('type') == 'email' and not v:
            raise ValueError('Subject is required for email templates')
        return v
    
    @validator('available_variables')
    def validate_available_variables(cls, v):
        return v or []

class NotificationTemplateCreate(NotificationTemplateBase):
    """Schema for creating a notification template"""
    pass

class NotificationTemplateUpdate(BaseModel):
    """Schema for updating a notification template"""
    name: Optional[str] = None
    type: Optional[str] = None
    event: Optional[str] = None
    subject: Optional[str] = None
    message: Optional[str] = None
    is_active: Optional[bool] = None
    send_hours_before: Optional[int] = Field(None, ge=0, le=168)
    available_variables: Optional[List[str]] = None

class NotificationTemplateResponse(BaseModel):
    """Schema for notification template response"""
    id: int
    name: str
    type: str
    event: str
    subject: Optional[str]
    message: str
    is_active: bool
    send_hours_before: Optional[int]
    available_variables: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed properties
    formatted_message: str
    
    class Config:
        from_attributes = True

# System settings schemas
class ThemeSettings(BaseModel):
    """Schema for theme settings"""
    primary_color: str = Field(..., pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: str = Field(..., pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: str = Field(..., pattern=r'^#[0-9A-Fa-f]{6}$')
    theme_mode: str = Field(..., pattern=r'^(light|dark|auto)$')
    
    @validator('primary_color', 'secondary_color', 'accent_color')
    def validate_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be in hex format (#RRGGBB)')
        return v.upper()

class NotificationSettings(BaseModel):
    """Schema for notification settings"""
    enable_email_notifications: bool = True
    enable_sms_notifications: bool = False
    enable_whatsapp_notifications: bool = False
    membership_expiry_reminder_days: int = Field(3, ge=1, le=30)
    class_reminder_hours: int = Field(2, ge=1, le=48)
    payment_reminder_days: int = Field(5, ge=1, le=30)

class SecuritySettings(BaseModel):
    """Schema for security settings"""
    session_timeout: int = Field(480, ge=30, le=1440)
    password_min_length: int = Field(8, ge=6, le=20)
    require_password_complexity: bool = True
    max_login_attempts: int = Field(5, ge=3, le=10)
    enable_two_factor_auth: bool = False
    require_email_verification: bool = True

class IntegrationSettings(BaseModel):
    """Schema for integration settings"""
    whatsapp_api_token: Optional[str] = None
    whatsapp_phone_number: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None
    instagram_access_token: Optional[str] = None
    instagram_business_account_id: Optional[str] = None
    enable_instagram_integration: bool = False
    enable_whatsapp_integration: bool = False

class BusinessSettings(BaseModel):
    """Schema for business settings"""
    gym_name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    currency: str = Field("USD", min_length=3, max_length=3)
    tax_rate: float = Field(0.0, ge=0, le=1)
    timezone: str = Field("America/Mexico_City", min_length=1)
    operating_hours: Optional[Dict[str, Dict[str, str]]] = None

# Backup and maintenance schemas
class BackupSettings(BaseModel):
    """Schema for backup settings"""
    auto_backup_enabled: bool = True
    backup_frequency: str = Field("daily", pattern=r'^(daily|weekly|monthly)$')
    backup_retention_days: int = Field(30, ge=7, le=365)
    backup_location: Optional[str] = None
    include_media_files: bool = True

class MaintenanceMode(BaseModel):
    """Schema for maintenance mode"""
    enabled: bool = False
    message: Optional[str] = None
    estimated_duration: Optional[int] = None  # minutes
    allowed_roles: List[str] = ["ADMIN", "OWNER"]

# Feature flags schemas
class FeatureFlags(BaseModel):
    """Schema for feature flags"""
    enable_member_app: bool = True
    enable_online_payments: bool = False
    enable_class_booking: bool = True
    enable_personal_training: bool = True
    enable_nutrition_tracking: bool = False
    enable_progress_photos: bool = True
    enable_community_features: bool = True
    enable_advanced_reporting: bool = False
    enable_api_access: bool = False

# Custom fields schemas
class CustomField(BaseModel):
    """Schema for custom field definition"""
    name: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=200)
    type: str = Field(..., pattern=r'^(text|number|email|phone|date|select|checkbox|textarea)$')
    required: bool = False
    options: Optional[List[str]] = None  # For select fields
    validation_regex: Optional[str] = None
    help_text: Optional[str] = None
    default_value: Optional[str] = None
    
    @validator('options')
    def validate_options(cls, v, values):
        if values.get('type') == 'select' and not v:
            raise ValueError('Options are required for select fields')
        return v

class CustomFieldsConfig(BaseModel):
    """Schema for custom fields configuration"""
    member_fields: List[CustomField] = []
    class_fields: List[CustomField] = []
    payment_fields: List[CustomField] = []
    employee_fields: List[CustomField] = []

# System status schemas
class SystemStatus(BaseModel):
    """Schema for system status"""
    status: str  # healthy, warning, error
    database_status: str
    redis_status: str
    storage_status: str
    backup_status: str
    last_backup: Optional[datetime]
    disk_usage_percentage: float
    memory_usage_percentage: float
    active_users: int
    system_load: float
    uptime_seconds: int

# List schemas
class NotificationTemplateList(BaseModel):
    """Schema for notification template list with pagination"""
    templates: List[NotificationTemplateResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Import/Export schemas
class ConfigurationExport(BaseModel):
    """Schema for configuration export"""
    include_sensitive_data: bool = False
    include_templates: bool = True
    include_custom_fields: bool = True
    format: str = Field('json', pattern=r'^(json|yaml)$')

class ConfigurationImport(BaseModel):
    """Schema for configuration import"""
    configuration_data: Dict[str, Any]
    overwrite_existing: bool = False
    import_templates: bool = True
    import_custom_fields: bool = True
    
    @validator('configuration_data')
    def validate_configuration_data(cls, v):
        if not v:
            raise ValueError('Configuration data cannot be empty')
        return v