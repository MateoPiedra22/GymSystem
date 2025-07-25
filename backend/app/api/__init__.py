"""API package for GymSystem.

This package contains all the API endpoints and routes for the GymSystem application.
It includes modules for authentication, user management, memberships, exercises,
routines, classes, employees, payments, and reports.
"""

from . import (
    auth,
    users,
    memberships,
    exercises,
    routines,
    classes,
    employees,
    payments,
    reports
)

__all__ = [
    "auth",
    "users", 
    "memberships",
    "exercises",
    "routines",
    "classes",
    "employees",
    "payments",
    "reports"
]