from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

# Import routers
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine, Base
from app.core.exceptions import setup_exception_handlers
from app.middleware.security import SecurityMiddleware
from app.middleware.logging import LoggingMiddleware

# Create tables
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting GymSystem API...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("📊 Database tables created")
    
    # Initialize default data
    from app.core.init_db import init_db
    init_db()
    logger.info("🔧 Database initialized with default data")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down GymSystem API...")

# Create FastAPI app
app = FastAPI(
    title="GymSystem API",
    description="Sistema de Gestión de Gimnasio Modular Avanzado",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(LoggingMiddleware)

# Setup exception handlers
setup_exception_handlers(app)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GymSystem API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🏋️ Bienvenido a GymSystem API",
        "version": "1.0.0",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else "Disabled in production",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )