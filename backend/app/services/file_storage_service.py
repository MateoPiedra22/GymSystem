from typing import List, Dict, Any, Optional, Union, BinaryIO
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
import aiofiles
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from PIL import Image, ImageOps
import cv2
import numpy as np
from fastapi import UploadFile, HTTPException
import logging
from ..core.config import settings
import json
from urllib.parse import urlparse
import requests
from io import BytesIO
import zipfile
import tempfile
import shutil

logger = logging.getLogger(__name__)

class StorageProvider(Enum):
    LOCAL = "local"
    AWS_S3 = "aws_s3"
    GOOGLE_CLOUD = "google_cloud"
    AZURE_BLOB = "azure_blob"

class FileType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    BACKUP = "backup"
    OTHER = "other"

class ImageFormat(Enum):
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    GIF = "gif"

@dataclass
class FileMetadata:
    """File metadata structure"""
    file_id: str
    original_name: str
    file_type: FileType
    mime_type: str
    size_bytes: int
    checksum: str
    storage_provider: StorageProvider
    storage_path: str
    public_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ImageProcessingOptions:
    """Image processing configuration"""
    resize: Optional[tuple] = None  # (width, height)
    quality: int = 85
    format: ImageFormat = ImageFormat.JPEG
    create_thumbnail: bool = True
    thumbnail_size: tuple = (150, 150)
    optimize: bool = True
    auto_orient: bool = True
    watermark: Optional[str] = None

@dataclass
class UploadResult:
    """Upload operation result"""
    success: bool
    file_metadata: Optional[FileMetadata] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None

