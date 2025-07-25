from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, date, timedelta
from decimal import Decimal
from ..core.database import get_db
from ..core.auth import (
    get_current_active_user, get_current_staff_user, get_current_admin_user,
    require_membership_management
)
from ..core.utils import ValidationUtils, DataUtils, BusinessUtils, DateUtils
from ..models.user import User
from ..models.membership import Membership, Payment
from ..schemas.membership import (
    MembershipCreate, MembershipUpdate, MembershipResponse, MembershipList,
    MembershipStats, MembershipRenewal, MembershipFreeze, MembershipBulkCreate,
    PaymentCreate, PaymentResponse, PaymentList, PaymentStats
)

router = APIRouter(tags=["Memberships"])

@router.get("/", response_model=MembershipList)
async def get_memberships(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by user name, email, or membership number"),
    membership_type: Optional[str] = Query(None, description="Filter by membership type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    expires_before: Optional[date] = Query(None, description="Expires before date"),
    expires_after: Optional[date] = Query(None, description="Expires after date"),
    created_after: Optional[date] = Query(None, description="Created after date"),
    created_before: Optional[date] = Query(None, description="Created before date"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get memberships with filtering, searching, and pagination"""
    
    # Build query
    query = db.query(Membership).options(
        joinedload(Membership.user),
        joinedload(Membership.payments)
    )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.join(User).filter(
            or_(
                func.concat(User.first_name, ' ', User.last_name).ilike(search_term),
                User.email.ilike(search_term),
                Membership.membership_number.ilike(search_term)
            )
        )
    
    # Apply filters
    if membership_type:
        query = query.filter(Membership.membership_type == membership_type)
    
    if status:
        query = query.filter(Membership.status == status)
    
    if payment_status:
        query = query.filter(Membership.payment_status == payment_status)
    
    if is_active is not None:
        query = query.filter(Membership.is_active == is_active)
    
    # Date filters
    if expires_before:
        query = query.filter(Membership.end_date <= expires_before)
    
    if expires_after:
        query = query.filter(Membership.end_date >= expires_after)
    
    if created_after:
        query = query.filter(Membership.created_at >= created_after)
    
    if created_before:
        query = query.filter(Membership.created_at <= created_before)
    
    # Apply sorting
    sort_column = getattr(Membership, sort_by, Membership.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Paginate
    result = DataUtils.paginate_query(query, page, per_page)
    
    return MembershipList(
        memberships=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.get("/stats", response_model=MembershipStats)
async def get_membership_stats(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get membership statistics"""
    
    # Total memberships
    total_memberships = db.query(Membership).count()
    
    # Active memberships
    active_memberships = db.query(Membership).filter(
        Membership.is_active == True
    ).count()
    
    # Expired memberships
    expired_memberships = db.query(Membership).filter(
        Membership.end_date < date.today()
    ).count()
    
    # Expiring soon (next 7 days)
    next_week = date.today() + timedelta(days=7)
    expiring_soon = db.query(Membership).filter(
        Membership.end_date <= next_week,
        Membership.end_date >= date.today(),
        Membership.is_active == True
    ).count()
    
    # New memberships this month
    start_of_month, end_of_month = DateUtils.get_month_dates()
    new_memberships_this_month = db.query(Membership).filter(
        Membership.created_at >= start_of_month,
        Membership.created_at <= end_of_month
    ).count()
    
    # Memberships by type
    memberships_by_type = db.query(
        Membership.membership_type,
        func.count(Membership.id).label('count')
    ).group_by(Membership.membership_type).all()
    
    # Memberships by status
    memberships_by_status = db.query(
        Membership.status,
        func.count(Membership.id).label('count')
    ).group_by(Membership.status).all()
    
    # Revenue this month
    revenue_this_month = db.query(
        func.sum(Payment.amount)
    ).join(Membership).filter(
        Payment.payment_date >= start_of_month,
        Payment.payment_date <= end_of_month,
        Payment.status == "COMPLETED"
    ).scalar() or Decimal('0')
    
    # Average membership duration
    avg_duration = db.query(
        func.avg(func.julianday(Membership.end_date) - func.julianday(Membership.start_date))
    ).filter(Membership.end_date.isnot(None)).scalar() or 0
    
    return MembershipStats(
        total_memberships=total_memberships,
        active_memberships=active_memberships,
        expired_memberships=expired_memberships,
        expiring_soon=expiring_soon,
        new_memberships_this_month=new_memberships_this_month,
        memberships_by_type={mtype: count for mtype, count in memberships_by_type},
        memberships_by_status={status: count for status, count in memberships_by_status},
        revenue_this_month=float(revenue_this_month),
        average_membership_duration=int(avg_duration) if avg_duration else 0
    )

@router.get("/expiring", response_model=MembershipList)
async def get_expiring_memberships(
    days: int = Query(7, ge=1, le=30, description="Days ahead to check"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get memberships expiring in the next N days"""
    
    end_date = date.today() + timedelta(days=days)
    
    query = db.query(Membership).options(
        joinedload(Membership.user)
    ).filter(
        Membership.end_date <= end_date,
        Membership.end_date >= date.today(),
        Membership.is_active == True
    ).order_by(asc(Membership.end_date))
    
    result = DataUtils.paginate_query(query, page, per_page)
    
    return MembershipList(
        memberships=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.get("/{membership_id}", response_model=MembershipResponse)
async def get_membership(
    membership_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get membership by ID"""
    
    membership = db.query(Membership).options(
        joinedload(Membership.user),
        joinedload(Membership.payments)
    ).filter(Membership.id == membership_id).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    # Check permissions
    if not current_user.is_staff and membership.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this membership"
        )
    
    return membership

@router.post("/", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
async def create_membership(
    membership_data: MembershipCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_membership_management),
    db: Session = Depends(get_db)
):
    """Create a new membership"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == membership_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check for active membership
    active_membership = db.query(Membership).filter(
        Membership.user_id == membership_data.user_id,
        Membership.is_active == True,
        Membership.end_date >= date.today()
    ).first()
    
    if active_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active membership"
        )
    
    # Calculate end date
    end_date = BusinessUtils.calculate_membership_expiry(
        membership_data.start_date,
        membership_data.membership_type
    )
    
    # Generate membership number
    membership_number = BusinessUtils.generate_membership_number()
    
    # Create membership
    new_membership = Membership(
        user_id=membership_data.user_id,
        membership_type=membership_data.membership_type,
        membership_number=membership_number,
        start_date=membership_data.start_date,
        end_date=end_date,
        price=membership_data.price,
        discount=membership_data.discount or Decimal('0'),
        total_amount=membership_data.price - (membership_data.discount or Decimal('0')),
        payment_method=membership_data.payment_method,
        payment_status=membership_data.payment_status or "PENDING",
        status="ACTIVE",
        notes=membership_data.notes,
        created_by_id=current_user.id
    )
    
    try:
        db.add(new_membership)
        db.commit()
        db.refresh(new_membership)
        
        # Create payment record if paid
        if membership_data.payment_status == "COMPLETED":
            payment = Payment(
                membership_id=new_membership.id,
                amount=new_membership.total_amount,
                payment_method=membership_data.payment_method,
                payment_date=datetime.utcnow().date(),
                status="COMPLETED",
                reference_number=BusinessUtils.generate_invoice_number(),
                created_by_id=current_user.id
            )
            db.add(payment)
            db.commit()
        
        # Send membership confirmation email
        background_tasks.add_task(
            send_membership_created_notification,
            user.email,
            user.first_name,
            new_membership
        )
        
        return new_membership
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create membership"
        )

@router.put("/{membership_id}", response_model=MembershipResponse)
async def update_membership(
    membership_id: int,
    membership_data: MembershipUpdate,
    current_user: User = Depends(require_membership_management),
    db: Session = Depends(get_db)
):
    """Update membership information"""
    
    membership = db.query(Membership).filter(Membership.id == membership_id).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    # Update membership fields
    update_data = membership_data.dict(exclude_unset=True)
    
    # Recalculate total if price or discount changed
    if 'price' in update_data or 'discount' in update_data:
        price = update_data.get('price', membership.price)
        discount = update_data.get('discount', membership.discount or Decimal('0'))
        update_data['total_amount'] = price - discount
    
    # Recalculate end date if start date or type changed
    if 'start_date' in update_data or 'membership_type' in update_data:
        start_date = update_data.get('start_date', membership.start_date)
        membership_type = update_data.get('membership_type', membership.membership_type)
        update_data['end_date'] = BusinessUtils.calculate_membership_expiry(
            start_date, membership_type
        )
    
    for field, value in update_data.items():
        if hasattr(membership, field):
            setattr(membership, field, value)
    
    membership.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(membership)
        return membership
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update membership"
        )

@router.post("/{membership_id}/renew", response_model=MembershipResponse)
async def renew_membership(
    membership_id: int,
    renewal_data: MembershipRenewal,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_membership_management),
    db: Session = Depends(get_db)
):
    """Renew membership"""
    
    membership = db.query(Membership).options(
        joinedload(Membership.user)
    ).filter(Membership.id == membership_id).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    # Calculate new dates
    new_start_date = max(membership.end_date + timedelta(days=1), date.today())
    new_end_date = BusinessUtils.calculate_membership_expiry(
        new_start_date,
        renewal_data.membership_type or membership.membership_type
    )
    
    # Calculate total amount
    discount = renewal_data.discount or Decimal('0')
    total_amount = renewal_data.price - discount
    
    # Update membership
    membership.membership_type = renewal_data.membership_type or membership.membership_type
    membership.start_date = new_start_date
    membership.end_date = new_end_date
    membership.price = renewal_data.price
    membership.discount = discount
    membership.total_amount = total_amount
    membership.payment_method = renewal_data.payment_method
    membership.payment_status = renewal_data.payment_status or "PENDING"
    membership.status = "ACTIVE"
    membership.is_active = True
    membership.notes = renewal_data.notes or membership.notes
    membership.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        
        # Create payment record if paid
        if renewal_data.payment_status == "COMPLETED":
            payment = Payment(
                membership_id=membership.id,
                amount=total_amount,
                payment_method=renewal_data.payment_method,
                payment_date=datetime.utcnow().date(),
                status="COMPLETED",
                reference_number=BusinessUtils.generate_invoice_number(),
                notes=f"Renewal payment for membership {membership.membership_number}",
                created_by_id=current_user.id
            )
            db.add(payment)
            db.commit()
        
        # Send renewal confirmation email
        background_tasks.add_task(
            send_membership_renewed_notification,
            membership.user.email,
            membership.user.first_name,
            membership
        )
        
        db.refresh(membership)
        return membership
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to renew membership"
        )

@router.post("/{membership_id}/freeze", response_model=MembershipResponse)
async def freeze_membership(
    membership_id: int,
    freeze_data: MembershipFreeze,
    current_user: User = Depends(require_membership_management),
    db: Session = Depends(get_db)
):
    """Freeze membership"""
    
    membership = db.query(Membership).filter(Membership.id == membership_id).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    if membership.status == "FROZEN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership is already frozen"
        )
    
    # Calculate new end date (extend by freeze duration)
    freeze_days = (freeze_data.end_date - freeze_data.start_date).days
    new_end_date = membership.end_date + timedelta(days=freeze_days)
    
    # Update membership
    membership.status = "FROZEN"
    membership.freeze_start_date = freeze_data.start_date
    membership.freeze_end_date = freeze_data.end_date
    membership.end_date = new_end_date
    membership.freeze_reason = freeze_data.reason
    membership.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(membership)
        return membership
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to freeze membership"
        )

@router.post("/{membership_id}/unfreeze", response_model=MembershipResponse)
async def unfreeze_membership(
    membership_id: int,
    current_user: User = Depends(require_membership_management),
    db: Session = Depends(get_db)
):
    """Unfreeze membership"""
    
    membership = db.query(Membership).filter(Membership.id == membership_id).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    if membership.status != "FROZEN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership is not frozen"
        )
    
    # Update membership
    membership.status = "ACTIVE"
    membership.freeze_start_date = None
    membership.freeze_end_date = None
    membership.freeze_reason = None
    membership.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(membership)
        return membership
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unfreeze membership"
        )

@router.post("/{membership_id}/cancel", response_model=MembershipResponse)
async def cancel_membership(
    membership_id: int,
    reason: str = Query(..., description="Cancellation reason"),
    current_user: User = Depends(require_membership_management),
    db: Session = Depends(get_db)
):
    """Cancel membership"""
    
    membership = db.query(Membership).filter(Membership.id == membership_id).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    if membership.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership is already cancelled"
        )
    
    # Update membership
    membership.status = "CANCELLED"
    membership.is_active = False
    membership.cancellation_date = date.today()
    membership.cancellation_reason = reason
    membership.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(membership)
        return membership
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel membership"
        )

# Background tasks
async def send_membership_created_notification(email: str, first_name: str, membership: Membership):
    """Send notification when membership is created"""
    from ..core.utils import NotificationUtils
    from ..core.config import settings
    
    subject = f"¡Bienvenido a {settings.PROJECT_NAME}! Tu membresía está activa"
    body = f"""
    Hola {first_name},
    
    ¡Tu membresía en {settings.PROJECT_NAME} ha sido activada exitosamente!
    
    Detalles de tu membresía:
    - Número de membresía: {membership.membership_number}
    - Tipo: {membership.membership_type}
    - Fecha de inicio: {membership.start_date.strftime('%d/%m/%Y')}
    - Fecha de vencimiento: {membership.end_date.strftime('%d/%m/%Y')}
    - Monto: ${membership.total_amount}
    
    ¡Esperamos verte pronto en el gimnasio!
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)

async def send_membership_renewed_notification(email: str, first_name: str, membership: Membership):
    """Send notification when membership is renewed"""
    from ..core.utils import NotificationUtils
    from ..core.config import settings
    
    subject = f"Tu membresía en {settings.PROJECT_NAME} ha sido renovada"
    body = f"""
    Hola {first_name},
    
    ¡Tu membresía en {settings.PROJECT_NAME} ha sido renovada exitosamente!
    
    Detalles de tu renovación:
    - Número de membresía: {membership.membership_number}
    - Tipo: {membership.membership_type}
    - Nueva fecha de vencimiento: {membership.end_date.strftime('%d/%m/%Y')}
    - Monto: ${membership.total_amount}
    
    ¡Gracias por continuar con nosotros!
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)