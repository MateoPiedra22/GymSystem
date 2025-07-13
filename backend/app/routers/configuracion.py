"""
Endpoints para configuración del sistema
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import os
import uuid
from PIL import Image
from io import BytesIO

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.usuarios import Usuario
from app.models.rutinas import ConfiguracionEstilos
from app.models.logos import LogoPersonalizado
from app.schemas.configuracion import (
    ConfiguracionEstilos as ConfiguracionEstilosSchema,
    ConfiguracionEstilosCreate,
    ConfiguracionEstilosUpdate,
    LogoPersonalizado as LogoPersonalizadoSchema,
    LogoPersonalizadoCreate,
    LogoPersonalizadoUpdate,
    ConfiguracionSistema,
    ConfiguracionSistemaUpdate,
    TemaPredefinido,
    obtener_temas_predefinidos,
    TEMAS_PREDEFINIDOS
)

router = APIRouter()

# ============= ENDPOINTS DE CONFIGURACIÓN DE ESTILOS =============

@router.get("/estilos", response_model=List[ConfiguracionEstilosSchema])
async def listar_configuraciones_estilos(
    skip: int = 0,
    limit: int = 100,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las configuraciones de estilos disponibles"""
    query = db.query(ConfiguracionEstilos)
    
    if activo is not None:
        query = query.filter(ConfiguracionEstilos.activo == activo)
    
    return query.offset(skip).limit(limit).all()

