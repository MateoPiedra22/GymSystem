from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, extract, case
from datetime import datetime, date, timedelta
from decimal import Decimal
import io
import csv
from ..core.database import get_db
from ..core.auth import get_current_admin_user, get_current_staff_user
from ..core.utils import DataUtils, FormatUtils, DateUtils
from ..models.user import User
from ..models.membership import Membership, MembershipType
from ..models.membership import Payment
from ..models.class_model import Class
from ..models.employee import Employee
# from ..schemas.report import (
#     MembershipReport, PaymentReport, AttendanceReport, EmployeeReport,
#     FinancialSummary, MembershipAnalytics, ClassAnalytics, UserAnalytics,
#     ReportFilter, ExportFormat
# )
from ..schemas.membership import PaymentReport

router = APIRouter(tags=["Reports"])

# @router.get("/membership-report", response_model=MembershipReport)
# async def get_membership_report(...):
#     """Generate comprehensive membership report"""
#     pass

@router.get("/payment-report", response_model=PaymentReport)
async def get_payment_report(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    payment_type: Optional[str] = Query(None, description="Filter by payment type"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Generate comprehensive payment report"""
    
    # Set default date range (last 30 days)
    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()
    
    # Base query
    base_query = db.query(Payment).filter(
        Payment.payment_date >= date_from,
        Payment.payment_date <= date_to
    )
    
    # Apply filters
    if payment_method:
        base_query = base_query.filter(Payment.payment_method == payment_method)
    
    if payment_type:
        base_query = base_query.filter(Payment.payment_type == payment_type)
    
    # Total payments and revenue
    total_payments = base_query.count()
    total_revenue = base_query.filter(
        Payment.status == "COMPLETED"
    ).with_entities(func.sum(Payment.amount)).scalar() or Decimal('0')
    
    # Successful vs failed payments
    successful_payments = base_query.filter(Payment.status == "COMPLETED").count()
    failed_payments = base_query.filter(Payment.status == "FAILED").count()
    pending_payments = base_query.filter(Payment.status == "PENDING").count()
    
    # Revenue by payment method
    revenue_by_method = base_query.filter(
        Payment.status == "COMPLETED"
    ).with_entities(
        Payment.payment_method,
        func.sum(Payment.amount).label('revenue'),
        func.count(Payment.id).label('count')
    ).group_by(Payment.payment_method).all()
    
    # Revenue by payment type
    revenue_by_type = base_query.filter(
        Payment.status == "COMPLETED"
    ).with_entities(
        Payment.payment_type,
        func.sum(Payment.amount).label('revenue'),
        func.count(Payment.id).label('count')
    ).group_by(Payment.payment_type).all()
    
    # Daily revenue trend
    daily_revenue = base_query.filter(
        Payment.status == "COMPLETED"
    ).with_entities(
        Payment.payment_date,
        func.sum(Payment.amount).label('revenue')
    ).group_by(Payment.payment_date).order_by(Payment.payment_date).all()
    
    # Average payment amount
    avg_payment = base_query.filter(
        Payment.status == "COMPLETED"
    ).with_entities(func.avg(Payment.amount)).scalar() or Decimal('0')
    
    # Top paying customers
    top_customers = db.query(
        User.first_name,
        User.last_name,
        User.email,
        func.sum(Payment.amount).label('total_paid')
    ).join(Payment).filter(
        Payment.status == "COMPLETED",
        Payment.payment_date >= date_from,
        Payment.payment_date <= date_to
    ).group_by(User.id).order_by(desc('total_paid')).limit(10).all()
    
    return PaymentReport(
        period_start=date_from,
        period_end=date_to,
        total_payments=total_payments,
        total_revenue=float(total_revenue),
        successful_payments=successful_payments,
        failed_payments=failed_payments,
        pending_payments=pending_payments,
        success_rate=round((successful_payments / total_payments * 100) if total_payments > 0 else 0, 2),
        average_payment=float(avg_payment),
        revenue_by_method=[
            {
                "method": method,
                "revenue": float(revenue),
                "count": count
            }
            for method, revenue, count in revenue_by_method
        ],
        revenue_by_type=[
            {
                "type": ptype,
                "revenue": float(revenue),
                "count": count
            }
            for ptype, revenue, count in revenue_by_type
        ],
        daily_revenue=[
            {
                "date": payment_date.isoformat(),
                "revenue": float(revenue)
            }
            for payment_date, revenue in daily_revenue
        ],
        top_customers=[
            {
                "name": f"{first_name} {last_name}",
                "email": email,
                "total_paid": float(total_paid)
            }
            for first_name, last_name, email, total_paid in top_customers
        ]
    )

# Attendance report endpoint commented out due to missing AttendanceReport schema
# @router.get("/attendance-report", response_model=AttendanceReport)
# async def get_attendance_report(...):
#     pass

# Employee report endpoint commented out due to missing EmployeeReport schema
# @router.get("/employee-report", response_model=EmployeeReport)
# async def get_employee_report(...):
#     pass

# Financial summary endpoint commented out due to missing FinancialSummary schema
# @router.get("/financial-summary", response_model=FinancialSummary)
# async def get_financial_summary(...):
#     pass

# Export endpoint and helper functions commented out due to missing ExportFormat schema
# @router.get("/export/{report_type}")
# async def export_report(...):
#     pass

# Helper functions commented out
# async def _export_memberships_data(...):
#     pass
# async def _export_payments_data(...):
#     pass
# async def _export_users_data(...):
#     pass
# async def _export_classes_data(...):
#     pass