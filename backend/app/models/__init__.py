# Import all models here to make them available
# This ensures SQLAlchemy can create all tables
import logging

logger = logging.getLogger(__name__)

# Core models - import with error handling
try:
    from .user import User
    logger.info("User model imported successfully")
except ImportError as e:
    logger.error(f"Failed to import User model: {e}")
    User = None

try:
    from .membership import Membership, Payment
    logger.info("Membership models imported successfully")
except ImportError as e:
    logger.error(f"Failed to import Membership models: {e}")
    Membership = Payment = None

try:
    from .exercise import Exercise
    logger.info("Exercise model imported successfully")
except ImportError as e:
    logger.error(f"Failed to import Exercise model: {e}")
    Exercise = None

try:
    from .routine import RoutineTemplate, Routine, RoutineExercise, RoutineAssignment
    logger.info("Routine models imported successfully")
except ImportError as e:
    logger.error(f"Failed to import Routine models: {e}")
    RoutineTemplate = Routine = RoutineExercise = RoutineAssignment = None

try:
    from .class_model import Class
    logger.info("Class model imported successfully")
except ImportError as e:
    logger.error(f"Failed to import Class model: {e}")
    Class = None

try:
    from .class_reservation import ClassReservation, ClassAttendance
    logger.info("Class reservation models imported successfully")
except ImportError as e:
    logger.error(f"Failed to import Class reservation models: {e}")
    ClassReservation = ClassAttendance = None

try:
    from .checkin import CheckIn
    logger.info("CheckIn model imported successfully")
except ImportError as e:
    logger.error(f"Failed to import CheckIn model: {e}")
    CheckIn = None

try:
    from .employee import Employee
    logger.info("Employee model imported successfully")
except ImportError as e:
    logger.error(f"Failed to import Employee model: {e}")
    Employee = None

try:
    from .user_progress import UserProgress, ProgressPhoto
    logger.info("User progress models imported successfully")
except ImportError as e:
    logger.error(f"Failed to import User progress models: {e}")
    UserProgress = ProgressPhoto = None

try:
    from .configuration import Configuration, NotificationTemplate, SystemLog
    logger.info("Configuration models imported successfully")
except ImportError as e:
    logger.error(f"Failed to import Configuration models: {e}")
    Configuration = NotificationTemplate = SystemLog = None

# Service models - import with error handling (these may not exist yet)
AuditLogModel = None
ConfigModel = None
ConfigHistoryModel = None

try:
    from ..services.audit_service import AuditLogModel
    logger.info("AuditLogModel imported successfully")
except ImportError as e:
    logger.warning(f"AuditLogModel not available: {e}")

try:
    from ..services.config_service import ConfigModel, ConfigHistoryModel
    logger.info("Config service models imported successfully")
except ImportError as e:
    logger.warning(f"Config service models not available: {e}")

# Only include models that were successfully imported
__all__ = []
for model_name, model_class in [
    ("User", User),
    ("Membership", Membership),
    ("Payment", Payment),
    ("Exercise", Exercise),
    ("RoutineTemplate", RoutineTemplate),
    ("Routine", Routine),
    ("RoutineExercise", RoutineExercise),
    ("RoutineAssignment", RoutineAssignment),
    ("Class", Class),
    ("ClassReservation", ClassReservation),
    ("ClassAttendance", ClassAttendance),
    ("CheckIn", CheckIn),
    ("Employee", Employee),
    ("UserProgress", UserProgress),
    ("ProgressPhoto", ProgressPhoto),
    ("Configuration", Configuration),
    ("NotificationTemplate", NotificationTemplate),
    ("SystemLog", SystemLog),
    ("AuditLogModel", AuditLogModel),
    ("ConfigModel", ConfigModel),
    ("ConfigHistoryModel", ConfigHistoryModel)
]:
    if model_class is not None:
        __all__.append(model_name)

logger.info(f"Models initialization completed. Available models: {__all__}")