from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from ..core.database import get_db, Base
from ..models.user import User
import uuid
from ipaddress import ip_address, IPv4Address, IPv6Address
import asyncio
from collections import defaultdict, deque
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class AuditAction(Enum):
    """Types of auditable actions"""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # User Management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ACTIVATE = "user_activate"
    USER_DEACTIVATE = "user_deactivate"
    
    # Membership Management
    MEMBERSHIP_CREATE = "membership_create"
    MEMBERSHIP_UPDATE = "membership_update"
    MEMBERSHIP_DELETE = "membership_delete"
    MEMBERSHIP_RENEW = "membership_renew"
    MEMBERSHIP_SUSPEND = "membership_suspend"
    
    # Payment Management
    PAYMENT_CREATE = "payment_create"
    PAYMENT_UPDATE = "payment_update"
    PAYMENT_DELETE = "payment_delete"
    PAYMENT_REFUND = "payment_refund"
    
    # Class Management
    CLASS_CREATE = "class_create"
    CLASS_UPDATE = "class_update"
    CLASS_DELETE = "class_delete"
    CLASS_CANCEL = "class_cancel"
    CLASS_BOOK = "class_book"
    CLASS_UNBOOK = "class_unbook"
    
    # Exercise & Routine Management
    EXERCISE_CREATE = "exercise_create"
    EXERCISE_UPDATE = "exercise_update"
    EXERCISE_DELETE = "exercise_delete"
    ROUTINE_CREATE = "routine_create"
    ROUTINE_UPDATE = "routine_update"
    ROUTINE_DELETE = "routine_delete"
    
    # System Configuration
    CONFIG_UPDATE = "config_update"
    CONFIG_RESET = "config_reset"
    CONFIG_IMPORT = "config_import"
    CONFIG_EXPORT = "config_export"
    
    # Data Management
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    DATA_BACKUP = "data_backup"
    DATA_RESTORE = "data_restore"
    
    # Security Events
    SECURITY_BREACH_ATTEMPT = "security_breach_attempt"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # System Events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    SYSTEM_ERROR = "system_error"
    MAINTENANCE_START = "maintenance_start"
    MAINTENANCE_END = "maintenance_end"
    
    # File Operations
    FILE_UPLOAD = "file_upload"
    FILE_DELETE = "file_delete"
    FILE_ACCESS = "file_access"
    
    # API Operations
    API_CALL = "api_call"
    API_ERROR = "api_error"
    
    # Custom Actions
    CUSTOM = "custom"

class AuditLevel(Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    DEBUG = "debug"

class AuditCategory(Enum):
    """Audit event categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_ADMINISTRATION = "system_administration"
    SECURITY = "security"
    BUSINESS_OPERATION = "business_operation"
    SYSTEM_EVENT = "system_event"
    USER_ACTIVITY = "user_activity"
    API_USAGE = "api_usage"

@dataclass
class AuditContext:
    """Context information for audit events"""
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    
class AuditLogModel(Base):
    """Database model for audit logs"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Action Information
    action = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)
    
    # User Information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    user_role = Column(String(50), nullable=True)
    
    # Request Information
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    request_id = Column(String(36), nullable=True, index=True)
    endpoint = Column(String(255), nullable=True, index=True)
    method = Column(String(10), nullable=True)
    
    # Event Details
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Data Changes
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    
    # Additional Context
    audit_metadata = Column(Text, nullable=True)  # JSON
    
    # Status
    success = Column(Boolean, default=True, index=True)
    error_message = Column(Text, nullable=True)
    
    # Performance
    duration_ms = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

