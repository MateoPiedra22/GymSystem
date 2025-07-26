from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    """User roles in the system"""
    ADMIN = "admin"  # Control total del sistema
    OWNER = "owner"  # Dueño del gimnasio
    TRAINER = "trainer"  # Entrenador/Empleado
    MEMBER = "member"  # Miembro del gimnasio

class UserType(str, enum.Enum):
    """User membership types"""
    MONTHLY = "monthly"  # Cuota mensual
    STUDENT = "student"  # Cuota estudiante
    FUNCTIONAL = "functional"  # Cuota funcional
    WEEKLY = "weekly"  # Cuota semanal
    DAILY = "daily"  # Cuota diaria
    PROMOTIONAL = "promotional"  # Cuota promocional

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    user_id = Column(String(20), unique=True, index=True, nullable=False)  # Custom ID for login
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)  # With +54 prefix
    password_hash = Column(String(255), nullable=False)
    
    # Personal info
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)  # male, female, other
    profile_photo = Column(String(255), nullable=True)
    
    # Contact info
    address = Column(Text, nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    
    # Medical info
    medical_conditions = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    
    # Fitness info
    fitness_goals = Column(Text, nullable=True)
    experience_level = Column(String(20), nullable=True)  # beginner, intermediate, advanced
    preferred_workout_time = Column(String(20), nullable=True)  # morning, afternoon, evening
    
    # System info
    role = Column(Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    user_type = Column(Enum(UserType), nullable=True)  # Only for members and trainers
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0)
    
    # Relationships
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    routines = relationship("Routine", foreign_keys="Routine.created_by_user_id", back_populates="user", cascade="all, delete-orphan")
    routine_assignments = relationship("RoutineAssignment", foreign_keys="RoutineAssignment.user_id", back_populates="user", cascade="all, delete-orphan")
    class_reservations = relationship("ClassReservation", foreign_keys="ClassReservation.user_id", back_populates="user", cascade="all, delete-orphan")
    class_attendances = relationship("ClassAttendance", foreign_keys="ClassAttendance.user_id", back_populates="user", cascade="all, delete-orphan")
    check_ins = relationship("CheckIn", foreign_keys="CheckIn.user_id", back_populates="user", cascade="all, delete-orphan")
    progress_records = relationship("UserProgress", foreign_keys="UserProgress.user_id", back_populates="user", cascade="all, delete-orphan")
    progress_photos = relationship("ProgressPhoto", foreign_keys="ProgressPhoto.user_id", back_populates="user", cascade="all, delete-orphan")
    
    # Employee relationships (if trainer/employee)
    employee_profile = relationship("Employee", foreign_keys="Employee.user_id", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Employees created by this user (for admin/owner users)
    created_employees = relationship("Employee", foreign_keys="Employee.created_by", back_populates="created_by_user")
    
    # Routine template relationships
    created_routine_templates = relationship("RoutineTemplate", foreign_keys="RoutineTemplate.created_by_user_id", back_populates="created_by")
    
    # Routine assignment relationships (as assigner)
    assigned_routine_assignments = relationship("RoutineAssignment", foreign_keys="RoutineAssignment.assigned_by_user_id", back_populates="assigned_by")
    
    # Trainer relationships (classes taught)
    taught_classes = relationship("Class", foreign_keys="Class.instructor_id", back_populates="instructor")
    
    # Audit logs for this user
    audit_logs = relationship("AuditLogModel", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, user_id='{self.user_id}', email='{self.email}', role='{self.role}')>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_staff(self):
        """Check if user has staff privileges"""
        return self.role in [UserRole.ADMIN, UserRole.OWNER, UserRole.TRAINER]
    
    @property
    def can_access_admin(self):
        """Check if user can access admin panel"""
        return self.role in [UserRole.ADMIN, UserRole.OWNER]
    
    @property
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role in [UserRole.ADMIN, UserRole.OWNER]
    
    @property
    def can_manage_classes(self):
        """Check if user can manage classes"""
        return self.role in [UserRole.ADMIN, UserRole.OWNER, UserRole.TRAINER]
    
    @property
    def can_create_routines(self):
        """Check if user can create routines"""
        return self.role in [UserRole.ADMIN, UserRole.OWNER, UserRole.TRAINER]