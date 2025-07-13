# /backend/app/routers/pagos.py
"""
Router para gestión de pagos
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
from datetime import datetime, date, timedelta

from app.core.auth import get_current_user, get_current_admin_user
from app.services.pago_service import (
    crear_pago, obtener_pago, obtener_pagos, 
    actualizar_pago, eliminar_pago, obtener_pagos_usuario,
    obtener_estadisticas_pagos, generar_reporte_pagos
)
from app.models.pagos import EstadoPago
from app.schemas.pagos import (
    Pago, PagoCreate, PagoUpdate, PagoResumen,
    PagoEstadistica, ReportePagos
)
from app.schemas.usuarios import UsuarioInDB as Usuario
from app.core.database import get_db

# Crear router
router = APIRouter(
    tags=["pagos"],
    responses={404: {"description": "No encontrado"}},
)


@router.post("/", response_model=Pago, status_code=201)
async def crear_nuevo_pago(
    pago: PagoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear un nuevo pago en el sistema.
    
    - **usuario_id**: ID del usuario que realiza el pago
    - **monto**: Cantidad del pago (debe ser positivo)
    - **fecha_pago**: Fecha y hora del pago (opcional, por defecto es ahora)
    - **metodo_pago**: Método utilizado para el pago
    - **concepto**: Descripción o razón del pago
    - **notas**: Notas adicionales sobre el pago (opcional)
    - **estado**: Estado inicial del pago (por defecto es 'pendiente')
    """
    # Verificar que el usuario actual sea admin o el mismo usuario del pago
    if not current_user.es_admin and current_user.id != pago.usuario_id:
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para registrar pagos de otros usuarios"
        )
    
    return await crear_pago(db=db, pago=pago)


@router.get("/", response_model=List[PagoResumen])
async def listar_pagos(
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    usuario_id: Optional[str] = Query(None, description="Filtrar por ID de usuario"),
    estado: Optional[str] = Query(None, description="Filtrar por estado de pago"),
    desde: Optional[datetime] = Query(None, description="Fecha desde (formato YYYY-MM-DDTHH:MM:SS)"),
    hasta: Optional[datetime] = Query(None, description="Fecha hasta (formato YYYY-MM-DDTHH:MM:SS)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener lista de pagos con opciones de filtrado.
    
    Si el usuario no es administrador, solo verá sus propios pagos.
    Admite filtrado por usuario, estado y rango de fechas.
    """
    id_a_filtrar = usuario_id
    # Si no es admin, forzar filtro por usuario actual e ignorar el parámetro usuario_id
    if not current_user.es_admin:
        id_a_filtrar = current_user.id
    
    estado_enum: Optional[EstadoPago] = None
    if estado:
        try:
            estado_enum = EstadoPago(estado)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"'{estado}' no es un estado de pago válido. Use uno de: {[e.value for e in EstadoPago]}."
            )

    return await obtener_pagos(
        db=db, 
        skip=skip, 
        limit=limit, 
        usuario_id=id_a_filtrar,
        estado=estado_enum,
        fecha_desde=desde,
        fecha_hasta=hasta
    )


@router.get("/{pago_id}", response_model=Pago)
async def obtener_detalles_pago(
    pago_id: str = Path(..., description="ID del pago a consultar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener los detalles completos de un pago específico por su ID.
    
    Si el usuario no es administrador, solo podrá ver sus propios pagos.
    """
    pago = await obtener_pago(db, pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    # Verificar permisos
    if not current_user.es_admin and pago.usuario_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para ver este pago"
        )
    
    return pago


@router.put("/{pago_id}", response_model=Pago)
async def actualizar_datos_pago(
    pago_id: str = Path(..., description="ID del pago a actualizar"),
    pago_update: PagoUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Actualizar los datos de un pago existente.
    
    Solo administradores pueden actualizar pagos.
    Permite actualizar monto, fecha, método, concepto, notas y estado.
    """
    pago_existente = await obtener_pago(db, pago_id)
    if not pago_existente:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    return await actualizar_pago(db=db, pago_id=pago_id, pago_update=pago_update)


@router.delete("/{pago_id}", status_code=204)
async def eliminar_pago_existente(
    pago_id: str = Path(..., description="ID del pago a eliminar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Eliminar un pago del sistema.
    
    Solo administradores pueden eliminar pagos.
    """
    pago = await obtener_pago(db, pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    await eliminar_pago(db=db, pago_id=pago_id)
    return None


@router.get("/usuario/{usuario_id}", response_model=List[PagoResumen])
async def listar_pagos_usuario(
    usuario_id: str = Path(..., description="ID del usuario"),
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener lista de pagos de un usuario específico.
    
    Si el usuario no es administrador, solo podrá ver sus propios pagos.
    """
    # Verificar permisos
    if not current_user.es_admin and usuario_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para ver pagos de otros usuarios"
        )
    
    return await obtener_pagos_usuario(db=db, usuario_id=usuario_id, skip=skip, limit=limit)


@router.get("/estadisticas/resumen", response_model=PagoEstadistica)
async def obtener_estadisticas(
    desde: Optional[datetime] = Query(None, description="Fecha desde (formato YYYY-MM-DDTHH:MM:SS)"),
    hasta: Optional[datetime] = Query(None, description="Fecha hasta (formato YYYY-MM-DDTHH:MM:SS)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Obtener estadísticas generales de pagos.
    
    Solo administradores pueden acceder a estas estadísticas.
    Incluye totales, promedios, distribución por método de pago y tendencias mensuales.
    """
    # Usar valores por defecto si no se proporcionan
    fecha_fin = hasta or datetime.now()
    fecha_inicio = desde or (fecha_fin - timedelta(days=30))

    return await obtener_estadisticas_pagos(db=db, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)


@router.get("/reportes/periodo", response_model=ReportePagos)
async def generar_reporte(
    desde: datetime = Query(..., description="Fecha desde (formato YYYY-MM-DDTHH:MM:SS)"),
    hasta: datetime = Query(..., description="Fecha hasta (formato YYYY-MM-DDTHH:MM:SS)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Generar un reporte detallado de pagos por periodo.
    
    Solo administradores pueden acceder a estos reportes.
    Incluye lista de pagos en el periodo y métricas agregadas.
    """
    if hasta < desde:
        raise HTTPException(
            status_code=400, 
            detail="La fecha final debe ser posterior a la fecha inicial"
        )
    
    return await generar_reporte_pagos(db=db, fecha_inicio=desde, fecha_fin=hasta)
