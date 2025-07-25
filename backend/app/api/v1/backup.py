from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from ...core.auth import get_current_user, require_admin_access
from ...models.user import User
from ...services.backup_service import (
    backup_service, BackupType, BackupStatus, BackupStorage,
    BackupConfig, RestoreStatus
)

router = APIRouter()

# Pydantic Models
class BackupTypeEnum(str, Enum):
    """Backup type enumeration for API"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"
    CONFIG_ONLY = "config_only"

class BackupStatusEnum(str, Enum):
    """Backup status enumeration for API"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class BackupStorageEnum(str, Enum):
    """Backup storage enumeration for API"""
    LOCAL = "local"
    S3 = "s3"
    GOOGLE_CLOUD = "google_cloud"
    AZURE = "azure"
    FTP = "ftp"
    SFTP = "sftp"

class RestoreStatusEnum(str, Enum):
    """Restore status enumeration for API"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CreateBackupRequest(BaseModel):
    """Request model for creating a backup"""
    backup_type: BackupTypeEnum = Field(..., description="Type of backup to create")
    storage_location: BackupStorageEnum = Field(default=BackupStorageEnum.LOCAL, description="Storage location for backup")
    include_tables: List[str] = Field(default=[], description="Tables to include (empty means all)")
    exclude_tables: List[str] = Field(default=[], description="Tables to exclude")
    compression: bool = Field(default=True, description="Enable compression")
    encryption: bool = Field(default=False, description="Enable encryption")
    retention_days: int = Field(default=30, ge=1, le=365, description="Retention period in days")
    max_backups: int = Field(default=10, ge=1, le=100, description="Maximum number of backups to keep")
    notification_emails: List[str] = Field(default=[], description="Email addresses for notifications")
    storage_config: Dict[str, Any] = Field(default={}, description="Storage-specific configuration")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")

class RestoreBackupRequest(BaseModel):
    """Request model for restoring a backup"""
    backup_id: str = Field(..., description="ID of backup to restore")
    restore_tables: List[str] = Field(default=[], description="Tables to restore (empty means all)")
    drop_existing: bool = Field(default=False, description="Drop existing tables before restore")
    restore_data: bool = Field(default=True, description="Restore data")
    restore_schema: bool = Field(default=True, description="Restore schema")
    restore_config: bool = Field(default=False, description="Restore configuration")
    target_database: Optional[str] = Field(None, description="Target database (if different)")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")

class BackupResponse(BaseModel):
    """Response model for backup information"""
    backup_id: str
    backup_type: str
    status: str
    storage_location: str
    storage_path: Optional[str] = None
    size_bytes: Optional[int] = None
    compressed_size_bytes: Optional[int] = None
    table_count: Optional[int] = None
    record_count: Optional[int] = None
    compression_ratio: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    notes: Optional[str] = None

class RestoreResponse(BaseModel):
    """Response model for restore information"""
    restore_id: str
    backup_id: str
    status: str
    restore_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    tables_restored: Optional[int] = None
    records_restored: Optional[int] = None
    error_message: Optional[str] = None
    notes: Optional[str] = None
    restored_by_user_id: Optional[int] = None

class BackupOperationResponse(BaseModel):
    """Response model for backup operations"""
    success: bool
    backup_id: str
    backup_path: Optional[str] = None
    size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    message: str

class RestoreOperationResponse(BaseModel):
    """Response model for restore operations"""
    success: bool
    restore_id: str
    backup_id: str
    tables_restored: Optional[int] = None
    records_restored: Optional[int] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    message: str

class BackupStatisticsResponse(BaseModel):
    """Response model for backup statistics"""
    total_backups: int
    successful_backups: int
    failed_backups: int
    success_rate: float
    total_size_bytes: int
    total_size_mb: float
    average_size_bytes: float
    recent_backups_30_days: int
    backup_type_distribution: Dict[str, int]
    storage_distribution: Dict[str, int]

class BackupConfigResponse(BaseModel):
    """Response model for backup configuration"""
    supported_backup_types: List[str]
    supported_storage_locations: List[str]
    default_retention_days: int
    max_retention_days: int
    default_max_backups: int
    compression_enabled: bool
    encryption_available: bool
    storage_providers: Dict[str, Dict[str, Any]]

# API Endpoints
@router.post("/create", response_model=BackupOperationResponse)
async def create_backup(
    request: CreateBackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin_access)
):
    """Create a new backup"""
    try:
        # Convert request to BackupConfig
        config = BackupConfig(
            backup_type=BackupType(request.backup_type.value),
            storage_location=BackupStorage(request.storage_location.value),
            include_tables=request.include_tables,
            exclude_tables=request.exclude_tables,
            compression=request.compression,
            encryption=request.encryption,
            retention_days=request.retention_days,
            max_backups=request.max_backups,
            notification_emails=request.notification_emails,
            storage_config=request.storage_config
        )
        
        # Create backup in background
        result = await backup_service.create_backup(config, current_user.id)
        
        if result["success"]:
            return BackupOperationResponse(
                success=True,
                backup_id=result["backup_id"],
                backup_path=result.get("backup_path"),
                size_bytes=result.get("size_bytes"),
                duration_seconds=result.get("duration_seconds"),
                message="Backup created successfully"
            )
        else:
            return BackupOperationResponse(
                success=False,
                backup_id=result["backup_id"],
                error=result.get("error"),
                message="Backup creation failed"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )

@router.post("/restore", response_model=RestoreOperationResponse)
async def restore_backup(
    request: RestoreBackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin_access)
):
    """Restore from a backup"""
    try:
        restore_options = {
            "restore_tables": request.restore_tables,
            "drop_existing": request.drop_existing,
            "restore_data": request.restore_data,
            "restore_schema": request.restore_schema,
            "restore_config": request.restore_config,
            "target_database": request.target_database,
            "notes": request.notes
        }
        
        result = await backup_service.restore_backup(
            request.backup_id, restore_options, current_user.id
        )
        
        if result["success"]:
            return RestoreOperationResponse(
                success=True,
                restore_id=result["restore_id"],
                backup_id=result["backup_id"],
                tables_restored=result.get("tables_restored"),
                records_restored=result.get("records_restored"),
                duration_seconds=result.get("duration_seconds"),
                message="Restore completed successfully"
            )
        else:
            return RestoreOperationResponse(
                success=False,
                restore_id=result["restore_id"],
                backup_id=result["backup_id"],
                error=result.get("error"),
                message="Restore failed"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore backup: {str(e)}"
        )

@router.get("/list", response_model=List[BackupResponse])
async def list_backups(
    limit: int = 50,
    backup_type: Optional[BackupTypeEnum] = None,
    status: Optional[BackupStatusEnum] = None,
    current_user: User = Depends(require_admin_access)
):
    """List available backups"""
    try:
        backup_type_filter = BackupType(backup_type.value) if backup_type else None
        status_filter = BackupStatus(status.value) if status else None
        
        backups = await backup_service.list_backups(
            limit=limit,
            backup_type=backup_type_filter,
            status=status_filter
        )
        
        return [
            BackupResponse(
                backup_id=backup["backup_id"],
                backup_type=backup["backup_type"],
                status=backup["status"],
                storage_location=backup["storage_location"],
                size_bytes=backup["size_bytes"],
                table_count=backup["table_count"],
                record_count=backup["record_count"],
                started_at=datetime.fromisoformat(backup["created_at"]),
                completed_at=datetime.fromisoformat(backup["completed_at"]) if backup["completed_at"] else None,
                duration_seconds=backup["duration_seconds"],
                expires_at=datetime.fromisoformat(backup["expires_at"]) if backup["expires_at"] else None
            )
            for backup in backups
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )

@router.get("/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: str,
    current_user: User = Depends(require_admin_access)
):
    """Get specific backup information"""
    try:
        backup_info = await backup_service._get_backup_info(backup_id)
        
        if not backup_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found"
            )
        
        return BackupResponse(
            backup_id=backup_info["backup_id"],
            backup_type=backup_info["backup_type"],
            status="completed",  # Assuming completed if found
            storage_location=backup_info["storage_location"],
            storage_path=backup_info["storage_path"],
            size_bytes=backup_info["size_bytes"],
            started_at=backup_info["created_at"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup: {str(e)}"
        )

@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: str,
    current_user: User = Depends(require_admin_access)
):
    """Delete a backup"""
    try:
        success = await backup_service.delete_backup(backup_id)
        
        if success:
            return {"message": "Backup deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup: {str(e)}"
        )

@router.get("/statistics/overview", response_model=BackupStatisticsResponse)
async def get_backup_statistics(
    current_user: User = Depends(require_admin_access)
):
    """Get backup statistics"""
    try:
        stats = await backup_service.get_backup_statistics()
        
        return BackupStatisticsResponse(
            total_backups=stats.get("total_backups", 0),
            successful_backups=stats.get("successful_backups", 0),
            failed_backups=stats.get("failed_backups", 0),
            success_rate=stats.get("success_rate", 0.0),
            total_size_bytes=stats.get("total_size_bytes", 0),
            total_size_mb=stats.get("total_size_mb", 0.0),
            average_size_bytes=stats.get("average_size_bytes", 0.0),
            recent_backups_30_days=stats.get("recent_backups_30_days", 0),
            backup_type_distribution=stats.get("backup_type_distribution", {}),
            storage_distribution=stats.get("storage_distribution", {})
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup statistics: {str(e)}"
        )

@router.get("/config/info", response_model=BackupConfigResponse)
async def get_backup_config(
    current_user: User = Depends(require_admin_access)
):
    """Get backup service configuration"""
    try:
        return BackupConfigResponse(
            supported_backup_types=[bt.value for bt in BackupType],
            supported_storage_locations=[sl.value for sl in BackupStorage],
            default_retention_days=30,
            max_retention_days=365,
            default_max_backups=10,
            compression_enabled=True,
            encryption_available=True,
            storage_providers={
                "local": {
                    "name": "Local Storage",
                    "description": "Store backups on local filesystem",
                    "available": True
                },
                "s3": {
                    "name": "Amazon S3",
                    "description": "Store backups on Amazon S3",
                    "available": backup_service.s3_client is not None
                },
                "google_cloud": {
                    "name": "Google Cloud Storage",
                    "description": "Store backups on Google Cloud",
                    "available": False
                },
                "azure": {
                    "name": "Azure Blob Storage",
                    "description": "Store backups on Azure",
                    "available": False
                }
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup configuration: {str(e)}"
        )

@router.post("/test")
async def test_backup_service(
    current_user: User = Depends(require_admin_access)
):
    """Test backup service functionality"""
    try:
        # Create a small test backup
        config = BackupConfig(
            backup_type=BackupType.CONFIG_ONLY,
            storage_location=BackupStorage.LOCAL,
            retention_days=1,
            max_backups=1
        )
        
        result = await backup_service.create_backup(config, current_user.id)
        
        return {
            "message": "Backup service test completed",
            "test_result": result,
            "service_status": "operational" if result["success"] else "error"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup service test failed: {str(e)}"
        )

@router.get("/types/available")
async def get_available_backup_types(
    current_user: User = Depends(get_current_user)
):
    """Get available backup types"""
    return {
        "backup_types": [
            {
                "value": bt.value,
                "name": bt.value.replace("_", " ").title(),
                "description": {
                    "full": "Complete database backup including schema and data",
                    "incremental": "Backup of changes since last backup",
                    "differential": "Backup of changes since last full backup",
                    "schema_only": "Database structure without data",
                    "data_only": "Data without database structure",
                    "config_only": "Application configuration only"
                }.get(bt.value, "")
            }
            for bt in BackupType
        ],
        "storage_locations": [
            {
                "value": sl.value,
                "name": sl.value.replace("_", " ").title(),
                "description": {
                    "local": "Store on local filesystem",
                    "s3": "Amazon S3 cloud storage",
                    "google_cloud": "Google Cloud Storage",
                    "azure": "Azure Blob Storage",
                    "ftp": "FTP server",
                    "sftp": "Secure FTP server"
                }.get(sl.value, "")
            }
            for sl in BackupStorage
        ],
        "statuses": [
            {
                "value": bs.value,
                "name": bs.value.replace("_", " ").title(),
                "description": {
                    "pending": "Backup is queued for execution",
                    "running": "Backup is currently in progress",
                    "completed": "Backup completed successfully",
                    "failed": "Backup failed with errors",
                    "cancelled": "Backup was cancelled",
                    "expired": "Backup has expired and been removed"
                }.get(bs.value, "")
            }
            for bs in BackupStatus
        ]
    }

@router.post("/cleanup")
async def cleanup_expired_backups(
    current_user: User = Depends(require_admin_access)
):
    """Manually trigger cleanup of expired backups"""
    try:
        # Create a dummy config for cleanup
        config = BackupConfig(
            backup_type=BackupType.FULL,
            storage_location=BackupStorage.LOCAL,
            retention_days=30,
            max_backups=10
        )
        
        await backup_service._cleanup_old_backups(config)
        
        return {"message": "Backup cleanup completed successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup backups: {str(e)}"
        )