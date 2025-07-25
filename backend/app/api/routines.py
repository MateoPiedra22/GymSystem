from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, date
from ..core.database import get_db
from ..core.auth import (
    get_current_active_user, get_current_staff_user, get_current_admin_user,
    require_routine_management
)
from ..core.utils import ValidationUtils, DataUtils, BusinessUtils
from ..models.user import User
from ..models.routine import RoutineTemplate, Routine, RoutineExercise, RoutineAssignment
from ..models.exercise import Exercise
from ..schemas.routine import (
    RoutineTemplateCreate, RoutineTemplateUpdate, RoutineTemplateResponse, RoutineTemplateList,
    RoutineCreate, RoutineUpdate, RoutineResponse, RoutineList,
    RoutineExerciseCreate, RoutineExerciseUpdate, RoutineExerciseResponse,
    RoutineAssignmentCreate, RoutineAssignmentUpdate, RoutineAssignmentResponse, RoutineAssignmentList,
    RoutineStats, RoutineBulkAssign, RoutineProgress, RoutineProgressResponse,
    WorkoutSession, WorkoutSessionResponse
)

router = APIRouter(tags=["Routines"])

# Routine Templates
@router.get("/templates", response_model=RoutineTemplateList)
async def get_routine_templates(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    duration_min: Optional[int] = Query(None, ge=0, description="Minimum duration in minutes"),
    duration_max: Optional[int] = Query(None, ge=0, description="Maximum duration in minutes"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_by_me: Optional[bool] = Query(None, description="Filter templates created by current user"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get routine templates with filtering, searching, and pagination"""
    
    # Build query
    query = db.query(RoutineTemplate).options(
        joinedload(RoutineTemplate.exercises).joinedload(RoutineExercise.exercise)
    )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                RoutineTemplate.name.ilike(search_term),
                RoutineTemplate.description.ilike(search_term)
            )
        )
    
    # Apply filters
    if category:
        query = query.filter(RoutineTemplate.category == category)
    
    if difficulty:
        query = query.filter(RoutineTemplate.difficulty == difficulty)
    
    if duration_min is not None:
        query = query.filter(RoutineTemplate.estimated_duration >= duration_min)
    
    if duration_max is not None:
        query = query.filter(RoutineTemplate.estimated_duration <= duration_max)
    
    if is_active is not None:
        query = query.filter(RoutineTemplate.is_active == is_active)
    
    if created_by_me:
        query = query.filter(RoutineTemplate.created_by_id == current_user.id)
    
    # Apply sorting
    sort_column = getattr(RoutineTemplate, sort_by, RoutineTemplate.name)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Paginate
    result = DataUtils.paginate_query(query, page, per_page)
    
    return RoutineTemplateList(
        templates=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.get("/templates/{template_id}", response_model=RoutineTemplateResponse)
async def get_routine_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get routine template by ID"""
    
    template = db.query(RoutineTemplate).options(
        joinedload(RoutineTemplate.exercises).joinedload(RoutineExercise.exercise)
    ).filter(RoutineTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine template not found"
        )
    
    # Check if template is active or user has permissions
    if not template.is_active and not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine template not found"
        )
    
    return template

@router.post("/templates", response_model=RoutineTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_routine_template(
    template_data: RoutineTemplateCreate,
    current_user: User = Depends(require_routine_management),
    db: Session = Depends(get_db)
):
    """Create a new routine template"""
    
    # Check if template name already exists
    existing_template = db.query(RoutineTemplate).filter(
        RoutineTemplate.name.ilike(template_data.name)
    ).first()
    
    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Routine template with this name already exists"
        )
    
    # Create template
    new_template = RoutineTemplate(
        name=template_data.name,
        description=template_data.description,
        category=template_data.category,
        difficulty=template_data.difficulty,
        estimated_duration=template_data.estimated_duration,
        goals=template_data.goals or [],
        instructions=template_data.instructions,
        created_by_id=current_user.id
    )
    
    try:
        db.add(new_template)
        db.commit()
        db.refresh(new_template)
        
        # Add exercises to template
        if template_data.exercises:
            for exercise_data in template_data.exercises:
                # Verify exercise exists
                exercise = db.query(Exercise).filter(Exercise.id == exercise_data.exercise_id).first()
                if not exercise:
                    continue
                
                routine_exercise = RoutineExercise(
                    routine_template_id=new_template.id,
                    exercise_id=exercise_data.exercise_id,
                    order_index=exercise_data.order_index,
                    sets=exercise_data.sets,
                    reps=exercise_data.reps,
                    weight=exercise_data.weight,
                    duration=exercise_data.duration,
                    rest_time=exercise_data.rest_time,
                    notes=exercise_data.notes
                )
                db.add(routine_exercise)
            
            db.commit()
        
        # Refresh to get exercises
        db.refresh(new_template)
        return new_template
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create routine template"
        )

@router.put("/templates/{template_id}", response_model=RoutineTemplateResponse)
async def update_routine_template(
    template_id: int,
    template_data: RoutineTemplateUpdate,
    current_user: User = Depends(require_routine_management),
    db: Session = Depends(get_db)
):
    """Update routine template"""
    
    template = db.query(RoutineTemplate).filter(RoutineTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine template not found"
        )
    
    # Check if name is being changed and if it conflicts
    if template_data.name and template_data.name != template.name:
        existing_template = db.query(RoutineTemplate).filter(
            RoutineTemplate.name.ilike(template_data.name),
            RoutineTemplate.id != template_id
        ).first()
        
        if existing_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Routine template with this name already exists"
            )
    
    # Update template fields
    update_data = template_data.dict(exclude_unset=True, exclude={'exercises'})
    
    for field, value in update_data.items():
        if hasattr(template, field):
            setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(template)
        return template
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update routine template"
        )

