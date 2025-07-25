from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from ..models.routine import RoutineType, RoutineDifficulty

# Routine Template schemas
class RoutineTemplateBase(BaseModel):
    """Base routine template schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    routine_type: RoutineType
    difficulty: RoutineDifficulty
    estimated_duration_minutes: int = Field(..., ge=5, le=300)
    target_muscle_groups: List[str] = []
    equipment_needed: List[str] = []
    goals: List[str] = []  # weight_loss, muscle_gain, endurance, etc.
    is_public: bool = True
    is_active: bool = True
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Routine name cannot be empty')
        return v.strip().title()
    
    @validator('target_muscle_groups', 'equipment_needed', 'goals')
    def validate_lists(cls, v):
        return v or []
    
    @validator('estimated_duration_minutes')
    def validate_duration(cls, v):
        if v < 5:
            raise ValueError('Duration must be at least 5 minutes')
        if v > 300:
            raise ValueError('Duration cannot exceed 5 hours')
        return v

class RoutineTemplateCreate(RoutineTemplateBase):
    """Schema for creating a routine template"""
    created_by: Optional[int] = None
    exercises: List[Dict[str, Any]] = []  # Exercise configurations
    
    @validator('exercises')
    def validate_exercises(cls, v):
        if not v:
            raise ValueError('At least one exercise is required')
        for exercise in v:
            if 'exercise_id' not in exercise:
                raise ValueError('Each exercise must have an exercise_id')
            if 'order' not in exercise:
                raise ValueError('Each exercise must have an order')
        return v

class RoutineTemplateUpdate(BaseModel):
    """Schema for updating a routine template"""
    name: Optional[str] = None
    description: Optional[str] = None
    routine_type: Optional[RoutineType] = None
    difficulty: Optional[RoutineDifficulty] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=5, le=300)
    target_muscle_groups: Optional[List[str]] = None
    equipment_needed: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Routine name cannot be empty')
        return v.strip().title() if v else v

class RoutineTemplateResponse(BaseModel):
    """Schema for routine template response"""
    id: int
    name: str
    description: Optional[str]
    routine_type: RoutineType
    difficulty: RoutineDifficulty
    estimated_duration_minutes: int
    target_muscle_groups: List[str]
    equipment_needed: List[str]
    goals: List[str]
    is_public: bool
    is_active: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed properties
    difficulty_display: str
    type_display: str
    muscle_groups_display: str
    equipment_display: str
    
    # Creator info
    creator_name: Optional[str] = None
    
    # Exercise count
    exercise_count: int = 0
    
    # Usage stats
    times_used: int = 0
    
    class Config:
        from_attributes = True

# Routine schemas
class RoutineBase(BaseModel):
    """Base routine schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    routine_type: RoutineType
    difficulty: RoutineDifficulty
    estimated_duration_minutes: int = Field(..., ge=5, le=300)
    target_muscle_groups: List[str] = []
    equipment_needed: List[str] = []
    goals: List[str] = []
    is_active: bool = True
    notes: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Routine name cannot be empty')
        return v.strip().title()

class RoutineCreate(RoutineBase):
    """Schema for creating a routine"""
    user_id: int
    template_id: Optional[int] = None
    exercises: List[Dict[str, Any]] = []
    
    @validator('exercises')
    def validate_exercises(cls, v):
        if not v:
            raise ValueError('At least one exercise is required')
        return v

class RoutineUpdate(BaseModel):
    """Schema for updating a routine"""
    name: Optional[str] = None
    description: Optional[str] = None
    routine_type: Optional[RoutineType] = None
    difficulty: Optional[RoutineDifficulty] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=5, le=300)
    target_muscle_groups: Optional[List[str]] = None
    equipment_needed: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class RoutineResponse(BaseModel):
    """Schema for routine response"""
    id: int
    user_id: int
    template_id: Optional[int]
    name: str
    description: Optional[str]
    routine_type: RoutineType
    difficulty: RoutineDifficulty
    estimated_duration_minutes: int
    target_muscle_groups: List[str]
    equipment_needed: List[str]
    goals: List[str]
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # User info
    user_name: Optional[str] = None
    
    # Template info
    template_name: Optional[str] = None
    
    # Exercise count
    exercise_count: int = 0
    
    # Progress tracking
    times_completed: int = 0
    last_completed: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Routine Exercise schemas
