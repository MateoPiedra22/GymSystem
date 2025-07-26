from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime

class ExerciseCategory(str, enum.Enum):
    """Exercise categories"""
    STRENGTH = "strength"  # Fuerza
    CARDIO = "cardio"  # Cardiovascular
    FLEXIBILITY = "flexibility"  # Flexibilidad
    BALANCE = "balance"  # Equilibrio
    FUNCTIONAL = "functional"  # Funcional
    REHABILITATION = "rehabilitation"  # Rehabilitación
    SPORTS_SPECIFIC = "sports_specific"  # Específico del deporte

class MuscleGroup(str, enum.Enum):
    """Muscle groups"""
    CHEST = "chest"  # Pecho
    BACK = "back"  # Espalda
    SHOULDERS = "shoulders"  # Hombros
    BICEPS = "biceps"  # Bíceps
    TRICEPS = "triceps"  # Tríceps
    FOREARMS = "forearms"  # Antebrazos
    ABS = "abs"  # Abdominales
    OBLIQUES = "obliques"  # Oblicuos
    LOWER_BACK = "lower_back"  # Espalda baja
    GLUTES = "glutes"  # Glúteos
    QUADRICEPS = "quadriceps"  # Cuádriceps
    HAMSTRINGS = "hamstrings"  # Isquiotibiales
    CALVES = "calves"  # Pantorrillas
    FULL_BODY = "full_body"  # Cuerpo completo

class Exercise(Base):
    """Exercise model"""
    __tablename__ = "exercises"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    
    # Categorization
    category = Column(Enum(ExerciseCategory), nullable=False)
    primary_muscle_group = Column(Enum(MuscleGroup), nullable=False)
    secondary_muscle_groups = Column(JSON, nullable=True)  # List of MuscleGroup
    
    # Difficulty and requirements
    difficulty_level = Column(String(20), nullable=False)  # beginner, intermediate, advanced
    equipment_needed = Column(JSON, nullable=True)  # List of equipment
    space_required = Column(String(50), nullable=True)  # small, medium, large
    
    # Media
    image_url = Column(String(255), nullable=True)
    video_url = Column(String(255), nullable=True)
    demonstration_gif = Column(String(255), nullable=True)
    
    # Exercise parameters
    default_sets = Column(Integer, nullable=True)
    default_reps = Column(String(50), nullable=True)  # "8-12" or "30 seconds"
    default_rest_time = Column(Integer, nullable=True)  # seconds
    default_weight = Column(Float, nullable=True)  # kg
    
    # Metrics
    calories_per_minute = Column(Float, nullable=True)
    met_value = Column(Float, nullable=True)  # Metabolic equivalent
    
    # Safety and modifications
    safety_tips = Column(Text, nullable=True)
    common_mistakes = Column(Text, nullable=True)
    modifications = Column(JSON, nullable=True)  # List of modifications
    contraindications = Column(Text, nullable=True)
    
    # System info
    is_active = Column(Boolean, default=True)
    is_custom = Column(Boolean, default=False)  # Created by gym vs system default
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Tags for search
    tags = Column(JSON, nullable=True)  # List of tags
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    routine_exercises = relationship("RoutineExercise", back_populates="exercise")
    
    def __repr__(self):
        return f"<Exercise(id={self.id}, name='{self.name}', category='{self.category}')>"
    
    @property
    def difficulty_color(self):
        """Get difficulty color for UI"""
        colors = {
            "beginner": "green",
            "intermediate": "yellow",
            "advanced": "red"
        }
        return colors.get(self.difficulty_level, "gray")
    
    @property
    def muscle_groups_list(self):
        """Get all muscle groups as list"""
        groups = [self.primary_muscle_group]
        if self.secondary_muscle_groups:
            groups.extend(self.secondary_muscle_groups)
        return groups
    
    @property
    def equipment_list(self):
        """Get equipment as list"""
        return self.equipment_needed or []
    
    @property
    def tags_list(self):
        """Get tags as list"""
        return self.tags or []
    
    def matches_search(self, query: str) -> bool:
        """Check if exercise matches search query"""
        query = query.lower()
        return (
            query in self.name.lower() or
            (self.description and query in self.description.lower()) or
            query in self.category.value.lower() or
            query in self.primary_muscle_group.value.lower() or
            any(query in tag.lower() for tag in self.tags_list)
        )