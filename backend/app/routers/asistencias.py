# /backend/app/routers/asistencias.py
"""
Router para gestión de asistencias
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.core.auth import get_current_user, get_current_admin_user
from app.services.asistencia_service import (
    registrar_asistencia, obtener_asistencia, obtener_asistencias, 
    actualizar_asistencia, eliminar_asistencia, obtener_asistencias_usuario,
    obtener_asistencias_clase, obtener_estadisticas_asistencias,
    generar_reporte_asistencias
)
from app.schemas.asistencias import (
    Asistencia, AsistenciaCreate, AsistenciaUpdate, AsistenciaResumen,
    AsistenciaEstadistica, ReporteAsistenciasPeriodo
)
from app.schemas.usuarios import UsuarioInDB as Usuario
from app.core.database import get_db

# Crear router
router = APIRouter(
    tags=["asistencias"],
    responses={404: {"description": "No encontrado"}},
)


@router.post("/", response_model=Asistencia, status_code=201)
async def registrar_nueva_asistencia(
    asistencia: AsistenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registrar una nueva asistencia en el sistema.
    
    - **usuario_id**: ID del usuario que registra asistencia
    - **fecha**: Fecha y hora de la asistencia (opcional, por defecto es ahora)
    - **tipo**: Tipo de asistencia (clase, general, entrenamiento_personal)
    - **clase_id**: ID de la clase (requerido si el tipo es 'clase')
    - **notas**: Notas adicionales sobre la asistencia (opcional)
    - **duracion_minutos**: Duración de la sesión en minutos (opcional)
    """
    # Verificar que el usuario actual sea admin o el mismo usuario de la asistencia
    if not current_user.es_admin and current_user.id != asistencia.usuario_id:
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para registrar asistencias de otros usuarios"
        )
    
    return await registrar_asistencia(db=db, asistencia=asistencia)


@router.get("/", response_model=List[AsistenciaResumen])
async def listar_asistencias(
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    usuario_id: Optional[int] = Query(None, description="Filtrar por ID de usuario"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de asistencia"),
    clase_id: Optional[int] = Query(None, description="Filtrar por ID de clase"),
    desde: Optional[date] = Query(None, description="Fecha desde (formato YYYY-MM-DD)"),
    hasta: Optional[date] = Query(None, description="Fecha hasta (formato YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener lista de asistencias con opciones de filtrado.
    
    Si el usuario no es administrador, solo verá sus propias asistencias.
    Admite filtrado por usuario, tipo, clase y rango de fechas.
    """
    # Si no es admin, forzar filtro por usuario actual
    if not current_user.es_admin:
        usuario_id = current_user.id
    
    return await obtener_asistencias(
        db=db, 
        skip=skip, 
        limit=limit, 
        usuario_id=usuario_id,
        tipo=tipo,
        clase_id=clase_id,
        desde=desde,
        hasta=hasta
    )


@router.get("/{asistencia_id}", response_model=Asistencia)
async def obtener_detalles_asistencia(
    asistencia_id: int = Path(..., gt=0, description="ID de la asistencia a consultar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener los detalles completos de una asistencia específica por su ID.
    
    Si el usuario no es administrador, solo podrá ver sus propias asistencias.
    """
    asistencia = await obtener_asistencia(db, asistencia_id)
    if not asistencia:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")
    
    # Verificar permisos
    if not current_user.es_admin and asistencia.usuario_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para ver esta asistencia"
        )
    
    return asistencia


@router.put("/{asistencia_id}", response_model=Asistencia)
async def actualizar_datos_asistencia(
    asistencia_id: int = Path(..., gt=0, description="ID de la asistencia a actualizar"),
    asistencia_update: AsistenciaUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Actualizar los datos de una asistencia existente.
    
    Solo administradores pueden actualizar asistencias.
    Permite actualizar fecha, tipo, clase, notas y duración.
    """
    asistencia_existente = await obtener_asistencia(db, asistencia_id)
    if not asistencia_existente:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")
    
    return await actualizar_asistencia(db=db, asistencia_id=asistencia_id, asistencia_update=asistencia_update)


@router.delete("/{asistencia_id}", status_code=204)
async def eliminar_asistencia_existente(
    asistencia_id: int = Path(..., gt=0, description="ID de la asistencia a eliminar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Eliminar una asistencia del sistema.
    
    Solo administradores pueden eliminar asistencias.
    """
    asistencia = await obtener_asistencia(db, asistencia_id)
    if not asistencia:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")
    
    await eliminar_asistencia(db=db, asistencia_id=asistencia_id)
    return None


@router.get("/usuario/{usuario_id}", response_model=List[AsistenciaResumen])
async def listar_asistencias_usuario(
    usuario_id: int = Path(..., gt=0, description="ID del usuario"),
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    desde: Optional[date] = Query(None, description="Fecha desde (formato YYYY-MM-DD)"),
    hasta: Optional[date] = Query(None, description="Fecha hasta (formato YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener lista de asistencias de un usuario específico.
    
    Si el usuario no es administrador, solo podrá ver sus propias asistencias.
    """
    # Verificar permisos
    if not current_user.es_admin and usuario_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para ver asistencias de otros usuarios"
        )
    
    return await obtener_asistencias_usuario(
        db=db, 
        usuario_id=usuario_id, 
        skip=skip, 
        limit=limit,
        desde=desde,
        hasta=hasta
    )


@router.get("/clase/{clase_id}", response_model=List[AsistenciaResumen])
async def listar_asistencias_clase(
    clase_id: int = Path(..., gt=0, description="ID de la clase"),
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    desde: Optional[date] = Query(None, description="Fecha desde (formato YYYY-MM-DD)"),
    hasta: Optional[date] = Query(None, description="Fecha hasta (formato YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Obtener lista de asistencias a una clase específica.
    
    Solo administradores pueden acceder a esta información.
    """
    return await obtener_asistencias_clase(
        db=db, 
        clase_id=clase_id, 
        skip=skip, 
        limit=limit,
        desde=desde,
        hasta=hasta
    )


@router.get("/estadisticas/resumen", response_model=AsistenciaEstadistica)
async def obtener_estadisticas(
    desde: Optional[date] = Query(None, description="Fecha desde (formato YYYY-MM-DD)"),
    hasta: Optional[date] = Query(None, description="Fecha hasta (formato YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Obtener estadísticas generales de asistencias.
    
    Solo administradores pueden acceder a estas estadísticas.
    Incluye totales, distribución por tipo, por día de la semana, por hora y promedios.
    """
    return await obtener_estadisticas_asistencias(db=db, desde=desde, hasta=hasta)


@router.get("/reportes/periodo", response_model=ReporteAsistenciasPeriodo)
async def generar_reporte(
    desde: date = Query(..., description="Fecha desde (formato YYYY-MM-DD)"),
    hasta: date = Query(..., description="Fecha hasta (formato YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Generar un reporte detallado de asistencias por periodo.
    
    Solo administradores pueden acceder a estos reportes.
    Incluye métricas agregadas y análisis de tendencias.
    """
    if hasta < desde:
        raise HTTPException(
            status_code=400, 
            detail="La fecha final debe ser posterior a la fecha inicial"
        )
    
    return await generar_reporte_asistencias(db=db, desde=desde, hasta=hasta)
