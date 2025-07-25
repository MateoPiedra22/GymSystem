from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from ..models.class_model import ClassType, ClassStatus
from ..models.class_reservation import ReservationStatus

# Class schemas
class ClassBase(BaseModel):
    """Base class schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    class_type: ClassType
    date: date
    start_time: time
    end_time: time
    max_capacity: int = Field(..., ge=1, le=100)
    min_participants: int = Field(1, ge=1)
    difficulty_level: str = Field(..., pattern='^(beginner|intermediate|advanced|principiante|intermedio|avanzado)$')
    equipment_needed: Optional[str] = None
    special_requirements: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    is_included_in_membership: bool = True
    room: Optional[str] = None
    location_notes: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    trainer_notes: Optional[str] = None
    admin_notes: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Class name cannot be empty')
        return v.strip().title()
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @validator('max_capacity')
    def validate_max_capacity(cls, v, values):
        if 'min_participants' in values and v < values['min_participants']:
            raise ValueError('Max capacity must be greater than or equal to min participants')
        return v
    
    @validator('price')
    def validate_price(cls, v, values):
        if v is not None and v < 0:
            raise ValueError('Price cannot be negative')
        if v is not None and v > 0 and values.get('is_included_in_membership', True):
            raise ValueError('Price should be 0 or null if included in membership')
        return v
    
    @validator('date')
    def validate_date(cls, v):
        if v < date.today():
            raise ValueError('Class date cannot be in the past')
        return v

class ClassCreate(ClassBase):
    """Schema for creating a class"""
    trainer_id: int
    status: ClassStatus = ClassStatus.SCHEDULED

class ClassUpdate(BaseModel):
    """Schema for updating a class"""
    name: Optional[str] = None
    description: Optional[str] = None
    class_type: Optional[ClassType] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    max_capacity: Optional[int] = Field(None, ge=1, le=100)
    min_participants: Optional[int] = Field(None, ge=1)
    difficulty_level: Optional[str] = None
    equipment_needed: Optional[str] = None
    special_requirements: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    is_included_in_membership: Optional[bool] = None
    room: Optional[str] = None
    location_notes: Optional[str] = None
    status: Optional[ClassStatus] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    trainer_notes: Optional[str] = None
    admin_notes: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Class name cannot be empty')
        return v.strip().title() if v else v
    
    @validator('date')
    def validate_date(cls, v):
        if v is not None and v < date.today():
            raise ValueError('Class date cannot be in the past')
        return v

class ClassResponse(BaseModel):
    """Schema for class response"""
    id: int
    trainer_id: int
    name: str
    description: Optional[str]
    class_type: ClassType
    date: date
    start_time: time
    end_time: time
    max_capacity: int
    min_participants: int
    difficulty_level: str
    equipment_needed: Optional[str]
    special_requirements: Optional[str]
    price: Optional[float]
    is_included_in_membership: bool
    room: Optional[str]
    location_notes: Optional[str]
    status: ClassStatus
    is_recurring: bool
    recurrence_pattern: Optional[str]
    trainer_notes: Optional[str]
    admin_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed properties
    duration_minutes: int
    current_reservations: int
    available_spots: int
    is_full: bool
    waiting_list_count: int
    attendance_count: int
    attendance_rate: float
    
    # Trainer info
    trainer_name: str
    trainer_email: Optional[str] = None
    
    # Status info
    status_color: str
    can_book: bool
    can_cancel: bool
    
    class Config:
        from_attributes = True

# Class Reservation schemas
class ClassReservationBase(BaseModel):
    """Base class reservation schema"""
    notes: Optional[str] = None

class ClassReservationCreate(ClassReservationBase):
    """Schema for creating a class reservation"""
    user_id: int
    class_id: int
    payment_required: bool = False
    payment_amount: Optional[float] = Field(None, ge=0)
    
    @validator('payment_amount')
    def validate_payment_amount(cls, v, values):
        if values.get('payment_required', False) and (v is None or v <= 0):
            raise ValueError('Payment amount is required when payment is required')
        return v

class ClassReservationUpdate(BaseModel):
    """Schema for updating a class reservation"""
    status: Optional[ReservationStatus] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    
    @validator('cancellation_reason')
    def validate_cancellation_reason(cls, v, values):
        if values.get('status') == ReservationStatus.CANCELLED and not v:
            raise ValueError('Cancellation reason is required when cancelling')
        return v

class ClassReservationResponse(BaseModel):
    """Schema for class reservation response"""
    id: int
    user_id: int
    class_id: int
    status: ReservationStatus
    reservation_date: datetime
    payment_required: bool
    payment_amount: Optional[float]
    payment_status: Optional[str]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed properties
    can_cancel: bool
    status_color: str
    
    # User info
    user_name: str
    user_email: str
    user_phone: Optional[str] = None
    
    # Class info
    class_name: str
    class_date: date
    class_start_time: time
    class_trainer_name: str
    
    class Config:
        from_attributes = True

# Class Attendance schemas
class ClassAttendanceBase(BaseModel):
    """Base class attendance schema"""
    attended: bool
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None
    trainer_notes: Optional[str] = None

class ClassAttendanceCreate(ClassAttendanceBase):
    """Schema for creating class attendance"""
    user_id: int
    class_id: int
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    
    @validator('check_out_time')
    def validate_check_out_time(cls, v, values):
        if v and 'check_in_time' in values and values['check_in_time'] and v <= values['check_in_time']:
            raise ValueError('Check out time must be after check in time')
        return v

class ClassAttendanceUpdate(BaseModel):
    """Schema for updating class attendance"""
    attended: Optional[bool] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None
    trainer_notes: Optional[str] = None

class ClassAttendanceResponse(BaseModel):
    """Schema for class attendance response"""
    id: int
    user_id: int
    class_id: int
    attended: bool
    check_in_time: Optional[datetime]
    check_out_time: Optional[datetime]
    rating: Optional[int]
    feedback: Optional[str]
    trainer_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed properties
    duration_minutes: int
    was_late: bool
    minutes_late: int
    
    # User info
    user_name: str
    user_email: str
    
    # Class info
    class_name: str
    class_date: date
    class_start_time: time
    
    class Config:
        from_attributes = True

# Bulk operations
class ClassBulkCreate(BaseModel):
    """Schema for bulk class creation"""
    classes: List[ClassCreate]
    
    @validator('classes')
    def validate_classes(cls, v):
        if not v:
            raise ValueError('At least one class is required')
        if len(v) > 50:
            raise ValueError('Cannot create more than 50 classes at once')
        return v

class ReservationBulkCreate(BaseModel):
    """Schema for bulk reservation creation"""
    class_id: int
    user_ids: List[int]
    notes: Optional[str] = None
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if not v:
            raise ValueError('At least one user ID is required')
        if len(v) > 100:
            raise ValueError('Cannot create more than 100 reservations at once')
        return v

# List and pagination schemas
class ClassList(BaseModel):
    """Schema for class list with pagination"""
    classes: List[ClassResponse]
    total: int
    page: int
    per_page: int
    pages: int

class ClassReservationList(BaseModel):
    """Schema for class reservation list with pagination"""
    reservations: List[ClassReservationResponse]
    total: int
    page: int
    per_page: int
    pages: int

class ClassAttendanceList(BaseModel):
    """Schema for class attendance list with pagination"""
    attendances: List[ClassAttendanceResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Filter schemas
class ClassFilter(BaseModel):
    """Schema for class filtering"""
    class_type: Optional[ClassType] = None
    trainer_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[ClassStatus] = None
    difficulty_level: Optional[str] = None
    has_available_spots: Optional[bool] = None
    is_included_in_membership: Optional[bool] = None
    room: Optional[str] = None

# Statistics schemas
class ClassStats(BaseModel):
    """Schema for class statistics"""
    total_classes: int
    scheduled_classes: int
    completed_classes: int
    cancelled_classes: int
    classes_by_type: Dict[str, int]
    classes_by_trainer: Dict[str, int]
    average_attendance_rate: float
    most_popular_classes: List[Dict[str, Any]]
    revenue_from_classes: float
    total_reservations: int
    total_attendances: int

# Schedule schemas
class ClassSchedule(BaseModel):
    """Schema for class schedule view"""
    date: date
    classes: List[ClassResponse]
    total_classes: int
    total_capacity: int
    total_reservations: int

class WeeklySchedule(BaseModel):
    """Schema for weekly schedule"""
    week_start: date
    week_end: date
    daily_schedules: List[ClassSchedule]
    week_stats: Dict[str, Any]

# Recurring class schemas
class RecurringClassCreate(BaseModel):
    """Schema for creating recurring classes"""
    base_class: ClassCreate
    recurrence_type: str = Field(..., pattern='^(daily|weekly|monthly)$')
    recurrence_interval: int = Field(..., ge=1, le=12)  # Every X days/weeks/months
    end_date: date
    days_of_week: Optional[List[int]] = None  # For weekly: [0,1,2,3,4,5,6]
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'base_class' in values and v <= values['base_class'].date:
            raise ValueError('End date must be after the first class date')
        return v
    
    @validator('days_of_week')
    def validate_days_of_week(cls, v, values):
        if values.get('recurrence_type') == 'weekly' and not v:
            raise ValueError('Days of week are required for weekly recurrence')
        if v:
            for day in v:
                if day < 0 or day > 6:
                    raise ValueError('Days of week must be between 0 (Monday) and 6 (Sunday)')
        return v

# Waitlist schemas
class WaitlistEntry(BaseModel):
    """Schema for waitlist entry"""
    class_id: int
    user_id: int
    position: int
    added_at: datetime
    notified: bool = False
    
    class Config:
        from_attributes = True

class WaitlistResponse(BaseModel):
    """Schema for waitlist response"""
    entries: List[WaitlistEntry]
    total_waiting: int
    estimated_availability: Optional[datetime] = None