class RoutineExerciseBase(BaseModel):
    """Base routine exercise schema"""
    exercise_id: int
    order: int = Field(..., ge=1)
    sets: int = Field(..., ge=1, le=20)
    reps: Optional[int] = Field(None, ge=1, le=200)
    weight: Optional[float] = Field(None, ge=0)
    duration_seconds: Optional[int] = Field(None, ge=1)
    rest_seconds: int = Field(60, ge=0, le=600)
    notes: Optional[str] = None
    
    @validator('sets')
    def validate_sets(cls, v):
        if v <= 0:
            raise ValueError('Sets must be positive')
        return v
    
    @validator('reps')
    def validate_reps(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Reps must be positive')
        return v
    
    @validator('weight')
    def validate_weight(cls, v):
        if v is not None and v < 0:
            raise ValueError('Weight cannot be negative')
        return v

class RoutineExerciseCreate(RoutineExerciseBase):
    """Schema for creating a routine exercise"""
    routine_id: int

class RoutineExerciseUpdate(BaseModel):
    """Schema for updating a routine exercise"""
    exercise_id: Optional[int] = None
    order: Optional[int] = Field(None, ge=1)
    sets: Optional[int] = Field(None, ge=1, le=20)
    reps: Optional[int] = Field(None, ge=1, le=200)
    weight: Optional[float] = Field(None, ge=0)
    duration_seconds: Optional[int] = Field(None, ge=1)
    rest_seconds: Optional[int] = Field(None, ge=0, le=600)
    notes: Optional[str] = None

class RoutineExerciseResponse(BaseModel):
    """Schema for routine exercise response"""
    id: int
    routine_id: int
    exercise_id: int
    order: int
    sets: int
    reps: Optional[int]
    weight: Optional[float]
    duration_seconds: Optional[int]
    rest_seconds: int
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Exercise info
    exercise_name: str
    exercise_category: str
    exercise_muscle_group: str
    exercise_difficulty: str
    exercise_image_url: Optional[str] = None
    
    class Config:
        from_attributes = True

# Routine Assignment schemas
class RoutineAssignmentBase(BaseModel):
    """Base routine assignment schema"""
    routine_id: int
    assigned_date: date
    target_date: Optional[date] = None
    notes: Optional[str] = None
    
    @validator('target_date')
    def validate_target_date(cls, v, values):
        if v and 'assigned_date' in values and v < values['assigned_date']:
            raise ValueError('Target date cannot be before assigned date')
        return v

class RoutineAssignmentCreate(RoutineAssignmentBase):
    """Schema for creating a routine assignment"""
    user_id: int
    assigned_by: Optional[int] = None  # Trainer who assigned

class RoutineAssignmentUpdate(BaseModel):
    """Schema for updating a routine assignment"""
    target_date: Optional[date] = None
    notes: Optional[str] = None
    is_completed: Optional[bool] = None
    completed_date: Optional[datetime] = None
    completion_notes: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)

class RoutineAssignmentResponse(BaseModel):
    """Schema for routine assignment response"""
    id: int
    user_id: int
    routine_id: int
    assigned_by: Optional[int]
    assigned_date: date
    target_date: Optional[date]
    is_completed: bool
    completed_date: Optional[datetime]
    completion_notes: Optional[str]
    rating: Optional[int]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # User info
    user_name: str
    
    # Routine info
    routine_name: str
    routine_difficulty: str
    routine_duration: int
    
    # Assigner info
    assigned_by_name: Optional[str] = None
    
    # Status
    is_overdue: bool
    days_until_target: Optional[int] = None
    
    class Config:
        from_attributes = True

# Bulk operations
class RoutineBulkAssign(BaseModel):
    """Schema for bulk routine assignment"""
    routine_id: int
    user_ids: List[int]
    assigned_date: date
    target_date: Optional[date] = None
    notes: Optional[str] = None
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if not v:
            raise ValueError('At least one user ID is required')
        if len(v) > 100:
            raise ValueError('Cannot assign to more than 100 users at once')
        return v

# List and pagination schemas
class RoutineTemplateList(BaseModel):
    """Schema for routine template list with pagination"""
    templates: List[RoutineTemplateResponse]
    total: int
    page: int
    per_page: int
    pages: int

class RoutineList(BaseModel):
    """Schema for routine list with pagination"""
    routines: List[RoutineResponse]
    total: int
    page: int
    per_page: int
    pages: int

class RoutineAssignmentList(BaseModel):
    """Schema for routine assignment list with pagination"""
    assignments: List[RoutineAssignmentResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Statistics schemas
class RoutineStats(BaseModel):
    """Schema for routine statistics"""
    total_routines: int
    active_routines: int
    total_templates: int
    public_templates: int
    routines_by_type: Dict[str, int]
    routines_by_difficulty: Dict[str, int]
    most_popular_templates: List[Dict[str, Any]]
    completion_rate: float
    average_rating: float

# Progress tracking schemas
class RoutineProgress(BaseModel):
    """Schema for routine progress tracking"""
    assignment_id: int
    exercise_id: int
    sets_completed: int
    reps_completed: Optional[int] = None
    weight_used: Optional[float] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None
    difficulty_rating: Optional[int] = Field(None, ge=1, le=10)
    
    @validator('sets_completed')
    def validate_sets(cls, v):
        if v < 0:
            raise ValueError('Sets completed cannot be negative')
        return v

class RoutineProgressResponse(RoutineProgress):
    """Schema for routine progress response"""
    id: int
    user_id: int
    exercise_name: str
    recorded_at: datetime
    
    class Config:
        from_attributes = True

# Workout session schemas
class WorkoutSession(BaseModel):
    """Schema for workout session"""
    assignment_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    exercises_completed: List[RoutineProgress] = []
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if v and 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class WorkoutSessionResponse(WorkoutSession):
    """Schema for workout session response"""
    id: int
    user_id: int
    routine_name: str
    duration_minutes: Optional[int] = None
    completion_percentage: float
    created_at: datetime
    
    class Config:
        from_attributes = True