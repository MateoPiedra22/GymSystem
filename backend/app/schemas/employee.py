from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from ..models.employee import EmployeeStatus, ContractType, ShiftType

# Employee schemas
class EmployeeBase(BaseModel):
    """Base employee schema"""
    employee_id: str = Field(..., min_length=1, max_length=20)
    hire_date: date
    contract_type: ContractType
    position: str = Field(..., min_length=1, max_length=100)
    department: Optional[str] = None
    supervisor_id: Optional[int] = None
    base_salary: Optional[float] = Field(None, ge=0)
    hourly_rate: Optional[float] = Field(None, ge=0)
    commission_rate: Optional[float] = Field(None, ge=0, le=1)
    default_shift: Optional[ShiftType] = None
    weekly_hours: Optional[int] = Field(None, ge=1, le=80)
    certifications: Optional[str] = None
    specializations: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    performance_rating: Optional[float] = Field(None, ge=1, le=5)
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    access_level: int = Field(1, ge=1, le=5)
    can_open_gym: bool = False
    can_close_gym: bool = False
    can_handle_payments: bool = False
    can_manage_classes: bool = False
    notes: Optional[str] = None
    
    @validator('employee_id')
    def validate_employee_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Employee ID cannot be empty')
        return v.strip().upper()
    
    @validator('position')
    def validate_position(cls, v):
        if not v or not v.strip():
            raise ValueError('Position cannot be empty')
        return v.strip().title()
    
    @validator('hire_date')
    def validate_hire_date(cls, v):
        if v > date.today():
            raise ValueError('Hire date cannot be in the future')
        return v
    
    @validator('next_review_date')
    def validate_next_review_date(cls, v, values):
        if v and 'last_review_date' in values and values['last_review_date'] and v <= values['last_review_date']:
            raise ValueError('Next review date must be after last review date')
        return v
    
    @validator('commission_rate')
    def validate_commission_rate(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Commission rate must be between 0 and 1')
        return v
    
    @validator('performance_rating')
    def validate_performance_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Performance rating must be between 1 and 5')
        return v

class EmployeeCreate(EmployeeBase):
    """Schema for creating an employee"""
    user_id: int
    status: EmployeeStatus = EmployeeStatus.ACTIVE

class EmployeeUpdate(BaseModel):
    """Schema for updating an employee"""
    employee_id: Optional[str] = None
    contract_type: Optional[ContractType] = None
    status: Optional[EmployeeStatus] = None
    position: Optional[str] = None
    department: Optional[str] = None
    supervisor_id: Optional[int] = None
    termination_date: Optional[date] = None
    base_salary: Optional[float] = Field(None, ge=0)
    hourly_rate: Optional[float] = Field(None, ge=0)
    commission_rate: Optional[float] = Field(None, ge=0, le=1)
    default_shift: Optional[ShiftType] = None
    weekly_hours: Optional[int] = Field(None, ge=1, le=80)
    certifications: Optional[str] = None
    specializations: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    performance_rating: Optional[float] = Field(None, ge=1, le=5)
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    access_level: Optional[int] = Field(None, ge=1, le=5)
    can_open_gym: Optional[bool] = None
    can_close_gym: Optional[bool] = None
    can_handle_payments: Optional[bool] = None
    can_manage_classes: Optional[bool] = None
    notes: Optional[str] = None
    
    @validator('termination_date')
    def validate_termination_date(cls, v):
        if v and v > date.today():
            raise ValueError('Termination date cannot be in the future')
        return v

class EmployeeResponse(BaseModel):
    """Schema for employee response"""
    id: int
    user_id: int
    employee_id: str
    hire_date: date
    termination_date: Optional[date]
    contract_type: ContractType
    status: EmployeeStatus
    position: str
    department: Optional[str]
    supervisor_id: Optional[int]
    base_salary: Optional[float]
    hourly_rate: Optional[float]
    commission_rate: Optional[float]
    default_shift: Optional[ShiftType]
    weekly_hours: Optional[int]
    certifications: Optional[str]
    specializations: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relationship: Optional[str]
    performance_rating: Optional[float]
    last_review_date: Optional[date]
    next_review_date: Optional[date]
    access_level: int
    can_open_gym: bool
    can_close_gym: bool
    can_handle_payments: bool
    can_manage_classes: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed properties
    full_name: str
    is_active: bool
    years_of_service: float
    total_hours_this_week: float
    
    # User info
    user_email: str
    user_phone: Optional[str] = None
    
    # Supervisor info
    supervisor_name: Optional[str] = None
    
    # Subordinates count
    subordinates_count: int = 0
    
    class Config:
        from_attributes = True







# Bulk operations
class EmployeeBulkUpdate(BaseModel):
    """Schema for bulk employee update"""
    employee_ids: List[int]
    updates: EmployeeUpdate
    
    @validator('employee_ids')
    def validate_employee_ids(cls, v):
        if not v:
            raise ValueError('At least one employee ID is required')
        if len(v) > 50:
            raise ValueError('Cannot update more than 50 employees at once')
        return v



# List and pagination schemas
class EmployeeList(BaseModel):
    """Schema for employee list with pagination"""
    employees: List[EmployeeResponse]
    total: int
    page: int
    per_page: int
    pages: int



# Filter schemas
class EmployeeFilter(BaseModel):
    """Schema for employee filtering"""
    status: Optional[EmployeeStatus] = None
    contract_type: Optional[ContractType] = None
    position: Optional[str] = None
    department: Optional[str] = None
    supervisor_id: Optional[int] = None
    hire_date_from: Optional[date] = None
    hire_date_to: Optional[date] = None
    access_level: Optional[int] = None
    search_term: Optional[str] = None

# Statistics schemas
class EmployeeStats(BaseModel):
    """Schema for employee statistics"""
    total_employees: int
    active_employees: int
    inactive_employees: int
    employees_by_status: Dict[str, int]
    employees_by_contract_type: Dict[str, int]
    employees_by_department: Dict[str, int]
    average_years_of_service: float
    upcoming_reviews: int
    total_hours_this_week: float
    overtime_hours_this_week: float

# Payroll schemas
class PayrollPeriod(BaseModel):
    """Schema for payroll period"""
    start_date: date
    end_date: date
    employee_id: Optional[int] = None
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class PayrollSummary(BaseModel):
    """Schema for payroll summary"""
    employee_id: int
    employee_name: str
    period_start: date
    period_end: date
    regular_hours: float
    overtime_hours: float
    total_hours: float
    hourly_rate: Optional[float]
    base_salary: Optional[float]
    gross_pay: float
    commission: float
    total_pay: float

# Performance schemas
class PerformanceReview(BaseModel):
    """Schema for performance review"""
    employee_id: int
    review_date: date
    reviewer_id: int
    rating: float = Field(..., ge=1, le=5)
    goals_met: bool
    strengths: str
    areas_for_improvement: str
    goals_for_next_period: str
    comments: Optional[str] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

class PerformanceReviewResponse(PerformanceReview):
    """Schema for performance review response"""
    id: int
    employee_name: str
    reviewer_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True