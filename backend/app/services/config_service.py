from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from ..core.database import Base, get_db
from ..core.config import settings
import yaml
from cryptography.fernet import Fernet
import base64
from jinja2 import Template
import re

logger = logging.getLogger(__name__)

class ConfigType(Enum):
    """Configuration value types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"
    ENCRYPTED = "encrypted"
    FILE_PATH = "file_path"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"

class ConfigScope(Enum):
    """Configuration scope levels"""
    GLOBAL = "global"
    TENANT = "tenant"
    USER = "user"
    SESSION = "session"
    ENVIRONMENT = "environment"

class ConfigCategory(Enum):
    """Configuration categories"""
    SYSTEM = "system"
    DATABASE = "database"
    SECURITY = "security"
    EMAIL = "email"
    SMS = "sms"
    PAYMENT = "payment"
    INTEGRATION = "integration"
    UI = "ui"
    BUSINESS = "business"
    NOTIFICATION = "notification"
    BACKUP = "backup"
    MONITORING = "monitoring"
    CUSTOM = "custom"

@dataclass
class ConfigDefinition:
    """Configuration definition with metadata"""
    key: str
    name: str
    description: str
    config_type: ConfigType
    category: ConfigCategory
    scope: ConfigScope = ConfigScope.GLOBAL
    default_value: Any = None
    required: bool = False
    encrypted: bool = False
    validation_pattern: Optional[str] = None
    validation_function: Optional[str] = None
    options: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    depends_on: Optional[List[str]] = None
    tags: List[str] = field(default_factory=list)
    ui_component: str = "input"
    ui_order: int = 0
    readonly: bool = False
    restart_required: bool = False

class ConfigModel(Base):
    """Configuration database model"""
    __tablename__ = "config_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(200), nullable=False, index=True)
    value = Column(Text, nullable=True)
    config_type = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    scope = Column(String(20), nullable=False, default="global")
    
    # Scope identifiers
    tenant_id = Column(Integer, nullable=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    environment = Column(String(50), nullable=True, index=True)
    
    # Metadata
    encrypted = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Audit fields
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Versioning
    version = Column(Integer, default=1)
    previous_value = Column(Text, nullable=True)

class ConfigHistoryModel(Base):
    """Configuration change history"""
    __tablename__ = "config_history"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, nullable=False, index=True)
    key = Column(String(200), nullable=False, index=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    change_type = Column(String(20), nullable=False)  # create, update, delete
    changed_by = Column(Integer, nullable=True)
    change_reason = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)

class ConfigService:
    """Advanced configuration management service"""
    
    def __init__(self):
        self.definitions: Dict[str, ConfigDefinition] = {}
        self.cache: Dict[str, Any] = {}
        self.encryption_key: Optional[bytes] = None
        self.watchers: Dict[str, List[callable]] = {}
        
        self._load_encryption_key()
        self._load_definitions()
        self._load_cache()
    
    def _load_encryption_key(self):
        """Load or generate encryption key for sensitive configs"""
        try:
            key_file = Path("config_encryption.key")
            if key_file.exists():
                with open(key_file, "rb") as f:
                    self.encryption_key = f.read()
            else:
                self.encryption_key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(self.encryption_key)
                # Secure the key file
                os.chmod(key_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to load encryption key: {e}")
            self.encryption_key = Fernet.generate_key()
    
    def _load_definitions(self):
        """Load configuration definitions"""
        # Load from YAML files
        config_dir = Path("config_definitions")
        if config_dir.exists():
            for yaml_file in config_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        self._parse_definitions(data)
                except Exception as e:
                    logger.error(f"Failed to load config definitions from {yaml_file}: {e}")
        
        # Add default definitions
        self._add_default_definitions()
    
    def _parse_definitions(self, data: Dict[str, Any]):
        """Parse configuration definitions from YAML data"""
        for key, config_data in data.items():
            try:
                definition = ConfigDefinition(
                    key=key,
                    name=config_data.get("name", key),
                    description=config_data.get("description", ""),
                    config_type=ConfigType(config_data.get("type", "string")),
                    category=ConfigCategory(config_data.get("category", "custom")),
                    scope=ConfigScope(config_data.get("scope", "global")),
                    default_value=config_data.get("default"),
                    required=config_data.get("required", False),
                    encrypted=config_data.get("encrypted", False),
                    validation_pattern=config_data.get("validation_pattern"),
                    validation_function=config_data.get("validation_function"),
                    options=config_data.get("options"),
                    min_value=config_data.get("min_value"),
                    max_value=config_data.get("max_value"),
                    depends_on=config_data.get("depends_on"),
                    tags=config_data.get("tags", []),
                    ui_component=config_data.get("ui_component", "input"),
                    ui_order=config_data.get("ui_order", 0),
                    readonly=config_data.get("readonly", False),
                    restart_required=config_data.get("restart_required", False)
                )
                self.definitions[key] = definition
            except Exception as e:
                logger.error(f"Failed to parse config definition for {key}: {e}")
    
    def _add_default_definitions(self):
        """Add default configuration definitions"""
        defaults = [
            # System configurations
            ConfigDefinition(
                key="app_name",
                name="Application Name",
                description="Name of the application",
                config_type=ConfigType.STRING,
                category=ConfigCategory.SYSTEM,
                default_value="Gym Management System",
                required=True
            ),
            ConfigDefinition(
                key="app_version",
                name="Application Version",
                description="Current version of the application",
                config_type=ConfigType.STRING,
                category=ConfigCategory.SYSTEM,
                default_value="1.0.0",
                readonly=True
            ),
            ConfigDefinition(
                key="debug_mode",
                name="Debug Mode",
                description="Enable debug mode for development",
                config_type=ConfigType.BOOLEAN,
                category=ConfigCategory.SYSTEM,
                default_value=False,
                restart_required=True
            ),
            
            # Database configurations
            ConfigDefinition(
                key="db_pool_size",
                name="Database Pool Size",
                description="Maximum number of database connections",
                config_type=ConfigType.INTEGER,
                category=ConfigCategory.DATABASE,
                default_value=10,
                min_value=1,
                max_value=100,
                restart_required=True
            ),
            
            # Security configurations
            ConfigDefinition(
                key="jwt_secret_key",
                name="JWT Secret Key",
                description="Secret key for JWT token signing",
                config_type=ConfigType.STRING,
                category=ConfigCategory.SECURITY,
                encrypted=True,
                required=True
            ),
            ConfigDefinition(
                key="session_timeout",
                name="Session Timeout",
                description="Session timeout in minutes",
                config_type=ConfigType.INTEGER,
                category=ConfigCategory.SECURITY,
                default_value=60,
                min_value=5,
                max_value=1440
            ),
            
            # Email configurations
            ConfigDefinition(
                key="smtp_host",
                name="SMTP Host",
                description="SMTP server hostname",
                config_type=ConfigType.STRING,
                category=ConfigCategory.EMAIL,
                validation_pattern=r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            ),
            ConfigDefinition(
                key="smtp_port",
                name="SMTP Port",
                description="SMTP server port",
                config_type=ConfigType.INTEGER,
                category=ConfigCategory.EMAIL,
                default_value=587,
                options=[25, 465, 587, 2525]
            ),
            ConfigDefinition(
                key="smtp_username",
                name="SMTP Username",
                description="SMTP authentication username",
                config_type=ConfigType.STRING,
                category=ConfigCategory.EMAIL
            ),
            ConfigDefinition(
                key="smtp_password",
                name="SMTP Password",
                description="SMTP authentication password",
                config_type=ConfigType.STRING,
                category=ConfigCategory.EMAIL,
                encrypted=True
            ),
            
            # Business configurations
            ConfigDefinition(
                key="gym_name",
                name="Gym Name",
                description="Name of the gym",
                config_type=ConfigType.STRING,
                category=ConfigCategory.BUSINESS,
                required=True
            ),
            ConfigDefinition(
                key="gym_address",
                name="Gym Address",
                description="Physical address of the gym",
                config_type=ConfigType.STRING,
                category=ConfigCategory.BUSINESS
            ),
            ConfigDefinition(
                key="gym_phone",
                name="Gym Phone",
                description="Contact phone number",
                config_type=ConfigType.PHONE,
                category=ConfigCategory.BUSINESS,
                validation_pattern=r"^\+?[1-9]\d{1,14}$"
            ),
            ConfigDefinition(
                key="gym_email",
                name="Gym Email",
                description="Contact email address",
                config_type=ConfigType.EMAIL,
                category=ConfigCategory.BUSINESS,
                validation_pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            ),
            ConfigDefinition(
                key="currency",
                name="Currency",
                description="Default currency for payments",
                config_type=ConfigType.STRING,
                category=ConfigCategory.BUSINESS,
                default_value="USD",
                options=["USD", "EUR", "GBP", "CAD", "AUD", "MXN"]
            ),
            ConfigDefinition(
                key="timezone",
                name="Timezone",
                description="Default timezone",
                config_type=ConfigType.STRING,
                category=ConfigCategory.SYSTEM,
                default_value="UTC"
            )
        ]
        
        for definition in defaults:
            if definition.key not in self.definitions:
                self.definitions[definition.key] = definition
    
    def _load_cache(self):
        """Load configurations into cache"""
        try:
            db = next(get_db())
            configs = db.query(ConfigModel).all()
            
            for config in configs:
                cache_key = self._build_cache_key(
                    config.key, config.scope, config.tenant_id,
                    config.user_id, config.session_id, config.environment
                )
                
                value = self._deserialize_value(config.value, config.config_type, config.encrypted)
                self.cache[cache_key] = value
                
        except Exception as e:
            logger.error(f"Failed to load configuration cache: {e}")
        finally:
            db.close()
    
    def get_config(self, key: str, scope: ConfigScope = ConfigScope.GLOBAL,
                  tenant_id: Optional[int] = None, user_id: Optional[int] = None,
                  session_id: Optional[str] = None, environment: Optional[str] = None,
                  default: Any = None) -> Any:
        """Get configuration value"""
        # Build cache key
        cache_key = self._build_cache_key(key, scope, tenant_id, user_id, session_id, environment)
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Check definition for default value
        if key in self.definitions:
            definition = self.definitions[key]
            if definition.default_value is not None:
                return definition.default_value
        
        # Return provided default or None
        return default
    
    def set_config(self, key: str, value: Any, scope: ConfigScope = ConfigScope.GLOBAL,
                  tenant_id: Optional[int] = None, user_id: Optional[int] = None,
                  session_id: Optional[str] = None, environment: Optional[str] = None,
                  changed_by: Optional[int] = None, change_reason: Optional[str] = None) -> bool:
        """Set configuration value"""
        try:
            # Validate configuration
            if not self._validate_config(key, value):
                return False
            
            # Get current value for history
            current_value = self.get_config(key, scope, tenant_id, user_id, session_id, environment)
            
            # Determine config type and encryption
            config_type = ConfigType.STRING
            encrypted = False
            
            if key in self.definitions:
                definition = self.definitions[key]
                config_type = definition.config_type
                encrypted = definition.encrypted
            
            # Serialize value
            serialized_value = self._serialize_value(value, config_type, encrypted)
            
            db = next(get_db())
            
            # Check if config exists
            existing_config = db.query(ConfigModel).filter(
                ConfigModel.key == key,
                ConfigModel.scope == scope.value,
                ConfigModel.tenant_id == tenant_id,
                ConfigModel.user_id == user_id,
                ConfigModel.session_id == session_id,
                ConfigModel.environment == environment
            ).first()
            
            if existing_config:
                # Update existing
                existing_config.previous_value = existing_config.value
                existing_config.value = serialized_value
                existing_config.updated_by = changed_by
                existing_config.updated_at = datetime.utcnow()
                existing_config.version += 1
                
                # Log history
                self._log_config_change(
                    db, existing_config.id, key, current_value, value,
                    "update", changed_by, change_reason
                )
            else:
                # Create new
                new_config = ConfigModel(
                    key=key,
                    value=serialized_value,
                    config_type=config_type.value,
                    category=self.definitions.get(key, ConfigDefinition(
                        key=key, name=key, description="", config_type=config_type,
                        category=ConfigCategory.CUSTOM
                    )).category.value,
                    scope=scope.value,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    session_id=session_id,
                    environment=environment,
                    encrypted=encrypted,
                    created_by=changed_by,
                    updated_by=changed_by
                )
                
                db.add(new_config)
                db.flush()  # Get the ID
                
                # Log history
                self._log_config_change(
                    db, new_config.id, key, None, value,
                    "create", changed_by, change_reason
                )
            
            db.commit()
            
            # Update cache
            cache_key = self._build_cache_key(key, scope, tenant_id, user_id, session_id, environment)
            self.cache[cache_key] = value
            
            # Notify watchers
            self._notify_watchers(key, current_value, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set configuration {key}: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def delete_config(self, key: str, scope: ConfigScope = ConfigScope.GLOBAL,
                     tenant_id: Optional[int] = None, user_id: Optional[int] = None,
                     session_id: Optional[str] = None, environment: Optional[str] = None,
                     deleted_by: Optional[int] = None, delete_reason: Optional[str] = None) -> bool:
        """Delete configuration"""
        try:
            db = next(get_db())
            
            config = db.query(ConfigModel).filter(
                ConfigModel.key == key,
                ConfigModel.scope == scope.value,
                ConfigModel.tenant_id == tenant_id,
                ConfigModel.user_id == user_id,
                ConfigModel.session_id == session_id,
                ConfigModel.environment == environment
            ).first()
            
            if config:
                current_value = self._deserialize_value(config.value, config.config_type, config.encrypted)
                
                # Log history
                self._log_config_change(
                    db, config.id, key, current_value, None,
                    "delete", deleted_by, delete_reason
                )
                
                db.delete(config)
                db.commit()
                
                # Remove from cache
                cache_key = self._build_cache_key(key, scope, tenant_id, user_id, session_id, environment)
                self.cache.pop(cache_key, None)
                
                # Notify watchers
                self._notify_watchers(key, current_value, None)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete configuration {key}: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_category_configs(self, category: Union[str, ConfigCategory],
                           scope: ConfigScope = ConfigScope.GLOBAL,
                           tenant_id: Optional[int] = None,
                           user_id: Optional[int] = None,
                           session_id: Optional[str] = None,
                           environment: Optional[str] = None) -> Dict[str, Any]:
        """Get all configurations for a category"""
        if isinstance(category, str):
            category = ConfigCategory(category)
        
        result = {}
        
        # Get from definitions
        for key, definition in self.definitions.items():
            if definition.category == category:
                value = self.get_config(key, scope, tenant_id, user_id, session_id, environment)
                if value is not None:
                    result[key] = value
        
        return result
    
    def get_all_configs(self, scope: ConfigScope = ConfigScope.GLOBAL,
                       tenant_id: Optional[int] = None,
                       user_id: Optional[int] = None,
                       session_id: Optional[str] = None,
                       environment: Optional[str] = None,
                       include_sensitive: bool = False) -> Dict[str, Any]:
        """Get all configurations"""
        result = {}
        
        for key, definition in self.definitions.items():
            if not include_sensitive and definition.encrypted:
                continue
                
            value = self.get_config(key, scope, tenant_id, user_id, session_id, environment)
            if value is not None:
                result[key] = value
        
        return result
    
    def get_config_definitions(self, category: Optional[ConfigCategory] = None) -> List[ConfigDefinition]:
        """Get configuration definitions"""
        if category:
            return [def_ for def_ in self.definitions.values() if def_.category == category]
        return list(self.definitions.values())
    
    def watch_config(self, key: str, callback: callable):
        """Watch for configuration changes"""
        if key not in self.watchers:
            self.watchers[key] = []
        self.watchers[key].append(callback)
    
    def unwatch_config(self, key: str, callback: callable):
        """Stop watching configuration changes"""
        if key in self.watchers and callback in self.watchers[key]:
            self.watchers[key].remove(callback)
    
    def export_configs(self, format: str = "json", include_sensitive: bool = False,
                      scope: ConfigScope = ConfigScope.GLOBAL,
                      tenant_id: Optional[int] = None,
                      user_id: Optional[int] = None,
                      session_id: Optional[str] = None,
                      environment: Optional[str] = None) -> str:
        """Export configurations to JSON or YAML"""
        configs = self.get_all_configs(scope, tenant_id, user_id, session_id, environment, include_sensitive)
        
        if format.lower() == "yaml":
            return yaml.dump(configs, default_flow_style=False)
        else:
            return json.dumps(configs, indent=2, default=str)
    
    def import_configs(self, data: str, format: str = "json",
                      scope: ConfigScope = ConfigScope.GLOBAL,
                      tenant_id: Optional[int] = None,
                      user_id: Optional[int] = None,
                      session_id: Optional[str] = None,
                      environment: Optional[str] = None,
                      changed_by: Optional[int] = None) -> Dict[str, bool]:
        """Import configurations from JSON or YAML"""
        try:
            if format.lower() == "yaml":
                configs = yaml.safe_load(data)
            else:
                configs = json.loads(data)
            
            results = {}
            for key, value in configs.items():
                success = self.set_config(
                    key, value, scope, tenant_id, user_id, session_id,
                    environment, changed_by, "Imported configuration"
                )
                results[key] = success
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to import configurations: {e}")
            return {}
    
    def validate_all_configs(self) -> Dict[str, List[str]]:
        """Validate all configurations"""
        errors = {}
        
        for key, definition in self.definitions.items():
            value = self.get_config(key)
            validation_errors = self._validate_config_detailed(key, value)
            if validation_errors:
                errors[key] = validation_errors
        
        return errors
    
    def get_config_history(self, key: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        try:
            db = next(get_db())
            
            history = db.query(ConfigHistoryModel).filter(
                ConfigHistoryModel.key == key
            ).order_by(ConfigHistoryModel.changed_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": h.id,
                    "key": h.key,
                    "old_value": h.old_value,
                    "new_value": h.new_value,
                    "change_type": h.change_type,
                    "changed_by": h.changed_by,
                    "change_reason": h.change_reason,
                    "changed_at": h.changed_at.isoformat()
                }
                for h in history
            ]
            
        except Exception as e:
            logger.error(f"Failed to get config history: {e}")
            return []
        finally:
            db.close()
    
    def _build_cache_key(self, key: str, scope: ConfigScope,
                        tenant_id: Optional[int] = None,
                        user_id: Optional[int] = None,
                        session_id: Optional[str] = None,
                        environment: Optional[str] = None) -> str:
        """Build cache key for configuration"""
        parts = [key, scope.value]
        
        if tenant_id is not None:
            parts.append(f"tenant:{tenant_id}")
        if user_id is not None:
            parts.append(f"user:{user_id}")
        if session_id is not None:
            parts.append(f"session:{session_id}")
        if environment is not None:
            parts.append(f"env:{environment}")
        
        return ":".join(parts)
    
    def _serialize_value(self, value: Any, config_type: ConfigType, encrypted: bool) -> str:
        """Serialize configuration value"""
        if value is None:
            return ""
        
        # Convert to string based on type
        if config_type == ConfigType.JSON or config_type == ConfigType.LIST:
            serialized = json.dumps(value)
        elif config_type == ConfigType.BOOLEAN:
            serialized = str(bool(value)).lower()
        else:
            serialized = str(value)
        
        # Encrypt if needed
        if encrypted and self.encryption_key:
            fernet = Fernet(self.encryption_key)
            encrypted_value = fernet.encrypt(serialized.encode())
            return base64.b64encode(encrypted_value).decode()
        
        return serialized
    
    def _deserialize_value(self, value: str, config_type: str, encrypted: bool) -> Any:
        """Deserialize configuration value"""
        if not value:
            return None
        
        # Decrypt if needed
        if encrypted and self.encryption_key:
            try:
                fernet = Fernet(self.encryption_key)
                encrypted_value = base64.b64decode(value.encode())
                value = fernet.decrypt(encrypted_value).decode()
            except Exception as e:
                logger.error(f"Failed to decrypt config value: {e}")
                return None
        
        # Convert from string based on type
        try:
            if config_type == ConfigType.INTEGER.value:
                return int(value)
            elif config_type == ConfigType.FLOAT.value:
                return float(value)
            elif config_type == ConfigType.BOOLEAN.value:
                return value.lower() in ("true", "1", "yes", "on")
            elif config_type == ConfigType.JSON.value:
                return json.loads(value)
            elif config_type == ConfigType.LIST.value:
                return json.loads(value) if value.startswith('[') else value.split(',')
            else:
                return value
        except Exception as e:
            logger.error(f"Failed to deserialize config value: {e}")
            return value
    
    def _validate_config(self, key: str, value: Any) -> bool:
        """Validate configuration value"""
        errors = self._validate_config_detailed(key, value)
        return len(errors) == 0
    
    def _validate_config_detailed(self, key: str, value: Any) -> List[str]:
        """Validate configuration value with detailed errors"""
        errors = []
        
        if key not in self.definitions:
            return errors  # No validation for undefined configs
        
        definition = self.definitions[key]
        
        # Required check
        if definition.required and (value is None or value == ""):
            errors.append(f"Configuration '{key}' is required")
            return errors
        
        if value is None:
            return errors
        
        # Type validation
        if definition.config_type == ConfigType.INTEGER:
            try:
                int_value = int(value)
                if definition.min_value is not None and int_value < definition.min_value:
                    errors.append(f"Value must be >= {definition.min_value}")
                if definition.max_value is not None and int_value > definition.max_value:
                    errors.append(f"Value must be <= {definition.max_value}")
            except (ValueError, TypeError):
                errors.append("Value must be an integer")
        
        elif definition.config_type == ConfigType.FLOAT:
            try:
                float_value = float(value)
                if definition.min_value is not None and float_value < definition.min_value:
                    errors.append(f"Value must be >= {definition.min_value}")
                if definition.max_value is not None and float_value > definition.max_value:
                    errors.append(f"Value must be <= {definition.max_value}")
            except (ValueError, TypeError):
                errors.append("Value must be a number")
        
        elif definition.config_type == ConfigType.BOOLEAN:
            if not isinstance(value, bool) and str(value).lower() not in ("true", "false", "1", "0", "yes", "no", "on", "off"):
                errors.append("Value must be a boolean")
        
        elif definition.config_type == ConfigType.EMAIL:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, str(value)):
                errors.append("Value must be a valid email address")
        
        elif definition.config_type == ConfigType.URL:
            url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
            if not re.match(url_pattern, str(value)):
                errors.append("Value must be a valid URL")
        
        # Pattern validation
        if definition.validation_pattern and isinstance(value, str):
            if not re.match(definition.validation_pattern, value):
                errors.append(f"Value does not match required pattern: {definition.validation_pattern}")
        
        # Options validation
        if definition.options and value not in definition.options:
            errors.append(f"Value must be one of: {', '.join(map(str, definition.options))}")
        
        # Custom validation function
        if definition.validation_function:
            try:
                # This would need to be implemented based on your validation functions
                pass
            except Exception as e:
                errors.append(f"Custom validation failed: {e}")
        
        return errors
    
    def _notify_watchers(self, key: str, old_value: Any, new_value: Any):
        """Notify configuration watchers"""
        if key in self.watchers:
            for callback in self.watchers[key]:
                try:
                    callback(key, old_value, new_value)
                except Exception as e:
                    logger.error(f"Config watcher callback failed: {e}")
    
    def _log_config_change(self, db: Session, config_id: int, key: str,
                          old_value: Any, new_value: Any, change_type: str,
                          changed_by: Optional[int], change_reason: Optional[str]):
        """Log configuration change to history"""
        try:
            history_entry = ConfigHistoryModel(
                config_id=config_id,
                key=key,
                old_value=json.dumps(old_value) if old_value is not None else None,
                new_value=json.dumps(new_value) if new_value is not None else None,
                change_type=change_type,
                changed_by=changed_by,
                change_reason=change_reason
            )
            
            db.add(history_entry)
            
        except Exception as e:
            logger.error(f"Failed to log config change: {e}")

# Global configuration service instance
config_service = ConfigService()