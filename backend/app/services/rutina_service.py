"""
Módulo de servicios para rutinas
Contiene la lógica de negocio relacionada con rutinas y ejercicios
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.rutinas import Rutina, Ejercicio, RutinaUsuario, ProgresoRutina
from app.schemas.rutinas import (
    RutinaCreate, RutinaUpdate, EjercicioCreate, EjercicioUpdate,
    RutinaUsuarioCreate, RutinaUsuarioUpdate, ProgresoRutinaCreate
)

# ----- Funciones para ejercicios -----

def obtener_ejercicios(db: Session, skip: int = 0, limit: int = 100) -> List[Ejercicio]:
    """
    Obtiene una lista de ejercicios
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a omitir
        limit: Límite de registros a obtener
        
    Returns:
        Lista de ejercicios
    """
    return db.query(Ejercicio).offset(skip).limit(limit).all()

def obtener_ejercicio(db: Session, ejercicio_id: int) -> Optional[Ejercicio]:
    """
    Obtiene un ejercicio por su ID
    
    Args:
        db: Sesión de base de datos
        ejercicio_id: ID del ejercicio
        
    Returns:
        Ejercicio encontrado o None
    """
    return db.query(Ejercicio).filter(Ejercicio.id == ejercicio_id).first()

def crear_ejercicio(db: Session, ejercicio_create: EjercicioCreate) -> Ejercicio:
    """
    Crea un nuevo ejercicio
    
    Args:
        db: Sesión de base de datos
        ejercicio_create: Datos para crear el ejercicio
        
    Returns:
        Ejercicio creado
    """
    db_ejercicio = Ejercicio(**ejercicio_create.dict())
    db.add(db_ejercicio)
    db.commit()
    db.refresh(db_ejercicio)
    return db_ejercicio

def actualizar_ejercicio(db: Session, ejercicio_id: int, ejercicio_update: EjercicioUpdate) -> Optional[Ejercicio]:
    """
    Actualiza un ejercicio existente
    
    Args:
        db: Sesión de base de datos
        ejercicio_id: ID del ejercicio a actualizar
        ejercicio_update: Datos actualizados
        
    Returns:
        Ejercicio actualizado o None
    """
    db_ejercicio = obtener_ejercicio(db, ejercicio_id)
    if db_ejercicio:
        for key, value in ejercicio_update.dict(exclude_unset=True).items():
            setattr(db_ejercicio, key, value)
        db.commit()
        db.refresh(db_ejercicio)
    return db_ejercicio

def eliminar_ejercicio(db: Session, ejercicio_id: int) -> bool:
    """
    Elimina un ejercicio
    
    Args:
        db: Sesión de base de datos
        ejercicio_id: ID del ejercicio a eliminar
        
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    db_ejercicio = obtener_ejercicio(db, ejercicio_id)
    if db_ejercicio:
        db.delete(db_ejercicio)
        db.commit()
        return True
    return False

# ----- Funciones para rutinas -----

def obtener_rutinas(db: Session, skip: int = 0, limit: int = 100) -> List[Rutina]:
    """
    Obtiene una lista de rutinas
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a omitir
        limit: Límite de registros a obtener
        
    Returns:
        Lista de rutinas
    """
    return db.query(Rutina).offset(skip).limit(limit).all()

def obtener_rutina(db: Session, rutina_id: int) -> Optional[Rutina]:
    """
    Obtiene una rutina por su ID
    
    Args:
        db: Sesión de base de datos
        rutina_id: ID de la rutina
        
    Returns:
        Rutina encontrada o None
    """
    return db.query(Rutina).filter(Rutina.id == rutina_id).first()

def crear_rutina(db: Session, rutina_create: RutinaCreate) -> Rutina:
    """
    Crea una nueva rutina
    
    Args:
        db: Sesión de base de datos
        rutina_create: Datos para crear la rutina
        
    Returns:
        Rutina creada
    """
    db_rutina = Rutina(**rutina_create.dict())
    db.add(db_rutina)
    db.commit()
    db.refresh(db_rutina)
    return db_rutina