class FileStorageService:
    """Advanced file storage and management service"""
    
    def __init__(self):
        self.storage_provider = StorageProvider.LOCAL  # Default to local storage
        self.local_storage_path = Path("uploads")
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {
            FileType.IMAGE: {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'},
            FileType.VIDEO: {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'},
            FileType.DOCUMENT: {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'},
            FileType.AUDIO: {'.mp3', '.wav', '.ogg', '.m4a', '.flac'},
            FileType.BACKUP: {'.zip', '.tar', '.gz', '.bak', '.sql'}
        }
        
        # Initialize storage providers
        self._init_local_storage()
        self._init_cloud_storage()
        
    def _init_local_storage(self):
        """Initialize local storage directories"""
        self.local_storage_path.mkdir(exist_ok=True)
        
        # Create subdirectories for different file types
        for file_type in FileType:
            (self.local_storage_path / file_type.value).mkdir(exist_ok=True)
            (self.local_storage_path / file_type.value / "thumbnails").mkdir(exist_ok=True)
    
    def _init_cloud_storage(self):
        """Initialize cloud storage clients"""
        try:
            # AWS S3
            if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
                )
                self.s3_bucket = getattr(settings, 'S3_BUCKET_NAME', 'gym-system-files')
            else:
                self.s3_client = None
                
        except Exception as e:
            logger.warning(f"Could not initialize cloud storage: {e}")
            self.s3_client = None
    
    async def upload_file(
        self,
        file: UploadFile,
        file_type: FileType = None,
        processing_options: Optional[ImageProcessingOptions] = None,
        custom_path: Optional[str] = None,
        expires_in_days: Optional[int] = None
    ) -> UploadResult:
        """Upload and process a file"""
        start_time = datetime.now()
        
        try:
            # Validate file
            validation_result = await self._validate_file(file, file_type)
            if not validation_result['valid']:
                return UploadResult(
                    success=False,
                    error_message=validation_result['error']
                )
            
            file_type = validation_result['file_type']
            
            # Generate file ID and paths
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix.lower()
            
            # Read file content
            file_content = await file.read()
            file_checksum = hashlib.md5(file_content).hexdigest()
            
            # Determine storage path
            if custom_path:
                storage_path = custom_path
            else:
                storage_path = f"{file_type.value}/{file_id}{file_extension}"
            
            # Process file based on type
            processed_content = file_content
            thumbnail_path = None
            
            if file_type == FileType.IMAGE and processing_options:
                processed_content, thumbnail_path = await self._process_image(
                    file_content, file_id, processing_options
                )
            
            # Store file
            storage_result = await self._store_file(
                processed_content,
                storage_path,
                file.content_type
            )
            
            if not storage_result['success']:
                return UploadResult(
                    success=False,
                    error_message=storage_result['error']
                )
            
            # Store thumbnail if created
            thumbnail_url = None
            if thumbnail_path:
                thumbnail_storage_result = await self._store_thumbnail(
                    thumbnail_path, file_id, file_type
                )
                if thumbnail_storage_result['success']:
                    thumbnail_url = thumbnail_storage_result['url']
            
            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            # Create metadata
            file_metadata = FileMetadata(
                file_id=file_id,
                original_name=file.filename,
                file_type=file_type,
                mime_type=file.content_type,
                size_bytes=len(processed_content),
                checksum=file_checksum,
                storage_provider=self.storage_provider,
                storage_path=storage_path,
                public_url=storage_result['url'],
                thumbnail_url=thumbnail_url,
                created_at=datetime.now(),
                expires_at=expires_at,
                metadata={
                    'original_size': len(file_content),
                    'processed': file_type == FileType.IMAGE and processing_options is not None
                }
            )
            
            # Save metadata to database (would implement with actual DB)
            await self._save_file_metadata(file_metadata)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return UploadResult(
                success=True,
                file_metadata=file_metadata,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return UploadResult(
                success=False,
                error_message=str(e)
            )
    
    async def _validate_file(
        self,
        file: UploadFile,
        file_type: Optional[FileType] = None
    ) -> Dict[str, Any]:
        """Validate uploaded file"""
        # Check file size
        file_content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        if len(file_content) > self.max_file_size:
            return {
                'valid': False,
                'error': f'File size exceeds maximum allowed size of {self.max_file_size / 1024 / 1024:.1f}MB'
            }
        
        # Determine file type from extension
        file_extension = Path(file.filename).suffix.lower()
        
        if not file_type:
            file_type = self._detect_file_type(file_extension, file.content_type)
        
        # Check if extension is allowed
        if file_type not in self.allowed_extensions:
            return {
                'valid': False,
                'error': f'File type {file_type.value} is not supported'
            }
        
        if file_extension not in self.allowed_extensions[file_type]:
            return {
                'valid': False,
                'error': f'File extension {file_extension} is not allowed for {file_type.value} files'
            }
        
        # Additional validation for images
        if file_type == FileType.IMAGE:
            try:
                image = Image.open(BytesIO(file_content))
                image.verify()
            except Exception:
                return {
                    'valid': False,
                    'error': 'Invalid or corrupted image file'
                }
        
        return {
            'valid': True,
            'file_type': file_type
        }
    
    def _detect_file_type(self, extension: str, mime_type: str) -> FileType:
        """Detect file type from extension and MIME type"""
        for file_type, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return file_type
        
        # Fallback to MIME type detection
        if mime_type:
            if mime_type.startswith('image/'):
                return FileType.IMAGE
            elif mime_type.startswith('video/'):
                return FileType.VIDEO
            elif mime_type.startswith('audio/'):
                return FileType.AUDIO
            elif mime_type in ['application/pdf', 'application/msword']:
                return FileType.DOCUMENT
        
        return FileType.OTHER
    
    async def _process_image(
        self,
        image_content: bytes,
        file_id: str,
        options: ImageProcessingOptions
    ) -> tuple[bytes, Optional[str]]:
        """Process image with specified options"""
        try:
            # Open image
            image = Image.open(BytesIO(image_content))
            
            # Auto-orient based on EXIF data
            if options.auto_orient:
                image = ImageOps.exif_transpose(image)
            
            # Resize if specified
            if options.resize:
                image = image.resize(options.resize, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if options.format in [ImageFormat.JPEG] and image.mode in ['RGBA', 'P']:
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Add watermark if specified
            if options.watermark:
                image = await self._add_watermark(image, options.watermark)
            
            # Save processed image
            output = BytesIO()
            save_kwargs = {
                'format': options.format.value.upper(),
                'optimize': options.optimize
            }
            
            if options.format == ImageFormat.JPEG:
                save_kwargs['quality'] = options.quality
            
            image.save(output, **save_kwargs)
            processed_content = output.getvalue()
            
            # Create thumbnail if requested
            thumbnail_path = None
            if options.create_thumbnail:
                thumbnail_path = await self._create_thumbnail(
                    image, file_id, options.thumbnail_size
                )
            
            return processed_content, thumbnail_path
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return image_content, None
    
    async def _add_watermark(self, image: Image.Image, watermark_text: str) -> Image.Image:
        """Add watermark to image"""
        try:
            from PIL import ImageDraw, ImageFont
            
            # Create a copy of the image
            watermarked = image.copy()
            draw = ImageDraw.Draw(watermarked)
            
            # Try to use a font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position (bottom right)
            text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = image.width - text_width - 20
            y = image.height - text_height - 20
            
            # Draw text with semi-transparent background
            draw.rectangle(
                [x - 10, y - 5, x + text_width + 10, y + text_height + 5],
                fill=(0, 0, 0, 128)
            )
            draw.text((x, y), watermark_text, fill=(255, 255, 255, 200), font=font)
            
            return watermarked
            
        except Exception as e:
            logger.error(f"Error adding watermark: {e}")
            return image
    
    async def _create_thumbnail(
        self,
        image: Image.Image,
        file_id: str,
        thumbnail_size: tuple
    ) -> str:
        """Create thumbnail for image"""
        try:
            # Create thumbnail
            thumbnail = image.copy()
            thumbnail.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            thumbnail_path = self.local_storage_path / "images" / "thumbnails" / f"{file_id}_thumb.jpg"
            thumbnail.save(thumbnail_path, 'JPEG', quality=80)
            
            return str(thumbnail_path)
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return None
    
    async def _store_file(
        self,
        file_content: bytes,
        storage_path: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Store file in configured storage provider"""
        if self.storage_provider == StorageProvider.LOCAL:
            return await self._store_file_local(file_content, storage_path)
        elif self.storage_provider == StorageProvider.AWS_S3:
            return await self._store_file_s3(file_content, storage_path, content_type)
        else:
            return {
                'success': False,
                'error': f'Storage provider {self.storage_provider} not implemented'
            }
    
    async def _store_file_local(self, file_content: bytes, storage_path: str) -> Dict[str, Any]:
        """Store file in local filesystem"""
        try:
            full_path = self.local_storage_path / storage_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(file_content)
            
            # Generate public URL (would be actual URL in production)
            public_url = f"/files/{storage_path}"
            
            return {
                'success': True,
                'url': public_url,
                'storage_path': str(full_path)
            }
            
        except Exception as e:
            logger.error(f"Error storing file locally: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _store_file_s3(
        self,
        file_content: bytes,
        storage_path: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Store file in AWS S3"""
        try:
            if not self.s3_client:
                return {
                    'success': False,
                    'error': 'S3 client not configured'
                }
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=storage_path,
                Body=file_content,
                ContentType=content_type,
                ACL='public-read'  # Make file publicly accessible
            )
            
            # Generate public URL
            public_url = f"https://{self.s3_bucket}.s3.amazonaws.com/{storage_path}"
            
            return {
                'success': True,
                'url': public_url,
                'storage_path': storage_path
            }
            
        except Exception as e:
            logger.error(f"Error storing file in S3: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _store_thumbnail(
        self,
        thumbnail_path: str,
        file_id: str,
        file_type: FileType
    ) -> Dict[str, Any]:
        """Store thumbnail file"""
        try:
            # Read thumbnail content
            async with aiofiles.open(thumbnail_path, 'rb') as f:
                thumbnail_content = await f.read()
            
            # Store thumbnail
            thumbnail_storage_path = f"{file_type.value}/thumbnails/{file_id}_thumb.jpg"
            result = await self._store_file(
                thumbnail_content,
                thumbnail_storage_path,
                'image/jpeg'
            )
            
            # Clean up local thumbnail file
            try:
                os.remove(thumbnail_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            logger.error(f"Error storing thumbnail: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _save_file_metadata(self, metadata: FileMetadata):
        """Save file metadata to database"""
        # In a real implementation, this would save to the database
        # For now, we'll save to a JSON file
        try:
            metadata_file = self.local_storage_path / "metadata.json"
            
            # Load existing metadata
            existing_metadata = []
            if metadata_file.exists():
                async with aiofiles.open(metadata_file, 'r') as f:
                    content = await f.read()
                    if content:
                        existing_metadata = json.loads(content)
            
            # Add new metadata
            metadata_dict = {
                'file_id': metadata.file_id,
                'original_name': metadata.original_name,
                'file_type': metadata.file_type.value,
                'mime_type': metadata.mime_type,
                'size_bytes': metadata.size_bytes,
                'checksum': metadata.checksum,
                'storage_provider': metadata.storage_provider.value,
                'storage_path': metadata.storage_path,
                'public_url': metadata.public_url,
                'thumbnail_url': metadata.thumbnail_url,
                'created_at': metadata.created_at.isoformat() if metadata.created_at else None,
                'expires_at': metadata.expires_at.isoformat() if metadata.expires_at else None,
                'metadata': metadata.metadata
            }
            
            existing_metadata.append(metadata_dict)
            
            # Save updated metadata
            async with aiofiles.open(metadata_file, 'w') as f:
                await f.write(json.dumps(existing_metadata, indent=2))
                
        except Exception as e:
            logger.error(f"Error saving file metadata: {e}")
    
    async def get_file_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """Get file metadata by ID"""
        try:
            metadata_file = self.local_storage_path / "metadata.json"
            
            if not metadata_file.exists():
                return None
            
            async with aiofiles.open(metadata_file, 'r') as f:
                content = await f.read()
                if not content:
                    return None
                
                metadata_list = json.loads(content)
                
                for metadata_dict in metadata_list:
                    if metadata_dict['file_id'] == file_id:
                        return FileMetadata(
                            file_id=metadata_dict['file_id'],
                            original_name=metadata_dict['original_name'],
                            file_type=FileType(metadata_dict['file_type']),
                            mime_type=metadata_dict['mime_type'],
                            size_bytes=metadata_dict['size_bytes'],
                            checksum=metadata_dict['checksum'],
                            storage_provider=StorageProvider(metadata_dict['storage_provider']),
                            storage_path=metadata_dict['storage_path'],
                            public_url=metadata_dict['public_url'],
                            thumbnail_url=metadata_dict['thumbnail_url'],
                            created_at=datetime.fromisoformat(metadata_dict['created_at']) if metadata_dict['created_at'] else None,
                            expires_at=datetime.fromisoformat(metadata_dict['expires_at']) if metadata_dict['expires_at'] else None,
                            metadata=metadata_dict['metadata']
                        )
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file and its metadata"""
        try:
            # Get file metadata
            metadata = await self.get_file_metadata(file_id)
            if not metadata:
                return False
            
            # Delete file from storage
            if self.storage_provider == StorageProvider.LOCAL:
                file_path = self.local_storage_path / metadata.storage_path
                if file_path.exists():
                    file_path.unlink()
                
                # Delete thumbnail if exists
                if metadata.thumbnail_url:
                    thumbnail_path = self.local_storage_path / f"{metadata.file_type.value}/thumbnails/{file_id}_thumb.jpg"
                    if thumbnail_path.exists():
                        thumbnail_path.unlink()
            
            elif self.storage_provider == StorageProvider.AWS_S3 and self.s3_client:
                # Delete from S3
                self.s3_client.delete_object(
                    Bucket=self.s3_bucket,
                    Key=metadata.storage_path
                )
                
                # Delete thumbnail from S3
                if metadata.thumbnail_url:
                    thumbnail_key = f"{metadata.file_type.value}/thumbnails/{file_id}_thumb.jpg"
                    self.s3_client.delete_object(
                        Bucket=self.s3_bucket,
                        Key=thumbnail_key
                    )
            
            # Remove metadata
            await self._remove_file_metadata(file_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    async def _remove_file_metadata(self, file_id: str):
        """Remove file metadata from storage"""
        try:
            metadata_file = self.local_storage_path / "metadata.json"
            
            if not metadata_file.exists():
                return
            
            async with aiofiles.open(metadata_file, 'r') as f:
                content = await f.read()
                if not content:
                    return
                
                metadata_list = json.loads(content)
            
            # Remove metadata for the file
            updated_metadata = [m for m in metadata_list if m['file_id'] != file_id]
            
            # Save updated metadata
            async with aiofiles.open(metadata_file, 'w') as f:
                await f.write(json.dumps(updated_metadata, indent=2))
                
        except Exception as e:
            logger.error(f"Error removing file metadata: {e}")
    
    async def create_backup_archive(
        self,
        file_ids: List[str],
        archive_name: str = None
    ) -> Optional[str]:
        """Create a backup archive from multiple files"""
        try:
            if not archive_name:
                archive_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                archive_path = Path(temp_dir) / archive_name
                
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_id in file_ids:
                        metadata = await self.get_file_metadata(file_id)
                        if metadata:
                            # Get file content
                            if self.storage_provider == StorageProvider.LOCAL:
                                file_path = self.local_storage_path / metadata.storage_path
                                if file_path.exists():
                                    zipf.write(file_path, metadata.original_name)
                            
                            # Add metadata to archive
                            metadata_json = json.dumps(metadata.__dict__, default=str, indent=2)
                            zipf.writestr(f"{metadata.original_name}.metadata.json", metadata_json)
                
                # Upload archive
                with open(archive_path, 'rb') as f:
                    archive_content = f.read()
                
                storage_path = f"backups/{archive_name}"
                result = await self._store_file(
                    archive_content,
                    storage_path,
                    'application/zip'
                )
                
                if result['success']:
                    return result['url']
                
            return None
            
        except Exception as e:
            logger.error(f"Error creating backup archive: {e}")
            return None
    
    async def cleanup_expired_files(self):
        """Clean up expired files"""
        try:
            metadata_file = self.local_storage_path / "metadata.json"
            
            if not metadata_file.exists():
                return
            
            async with aiofiles.open(metadata_file, 'r') as f:
                content = await f.read()
                if not content:
                    return
                
                metadata_list = json.loads(content)
            
            current_time = datetime.now()
            expired_files = []
            active_files = []
            
            for metadata_dict in metadata_list:
                if metadata_dict.get('expires_at'):
                    expires_at = datetime.fromisoformat(metadata_dict['expires_at'])
                    if expires_at <= current_time:
                        expired_files.append(metadata_dict['file_id'])
                        continue
                
                active_files.append(metadata_dict)
            
            # Delete expired files
            for file_id in expired_files:
                await self.delete_file(file_id)
                logger.info(f"Deleted expired file: {file_id}")
            
            logger.info(f"Cleaned up {len(expired_files)} expired files")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired files: {e}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            stats = {
                'total_files': 0,
                'total_size_bytes': 0,
                'files_by_type': {},
                'storage_provider': self.storage_provider.value
            }
            
            metadata_file = self.local_storage_path / "metadata.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    content = f.read()
                    if content:
                        metadata_list = json.loads(content)
                        
                        stats['total_files'] = len(metadata_list)
                        
                        for metadata_dict in metadata_list:
                            file_type = metadata_dict['file_type']
                            size_bytes = metadata_dict['size_bytes']
                            
                            stats['total_size_bytes'] += size_bytes
                            
                            if file_type not in stats['files_by_type']:
                                stats['files_by_type'][file_type] = {
                                    'count': 0,
                                    'total_size_bytes': 0
                                }
                            
                            stats['files_by_type'][file_type]['count'] += 1
                            stats['files_by_type'][file_type]['total_size_bytes'] += size_bytes
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                'error': str(e)
            }

# Global instance
file_storage_service = FileStorageService()