from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime, date
from app.models.user import UserRole, UserType

# Base schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    phone: Optional[str] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_conditions: Optional[str] = None
    fitness_goals: Optional[str] = None
    experience_level: Optional[str] = None
    preferred_workout_time: Optional[str] = None
    role: UserRole = UserRole.MEMBER
    user_type: UserType = UserType.MONTHLY
    is_active: bool = True
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and len(v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        if v and v.lower() not in ['male', 'female', 'other', 'masculino', 'femenino', 'otro']:
            raise ValueError('Gender must be male, female, or other')
        return v
    
    @validator('experience_level')
    def validate_experience_level(cls, v):
        if v and v.lower() not in ['beginner', 'intermediate', 'advanced', 'principiante', 'intermedio', 'avanzado']:
            raise ValueError('Experience level must be beginner, intermediate, or advanced')
        return v

class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_conditions: Optional[str] = None
    fitness_goals: Optional[str] = None
    experience_level: Optional[str] = None
    preferred_workout_time: Optional[str] = None
    role: Optional[UserRole] = None
    user_type: Optional[UserType] = None
    is_active: Optional[bool] = None
    profile_photo: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and len(v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v

class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: str
    phone: Optional[str]
    first_name: str
    last_name: str
    full_name: str
    date_of_birth: Optional[date]
    gender: Optional[str]
    address: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    medical_conditions: Optional[str]
    fitness_goals: Optional[str]
    experience_level: Optional[str]
    preferred_workout_time: Optional[str]
    role: UserRole
    user_type: Optional[UserType]
    is_active: bool
    profile_photo: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    
    # Computed properties
    is_staff: bool
    can_access_admin: bool
    can_manage_users: bool
    can_manage_classes: bool
    can_create_routines: bool
    
    class Config:
        from_attributes = True

# Authentication schemas
class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
    remember_me: bool = False

class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    terms_accepted: bool = Field(..., description="User must accept terms and conditions")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('terms_accepted')
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError('Terms and conditions must be accepted')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class Token(BaseModel):
    """Schema for authentication token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TokenData(BaseModel):
    """Schema for token data"""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None

class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class PasswordReset(BaseModel):
    """Schema for password reset"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

# List and pagination schemas
class UserList(BaseModel):
    """Schema for user list with pagination"""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int

class UserStats(BaseModel):
    """Schema for user statistics"""
    total_users: int
    active_users: int
    new_users_this_month: int
    users_by_type: dict
    users_by_role: dict