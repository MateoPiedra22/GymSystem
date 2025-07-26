from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

# Create main API router
api_router = APIRouter()

# Import and include API routers with error handling
try:
    from ...api import auth
    api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
    logger.info("Auth router included successfully")
except ImportError as e:
    logger.warning(f"Auth router not available: {e}")

try:
    from ...api import users
    api_router.include_router(users.router, prefix="/users", tags=["users"])
    logger.info("Users router included successfully")
except ImportError as e:
    logger.warning(f"Users router not available: {e}")

try:
    from ...api import employees
    api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
    logger.info("Employees router included successfully")
except ImportError as e:
    logger.warning(f"Employees router not available: {e}")

try:
    from ...api import memberships
    api_router.include_router(memberships.router, prefix="/memberships", tags=["memberships"])
    logger.info("Memberships router included successfully")
except ImportError as e:
    logger.warning(f"Memberships router not available: {e}")

try:
    from ...api import classes
    api_router.include_router(classes.router, prefix="/classes", tags=["classes"])
    logger.info("Classes router included successfully")
except ImportError as e:
    logger.warning(f"Classes router not available: {e}")

try:
    from ...api import routines
    api_router.include_router(routines.router, prefix="/routines", tags=["routines"])
    logger.info("Routines router included successfully")
except ImportError as e:
    logger.warning(f"Routines router not available: {e}")

try:
    from ...api import exercises
    api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
    logger.info("Exercises router included successfully")
except ImportError as e:
    logger.warning(f"Exercises router not available: {e}")

try:
    from ...api import payments
    api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
    logger.info("Payments router included successfully")
except ImportError as e:
    logger.warning(f"Payments router not available: {e}")

try:
    from ...api import reports
    api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
    logger.info("Reports router included successfully")
except ImportError as e:
    logger.warning(f"Reports router not available: {e}")

logger.info("API router initialization completed")