@router.delete("/templates/{template_id}")
async def delete_routine_template(
    template_id: int,
    current_user: User = Depends(require_routine_management),
    db: Session = Depends(get_db)
):
    """Delete routine template (soft delete)"""
    
    template = db.query(RoutineTemplate).filter(RoutineTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine template not found"
        )
    
    # Soft delete
    template.is_active = False
    template.deleted_at = datetime.utcnow()
    template.deleted_by_id = current_user.id
    
    try:
        db.commit()
        return {"message": "Routine template deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete routine template"
        )

# Routine Assignments
@router.get("/assignments", response_model=RoutineAssignmentList)
async def get_routine_assignments(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    template_id: Optional[int] = Query(None, description="Filter by template ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get routine assignments with filtering and pagination"""
    
    # Build query
    query = db.query(RoutineAssignment).options(
        joinedload(RoutineAssignment.user),
        joinedload(RoutineAssignment.template),
        joinedload(RoutineAssignment.assigned_by)
    )
    
    # Apply filters
    if user_id:
        query = query.filter(RoutineAssignment.user_id == user_id)
    
    if template_id:
        query = query.filter(RoutineAssignment.template_id == template_id)
    
    if status:
        query = query.filter(RoutineAssignment.status == status)
    
    if is_active is not None:
        query = query.filter(RoutineAssignment.is_active == is_active)
    
    # Order by creation date
    query = query.order_by(desc(RoutineAssignment.created_at))
    
    # Paginate
    result = DataUtils.paginate_query(query, page, per_page)
    
    return RoutineAssignmentList(
        assignments=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.get("/my-assignments", response_model=RoutineAssignmentList)
async def get_my_routine_assignments(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's routine assignments"""
    
    query = db.query(RoutineAssignment).options(
        joinedload(RoutineAssignment.template),
        joinedload(RoutineAssignment.assigned_by)
    ).filter(RoutineAssignment.user_id == current_user.id)
    
    if status:
        query = query.filter(RoutineAssignment.status == status)
    
    query = query.order_by(desc(RoutineAssignment.created_at))
    
    result = DataUtils.paginate_query(query, page, per_page)
    
    return RoutineAssignmentList(
        assignments=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.post("/assignments", response_model=RoutineAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_routine(
    assignment_data: RoutineAssignmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_routine_management),
    db: Session = Depends(get_db)
):
    """Assign a routine template to a user"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == assignment_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify template exists
    template = db.query(RoutineTemplate).filter(
        RoutineTemplate.id == assignment_data.template_id
    ).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine template not found"
        )
    
    # Check for existing active assignment
    existing_assignment = db.query(RoutineAssignment).filter(
        RoutineAssignment.user_id == assignment_data.user_id,
        RoutineAssignment.template_id == assignment_data.template_id,
        RoutineAssignment.is_active == True
    ).first()
    
    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has this routine assigned"
        )
    
    # Create assignment
    new_assignment = RoutineAssignment(
        user_id=assignment_data.user_id,
        template_id=assignment_data.template_id,
        start_date=assignment_data.start_date,
        end_date=assignment_data.end_date,
        frequency_per_week=assignment_data.frequency_per_week,
        notes=assignment_data.notes,
        assigned_by_id=current_user.id
    )
    
    try:
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)
        
        # Send notification to user
        background_tasks.add_task(
            send_routine_assigned_notification,
            user.email,
            user.first_name,
            template.name,
            new_assignment
        )
        
        return new_assignment
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign routine"
        )

@router.post("/assignments/bulk", response_model=List[RoutineAssignmentResponse])
async def bulk_assign_routine(
    assignment_data: RoutineBulkAssign,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_routine_management),
    db: Session = Depends(get_db)
):
    """Assign a routine template to multiple users"""
    
    # Verify template exists
    template = db.query(RoutineTemplate).filter(
        RoutineTemplate.id == assignment_data.template_id
    ).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine template not found"
        )
    
    created_assignments = []
    errors = []
    
    for user_id in assignment_data.user_ids:
        try:
            # Verify user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                errors.append(f"User {user_id}: User not found")
                continue
            
            # Check for existing active assignment
            existing_assignment = db.query(RoutineAssignment).filter(
                RoutineAssignment.user_id == user_id,
                RoutineAssignment.template_id == assignment_data.template_id,
                RoutineAssignment.is_active == True
            ).first()
            
            if existing_assignment:
                errors.append(f"User {user_id}: Already has this routine assigned")
                continue
            
            # Create assignment
            new_assignment = RoutineAssignment(
                user_id=user_id,
                template_id=assignment_data.template_id,
                start_date=assignment_data.start_date,
                end_date=assignment_data.end_date,
                frequency_per_week=assignment_data.frequency_per_week,
                notes=assignment_data.notes,
                assigned_by_id=current_user.id
            )
            
            db.add(new_assignment)
            created_assignments.append(new_assignment)
            
            # Send notification
            background_tasks.add_task(
                send_routine_assigned_notification,
                user.email,
                user.first_name,
                template.name,
                new_assignment
            )
            
        except Exception as e:
            errors.append(f"User {user_id}: {str(e)}")
    
    try:
        db.commit()
        
        # Refresh all created assignments
        for assignment in created_assignments:
            db.refresh(assignment)
        
        if errors:
            return {
                "created_assignments": created_assignments,
                "errors": errors,
                "message": f"Created {len(created_assignments)} assignments with {len(errors)} errors"
            }
        
        return created_assignments
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create assignments"
        )

@router.get("/stats", response_model=RoutineStats)
async def get_routine_stats(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get routine statistics"""
    
    # Total templates
    total_templates = db.query(RoutineTemplate).count()
    
    # Active templates
    active_templates = db.query(RoutineTemplate).filter(
        RoutineTemplate.is_active == True
    ).count()
    
    # Total assignments
    total_assignments = db.query(RoutineAssignment).count()
    
    # Active assignments
    active_assignments = db.query(RoutineAssignment).filter(
        RoutineAssignment.is_active == True
    ).count()
    
    # Templates by category
    templates_by_category = db.query(
        RoutineTemplate.category,
        func.count(RoutineTemplate.id).label('count')
    ).group_by(RoutineTemplate.category).all()
    
    # Templates by difficulty
    templates_by_difficulty = db.query(
        RoutineTemplate.difficulty,
        func.count(RoutineTemplate.id).label('count')
    ).group_by(RoutineTemplate.difficulty).all()
    
    # Assignments by status
    assignments_by_status = db.query(
        RoutineAssignment.status,
        func.count(RoutineAssignment.id).label('count')
    ).group_by(RoutineAssignment.status).all()
    
    # Most popular templates
    popular_templates = db.query(
        RoutineTemplate.name,
        func.count(RoutineAssignment.id).label('assignments_count')
    ).join(RoutineAssignment).group_by(
        RoutineTemplate.id, RoutineTemplate.name
    ).order_by(desc('assignments_count')).limit(10).all()
    
    return RoutineStats(
        total_templates=total_templates,
        active_templates=active_templates,
        inactive_templates=total_templates - active_templates,
        total_assignments=total_assignments,
        active_assignments=active_assignments,
        completed_assignments=db.query(RoutineAssignment).filter(
            RoutineAssignment.status == "COMPLETED"
        ).count(),
        templates_by_category={category: count for category, count in templates_by_category},
        templates_by_difficulty={difficulty: count for difficulty, count in templates_by_difficulty},
        assignments_by_status={status: count for status, count in assignments_by_status},
        popular_templates={name: count for name, count in popular_templates}
    )

# Background tasks
async def send_routine_assigned_notification(
    email: str, first_name: str, routine_name: str, assignment: RoutineAssignment
):
    """Send notification when routine is assigned"""
    from ..core.utils import NotificationUtils
    from ..core.config import settings
    
    subject = f"Nueva rutina asignada: {routine_name}"
    body = f"""
    Hola {first_name},
    
    Se te ha asignado una nueva rutina de ejercicios en {settings.PROJECT_NAME}.
    
    Detalles de la rutina:
    - Nombre: {routine_name}
    - Fecha de inicio: {assignment.start_date.strftime('%d/%m/%Y')}
    - Fecha de fin: {assignment.end_date.strftime('%d/%m/%Y') if assignment.end_date else 'Sin fecha límite'}
    - Frecuencia: {assignment.frequency_per_week} veces por semana
    
    {f'Notas: {assignment.notes}' if assignment.notes else ''}
    
    ¡Inicia sesión en la aplicación para ver los detalles completos de tu rutina!
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)