from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
from datetime import datetime

class UserProgress(Base):
    """User progress tracking model"""
    __tablename__ = "user_progress"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Progress date
    progress_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Body measurements
    weight = Column(Float, nullable=True)  # kg
    height = Column(Float, nullable=True)  # cm
    body_fat_percentage = Column(Float, nullable=True)
    muscle_mass = Column(Float, nullable=True)  # kg
    
    # Body measurements (circumferences in cm)
    chest = Column(Float, nullable=True)
    waist = Column(Float, nullable=True)
    hips = Column(Float, nullable=True)
    bicep_left = Column(Float, nullable=True)
    bicep_right = Column(Float, nullable=True)
    thigh_left = Column(Float, nullable=True)
    thigh_right = Column(Float, nullable=True)
    
    # Fitness metrics
    resting_heart_rate = Column(Integer, nullable=True)  # bpm
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    
    # Performance metrics
    max_bench_press = Column(Float, nullable=True)  # kg
    max_squat = Column(Float, nullable=True)  # kg
    max_deadlift = Column(Float, nullable=True)  # kg
    cardio_endurance = Column(Float, nullable=True)  # minutes or distance
    
    # Custom metrics (JSON for flexibility)
    custom_metrics = Column(JSON, nullable=True)
    
    # Goals and notes
    goals = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    trainer_notes = Column(Text, nullable=True)
    
    # System info
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="progress_records")
    recorded_by_user = relationship("User", foreign_keys=[recorded_by])
    
    def __repr__(self):
        return f"<UserProgress(id={self.id}, user_id={self.user_id}, progress_date='{self.progress_date}')>"
    
    @property
    def bmi(self):
        """Calculate BMI if weight and height are available"""
        if self.weight and self.height:
            height_m = self.height / 100  # Convert cm to meters
            return round(self.weight / (height_m ** 2), 2)
        return None
    
    @property
    def bmi_category(self):
        """Get BMI category"""
        bmi = self.bmi
        if not bmi:
            return None
        
        if bmi < 18.5:
            return "Bajo peso"
        elif bmi < 25:
            return "Peso normal"
        elif bmi < 30:
            return "Sobrepeso"
        else:
            return "Obesidad"

class ProgressPhoto(Base):
    """Progress photos model"""
    __tablename__ = "progress_photos"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    progress_id = Column(Integer, ForeignKey("user_progress.id"), nullable=True, index=True)
    
    # Photo details
    photo_url = Column(String(500), nullable=False)
    photo_type = Column(String(20), nullable=False)  # front, side, back, custom
    description = Column(Text, nullable=True)
    
    # Photo metadata
    file_size = Column(Integer, nullable=True)  # bytes
    file_format = Column(String(10), nullable=True)  # jpg, png, etc.
    
    # Progress tracking
    photo_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # System info
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="progress_photos")
    progress_record = relationship("UserProgress")
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f"<ProgressPhoto(id={self.id}, user_id={self.user_id}, photo_type='{self.photo_type}')>"
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None