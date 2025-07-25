from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, date, time, timedelta
from ..core.database import get_db
from ..core.auth import (
    get_current_active_user, get_current_staff_user, get_current_admin_user,
    require_class_management
)
from ..core.utils import ValidationUtils, DataUtils, BusinessUtils, DateUtils
from ..models.user import User
from ..models.class_model import Class
from ..models.class_reservation import ClassReservation, ClassAttendance
from ..models.employee import Employee
from ..schemas.class_schema import (
    ClassCreate, ClassUpdate, ClassResponse, ClassList, ClassStats,
    ClassReservationCreate, ClassReservationUpdate, ClassReservationResponse, ClassReservationList,
    ClassAttendanceCreate, ClassAttendanceUpdate, ClassAttendanceResponse, ClassAttendanceList,
    ClassFilter, ClassSchedule, RecurringClassCreate, WaitlistResponse
)

router = APIRouter(tags=["Classes"])

@router.get("/", response_model=ClassList)
async def get_classes(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    class_type: Optional[str] = Query(None, description="Filter by class type"),
    instructor_id: Optional[int] = Query(None, description="Filter by instructor"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    time_from: Optional[time] = Query(None, description="Filter from time"),
    time_to: Optional[time] = Query(None, description="Filter to time"),
    has_capacity: Optional[bool] = Query(None, description="Filter classes with available capacity"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("date", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get classes with filtering, searching, and pagination"""
    
    # Build query
    query = db.query(Class).options(
        joinedload(Class.instructor),
        joinedload(Class.reservations),
        joinedload(Class.attendances)
    )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Class.name.ilike(search_term),
                Class.description.ilike(search_term)
            )
        )
    
    # Apply filters
    if class_type:
        query = query.filter(Class.class_type == class_type)
    
    if instructor_id:
        query = query.filter(Class.instructor_id == instructor_id)
    
    if status:
        query = query.filter(Class.status == status)
    
    if date_from:
        query = query.filter(Class.date >= date_from)
    
    if date_to:
        query = query.filter(Class.date <= date_to)
    
    if time_from:
        query = query.filter(Class.start_time >= time_from)
    
    if time_to:
        query = query.filter(Class.end_time <= time_to)
    
    if has_capacity:
        # Filter classes with available spots
        subquery = db.query(
            ClassReservation.class_id,
            func.count(ClassReservation.id).label('reservation_count')
        ).filter(
            ClassReservation.status.in_(["CONFIRMED", "CHECKED_IN"])
        ).group_by(ClassReservation.class_id).subquery()
        
        query = query.outerjoin(subquery, Class.id == subquery.c.class_id)
        query = query.filter(
            or_(
                subquery.c.reservation_count < Class.max_capacity,
                subquery.c.reservation_count.is_(None)
            )
        )
    
    if is_active is not None:
        query = query.filter(Class.is_active == is_active)
    
    # Apply sorting
    if sort_by == "date":
        if sort_order == "desc":
            query = query.order_by(desc(Class.date), desc(Class.start_time))
        else:
            query = query.order_by(asc(Class.date), asc(Class.start_time))
    else:
        sort_column = getattr(Class, sort_by, Class.date)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    
    # Paginate
    result = DataUtils.paginate_query(query, page, per_page)
    
    return ClassList(
        classes=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.get("/stats", response_model=ClassStats)
async def get_class_stats(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get class statistics"""
    
    # Total classes
    total_classes = db.query(Class).count()
    
    # Active classes
    active_classes = db.query(Class).filter(Class.is_active == True).count()
    
    # Classes today
    today = date.today()
    classes_today = db.query(Class).filter(
        Class.date == today,
        Class.is_active == True
    ).count()
    
    # Classes this week
    start_of_week, end_of_week = DateUtils.get_week_dates()
    classes_this_week = db.query(Class).filter(
        Class.date >= start_of_week,
        Class.date <= end_of_week,
        Class.is_active == True
    ).count()
    
    # Total reservations
    total_reservations = db.query(ClassReservation).count()
    
    # Confirmed reservations
    confirmed_reservations = db.query(ClassReservation).filter(
        ClassReservation.status == "CONFIRMED"
    ).count()
    
    # Total attendance
    total_attendance = db.query(ClassAttendance).filter(
        ClassAttendance.attended == True
    ).count()
    
    # Classes by type
    classes_by_type = db.query(
        Class.class_type,
        func.count(Class.id).label('count')
    ).group_by(Class.class_type).all()
    
    # Classes by status
    classes_by_status = db.query(
        Class.status,
        func.count(Class.id).label('count')
    ).group_by(Class.status).all()
    
    # Average attendance rate
    attendance_stats = db.query(
        func.count(ClassReservation.id).label('total_reservations'),
        func.sum(func.case([(ClassAttendance.attended == True, 1)], else_=0)).label('total_attended')
    ).outerjoin(ClassAttendance, ClassReservation.id == ClassAttendance.reservation_id).first()
    
    attendance_rate = 0
    if attendance_stats.total_reservations and attendance_stats.total_reservations > 0:
        attendance_rate = (attendance_stats.total_attended or 0) / attendance_stats.total_reservations * 100
    
    # Most popular class types
    popular_class_types = db.query(
        Class.class_type,
        func.count(ClassReservation.id).label('reservation_count')
    ).join(ClassReservation).group_by(
        Class.class_type
    ).order_by(desc('reservation_count')).limit(10).all()
    
    # Capacity utilization
    capacity_stats = db.query(
        func.avg(Class.max_capacity).label('avg_capacity'),
        func.avg(func.count(ClassReservation.id)).label('avg_reservations')
    ).outerjoin(ClassReservation, and_(
        ClassReservation.class_id == Class.id,
        ClassReservation.status.in_(["CONFIRMED", "CHECKED_IN"])
    )).group_by(Class.id).first()
    
    capacity_utilization = 0
    if capacity_stats and capacity_stats.avg_capacity and capacity_stats.avg_capacity > 0:
        capacity_utilization = (capacity_stats.avg_reservations or 0) / capacity_stats.avg_capacity * 100
    
    return ClassStats(
        total_classes=total_classes,
        active_classes=active_classes,
        inactive_classes=total_classes - active_classes,
        classes_today=classes_today,
        classes_this_week=classes_this_week,
        total_reservations=total_reservations,
        confirmed_reservations=confirmed_reservations,
        cancelled_reservations=db.query(ClassReservation).filter(
            ClassReservation.status == "CANCELLED"
        ).count(),
        total_attendance=total_attendance,
        attendance_rate=round(attendance_rate, 2),
        capacity_utilization=round(capacity_utilization, 2),
        classes_by_type={class_type: count for class_type, count in classes_by_type},
        classes_by_status={status: count for status, count in classes_by_status},
        popular_class_types={class_type: count for class_type, count in popular_class_types}
    )

@router.get("/schedule", response_model=List[ClassSchedule])
async def get_class_schedule(
    date_from: date = Query(..., description="Start date"),
    date_to: date = Query(..., description="End date"),
    instructor_id: Optional[int] = Query(None, description="Filter by instructor"),
    class_type: Optional[str] = Query(None, description="Filter by class type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get class schedule for a date range"""
    
    # Validate date range
    if date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )
    
    # Limit to 30 days
    if (date_to - date_from).days > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 30 days"
        )
    
    query = db.query(Class).options(
        joinedload(Class.instructor)
    ).filter(
        Class.date >= date_from,
        Class.date <= date_to,
        Class.is_active == True
    )
    
    if instructor_id:
        query = query.filter(Class.instructor_id == instructor_id)
    
    if class_type:
        query = query.filter(Class.class_type == class_type)
    
    classes = query.order_by(Class.date, Class.start_time).all()
    
    # Group by date
    schedule = {}
    for class_obj in classes:
        date_str = class_obj.date.isoformat()
        if date_str not in schedule:
            schedule[date_str] = []
        
        # Get reservation count
        reservation_count = db.query(ClassReservation).filter(
            ClassReservation.class_id == class_obj.id,
            ClassReservation.status.in_(["CONFIRMED", "CHECKED_IN"])
        ).count()
        
        schedule[date_str].append({
            "class": class_obj,
            "available_spots": class_obj.max_capacity - reservation_count,
            "reservation_count": reservation_count
        })
    
    # Convert to list format
    result = []
    for date_str, classes_list in schedule.items():
        result.append({
            "date": date_str,
            "classes": classes_list
        })
    
    return result

@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get class by ID"""
    
    class_obj = db.query(Class).options(
        joinedload(Class.instructor),
        joinedload(Class.reservations).joinedload(ClassReservation.user),
        joinedload(Class.attendances)
    ).filter(Class.id == class_id).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Check if class is active or user has permissions
    if not class_obj.is_active and not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    return class_obj

@router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    current_user: User = Depends(require_class_management),
    db: Session = Depends(get_db)
):
    """Create a new class"""
    
    # Verify instructor exists
    if class_data.instructor_id:
        instructor = db.query(Employee).filter(
            Employee.id == class_data.instructor_id,
            Employee.position.in_(["INSTRUCTOR", "TRAINER"])
        ).first()
        if not instructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor not found"
            )
    
    # Check for scheduling conflicts
    conflict = db.query(Class).filter(
        Class.instructor_id == class_data.instructor_id,
        Class.date == class_data.date,
        Class.is_active == True,
        or_(
            and_(
                Class.start_time <= class_data.start_time,
                Class.end_time > class_data.start_time
            ),
            and_(
                Class.start_time < class_data.end_time,
                Class.end_time >= class_data.end_time
            ),
            and_(
                Class.start_time >= class_data.start_time,
                Class.end_time <= class_data.end_time
            )
        )
    ).first()
    
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instructor has a scheduling conflict"
        )
    
    # Create class
    new_class = Class(
        name=class_data.name,
        description=class_data.description,
        class_type=class_data.class_type,
        instructor_id=class_data.instructor_id,
        date=class_data.date,
        start_time=class_data.start_time,
        end_time=class_data.end_time,
        max_capacity=class_data.max_capacity,
        price=class_data.price,
        location=class_data.location,
        requirements=class_data.requirements,
        equipment_needed=class_data.equipment_needed or [],
        difficulty_level=class_data.difficulty_level,
        created_by_id=current_user.id
    )
    
    try:
        db.add(new_class)
        db.commit()
        db.refresh(new_class)
        return new_class
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create class"
        )

@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: int,
    class_data: ClassUpdate,
    current_user: User = Depends(require_class_management),
    db: Session = Depends(get_db)
):
    """Update class information"""
    
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify instructor if being changed
    if class_data.instructor_id and class_data.instructor_id != class_obj.instructor_id:
        instructor = db.query(Employee).filter(
            Employee.id == class_data.instructor_id,
            Employee.position.in_(["INSTRUCTOR", "TRAINER"])
        ).first()
        if not instructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor not found"
            )
    
    # Check for scheduling conflicts if date/time is being changed
    if (class_data.date or class_data.start_time or class_data.end_time or class_data.instructor_id):
        new_date = class_data.date or class_obj.date
        new_start_time = class_data.start_time or class_obj.start_time
        new_end_time = class_data.end_time or class_obj.end_time
        new_instructor_id = class_data.instructor_id or class_obj.instructor_id
        
        conflict = db.query(Class).filter(
            Class.instructor_id == new_instructor_id,
            Class.date == new_date,
            Class.id != class_id,
            Class.is_active == True,
            or_(
                and_(
                    Class.start_time <= new_start_time,
                    Class.end_time > new_start_time
                ),
                and_(
                    Class.start_time < new_end_time,
                    Class.end_time >= new_end_time
                ),
                and_(
                    Class.start_time >= new_start_time,
                    Class.end_time <= new_end_time
                )
            )
        ).first()
        
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instructor has a scheduling conflict"
            )
    
    # Update class fields
    update_data = class_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(class_obj, field):
            setattr(class_obj, field, value)
    
    class_obj.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(class_obj)
        return class_obj
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update class"
        )

@router.delete("/{class_id}")
async def delete_class(
    class_id: int,
    current_user: User = Depends(require_class_management),
    db: Session = Depends(get_db)
):
    """Delete class (soft delete)"""
    
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Check if class has reservations
    reservation_count = db.query(ClassReservation).filter(
        ClassReservation.class_id == class_id,
        ClassReservation.status.in_(["CONFIRMED", "CHECKED_IN"])
    ).count()
    
    if reservation_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete class with active reservations"
        )
    
    # Soft delete
    class_obj.is_active = False
    class_obj.status = "CANCELLED"
    class_obj.deleted_at = datetime.utcnow()
    class_obj.deleted_by_id = current_user.id
    
    try:
        db.commit()
        return {"message": "Class deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete class"
        )

# Class Reservations
@router.get("/{class_id}/reservations", response_model=ClassReservationList)
async def get_class_reservations(
    class_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get reservations for a specific class"""
    
    # Verify class exists
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    query = db.query(ClassReservation).options(
        joinedload(ClassReservation.user)
    ).filter(ClassReservation.class_id == class_id)
    
    if status:
        query = query.filter(ClassReservation.status == status)
    
    query = query.order_by(desc(ClassReservation.created_at))
    
    result = DataUtils.paginate_query(query, page, per_page)
    
    return ClassReservationList(
        reservations=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.post("/{class_id}/reserve", response_model=ClassReservationResponse, status_code=status.HTTP_201_CREATED)
async def reserve_class(
    class_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Reserve a spot in a class"""
    
    # Verify class exists and is available
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.is_active == True,
        Class.status == "SCHEDULED"
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or not available"
        )
    
    # Check if class is in the future
    class_datetime = datetime.combine(class_obj.date, class_obj.start_time)
    if class_datetime <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reserve past classes"
        )
    
    # Check if user already has a reservation
    existing_reservation = db.query(ClassReservation).filter(
        ClassReservation.class_id == class_id,
        ClassReservation.user_id == current_user.id,
        ClassReservation.status.in_(["CONFIRMED", "CHECKED_IN"])
    ).first()
    
    if existing_reservation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a reservation for this class"
        )
    
    # Check capacity
    current_reservations = db.query(ClassReservation).filter(
        ClassReservation.class_id == class_id,
        ClassReservation.status.in_(["CONFIRMED", "CHECKED_IN"])
    ).count()
    
    if current_reservations >= class_obj.max_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class is full"
        )
    
    # Create reservation
    new_reservation = ClassReservation(
        class_id=class_id,
        user_id=current_user.id,
        status="CONFIRMED",
        reservation_date=datetime.utcnow().date()
    )
    
    try:
        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)
        
        # Send confirmation email
        background_tasks.add_task(
            send_reservation_confirmation,
            current_user.email,
            current_user.first_name,
            class_obj,
            new_reservation
        )
        
        return new_reservation
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reservation"
        )

@router.delete("/reservations/{reservation_id}")
async def cancel_reservation(
    reservation_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel a class reservation"""
    
    reservation = db.query(ClassReservation).options(
        joinedload(ClassReservation.gym_class),
        joinedload(ClassReservation.user)
    ).filter(ClassReservation.id == reservation_id).first()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    # Check permissions
    if not current_user.is_staff and reservation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to cancel this reservation"
        )
    
    # Check if reservation can be cancelled
    if reservation.status in ["CANCELLED", "CHECKED_IN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation cannot be cancelled"
        )
    
    # Check cancellation deadline (e.g., 2 hours before class)
    class_datetime = datetime.combine(reservation.class_obj.date, reservation.class_obj.start_time)
    cancellation_deadline = class_datetime - timedelta(hours=2)
    
    if datetime.now() > cancellation_deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cancellation deadline has passed"
        )
    
    # Cancel reservation
    reservation.status = "CANCELLED"
    reservation.cancelled_at = datetime.utcnow()
    
    try:
        db.commit()
        
        # Send cancellation email
        background_tasks.add_task(
            send_cancellation_confirmation,
            reservation.user.email,
            reservation.user.first_name,
            reservation.class_obj
        )
        
        return {"message": "Reservation cancelled successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel reservation"
        )

# Background tasks
async def send_reservation_confirmation(
    email: str, first_name: str, class_obj: Class, reservation: ClassReservation
):
    """Send reservation confirmation email"""
    from ..core.utils import NotificationUtils
    from ..core.config import settings
    
    subject = f"Reserva confirmada: {class_obj.name}"
    body = f"""
    Hola {first_name},
    
    Tu reserva para la clase "{class_obj.name}" ha sido confirmada.
    
    Detalles de la clase:
    - Fecha: {class_obj.date.strftime('%d/%m/%Y')}
    - Hora: {class_obj.start_time.strftime('%H:%M')} - {class_obj.end_time.strftime('%H:%M')}
    - Ubicación: {class_obj.location}
    - Instructor: {class_obj.instructor.first_name + ' ' + class_obj.instructor.last_name if class_obj.instructor else 'Por asignar'}
    
    {f'Requisitos: {class_obj.requirements}' if class_obj.requirements else ''}
    
    ¡Te esperamos en {settings.PROJECT_NAME}!
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)

async def send_cancellation_confirmation(email: str, first_name: str, class_obj: Class):
    """Send cancellation confirmation email"""
    from ..core.utils import NotificationUtils
    from ..core.config import settings
    
    subject = f"Reserva cancelada: {class_obj.name}"
    body = f"""
    Hola {first_name},
    
    Tu reserva para la clase "{class_obj.name}" del {class_obj.date.strftime('%d/%m/%Y')} a las {class_obj.start_time.strftime('%H:%M')} ha sido cancelada exitosamente.
    
    Puedes hacer una nueva reserva cuando gustes a través de la aplicación.
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)