def actualizar_rutina(db: Session, rutina_id: int, rutina_update: RutinaUpdate) -> Optional[Rutina]:
    """
    Actualiza una rutina existente
    
    Args:
        db: Sesión de base de datos
        rutina_id: ID de la rutina a actualizar
        rutina_update: Datos actualizados
        
    Returns:
        Rutina actualizada o None
    """
    db_rutina = obtener_rutina(db, rutina_id)
    if db_rutina:
        for key, value in rutina_update.dict(exclude_unset=True).items():
            setattr(db_rutina, key, value)
        db.commit()
        db.refresh(db_rutina)
    return db_rutina

def eliminar_rutina(db: Session, rutina_id: int) -> bool:
    """
    Elimina una rutina
    
    Args:
        db: Sesión de base de datos
        rutina_id: ID de la rutina a eliminar
        
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    db_rutina = obtener_rutina(db, rutina_id)
    if db_rutina:
        db.delete(db_rutina)
        db.commit()
        return True
    return False

# ----- Funciones para asignación de rutinas a usuarios -----

def obtener_rutinas_usuario(db: Session, usuario_id: int) -> List[RutinaUsuario]:
    """
    Obtiene todas las rutinas asignadas a un usuario
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario
        
    Returns:
        Lista de asignaciones de rutinas al usuario
    """
    return db.query(RutinaUsuario).filter(RutinaUsuario.usuario_id == usuario_id).all()

def asignar_rutina(db: Session, asignacion: RutinaUsuarioCreate) -> RutinaUsuario:
    """
    Asigna una rutina a un usuario
    
    Args:
        db: Sesión de base de datos
        asignacion: Datos de la asignación
        
    Returns:
        Objeto RutinaUsuario creado
    """
    db_asignacion = RutinaUsuario(**asignacion.dict())
    db.add(db_asignacion)
    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion

def actualizar_asignacion_rutina(db: Session, asignacion_id: int, 
                                asignacion_update: RutinaUsuarioUpdate) -> Optional[RutinaUsuario]:
    """
    Actualiza una asignación de rutina
    
    Args:
        db: Sesión de base de datos
        asignacion_id: ID de la asignación
        asignacion_update: Datos actualizados
        
    Returns:
        Asignación actualizada o None
    """
    db_asignacion = db.query(RutinaUsuario).filter(RutinaUsuario.id == asignacion_id).first()
    if db_asignacion:
        for key, value in asignacion_update.dict(exclude_unset=True).items():
            setattr(db_asignacion, key, value)
        db.commit()
        db.refresh(db_asignacion)
    return db_asignacion

def eliminar_asignacion_rutina(db: Session, asignacion_id: int) -> bool:
    """
    Elimina una asignación de rutina
    
    Args:
        db: Sesión de base de datos
        asignacion_id: ID de la asignación a eliminar
        
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    db_asignacion = db.query(RutinaUsuario).filter(RutinaUsuario.id == asignacion_id).first()
    if db_asignacion:
        db.delete(db_asignacion)
        db.commit()
        return True
    return False

# ----- Funciones para progreso de rutinas -----

def registrar_progreso_rutina(db: Session, progreso: ProgresoRutinaCreate) -> ProgresoRutina:
    """
    Registra el progreso de un usuario en una rutina
    
    Args:
        db: Sesión de base de datos
        progreso: Datos del progreso
        
    Returns:
        Objeto ProgresoRutina creado
    """
    db_progreso = ProgresoRutina(**progreso.dict())
    db.add(db_progreso)
    db.commit()
    db.refresh(db_progreso)
    return db_progreso

def obtener_progreso_rutina(db: Session, usuario_id: int, rutina_id: Optional[int] = None) -> List[ProgresoRutina]:
    """
    Obtiene el progreso de un usuario en rutinas
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario
        rutina_id: ID de la rutina (opcional)
        
    Returns:
        Lista de registros de progreso
    """
    query = db.query(ProgresoRutina).filter(ProgresoRutina.usuario_id == usuario_id)
    if rutina_id:
        query = query.filter(ProgresoRutina.rutina_id == rutina_id)
    return query.order_by(ProgresoRutina.fecha.desc()).all()
