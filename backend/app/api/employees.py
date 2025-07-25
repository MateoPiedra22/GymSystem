from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from ..core.database import get_db
from ..core.auth import (
    get_current_active_user, get_current_staff_user, get_current_admin_user,
    require_employee_management, hash_password
)
from ..core.utils import ValidationUtils, DataUtils, BusinessUtils, DateUtils
from ..models.user import User
from ..models.employee import Employee
from ..schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeList, EmployeeStats,
    EmployeeFilter, PayrollSummary, PerformanceReview
)

router = APIRouter(prefix="/employees", tags=["Employees"])

@router.get("/", response_model=EmployeeList)
async def get_employees(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or employee ID"),
    position: Optional[str] = Query(None, description="Filter by position"),
    department: Optional[str] = Query(None, description="Filter by department"),
    employment_status: Optional[str] = Query(None, description="Filter by employment status"),
    contract_type: Optional[str] = Query(None, description="Filter by contract type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    hired_after: Optional[date] = Query(None, description="Hired after date"),
    hired_before: Optional[date] = Query(None, description="Hired before date"),
    sort_by: str = Query("hire_date", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get employees with filtering, searching, and pagination"""
    
    # Build query
    query = db.query(Employee).options(
        joinedload(Employee.user)
    )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.join(User).filter(
            or_(
                func.concat(User.first_name, ' ', User.last_name).ilike(search_term),
                User.email.ilike(search_term),
                Employee.employee_id.ilike(search_term)
            )
        )
    
    # Apply filters
    if position:
        query = query.filter(Employee.position == position)
    
    if department:
        query = query.filter(Employee.department == department)
    
    if employment_status:
        query = query.filter(Employee.employment_status == employment_status)
    
    if contract_type:
        query = query.filter(Employee.contract_type == contract_type)
    
    if is_active is not None:
        query = query.filter(Employee.is_active == is_active)
    
    # Date filters
    if hired_after:
        query = query.filter(Employee.hire_date >= hired_after)
    
    if hired_before:
        query = query.filter(Employee.hire_date <= hired_before)
    
    # Apply sorting
    sort_column = getattr(Employee, sort_by, Employee.hire_date)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Paginate
    result = DataUtils.paginate_query(query, page, per_page)
    
    return EmployeeList(
        employees=result['items'],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages']
    )

@router.get("/stats", response_model=EmployeeStats)
async def get_employee_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get employee statistics"""
    
    # Total employees
    total_employees = db.query(Employee).count()
    
    # Active employees
    active_employees = db.query(Employee).filter(Employee.is_active == True).count()
    
    # New hires this month
    start_of_month, end_of_month = DateUtils.get_month_dates()
    new_hires_this_month = db.query(Employee).filter(
        Employee.hire_date >= start_of_month,
        Employee.hire_date <= end_of_month
    ).count()
    
    # Employees by position
    employees_by_position = db.query(
        Employee.position,
        func.count(Employee.id).label('count')
    ).group_by(Employee.position).all()
    
    # Employees by department
    employees_by_department = db.query(
        Employee.department,
        func.count(Employee.id).label('count')
    ).group_by(Employee.department).all()
    
    # Employees by employment status
    employees_by_status = db.query(
        Employee.employment_status,
        func.count(Employee.id).label('count')
    ).group_by(Employee.employment_status).all()
    
    # Employees by contract type
    employees_by_contract = db.query(
        Employee.contract_type,
        func.count(Employee.id).label('count')
    ).group_by(Employee.contract_type).all()
    
    # Average salary by position
    avg_salary_by_position = db.query(
        Employee.position,
        func.avg(Employee.salary).label('avg_salary')
    ).filter(Employee.salary.isnot(None)).group_by(Employee.position).all()
    
    # Total payroll
    total_payroll = db.query(
        func.sum(Employee.salary)
    ).filter(
        Employee.is_active == True,
        Employee.salary.isnot(None)
    ).scalar() or Decimal('0')
    
    return EmployeeStats(
        total_employees=total_employees,
        active_employees=active_employees,
        inactive_employees=total_employees - active_employees,
        new_hires_this_month=new_hires_this_month,
        employees_by_position={position: count for position, count in employees_by_position},
        employees_by_department={dept: count for dept, count in employees_by_department},
        employees_by_status={status: count for status, count in employees_by_status},
        employees_by_contract={contract: count for contract, count in employees_by_contract},
        avg_salary_by_position={position: float(avg_salary) for position, avg_salary in avg_salary_by_position},
        total_payroll=float(total_payroll)
    )

@router.get("/positions", response_model=List[str])
async def get_positions(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get all employee positions"""
    
    positions = db.query(Employee.position).distinct().filter(
        Employee.position.isnot(None),
        Employee.is_active == True
    ).all()
    
    return [position[0] for position in positions if position[0]]

@router.get("/departments", response_model=List[str])
async def get_departments(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get all departments"""
    
    departments = db.query(Employee.department).distinct().filter(
        Employee.department.isnot(None),
        Employee.is_active == True
    ).all()
    
    return [dept[0] for dept in departments if dept[0]]

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get employee by ID"""
    
    employee = db.query(Employee).options(
        joinedload(Employee.user)
    ).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return employee

@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_employee_management),
    db: Session = Depends(get_db)
):
    """Create a new employee"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == employee_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is already an employee
    existing_employee = db.query(Employee).filter(
        Employee.user_id == employee_data.user_id
    ).first()
    
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an employee"
        )
    
    # Generate employee ID
    employee_id = BusinessUtils.generate_membership_number()  # Reuse function for unique ID
    
    # Create employee
    new_employee = Employee(
        user_id=employee_data.user_id,
        employee_id=employee_id,
        position=employee_data.position,
        department=employee_data.department,
        hire_date=employee_data.hire_date,
        employment_status=employee_data.employment_status or "ACTIVE",
        contract_type=employee_data.contract_type,
        salary=employee_data.salary,
        hourly_rate=employee_data.hourly_rate,
        benefits=employee_data.benefits or [],
        emergency_contact_name=employee_data.emergency_contact_name,
        emergency_contact_phone=employee_data.emergency_contact_phone,
        bank_account=employee_data.bank_account,
        tax_id=employee_data.tax_id,
        social_security=employee_data.social_security,
        access_level=employee_data.access_level or "BASIC",
        permissions=employee_data.permissions or [],
        notes=employee_data.notes,
        created_by_id=current_user.id
    )
    
    try:
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        
        # Update user role if needed
        if employee_data.position in ["MANAGER", "ADMIN", "OWNER"]:
            user.role = employee_data.position
            user.is_staff = True
            db.commit()
        
        # Send welcome email
        background_tasks.add_task(
            send_employee_welcome_notification,
            user.email,
            user.first_name,
            new_employee
        )
        
        return new_employee
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create employee"
        )

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: User = Depends(require_employee_management),
    db: Session = Depends(get_db)
):
    """Update employee information"""
    
    employee = db.query(Employee).options(
        joinedload(Employee.user)
    ).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Update employee fields
    update_data = employee_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(employee, field):
            setattr(employee, field, value)
    
    employee.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        
        # Update user role if position changed
        if 'position' in update_data:
            if employee.position in ["MANAGER", "ADMIN", "OWNER"]:
                employee.user.role = employee.position
                employee.user.is_staff = True
            else:
                employee.user.role = "MEMBER"
                employee.user.is_staff = False
            db.commit()
        
        db.refresh(employee)
        return employee
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employee"
        )

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    current_user: User = Depends(require_employee_management),
    db: Session = Depends(get_db)
):
    """Delete employee (soft delete)"""
    
    employee = db.query(Employee).options(
        joinedload(Employee.user)
    ).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Prevent deletion of owner accounts
    if employee.position == "OWNER":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete owner accounts"
        )
    
    # Soft delete
    employee.is_active = False
    employee.employment_status = "TERMINATED"
    employee.termination_date = date.today()
    employee.deleted_at = datetime.utcnow()
    employee.deleted_by_id = current_user.id
    
    # Update user role
    employee.user.role = "MEMBER"
    employee.user.is_staff = False
    
    try:
        db.commit()
        return {"message": "Employee deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete employee"
        )

# Background tasks
async def send_employee_welcome_notification(
    email: str, first_name: str, employee: Employee
):
    """Send welcome notification to new employee"""
    from ..core.utils import NotificationUtils
    from ..core.config import settings
    
    subject = f"¡Bienvenido al equipo de {settings.PROJECT_NAME}!"
    body = f"""
    Hola {first_name},
    
    ¡Bienvenido al equipo de {settings.PROJECT_NAME}!
    
    Detalles de tu empleo:
    - ID de empleado: {employee.employee_id}
    - Posición: {employee.position}
    - Departamento: {employee.department}
    - Fecha de contratación: {employee.hire_date.strftime('%d/%m/%Y')}
    
    Pronto recibirás más información sobre tu horario y responsabilidades.
    
    ¡Esperamos trabajar contigo!
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)