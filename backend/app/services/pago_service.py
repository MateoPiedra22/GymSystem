"""
Módulo de servicios para pagos.

Este módulo contiene la lógica de negocio relacionada con la gestión de pagos de usuarios,
incluyendo operaciones CRUD, cálculos de estadísticas y generación de reportes.
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.pagos import Pago, EstadoPago, MetodoPago
from app.schemas.pagos import PagoCreate, PagoUpdate

async def crear_pago(db: Session, pago: PagoCreate) -> Pago:
    """Crea un nuevo pago en el sistema.
    
    Args:
        db: Sesión activa de base de datos SQLAlchemy.
        pago: Datos del pago a crear, validados según el schema PagoCreate.
        
    Returns:
        Instancia del pago creado con ID asignado y timestamps actualizados.
        
    Raises:
        SQLAlchemyError: Si ocurre un error durante la operación de base de datos.
        ValidationError: Si los datos del pago no son válidos.
        
    Example:
        >>> pago_data = PagoCreate(monto=100.0, usuario_id="123", concepto="MEMBRESIA")
        >>> nuevo_pago = crear_pago(db, pago_data)
        >>> print(nuevo_pago.id)
    """
    db_pago = Pago(**pago.dict())
    db.add(db_pago)
    db.commit()
    db.refresh(db_pago)
    return db_pago

async def obtener_pago(db: Session, pago_id: str) -> Optional[Pago]:
    """Obtiene un pago específico por su identificador único.
    
    Args:
        db: Sesión activa de base de datos SQLAlchemy.
        pago_id: Identificador único del pago (UUID como string).
        
    Returns:
        Instancia del pago si existe, None en caso contrario.
        
    Note:
        Esta función no lanza excepciones si el pago no existe,
        retorna None para permitir validaciones en el código cliente.
    """
    return db.query(Pago).filter(Pago.id == pago_id).first()

async def obtener_pagos(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    usuario_id: Optional[str] = None,
    estado: Optional[EstadoPago] = None,
    metodo_pago: Optional[MetodoPago] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None
) -> List[Pago]:
    """Obtiene una lista paginada de pagos con filtros opcionales.
    
    Args:
        db: Sesión activa de base de datos SQLAlchemy.
        skip: Número de registros a omitir para paginación. Defaults to 0.
        limit: Número máximo de registros a retornar. Defaults to 100.
        usuario_id: Filtro opcional por ID de usuario.
        estado: Filtro opcional por estado del pago.
        metodo_pago: Filtro opcional por método de pago.
        fecha_desde: Filtro opcional de fecha inicio (inclusive).
        fecha_hasta: Filtro opcional de fecha fin (inclusive).
        
    Returns:
        Lista de pagos que cumplen los criterios de filtrado y paginación.
        
    Note:
        Los filtros se aplican con operador AND. Si no se especifica ningún
        filtro, retorna todos los pagos con la paginación aplicada.
    """
    query = db.query(Pago)
    
    # Aplicar filtros si están presentes
    if usuario_id:
        query = query.filter(Pago.usuario_id == usuario_id)
    if estado:
        query = query.filter(Pago.estado == estado)
    if metodo_pago:
        query = query.filter(Pago.metodo_pago == metodo_pago)
    if fecha_desde:
        query = query.filter(Pago.fecha_pago >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Pago.fecha_pago <= fecha_hasta)
    
    return query.order_by(Pago.fecha_pago.desc()).offset(skip).limit(limit).all()

async def actualizar_pago(db: Session, pago_id: str, pago_update: PagoUpdate) -> Optional[Pago]:
    """Actualiza los datos de un pago existente.
    
    Args:
        db: Sesión activa de base de datos SQLAlchemy.
        pago_id: Identificador único del pago a actualizar.
        pago_update: Datos parciales a actualizar, validados según PagoUpdate.
        
    Returns:
        Instancia del pago actualizado si existe, None si no se encuentra.
        
    Note:
        Solo se actualizan los campos proporcionados en pago_update.
        Los campos no especificados mantienen sus valores originales.
    """
    db_pago = await obtener_pago(db, pago_id)
    if db_pago:
        for key, value in pago_update.dict(exclude_unset=True).items():
            setattr(db_pago, key, value)
        db.commit()
        db.refresh(db_pago)
    return db_pago

async def eliminar_pago(db: Session, pago_id: str) -> bool:
    """Elimina un pago del sistema de forma permanente.
    
    Args:
        db: Sesión activa de base de datos SQLAlchemy.
        pago_id: Identificador único del pago a eliminar.
        
    Returns:
        True si el pago fue eliminado exitosamente, False si no existe.
        
    Warning:
        Esta operación es irreversible. Considere marcar el pago como
        "CANCELADO" en lugar de eliminarlo para mantener auditoría.
    """
    db_pago = await obtener_pago(db, pago_id)
    if db_pago:
        db.delete(db_pago)
        db.commit()
        return True
    return False

async def obtener_pagos_usuario(db: Session, usuario_id: str, skip: int = 0, limit: int = 100) -> List[Pago]:
    """Obtiene todos los pagos realizados por un usuario específico.
    
    Args:
        db: Sesión activa de base de datos SQLAlchemy.
        usuario_id: Identificador único del usuario.
        skip: Número de registros a omitir para paginación.
        limit: Número máximo de registros a retornar.
        
    Returns:
        Lista de pagos del usuario ordenados por fecha descendente.
        Lista vacía si el usuario no tiene pagos registrados.
    """
    return (db.query(Pago)
            .filter(Pago.usuario_id == usuario_id)
            .order_by(Pago.fecha_pago.desc())
            .offset(skip).limit(limit)
            .all())

async def obtener_estadisticas_pagos(
    db: Session, 
    fecha_inicio: datetime, 
    fecha_fin: datetime
) -> Dict[str, Union[int, float, datetime]]:
    """Calcula estadísticas de pagos para un período específico.
    
    Args:
        db: Sesión activa de base de datos SQLAlchemy.
        fecha_inicio: Fecha de inicio del período a analizar (inclusive).
        fecha_fin: Fecha de fin del período a analizar (inclusive).
        
    Returns:
        Diccionario con las siguientes métricas:
        - total_pagos: Número total de pagos en el período
        - monto_total: Suma total de montos pagados
        - promedio_diario: Promedio de ingresos por día
        - periodo_inicio: Fecha de inicio del análisis
        - periodo_fin: Fecha de fin del análisis
        
    Raises:
        ValueError: Si fecha_fin es anterior a fecha_inicio.
        
    Example:
        >>> stats = obtener_estadisticas_pagos(
        ...     db, 
        ...     datetime(2024, 1, 1), 
        ...     datetime(2024, 1, 31)
        ... )
        >>> print(f"Total ingresos: ${stats['monto_total']}")
    """
    if fecha_fin < fecha_inicio:
        raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
    
    pagos = db.query(Pago).filter(
        and_(
            Pago.fecha_pago >= fecha_inicio,
            Pago.fecha_pago <= fecha_fin,
            Pago.estado == EstadoPago.PAGADO
        )
    ).all()
    
    total_pagos = len(pagos)
    monto_total = sum(float(pago.monto_final or pago.monto or 0) for pago in pagos)
    
    # Calcular promedio diario
    dias_periodo = (fecha_fin - fecha_inicio).days + 1  # +1 para incluir ambos días
    promedio_diario = monto_total / dias_periodo if dias_periodo > 0 else 0
    
    return {
        "total_pagos": total_pagos,
        "monto_total": round(monto_total, 2),
        "promedio_diario": round(promedio_diario, 2),
        "periodo_inicio": fecha_inicio,
        "periodo_fin": fecha_fin
    }

async def generar_reporte_pagos(
    db: Session, 
    fecha_inicio: datetime, 
    fecha_fin: datetime
) -> Dict[str, Any]:
    """Genera un reporte completo de pagos para un período determinado.
    
    Args:
        db: Sesión activa de base de datos SQLAlchemy.
        fecha_inicio: Fecha de inicio del período del reporte.
        fecha_fin: Fecha de fin del período del reporte.
        
    Returns:
        Diccionario con estructura completa del reporte incluyendo:
        - Metadatos del reporte (título, fecha de generación, período)
        - Estadísticas generales (ver obtener_estadisticas_pagos)
        - Desglose por métodos de pago
        - Desglose por conceptos de pago
        
    Example:
        >>> reporte = generar_reporte_pagos(
        ...     db, 
        ...     datetime(2024, 1, 1), 
        ...     datetime(2024, 1, 31)
        ... )
        >>> print(reporte['titulo'])
        "Reporte de Pagos"
    """
    estadisticas = await obtener_estadisticas_pagos(db, fecha_inicio, fecha_fin)
    
    # Obtener desglose por métodos de pago
    query_metodos = (db.query(Pago.metodo_pago, func.count(), func.sum(Pago.monto_final))
                    .filter(and_(
                        Pago.fecha_pago >= fecha_inicio,
                        Pago.fecha_pago <= fecha_fin,
                        Pago.estado == EstadoPago.PAGADO
                    ))
                    .group_by(Pago.metodo_pago)
                    .all())
    
    desglose_metodos = {
        str(metodo): {"cantidad": cantidad, "monto": float(monto or 0)}
        for metodo, cantidad, monto in query_metodos
    }
    
    return {
        "titulo": "Reporte de Pagos",
        "fecha_generacion": datetime.utcnow(),
        "periodo_inicio": fecha_inicio,
        "periodo_fin": fecha_fin,
        "estadisticas": estadisticas,
        "desglose_metodos_pago": desglose_metodos
    }
