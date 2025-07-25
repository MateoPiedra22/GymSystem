from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, date
from ..core.database import get_db
from ..core.auth import (
    get_current_active_user, get_current_staff_user, get_current_admin_user,
    require_user_management, hash_password
)
from ..core.utils import ValidationUtils, DataUtils, BusinessUtils, DateUtils
from ..models.user import User
from ..models.membership import Membership
from ..schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserList, UserStats
)
from ..schemas.membership import MembershipResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=UserList)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    role: Optional[str] = Query(None, description="Filter by role"),
    user_type: Optional[str] = Query(None, description="Filter by user type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    age_min: Optional[int] = Query(None, ge=0, le=120, description="Minimum age"),
    age_max: Optional[int] = Query(None, ge=0, le=120, description="Maximum age"),
    created_after: Optional[date] = Query(None, description="Created after date"),
    created_before: Optional[date] = Query(None, description="Created before date"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get users with filtering, searching, and pagination"""
    
    # Build query
    query = db.query(User).options(
        joinedload(User.memberships),
        joinedload(User.payments)
    )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                func.concat(User.first_name, ' ', User.last_name).ilike(search_term),
                User.email.ilike(search_term),
                User.phone.ilike(search_term)
            )
        )
    
    # Apply filters
    if role:
        query = query.filter(User.role == role)
    
    if user_type:
        query = query.filter(User.user_type == user_type)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if gender:
        query = query.filter(User.gender == gender)
    
    # Age filters
    if age_min is not None or age_max is not None:
        today = date.today()
        
        if age_min is not None:
            max_birth_date = date(today.year - age_min, today.month, today.day)
            query = query.filter(User.date_of_birth <= max_birth_date)
        
        if age_max is not None:
            min_birth_date = date(today.year - age_max - 1, today.month, today.day)
            query = query.filter(User.date_of_birth > min_birth_date)
    
    # Date filters
    if created_after:
        query = query.filter(User.created_at >= created_after)
    
    if created_before:
        query = query.filter(User.created_at <= created_before)
    
    # Apply sorting
    sort_column = getattr(User, sort_by, User.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Paginate
    result = DataUtils.paginate_query(query, page, per_page)
    
    return UserList(
        users=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    
    # Total users
    total_users = db.query(User).count()
    
    # Active users
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # New users this month
    start_of_month, end_of_month = DateUtils.get_month_dates()
    new_users_this_month = db.query(User).filter(
        User.created_at >= start_of_month,
        User.created_at <= end_of_month
    ).count()
    
    # Users by role
    users_by_role = db.query(
        User.role,
        func.count(User.id).label('count')
    ).group_by(User.role).all()
    
    # Users by type
    users_by_type = db.query(
        User.user_type,
        func.count(User.id).label('count')
    ).group_by(User.user_type).all()
    
    # Users by gender
    users_by_gender = db.query(
        User.gender,
        func.count(User.id).label('count')
    ).group_by(User.gender).all()
    
    # Age distribution
    today = date.today()
    age_ranges = [
        ("18-25", 18, 25),
        ("26-35", 26, 35),
        ("36-45", 36, 45),
        ("46-55", 46, 55),
        ("56+", 56, 120)
    ]
    
    age_distribution = []
    for range_name, min_age, max_age in age_ranges:
        max_birth_date = date(today.year - min_age, today.month, today.day)
        min_birth_date = date(today.year - max_age - 1, today.month, today.day)
        
        count = db.query(User).filter(
            User.date_of_birth <= max_birth_date,
            User.date_of_birth > min_birth_date
        ).count()
        
        age_distribution.append({"range": range_name, "count": count})
    
    return UserStats(
        total_users=total_users,
        active_users=active_users,
        inactive_users=total_users - active_users,
        new_users_this_month=new_users_this_month,
        users_by_role={role: count for role, count in users_by_role},
        users_by_type={user_type: count for user_type, count in users_by_type},
        users_by_gender={gender: count for gender, count in users_by_gender},
        age_distribution=age_distribution
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    
    # Check permissions
    if not current_user.is_staff and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this user"
        )
    
    user = db.query(User).options(
        joinedload(User.memberships),
        joinedload(User.payments)
    ).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_user_management),
    db: Session = Depends(get_db)
):
    """Create a new user"""
    
    # Validate email format
    if not ValidationUtils.validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email.lower()) | 
        (User.phone == user_data.phone)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Validate phone number
    is_valid_phone, formatted_phone = ValidationUtils.validate_phone(user_data.phone)
    if not is_valid_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    new_user = User(
        email=user_data.email.lower(),
        phone=formatted_phone,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        date_of_birth=user_data.date_of_birth,
        gender=user_data.gender,
        address=user_data.address,
        emergency_contact_name=user_data.emergency_contact_name,
        emergency_contact_phone=user_data.emergency_contact_phone,
        medical_conditions=user_data.medical_conditions,
        medications=user_data.medications,
        allergies=user_data.allergies,
        fitness_goals=user_data.fitness_goals,
        experience_level=user_data.experience_level,
        preferred_workout_time=user_data.preferred_workout_time,
        role=user_data.role or "MEMBER",
        user_type=user_data.user_type or "MONTHLY",
        is_active=user_data.is_active if user_data.is_active is not None else True,
        created_by_id=current_user.id
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Send welcome email
        background_tasks.add_task(
            send_user_created_notification,
            new_user.email,
            new_user.first_name,
            user_data.password
        )
        
        return new_user
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user information"""
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if not current_user.can_manage_users and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user"
        )
    
    # Validate email if provided
    if user_data.email and user_data.email != user.email:
        if not ValidationUtils.validate_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Check if email is already taken
        existing_user = db.query(User).filter(
            User.email == user_data.email.lower(),
            User.id != user_id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Validate phone if provided
    if user_data.phone and user_data.phone != user.phone:
        is_valid_phone, formatted_phone = ValidationUtils.validate_phone(user_data.phone)
        if not is_valid_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format"
            )
        
        # Check if phone is already taken
        existing_user = db.query(User).filter(
            User.phone == formatted_phone,
            User.id != user_id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
        
        user_data.phone = formatted_phone
    
    # Update user fields
    update_data = user_data.dict(exclude_unset=True)
    
    # Only staff can update role and user_type
    if not current_user.is_staff:
        update_data.pop('role', None)
        update_data.pop('user_type', None)
        update_data.pop('is_active', None)
    
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(user)
        return user
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_user_management),
    db: Session = Depends(get_db)
):
    """Delete user (soft delete)"""
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Prevent deletion of owner accounts
    if user.role == "OWNER":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete owner accounts"
        )
    
    # Soft delete
    user.is_active = False
    user.deleted_at = datetime.utcnow()
    user.deleted_by_id = current_user.id
    
    try:
        db.commit()
        return {"message": "User deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_user_management),
    db: Session = Depends(get_db)
):
    """Activate user account"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    user.deleted_at = None
    user.deleted_by_id = None
    user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        return {"message": "User activated successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )

@router.get("/{user_id}/memberships", response_model=List[MembershipResponse])
async def get_user_memberships(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's memberships"""
    
    # Check permissions
    if not current_user.is_staff and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this user's memberships"
        )
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    memberships = db.query(Membership).filter(
        Membership.user_id == user_id
    ).order_by(desc(Membership.created_at)).all()
    
    return memberships

