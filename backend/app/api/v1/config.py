from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from app.core.auth import get_current_user, require_admin_access
from app.services.config_service import (
    get_config_service, ConfigType, ConfigScope, ConfigCategory, ConfigDefinition
)
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class ConfigValueRequest(BaseModel):
    """Configuration value request model"""
    key: str
    value: Any
    scope: ConfigScope = ConfigScope.GLOBAL
    tenant_id: Optional[int] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    environment: Optional[str] = None
    change_reason: Optional[str] = None

class ConfigValueResponse(BaseModel):
    """Configuration value response model"""
    key: str
    value: Any
    config_type: str
    category: str
    scope: str
    encrypted: bool
    description: Optional[str] = None
    last_updated: Optional[str] = None
    updated_by: Optional[int] = None

class ConfigDefinitionResponse(BaseModel):
    """Configuration definition response model"""
    key: str
    name: str
    description: str
    config_type: str
    category: str
    scope: str
    default_value: Any
    required: bool
    encrypted: bool
    validation_pattern: Optional[str]
    options: Optional[List[Any]]
    min_value: Optional[Union[int, float]]
    max_value: Optional[Union[int, float]]
    depends_on: Optional[List[str]]
    tags: List[str]
    ui_component: str
    ui_order: int
    readonly: bool
    restart_required: bool

class ConfigHistoryResponse(BaseModel):
    """Configuration history response model"""
    id: int
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    change_type: str
    changed_by: Optional[int]
    change_reason: Optional[str]
    changed_at: str

class ConfigValidationResponse(BaseModel):
    """Configuration validation response model"""
    valid: bool
    errors: Dict[str, List[str]]
    warnings: List[str] = []

class ConfigExportRequest(BaseModel):
    """Configuration export request model"""
    format: str = Field(default="json", pattern="^(json|yaml)$")
    include_sensitive: bool = False
    scope: ConfigScope = ConfigScope.GLOBAL
    tenant_id: Optional[int] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    environment: Optional[str] = None
    categories: Optional[List[str]] = None

class ConfigImportRequest(BaseModel):
    """Configuration import request model"""
    data: str
    format: str = Field(default="json", pattern="^(json|yaml)$")
    scope: ConfigScope = ConfigScope.GLOBAL
    tenant_id: Optional[int] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    environment: Optional[str] = None
    overwrite_existing: bool = True

class ConfigImportResponse(BaseModel):
    """Configuration import response model"""
    success: bool
    imported_count: int
    failed_count: int
    results: Dict[str, bool]
    errors: List[str] = []

class ConfigStatsResponse(BaseModel):
    """Configuration statistics response model"""
    total_configs: int
    configs_by_category: Dict[str, int]
    configs_by_scope: Dict[str, int]
    encrypted_configs: int
    required_configs: int
    configs_with_defaults: int
    recent_changes_24h: int

