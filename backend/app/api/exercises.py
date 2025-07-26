from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime
from app.core.database import get_db
from app.core.auth import (
    get_current_active_user, get_current_staff_user, get_current_admin_user,
    require_exercise_management
)
from app.core.utils import ValidationUtils, DataUtils, FileUtils
from app.models.user import User
from app.models.exercise import Exercise
from app.schemas.exercise import (
    ExerciseCreate, ExerciseUpdate, ExerciseResponse, ExerciseList,
    ExerciseStats, ExerciseFilter, ExerciseSearch, ExerciseBulkCreate,
    ExerciseImport, ExerciseExport, CustomExerciseCreate, ExerciseTemplate,
    ExerciseProgression, ExerciseProgressionResponse
)

router = APIRouter(tags=["Exercises"])

@router.get("/", response_model=ExerciseList)
async def get_exercises(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    primary_muscle: Optional[str] = Query(None, description="Filter by primary muscle"),
    secondary_muscles: Optional[str] = Query(None, description="Filter by secondary muscles"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    equipment: Optional[str] = Query(None, description="Filter by equipment"),
    exercise_type: Optional[str] = Query(None, description="Filter by exercise type"),
    is_cardio: Optional[bool] = Query(None, description="Filter cardio exercises"),
    is_strength: Optional[bool] = Query(None, description="Filter strength exercises"),
    is_flexibility: Optional[bool] = Query(None, description="Filter flexibility exercises"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_by_me: Optional[bool] = Query(None, description="Filter exercises created by current user"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get exercises with filtering, searching, and pagination"""
    
    # Build query
    query = db.query(Exercise)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Exercise.name.ilike(search_term),
                Exercise.description.ilike(search_term),
                Exercise.instructions.ilike(search_term)
            )
        )
    
    # Apply filters
    if category:
        query = query.filter(Exercise.category == category)
    
    if primary_muscle:
        query = query.filter(Exercise.primary_muscle == primary_muscle)
    
    if secondary_muscles:
        query = query.filter(Exercise.secondary_muscles.contains([secondary_muscles]))
    
    if difficulty:
        query = query.filter(Exercise.difficulty == difficulty)
    
    if equipment:
        query = query.filter(Exercise.equipment.contains([equipment]))
    
    if exercise_type:
        query = query.filter(Exercise.exercise_type == exercise_type)
    
    if is_cardio is not None:
        query = query.filter(Exercise.is_cardio == is_cardio)
    
    if is_strength is not None:
        query = query.filter(Exercise.is_strength == is_strength)
    
    if is_flexibility is not None:
        query = query.filter(Exercise.is_flexibility == is_flexibility)
    
    if is_active is not None:
        query = query.filter(Exercise.is_active == is_active)
    
    if created_by_me:
        query = query.filter(Exercise.created_by_id == current_user.id)
    
    # Apply sorting
    sort_column = getattr(Exercise, sort_by, Exercise.name)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Paginate
    result = DataUtils.paginate_query(query, page, per_page)
    
    return ExerciseList(
        exercises=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.get("/stats", response_model=ExerciseStats)
async def get_exercise_stats(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get exercise statistics"""
    
    # Total exercises
    total_exercises = db.query(Exercise).count()
    
    # Active exercises
    active_exercises = db.query(Exercise).filter(Exercise.is_active == True).count()
    
    # Exercises by category
    exercises_by_category = db.query(
        Exercise.category,
        func.count(Exercise.id).label('count')
    ).group_by(Exercise.category).all()
    
    # Exercises by difficulty
    exercises_by_difficulty = db.query(
        Exercise.difficulty,
        func.count(Exercise.id).label('count')
    ).group_by(Exercise.difficulty).all()
    
    # Exercises by type
    exercises_by_type = db.query(
        Exercise.exercise_type,
        func.count(Exercise.id).label('count')
    ).group_by(Exercise.exercise_type).all()
    
    # Most popular muscles
    popular_muscles = db.query(
        Exercise.primary_muscle,
        func.count(Exercise.id).label('count')
    ).group_by(Exercise.primary_muscle).order_by(desc('count')).limit(10).all()
    
    # Exercise type distribution
    cardio_count = db.query(Exercise).filter(Exercise.is_cardio == True).count()
    strength_count = db.query(Exercise).filter(Exercise.is_strength == True).count()
    flexibility_count = db.query(Exercise).filter(Exercise.is_flexibility == True).count()
    
    return ExerciseStats(
        total_exercises=total_exercises,
        active_exercises=active_exercises,
        inactive_exercises=total_exercises - active_exercises,
        exercises_by_category={category: count for category, count in exercises_by_category},
        exercises_by_difficulty={difficulty: count for difficulty, count in exercises_by_difficulty},
        exercises_by_type={ex_type: count for ex_type, count in exercises_by_type},
        popular_muscles={muscle: count for muscle, count in popular_muscles},
        cardio_exercises=cardio_count,
        strength_exercises=strength_count,
        flexibility_exercises=flexibility_count
    )

@router.get("/categories", response_model=List[str])
async def get_exercise_categories(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all exercise categories"""
    
    categories = db.query(Exercise.category).distinct().filter(
        Exercise.category.isnot(None),
        Exercise.is_active == True
    ).all()
    
    return [category[0] for category in categories if category[0]]

@router.get("/muscles", response_model=List[str])
async def get_muscle_groups(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all muscle groups"""
    
    muscles = db.query(Exercise.primary_muscle).distinct().filter(
        Exercise.primary_muscle.isnot(None),
        Exercise.is_active == True
    ).all()
    
    return [muscle[0] for muscle in muscles if muscle[0]]

@router.get("/equipment", response_model=List[str])
async def get_equipment_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all equipment types"""
    
    # Get all equipment arrays and flatten them
    equipment_arrays = db.query(Exercise.equipment).filter(
        Exercise.equipment.isnot(None),
        Exercise.is_active == True
    ).all()
    
    equipment_set = set()
    for equipment_array in equipment_arrays:
        if equipment_array[0]:  # equipment_array is a tuple
            equipment_set.update(equipment_array[0])
    
    return sorted(list(equipment_set))

@router.get("/search", response_model=ExerciseList)
async def search_exercises(
    query: str = Query(..., min_length=2, description="Search query"),
    filters: ExerciseFilter = Depends(),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Advanced exercise search"""
    
    # Build base query
    db_query = db.query(Exercise)
    
    # Apply search
    search_term = f"%{query}%"
    db_query = db_query.filter(
        or_(
            Exercise.name.ilike(search_term),
            Exercise.description.ilike(search_term),
            Exercise.instructions.ilike(search_term),
            Exercise.primary_muscle.ilike(search_term)
        )
    )
    
    # Apply filters
    if filters.category:
        db_query = db_query.filter(Exercise.category == filters.category)
    
    if filters.primary_muscle:
        db_query = db_query.filter(Exercise.primary_muscle == filters.primary_muscle)
    
    if filters.difficulty:
        db_query = db_query.filter(Exercise.difficulty == filters.difficulty)
    
    if filters.equipment:
        db_query = db_query.filter(Exercise.equipment.contains([filters.equipment]))
    
    if filters.is_cardio is not None:
        db_query = db_query.filter(Exercise.is_cardio == filters.is_cardio)
    
    if filters.is_strength is not None:
        db_query = db_query.filter(Exercise.is_strength == filters.is_strength)
    
    if filters.is_flexibility is not None:
        db_query = db_query.filter(Exercise.is_flexibility == filters.is_flexibility)
    
    # Only active exercises
    db_query = db_query.filter(Exercise.is_active == True)
    
    # Order by relevance (name matches first)
    db_query = db_query.order_by(
        Exercise.name.ilike(search_term).desc(),
        Exercise.name
    )
    
    # Paginate
    result = DataUtils.paginate_query(db_query, page, per_page)
    
    return ExerciseList(
        exercises=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get exercise by ID"""
    
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    
    # Check if exercise is active or user has permissions
    if not exercise.is_active and not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    
    return exercise

@router.post("/", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    exercise_data: ExerciseCreate,
    current_user: User = Depends(require_exercise_management),
    db: Session = Depends(get_db)
):
    """Create a new exercise"""
    
    # Check if exercise name already exists
    existing_exercise = db.query(Exercise).filter(
        Exercise.name.ilike(exercise_data.name)
    ).first()
    
    if existing_exercise:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exercise with this name already exists"
        )
    
    # Create exercise
    new_exercise = Exercise(
        name=exercise_data.name,
        description=exercise_data.description,
        instructions=exercise_data.instructions,
        category=exercise_data.category,
        primary_muscle=exercise_data.primary_muscle,
        secondary_muscles=exercise_data.secondary_muscles or [],
        difficulty=exercise_data.difficulty,
        equipment=exercise_data.equipment or [],
        exercise_type=exercise_data.exercise_type,
        default_sets=exercise_data.default_sets,
        default_reps=exercise_data.default_reps,
        default_weight=exercise_data.default_weight,
        default_duration=exercise_data.default_duration,
        default_rest_time=exercise_data.default_rest_time,
        calories_per_minute=exercise_data.calories_per_minute,
        image_url=exercise_data.image_url,
        video_url=exercise_data.video_url,
        is_cardio=exercise_data.is_cardio or False,
        is_strength=exercise_data.is_strength or False,
        is_flexibility=exercise_data.is_flexibility or False,
        tips=exercise_data.tips,
        warnings=exercise_data.warnings,
        created_by_id=current_user.id
    )
    
    try:
        db.add(new_exercise)
        db.commit()
        db.refresh(new_exercise)
        return new_exercise
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exercise"
        )

@router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: int,
    exercise_data: ExerciseUpdate,
    current_user: User = Depends(require_exercise_management),
    db: Session = Depends(get_db)
):
    """Update exercise information"""
    
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    
    # Check if name is being changed and if it conflicts
    if exercise_data.name and exercise_data.name != exercise.name:
        existing_exercise = db.query(Exercise).filter(
            Exercise.name.ilike(exercise_data.name),
            Exercise.id != exercise_id
        ).first()
        
        if existing_exercise:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exercise with this name already exists"
            )
    
    # Update exercise fields
    update_data = exercise_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(exercise, field):
            setattr(exercise, field, value)
    
    exercise.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(exercise)
        return exercise
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update exercise"
        )

@router.delete("/{exercise_id}")
async def delete_exercise(
    exercise_id: int,
    current_user: User = Depends(require_exercise_management),
    db: Session = Depends(get_db)
):
    """Delete exercise (soft delete)"""
    
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    
    # Soft delete
    exercise.is_active = False
    exercise.deleted_at = datetime.utcnow()
    exercise.deleted_by_id = current_user.id
    
    try:
        db.commit()
        return {"message": "Exercise deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete exercise"
        )

@router.post("/bulk", response_model=List[ExerciseResponse])
async def create_bulk_exercises(
    exercises_data: ExerciseBulkCreate,
    current_user: User = Depends(require_exercise_management),
    db: Session = Depends(get_db)
):
    """Create multiple exercises at once"""
    
    created_exercises = []
    errors = []
    
    for i, exercise_data in enumerate(exercises_data.exercises):
        try:
            # Check if exercise name already exists
            existing_exercise = db.query(Exercise).filter(
                Exercise.name.ilike(exercise_data.name)
            ).first()
            
            if existing_exercise:
                errors.append(f"Exercise {i+1}: Name '{exercise_data.name}' already exists")
                continue
            
            # Create exercise
            new_exercise = Exercise(
                name=exercise_data.name,
                description=exercise_data.description,
                instructions=exercise_data.instructions,
                category=exercise_data.category,
                primary_muscle=exercise_data.primary_muscle,
                secondary_muscles=exercise_data.secondary_muscles or [],
                difficulty=exercise_data.difficulty,
                equipment=exercise_data.equipment or [],
                exercise_type=exercise_data.exercise_type,
                default_sets=exercise_data.default_sets,
                default_reps=exercise_data.default_reps,
                default_weight=exercise_data.default_weight,
                default_duration=exercise_data.default_duration,
                default_rest_time=exercise_data.default_rest_time,
                calories_per_minute=exercise_data.calories_per_minute,
                image_url=exercise_data.image_url,
                video_url=exercise_data.video_url,
                is_cardio=exercise_data.is_cardio or False,
                is_strength=exercise_data.is_strength or False,
                is_flexibility=exercise_data.is_flexibility or False,
                tips=exercise_data.tips,
                warnings=exercise_data.warnings,
                created_by_id=current_user.id
            )
            
            db.add(new_exercise)
            created_exercises.append(new_exercise)
            
        except Exception as e:
            errors.append(f"Exercise {i+1}: {str(e)}")
    
    try:
        db.commit()
        
        # Refresh all created exercises
        for exercise in created_exercises:
            db.refresh(exercise)
        
        if errors:
            return {
                "created_exercises": created_exercises,
                "errors": errors,
                "message": f"Created {len(created_exercises)} exercises with {len(errors)} errors"
            }
        
        return created_exercises
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exercises"
        )

@router.post("/custom", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_exercise(
    exercise_data: CustomExerciseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a custom exercise for the current user"""
    
    # Check if user already has an exercise with this name
    existing_exercise = db.query(Exercise).filter(
        Exercise.name.ilike(exercise_data.name),
        Exercise.created_by_id == current_user.id
    ).first()
    
    if existing_exercise:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an exercise with this name"
        )
    
    # Create custom exercise
    new_exercise = Exercise(
        name=exercise_data.name,
        description=exercise_data.description,
        instructions=exercise_data.instructions,
        category=exercise_data.category,
        primary_muscle=exercise_data.primary_muscle,
        secondary_muscles=exercise_data.secondary_muscles or [],
        difficulty=exercise_data.difficulty,
        equipment=exercise_data.equipment or [],
        exercise_type=exercise_data.exercise_type,
        default_sets=exercise_data.default_sets,
        default_reps=exercise_data.default_reps,
        default_weight=exercise_data.default_weight,
        default_duration=exercise_data.default_duration,
        default_rest_time=exercise_data.default_rest_time,
        is_cardio=exercise_data.is_cardio or False,
        is_strength=exercise_data.is_strength or False,
        is_flexibility=exercise_data.is_flexibility or False,
        is_custom=True,
        created_by_id=current_user.id
    )
    
    try:
        db.add(new_exercise)
        db.commit()
        db.refresh(new_exercise)
        return new_exercise
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create custom exercise"
        )

@router.get("/my-exercises", response_model=ExerciseList)
async def get_my_exercises(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get exercises created by the current user"""
    
    query = db.query(Exercise).filter(
        Exercise.created_by_id == current_user.id
    ).order_by(desc(Exercise.created_at))
    
    result = DataUtils.paginate_query(query, page, per_page)
    
    return ExerciseList(
        exercises=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )