"""
Módulo de servicios para clases
Contiene la lógica de negocio relacionada con clases y horarios
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func

from app.models.clases import Clase, HorarioClase, NivelDificultad
from app.models.empleados import Empleado
from app.models.usuarios import Usuario
from app.schemas.clases import ClaseCreate, ClaseUpdate, HorarioClaseCreate, HorarioClaseUpdate

# --- Service for Clase (Templates) ---

def get_clase_by_id(db: Session, clase_id: str) -> Optional[Clase]:
    return db.query(Clase).filter(Clase.id == clase_id).first()

def get_clase_by_nombre(db: Session, nombre: str) -> Optional[Clase]:
    return db.query(Clase).filter(func.lower(Clase.nombre) == func.lower(nombre)).first()

def get_clases(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    esta_activa: Optional[bool] = None,
    nivel: Optional[NivelDificultad] = None,
) -> List[Clase]:
    query = db.query(Clase)
    if esta_activa is not None:
        query = query.filter(Clase.esta_activa == esta_activa)
    if nivel:
        query = query.filter(Clase.nivel == nivel)
    return query.order_by(Clase.nombre).offset(skip).limit(limit).all()

def create_clase(db: Session, clase_create: ClaseCreate) -> Clase:
    db_clase = Clase(**clase_create.dict())
    db.add(db_clase)
    db.commit()
    db.refresh(db_clase)
    return db_clase

def update_clase(db: Session, clase_id: str, clase_update: ClaseUpdate) -> Optional[Clase]:
    db_clase = get_clase_by_id(db, clase_id)
    if db_clase:
        update_data = clase_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_clase, key, value)
        db.commit()
        db.refresh(db_clase)
    return db_clase

def delete_clase(db: Session, clase_id: str) -> bool:
    db_clase = get_clase_by_id(db, clase_id)
    if db_clase:
        db.delete(db_clase)
        db.commit()
        return True
    return False

# --- Service for HorarioClase (Schedules) ---

def get_horario_by_id(db: Session, horario_id: str) -> Optional[HorarioClase]:
    return db.query(HorarioClase).options(joinedload(HorarioClase.clase)).filter(HorarioClase.id == horario_id).first()

def get_horarios_for_clase(db: Session, clase_id: str) -> List[HorarioClase]:
    return db.query(HorarioClase).filter(HorarioClase.clase_id == clase_id).order_by(HorarioClase.dia, HorarioClase.hora_inicio).all()

def create_horario_clase(db: Session, horario: HorarioClaseCreate) -> HorarioClase:
    db_horario = HorarioClase(**horario.dict())
    db_horario.plazas_disponibles = db_horario.capacidad_maxima
    db.add(db_horario)
    db.commit()
    db.refresh(db_horario)
    return db_horario

def update_horario_clase(db: Session, horario_id: str, horario_update: HorarioClaseUpdate) -> Optional[HorarioClase]:
    db_horario = get_horario_by_id(db, horario_id)
    if db_horario:
        update_data = horario_update.dict(exclude_unset=True)
        
        # Si cambia la capacidad, ajustar plazas disponibles
        if 'capacidad_maxima' in update_data:
            current_participants = db_horario.capacidad_maxima - db_horario.plazas_disponibles
            new_capacity = update_data['capacidad_maxima']
            if new_capacity < current_participants:
                raise ValueError("La nueva capacidad no puede ser menor que el número de participantes inscritos.")
            db_horario.plazas_disponibles = new_capacity - current_participants

        for key, value in update_data.items():
            setattr(db_horario, key, value)
        
        db.commit()
        db.refresh(db_horario)
    return db_horario

def delete_horario_clase(db: Session, horario_id: str) -> bool:
    db_horario = get_horario_by_id(db, horario_id)
    if db_horario:
        db.delete(db_horario)
        db.commit()
        return True
    return False

def inscribir_usuario_en_horario(db: Session, horario_id: str, usuario_id: str) -> Optional[HorarioClase]:
    db_horario = get_horario_by_id(db, horario_id)
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not db_horario or not db_usuario:
        return None

    if db_horario.plazas_disponibles <= 0:
        raise ValueError("No hay plazas disponibles en esta clase.")
    
    if db_usuario in db_horario.participantes:
        raise ValueError("El usuario ya está inscrito en esta clase.")

    db_horario.participantes.append(db_usuario)
    db_horario.plazas_disponibles -= 1  # type: ignore
    db.commit()
    db.refresh(db_horario)
    return db_horario

def dar_de_baja_usuario_de_horario(db: Session, horario_id: str, usuario_id: str) -> Optional[HorarioClase]:
    db_horario = get_horario_by_id(db, horario_id)
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not db_horario or not db_usuario:
        return None

    if db_usuario not in db_horario.participantes:
        raise ValueError("El usuario no está inscrito en esta clase.")

    db_horario.participantes.remove(db_usuario)
    db_horario.plazas_disponibles += 1  # type: ignore
    db.commit()
    db.refresh(db_horario)
    return db_horario

# --- Complex Queries ---

def get_clases_con_asistencias(db: Session, fecha_inicio: datetime, fecha_fin: datetime):
    # NOTA: Esta es una implementación compleja. La lógica para contar asistencias
    # y calcular porcentajes de ocupación dependería del modelo Asistencia,
    # que no está en el alcance de esta refactorización inmediata.
    # Se deja una implementación básica que retorna las clases.
    # Para una implementación real se necesitaría un JOIN con la tabla de asistencias.
    clases = get_clases(db, limit=1000)
    resultados = []
    for clase in clases:
        resultados.append({
            "id": clase.id,
            "nombre": clase.nombre,
            "nivel": clase.nivel,
            "duracion_minutos": clase.duracion_minutos,
            "esta_activa": clase.esta_activa,
            "total_asistencias": 0, # Placeholder
            "porcentaje_ocupacion": 0.0, # Placeholder
            "asistencias_por_dia": {}, # Placeholder
            "horarios": clase.horarios
        })
    return resultados
