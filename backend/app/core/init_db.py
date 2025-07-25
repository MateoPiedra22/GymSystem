from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.employee import Employee, EmployeeStatus, ContractType
from app.core.auth import get_password_hash
from loguru import logger
from datetime import datetime


def init_db() -> None:
    """Initialize database with default data"""
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@gymsystem.com").first()
        
        if not admin_user:
            # Create default admin user
            admin_user = User(
                user_id="ADMIN001",
                email="admin@gymsystem.com",
                phone="+541234567890",
                password_hash=get_password_hash("admin123"),
                first_name="System",
                last_name="Administrator",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            logger.info("✅ Default admin user created")
        
        # Check if admin employee exists
        admin_employee = db.query(Employee).filter(Employee.user_id == admin_user.id).first()
        
        if not admin_employee:
            # Create default admin employee
            admin_employee = Employee(
                user_id=admin_user.id,
                employee_id="EMP001",
                position="System Administrator",
                department="IT",
                hire_date=datetime(2024, 1, 1),
                contract_type=ContractType.FULL_TIME,
                status=EmployeeStatus.ACTIVE,
                salary=50000.0,
                access_level=5
            )
            db.add(admin_employee)
            db.commit()
            logger.info("✅ Default admin employee created")
        
        logger.info("🔧 Database initialization completed")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        db.rollback()
    finally:
        db.close()