class AuditService:
    """Comprehensive audit logging service"""
    
    def __init__(self):
        self.batch_size = 100
        self.batch_timeout = 30  # seconds
        self.pending_logs = deque()
        self.batch_lock = threading.Lock()
        self.background_task = None
        self.is_running = False
        
        # Performance tracking
        self.performance_stats = defaultdict(list)
        self.stats_lock = threading.Lock()
        
        # Rate limiting for audit logs
        self.rate_limits = {
            AuditAction.API_CALL: 1000,  # Max 1000 API call logs per minute
            AuditAction.FILE_ACCESS: 500,  # Max 500 file access logs per minute
        }
        self.rate_counters = defaultdict(lambda: defaultdict(int))
        
        # Context storage for request-scoped data
        self.context_storage = threading.local()
    
    async def start_background_processing(self):
        """Start background task for batch processing"""
        if self.is_running:
            return
        
        self.is_running = True
        self.background_task = asyncio.create_task(self._background_processor())
        logger.info("Audit service background processing started")
    
    async def stop_background_processing(self):
        """Stop background processing and flush remaining logs"""
        self.is_running = False
        
        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining logs
        await self._flush_pending_logs()
        logger.info("Audit service background processing stopped")
    
    async def _background_processor(self):
        """Background task to process audit logs in batches"""
        while self.is_running:
            try:
                await asyncio.sleep(self.batch_timeout)
                await self._flush_pending_logs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in audit background processor: {e}")
    
    async def _flush_pending_logs(self):
        """Flush pending logs to database"""
        if not self.pending_logs:
            return
        
        with self.batch_lock:
            logs_to_process = list(self.pending_logs)
            self.pending_logs.clear()
        
        if not logs_to_process:
            return
        
        try:
            db = next(get_db())
            
            # Batch insert
            db.bulk_insert_mappings(AuditLogModel, logs_to_process)
            db.commit()
            
            logger.debug(f"Flushed {len(logs_to_process)} audit logs to database")
            
        except Exception as e:
            logger.error(f"Error flushing audit logs: {e}")
            
            # Re-add logs to queue for retry
            with self.batch_lock:
                self.pending_logs.extendleft(reversed(logs_to_process))
    
    def set_context(self, context: AuditContext):
        """Set audit context for current request/session"""
        self.context_storage.context = context
    
    def get_context(self) -> Optional[AuditContext]:
        """Get current audit context"""
        return getattr(self.context_storage, 'context', None)
    
    @contextmanager
    def audit_context(self, context: AuditContext):
        """Context manager for audit context"""
        old_context = self.get_context()
        self.set_context(context)
        try:
            yield
        finally:
            self.set_context(old_context)
    
    def log(
        self,
        action: AuditAction,
        category: AuditCategory,
        level: AuditLevel = AuditLevel.INFO,
        description: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[Union[str, int]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[float] = None,
        context: Optional[AuditContext] = None
    ):
        """Log an audit event"""
        try:
            # Check rate limiting
            if self._is_rate_limited(action):
                return
            
            # Use provided context or get from thread local
            audit_context = context or self.get_context() or AuditContext()
            
            # Create audit log entry
            log_entry = {
                'event_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow(),
                'action': action.value,
                'category': category.value,
                'level': level.value,
                'user_id': audit_context.user_id,
                'user_email': audit_context.user_email,
                'user_role': audit_context.user_role,
                'ip_address': audit_context.ip_address,
                'user_agent': audit_context.user_agent,
                'session_id': audit_context.session_id,
                'request_id': audit_context.request_id,
                'endpoint': audit_context.endpoint,
                'method': audit_context.method,
                'resource_type': resource_type,
                'resource_id': str(resource_id) if resource_id else None,
                'description': description,
                'old_values': json.dumps(old_values) if old_values else None,
                'new_values': json.dumps(new_values) if new_values else None,
                'audit_metadata': json.dumps(metadata) if metadata else None,
                'success': success,
                'error_message': error_message,
                'duration_ms': duration_ms
            }
            
            # Add to pending logs for batch processing
            with self.batch_lock:
                self.pending_logs.append(log_entry)
                
                # Flush if batch is full
                if len(self.pending_logs) >= self.batch_size:
                    asyncio.create_task(self._flush_pending_logs())
            
            # Log to application logger for immediate visibility
            log_message = f"AUDIT: {action.value} - {description or 'No description'}"
            if audit_context.user_email:
                log_message += f" (User: {audit_context.user_email})"
            
            if level == AuditLevel.ERROR or level == AuditLevel.CRITICAL:
                logger.error(log_message)
            elif level == AuditLevel.WARNING:
                logger.warning(log_message)
            else:
                logger.info(log_message)
            
            # Update performance stats
            if duration_ms is not None:
                with self.stats_lock:
                    self.performance_stats[action.value].append(duration_ms)
                    
                    # Keep only last 1000 entries per action
                    if len(self.performance_stats[action.value]) > 1000:
                        self.performance_stats[action.value] = self.performance_stats[action.value][-1000:]
        
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
    
    def _is_rate_limited(self, action: AuditAction) -> bool:
        """Check if action is rate limited"""
        if action not in self.rate_limits:
            return False
        
        current_minute = datetime.now().replace(second=0, microsecond=0)
        
        with self.stats_lock:
            self.rate_counters[action][current_minute] += 1
            
            # Clean old entries
            cutoff_time = current_minute - timedelta(minutes=5)
            keys_to_remove = [k for k in self.rate_counters[action] if k < cutoff_time]
            for key in keys_to_remove:
                del self.rate_counters[action][key]
            
            # Check rate limit
            current_count = self.rate_counters[action][current_minute]
            return current_count > self.rate_limits[action]
    
    def log_authentication(self, action: AuditAction, user_email: str, success: bool, error_message: Optional[str] = None):
        """Log authentication events"""
        self.log(
            action=action,
            category=AuditCategory.AUTHENTICATION,
            level=AuditLevel.WARNING if not success else AuditLevel.INFO,
            description=f"Authentication attempt for {user_email}",
            resource_type="user",
            resource_id=user_email,
            success=success,
            error_message=error_message
        )
    
    def log_data_change(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: Union[str, int],
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ):
        """Log data modification events"""
        self.log(
            action=action,
            category=AuditCategory.DATA_MODIFICATION,
            level=AuditLevel.INFO,
            description=description or f"{action.value} on {resource_type}",
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values
        )
    
    def log_security_event(
        self,
        action: AuditAction,
        description: str,
        level: AuditLevel = AuditLevel.WARNING,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log security events"""
        self.log(
            action=action,
            category=AuditCategory.SECURITY,
            level=level,
            description=description,
            metadata=metadata,
            success=False
        )
    
    def log_system_event(
        self,
        action: AuditAction,
        description: str,
        level: AuditLevel = AuditLevel.INFO,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log system events"""
        self.log(
            action=action,
            category=AuditCategory.SYSTEM_EVENT,
            level=level,
            description=description,
            metadata=metadata
        )
    
    def log_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        error_message: Optional[str] = None
    ):
        """Log API calls"""
        success = 200 <= status_code < 400
        level = AuditLevel.ERROR if status_code >= 500 else AuditLevel.WARNING if status_code >= 400 else AuditLevel.INFO
        
        self.log(
            action=AuditAction.API_CALL,
            category=AuditCategory.API_USAGE,
            level=level,
            description=f"{method} {endpoint} - {status_code}",
            metadata={
                'status_code': status_code,
                'response_time_ms': duration_ms
            },
            success=success,
            error_message=error_message,
            duration_ms=duration_ms
        )
    
    async def get_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        action: Optional[AuditAction] = None,
        category: Optional[AuditCategory] = None,
        level: Optional[AuditLevel] = None,
        resource_type: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering"""
        try:
            db = next(get_db())
            
            query = db.query(AuditLogModel)
            
            # Apply filters
            if start_date:
                query = query.filter(AuditLogModel.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLogModel.timestamp <= end_date)
            if user_id:
                query = query.filter(AuditLogModel.user_id == user_id)
            if action:
                query = query.filter(AuditLogModel.action == action.value)
            if category:
                query = query.filter(AuditLogModel.category == category.value)
            if level:
                query = query.filter(AuditLogModel.level == level.value)
            if resource_type:
                query = query.filter(AuditLogModel.resource_type == resource_type)
            if success is not None:
                query = query.filter(AuditLogModel.success == success)
            
            # Order by timestamp descending
            query = query.order_by(AuditLogModel.timestamp.desc())
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            logs = query.all()
            
            # Convert to dictionaries
            result = []
            for log in logs:
                log_dict = {
                    'id': log.id,
                    'event_id': log.event_id,
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.action,
                    'category': log.category,
                    'level': log.level,
                    'user_id': log.user_id,
                    'user_email': log.user_email,
                    'user_role': log.user_role,
                    'ip_address': log.ip_address,
                    'session_id': log.session_id,
                    'request_id': log.request_id,
                    'endpoint': log.endpoint,
                    'method': log.method,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'description': log.description,
                    'success': log.success,
                    'error_message': log.error_message,
                    'duration_ms': log.duration_ms
                }
                
                # Parse JSON fields
                if log.old_values:
                    try:
                        log_dict['old_values'] = json.loads(log.old_values)
                    except json.JSONDecodeError:
                        log_dict['old_values'] = log.old_values
                
                if log.new_values:
                    try:
                        log_dict['new_values'] = json.loads(log.new_values)
                    except json.JSONDecodeError:
                        log_dict['new_values'] = log.new_values
                
                if log.audit_metadata:
                    try:
                        log_dict['metadata'] = json.loads(log.audit_metadata)
                    except json.JSONDecodeError:
                        log_dict['metadata'] = log.audit_metadata
                
                result.append(log_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            return []
    
    async def get_audit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit statistics"""
        try:
            db = next(get_db())
            
            query = db.query(AuditLogModel)
            
            if start_date:
                query = query.filter(AuditLogModel.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLogModel.timestamp <= end_date)
            
            logs = query.all()
            
            # Calculate statistics
            total_events = len(logs)
            successful_events = len([log for log in logs if log.success])
            failed_events = total_events - successful_events
            
            # Group by action
            action_counts = defaultdict(int)
            for log in logs:
                action_counts[log.action] += 1
            
            # Group by category
            category_counts = defaultdict(int)
            for log in logs:
                category_counts[log.category] += 1
            
            # Group by level
            level_counts = defaultdict(int)
            for log in logs:
                level_counts[log.level] += 1
            
            # Group by user
            user_counts = defaultdict(int)
            for log in logs:
                if log.user_email:
                    user_counts[log.user_email] += 1
            
            # Performance statistics
            performance_stats = {}
            with self.stats_lock:
                for action, durations in self.performance_stats.items():
                    if durations:
                        performance_stats[action] = {
                            'count': len(durations),
                            'avg_duration_ms': sum(durations) / len(durations),
                            'min_duration_ms': min(durations),
                            'max_duration_ms': max(durations)
                        }
            
            return {
                'total_events': total_events,
                'successful_events': successful_events,
                'failed_events': failed_events,
                'success_rate': (successful_events / total_events * 100) if total_events > 0 else 0,
                'action_counts': dict(action_counts),
                'category_counts': dict(category_counts),
                'level_counts': dict(level_counts),
                'user_counts': dict(user_counts),
                'performance_stats': performance_stats,
                'date_range': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {e}")
            return {}
    
    async def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Clean up old audit logs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            db = next(get_db())
            
            # Count logs to be deleted
            count = db.query(AuditLogModel).filter(
                AuditLogModel.timestamp < cutoff_date
            ).count()
            
            # Delete old logs
            db.query(AuditLogModel).filter(
                AuditLogModel.timestamp < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {count} audit logs older than {days_to_keep} days")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up audit logs: {e}")
            return 0

# Global audit service instance
audit_service = AuditService()

# Decorator for automatic audit logging
def audit_action(
    action: AuditAction,
    category: AuditCategory,
    resource_type: Optional[str] = None,
    description: Optional[str] = None
):
    """Decorator to automatically audit function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            success = True
            error_message = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                audit_service.log(
                    action=action,
                    category=category,
                    description=description or f"{func.__name__} called",
                    resource_type=resource_type,
                    success=success,
                    error_message=error_message,
                    duration_ms=duration_ms
                )
        
        return wrapper
    return decorator