# /backend/app/routers/clases.py
"""
Router para gestión de clases y horarios
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import time

from app.core.auth import get_current_user, get_current_admin_user
from app.services import clase_service
from app.models.clases import NivelDificultad
from app.schemas.clases import (
    Clase, ClaseCreate, ClaseUpdate, ClaseResumen,
    HorarioClase, HorarioClaseCreate, HorarioClaseUpdate,
    ClaseConAsistencias
)
from app.schemas.usuarios import UsuarioInDB as Usuario
from app.core.database import get_db

# Crear router
router = APIRouter(
    tags=["clases"],
    responses={404: {"description": "No encontrado"}},
)


@router.post("/", response_model=Clase, status_code=201)
def crear_nueva_clase(
    clase: ClaseCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Crear una nueva clase en el sistema.
    
    - **nombre**: Nombre de la clase
    - **descripcion**: Descripción detallada de la clase
    - **duracion_minutos**: Duración de la clase en minutos
    - **nivel**: Nivel de dificultad (principiante, intermedio, avanzado)
    - **esta_activa**: Si la clase está activa (por defecto es verdadero)
    """
    return clase_service.create_clase(db=db, clase_create=clase)


@router.get("/", response_model=List[ClaseResumen])
def listar_clases(
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    esta_activa: Optional[bool] = Query(None, description="Filtrar solo clases activas/inactivas"),
    nivel: Optional[str] = Query(None, description="Filtrar por nivel de dificultad"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener lista de clases con opciones de filtrado.
    
    Admite filtrado por estado (activas/inactivas) y nivel de dificultad.
    """
    nivel_enum: Optional[NivelDificultad] = None
    if nivel:
        try:
            nivel_enum = NivelDificultad(nivel)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{nivel}' no es un nivel de dificultad válido. Use uno de: {[e.value for e in NivelDificultad]}."
            )

    return clase_service.get_clases(
        db=db, 
        skip=skip, 
        limit=limit, 
        esta_activa=esta_activa,
        nivel=nivel_enum,
    )


@router.get("/{clase_id}", response_model=Clase)
def obtener_detalles_clase(
    clase_id: str = Path(..., description="ID de la clase a consultar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener los detalles completos de una clase específica por su ID.
    
    Incluye la información de los horarios asociados.
    """
    clase = clase_service.get_clase_by_id(db, clase_id)
    if not clase:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    
    return clase


@router.put("/{clase_id}", response_model=Clase)
def actualizar_datos_clase(
    clase_id: str = Path(..., description="ID de la clase a actualizar"),
    clase_update: ClaseUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Actualizar los datos de una clase existente.
    
    Solo administradores pueden actualizar clases.
    """
    clase_existente = clase_service.get_clase_by_id(db, clase_id)
    if not clase_existente:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    
    return clase_service.update_clase(db=db, clase_id=clase_id, clase_update=clase_update)


@router.delete("/{clase_id}", status_code=204)
def eliminar_clase_existente(
    clase_id: str = Path(..., description="ID de la clase a eliminar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Eliminar una clase del sistema.
    
    Solo administradores pueden eliminar clases.
    Esto eliminará también todos los horarios asociados.
    """
    clase = clase_service.get_clase_by_id(db, clase_id)
    if not clase:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    
    clase_service.delete_clase(db=db, clase_id=clase_id)
    return None


# Endpoints para gestión de horarios de clases

@router.post("/{clase_id}/horarios", response_model=HorarioClase, status_code=201)
def crear_nuevo_horario(
    clase_id: str = Path(..., description="ID de la clase"),
    horario: HorarioClaseCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Crear un nuevo horario para una clase existente.
    
    - **dia**: Día de la semana (lunes, martes, etc.)
    - **hora_inicio**: Hora de inicio (formato HH:MM)
    - **salon**: Salón o ubicación de la clase
    """
    # Verificar que la clase exista
    clase = clase_service.get_clase_by_id(db, clase_id)
    if not clase:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    
    # Verificar que la clase_id en el horario coincida con la URL
    if horario.clase_id != clase_id:
        raise HTTPException(
            status_code=400, 
            detail="El ID de clase en el horario no coincide con el ID de la URL"
        )
    
    return clase_service.create_horario_clase(db=db, horario=horario)


@router.get("/{clase_id}/horarios", response_model=List[HorarioClase])
def listar_horarios_clase(
    clase_id: str = Path(..., description="ID de la clase"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener todos los horarios de una clase específica.
    """
    # Verificar que la clase exista
    clase = clase_service.get_clase_by_id(db, clase_id)
    if not clase:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    
    return clase_service.get_horarios_for_clase(db=db, clase_id=clase_id)


@router.get("/horarios/{horario_id}", response_model=HorarioClase)
def obtener_detalles_horario(
    horario_id: str = Path(..., description="ID del horario a consultar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener los detalles de un horario específico por su ID.
    """
    horario = clase_service.get_horario_by_id(db, horario_id)
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    return horario


@router.put("/horarios/{horario_id}", response_model=HorarioClase)
def actualizar_datos_horario(
    horario_id: str = Path(..., description="ID del horario a actualizar"),
    horario_update: HorarioClaseUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Actualizar los datos de un horario existente.
    
    Solo administradores pueden actualizar horarios.
    """
    horario_existente = clase_service.get_horario_by_id(db, horario_id)
    if not horario_existente:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    return clase_service.update_horario_clase(db=db, horario_id=horario_id, horario_update=horario_update)


@router.delete("/horarios/{horario_id}", status_code=204)
def eliminar_horario_existente(
    horario_id: str = Path(..., description="ID del horario a eliminar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Eliminar un horario de clase del sistema.
    
    Solo administradores pueden eliminar horarios.
    """
    horario = clase_service.get_horario_by_id(db, horario_id)
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    clase_service.delete_horario_clase(db=db, horario_id=horario_id)
    return None


@router.get("/estadisticas/asistencias", response_model=List[ClaseConAsistencias])
def obtener_clases_con_estadisticas(
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Obtener estadísticas de asistencia para todas las clases.
    
    Solo administradores pueden acceder a estas estadísticas.
    Incluye total de asistencias, porcentaje de ocupación y distribución por día.
    """
    from datetime import datetime, timedelta
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=30)
    return clase_service.get_clases_con_asistencias(db=db, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
