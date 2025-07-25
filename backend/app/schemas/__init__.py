# Import all schemas here

from .user import (
    UserBase, UserCreate, UserUpdate, UserResponse,
    UserLogin, UserRegister, Token, TokenData,
    PasswordChange, PasswordReset, PasswordResetConfirm,
    UserList, UserStats
)
from .membership import (
    MembershipBase, MembershipCreate, MembershipUpdate, MembershipResponse,
    PaymentBase, PaymentCreate, PaymentUpdate, PaymentResponse,
    MembershipBulkCreate, PaymentBulkCreate,
    MembershipList, PaymentList, MembershipStats
)
from .exercise import (
    ExerciseBase, ExerciseCreate, ExerciseUpdate, ExerciseResponse,
    ExerciseBulkCreate, ExerciseBulkUpdate, ExerciseFilter, ExerciseSearch,
    ExerciseList, ExerciseStats, ExerciseImport, ExerciseExport,
    CustomExerciseCreate, ExerciseTemplate, ExerciseProgression, ExerciseProgressionResponse
)
from .routine import (
    RoutineTemplateBase, RoutineTemplateCreate, RoutineTemplateUpdate, RoutineTemplateResponse,
    RoutineBase, RoutineCreate, RoutineUpdate, RoutineResponse,
    RoutineExerciseBase, RoutineExerciseCreate, RoutineExerciseUpdate, RoutineExerciseResponse,
    RoutineAssignmentBase, RoutineAssignmentCreate, RoutineAssignmentUpdate, RoutineAssignmentResponse,
    RoutineBulkAssign, RoutineTemplateList, RoutineList, RoutineAssignmentList,
    RoutineStats, RoutineProgress, RoutineProgressResponse,
    WorkoutSession, WorkoutSessionResponse
)
from .class_schema import (
    ClassBase, ClassCreate, ClassUpdate, ClassResponse,
    ClassReservationBase, ClassReservationCreate, ClassReservationUpdate, ClassReservationResponse,
    ClassAttendanceBase, ClassAttendanceCreate, ClassAttendanceUpdate, ClassAttendanceResponse,
    ClassBulkCreate, ReservationBulkCreate,
    ClassList, ClassReservationList, ClassAttendanceList,
    ClassFilter, ClassStats, ClassSchedule, WeeklySchedule,
    RecurringClassCreate, WaitlistEntry, WaitlistResponse
)
from .employee import (
    EmployeeBase, EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    EmployeeBulkUpdate,
    EmployeeList,
    EmployeeFilter, EmployeeStats,
    PayrollPeriod, PayrollSummary, PerformanceReview, PerformanceReviewResponse
)
from .configuration import (
    ConfigurationBase, ConfigurationCreate, ConfigurationUpdate, ConfigurationResponse,
    NotificationTemplateBase, NotificationTemplateCreate, NotificationTemplateUpdate, NotificationTemplateResponse,
    ThemeSettings, NotificationSettings, SecuritySettings, IntegrationSettings,
    BusinessSettings, BackupSettings, MaintenanceMode, FeatureFlags,
    CustomField, CustomFieldsConfig, SystemStatus, NotificationTemplateList,
    ConfigurationExport, ConfigurationImport
)

__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserResponse",
    "UserLogin", "UserRegister", "Token", "TokenData",
    "PasswordChange", "PasswordReset", "PasswordResetConfirm",
    "UserList", "UserStats",
    
    # Membership schemas
    "MembershipBase", "MembershipCreate", "MembershipUpdate", "MembershipResponse",
    "PaymentBase", "PaymentCreate", "PaymentUpdate", "PaymentResponse",
    "MembershipBulkCreate", "PaymentBulkCreate",
    "MembershipList", "PaymentList", "MembershipStats",
    
    # Exercise schemas
    "ExerciseBase", "ExerciseCreate", "ExerciseUpdate", "ExerciseResponse",
    "ExerciseBulkCreate", "ExerciseBulkUpdate", "ExerciseFilter", "ExerciseSearch",
    "ExerciseList", "ExerciseStats", "ExerciseImport", "ExerciseExport",
    "CustomExerciseCreate", "ExerciseTemplate", "ExerciseProgression", "ExerciseProgressionResponse",
    
    # Routine schemas
    "RoutineTemplateBase", "RoutineTemplateCreate", "RoutineTemplateUpdate", "RoutineTemplateResponse",
    "RoutineBase", "RoutineCreate", "RoutineUpdate", "RoutineResponse",
    "RoutineExerciseBase", "RoutineExerciseCreate", "RoutineExerciseUpdate", "RoutineExerciseResponse",
    "RoutineAssignmentBase", "RoutineAssignmentCreate", "RoutineAssignmentUpdate", "RoutineAssignmentResponse",
    "RoutineBulkAssign", "RoutineTemplateList", "RoutineList", "RoutineAssignmentList",
    "RoutineStats", "RoutineProgress", "RoutineProgressResponse",
    "WorkoutSession", "WorkoutSessionResponse",
    
    # Class schemas
    "ClassBase", "ClassCreate", "ClassUpdate", "ClassResponse",
    "ClassReservationBase", "ClassReservationCreate", "ClassReservationUpdate", "ClassReservationResponse",
    "ClassAttendanceBase", "ClassAttendanceCreate", "ClassAttendanceUpdate", "ClassAttendanceResponse",
    "ClassBulkCreate", "ReservationBulkCreate",
    "ClassList", "ClassReservationList", "ClassAttendanceList",
    "ClassFilter", "ClassStats", "ClassSchedule", "WeeklySchedule",
    "RecurringClassCreate", "WaitlistEntry", "WaitlistResponse",
    
    # Employee schemas
    "EmployeeBase", "EmployeeCreate", "EmployeeUpdate", "EmployeeResponse",
    "EmployeeBulkUpdate",
    "EmployeeList",
    "EmployeeFilter", "EmployeeStats",
    "PayrollPeriod", "PayrollSummary", "PerformanceReview", "PerformanceReviewResponse",
    
    # Configuration schemas
    "ConfigurationBase", "ConfigurationCreate", "ConfigurationUpdate", "ConfigurationResponse",
    "NotificationTemplateBase", "NotificationTemplateCreate", "NotificationTemplateUpdate", "NotificationTemplateResponse",
    "ThemeSettings", "NotificationSettings", "SecuritySettings", "IntegrationSettings",
    "BusinessSettings", "BackupSettings", "MaintenanceMode", "FeatureFlags",
    "CustomField", "CustomFieldsConfig", "SystemStatus", "NotificationTemplateList",
    "ConfigurationExport", "ConfigurationImport"
]