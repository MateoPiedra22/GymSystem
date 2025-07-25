from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON, Enum, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum
from datetime import datetime, time

class ClassStatus(str, enum.Enum):
    """Class status options"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"

class ClassType(str, enum.Enum):
    """Class type options"""
    GROUP_FITNESS = "group_fitness"
    PERSONAL_TRAINING = "personal_training"
    YOGA = "yoga"
    PILATES = "pilates"
    SPINNING = "spinning"
    CROSSFIT = "crossfit"
    ZUMBA = "zumba"
    AQUA_FITNESS = "aqua_fitness"
    MARTIAL_ARTS = "martial_arts"
    DANCE = "dance"
    STRENGTH_TRAINING = "strength_training"
    CARDIO = "cardio"
    STRETCHING = "stretching"
    REHABILITATION = "rehabilitation"
    OTHER = "other"

class DifficultyLevel(str, enum.Enum):
    """Difficulty level options"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ALL_LEVELS = "all_levels"

class Class(Base):
    """Gym class model"""
    __tablename__ = "classes"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    class_type = Column(Enum(ClassType), nullable=False, index=True)
    difficulty_level = Column(Enum(DifficultyLevel), nullable=False, default=DifficultyLevel.ALL_LEVELS)
    
    # Instructor
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    substitute_instructor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Schedule
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)  # Duration in minutes
    
    # Recurring schedule (for regular classes)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # Days of week, frequency, etc.
    
    # Capacity and booking
    max_capacity = Column(Integer, nullable=False, default=20)
    min_capacity = Column(Integer, nullable=False, default=1)
    current_bookings = Column(Integer, nullable=False, default=0)
    waiting_list_enabled = Column(Boolean, default=True)
    
    # Location and equipment
    room = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)
    required_equipment = Column(JSON, nullable=True)  # List of required equipment
    
    # Pricing
    price = Column(Float, nullable=True)  # Price per class (if not included in membership)
    credits_required = Column(Integer, nullable=True)  # Credits needed to book
    
    # Status and settings
    status = Column(Enum(ClassStatus), nullable=False, default=ClassStatus.SCHEDULED)
    is_active = Column(Boolean, default=True)
    allow_drop_ins = Column(Boolean, default=True)
    cancellation_deadline_hours = Column(Integer, default=24)  # Hours before class
    
    # Class details
    prerequisites = Column(Text, nullable=True)
    what_to_bring = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)
    
    # Media
    image_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    
    # Ratings and feedback
    average_rating = Column(Float, nullable=True)
    total_ratings = Column(Integer, default=0)
    
    # Notes
    instructor_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # System info
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    instructor = relationship("User", foreign_keys=[instructor_id], back_populates="taught_classes")
    substitute_instructor = relationship("User", foreign_keys=[substitute_instructor_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    # Reverse relationships
    reservations = relationship("ClassReservation", back_populates="gym_class", cascade="all, delete-orphan")
    attendances = relationship("ClassAttendance", back_populates="gym_class", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Class(id={self.id}, name='{self.name}', start_time='{self.start_time}')>"
    
    @property
    def is_full(self):
        """Check if class is at capacity"""
        return self.current_bookings >= self.max_capacity
    
    @property
    def available_spots(self):
        """Get number of available spots"""
        return max(0, self.max_capacity - self.current_bookings)
    
    @property
    def occupancy_rate(self):
        """Get occupancy rate as percentage"""
        if self.max_capacity == 0:
            return 0
        return round((self.current_bookings / self.max_capacity) * 100, 1)
    
    @property
    def is_past(self):
        """Check if class is in the past"""
        return self.end_time < datetime.now()
    
    @property
    def is_upcoming(self):
        """Check if class is upcoming (within next 24 hours)"""
        now = datetime.now()
        return self.start_time > now and (self.start_time - now).total_seconds() <= 86400
    
    @property
    def can_be_cancelled(self):
        """Check if class can still be cancelled by users"""
        if not self.cancellation_deadline_hours:
            return True
        
        deadline = self.start_time.timestamp() - (self.cancellation_deadline_hours * 3600)
        return datetime.now().timestamp() < deadline
    
    def cancel_class(self, reason: str = None):
        """Cancel the class"""
        self.status = ClassStatus.CANCELLED
        if reason:
            self.admin_notes = f"{self.admin_notes or ''}\nCancelled: {reason}"
    
    def start_class(self):
        """Mark class as in progress"""
        self.status = ClassStatus.IN_PROGRESS
    
    def complete_class(self):
        """Mark class as completed"""
        self.status = ClassStatus.COMPLETED
    
    def add_booking(self):
        """Add a booking to the class"""
        if not self.is_full:
            self.current_bookings += 1
            return True
        return False
    
    def remove_booking(self):
        """Remove a booking from the class"""
        if self.current_bookings > 0:
            self.current_bookings -= 1
            return True
        return False
    
    def update_rating(self, new_rating: float):
        """Update class average rating"""
        if self.total_ratings == 0:
            self.average_rating = new_rating
        else:
            total_score = (self.average_rating or 0) * self.total_ratings
            total_score += new_rating
            self.total_ratings += 1
            self.average_rating = round(total_score / self.total_ratings, 2)
        
        if self.total_ratings == 0:
            self.total_ratings = 1