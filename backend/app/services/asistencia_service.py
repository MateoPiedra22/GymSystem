"""
Módulo de servicios para asistencias
Contiene la lógica de negocio relacionada con asistencias de usuarios
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.asistencias import Asistencia
from app.schemas.asistencias import AsistenciaCreate, AsistenciaUpdate

async def registrar_asistencia(db: Session, asistencia: AsistenciaCreate) -> Asistencia:
    """
    Registra una nueva asistencia
    
    Args:
        db: Sesión de base de datos
        asistencia: Datos para registrar la asistencia
        
    Returns:
        Asistencia registrada
    """
    # Implementación temporal
    db_asistencia = Asistencia(**asistencia.dict())
    db.add(db_asistencia)
    db.commit()
    db.refresh(db_asistencia)
    return db_asistencia

# Alias para compatibilidad con tests
registrar_entrada = registrar_asistencia

async def obtener_asistencia(db: Session, asistencia_id: int) -> Optional[Asistencia]:
    """
    Obtiene una asistencia por su ID
    
    Args:
        db: Sesión de base de datos
        asistencia_id: ID de la asistencia
        
    Returns:
        Asistencia encontrada o None
    """
    return db.query(Asistencia).filter(Asistencia.id == asistencia_id).first()

async def obtener_asistencias(db: Session, skip: int = 0, limit: int = 100) -> List[Asistencia]:
    """
    Obtiene una lista de asistencias
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a omitir
        limit: Límite de registros a obtener
        
    Returns:
        Lista de asistencias
    """
    return db.query(Asistencia).offset(skip).limit(limit).all()

async def actualizar_asistencia(db: Session, asistencia_id: int, asistencia_update: AsistenciaUpdate) -> Optional[Asistencia]:
    """
    Actualiza una asistencia existente
    
    Args:
        db: Sesión de base de datos
        asistencia_id: ID de la asistencia a actualizar
        asistencia_update: Datos actualizados
        
    Returns:
        Asistencia actualizada o None
    """
    db_asistencia = await obtener_asistencia(db, asistencia_id)
    if db_asistencia:
        for key, value in asistencia_update.dict(exclude_unset=True).items():
            setattr(db_asistencia, key, value)
        db.commit()
        db.refresh(db_asistencia)
    return db_asistencia

async def eliminar_asistencia(db: Session, asistencia_id: int) -> bool:
    """
    Elimina una asistencia
    
    Args:
        db: Sesión de base de datos
        asistencia_id: ID de la asistencia a eliminar
        
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    db_asistencia = await obtener_asistencia(db, asistencia_id)
    if db_asistencia:
        db.delete(db_asistencia)
        db.commit()
        return True
    return False

async def obtener_asistencias_usuario(db: Session, usuario_id: int) -> List[Asistencia]:
    """
    Obtiene todas las asistencias de un usuario
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario
        
    Returns:
        Lista de asistencias del usuario
    """
    return db.query(Asistencia).filter(Asistencia.usuario_id == usuario_id).all()

async def obtener_asistencias_clase(db: Session, clase_id: int) -> List[Asistencia]:
    """
    Obtiene todas las asistencias a una clase
    
    Args:
        db: Sesión de base de datos
        clase_id: ID de la clase
        
    Returns:
        Lista de asistencias a la clase
    """
    return db.query(Asistencia).filter(Asistencia.clase_id == clase_id).all()

async def obtener_estadisticas_asistencias(db: Session, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
    """
    Obtiene estadísticas de asistencias en un período
    
    Args:
        db: Sesión de base de datos
        fecha_inicio: Fecha de inicio del período
        fecha_fin: Fecha de fin del período
        
    Returns:
        Diccionario con estadísticas
    """
    # Implementación temporal
    total_asistencias = db.query(Asistencia).filter(
        and_(
            Asistencia.fecha_hora >= fecha_inicio,
            Asistencia.fecha_hora <= fecha_fin
        )
    ).count()
    
    return {
        "total_asistencias": total_asistencias,
        "periodo_inicio": fecha_inicio,
        "periodo_fin": fecha_fin,
        "promedio_diario": total_asistencias / (fecha_fin - fecha_inicio).days if (fecha_fin - fecha_inicio).days > 0 else 0
    }

async def generar_reporte_asistencias(db: Session, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
    """
    Genera un reporte de asistencias en un período
    
    Args:
        db: Sesión de base de datos
        fecha_inicio: Fecha de inicio del período
        fecha_fin: Fecha de fin del período
        
    Returns:
        Diccionario con datos del reporte
    """
    # Implementación temporal
    estadisticas = await obtener_estadisticas_asistencias(db, fecha_inicio, fecha_fin)
    
    return {
        "titulo": "Reporte de Asistencias",
        "fecha_generacion": datetime.now(),
        "periodo_inicio": fecha_inicio,
        "periodo_fin": fecha_fin,
        "estadisticas": estadisticas
    }