@router.post("/{user_id}/reset-password")
async def admin_reset_password(
    user_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_user_management),
    db: Session = Depends(get_db)
):
    """Admin reset user password"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate temporary password
    temp_password = BusinessUtils.generate_membership_number()[-8:]  # Use last 8 chars
    
    # Update password
    user.password_hash = hash_password(temp_password)
    user.password_changed_at = datetime.utcnow()
    
    try:
        db.commit()
        
        # Send new password email
        background_tasks.add_task(
            send_password_reset_notification,
            user.email,
            user.first_name,
            temp_password
        )
        
        return {"message": "Password reset successfully. New password sent to user's email."}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

# Background tasks
async def send_user_created_notification(email: str, first_name: str, password: str):
    """Send notification when user is created by admin"""
    from ..core.utils import NotificationUtils
    from ..core.config import settings
    
    subject = f"Tu cuenta en {settings.PROJECT_NAME} ha sido creada"
    body = f"""
    Hola {first_name},
    
    Tu cuenta en {settings.PROJECT_NAME} ha sido creada exitosamente.
    
    Datos de acceso:
    Email: {email}
    Contraseña temporal: {password}
    
    Por favor, cambia tu contraseña después del primer inicio de sesión.
    
    ¡Bienvenido al gimnasio!
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)

async def send_password_reset_notification(email: str, first_name: str, new_password: str):
    """Send notification when password is reset by admin"""
    from ..core.utils import NotificationUtils
    from ..core.config import settings
    
    subject = "Tu contraseña ha sido restablecida"
    body = f"""
    Hola {first_name},
    
    Tu contraseña en {settings.PROJECT_NAME} ha sido restablecida por un administrador.
    
    Nueva contraseña temporal: {new_password}
    
    Por favor, cambia tu contraseña después del próximo inicio de sesión.
    
    Si no solicitaste este cambio, contacta inmediatamente con el administrador.
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)