# API Routes
@router.get("/config/{key}")
async def get_config_value(
    key: str,
    scope: ConfigScope = Query(ConfigScope.GLOBAL),
    tenant_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    session_id: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get a configuration value"""
    try:
        # For user scope, use current user's ID if not admin
        if scope == ConfigScope.USER and not current_user.is_admin:
            user_id = current_user.id
        
        value = get_config_service().get_config(
            key, scope, tenant_id, user_id, session_id, environment
        )
        
        if value is None:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        # Get definition for metadata
        definition = get_config_service().definitions.get(key)
        
        return {
            "key": key,
            "value": value,
            "config_type": definition.config_type.value if definition else "string",
            "category": definition.category.value if definition else "custom",
            "scope": scope.value,
            "encrypted": definition.encrypted if definition else False,
            "description": definition.description if definition else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get config {key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get configuration")

@router.post("/config")
async def set_config_value(
    config_request: ConfigValueRequest,
    current_user: User = Depends(get_current_user)
):
    """Set a configuration value"""
    try:
        # Check permissions
        if config_request.scope in [ConfigScope.GLOBAL, ConfigScope.TENANT] and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required for global/tenant configurations")
        
        # For user scope, use current user's ID if not admin
        if config_request.scope == ConfigScope.USER and not current_user.is_admin:
            config_request.user_id = current_user.id
        
        # Check if config is readonly
        definition = get_config_service().definitions.get(config_request.key)
        if definition and definition.readonly and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Configuration is read-only")
        
        success = get_config_service().set_config(
            key=config_request.key,
            value=config_request.value,
            scope=config_request.scope,
            tenant_id=config_request.tenant_id,
            user_id=config_request.user_id,
            session_id=config_request.session_id,
            environment=config_request.environment,
            changed_by=current_user.id,
            change_reason=config_request.change_reason
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to set configuration")
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "restart_required": definition.restart_required if definition else False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set config {config_request.key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to set configuration")

@router.delete("/config/{key}")
async def delete_config_value(
    key: str,
    scope: ConfigScope = Query(ConfigScope.GLOBAL),
    tenant_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    session_id: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    delete_reason: Optional[str] = Query(None),
    current_user: User = Depends(require_admin_access)
):
    """Delete a configuration value"""
    try:
        success = get_config_service().delete_config(
            key=key,
            scope=scope,
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            environment=environment,
            deleted_by=current_user.id,
            delete_reason=delete_reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        return {"success": True, "message": "Configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete config {key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete configuration")

@router.get("/configs", response_model=Dict[str, Any])
async def get_all_configs(
    scope: ConfigScope = Query(ConfigScope.GLOBAL),
    tenant_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    session_id: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    include_sensitive: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Get all configurations"""
    try:
        # Check permissions for sensitive data
        if include_sensitive and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required for sensitive configurations")
        
        # For user scope, use current user's ID if not admin
        if scope == ConfigScope.USER and not current_user.is_admin:
            user_id = current_user.id
        
        if category:
            try:
                category_enum = ConfigCategory(category)
                configs = get_config_service().get_category_configs(
                    category_enum, scope, tenant_id, user_id, session_id, environment
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid category")
        else:
            configs = get_config_service().get_all_configs(
                scope, tenant_id, user_id, session_id, environment, include_sensitive
            )
        
        return configs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get configurations")

@router.get("/definitions", response_model=List[ConfigDefinitionResponse])
async def get_config_definitions(
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get configuration definitions"""
    try:
        category_filter = None
        if category:
            try:
                category_filter = ConfigCategory(category)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid category")
        
        definitions = get_config_service().get_config_definitions(category_filter)
        
        return [
            ConfigDefinitionResponse(
                key=d.key,
                name=d.name,
                description=d.description,
                config_type=d.config_type.value,
                category=d.category.value,
                scope=d.scope.value,
                default_value=d.default_value,
                required=d.required,
                encrypted=d.encrypted,
                validation_pattern=d.validation_pattern,
                options=d.options,
                min_value=d.min_value,
                max_value=d.max_value,
                depends_on=d.depends_on,
                tags=d.tags,
                ui_component=d.ui_component,
                ui_order=d.ui_order,
                readonly=d.readonly,
                restart_required=d.restart_required
            )
            for d in definitions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get config definitions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get configuration definitions")

@router.get("/history/{key}", response_model=List[ConfigHistoryResponse])
async def get_config_history(
    key: str,
    limit: int = Query(50, ge=1, le=1000),
    current_user: User = Depends(require_admin_access)
):
    """Get configuration change history"""
    try:
        history = get_config_service().get_config_history(key, limit)
        
        return [
            ConfigHistoryResponse(**h)
            for h in history
        ]
        
    except Exception as e:
        logger.error(f"Failed to get config history for {key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get configuration history")

@router.post("/validate", response_model=ConfigValidationResponse)
async def validate_configs(
    current_user: User = Depends(require_admin_access)
):
    """Validate all configurations"""
    try:
        errors = get_config_service().validate_all_configs()
        
        return ConfigValidationResponse(
            valid=len(errors) == 0,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Failed to validate configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate configurations")

@router.post("/export")
async def export_configs(
    export_request: ConfigExportRequest,
    current_user: User = Depends(require_admin_access)
):
    """Export configurations"""
    try:
        # Check permissions for sensitive data
        if export_request.include_sensitive and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required for sensitive configurations")
        
        exported_data = get_config_service().export_configs(
            format=export_request.format,
            include_sensitive=export_request.include_sensitive,
            scope=export_request.scope,
            tenant_id=export_request.tenant_id,
            user_id=export_request.user_id,
            session_id=export_request.session_id,
            environment=export_request.environment
        )
        
        return {
            "success": True,
            "format": export_request.format,
            "data": exported_data,
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to export configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to export configurations")

@router.post("/import", response_model=ConfigImportResponse)
async def import_configs(
    import_request: ConfigImportRequest,
    current_user: User = Depends(require_admin_access)
):
    """Import configurations"""
    try:
        results = get_config_service().import_configs(
            data=import_request.data,
            format=import_request.format,
            scope=import_request.scope,
            tenant_id=import_request.tenant_id,
            user_id=import_request.user_id,
            session_id=import_request.session_id,
            environment=import_request.environment,
            changed_by=current_user.id
        )
        
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        return ConfigImportResponse(
            success=failed == 0,
            imported_count=successful,
            failed_count=failed,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Failed to import configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to import configurations")

@router.get("/statistics", response_model=ConfigStatsResponse)
async def get_config_statistics(
    current_user: User = Depends(require_admin_access)
):
    """Get configuration statistics"""
    try:
        definitions = get_config_service().get_config_definitions()
        
        # Count by category
        category_counts = {}
        for definition in definitions:
            category = definition.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Count by scope
        scope_counts = {}
        for definition in definitions:
            scope = definition.scope.value
            scope_counts[scope] = scope_counts.get(scope, 0) + 1
        
        # Count special types
        encrypted_count = sum(1 for d in definitions if d.encrypted)
        required_count = sum(1 for d in definitions if d.required)
        default_count = sum(1 for d in definitions if d.default_value is not None)
        
        return ConfigStatsResponse(
            total_configs=len(definitions),
            configs_by_category=category_counts,
            configs_by_scope=scope_counts,
            encrypted_configs=encrypted_count,
            required_configs=required_count,
            configs_with_defaults=default_count,
            recent_changes_24h=0  # This would need to be implemented with actual history query
        )
        
    except Exception as e:
        logger.error(f"Failed to get config statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get configuration statistics")

@router.get("/categories")
async def get_config_categories():
    """Get available configuration categories"""
    return {
        "categories": [category.value for category in ConfigCategory],
        "types": [config_type.value for config_type in ConfigType],
        "scopes": [scope.value for scope in ConfigScope]
    }

@router.post("/reset/{key}")
async def reset_config_to_default(
    key: str,
    scope: ConfigScope = Query(ConfigScope.GLOBAL),
    tenant_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    session_id: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    current_user: User = Depends(require_admin_access)
):
    """Reset configuration to default value"""
    try:
        definition = get_config_service().definitions.get(key)
        if not definition:
            raise HTTPException(status_code=404, detail="Configuration definition not found")
        
        if definition.default_value is None:
            raise HTTPException(status_code=400, detail="No default value defined for this configuration")
        
        success = get_config_service().set_config(
            key=key,
            value=definition.default_value,
            scope=scope,
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            environment=environment,
            changed_by=current_user.id,
            change_reason="Reset to default value"
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to reset configuration")
        
        return {
            "success": True,
            "message": "Configuration reset to default value",
            "default_value": definition.default_value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset config {key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset configuration")

@router.get("/health")
async def config_health_check():
    """Check configuration service health"""
    try:
        total_definitions = len(get_config_service().definitions)
        cached_configs = len(get_config_service().cache)
        
        # Validate critical configs
        validation_errors = get_config_service().validate_all_configs()
        critical_errors = sum(1 for errors in validation_errors.values() if errors)
        
        return {
            "status": "healthy" if critical_errors == 0 else "degraded",
            "total_definitions": total_definitions,
            "cached_configs": cached_configs,
            "validation_errors": critical_errors,
            "encryption_enabled": get_config_service().encryption_key is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Config health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")