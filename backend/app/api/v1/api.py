from fastapi import APIRouter

# Import all API routers
from .. import (
    auth,
    users,
    employees,
    memberships,
    classes,
    routines,
    exercises,
    payments,
    reports
)

# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(memberships.router, prefix="/memberships", tags=["memberships"])
api_router.include_router(classes.router, prefix="/classes", tags=["classes"])
api_router.include_router(routines.router, prefix="/routines", tags=["routines"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])