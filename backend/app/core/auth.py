from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.database import get_db
from ..models.user import User
from ..schemas.user import TokenData
import secrets
import string

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme for JWT
security = HTTPBearer()

class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token (longer expiration)"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: int = payload.get("sub")
            if user_id is None:
                return None
            token_data = TokenData(user_id=user_id)
            return token_data
        except JWTError:
            return None
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    def generate_reset_token(self) -> str:
        """Generate a secure reset token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """Validate password strength based on settings"""
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
        
        if settings.REQUIRE_PASSWORD_COMPLEXITY:
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
            
            if not (has_upper and has_lower and has_digit and has_special):
                return False, "Password must contain uppercase, lowercase, digit, and special character"
        
        return True, "Password is valid"
    
    def check_user_permissions(self, user: User, required_permission: str) -> bool:
        """Check if user has required permission"""
        permission_map = {
            "admin_access": user.can_access_admin,
            "manage_users": user.can_manage_users,
            "manage_classes": user.can_manage_classes,
            "create_routines": user.can_create_routines,
            "staff_access": user.is_staff,
        }
        
        return permission_map.get(required_permission, False)
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted (implement with Redis in production)"""
        # TODO: Implement token blacklisting with Redis
        return False
    
    def blacklist_token(self, token: str) -> None:
        """Add token to blacklist (implement with Redis in production)"""
        # TODO: Implement token blacklisting with Redis
        pass

# Global auth manager instance
auth_manager = AuthManager()

# Standalone functions for backward compatibility
def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return auth_manager.get_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return auth_manager.verify_password(plain_password, hashed_password)

# Dependency functions
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        
        # Check if token is blacklisted
        if auth_manager.is_token_blacklisted(token):
            raise credentials_exception
        
        # Verify token
        token_data = auth_manager.verify_token(token)
        if token_data is None:
            raise credentials_exception
        
        # Get user from database
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if user is None:
            raise credentials_exception
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return user
    
    except JWTError:
        raise credentials_exception

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

def get_current_staff_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current staff user (admin, owner, trainer)"""
    if not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current admin user (admin or owner)"""
    if not current_user.can_access_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def get_current_owner_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current owner user"""
    if current_user.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required"
        )
    return current_user

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not auth_manager.check_user_permissions(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker

# Permission-specific dependencies
require_admin_access = require_permission("admin_access")
require_user_management = require_permission("manage_users")
require_class_management = require_permission("manage_classes")
require_routine_creation = require_permission("create_routines")
require_staff_access = require_permission("staff_access")
require_exercise_management = require_permission("manage_exercises")
require_routine_management = require_permission("manage_routines")
require_payment_management = require_permission("manage_payments")
require_employee_management = require_permission("manage_employees")
require_membership_management = require_permission("manage_memberships")

# Rate limiting helpers
class RateLimiter:
    """Simple rate limiter for authentication attempts"""
    
    def __init__(self):
        self.attempts = {}  # In production, use Redis
    
    def is_rate_limited(self, identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if identifier is rate limited"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        # Remove old attempts
        self.attempts[identifier] = [
            attempt_time for attempt_time in self.attempts[identifier]
            if attempt_time > window_start
        ]
        
        return len(self.attempts[identifier]) >= max_attempts
    
    def record_attempt(self, identifier: str) -> None:
        """Record a failed attempt"""
        now = datetime.utcnow()
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        self.attempts[identifier].append(now)
    
    def clear_attempts(self, identifier: str) -> None:
        """Clear attempts for identifier (on successful login)"""
        if identifier in self.attempts:
            del self.attempts[identifier]

# Global rate limiter instance
rate_limiter = RateLimiter()

# Utility functions
def create_user_tokens(user: User) -> dict:
    """Create access and refresh tokens for user"""
    access_token_expires = timedelta(minutes=auth_manager.access_token_expire_minutes)
    access_token = auth_manager.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = auth_manager.create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": auth_manager.access_token_expire_minutes * 60
    }

def verify_refresh_token(token: str) -> Optional[int]:
    """Verify refresh token and return user ID"""
    try:
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        user_id: int = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            return None
        
        return int(user_id)
    except JWTError:
        return None

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return auth_manager.get_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return auth_manager.verify_password(plain_password, hashed_password)

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Session management
class SessionManager:
    """Manage user sessions"""
    
    def __init__(self):
        self.active_sessions = {}  # In production, use Redis
    
    def create_session(self, user_id: int, token: str, expires_at: datetime) -> str:
        """Create a new session"""
        session_id = generate_secure_token()
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "token": token,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session by ID"""
        session = self.active_sessions.get(session_id)
        if session and session["expires_at"] > datetime.utcnow():
            return session
        elif session:
            # Remove expired session
            del self.active_sessions[session_id]
        return None
    
    def invalidate_session(self, session_id: str) -> None:
        """Invalidate a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def invalidate_user_sessions(self, user_id: int) -> None:
        """Invalidate all sessions for a user"""
        sessions_to_remove = [
            session_id for session_id, session in self.active_sessions.items()
            if session["user_id"] == user_id
        ]
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
    
    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions"""
        now = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if session["expires_at"] <= now
        ]
        for session_id in expired_sessions:
            del self.active_sessions[session_id]

# Global session manager
session_manager = SessionManager()