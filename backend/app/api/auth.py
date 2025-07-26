from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import (
    auth_manager, rate_limiter, create_user_tokens, verify_refresh_token,
    get_current_user, get_current_active_user
)
from app.core.utils import ValidationUtils, NotificationUtils, SecurityUtils
from app.models.user import User
from app.schemas.user import (
    UserLogin, UserRegister, Token, PasswordChange, 
    PasswordReset, PasswordResetConfirm, UserResponse
)
from app.core.config import settings
import secrets
import string

router = APIRouter(tags=["Authentication"])
security = HTTPBearer()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if rate_limiter.is_rate_limited(f"register_{client_ip}", max_attempts=3, window_minutes=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later."
        )
    
    # Validate email format
    if not ValidationUtils.validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | 
        (User.phone == user_data.phone)
    ).first()
    
    if existing_user:
        rate_limiter.record_attempt(f"register_{client_ip}")
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Validate password strength
    is_valid, password_issues = ValidationUtils.validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(password_issues)}"
        )
    
    # Validate phone number
    is_valid_phone, formatted_phone = ValidationUtils.validate_phone(user_data.phone)
    if not is_valid_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    
    # Create new user
    hashed_password = auth_manager.get_password_hash(user_data.password)
    
    new_user = User(
        email=user_data.email.lower(),
        phone=formatted_phone,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        date_of_birth=user_data.date_of_birth,
        gender=user_data.gender,
        role="MEMBER",  # Default role
        user_type="MONTHLY",  # Default type
        is_active=True,
        email_verified=False,
        terms_accepted=user_data.terms_accepted,
        terms_accepted_at=datetime.utcnow() if user_data.terms_accepted else None
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Send welcome email
        background_tasks.add_task(
            send_welcome_email,
            new_user.email,
            new_user.first_name
        )
        
        # Clear rate limiting on successful registration
        rate_limiter.clear_attempts(f"register_{client_ip}")
        
        return new_user
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )

@router.post("/test")
async def test_endpoint():
    """Simple test endpoint"""
    print("TEST ENDPOINT REACHED!")
    return {"message": "Test endpoint working"}

@router.post("/login-simple")
async def login_simple(user_credentials: UserLogin):
    """Simplified login endpoint for debugging"""
    return {
        "message": "Login endpoint reached",
        "email": user_credentials.email,
        "status": "success"
    }

@router.post("/login-debug")
async def login_debug(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Debug login endpoint to test step by step"""
    try:
        # Step 1: Check if user exists
        user = db.query(User).filter(User.email == user_credentials.email).first()
        if not user:
            return {
                "step": "1",
                "error": "User not found",
                "email": user_credentials.email
            }
        
        # Step 2: Check password
        password_valid = auth_manager.verify_password(user_credentials.password, user.password_hash)
        
        return {
            "step": "2",
            "user_found": True,
            "user_id": user.id,
            "user_email": user.email,
            "user_active": user.is_active,
            "password_valid": password_valid,
            "password_hash": user.password_hash[:20] + "..."
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }

@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token"""
    
    try:
        # Authenticate user
        user = auth_manager.authenticate_user(db, user_credentials.email, user_credentials.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        db.commit()
        
        # Create tokens
        tokens = create_user_tokens(user)
        
        # Return Token schema format
        return Token(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    # Verify refresh token
    user_id = verify_refresh_token(refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    tokens = create_user_tokens(user)
    
    # Return Token schema format
    return Token(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user=UserResponse.from_orm(user)
    )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """Logout user (invalidate token)"""
    
    # TODO: Implement token blacklisting with Redis
    # For now, just return success
    
    return {"message": "Successfully logged out"}

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    # Verify current password
    if not auth_manager.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    is_valid, password_issues = ValidationUtils.validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(password_issues)}"
        )
    
    # Check if new password is different from current
    if auth_manager.verify_password(password_data.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Update password
    current_user.password_hash = auth_manager.get_password_hash(password_data.new_password)
    current_user.password_changed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordReset,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    identifier = f"forgot_password_{password_reset.email}_{client_ip}"
    
    if rate_limiter.is_rate_limited(identifier, max_attempts=3, window_minutes=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset attempts. Please try again later."
        )
    
    # Find user
    user = db.query(User).filter(User.email == password_reset.email.lower()).first()
    
    if user and user.is_active:
        # Generate reset token
        reset_token = auth_manager.generate_reset_token()
        reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        
        # Save reset token
        user.reset_token = reset_token
        user.reset_token_expires = reset_expires
        db.commit()
        
        # Send reset email
        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            user.first_name,
            reset_token
        )
    
    # Always return success to prevent email enumeration
    rate_limiter.record_attempt(identifier)
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    
    # Find user with valid reset token
    user = db.query(User).filter(
        User.reset_token == reset_data.token,
        User.reset_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Validate new password strength
    is_valid, password_issues = ValidationUtils.validate_password_strength(reset_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(password_issues)}"
        )
    
    # Update password and clear reset token
    user.password_hash = auth_manager.get_password_hash(reset_data.new_password)
    user.password_changed_at = datetime.utcnow()
    user.reset_token = None
    user.reset_token_expires = None
    
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user

@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify user email address"""
    
    # TODO: Implement email verification token system
    # For now, just return success
    
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(
    email: str,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    """Resend email verification"""
    
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    identifier = f"resend_verification_{email}_{client_ip}"
    
    if rate_limiter.is_rate_limited(identifier, max_attempts=3, window_minutes=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification attempts. Please try again later."
        )
    
    # Find user
    user = db.query(User).filter(User.email == email.lower()).first()
    
    if user and not user.email_verified:
        # Send verification email
        background_tasks.add_task(
            send_verification_email,
            user.email,
            user.first_name
        )
    
    rate_limiter.record_attempt(identifier)
    return {"message": "If the email exists and is unverified, a verification link has been sent"}

# Background tasks for email notifications
async def send_welcome_email(email: str, first_name: str):
    """Send welcome email to new user"""
    subject = f"¡Bienvenido a {settings.PROJECT_NAME}!"
    body = f"""
    Hola {first_name},
    
    ¡Bienvenido a {settings.PROJECT_NAME}! Tu cuenta ha sido creada exitosamente.
    
    Ahora puedes acceder a todas las funcionalidades de nuestro gimnasio.
    
    Si tienes alguna pregunta, no dudes en contactarnos.
    
    ¡Nos vemos en el gimnasio!
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)

async def send_password_reset_email(email: str, first_name: str, reset_token: str):
    """Send password reset email"""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    subject = "Restablecer contraseña"
    body = f"""
    Hola {first_name},
    
    Hemos recibido una solicitud para restablecer tu contraseña.
    
    Haz clic en el siguiente enlace para restablecer tu contraseña:
    {reset_url}
    
    Este enlace expirará en 1 hora.
    
    Si no solicitaste este cambio, puedes ignorar este correo.
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)

async def send_verification_email(email: str, first_name: str):
    """Send email verification"""
    verification_token = SecurityUtils.generate_secure_token()
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    
    subject = "Verificar correo electrónico"
    body = f"""
    Hola {first_name},
    
    Por favor verifica tu correo electrónico haciendo clic en el siguiente enlace:
    {verification_url}
    
    Si no creaste esta cuenta, puedes ignorar este correo.
    
    Saludos,
    El equipo de {settings.PROJECT_NAME}
    """
    
    NotificationUtils.send_email(email, subject, body)