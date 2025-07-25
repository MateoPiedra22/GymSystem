from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import os
import shutil
import zipfile
import tempfile
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy import create_engine, MetaData, Table
from ..core.database import Base, get_db, engine
from ..core.config import settings
from .config_service import get_config_service
import pandas as pd
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BackupType(Enum):
    """Types of backups"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"
    CONFIG_ONLY = "config_only"

class BackupStatus(Enum):
    """Backup operation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class BackupStorage(Enum):
    """Backup storage locations"""
    LOCAL = "local"
    S3 = "s3"
    GOOGLE_CLOUD = "google_cloud"
    AZURE = "azure"
    FTP = "ftp"
    SFTP = "sftp"

class RestoreStatus(Enum):
    """Restore operation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BackupConfig:
    """Backup configuration"""
    backup_type: BackupType
    storage_location: BackupStorage
    include_tables: List[str] = field(default_factory=list)
    exclude_tables: List[str] = field(default_factory=list)
    compression: bool = True
    encryption: bool = False
    retention_days: int = 30
    max_backups: int = 10
    schedule_cron: Optional[str] = None
    notification_emails: List[str] = field(default_factory=list)
    storage_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BackupMetadata:
    """Backup metadata information"""
    backup_id: str
    backup_type: BackupType
    created_at: datetime
    size_bytes: int
    table_count: int
    record_count: int
    checksum: str
    storage_location: BackupStorage
    storage_path: str
    compression_ratio: float
    database_version: str
    application_version: str
    notes: Optional[str] = None

class BackupLogModel(Base):
    """Backup log database model"""
    __tablename__ = "backup_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    backup_id = Column(String(100), unique=True, nullable=False, index=True)
    backup_type = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    storage_location = Column(String(20), nullable=False)
    storage_path = Column(String(500), nullable=False)
    
    # Size and statistics
    size_bytes = Column(Integer, nullable=True)
    compressed_size_bytes = Column(Integer, nullable=True)
    table_count = Column(Integer, nullable=True)
    record_count = Column(Integer, nullable=True)
    compression_ratio = Column(Float, nullable=True)
    
    # Timing information
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Metadata
    checksum = Column(String(64), nullable=True)
    database_version = Column(String(50), nullable=True)
    application_version = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    backup_metadata = Column(JSON, nullable=True)
    
    # Retention
    expires_at = Column(DateTime, nullable=True)
    is_archived = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RestoreLogModel(Base):
    """Restore log database model"""
    __tablename__ = "restore_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    restore_id = Column(String(100), unique=True, nullable=False, index=True)
    backup_id = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    restore_type = Column(String(20), nullable=False)
    
    # Timing information
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Statistics
    tables_restored = Column(Integer, nullable=True)
    records_restored = Column(Integer, nullable=True)
    
    # Metadata
    error_message = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    restore_metadata = Column(JSON, nullable=True)
    
    # User information
    restored_by_user_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BackupService:
    """Comprehensive backup and restore service"""
    
    def __init__(self):
        self.backup_dir = Path(settings.BACKUP_DIR if hasattr(settings, 'BACKUP_DIR') else "./backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.temp_dir = Path(tempfile.gettempdir()) / "gym_backups"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Storage clients
        self.s3_client = None
        self.gcs_client = None
        self.azure_client = None
        
        self._initialize_storage_clients()
    
    def _initialize_storage_clients(self):
        """Initialize cloud storage clients"""
        try:
            # Initialize S3 client if configured
            s3_config = get_config_service().get_category_configs("backup_s3")
            if s3_config.get("enabled"):
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=s3_config.get("access_key_id"),
                    aws_secret_access_key=s3_config.get("secret_access_key"),
                    region_name=s3_config.get("region", "us-east-1")
                )
            
            # TODO: Initialize Google Cloud Storage and Azure clients
            
        except Exception as e:
            logger.warning(f"Failed to initialize storage clients: {e}")
    
    async def create_backup(self, config: BackupConfig, 
                          user_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a backup with specified configuration"""
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Log backup start
            backup_log = await self._create_backup_log(
                backup_id, config, BackupStatus.RUNNING
            )
            
            # Create backup based on type
            if config.backup_type == BackupType.FULL:
                result = await self._create_full_backup(backup_id, config)
            elif config.backup_type == BackupType.SCHEMA_ONLY:
                result = await self._create_schema_backup(backup_id, config)
            elif config.backup_type == BackupType.DATA_ONLY:
                result = await self._create_data_backup(backup_id, config)
            elif config.backup_type == BackupType.CONFIG_ONLY:
                result = await self._create_config_backup(backup_id, config)
            else:
                raise ValueError(f"Unsupported backup type: {config.backup_type}")
            
            # Upload to storage if not local
            if config.storage_location != BackupStorage.LOCAL:
                result = await self._upload_backup(result, config)
            
            # Update backup log with success
            await self._update_backup_log(
                backup_id, BackupStatus.COMPLETED, result
            )
            
            # Clean up old backups
            await self._cleanup_old_backups(config)
            
            return {
                "success": True,
                "backup_id": backup_id,
                "backup_path": result["backup_path"],
                "size_bytes": result["size_bytes"],
                "duration_seconds": result["duration_seconds"]
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            
            # Update backup log with failure
            await self._update_backup_log(
                backup_id, BackupStatus.FAILED, {"error": str(e)}
            )
            
            return {
                "success": False,
                "backup_id": backup_id,
                "error": str(e)
            }
    
    async def restore_backup(self, backup_id: str, 
                           restore_options: Dict[str, Any],
                           user_id: Optional[int] = None) -> Dict[str, Any]:
        """Restore from a backup"""
        restore_id = f"restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Get backup information
            backup_info = await self._get_backup_info(backup_id)
            if not backup_info:
                raise ValueError(f"Backup {backup_id} not found")
            
            # Log restore start
            restore_log = await self._create_restore_log(
                restore_id, backup_id, RestoreStatus.RUNNING, user_id
            )
            
            # Download backup if from remote storage
            local_backup_path = await self._download_backup_if_needed(
                backup_info, restore_options
            )
            
            # Perform restore based on backup type
            if backup_info["backup_type"] == BackupType.FULL.value:
                result = await self._restore_full_backup(
                    local_backup_path, restore_options
                )
            elif backup_info["backup_type"] == BackupType.SCHEMA_ONLY.value:
                result = await self._restore_schema_backup(
                    local_backup_path, restore_options
                )
            elif backup_info["backup_type"] == BackupType.DATA_ONLY.value:
                result = await self._restore_data_backup(
                    local_backup_path, restore_options
                )
            elif backup_info["backup_type"] == BackupType.CONFIG_ONLY.value:
                result = await self._restore_config_backup(
                    local_backup_path, restore_options
                )
            else:
                raise ValueError(f"Unsupported backup type: {backup_info['backup_type']}")
            
            # Update restore log with success
            await self._update_restore_log(
                restore_id, RestoreStatus.COMPLETED, result
            )
            
            return {
                "success": True,
                "restore_id": restore_id,
                "backup_id": backup_id,
                "tables_restored": result["tables_restored"],
                "records_restored": result["records_restored"],
                "duration_seconds": result["duration_seconds"]
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            
            # Update restore log with failure
            await self._update_restore_log(
                restore_id, RestoreStatus.FAILED, {"error": str(e)}
            )
            
            return {
                "success": False,
                "restore_id": restore_id,
                "backup_id": backup_id,
                "error": str(e)
            }
    
    async def list_backups(self, limit: int = 50, 
                         backup_type: Optional[BackupType] = None,
                         status: Optional[BackupStatus] = None) -> List[Dict[str, Any]]:
        """List available backups"""
        try:
            db = next(get_db())
            
            query = db.query(BackupLogModel)
            
            if backup_type:
                query = query.filter(BackupLogModel.backup_type == backup_type.value)
            if status:
                query = query.filter(BackupLogModel.status == status.value)
            
            backups = query.order_by(BackupLogModel.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "backup_id": backup.backup_id,
                    "backup_type": backup.backup_type,
                    "status": backup.status,
                    "storage_location": backup.storage_location,
                    "size_bytes": backup.size_bytes,
                    "table_count": backup.table_count,
                    "record_count": backup.record_count,
                    "created_at": backup.created_at.isoformat(),
                    "completed_at": backup.completed_at.isoformat() if backup.completed_at else None,
                    "duration_seconds": backup.duration_seconds,
                    "expires_at": backup.expires_at.isoformat() if backup.expires_at else None
                }
                for backup in backups
            ]
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
        finally:
            db.close()
    
    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup"""
        try:
            db = next(get_db())
            
            backup = db.query(BackupLogModel).filter(
                BackupLogModel.backup_id == backup_id
            ).first()
            
            if not backup:
                return False
            
            # Delete from storage
            if backup.storage_location == BackupStorage.LOCAL.value:
                backup_path = Path(backup.storage_path)
                if backup_path.exists():
                    backup_path.unlink()
            elif backup.storage_location == BackupStorage.S3.value:
                await self._delete_s3_backup(backup.storage_path)
            # TODO: Add other storage providers
            
            # Delete from database
            db.delete(backup)
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False
        finally:
            db.close()
    
    async def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics"""
        try:
            db = next(get_db())
            
            # Total backups
            total_backups = db.query(BackupLogModel).count()
            
            # Successful backups
            successful_backups = db.query(BackupLogModel).filter(
                BackupLogModel.status == BackupStatus.COMPLETED.value
            ).count()
            
            # Failed backups
            failed_backups = db.query(BackupLogModel).filter(
                BackupLogModel.status == BackupStatus.FAILED.value
            ).count()
            
            # Total storage used
            total_size = db.query(BackupLogModel).filter(
                BackupLogModel.status == BackupStatus.COMPLETED.value
            ).with_entities(BackupLogModel.size_bytes).all()
            
            total_size_bytes = sum(size[0] for size in total_size if size[0])
            
            # Backup types distribution
            type_stats = {}
            for backup_type in BackupType:
                count = db.query(BackupLogModel).filter(
                    BackupLogModel.backup_type == backup_type.value
                ).count()
                if count > 0:
                    type_stats[backup_type.value] = count
            
            # Storage location distribution
            storage_stats = {}
            for storage in BackupStorage:
                count = db.query(BackupLogModel).filter(
                    BackupLogModel.storage_location == storage.value
                ).count()
                if count > 0:
                    storage_stats[storage.value] = count
            
            # Recent backup activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_backups = db.query(BackupLogModel).filter(
                BackupLogModel.created_at >= thirty_days_ago
            ).count()
            
            # Average backup size
            avg_size = total_size_bytes / successful_backups if successful_backups > 0 else 0
            
            # Success rate
            success_rate = (successful_backups / total_backups * 100) if total_backups > 0 else 0
            
            return {
                "total_backups": total_backups,
                "successful_backups": successful_backups,
                "failed_backups": failed_backups,
                "success_rate": round(success_rate, 2),
                "total_size_bytes": total_size_bytes,
                "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
                "average_size_bytes": round(avg_size),
                "recent_backups_30_days": recent_backups,
                "backup_type_distribution": type_stats,
                "storage_distribution": storage_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get backup statistics: {e}")
            return {}
        finally:
            db.close()
    
    async def _create_full_backup(self, backup_id: str, 
                                config: BackupConfig) -> Dict[str, Any]:
        """Create a full database backup"""
        start_time = datetime.utcnow()
        
        # Create backup directory
        backup_path = self.backup_dir / f"{backup_id}.zip"
        temp_backup_dir = self.temp_dir / backup_id
        temp_backup_dir.mkdir(exist_ok=True)
        
        try:
            # Get database metadata
            metadata = MetaData()
            metadata.reflect(bind=engine)
            
            # Export each table
            table_count = 0
            record_count = 0
            
            for table_name, table in metadata.tables.items():
                if config.include_tables and table_name not in config.include_tables:
                    continue
                if table_name in config.exclude_tables:
                    continue
                
                # Export table data to CSV
                df = pd.read_sql_table(table_name, engine)
                csv_path = temp_backup_dir / f"{table_name}.csv"
                df.to_csv(csv_path, index=False)
                
                table_count += 1
                record_count += len(df)
            
            # Export schema
            schema_path = temp_backup_dir / "schema.sql"
            await self._export_schema(schema_path)
            
            # Create metadata file
            metadata_info = {
                "backup_id": backup_id,
                "backup_type": config.backup_type.value,
                "created_at": start_time.isoformat(),
                "table_count": table_count,
                "record_count": record_count,
                "database_version": "postgresql",  # TODO: Get actual version
                "application_version": "1.0.0"  # TODO: Get from settings
            }
            
            metadata_path = temp_backup_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata_info, f, indent=2)
            
            # Create ZIP archive
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_backup_dir.rglob('*'):
                    if file_path.is_file():
                        zipf.write(file_path, file_path.relative_to(temp_backup_dir))
            
            # Calculate file size and duration
            size_bytes = backup_path.stat().st_size
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "backup_path": str(backup_path),
                "size_bytes": size_bytes,
                "table_count": table_count,
                "record_count": record_count,
                "duration_seconds": duration
            }
            
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_backup_dir, ignore_errors=True)
    
    async def _create_schema_backup(self, backup_id: str, 
                                  config: BackupConfig) -> Dict[str, Any]:
        """Create a schema-only backup"""
        start_time = datetime.utcnow()
        
        backup_path = self.backup_dir / f"{backup_id}_schema.sql"
        
        await self._export_schema(backup_path)
        
        size_bytes = backup_path.stat().st_size
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "backup_path": str(backup_path),
            "size_bytes": size_bytes,
            "table_count": 0,
            "record_count": 0,
            "duration_seconds": duration
        }
    
    async def _create_data_backup(self, backup_id: str, 
                                config: BackupConfig) -> Dict[str, Any]:
        """Create a data-only backup"""
        # Similar to full backup but without schema
        # Implementation would be similar to _create_full_backup
        # but skip schema export
        pass
    
    async def _create_config_backup(self, backup_id: str, 
                                  config: BackupConfig) -> Dict[str, Any]:
        """Create a configuration-only backup"""
        start_time = datetime.utcnow()
        
        backup_path = self.backup_dir / f"{backup_id}_config.json"
        
        # Export all configurations
        all_configs = get_config_service().export_all_configs()
        
        with open(backup_path, 'w') as f:
            json.dump(all_configs, f, indent=2)
        
        size_bytes = backup_path.stat().st_size
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "backup_path": str(backup_path),
            "size_bytes": size_bytes,
            "table_count": 0,
            "record_count": 0,
            "duration_seconds": duration
        }
    
    async def _export_schema(self, output_path: Path):
        """Export database schema to SQL file"""
        # This is a simplified implementation
        # In production, you'd use pg_dump or similar tools
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        with open(output_path, 'w') as f:
            f.write("-- Database Schema Export\n")
            f.write(f"-- Generated at: {datetime.utcnow().isoformat()}\n\n")
            
            for table_name, table in metadata.tables.items():
                f.write(f"-- Table: {table_name}\n")
                # TODO: Generate actual CREATE TABLE statements
                f.write(f"-- Columns: {', '.join([col.name for col in table.columns])}\n\n")
    
    async def _upload_backup(self, backup_result: Dict[str, Any], 
                           config: BackupConfig) -> Dict[str, Any]:
        """Upload backup to configured storage"""
        if config.storage_location == BackupStorage.S3:
            return await self._upload_to_s3(backup_result, config)
        # TODO: Add other storage providers
        
        return backup_result
    
    async def _upload_to_s3(self, backup_result: Dict[str, Any], 
                          config: BackupConfig) -> Dict[str, Any]:
        """Upload backup to S3"""
        if not self.s3_client:
            raise ValueError("S3 client not configured")
        
        backup_path = Path(backup_result["backup_path"])
        s3_key = f"backups/{backup_path.name}"
        bucket_name = config.storage_config.get("bucket_name")
        
        if not bucket_name:
            raise ValueError("S3 bucket name not configured")
        
        try:
            self.s3_client.upload_file(
                str(backup_path), bucket_name, s3_key
            )
            
            # Update result with S3 path
            backup_result["storage_path"] = f"s3://{bucket_name}/{s3_key}"
            
            # Optionally delete local file
            if config.storage_config.get("delete_local", False):
                backup_path.unlink()
            
            return backup_result
            
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
    
    async def _create_backup_log(self, backup_id: str, config: BackupConfig, 
                               status: BackupStatus) -> BackupLogModel:
        """Create backup log entry"""
        try:
            db = next(get_db())
            
            backup_log = BackupLogModel(
                backup_id=backup_id,
                backup_type=config.backup_type.value,
                status=status.value,
                storage_location=config.storage_location.value,
                storage_path="",  # Will be updated later
                started_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=config.retention_days)
            )
            
            db.add(backup_log)
            db.commit()
            
            return backup_log
            
        except Exception as e:
            logger.error(f"Failed to create backup log: {e}")
            raise
        finally:
            db.close()
    
    async def _update_backup_log(self, backup_id: str, status: BackupStatus, 
                               result: Dict[str, Any]):
        """Update backup log with results"""
        try:
            db = next(get_db())
            
            backup_log = db.query(BackupLogModel).filter(
                BackupLogModel.backup_id == backup_id
            ).first()
            
            if backup_log:
                backup_log.status = status.value
                backup_log.completed_at = datetime.utcnow()
                backup_log.duration_seconds = int(
                    (backup_log.completed_at - backup_log.started_at).total_seconds()
                )
                
                if status == BackupStatus.COMPLETED:
                    backup_log.storage_path = result.get("backup_path", "")
                    backup_log.size_bytes = result.get("size_bytes", 0)
                    backup_log.table_count = result.get("table_count", 0)
                    backup_log.record_count = result.get("record_count", 0)
                elif status == BackupStatus.FAILED:
                    backup_log.error_message = result.get("error", "")
                
                db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update backup log: {e}")
        finally:
            db.close()
    
    async def _cleanup_old_backups(self, config: BackupConfig):
        """Clean up old backups based on retention policy"""
        try:
            db = next(get_db())
            
            # Find expired backups
            expired_backups = db.query(BackupLogModel).filter(
                BackupLogModel.expires_at < datetime.utcnow(),
                BackupLogModel.status == BackupStatus.COMPLETED.value
            ).all()
            
            for backup in expired_backups:
                await self.delete_backup(backup.backup_id)
            
            # Limit number of backups
            if config.max_backups > 0:
                excess_backups = db.query(BackupLogModel).filter(
                    BackupLogModel.backup_type == config.backup_type.value,
                    BackupLogModel.status == BackupStatus.COMPLETED.value
                ).order_by(BackupLogModel.created_at.desc()).offset(config.max_backups).all()
                
                for backup in excess_backups:
                    await self.delete_backup(backup.backup_id)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
        finally:
            db.close()
    
    # Additional helper methods for restore operations would go here...
    # _create_restore_log, _update_restore_log, _get_backup_info, etc.
    
    async def _get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Get backup information"""
        try:
            db = next(get_db())
            
            backup = db.query(BackupLogModel).filter(
                BackupLogModel.backup_id == backup_id
            ).first()
            
            if backup:
                return {
                    "backup_id": backup.backup_id,
                    "backup_type": backup.backup_type,
                    "storage_location": backup.storage_location,
                    "storage_path": backup.storage_path,
                    "size_bytes": backup.size_bytes,
                    "created_at": backup.created_at
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get backup info: {e}")
            return None
        finally:
            db.close()

# Global backup service instance
backup_service = BackupService()