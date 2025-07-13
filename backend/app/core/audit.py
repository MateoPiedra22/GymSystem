"""
Sistema de auditoría de seguridad
Registra eventos críticos de seguridad y actividades sospechosas
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings
from app.core.database import get_db

# Base para modelos de auditoría
AuditBase = declarative_base()

class EventType(Enum):
    """Tipos de eventos de auditoría"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_BLOCKED = "login_blocked"
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_DELETED = "account_deleted"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    DATA_ACCESSED = "data_accessed"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"
    FILE_UPLOADED = "file_uploaded"
    FILE_DOWNLOADED = "file_downloaded"
    FILE_DELETED = "file_deleted"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ATTACK_DETECTED = "attack_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_CHANGED = "configuration_changed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"

class RiskLevel(Enum):
    """Niveles de riesgo"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Evento de auditoría"""
    event_type: EventType
    risk_level: RiskLevel
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    success: bool = True
    message: str = ""
    details: Dict[str, Any] = None
    timestamp: datetime = None
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}

class SecurityAuditLog(AuditBase):
    """Modelo de base de datos para logs de auditoría"""
    __tablename__ = "security_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    risk_level = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(200), nullable=True, index=True)
    method = Column(String(10), nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON serializado
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    hash_signature = Column(String(64), nullable=True)  # Para integridad
    
    # Índices compuestos para consultas comunes
    __table_args__ = (
        Index('idx_user_activity', 'user_id', 'timestamp'),
        Index('idx_ip_activity', 'ip_address', 'timestamp'),
        Index('idx_risk_events', 'risk_level', 'timestamp'),
        Index('idx_event_type_time', 'event_type', 'timestamp'),
    )

class SecurityAuditor:
    """Gestor de auditoría de seguridad"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configurar logger específico para auditoría
        audit_handler = logging.FileHandler('logs/security_audit.log')
        audit_formatter = logging.Formatter(
            '%(asctime)s [AUDIT] [%(levelname)s] %(message)s'
        )
        audit_handler.setFormatter(audit_formatter)
        self.audit_logger = logging.getLogger('security_audit')
        self.audit_logger.addHandler(audit_handler)
        self.audit_logger.setLevel(logging.INFO)
    
    def log_event(self, event: AuditEvent, db: Session = None) -> bool:
        """
        Registra un evento de auditoría
        
        Args:
            event: Evento a registrar
            db: Sesión de base de datos (opcional)
            
        Returns:
            bool: True si se registró correctamente
        """
        try:
            # Log en archivo
            self._log_to_file(event)
            
            # Log en base de datos si está disponible
            if db:
                self._log_to_database(event, db)
            
            # Log en sistema de monitoreo externo (si está configurado)
            self._log_to_external_system(event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging audit event: {str(e)}")
            return False
    
    def _log_to_file(self, event: AuditEvent):
        """Registra evento en archivo de log con logging asíncrono"""
        try:
            log_data = {
                'event_type': event.event_type.value,
                'risk_level': event.risk_level.value,
                'user_id': event.user_id,
                'username': event.username,
                'ip_address': event.ip_address,
                'endpoint': event.endpoint,
                'method': event.method,
                'success': event.success,
                'message': event.message,
                'details': event.details,
                'timestamp': event.timestamp.isoformat(),
                'session_id': event.session_id
            }
            
            log_level = self._get_log_level(event.risk_level)
            
            # Logging asíncrono para no impactar el rendimiento
            import threading
            
            def async_log():
                try:
                    self.audit_logger.log(log_level, json.dumps(log_data, ensure_ascii=False))
                except Exception as e:
                    # Fallback a logging síncrono si hay error
                    self.logger.error(f"Error en logging asíncrono: {e}")
                    self.audit_logger.log(log_level, json.dumps(log_data, ensure_ascii=False))
            
            # Ejecutar en thread separado para no bloquear
            thread = threading.Thread(target=async_log, daemon=True)
            thread.start()
            
        except Exception as e:
            # Fallback en caso de error
            self.logger.error(f"Error en logging de auditoría: {e}")
            try:
                self.audit_logger.log(logging.ERROR, f"Error logging event: {event.event_type.value}")
            except:
                pass
    
    def _log_to_database(self, event: AuditEvent, db: Session):
        """Registra evento en base de datos"""
        try:
            audit_record = self._create_audit_record(event)
            db.add(audit_record)
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Error saving audit event to database: {str(e)}")
            db.rollback()
    
    def _create_audit_record(self, event: AuditEvent) -> SecurityAuditLog:
        """Crea el registro de auditoría"""
        details_json = self._serialize_details(event.details)
        hash_signature = self._generate_hash_signature(event)
        
        return SecurityAuditLog(
            event_type=event.event_type.value,
            risk_level=event.risk_level.value,
            user_id=event.user_id,
            username=event.username,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            endpoint=event.endpoint,
            method=event.method,
            success=event.success,
            message=event.message,
            details=details_json,
            timestamp=event.timestamp,
            session_id=event.session_id,
            hash_signature=hash_signature
        )
    
    def _serialize_details(self, details: Dict[str, Any]) -> Optional[str]:
        """Serializa los detalles del evento como JSON"""
        return json.dumps(details, ensure_ascii=False) if details else None
    
    def _generate_hash_signature(self, event: AuditEvent) -> str:
        """Genera hash de integridad para el evento"""
        hash_data = f"{event.event_type.value}{event.timestamp.isoformat()}{event.message}"
        return hashlib.sha256(hash_data.encode()).hexdigest()
    
    def _log_to_external_system(self, event: AuditEvent):
        """Envía evento a sistema de monitoreo externo (SIEM, etc.)"""
        # Aquí se podría integrar con sistemas como:
        # - Splunk
        # - ELK Stack
        # - Azure Sentinel
        # - AWS CloudWatch
        # Por ahora, solo registramos eventos críticos
        
        if event.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.logger.critical(
                f"CRITICAL SECURITY EVENT: {event.event_type.value} - {event.message}"
            )
    
    def _get_log_level(self, risk_level: RiskLevel) -> int:
        """Mapea nivel de riesgo a nivel de log"""
        mapping = {
            RiskLevel.LOW: logging.INFO,
            RiskLevel.MEDIUM: logging.WARNING,
            RiskLevel.HIGH: logging.ERROR,
            RiskLevel.CRITICAL: logging.CRITICAL
        }
        return mapping.get(risk_level, logging.INFO)
    
    def get_recent_events(
        self, 
        db: Session,
        hours: int = 24,
        event_types: List[EventType] = None,
        risk_levels: List[RiskLevel] = None,
        user_id: int = None,
        ip_address: str = None
    ) -> List[SecurityAuditLog]:
        """
        Obtiene eventos recientes de auditoría
        
        Args:
            db: Sesión de base de datos
            hours: Horas hacia atrás a buscar
            event_types: Tipos de eventos a filtrar
            risk_levels: Niveles de riesgo a filtrar
            user_id: ID de usuario específico
            ip_address: IP específica
            
        Returns:
            Lista de eventos de auditoría
        """
        query = db.query(SecurityAuditLog)
        
        # Filtro por tiempo
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(SecurityAuditLog.timestamp >= since)
        
        # Filtros opcionales
        if event_types:
            event_values = [et.value for et in event_types]
            query = query.filter(SecurityAuditLog.event_type.in_(event_values))
        
        if risk_levels:
            risk_values = [rl.value for rl in risk_levels]
            query = query.filter(SecurityAuditLog.risk_level.in_(risk_values))
        
        if user_id:
            query = query.filter(SecurityAuditLog.user_id == user_id)
        
        if ip_address:
            query = query.filter(SecurityAuditLog.ip_address == ip_address)
        
        return query.order_by(SecurityAuditLog.timestamp.desc()).limit(1000).all()
    
    def get_security_summary(self, db: Session, hours: int = 24) -> Dict[str, Any]:
        """
        Obtiene resumen de seguridad
        
        Args:
            db: Sesión de base de datos
            hours: Horas hacia atrás a analizar
            
        Returns:
            Resumen de eventos de seguridad
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Contar eventos por tipo
        from sqlalchemy import func
        
        event_counts = db.query(
            SecurityAuditLog.event_type,
            func.count(SecurityAuditLog.id).label('count')
        ).filter(
            SecurityAuditLog.timestamp >= since
        ).group_by(SecurityAuditLog.event_type).all()
        
        # Contar eventos por nivel de riesgo
        risk_counts = db.query(
            SecurityAuditLog.risk_level,
            func.count(SecurityAuditLog.id).label('count')
        ).filter(
            SecurityAuditLog.timestamp >= since
        ).group_by(SecurityAuditLog.risk_level).all()
        
        # IPs más activas
        top_ips = db.query(
            SecurityAuditLog.ip_address,
            func.count(SecurityAuditLog.id).label('count')
        ).filter(
            SecurityAuditLog.timestamp >= since,
            SecurityAuditLog.ip_address.isnot(None)
        ).group_by(SecurityAuditLog.ip_address).order_by(
            func.count(SecurityAuditLog.id).desc()
        ).limit(10).all()
        
        # Eventos fallidos
        failed_events = db.query(func.count(SecurityAuditLog.id)).filter(
            SecurityAuditLog.timestamp >= since,
            SecurityAuditLog.success == False
        ).scalar()
        
        return {
            'period_hours': hours,
            'total_events': sum(count for _, count in event_counts),
            'events_by_type': {event_type: count for event_type, count in event_counts},
            'events_by_risk': {risk_level: count for risk_level, count in risk_counts},
            'top_ips': [{'ip': ip, 'count': count} for ip, count in top_ips],
            'failed_events': failed_events or 0,
            'critical_events': dict(risk_counts).get('critical', 0),
            'high_risk_events': dict(risk_counts).get('high', 0)
        }

# Instancia global del auditor
security_auditor = SecurityAuditor()

# Funciones de conveniencia para logging rápido
def log_login_success(user_id: int, username: str, ip_address: str, session_id: str, db: Session = None):
    """Registra login exitoso"""
    event = AuditEvent(
        event_type=EventType.LOGIN_SUCCESS,
        risk_level=RiskLevel.LOW,
        user_id=user_id,
        username=username,
        ip_address=ip_address,
        session_id=session_id,
        message=f"Usuario {username} inició sesión exitosamente"
    )
    security_auditor.log_event(event, db)

def log_login_failed(username: str, ip_address: str, reason: str, db: Session = None):
    """Registra intento de login fallido"""
    event = AuditEvent(
        event_type=EventType.LOGIN_FAILED,
        risk_level=RiskLevel.MEDIUM,
        username=username,
        ip_address=ip_address,
        success=False,
        message=f"Intento de login fallido para {username}: {reason}"
    )
    security_auditor.log_event(event, db)

def log_suspicious_activity(ip_address: str, activity_type: str, details: Dict[str, Any], db: Session = None):
    """Registra actividad sospechosa"""
    event = AuditEvent(
        event_type=EventType.SUSPICIOUS_ACTIVITY,
        risk_level=RiskLevel.HIGH,
        ip_address=ip_address,
        message=f"Actividad sospechosa detectada: {activity_type}",
        details=details
    )
    security_auditor.log_event(event, db)

def log_attack_detected(ip_address: str, attack_type: str, endpoint: str, details: Dict[str, Any], db: Session = None):
    """Registra ataque detectado"""
    event = AuditEvent(
        event_type=EventType.ATTACK_DETECTED,
        risk_level=RiskLevel.CRITICAL,
        ip_address=ip_address,
        endpoint=endpoint,
        message=f"Ataque detectado: {attack_type}",
        details=details,
        success=False
    )
    security_auditor.log_event(event, db)

def log_data_access(user_id: int, username: str, resource: str, action: str, db: Session = None):
    """Registra acceso a datos sensibles"""
    event = AuditEvent(
        event_type=EventType.DATA_ACCESSED,
        risk_level=RiskLevel.LOW,
        user_id=user_id,
        username=username,
        message=f"Usuario {username} accedió a {resource}",
        details={'resource': resource, 'action': action}
    )
    security_auditor.log_event(event, db) 