@router.get("/estilos/{configuracion_id}", response_model=ConfiguracionEstilosSchema)
async def obtener_configuracion_estilos(
    configuracion_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una configuración de estilos específica"""
    configuracion = db.query(ConfiguracionEstilos).filter(
        ConfiguracionEstilos.id == configuracion_id
    ).first()
    
    if not configuracion:
        raise HTTPException(
            status_code=404,
            detail="Configuración de estilos no encontrada"
        )
    
    return configuracion

@router.post("/estilos", response_model=ConfiguracionEstilosSchema)
async def crear_configuracion_estilos(
    configuracion: ConfiguracionEstilosCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una nueva configuración de estilos"""
    # Verificar si ya existe una configuración con el mismo nombre
    existing = db.query(ConfiguracionEstilos).filter(
        ConfiguracionEstilos.nombre_tema == configuracion.nombre_tema
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una configuración con ese nombre de tema"
        )
    
    # Si se marca como predeterminado, desmarcar otros
    if configuracion.es_predeterminado:
        db.query(ConfiguracionEstilos).filter(
            ConfiguracionEstilos.es_predeterminado == True
        ).update({"es_predeterminado": False})
    
    db_configuracion = ConfiguracionEstilos(
        id=str(uuid.uuid4()),
        **configuracion.dict()
    )
    
    db.add(db_configuracion)
    db.commit()
    db.refresh(db_configuracion)
    
    return db_configuracion

@router.put("/estilos/{configuracion_id}", response_model=ConfiguracionEstilosSchema)
async def actualizar_configuracion_estilos(
    configuracion_id: str,
    configuracion: ConfiguracionEstilosUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza una configuración de estilos"""
    db_configuracion = db.query(ConfiguracionEstilos).filter(
        ConfiguracionEstilos.id == configuracion_id
    ).first()
    
    if not db_configuracion:
        raise HTTPException(
            status_code=404,
            detail="Configuración de estilos no encontrada"
        )
    
    # Si se marca como predeterminado, desmarcar otros
    if configuracion.es_predeterminado:
        db.query(ConfiguracionEstilos).filter(
            ConfiguracionEstilos.es_predeterminado == True,
            ConfiguracionEstilos.id != configuracion_id
        ).update({"es_predeterminado": False})
    
    # Actualizar campos
    update_data = configuracion.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_configuracion, field, value)
    
    db.commit()
    db.refresh(db_configuracion)
    
    return db_configuracion

@router.delete("/estilos/{configuracion_id}")
async def eliminar_configuracion_estilos(
    configuracion_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina una configuración de estilos"""
    db_configuracion = db.query(ConfiguracionEstilos).filter(
        ConfiguracionEstilos.id == configuracion_id
    ).first()
    
    if not db_configuracion:
        raise HTTPException(
            status_code=404,
            detail="Configuración de estilos no encontrada"
        )
    
    if db_configuracion.es_predeterminado:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar la configuración predeterminada"
        )
    
    db.delete(db_configuracion)
    db.commit()
    
    return {"detail": "Configuración de estilos eliminada exitosamente"}

@router.get("/estilos/predefinidos", response_model=List[TemaPredefinido])
async def obtener_temas_predefinidos_endpoint():
    """Obtiene los temas predefinidos disponibles"""
    return obtener_temas_predefinidos()

@router.post("/estilos/aplicar-predefinido/{nombre_tema}", response_model=ConfiguracionEstilosSchema)
async def aplicar_tema_predefinido(
    nombre_tema: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Aplica un tema predefinido"""
    if nombre_tema not in TEMAS_PREDEFINIDOS:
        raise HTTPException(
            status_code=404,
            detail="Tema predefinido no encontrado"
        )
    
    # Verificar si ya existe
    existing = db.query(ConfiguracionEstilos).filter(
        ConfiguracionEstilos.nombre_tema == TEMAS_PREDEFINIDOS[nombre_tema]["nombre_tema"]
    ).first()
    
    if existing:
        # Actualizar existente
        for field, value in TEMAS_PREDEFINIDOS[nombre_tema].items():
            setattr(existing, field, value)
        db_configuracion = existing
    else:
        # Crear nuevo
        db_configuracion = ConfiguracionEstilos(
            id=str(uuid.uuid4()),
            **TEMAS_PREDEFINIDOS[nombre_tema]
        )
        db.add(db_configuracion)
    
    db.commit()
    db.refresh(db_configuracion)
    
    return db_configuracion

# ============= ENDPOINTS DE LOGOS PERSONALIZADOS =============

@router.get("/logos", response_model=List[LogoPersonalizadoSchema])
async def listar_logos(
    skip: int = 0,
    limit: int = 100,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista los logos personalizados"""
    query = db.query(LogoPersonalizado)
    
    if activo is not None:
        query = query.filter(LogoPersonalizado.activo == activo)
    
    return query.offset(skip).limit(limit).all()

@router.get("/logos/{logo_id}", response_model=LogoPersonalizadoSchema)
async def obtener_logo(
    logo_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un logo específico"""
    logo = db.query(LogoPersonalizado).filter(
        LogoPersonalizado.id == logo_id
    ).first()
    
    if not logo:
        raise HTTPException(
            status_code=404,
            detail="Logo no encontrado"
        )
    
    return logo

@router.post("/logos/upload", response_model=LogoPersonalizadoSchema)
async def subir_logo(
    file: UploadFile = File(...),
    nombre: str = "Logo personalizado",
    descripcion: Optional[str] = None,
    es_principal: bool = False,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Sube un nuevo logo personalizado"""
    # Validar tipo de archivo
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/svg+xml"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido. Solo se permiten PNG, JPG y SVG"
        )
    
    # Leer archivo
    content = await file.read()
    file_size_kb = len(content) // 1024
    
    # Validar tamaño (máximo 5MB)
    if file_size_kb > 5120:
        raise HTTPException(
            status_code=400,
            detail="El archivo es demasiado grande. Máximo 5MB permitido"
        )
    
    # Obtener dimensiones (solo para imágenes raster)
    dimensiones = {}
    if file.content_type in ["image/png", "image/jpeg", "image/jpg"]:
        try:
            image = Image.open(BytesIO(content))
            dimensiones = {"width": image.width, "height": image.height}
        except Exception:
            dimensiones = {"width": 0, "height": 0}
    
    # Generar nombre único para el archivo
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Directorio de uploads
    upload_dir = "uploads/logos"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Guardar archivo
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Si se marca como principal, desmarcar otros
    if es_principal:
        db.query(LogoPersonalizado).filter(
            LogoPersonalizado.es_principal == True
        ).update({"es_principal": False})
    
    # Crear registro en base de datos
    db_logo = LogoPersonalizado(
        id=str(uuid.uuid4()),
        nombre=nombre,
        descripcion=descripcion,
        archivo_path=file_path,
        tipo_archivo=file.content_type,
        tamaño_kb=file_size_kb,
        dimensiones=dimensiones,
        es_principal=es_principal,
        activo=True
    )
    
    db.add(db_logo)
    db.commit()
    db.refresh(db_logo)
    
    return db_logo

@router.put("/logos/{logo_id}", response_model=LogoPersonalizadoSchema)
async def actualizar_logo(
    logo_id: str,
    logo: LogoPersonalizadoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un logo personalizado"""
    db_logo = db.query(LogoPersonalizado).filter(
        LogoPersonalizado.id == logo_id
    ).first()
    
    if not db_logo:
        raise HTTPException(
            status_code=404,
            detail="Logo no encontrado"
        )
    
    # Si se marca como principal, desmarcar otros
    if logo.es_principal:
        db.query(LogoPersonalizado).filter(
            LogoPersonalizado.es_principal == True,
            LogoPersonalizado.id != logo_id
        ).update({"es_principal": False})
    
    # Actualizar campos
    update_data = logo.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_logo, field, value)
    
    db.commit()
    db.refresh(db_logo)
    
    return db_logo

@router.delete("/logos/{logo_id}")
async def eliminar_logo(
    logo_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un logo personalizado"""
    db_logo = db.query(LogoPersonalizado).filter(
        LogoPersonalizado.id == logo_id
    ).first()
    
    if not db_logo:
        raise HTTPException(
            status_code=404,
            detail="Logo no encontrado"
        )
    
    # Eliminar archivo físico
    try:
        if os.path.exists(db_logo.archivo_path):
            os.remove(db_logo.archivo_path)
    except Exception:
        pass  # No fallar si no se puede eliminar el archivo
    
    db.delete(db_logo)
    db.commit()
    
    return {"detail": "Logo eliminado exitosamente"}

# ============= ENDPOINTS DE CONFIGURACIÓN GENERAL =============

@router.get("/sistema", response_model=ConfiguracionSistema)
async def obtener_configuracion_sistema(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene la configuración actual del sistema"""
    # Obtener tema activo (predeterminado)
    tema_activo = db.query(ConfiguracionEstilos).filter(
        ConfiguracionEstilos.es_predeterminado == True
    ).first()
    
    # Obtener logo principal
    logo_principal = db.query(LogoPersonalizado).filter(
        LogoPersonalizado.es_principal == True
    ).first()
    
    return ConfiguracionSistema(
        tema_activo=tema_activo,
        logo_principal=logo_principal,
        configuraciones_adicionales={}
    )

@router.put("/sistema", response_model=ConfiguracionSistema)
async def actualizar_configuracion_sistema(
    configuracion: ConfiguracionSistemaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza la configuración del sistema"""
    # Actualizar tema activo
    if configuracion.tema_activo_id:
        # Desmarcar todos como predeterminado
        db.query(ConfiguracionEstilos).update({"es_predeterminado": False})
        
        # Marcar el nuevo como predeterminado
        tema = db.query(ConfiguracionEstilos).filter(
            ConfiguracionEstilos.id == configuracion.tema_activo_id
        ).first()
        
        if tema:
            tema.es_predeterminado = True
    
    # Actualizar logo principal
    if configuracion.logo_principal_id:
        # Desmarcar todos como principal
        db.query(LogoPersonalizado).update({"es_principal": False})
        
        # Marcar el nuevo como principal
        logo = db.query(LogoPersonalizado).filter(
            LogoPersonalizado.id == configuracion.logo_principal_id
        ).first()
        
        if logo:
            logo.es_principal = True
    
    db.commit()
    
    # Retornar configuración actualizada
    return await obtener_configuracion_sistema(db, current_user)

@router.get("/css/{configuracion_id}")
async def generar_css_personalizado(
    configuracion_id: str,
    db: Session = Depends(get_db)
):
    """Genera CSS personalizado basado en una configuración de estilos"""
    configuracion = db.query(ConfiguracionEstilos).filter(
        ConfiguracionEstilos.id == configuracion_id
    ).first()
    
    if not configuracion:
        raise HTTPException(
            status_code=404,
            detail="Configuración de estilos no encontrada"
        )
    
    # Generar CSS
    css_content = generar_css_desde_configuracion(configuracion)
    
    from fastapi.responses import Response
    return Response(
        content=css_content,
        media_type="text/css",
        headers={"Cache-Control": "max-age=3600"}
    )

def generar_css_desde_configuracion(configuracion: ConfiguracionEstilos) -> str:
    """Genera CSS personalizado desde una configuración"""
    css_vars = []
    
    # Colores primarios
    for color, value in configuracion.colores_primarios.items():
        css_vars.append(f"--{color}: {value};")
    
    # Colores secundarios
    for color, value in configuracion.colores_secundarios.items():
        css_vars.append(f"--{color}: {value};")
    
    # Fuentes
    for font, value in configuracion.fuentes.items():
        css_vars.append(f"--{font}: {value};")
    
    # Tamaños y espaciado
    for size, value in configuracion.tamaños.items():
        css_vars.append(f"--{size}: {value};")
    
    # Bordes y sombras
    for border, value in configuracion.bordes_y_sombras.items():
        css_vars.append(f"--{border}: {value};")
    
    # Animaciones
    for animation, value in configuracion.animaciones.items():
        css_vars.append(f"--{animation}: {value};")
    
    css_content = f"""
/* Tema personalizado: {configuracion.nombre_tema} */
:root {{
    {chr(10).join(css_vars)}
}}

/* Aplicar variables a elementos base */
body {{
    font-family: var(--font-family, system-ui);
    font-size: var(--font-size-base, 14px);
    color: var(--foreground, #000000);
    background-color: var(--background, #ffffff);
    transition: var(--transition, all 0.2s ease-in-out);
}}

.primary {{
    background-color: var(--primary);
    color: var(--primary-foreground);
}}

.secondary {{
    background-color: var(--secondary);
    color: var(--secondary-foreground);
}}

.accent {{
    background-color: var(--accent);
    color: var(--accent-foreground);
}}

.muted {{
    background-color: var(--muted);
    color: var(--muted-foreground);
}}

.border {{
    border: var(--border);
}}

.shadow {{
    box-shadow: var(--shadow);
}}

.rounded {{
    border-radius: var(--border-radius);
}}

.transition {{
    transition: var(--transition);
}}
"""
    
    return css_content 