"""
Router para gestión de logos personalizados
"""
import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from PIL import Image
import uuid

from ..core.database import get_db
from ..core.auth import get_current_user
from ..models import LogoPersonalizado, Usuario
from ..schemas.logos import (
    LogoResponse, LogoUpdate, LogoUploadResponse, 
    LogoPrincipalUpdate, LogosListResponse
)

router = APIRouter(prefix="/configuracion/logos", tags=["Logos"])

# Directorio para almacenar logos
LOGOS_DIR = "uploads/logos"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Crear directorio si no existe
os.makedirs(LOGOS_DIR, exist_ok=True)

@router.get("/", response_model=LogosListResponse)
async def obtener_logos(
    activos_solo: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene todos los logos disponibles"""
    query = db.query(LogoPersonalizado)
    
    if activos_solo:
        query = query.filter(LogoPersonalizado.activo == True)
    
    logos = query.order_by(LogoPersonalizado.es_principal.desc(), LogoPersonalizado.creado_en.desc()).all()
    
    # Obtener logo principal
    logo_principal = db.query(LogoPersonalizado).filter(
        LogoPersonalizado.es_principal == True,
        LogoPersonalizado.activo == True
    ).first()
    
    return LogosListResponse(
        logos=[LogoResponse.from_orm(logo) for logo in logos],
        total=len(logos),
        logo_principal=LogoResponse.from_orm(logo_principal) if logo_principal else None
    )

@router.post("/upload", response_model=LogoUploadResponse)
async def subir_logo(
    file: UploadFile = File(...),
    nombre: str = Form(...),
    descripcion: Optional[str] = Form(None),
    es_principal: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Sube un nuevo logo al sistema"""
    
    # Validar tipo de archivo
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo requerido")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de archivo no permitido. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validar tamaño
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (máximo 5MB)")
    
    # Generar nombre único
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(LOGOS_DIR, unique_filename)
    
    try:
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Obtener dimensiones de imagen (solo para imágenes)
        dimensiones = {"width": 0, "height": 0}
        if file_ext in [".png", ".jpg", ".jpeg", ".gif"]:
            try:
                with Image.open(file_path) as img:
                    dimensiones = {"width": img.width, "height": img.height}
            except Exception:
                pass  # Si no se puede obtener dimensiones, usar valores por defecto
        
        # Si es principal, quitar el flag de otros logos
        if es_principal:
            db.query(LogoPersonalizado).filter(
                LogoPersonalizado.es_principal == True
            ).update({"es_principal": False})
            db.commit()
        
        # Crear registro en base de datos
        logo = LogoPersonalizado(
            nombre=nombre,
            descripcion=descripcion,
            archivo_path=f"logos/{unique_filename}",
            tipo_archivo=file_ext.replace(".", ""),
            tamaño_kb=len(content) // 1024,
            dimensiones=dimensiones,
            es_principal=es_principal,
            activo=True
        )
        
        db.add(logo)
        db.commit()
        db.refresh(logo)
        
        return LogoUploadResponse(
            id=logo.id,
            nombre=logo.nombre,
            descripcion=logo.descripcion,
            archivo_path=logo.archivo_path,
            url=logo.get_url(),
            tipo_archivo=logo.tipo_archivo,
            tamaño_kb=logo.tamaño_kb,
            dimensiones=logo.dimensiones,
            mensaje="Logo subido exitosamente"
        )
        
    except Exception as e:
        # Limpiar archivo si hay error
        if os.path.exists(file_path):
            os.remove(file_path)
        
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al subir logo: {str(e)}")

@router.get("/{logo_id}", response_model=LogoResponse)
async def obtener_logo(
    logo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un logo específico"""
    logo = db.query(LogoPersonalizado).filter(LogoPersonalizado.id == logo_id).first()
    
    if not logo:
        raise HTTPException(status_code=404, detail="Logo no encontrado")
    
    return LogoResponse.from_orm(logo)

@router.put("/{logo_id}", response_model=LogoResponse)
async def actualizar_logo(
    logo_id: int,
    logo_update: LogoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un logo existente"""
    logo = db.query(LogoPersonalizado).filter(LogoPersonalizado.id == logo_id).first()
    
    if not logo:
        raise HTTPException(status_code=404, detail="Logo no encontrado")
    
    # Si se establece como principal, quitar el flag de otros logos
    if logo_update.es_principal:
        db.query(LogoPersonalizado).filter(
            LogoPersonalizado.es_principal == True,
            LogoPersonalizado.id != logo_id
        ).update({"es_principal": False})
    
    # Actualizar campos
    update_data = logo_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(logo, field, value)
    
    db.commit()
    db.refresh(logo)
    
    return LogoResponse.from_orm(logo)

@router.delete("/{logo_id}")
async def eliminar_logo(
    logo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un logo"""
    logo = db.query(LogoPersonalizado).filter(LogoPersonalizado.id == logo_id).first()
    
    if not logo:
        raise HTTPException(status_code=404, detail="Logo no encontrado")
    
    # No permitir eliminar el logo principal activo
    if logo.es_principal:
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar el logo principal. Establezca otro logo como principal primero."
        )
    
    try:
        # Eliminar archivo físico
        file_path = os.path.join("uploads", logo.archivo_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Eliminar registro de base de datos
        db.delete(logo)
        db.commit()
        
        return {"mensaje": "Logo eliminado exitosamente"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar logo: {str(e)}")

@router.post("/establecer-principal")
async def establecer_logo_principal(
    logo_update: LogoPrincipalUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Establece un logo como principal"""
    logo = db.query(LogoPersonalizado).filter(LogoPersonalizado.id == logo_update.logo_id).first()
    
    if not logo:
        raise HTTPException(status_code=404, detail="Logo no encontrado")
    
    if not logo.activo:
        raise HTTPException(status_code=400, detail="No se puede establecer como principal un logo inactivo")
    
    try:
        # Quitar flag principal de otros logos
        db.query(LogoPersonalizado).filter(
            LogoPersonalizado.es_principal == True
        ).update({"es_principal": False})
        
        # Establecer como principal
        logo.es_principal = True
        
        db.commit()
        db.refresh(logo)
        
        return {
            "mensaje": "Logo establecido como principal exitosamente",
            "logo": LogoResponse.from_orm(logo)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al establecer logo principal: {str(e)}")

@router.get("/archivo/{logo_id}")
async def servir_logo(
    logo_id: int,
    db: Session = Depends(get_db)
):
    """Sirve el archivo de logo directamente"""
    logo = db.query(LogoPersonalizado).filter(
        LogoPersonalizado.id == logo_id,
        LogoPersonalizado.activo == True
    ).first()
    
    if not logo:
        raise HTTPException(status_code=404, detail="Logo no encontrado")
    
    file_path = os.path.join("uploads", logo.archivo_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo de logo no encontrado")
    
    return FileResponse(
        file_path,
        media_type=f"image/{logo.tipo_archivo}",
        filename=f"{logo.nombre}.{logo.tipo_archivo}"
    )

@router.get("/principal/actual", response_model=Optional[LogoResponse])
async def obtener_logo_principal(
    db: Session = Depends(get_db)
):
    """Obtiene el logo principal actual"""
    logo = db.query(LogoPersonalizado).filter(
        LogoPersonalizado.es_principal == True,
        LogoPersonalizado.activo == True
    ).first()
    
    if not logo:
        return None
    
    return LogoResponse.from_orm(logo) 