from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, extract
from datetime import datetime, date, timedelta
from decimal import Decimal
from ..core.database import get_db
from ..core.auth import (
    get_current_active_user, get_current_staff_user, get_current_admin_user,
    require_payment_management
)
from ..core.utils import ValidationUtils, DataUtils, BusinessUtils, FormatUtils
from ..models.user import User
from ..models.membership import Membership
from ..models.membership import Payment, PaymentStatus
from ..schemas.membership import (
    PaymentCreate, PaymentUpdate, PaymentResponse, PaymentList, PaymentStats,
    PaymentMethod, PaymentReport
)

router = APIRouter(tags=["Payments"])

@router.get("/", response_model=PaymentList)
async def get_payments(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by user name, email, or payment reference"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    status: Optional[str] = Query(None, description="Filter by payment status"),
    payment_type: Optional[str] = Query(None, description="Filter by payment type"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    amount_min: Optional[Decimal] = Query(None, description="Minimum amount"),
    amount_max: Optional[Decimal] = Query(None, description="Maximum amount"),
    sort_by: str = Query("payment_date", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get payments with filtering, searching, and pagination"""
    
    # Build query
    query = db.query(Payment).options(
        joinedload(Payment.user),
        joinedload(Payment.membership),
        joinedload(Payment.invoice)
    )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.join(User).filter(
            or_(
                func.concat(User.first_name, ' ', User.last_name).ilike(search_term),
                User.email.ilike(search_term),
                Payment.reference.ilike(search_term),
                Payment.transaction_id.ilike(search_term)
            )
        )
    
    # Apply filters
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)
    
    if status:
        query = query.filter(Payment.status == status)
    
    if payment_type:
        query = query.filter(Payment.payment_type == payment_type)
    
    # Date filters
    if date_from:
        query = query.filter(Payment.payment_date >= date_from)
    
    if date_to:
        query = query.filter(Payment.payment_date <= date_to)
    
    # Amount filters
    if amount_min:
        query = query.filter(Payment.amount >= amount_min)
    
    if amount_max:
        query = query.filter(Payment.amount <= amount_max)
    
    # Apply sorting
    sort_column = getattr(Payment, sort_by, Payment.payment_date)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Paginate
    result = DataUtils.paginate_query(query, page, per_page)
    
    return PaymentList(
        payments=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.get("/stats", response_model=PaymentStats)
async def get_payment_stats(
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get payment statistics"""
    
    # Base query
    base_query = db.query(Payment)
    
    # Apply date filters
    if date_from:
        base_query = base_query.filter(Payment.payment_date >= date_from)
    
    if date_to:
        base_query = base_query.filter(Payment.payment_date <= date_to)
    
    # Total payments
    total_payments = base_query.count()
    
    # Successful payments
    successful_payments = base_query.filter(Payment.status == "COMPLETED").count()
    
    # Pending payments
    pending_payments = base_query.filter(Payment.status == "PENDING").count()
    
    # Failed payments
    failed_payments = base_query.filter(Payment.status == "FAILED").count()
    
    # Total revenue
    total_revenue = base_query.filter(
        Payment.status == "COMPLETED"
    ).with_entities(func.sum(Payment.amount)).scalar() or Decimal('0')
    
    # Revenue this month
    start_of_month = date.today().replace(day=1)
    revenue_this_month = db.query(Payment).filter(
        Payment.status == "COMPLETED",
        Payment.payment_date >= start_of_month
    ).with_entities(func.sum(Payment.amount)).scalar() or Decimal('0')
    
    # Revenue by payment method
    revenue_by_method = db.query(
        Payment.payment_method,
        func.sum(Payment.amount).label('total')
    ).filter(
        Payment.status == "COMPLETED"
    ).group_by(Payment.payment_method).all()
    
    if date_from:
        revenue_by_method = db.query(
            Payment.payment_method,
            func.sum(Payment.amount).label('total')
        ).filter(
            Payment.status == "COMPLETED",
            Payment.payment_date >= date_from
        )
        if date_to:
            revenue_by_method = revenue_by_method.filter(Payment.payment_date <= date_to)
        revenue_by_method = revenue_by_method.group_by(Payment.payment_method).all()
    
    # Payments by status
    payments_by_status = db.query(
        Payment.status,
        func.count(Payment.id).label('count')
    )
    
    if date_from:
        payments_by_status = payments_by_status.filter(Payment.payment_date >= date_from)
    if date_to:
        payments_by_status = payments_by_status.filter(Payment.payment_date <= date_to)
    
    payments_by_status = payments_by_status.group_by(Payment.status).all()
    
    # Average payment amount
    avg_payment = base_query.filter(
        Payment.status == "COMPLETED"
    ).with_entities(func.avg(Payment.amount)).scalar() or Decimal('0')
    
    # Daily revenue for last 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    daily_revenue = db.query(
        Payment.payment_date,
        func.sum(Payment.amount).label('total')
    ).filter(
        Payment.status == "COMPLETED",
        Payment.payment_date >= thirty_days_ago
    ).group_by(Payment.payment_date).order_by(Payment.payment_date).all()
    
    return PaymentStats(
        total_payments=total_payments,
        successful_payments=successful_payments,
        pending_payments=pending_payments,
        failed_payments=failed_payments,
        total_revenue=float(total_revenue),
        revenue_this_month=float(revenue_this_month),
        revenue_by_method={method: float(total) for method, total in revenue_by_method},
        payments_by_status={status: count for status, count in payments_by_status},
        average_payment=float(avg_payment),
        daily_revenue=[
            {"date": payment_date.isoformat(), "revenue": float(total)}
            for payment_date, total in daily_revenue
        ]
    )

# @router.get("/revenue-report", response_model=RevenueReport)
# async def get_revenue_report(...):
#     """Get revenue report by period"""
#     pass

@router.get("/methods", response_model=List[str])
async def get_payment_methods(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all payment methods"""
    
    methods = db.query(Payment.payment_method).distinct().filter(
        Payment.payment_method.isnot(None)
    ).all()
    
    return [method[0] for method in methods if method[0]]

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payment by ID"""
    
    payment = db.query(Payment).options(
        joinedload(Payment.user),
        joinedload(Payment.membership),
        joinedload(Payment.invoice)
    ).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check permissions
    if not current_user.is_staff and payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return payment

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Create a new payment"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == payment_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify membership if provided
    membership = None
    if payment_data.membership_id:
        membership = db.query(Membership).filter(
            Membership.id == payment_data.membership_id
        ).first()
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found"
            )
    
    # Generate payment reference
    reference = BusinessUtils.generate_invoice_number()
    
    # Create payment
    new_payment = Payment(
        user_id=payment_data.user_id,
        membership_id=payment_data.membership_id,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        payment_type=payment_data.payment_type or "MEMBERSHIP",
        status=payment_data.status or "PENDING",
        reference=reference,
        transaction_id=payment_data.transaction_id,
        payment_date=payment_data.payment_date or date.today(),
        due_date=payment_data.due_date,
        description=payment_data.description,
        notes=payment_data.notes,
        created_by_id=current_user.id
    )
    
    try:
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)
        
        # Send payment confirmation email if completed
        if new_payment.status == "COMPLETED":
            background_tasks.add_task(
                send_payment_confirmation,
                user.email,
                user.first_name,
                new_payment
            )
        
        return new_payment
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment"
        )

@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_payment_management),
    db: Session = Depends(get_db)
):
    """Update payment information"""
    
    payment = db.query(Payment).options(
        joinedload(Payment.user)
    ).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Store old status for comparison
    old_status = payment.status
    
    # Update payment fields
    update_data = payment_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(payment, field):
            setattr(payment, field, value)
    
    payment.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        
        # Send notification if status changed to completed
        if old_status != "COMPLETED" and payment.status == "COMPLETED":
            background_tasks.add_task(
                send_payment_confirmation,
                payment.user.email,
                payment.user.first_name,
                payment
            )
        
        db.refresh(payment)
        return payment
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update payment"
        )

@router.delete("/{payment_id}")
async def delete_payment(
    payment_id: int,
    current_user: User = Depends(require_payment_management),
    db: Session = Depends(get_db)
):
    """Delete payment (soft delete)"""
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Only allow deletion of pending or failed payments
    if payment.status == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete completed payments"
        )
    
    # Soft delete
    payment.deleted_at = datetime.utcnow()
    payment.deleted_by_id = current_user.id
    
    try:
        db.commit()
        return {"message": "Payment deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete payment"
        )

# Invoice endpoints - Commented out until Invoice model is implemented
# @router.get("/invoices/", response_model=InvoiceList)
# async def get_invoices(...):
#     """Get invoices with filtering and pagination"""
#     pass

# @router.post("/invoices/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
# async def create_invoice(...):
#     """Create a new invoice"""
#     pass

# Background tasks
async def send_payment_confirmation(
    email: str, first_name: str, payment: Payment
):
    """Send payment confirmation email"""
    from ..core.utils import NotificationUtils
    from ..core.config import settings
    
    subject = "Confirmación de pago recibido"
    body = f"""
    Hola {first_name},
    
    Hemos recibido tu pago exitosamente.
    
    Detalles del pago:
    - Referencia: {payment.reference}
    - Monto: {FormatUtils.format_currency(payment.amount)}
    - Método: {payment.payment_method}
    - Fecha: {payment.payment_date.strftime('%d/%m/%Y')}
    - Descripción: {payment.description or 'N/A'}
    
    Gracias por tu pago.
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)

# async def send_invoice_email(...):
#     """Send invoice email"""
#     pass