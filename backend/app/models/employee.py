from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum
from datetime import datetime, date

class EmployeeStatus(str, enum.Enum):
    """Employee status options"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"

class ContractType(str, enum.Enum):
    """Contract type options"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERN = "intern"

class ShiftType(str, enum.Enum):
    """Shift type options"""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    SPLIT = "split"
    FLEXIBLE = "flexible"

class Employee(Base):
    """Employee profile model"""
    __tablename__ = "employees"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Employee details
    employee_id = Column(String(20), unique=True, nullable=False, index=True)
    position = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    
    # Employment details
    hire_date = Column(DateTime, nullable=False)
    termination_date = Column(DateTime, nullable=True)
    contract_type = Column(Enum(ContractType), nullable=False, default=ContractType.FULL_TIME)
    status = Column(Enum(EmployeeStatus), nullable=False, default=EmployeeStatus.ACTIVE)
    
    # Compensation
    salary = Column(Float, nullable=True)  # Monthly salary
    hourly_rate = Column(Float, nullable=True)  # For hourly employees
    commission_rate = Column(Float, nullable=True)  # For sales/trainers
    
    # Work schedule
    work_schedule = Column(JSON, nullable=True)  # Weekly schedule
    max_hours_per_week = Column(Integer, nullable=True)
    
    # Certifications and qualifications
    certifications = Column(JSON, nullable=True)  # List of certifications
    specializations = Column(JSON, nullable=True)  # Training specializations
    education = Column(Text, nullable=True)
    
    # Performance
    performance_rating = Column(Float, nullable=True)  # 1-5 scale
    last_review_date = Column(DateTime, nullable=True)
    next_review_date = Column(DateTime, nullable=True)
    
    # Contact and emergency
    work_phone = Column(String(20), nullable=True)
    work_email = Column(String(255), nullable=True)
    emergency_contact = Column(JSON, nullable=True)  # Emergency contact info
    
    # Benefits and permissions
    benefits = Column(JSON, nullable=True)  # Health, vacation, etc.
    permissions = Column(JSON, nullable=True)  # System permissions
    access_level = Column(Integer, nullable=False, default=1)  # 1-5 access level
    
    # Notes and comments
    notes = Column(Text, nullable=True)
    hr_notes = Column(Text, nullable=True)
    
    # System info
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="employee_profile")
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="created_employees")
    
    def __repr__(self):
        return f"<Employee(id={self.id}, employee_id='{self.employee_id}', position='{self.position}')>"
    
    @property
    def is_active(self):
        """Check if employee is active"""
        return self.status == EmployeeStatus.ACTIVE
    
    @property
    def years_of_service(self):
        """Calculate years of service"""
        if not self.hire_date:
            return 0
        
        end_date = self.termination_date or datetime.now()
        delta = end_date - self.hire_date
        return round(delta.days / 365.25, 1)
    
    @property
    def is_trainer(self):
        """Check if employee is a trainer"""
        return "trainer" in self.position.lower() or "entrenador" in self.position.lower()
    
    @property
    def monthly_compensation(self):
        """Calculate estimated monthly compensation"""
        if self.salary:
            return self.salary
        elif self.hourly_rate and self.max_hours_per_week:
            # Estimate monthly from hourly rate
            weekly_pay = self.hourly_rate * self.max_hours_per_week
            return weekly_pay * 4.33  # Average weeks per month
        return None
    
    def terminate(self, termination_date: datetime = None, reason: str = None):
        """Terminate employee"""
        self.status = EmployeeStatus.TERMINATED
        self.termination_date = termination_date or datetime.now()
        if reason:
            self.notes = f"{self.notes or ''}\nTermination reason: {reason}"
    
    def reactivate(self):
        """Reactivate employee"""
        if self.status == EmployeeStatus.TERMINATED:
            self.status = EmployeeStatus.ACTIVE
            self.termination_date = None
    
    def update_performance(self, rating: float, notes: str = None):
        """Update performance rating"""
        self.performance_rating = max(1, min(5, rating))  # Ensure 1-5 range
        self.last_review_date = datetime.now()
        # Set next review date (1 year from now)
        self.next_review_date = datetime(datetime.now().year + 1, datetime.now().month, datetime.now().day)
        if notes:
            self.hr_notes = f"{self.hr_notes or ''}\n{datetime.now().strftime('%Y-%m-%d')}: {notes}"