"""
Router para gestión de tipos de cuota
"""
from typing import List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_admin_user
from app.models.tipos_cuota import TipoCuota
from app.models.usuarios import Usuario
from app.schemas.tipos_cuota import (
    TipoCuotaCreate, TipoCuotaUpdate, TipoCuotaOut, 
    TipoCuotaList, TipoCuotaStats
)

router = APIRouter()

@router.get("/", response_model=TipoCuotaList)
async def listar_tipos_cuota(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    activos_solo: bool = Query(True),
    incluir_promociones: bool = Query(True),
    ordenar_por: str = Query("orden_visualizacion", regex="^(orden_visualizacion|precio|duracion_dias|popularidad)$"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los tipos de cuota disponibles
    No requiere autenticación para poder mostrar en la web pública
    """
    query = db.query(TipoCuota)
    
    # Filtros
    if activos_solo:
        query = query.filter(TipoCuota.activo == True)
    
    if not incluir_promociones:
        query = query.filter(TipoCuota.es_promocion == False)
    
    # Solo mostrar los visibles en web
    query = query.filter(TipoCuota.visible_web == True)
    
    # Contar total
    total = query.count()
    
    # Ordenamiento
    if ordenar_por == "precio":
        query = query.order_by(TipoCuota.precio)
    elif ordenar_por == "duracion_dias":
        query = query.order_by(TipoCuota.duracion_dias)
    elif ordenar_por == "popularidad":
        query = query.order_by(TipoCuota.popularidad.desc())
    else:
        query = query.order_by(TipoCuota.orden_visualizacion)
    
    # Paginación
    tipos = query.offset(skip).limit(limit).all()
    
    # Convertir con campos calculados
    items = []
    for tipo in tipos:
        try:
            item = TipoCuotaOut.from_orm_with_computed(tipo)
            items.append(item)
        except:
            # Fallback si hay problemas con los métodos computados
            item_dict = tipo.__dict__.copy()
            item_dict['duracion_meses'] = round(tipo.duracion_dias / 30) if tipo.duracion_dias else 0
            item_dict['precio_efectivo'] = tipo.precio
            item_dict['descuento_porcentaje'] = 0
            items.append(TipoCuotaOut(**item_dict))
    
    return TipoCuotaList(total=total, items=items)

@router.get("/stats", response_model=TipoCuotaStats)
async def estadisticas_tipos_cuota(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene estadísticas de los tipos de cuota
    """
    total_tipos = db.query(TipoCuota).count()
    tipos_activos = db.query(TipoCuota).filter(TipoCuota.activo == True).count()
    tipos_con_promocion = db.query(TipoCuota).filter(
        TipoCuota.es_promocion == True,
        TipoCuota.activo == True
    ).count()
    
    # Estadísticas de precios
    stats = db.query(
        func.min(TipoCuota.precio).label('min'),
        func.max(TipoCuota.precio).label('max'),
        func.avg(TipoCuota.precio).label('avg')
    ).filter(TipoCuota.activo == True).first()
    
    # Tipo más popular
    tipo_popular = db.query(TipoCuota).filter(
        TipoCuota.activo == True
    ).order_by(TipoCuota.popularidad.desc()).first()
    
    return TipoCuotaStats(
        total_tipos=total_tipos,
        tipos_activos=tipos_activos,
        tipos_con_promocion=tipos_con_promocion,
        precio_minimo=float(stats.min if stats and stats.min is not None else 0),
        precio_maximo=float(stats.max if stats and stats.max is not None else 0),
        precio_promedio=round(float(stats.avg if stats and stats.avg is not None else 0), 2),
        tipo_mas_popular={
            "id": tipo_popular.id,
            "codigo": tipo_popular.codigo,
            "nombre": tipo_popular.nombre,
            "popularidad": tipo_popular.popularidad
        } if tipo_popular else None
    )

@router.get("/{tipo_cuota_id}", response_model=TipoCuotaOut)
async def obtener_tipo_cuota(
    tipo_cuota_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene un tipo de cuota por ID
    No requiere autenticación para poder mostrar en la web pública
    """
    tipo = db.query(TipoCuota).filter(TipoCuota.id == tipo_cuota_id).first()
    
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de cuota no encontrado"
        )
    
    # Incrementar popularidad
    tipo.popularidad = tipo.popularidad + 1
    db.commit()
    
    return TipoCuotaOut.from_orm_with_computed(tipo)

@router.post("/", response_model=TipoCuotaOut)
async def crear_tipo_cuota(
    tipo_cuota: TipoCuotaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Crea un nuevo tipo de cuota (requiere permisos de administrador)
    """
    # Verificar código único
    existing = db.query(TipoCuota).filter(
        TipoCuota.codigo == tipo_cuota.codigo
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un tipo de cuota con ese código"
        )
    
    # Crear tipo de cuota
    db_tipo = TipoCuota(
        **tipo_cuota.dict(),
        id=str(uuid.uuid4()),
        creado_por=current_user.id
    )
    
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    
    return TipoCuotaOut.from_orm_with_computed(db_tipo)

@router.put("/{tipo_cuota_id}", response_model=TipoCuotaOut)
async def actualizar_tipo_cuota(
    tipo_cuota_id: str,
    tipo_cuota: TipoCuotaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Actualiza un tipo de cuota (requiere permisos de administrador)
    """
    db_tipo = db.query(TipoCuota).filter(TipoCuota.id == tipo_cuota_id).first()
    
    if not db_tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de cuota no encontrado"
        )
    
    # Actualizar campos
    update_data = tipo_cuota.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tipo, field, value)
    
    db_tipo.modificado_por = current_user.id
    # ultima_modificacion se actualiza automáticamente con onupdate
    
    db.commit()
    db.refresh(db_tipo)
    
    return TipoCuotaOut.from_orm_with_computed(db_tipo)

@router.delete("/{tipo_cuota_id}")
async def eliminar_tipo_cuota(
    tipo_cuota_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Marca un tipo de cuota como inactivo (requiere permisos de administrador)
    """
    db_tipo = db.query(TipoCuota).filter(TipoCuota.id == tipo_cuota_id).first()
    
    if not db_tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de cuota no encontrado"
        )
    
    # Verificar si tiene pagos asociados
    from app.models.pagos import Pago
    pagos_count = db.query(Pago).filter(Pago.tipo_cuota_id == tipo_cuota_id).count()
    
    if pagos_count > 0:
        # Solo marcar como inactivo si tiene pagos asociados
        db_tipo.activo = False
        db_tipo.visible_web = False
        message = "Tipo de cuota marcado como inactivo (tiene pagos asociados)"
    else:
        # Si no tiene pagos, se puede eliminar físicamente
        db.delete(db_tipo)
        message = "Tipo de cuota eliminado"
    
    db_tipo.modificado_por = current_user.id
    db.commit()
    
    return {"message": message}

@router.post("/{tipo_cuota_id}/activar-promocion")
async def activar_promocion(
    tipo_cuota_id: str,
    precio_promocional: float = Query(..., gt=0),
    fecha_inicio: datetime = Query(...),
    fecha_fin: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Activa una promoción para un tipo de cuota (requiere permisos de administrador)
    """
    db_tipo = db.query(TipoCuota).filter(TipoCuota.id == tipo_cuota_id).first()
    
    if not db_tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de cuota no encontrado"
        )
    
    if precio_promocional >= db_tipo.precio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El precio promocional debe ser menor al precio regular"
        )
    
    if fecha_fin <= fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )
    
    # Activar promoción
    db_tipo.es_promocion = True
    db_tipo.precio_promocional = precio_promocional
    db_tipo.fecha_inicio_promo = fecha_inicio
    db_tipo.fecha_fin_promo = fecha_fin
    db_tipo.modificado_por = current_user.id
    
    db.commit()
    
    return {"message": "Promoción activada exitosamente"} 