from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from ..models.membership import MembershipType, PaymentStatus

class PaymentMethod(str, Enum):
    """Payment methods available"""
    CASH = "cash"  # Efectivo
    CARD = "card"  # Tarjeta
    TRANSFER = "transfer"  # Transferencia
    CHECK = "check"  # Cheque
    DIGITAL = "digital"  # Pago digital

# Membership schemas
class MembershipBase(BaseModel):
    """Base membership schema"""
    membership_type: MembershipType
    start_date: date
    end_date: date
    price: float = Field(..., gt=0)
    is_active: bool = True
    auto_renew: bool = False
    notes: Optional[str] = None
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v

class MembershipCreate(MembershipBase):
    """Schema for creating a membership"""
    user_id: int
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None

class MembershipUpdate(BaseModel):
    """Schema for updating a membership"""
    membership_type: Optional[MembershipType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None
    auto_renew: Optional[bool] = None
    notes: Optional[str] = None
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be greater than 0')
        return v

class MembershipResponse(BaseModel):
    """Schema for membership response"""
    id: int
    user_id: int
    membership_type: MembershipType
    start_date: date
    end_date: date
    price: float
    is_active: bool
    auto_renew: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed properties
    is_expired: bool
    days_remaining: int
    is_expiring_soon: bool
    
    # User info (optional)
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    
    class Config:
        from_attributes = True

# Payment schemas
class PaymentBase(BaseModel):
    """Base payment schema"""
    amount: float = Field(..., gt=0)
    payment_method: PaymentMethod
    payment_date: Optional[date] = None
    due_date: Optional[date] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v
    
    @validator('due_date')
    def due_date_validation(cls, v, values):
        if v and 'payment_date' in values and values['payment_date'] and v < values['payment_date']:
            raise ValueError('Due date cannot be before payment date')
        return v

class PaymentCreate(PaymentBase):
    """Schema for creating a payment"""
    user_id: int
    membership_id: Optional[int] = None
    status: PaymentStatus = PaymentStatus.PENDING

class PaymentUpdate(BaseModel):
    """Schema for updating a payment"""
    amount: Optional[float] = None
    payment_method: Optional[PaymentMethod] = None
    payment_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[PaymentStatus] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class PaymentResponse(BaseModel):
    """Schema for payment response"""
    id: int
    user_id: int
    membership_id: Optional[int]
    amount: float
    payment_method: PaymentMethod
    payment_date: Optional[date]
    due_date: Optional[date]
    status: PaymentStatus
    description: Optional[str]
    reference_number: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed properties
    is_overdue: bool
    days_overdue: int
    status_color: str
    
    # User info (optional)
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    
    # Membership info (optional)
    membership_type: Optional[str] = None
    
    class Config:
        from_attributes = True

# Bulk operations
class MembershipBulkCreate(BaseModel):
    """Schema for bulk membership creation"""
    memberships: List[MembershipCreate]
    
    @validator('memberships')
    def validate_memberships(cls, v):
        if not v:
            raise ValueError('At least one membership is required')
        if len(v) > 100:
            raise ValueError('Cannot create more than 100 memberships at once')
        return v

class PaymentBulkCreate(BaseModel):
    """Schema for bulk payment creation"""
    payments: List[PaymentCreate]
    
    @validator('payments')
    def validate_payments(cls, v):
        if not v:
            raise ValueError('At least one payment is required')
        if len(v) > 100:
            raise ValueError('Cannot create more than 100 payments at once')
        return v

# List and pagination schemas
class MembershipList(BaseModel):
    """Schema for membership list with pagination"""
    memberships: List[MembershipResponse]
    total: int
    page: int
    per_page: int
    pages: int

class PaymentList(BaseModel):
    """Schema for payment list with pagination"""
    payments: List[PaymentResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Statistics schemas
class MembershipStats(BaseModel):
    """Schema for membership statistics"""
    total_memberships: int
    active_memberships: int
    expired_memberships: int
    expiring_soon: int
    memberships_by_type: dict
    revenue_this_month: float
    revenue_last_month: float
    growth_percentage: float

class PaymentStats(BaseModel):
    """Schema for payment statistics"""
    total_payments: int
    paid_payments: int
    pending_payments: int
    overdue_payments: int
    total_revenue: float
    revenue_this_month: float
    revenue_last_month: float
    payments_by_method: dict
    monthly_revenue: List[dict]  # For charts

# Renewal schemas
class MembershipRenewal(BaseModel):
    """Schema for membership renewal"""
    membership_id: int
    new_end_date: date
    price: Optional[float] = None
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('new_end_date')
    def validate_new_end_date(cls, v):
        if v <= date.today():
            raise ValueError('New end date must be in the future')
        return v

class MembershipFreeze(BaseModel):
    """Schema for membership freeze"""
    membership_id: int
    freeze_start_date: date
    freeze_end_date: date
    reason: str
    
    @validator('freeze_end_date')
    def freeze_end_after_start(cls, v, values):
        if 'freeze_start_date' in values and v <= values['freeze_start_date']:
            raise ValueError('Freeze end date must be after start date')
        return v
    
    @validator('reason')
    def validate_reason(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('Reason must be at least 5 characters long')
        return v

# Report schemas
class MembershipReport(BaseModel):
    """Schema for membership reports"""
    period_start: date
    period_end: date
    total_memberships: int
    new_memberships: int
    renewed_memberships: int
    cancelled_memberships: int
    total_revenue: float
    average_membership_value: float
    retention_rate: float
    churn_rate: float

class PaymentReport(BaseModel):
    """Schema for payment reports"""
    period_start: date
    period_end: date
    total_payments: int
    successful_payments: int
    failed_payments: int
    total_amount: float
    average_payment_amount: float
    payment_success_rate: float
    payments_by_method: dict
    daily_revenue: List[dict]