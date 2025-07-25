from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
from datetime import datetime

class CheckIn(Base):
    """Check-in model for gym access tracking"""
    __tablename__ = "check_ins"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Check-in details
    check_in_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    
    # Location and method
    location = Column(String(100), nullable=True)  # Which gym location
    check_in_method = Column(String(20), nullable=False, default="manual")  # manual, qr_code, card, app
    
    # Session details
    duration_minutes = Column(Integer, nullable=True)  # Calculated on check-out
    notes = Column(Text, nullable=True)
    
    # System info
    is_active = Column(Boolean, default=True)  # False if checked out
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Staff member who registered
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="check_ins")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<CheckIn(id={self.id}, user_id={self.user_id}, check_in_time='{self.check_in_time}')>"
    
    @property
    def session_duration(self):
        """Calculate session duration in minutes"""
        if self.check_out_time and self.check_in_time:
            delta = self.check_out_time - self.check_in_time
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def is_checked_out(self):
        """Check if user has checked out"""
        return self.check_out_time is not None
    
    @property
    def status_text(self):
        """Get human readable status"""
        if self.is_checked_out:
            return "Finalizada"
        else:
            return "En curso"
    
    def check_out(self):
        """Mark check-in as completed"""
        if not self.check_out_time:
            self.check_out_time = datetime.utcnow()
            self.is_active = False
            if self.check_in_time:
                delta = self.check_out_time - self.check_in_time
                self.duration_minutes = int(delta.total_seconds() / 60)