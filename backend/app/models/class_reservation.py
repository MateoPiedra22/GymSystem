from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum
from datetime import datetime

class ReservationStatus(str, enum.Enum):
    """Reservation status options"""
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class ClassReservation(Base):
    """Class reservation model"""
    __tablename__ = "class_reservations"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    
    # Reservation details
    reservation_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(Enum(ReservationStatus), nullable=False, default=ReservationStatus.CONFIRMED)
    
    # Additional info
    notes = Column(Text, nullable=True)
    special_requirements = Column(Text, nullable=True)
    
    # Cancellation info
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    cancelled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # System info
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="class_reservations")
    gym_class = relationship("Class", back_populates="reservations")
    created_by_user = relationship("User", foreign_keys=[created_by])
    cancelled_by_user = relationship("User", foreign_keys=[cancelled_by])
    
    def __repr__(self):
        return f"<ClassReservation(id={self.id}, user_id={self.user_id}, class_id={self.class_id}, status='{self.status}')>"
    
    @property
    def can_cancel(self):
        """Check if reservation can be cancelled"""
        return self.status in [ReservationStatus.CONFIRMED, ReservationStatus.PENDING]
    
    @property
    def is_active(self):
        """Check if reservation is active"""
        return self.status in [ReservationStatus.CONFIRMED, ReservationStatus.PENDING]
    
    def cancel(self, reason: str = None, cancelled_by_user_id: int = None):
        """Cancel the reservation"""
        if self.can_cancel:
            self.status = ReservationStatus.CANCELLED
            self.cancelled_at = datetime.utcnow()
            self.cancellation_reason = reason
            self.cancelled_by = cancelled_by_user_id
    
    def mark_no_show(self):
        """Mark as no-show"""
        if self.status == ReservationStatus.CONFIRMED:
            self.status = ReservationStatus.NO_SHOW
    
    def complete(self):
        """Mark as completed"""
        if self.status == ReservationStatus.CONFIRMED:
            self.status = ReservationStatus.COMPLETED

class ClassAttendance(Base):
    """Class attendance tracking model"""
    __tablename__ = "class_attendances"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    reservation_id = Column(Integer, ForeignKey("class_reservations.id"), nullable=True, index=True)
    
    # Attendance details
    attended_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    attendance_method = Column(String(20), nullable=False, default="manual")  # manual, qr_code, check_in
    
    # Performance tracking
    performance_rating = Column(Integer, nullable=True)  # 1-5 scale
    instructor_notes = Column(Text, nullable=True)
    user_feedback = Column(Text, nullable=True)
    
    # System info
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="class_attendances")
    gym_class = relationship("Class", back_populates="attendances")
    reservation = relationship("ClassReservation")
    recorded_by_user = relationship("User", foreign_keys=[recorded_by])
    
    def __repr__(self):
        return f"<ClassAttendance(id={self.id}, user_id={self.user_id}, class_id={self.class_id}, attended_at='{self.attended_at}')>"