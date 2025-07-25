from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum
from datetime import datetime

class RoutineType(str, enum.Enum):
    """Routine types"""
    WEIGHT_LOSS = "weight_loss"  # Pérdida de peso
    MUSCLE_GAIN = "muscle_gain"  # Ganancia muscular
    STRENGTH = "strength"  # Fuerza
    ENDURANCE = "endurance"  # Resistencia
    FLEXIBILITY = "flexibility"  # Flexibilidad
    REHABILITATION = "rehabilitation"  # Rehabilitación
    FUNCTIONAL = "functional"  # Funcional
    SPORTS_SPECIFIC = "sports_specific"  # Específico del deporte
    GENERAL_FITNESS = "general_fitness"  # Fitness general

class RoutineDifficulty(str, enum.Enum):
    """Routine difficulty levels"""
    BEGINNER = "beginner"  # Principiante
    INTERMEDIATE = "intermediate"  # Intermedio
    ADVANCED = "advanced"  # Avanzado
    EXPERT = "expert"  # Experto

class RoutineTemplate(Base):
    """Routine template model for predefined routines"""
    __tablename__ = "routine_templates"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Classification
    routine_type = Column(Enum(RoutineType), nullable=False)
    difficulty = Column(Enum(RoutineDifficulty), nullable=False)
    
    # Duration and frequency
    duration_weeks = Column(Integer, nullable=False)  # Duration in weeks
    sessions_per_week = Column(Integer, nullable=False)
    session_duration_minutes = Column(Integer, nullable=False)
    
    # Requirements
    equipment_needed = Column(JSON, nullable=True)  # List of equipment
    space_required = Column(String(50), nullable=True)
    experience_required = Column(String(50), nullable=True)
    
    # Goals and benefits
    primary_goals = Column(JSON, nullable=True)  # List of goals
    expected_results = Column(Text, nullable=True)
    
    # Template structure
    template_structure = Column(JSON, nullable=False)  # Detailed routine structure
    
    # Media
    image_url = Column(String(255), nullable=True)
    
    # System info
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Usage stats
    usage_count = Column(Integer, default=0)
    average_rating = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_routine_templates")
    routines = relationship("Routine", back_populates="template")
    
    def __repr__(self):
        return f"<RoutineTemplate(id={self.id}, name='{self.name}', type='{self.routine_type}')>"

class Routine(Base):
    """Routine model for individual user routines"""
    __tablename__ = "routines"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    template_id = Column(Integer, ForeignKey("routine_templates.id"), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Classification
    routine_type = Column(Enum(RoutineType), nullable=False)
    difficulty = Column(Enum(RoutineDifficulty), nullable=False)
    
    # Schedule
    sessions_per_week = Column(Integer, nullable=False)
    session_duration_minutes = Column(Integer, nullable=False)
    
    # Customization
    is_custom = Column(Boolean, default=False)  # Custom vs from template
    notes = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    template = relationship("RoutineTemplate", back_populates="routines")
    user = relationship("User", foreign_keys=[created_by_user_id], back_populates="routines")
    exercises = relationship("RoutineExercise", back_populates="routine", cascade="all, delete-orphan")
    assignments = relationship("RoutineAssignment", back_populates="routine")
    
    def __repr__(self):
        return f"<Routine(id={self.id}, name='{self.name}', created_by={self.created_by_user_id})>"
    
    @property
    def total_exercises(self):
        """Get total number of exercises"""
        return len(self.exercises)
    
    @property
    def estimated_calories(self):
        """Estimate calories burned per session"""
        total_calories = 0
        for routine_exercise in self.exercises:
            if routine_exercise.exercise.calories_per_minute:
                # Estimate time per exercise (sets * reps * rest)
                exercise_time = routine_exercise.sets * 2 + routine_exercise.rest_time / 60
                total_calories += routine_exercise.exercise.calories_per_minute * exercise_time
        return round(total_calories)

class RoutineExercise(Base):
    """Exercise within a routine with specific parameters"""
    __tablename__ = "routine_exercises"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    routine_id = Column(Integer, ForeignKey("routines.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    
    # Exercise parameters
    sets = Column(Integer, nullable=False)
    reps = Column(String(50), nullable=False)  # "8-12" or "30 seconds"
    weight = Column(Float, nullable=True)  # kg
    rest_time = Column(Integer, nullable=False)  # seconds
    
    # Order and grouping
    order_index = Column(Integer, nullable=False)  # Order within routine
    superset_group = Column(String(10), nullable=True)  # Group exercises in supersets
    
    # Notes and modifications
    notes = Column(Text, nullable=True)
    modifications = Column(Text, nullable=True)
    
    # Progression tracking
    progression_type = Column(String(20), nullable=True)  # weight, reps, time, distance
    progression_increment = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    routine = relationship("Routine", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="routine_exercises")
    
    def __repr__(self):
        return f"<RoutineExercise(id={self.id}, routine_id={self.routine_id}, exercise_id={self.exercise_id})>"
    
    @property
    def estimated_duration_minutes(self):
        """Estimate duration for this exercise"""
        # Rough estimate: sets * 2 minutes + rest time
        return self.sets * 2 + (self.rest_time * (self.sets - 1)) / 60

class RoutineAssignment(Base):
    """Assignment of routine to user with tracking"""
    __tablename__ = "routine_assignments"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    routine_id = Column(Integer, ForeignKey("routines.id"), nullable=False)
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Assignment details
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Progress tracking
    sessions_completed = Column(Integer, default=0)
    sessions_planned = Column(Integer, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    completion_percentage = Column(Float, default=0.0)
    
    # Notes
    trainer_notes = Column(Text, nullable=True)
    user_feedback = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_session_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="routine_assignments")
    routine = relationship("Routine", back_populates="assignments")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id], back_populates="assigned_routine_assignments")
    
    def __repr__(self):
        return f"<RoutineAssignment(id={self.id}, user_id={self.user_id}, routine_id={self.routine_id})>"
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.sessions_planned == 0:
            return 0
        return min(100, (self.sessions_completed / self.sessions_planned) * 100)
    
    @property
    def is_completed(self):
        """Check if routine is completed"""
        return self.sessions_completed >= self.sessions_planned
    
    @property
    def status_text(self):
        """Get human readable status"""
        if not self.is_active:
            return "Inactiva"
        elif self.is_completed:
            return "Completada"
        elif self.sessions_completed == 0:
            return "No iniciada"
        else:
            return "En progreso"