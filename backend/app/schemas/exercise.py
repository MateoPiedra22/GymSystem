from pydantic import BaseModel, validator, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from ..models.exercise import ExerciseCategory, MuscleGroup

class DifficultyLevel(str, Enum):
    """Exercise difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class EquipmentType(str, Enum):
    """Equipment types"""
    NONE = "none"  # Sin equipo
    DUMBBELLS = "dumbbells"  # Mancuernas
    BARBELL = "barbell"  # Barra
    KETTLEBELL = "kettlebell"  # Pesa rusa
    RESISTANCE_BANDS = "resistance_bands"  # Bandas elásticas
    PULL_UP_BAR = "pull_up_bar"  # Barra de dominadas
    BENCH = "bench"  # Banco
    CABLE_MACHINE = "cable_machine"  # Máquina de poleas
    TREADMILL = "treadmill"  # Cinta de correr
    STATIONARY_BIKE = "stationary_bike"  # Bicicleta estática
    YOGA_MAT = "yoga_mat"  # Esterilla de yoga

# Base schemas
class ExerciseBase(BaseModel):
    """Base exercise schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: ExerciseCategory
    primary_muscle_group: MuscleGroup
    secondary_muscle_groups: Optional[List[MuscleGroup]] = []
    difficulty_level: DifficultyLevel
    equipment_needed: Optional[List[EquipmentType]] = []
    instructions: Optional[str] = None
    safety_tips: Optional[str] = None
    
    # Exercise parameters
    default_sets: Optional[int] = Field(None, ge=1, le=10)
    default_reps: Optional[int] = Field(None, ge=1, le=100)
    default_weight: Optional[float] = Field(None, ge=0)
    default_duration_seconds: Optional[int] = Field(None, ge=1)
    default_rest_seconds: Optional[int] = Field(None, ge=0, le=600)
    
    # Media
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    
    # Metadata
    calories_per_minute: Optional[float] = Field(None, ge=0)
    is_cardio: bool = False
    is_strength: bool = False
    is_flexibility: bool = False
    is_active: bool = True
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Exercise name cannot be empty')
        return v.strip().title()
    
    @validator('secondary_muscle_groups')
    def validate_secondary_muscles(cls, v, values):
        if v and 'primary_muscle_group' in values:
            if values['primary_muscle_group'] in v:
                raise ValueError('Primary muscle group cannot be in secondary muscle groups')
        return v or []
    
    @validator('equipment_needed')
    def validate_equipment(cls, v):
        return v or []
    
    @validator('default_sets', 'default_reps')
    def validate_positive_integers(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Sets and reps must be positive integers')
        return v
    
    @validator('default_weight', 'calories_per_minute')
    def validate_positive_floats(cls, v):
        if v is not None and v < 0:
            raise ValueError('Weight and calories must be non-negative')
        return v

class ExerciseCreate(ExerciseBase):
    """Schema for creating an exercise"""
    created_by: Optional[int] = None  # User ID who created the exercise

class ExerciseUpdate(BaseModel):
    """Schema for updating an exercise"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ExerciseCategory] = None
    primary_muscle_group: Optional[MuscleGroup] = None
    secondary_muscle_groups: Optional[List[MuscleGroup]] = None
    difficulty_level: Optional[DifficultyLevel] = None
    equipment_needed: Optional[List[EquipmentType]] = None
    instructions: Optional[str] = None
    safety_tips: Optional[str] = None
    
    # Exercise parameters
    default_sets: Optional[int] = Field(None, ge=1, le=10)
    default_reps: Optional[int] = Field(None, ge=1, le=100)
    default_weight: Optional[float] = Field(None, ge=0)
    default_duration_seconds: Optional[int] = Field(None, ge=1)
    default_rest_seconds: Optional[int] = Field(None, ge=0, le=600)
    
    # Media
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    
    # Metadata
    calories_per_minute: Optional[float] = Field(None, ge=0)
    is_cardio: Optional[bool] = None
    is_strength: Optional[bool] = None
    is_flexibility: Optional[bool] = None
    is_active: Optional[bool] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Exercise name cannot be empty')
        return v.strip().title() if v else v

class ExerciseResponse(BaseModel):
    """Schema for exercise response"""
    id: int
    name: str
    description: Optional[str]
    category: ExerciseCategory
    primary_muscle_group: MuscleGroup
    secondary_muscle_groups: List[MuscleGroup]
    difficulty_level: DifficultyLevel
    equipment_needed: List[EquipmentType]
    instructions: Optional[str]
    safety_tips: Optional[str]
    
    # Exercise parameters
    default_sets: Optional[int]
    default_reps: Optional[int]
    default_weight: Optional[float]
    default_duration_seconds: Optional[int]
    default_rest_seconds: Optional[int]
    
    # Media
    image_url: Optional[str]
    video_url: Optional[str]
    
    # Metadata
    calories_per_minute: Optional[float]
    is_cardio: bool
    is_strength: bool
    is_flexibility: bool
    is_active: bool
    
    # System fields
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed properties
    category_display: str
    difficulty_display: str
    muscle_groups_display: str
    equipment_display: str
    
    # Creator info (optional)
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Bulk operations
class ExerciseBulkCreate(BaseModel):
    """Schema for bulk exercise creation"""
    exercises: List[ExerciseCreate]
    
    @validator('exercises')
    def validate_exercises(cls, v):
        if not v:
            raise ValueError('At least one exercise is required')
        if len(v) > 50:
            raise ValueError('Cannot create more than 50 exercises at once')
        return v

class ExerciseBulkUpdate(BaseModel):
    """Schema for bulk exercise update"""
    exercise_ids: List[int]
    updates: ExerciseUpdate
    
    @validator('exercise_ids')
    def validate_exercise_ids(cls, v):
        if not v:
            raise ValueError('At least one exercise ID is required')
        if len(v) > 50:
            raise ValueError('Cannot update more than 50 exercises at once')
        return v

# Search and filter schemas
class ExerciseFilter(BaseModel):
    """Schema for exercise filtering"""
    category: Optional[ExerciseCategory] = None
    primary_muscle_group: Optional[MuscleGroup] = None
    secondary_muscle_groups: Optional[List[MuscleGroup]] = None
    difficulty_level: Optional[DifficultyLevel] = None
    equipment_needed: Optional[List[EquipmentType]] = None
    is_cardio: Optional[bool] = None
    is_strength: Optional[bool] = None
    is_flexibility: Optional[bool] = None
    is_active: Optional[bool] = None
    created_by: Optional[int] = None
    search_term: Optional[str] = None

class ExerciseSearch(BaseModel):
    """Schema for exercise search"""
    query: str = Field(..., min_length=1)
    filters: Optional[ExerciseFilter] = None
    limit: int = Field(20, ge=1, le=100)
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()

# List and pagination schemas
class ExerciseList(BaseModel):
    """Schema for exercise list with pagination"""
    exercises: List[ExerciseResponse]
    total: int
    page: int
    per_page: int
    pages: int
    filters: Optional[ExerciseFilter] = None

# Statistics schemas
class ExerciseStats(BaseModel):
    """Schema for exercise statistics"""
    total_exercises: int
    active_exercises: int
    exercises_by_category: Dict[str, int]
    exercises_by_muscle_group: Dict[str, int]
    exercises_by_difficulty: Dict[str, int]
    exercises_by_equipment: Dict[str, int]
    most_used_exercises: List[Dict[str, Any]]
    recently_added: List[ExerciseResponse]

# Import/Export schemas
class ExerciseImport(BaseModel):
    """Schema for exercise import"""
    exercises: List[Dict[str, Any]]
    overwrite_existing: bool = False
    
    @validator('exercises')
    def validate_exercises(cls, v):
        if not v:
            raise ValueError('At least one exercise is required')
        if len(v) > 200:
            raise ValueError('Cannot import more than 200 exercises at once')
        return v

class ExerciseExport(BaseModel):
    """Schema for exercise export"""
    exercise_ids: Optional[List[int]] = None
    filters: Optional[ExerciseFilter] = None
    format: str = Field('json', pattern='^(json|csv|xlsx)$')
    include_media: bool = False

# Custom exercise schemas
class CustomExerciseCreate(ExerciseCreate):
    """Schema for creating custom exercises"""
    is_custom: bool = True
    original_exercise_id: Optional[int] = None  # If based on existing exercise

class ExerciseTemplate(BaseModel):
    """Schema for exercise templates"""
    name: str
    exercises: List[Dict[str, Any]]  # Exercise configurations
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    estimated_duration_minutes: Optional[int] = None
    created_by: Optional[int] = None
    is_public: bool = False

# Exercise progression schemas
class ExerciseProgression(BaseModel):
    """Schema for exercise progression tracking"""
    exercise_id: int
    user_id: int
    date: datetime
    sets: int
    reps: int
    weight: Optional[float] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None
    difficulty_rating: Optional[int] = Field(None, ge=1, le=10)
    
    @validator('sets', 'reps')
    def validate_positive_integers(cls, v):
        if v <= 0:
            raise ValueError('Sets and reps must be positive integers')
        return v

class ExerciseProgressionResponse(ExerciseProgression):
    """Schema for exercise progression response"""
    id: int
    exercise_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True