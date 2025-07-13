"""
Router para gestión de multimedia en ejercicios y rutinas
"""
import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from PIL import Image
import hashlib
import mimetypes

from ..core.database import get_db
from ..core.auth import get_current_user
from ..models.multimedia import (
    MultimediaEjercicio, MultimediaRutina, AnotacionMultimedia,
    HistorialMultimedia, ColeccionMultimedia, ItemColeccionMultimedia,
    TipoMultimedia, EstadoMultimedia, CategoriaMultimedia
)
from ..models.usuarios import Usuario
from ..models.rutinas import Ejercicio, Rutina
from ..schemas.multimedia import (
    MultimediaCreate, MultimediaUpdate, MultimediaResponse, MultimediaListResponse,
    MultimediaUploadResponse, AnotacionCreate, AnotacionUpdate, AnotacionResponse,
    ColeccionCreate, ColeccionUpdate, ColeccionResponse, ItemColeccionCreate,
    HistorialAcceso, HistorialResponse, BusquedaMultimedia, EstadisticasGenerales,
    ValidacionArchivo, ConfiguracionMultimedia
)

router = APIRouter(tags=["Multimedia"])

# Configuración de archivos
UPLOAD_DIR = "uploads/multimedia"
THUMBNAIL_DIR = "uploads/thumbnails"
ALLOWED_EXTENSIONS = {
    TipoMultimedia.IMAGEN: [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
    TipoMultimedia.VIDEO: [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    TipoMultimedia.AUDIO: [".mp3", ".wav", ".ogg", ".aac", ".flac"],
    TipoMultimedia.DOCUMENTO: [".pdf", ".txt", ".doc", ".docx"]
}

# Tipos MIME permitidos por tipo de multimedia
ALLOWED_MIME_TYPES = {
    TipoMultimedia.IMAGEN: ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"],
    TipoMultimedia.VIDEO: ["video/mp4", "video/avi", "video/quicktime", "video/x-msvideo", "video/webm"],
    TipoMultimedia.AUDIO: ["audio/mpeg", "audio/wav", "audio/ogg", "audio/aac", "audio/flac"],
    TipoMultimedia.DOCUMENTO: ["application/pdf", "text/plain", "application/msword", 
                              "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
}

MAX_FILE_SIZE = {
    TipoMultimedia.IMAGEN: 10 * 1024 * 1024,     # 10MB
    TipoMultimedia.VIDEO: 500 * 1024 * 1024,     # 500MB
    TipoMultimedia.AUDIO: 50 * 1024 * 1024,      # 50MB
    TipoMultimedia.DOCUMENTO: 20 * 1024 * 1024   # 20MB
}

# Crear directorios si no existen
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

# ============= ENDPOINTS DE MULTIMEDIA DE EJERCICIOS =============

@router.get("/ejercicios/{ejercicio_id}", response_model=MultimediaListResponse)
async def obtener_multimedia_ejercicio(
    ejercicio_id: str,
    tipo: Optional[TipoMultimedia] = None,
    categoria: Optional[CategoriaMultimedia] = None,
    estado: Optional[EstadoMultimedia] = Query(EstadoMultimedia.APROBADO),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene el multimedia asociado a un ejercicio"""
    
    # Verificar que el ejercicio existe
    ejercicio = db.query(Ejercicio).filter(Ejercicio.id == ejercicio_id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    # Construir query
    query = db.query(MultimediaEjercicio).filter(MultimediaEjercicio.ejercicio_id == ejercicio_id)
    
    # Aplicar filtros
    if tipo:
        query = query.filter(MultimediaEjercicio.tipo == tipo.value)
    if categoria:
        query = query.filter(MultimediaEjercicio.categoria == categoria.value)
    if estado:
        query = query.filter(MultimediaEjercicio.estado == estado.value)
    
    # Contar total
    total = query.count()
    
    # Aplicar paginación y ordenamiento
    multimedia = query.order_by(
        MultimediaEjercicio.es_principal.desc(),
        MultimediaEjercicio.orden.asc(),
        MultimediaEjercicio.fecha_subida.desc()
    ).offset((pagina - 1) * por_pagina).limit(por_pagina).all()
    
    return MultimediaListResponse(
        multimedia=[MultimediaResponse.from_orm(m) for m in multimedia],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=(total + por_pagina - 1) // por_pagina
    )

@router.post("/ejercicios/{ejercicio_id}/upload", response_model=MultimediaUploadResponse)
async def subir_multimedia_ejercicio(
    ejercicio_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    nombre: str = Form(...),
    descripcion: Optional[str] = Form(None),
    tipo: TipoMultimedia = Form(...),
    categoria: CategoriaMultimedia = Form(...),
    orden: int = Form(1),
    es_principal: bool = Form(False),
    etiquetas: Optional[str] = Form(None),  # JSON string
    nivel_dificultad: Optional[str] = Form(None),
    es_premium: bool = Form(False),
    autoplay: bool = Form(False),
    loop: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Sube un archivo multimedia para un ejercicio"""
    
    # Verificar que el ejercicio existe
    ejercicio = db.query(Ejercicio).filter(Ejercicio.id == ejercicio_id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    # Validar tamaño antes de leer todo el archivo
    if file.size and file.size > MAX_FILE_SIZE.get(tipo, 10 * 1024 * 1024):
        max_mb = MAX_FILE_SIZE.get(tipo, 10 * 1024 * 1024) // (1024 * 1024)
        raise HTTPException(
            status_code=413, 
            detail=f"Archivo demasiado grande. Tamaño máximo permitido: {max_mb}MB"
        )
    
    # Validar archivo
    validacion = await validar_archivo(file, tipo)
    if not validacion.es_valido:
        raise HTTPException(status_code=400, detail=f"Archivo no válido: {', '.join(validacion.errores)}")
    
    # Generar nombre único
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Guardar archivo
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Procesar etiquetas
        etiquetas_list = []
        if etiquetas:
            import json
            try:
                etiquetas_list = json.loads(etiquetas)
            except Exception as e:
                etiquetas_list = [tag.strip() for tag in etiquetas.split(",")]
        
        # Si es principal, quitar flag de otros multimedia del ejercicio
        if es_principal:
            db.query(MultimediaEjercicio).filter(
                MultimediaEjercicio.ejercicio_id == ejercicio_id,
                MultimediaEjercicio.es_principal == True
            ).update({"es_principal": False})
        
        # Crear registro en base de datos
        multimedia = MultimediaEjercicio(
            ejercicio_id=ejercicio_id,
            nombre=nombre,
            descripcion=descripcion,
            tipo=tipo.value,
            categoria=categoria.value,
            archivo_path=unique_filename,
            formato=file_ext.replace(".", ""),
            tamaño_bytes=len(content),
            orden=orden,
            es_principal=es_principal,
            mostrar_en_preview=True,
            autoplay=autoplay,
            loop=loop,
            etiquetas=etiquetas_list,
            nivel_dificultad=nivel_dificultad,
            es_premium=es_premium,
            estado=EstadoMultimedia.PENDIENTE,
            subido_por=current_user.id,
            dimensiones=validacion.dimensiones,
            duracion_segundos=validacion.duracion_segundos
        )
        
        db.add(multimedia)
        db.commit()
        db.refresh(multimedia)
        
        # Procesar en segundo plano (thumbnails, compresión, etc.)
        background_tasks.add_task(procesar_multimedia_async, multimedia.id, file_path)
        
        return MultimediaUploadResponse(
            id=multimedia.id,
            nombre=multimedia.nombre,
            archivo_url=multimedia.get_url_completa(),
            formato=multimedia.formato,
            tamaño_mb=round(multimedia.tamaño_bytes / 1024 / 1024, 2),
            duracion_segundos=multimedia.duracion_segundos,
            dimensiones=multimedia.dimensiones,
            mensaje="Archivo subido exitosamente. Procesando en segundo plano..."
        )
        
    except Exception as e:
        # Limpiar archivo si hay error
        if os.path.exists(file_path):
            os.remove(file_path)
        
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

@router.get("/ejercicios/multimedia/{multimedia_id}", response_model=MultimediaResponse)
async def obtener_multimedia_detalle(
    multimedia_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene detalles de un archivo multimedia específico"""
    multimedia = db.query(MultimediaEjercicio).filter(MultimediaEjercicio.id == multimedia_id).first()
    
    if not multimedia:
        raise HTTPException(status_code=404, detail="Multimedia no encontrado")
    
    # Registrar visualización
    await registrar_acceso_multimedia(multimedia_id, current_user.id, db)
    
    return MultimediaResponse.from_orm(multimedia)

@router.put("/ejercicios/multimedia/{multimedia_id}", response_model=MultimediaResponse)
async def actualizar_multimedia(
    multimedia_id: str,
    multimedia_update: MultimediaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un archivo multimedia"""
    multimedia = db.query(MultimediaEjercicio).filter(MultimediaEjercicio.id == multimedia_id).first()
    
    if not multimedia:
        raise HTTPException(status_code=404, detail="Multimedia no encontrado")
    
    # Verificar permisos (solo el creador o admin puede editar)
    if multimedia.subido_por != current_user.id and not current_user.es_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar este multimedia")
    
    # Si se establece como principal, quitar flag de otros
    if multimedia_update.es_principal:
        db.query(MultimediaEjercicio).filter(
            MultimediaEjercicio.ejercicio_id == multimedia.ejercicio_id,
            MultimediaEjercicio.es_principal == True,
            MultimediaEjercicio.id != multimedia_id
        ).update({"es_principal": False})
    
    # Actualizar campos
    update_data = multimedia_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(multimedia, field, value)
    
    db.commit()
    db.refresh(multimedia)
    
    return MultimediaResponse.from_orm(multimedia)

@router.delete("/ejercicios/multimedia/{multimedia_id}")
async def eliminar_multimedia(
    multimedia_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un archivo multimedia"""
    multimedia = db.query(MultimediaEjercicio).filter(MultimediaEjercicio.id == multimedia_id).first()
    
    if not multimedia:
        raise HTTPException(status_code=404, detail="Multimedia no encontrado")
    
    # Verificar permisos
    if multimedia.subido_por != current_user.id and not current_user.es_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este multimedia")
    
    try:
        # Eliminar archivos físicos
        file_path = os.path.join(UPLOAD_DIR, multimedia.archivo_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Eliminar thumbnail si existe
        if multimedia.thumbnail_path:
            thumb_path = os.path.join(THUMBNAIL_DIR, multimedia.thumbnail_path)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        
        # Eliminar registro de base de datos
        db.delete(multimedia)
        db.commit()
        
        return {"mensaje": "Multimedia eliminado exitosamente"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar multimedia: {str(e)}")

# ============= ENDPOINTS DE ANOTACIONES =============

@router.get("/ejercicios/multimedia/{multimedia_id}/anotaciones", response_model=List[AnotacionResponse])
async def obtener_anotaciones(
    multimedia_id: str,
    activas_solo: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene las anotaciones de un archivo multimedia"""
    query = db.query(AnotacionMultimedia).filter(AnotacionMultimedia.multimedia_id == multimedia_id)
    
    if activas_solo:
        query = query.filter(AnotacionMultimedia.activo == True)
    
    anotaciones = query.order_by(AnotacionMultimedia.tiempo_inicio.asc()).all()
    
    return [AnotacionResponse.from_orm(a) for a in anotaciones]

@router.post("/ejercicios/multimedia/{multimedia_id}/anotaciones", response_model=AnotacionResponse)
async def crear_anotacion(
    multimedia_id: str,
    anotacion: AnotacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una nueva anotación en un archivo multimedia"""
    
    # Verificar que el multimedia existe
    multimedia = db.query(MultimediaEjercicio).filter(MultimediaEjercicio.id == multimedia_id).first()
    if not multimedia:
        raise HTTPException(status_code=404, detail="Multimedia no encontrado")
    
    # Crear anotación
    db_anotacion = AnotacionMultimedia(
        multimedia_id=multimedia_id,
        **anotacion.dict(exclude={'multimedia_id'}),
        creado_por=current_user.id
    )
    
    db.add(db_anotacion)
    db.commit()
    db.refresh(db_anotacion)
    
    return AnotacionResponse.from_orm(db_anotacion)

# ============= ENDPOINTS DE ARCHIVOS =============

@router.get("/archivo/{multimedia_id}")
async def servir_archivo_multimedia(
    multimedia_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Sirve un archivo multimedia"""
    multimedia = db.query(MultimediaEjercicio).filter(
        MultimediaEjercicio.id == multimedia_id,
        MultimediaEjercicio.estado == EstadoMultimedia.APROBADO
    ).first()
    
    if not multimedia:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    file_path = os.path.join(UPLOAD_DIR, multimedia.archivo_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo físico no encontrado")
    
    # Registrar descarga
    multimedia.descargas += 1
    db.commit()
    
    return FileResponse(
        file_path,
        media_type=f"{multimedia.tipo}/{multimedia.formato}",
        filename=f"{multimedia.nombre}.{multimedia.formato}"
    )

@router.get("/thumbnail/{multimedia_id}")
async def servir_thumbnail(
    multimedia_id: str,
    db: Session = Depends(get_db)
):
    """Sirve el thumbnail de un archivo multimedia"""
    multimedia = db.query(MultimediaEjercicio).filter(MultimediaEjercicio.id == multimedia_id).first()
    
    if not multimedia or not multimedia.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail no encontrado")
    
    thumb_path = os.path.join(THUMBNAIL_DIR, multimedia.thumbnail_path)
    
    if not os.path.exists(thumb_path):
        raise HTTPException(status_code=404, detail="Archivo de thumbnail no encontrado")
    
    return FileResponse(thumb_path, media_type="image/jpeg")

# ============= FUNCIONES AUXILIARES =============

async def _validar_nombre_archivo(file: UploadFile) -> tuple[bool, list[str]]:
    """Valida el nombre del archivo"""
    errores = []
    
    if not file.filename:
        errores.append("Archivo sin nombre")
        return False, errores
    
    # Validar nombre de archivo contra caracteres peligrosos
    filename_safe = os.path.basename(file.filename)
    if any(char in filename_safe for char in ['..', '/', '\\', '\x00']):
        errores.append("Nombre de archivo contiene caracteres no permitidos")
        return False, errores
    
    return True, errores

async def _validar_extension_tipo(file: UploadFile, tipo: TipoMultimedia) -> tuple[bool, list[str], str]:
    """Valida la extensión del archivo según el tipo"""
    errores = []
    
    filename = file.filename or ""
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS.get(tipo, []):
        errores.append(f"Extensión {file_ext} no permitida para tipo {tipo.value}")
        return False, errores, ""
    
    return True, errores, file_ext

async def _validar_tamaño_archivo(content: bytes, tipo: TipoMultimedia) -> tuple[bool, list[str], float]:
    """Valida el tamaño del archivo"""
    errores = []
    
    file_size_mb = len(content) / 1024 / 1024
    max_size = MAX_FILE_SIZE.get(tipo, 10 * 1024 * 1024)
    
    if len(content) > max_size:
        errores.append(f"Archivo demasiado grande. Máximo {max_size // (1024*1024)}MB")
        return False, errores, file_size_mb
    
    return True, errores, file_size_mb

async def _validar_tipo_mime(file: UploadFile, tipo: TipoMultimedia) -> tuple[bool, list[str]]:
    """Valida el tipo MIME del archivo"""
    errores = []
    
    filename = file.filename or ""
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        allowed_mimes = ALLOWED_MIME_TYPES.get(tipo, [])
        if mime_type not in allowed_mimes:
            errores.append(f"Tipo de archivo no permitido. Tipo detectado: {mime_type}")
    
    return True, errores

async def _validar_contenido_seguridad(content: bytes, tipo: TipoMultimedia) -> tuple[bool, list[str], list[str]]:
    """Valida la seguridad del contenido del archivo"""
    errores = []
    advertencias = []
    
    if len(content) == 0:
        errores.append("Archivo vacío")
        return False, errores, advertencias
    
    # Verificar magic bytes para detectar tipo real de archivo
    magic_bytes = content[:8]
    
    # Verificar que el contenido coincida con la extensión
    if tipo == TipoMultimedia.IMAGEN:
        image_signatures = [
            b'\xff\xd8\xff',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF87a',  # GIF
            b'GIF89a',  # GIF
            b'RIFF',  # WebP
        ]
        if not any(magic_bytes.startswith(sig) for sig in image_signatures):
            errores.append("El contenido del archivo no corresponde a una imagen válida")
    
    elif tipo == TipoMultimedia.VIDEO:
        video_signatures = [
            b'ftyp',  # MP4
            b'RIFF',  # AVI
            b'\x1a\x45\xdf\xa3',  # WebM
            b'\x00\x00\x00\x18',  # MP4
        ]
        if not any(magic_bytes.startswith(sig) for sig in video_signatures):
            errores.append("El contenido del archivo no corresponde a un video válido")
    
    elif tipo == TipoMultimedia.DOCUMENTO:
        doc_signatures = [
            b'%PDF',  # PDF
            b'PK\x03\x04',  # ZIP/DOCX
            b'\xd0\xcf\x11\xe0',  # DOC
        ]
        if not any(magic_bytes.startswith(sig) for sig in doc_signatures):
            errores.append("El contenido del archivo no corresponde a un documento válido")
    
    # Verificar que no sea un archivo ejecutable disfrazado
    executable_signatures = [
        b'MZ',  # Windows EXE
        b'\x7fELF',  # Linux ELF
        b'\xfe\xed\xfa',  # Mach-O
    ]
    if any(magic_bytes.startswith(sig) for sig in executable_signatures):
        errores.append("Archivos ejecutables no están permitidos")
    
    # Verificar tamaño mínimo (archivos vacíos o muy pequeños pueden ser sospechosos)
    if len(content) < 100:  # Menos de 100 bytes
        advertencias.append("Archivo muy pequeño, verificar contenido")
    
    # Verificar caracteres nulos (pueden indicar archivos binarios maliciosos)
    if b'\x00' in content[:1024]:  # Primeros 1KB
        if tipo == TipoMultimedia.DOCUMENTO:
            advertencias.append("Archivo contiene caracteres nulos")
        else:
            errores.append("Archivo contiene caracteres nulos no permitidos")
    
    return True, errores, advertencias

async def _analizar_metadatos(file: UploadFile, tipo: TipoMultimedia) -> tuple[Optional[dict], Optional[int], Optional[str], list[str]]:
    """Analiza los metadatos del archivo según su tipo"""
    dimensiones = None
    duracion_segundos = None
    calidad_detectada = None
    advertencias = []
    
    try:
        if tipo == TipoMultimedia.IMAGEN:
            # Resetear posición para PIL
            await file.seek(0)
            with Image.open(file.file) as img:
                dimensiones = {"width": img.width, "height": img.height}
                calidad_detectada = "HD" if img.width >= 1280 else "SD"
                
                # Validar dimensiones máximas
                if img.width > 4096 or img.height > 4096:
                    advertencias.append("Imagen muy grande, se recomienda reducir dimensiones")
        
        elif tipo == TipoMultimedia.VIDEO:
            # Sin ffmpeg, solo validación básica
            dimensiones = {"width": 1920, "height": 1080}  # Placeholder
            duracion_segundos = 120  # Placeholder
            calidad_detectada = "FHD"
            
    except Exception as e:
        advertencias.append(f"No se pudieron analizar metadatos: {str(e)}")
    
    return dimensiones, duracion_segundos, calidad_detectada, advertencias

async def validar_archivo(file: UploadFile, tipo: TipoMultimedia) -> ValidacionArchivo:
    """Valida un archivo antes de subirlo con validación robusta de contenido"""
    
    # Leer contenido para análisis
    content = await file.read()
    await file.seek(0)  # Resetear posición
    
    errores = []
    advertencias = []
    
    # Validar nombre de archivo
    nombre_valido, errores_nombre = await _validar_nombre_archivo(file)
    errores.extend(errores_nombre)
    
    if nombre_valido:
        # Validar extensión
        ext_valida, errores_ext, file_ext = await _validar_extension_tipo(file, tipo)
        errores.extend(errores_ext)
        
        # Validar tamaño
        tam_valido, errores_tam, file_size_mb = await _validar_tamaño_archivo(content, tipo)
        errores.extend(errores_tam)
        
        # Validar tipo MIME
        mime_valido, errores_mime = await _validar_tipo_mime(file, tipo)
        errores.extend(errores_mime)
        
        # Validar contenido de seguridad
        seg_valido, errores_seg, advertencias_seg = await _validar_contenido_seguridad(content, tipo)
        errores.extend(errores_seg)
        advertencias.extend(advertencias_seg)
        
        # Analizar metadatos
        dimensiones, duracion_segundos, calidad_detectada, advertencias_meta = await _analizar_metadatos(file, tipo)
        advertencias.extend(advertencias_meta)
        
        formato_detectado = file_ext.replace(".", "") if file_ext else ""
    else:
        file_size_mb = 0
        formato_detectado = ""
        dimensiones = None
        duracion_segundos = None
        calidad_detectada = None
    
    return ValidacionArchivo(
        es_valido=len(errores) == 0,
        tipo_detectado=None,
        formato_detectado=formato_detectado,
        tamaño_mb=file_size_mb,
        duracion_segundos=duracion_segundos,
        dimensiones=dimensiones,
        calidad_detectada=calidad_detectada,
        errores=errores,
        advertencias=advertencias
    )

async def procesar_multimedia_async(multimedia_id: str, file_path: str):
    """Procesa multimedia en segundo plano (thumbnails, compresión, etc.)"""
    try:
        # Aquí iría el procesamiento:
        # - Generar thumbnails para videos
        # - Comprimir archivos si es necesario
        # - Generar diferentes calidades
        # - Análisis de contenido
        
        # Por ahora, solo marcamos como aprobado
        from ..core.database import SessionLocal
        db = SessionLocal()
        
        multimedia = db.query(MultimediaEjercicio).filter(MultimediaEjercicio.id == multimedia_id).first()
        if multimedia:
            multimedia.estado = EstadoMultimedia.APROBADO
            db.commit()
        
        db.close()
        
    except Exception as e:
        print(f"Error procesando multimedia {multimedia_id}: {e}")

async def registrar_acceso_multimedia(multimedia_id: str, usuario_id: str, db: Session):
    """Registra el acceso a un archivo multimedia"""
    try:
        # Incrementar contador de vistas
        multimedia = db.query(MultimediaEjercicio).filter(MultimediaEjercicio.id == multimedia_id).first()
        if multimedia:
            multimedia.vistas += 1
        
        # Crear registro de historial
        historial = HistorialMultimedia(
            usuario_id=usuario_id,
            multimedia_id=multimedia_id,
            dispositivo="web"  # Detectar desde headers si es necesario
        )
        
        db.add(historial)
        db.commit()
        
    except Exception as e:
        print(f"Error registrando acceso: {e}") 