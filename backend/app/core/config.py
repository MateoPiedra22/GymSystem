from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Basic settings
    PROJECT_NAME: str = "GymSystem"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Sistema de Gestión de Gimnasio Modular Avanzado"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./gymsystem.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "tauri://localhost",
        "https://tauri.localhost"
    ]
    
    # File uploads
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/webm"]
    
    # WhatsApp Integration
    WHATSAPP_API_URL: str = ""
    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""
    
    # Instagram Integration
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_USER_ID: str = ""
    
    # Email settings
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    
    # Redis (for caching and tasks)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Gym settings (customizable)
    GYM_NAME: str = "GymSystem"
    GYM_LOGO: str = ""
    GYM_PRIMARY_COLOR: str = "#1e40af"
    GYM_SECONDARY_COLOR: str = "#059669"
    GYM_ADDRESS: str = ""
    GYM_PHONE: str = ""
    GYM_EMAIL: str = ""
    GYM_WEBSITE: str = ""
    
    # Default phone country code
    DEFAULT_COUNTRY_CODE: str = "+54"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure upload directory exists
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(exist_ok=True)
(upload_path / "profiles").mkdir(exist_ok=True)
(upload_path / "exercises").mkdir(exist_ok=True)
(upload_path / "documents").mkdir(exist_ok=True)