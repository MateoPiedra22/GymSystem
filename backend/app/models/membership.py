from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime, date

class MembershipType(str, enum.Enum):
    """Membership types available"""
    MONTHLY = "monthly"  # Cuota mensual
    STUDENT = "student"  # Cuota estudiante
    FUNCTIONAL = "functional"  # Cuota funcional
    WEEKLY = "weekly"  # Cuota semanal
    DAILY = "daily"  # Cuota diaria
    PROMOTIONAL = "promotional"  # Cuota promocional

class PaymentStatus(str, enum.Enum):
    """Payment status"""
    PENDING = "pending"  # Pendiente
    PAID = "paid"  # Pagado
    OVERDUE = "overdue"  # Vencido
    CANCELLED = "cancelled"  # Cancelado
    REFUNDED = "refunded"  # Reembolsado

class Membership(Base):
    """Membership model"""
    __tablename__ = "memberships"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Membership details
    membership_type = Column(Enum(MembershipType), nullable=False)
    price = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=True)
    
    # Additional benefits
    includes_classes = Column(Boolean, default=True)
    includes_personal_training = Column(Boolean, default=False)
    includes_nutrition_plan = Column(Boolean, default=False)
    max_classes_per_month = Column(Integer, nullable=True)  # null = unlimited
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="memberships")
    payments = relationship("Payment", back_populates="membership")
    
    def __repr__(self):
        return f"<Membership(id={self.id}, user_id={self.user_id}, type='{self.membership_type}', active={self.is_active})>"
    
    @property
    def is_expired(self):
        """Check if membership is expired"""
        return date.today() > self.end_date
    
    @property
    def days_remaining(self):
        """Get days remaining in membership"""
        if self.is_expired:
            return 0
        return (self.end_date - date.today()).days
    
    @property
    def status_text(self):
        """Get human readable status"""
        if not self.is_active:
            return "Inactiva"
        elif self.is_expired:
            return "Vencida"
        elif self.days_remaining <= 7:
            return "Por vencer"
        else:
            return "Activa"

class Payment(Base):
    """Payment model"""
    __tablename__ = "payments"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    membership_id = Column(Integer, ForeignKey("memberships.id"), nullable=True)
    
    # Payment details
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)  # cash, card, transfer, etc.
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Dates
    due_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=True)
    
    # Receipt info
    receipt_number = Column(String(50), unique=True, nullable=True)
    receipt_url = Column(String(255), nullable=True)
    
    # Description
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # WhatsApp notifications
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="payments")
    membership = relationship("Membership", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status='{self.status}')>"
    
    @property
    def is_overdue(self):
        """Check if payment is overdue"""
        return self.status == PaymentStatus.PENDING and date.today() > self.due_date
    
    @property
    def days_overdue(self):
        """Get days overdue"""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days
    
    @property
    def status_color(self):
        """Get status color for UI"""
        colors = {
            PaymentStatus.PAID: "green",
            PaymentStatus.PENDING: "yellow",
            PaymentStatus.OVERDUE: "red",
            PaymentStatus.CANCELLED: "gray",
            PaymentStatus.REFUNDED: "blue"
        }
        return colors.get(self.status, "gray")