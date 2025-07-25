# Import all models here to make them available
# This ensures SQLAlchemy can create all tables

from .user import User
from .membership import Membership, Payment
from .exercise import Exercise
from .routine import RoutineTemplate, Routine, RoutineExercise, RoutineAssignment
from .class_model import Class
from .class_reservation import ClassReservation, ClassAttendance
from .checkin import CheckIn
from .employee import Employee
from .user_progress import UserProgress, ProgressPhoto
from .configuration import Configuration, NotificationTemplate, SystemLog
from ..services.audit_service import AuditLogModel

__all__ = [
    "User",
    "Membership", 
    "Payment",
    "Exercise",
    "RoutineTemplate",
    "Routine", 
    "RoutineExercise",
    "RoutineAssignment",
    "Class",
    "ClassReservation",
    "ClassAttendance",
    "CheckIn",
    "Employee",
    "UserProgress",
    "ProgressPhoto",
    "Configuration",
    "NotificationTemplate",
    "SystemLog",
    "AuditLogModel"
]