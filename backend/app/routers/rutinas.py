# /backend/app/routers/rutinas.py
"""
Router para gestión de rutinas y ejercicios
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.auth import get_current_user, get_current_admin_user
from app.services.rutina_service import (
    crear_ejercicio, obtener_ejercicio, obtener_ejercicios,
    actualizar_ejercicio, eliminar_ejercicio, crear_rutina,
    obtener_rutina, obtener_rutinas, actualizar_rutina,
    eliminar_rutina, asignar_rutina, obtener_rutinas_usuario,
    actualizar_asignacion_rutina, eliminar_asignacion_rutina,
    registrar_progreso_rutina, obtener_progreso_rutina
)
from app.schemas.rutinas import (
    Ejercicio, EjercicioCreate, EjercicioUpdate, EjercicioResumen,
    Rutina, RutinaCreate, RutinaUpdate, RutinaResumen,
    RutinaUsuario, RutinaUsuarioCreate, RutinaUsuarioUpdate, 
    ProgresoRutina
)
from app.schemas.usuarios import UsuarioInDB as Usuario
from app.core.database import get_db

# Crear router
router = APIRouter(
    tags=["rutinas"],
    responses={404: {"description": "No encontrado"}},
)


# Endpoints para gestión de ejercicios

@router.post("/ejercicios", response_model=Ejercicio, status_code=201)
async def crear_nuevo_ejercicio(
    ejercicio: EjercicioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Crear un nuevo ejercicio en el sistema.
    
    - **nombre**: Nombre del ejercicio
    - **descripcion**: Descripción detallada del ejercicio
    - **categoria**: Categoría principal del ejercicio
    - **instrucciones**: Instrucciones paso a paso
    - **nivel**: Nivel de dificultad
    - **es_compuesto**: Si es un ejercicio compuesto (múltiples grupos musculares)
    - **imagen_url**: URL de la imagen demostrativa (opcional)
    - **video_url**: URL del video demostrativo (opcional)
    - **variaciones**: Lista de variaciones posibles (opcional)
    - **precauciones**: Precauciones o contraindicaciones (opcional)
    - **equipo_necesario**: Lista de equipo necesario (opcional)
    - **musculos_secundarios**: Lista de músculos secundarios (opcional)
    """
    return await crear_ejercicio(db=db, ejercicio=ejercicio)


@router.get("/ejercicios", response_model=List[EjercicioResumen])
async def listar_ejercicios(
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    nivel: Optional[str] = Query(None, description="Filtrar por nivel de dificultad"),
    es_compuesto: Optional[bool] = Query(None, description="Filtrar por ejercicios compuestos"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener lista de ejercicios con opciones de filtrado.
    
    Admite filtrado por categoría, nivel de dificultad y tipo (compuesto/simple).
    """
    return await obtener_ejercicios(
        db=db, 
        skip=skip, 
        limit=limit, 
        categoria=categoria,
        nivel=nivel,
        es_compuesto=es_compuesto
    )


@router.get("/ejercicios/{ejercicio_id}", response_model=Ejercicio)
async def obtener_detalles_ejercicio(
    ejercicio_id: int = Path(..., gt=0, description="ID del ejercicio a consultar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener los detalles completos de un ejercicio específico por su ID.
    """
    ejercicio = await obtener_ejercicio(db, ejercicio_id)
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    return ejercicio


@router.put("/ejercicios/{ejercicio_id}", response_model=Ejercicio)
async def actualizar_datos_ejercicio(
    ejercicio_id: int = Path(..., gt=0, description="ID del ejercicio a actualizar"),
    ejercicio_update: EjercicioUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Actualizar los datos de un ejercicio existente.
    
    Solo administradores pueden actualizar ejercicios.
    """
    ejercicio_existente = await obtener_ejercicio(db, ejercicio_id)
    if not ejercicio_existente:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    return await actualizar_ejercicio(db=db, ejercicio_id=ejercicio_id, ejercicio_update=ejercicio_update)


@router.delete("/ejercicios/{ejercicio_id}", status_code=204)
async def eliminar_ejercicio_existente(
    ejercicio_id: int = Path(..., gt=0, description="ID del ejercicio a eliminar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)  # Solo admins
):
    """
    Eliminar un ejercicio del sistema.
    
    Solo administradores pueden eliminar ejercicios.
    No se podrá eliminar si está siendo utilizado en rutinas.
    """
    ejercicio = await obtener_ejercicio(db, ejercicio_id)
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    await eliminar_ejercicio(db=db, ejercicio_id=ejercicio_id)
    return None


# Endpoints para gestión de rutinas

@router.post("/", response_model=Rutina, status_code=201)
async def crear_nueva_rutina(
    rutina: RutinaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear una nueva rutina en el sistema.
    
    - **nombre**: Nombre de la rutina
    - **descripcion**: Descripción detallada de la rutina
    - **nivel**: Nivel de dificultad
    - **objetivo**: Objetivo principal (hipertrofia, fuerza, etc.)
    - **dias_semana**: Días de la semana recomendados
    - **duracion_estimada_minutos**: Duración estimada en minutos
    - **notas_generales**: Notas generales (opcional)
    - **ejercicios**: Lista de ejercicios que componen la rutina
    - **publico**: Si la rutina es pública o privada
    """
    # Si el usuario no es admin, establecer el creador_id automáticamente
    if not current_user.es_admin:
        rutina.creador_id = current_user.id
    
    return await crear_rutina(db=db, rutina=rutina, usuario=current_user)


@router.get("/", response_model=List[RutinaResumen])
async def listar_rutinas(
    skip: int = Query(0, ge=0, description="Número de registros para saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    nivel: Optional[str] = Query(None, description="Filtrar por nivel de dificultad"),
    objetivo: Optional[str] = Query(None, description="Filtrar por objetivo"),
    solo_publicas: bool = Query(True, description="Mostrar solo rutinas públicas"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener lista de rutinas con opciones de filtrado.
    
    Si solo_publicas es True, muestra rutinas públicas y las creadas por el usuario actual.
    Si el usuario es admin, puede ver todas las rutinas al establecer solo_publicas=False.
    """
    return await obtener_rutinas(
        db=db, 
        skip=skip, 
        limit=limit, 
        nivel=nivel,
        objetivo=objetivo,
        solo_publicas=solo_publicas,
        usuario_actual=current_user
    )


@router.get("/{rutina_id}", response_model=Rutina)
async def obtener_detalles_rutina(
    rutina_id: int = Path(..., gt=0, description="ID de la rutina a consultar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener los detalles completos de una rutina específica por su ID.
    
    Incluye la información completa de los ejercicios asociados.
    Si la rutina es privada, solo el creador y los administradores pueden verla.
    """
    rutina = await obtener_rutina(db, rutina_id)
    if not rutina:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    
    # Verificar permisos para rutinas privadas
    if not rutina.publico and not current_user.es_admin and (not rutina.creador_id or rutina.creador_id != current_user.id):
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para ver esta rutina privada"
        )
    
    return rutina


@router.put("/{rutina_id}", response_model=Rutina)
async def actualizar_datos_rutina(
    rutina_id: int = Path(..., gt=0, description="ID de la rutina a actualizar"),
    rutina_update: RutinaUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualizar los datos de una rutina existente.
    
    Solo el creador y los administradores pueden actualizar rutinas.
    """
    rutina_existente = await obtener_rutina(db, rutina_id)
    if not rutina_existente:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    
    # Verificar permisos
    if not current_user.es_admin and (not rutina_existente.creador_id or rutina_existente.creador_id != current_user.id):
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para actualizar esta rutina"
        )
    
    return await actualizar_rutina(db=db, rutina_id=rutina_id, rutina_update=rutina_update)


@router.delete("/{rutina_id}", status_code=204)
async def eliminar_rutina_existente(
    rutina_id: int = Path(..., gt=0, description="ID de la rutina a eliminar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Eliminar una rutina del sistema.
    
    Solo el creador y los administradores pueden eliminar rutinas.
    """
    rutina = await obtener_rutina(db, rutina_id)
    if not rutina:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    
    # Verificar permisos
    if not current_user.es_admin and (not rutina.creador_id or rutina.creador_id != current_user.id):
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para eliminar esta rutina"
        )
    
    await eliminar_rutina(db=db, rutina_id=rutina_id)
    return None


# Endpoints para asignación de rutinas a usuarios

@router.post("/asignar", response_model=RutinaUsuario, status_code=201)
async def asignar_rutina_usuario(
    asignacion: RutinaUsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Asignar una rutina a un usuario.
    
    - **usuario_id**: ID del usuario
    - **rutina_id**: ID de la rutina
    - **fecha_inicio**: Fecha de inicio de la rutina
    - **fecha_fin**: Fecha de finalización planificada (opcional)
    - **notas**: Notas sobre la asignación (opcional)
    - **asignado_por_id**: ID del usuario que asigna la rutina (opcional)
    
    Los administradores pueden asignar rutinas a cualquier usuario.
    Los usuarios normales solo pueden asignarse rutinas a sí mismos.
    """
    # Verificar permisos
    if not current_user.es_admin and current_user.id != asignacion.usuario_id:
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para asignar rutinas a otros usuarios"
        )
    
    # Si no se especifica quien asigna, establecer el usuario actual
    if not asignacion.asignado_por_id:
        asignacion.asignado_por_id = current_user.id
    
    return await asignar_rutina(db=db, asignacion=asignacion)


@router.get("/usuario/{usuario_id}", response_model=List[RutinaUsuario])
async def listar_rutinas_usuario(
    usuario_id: int = Path(..., gt=0, description="ID del usuario"),
    activas: Optional[bool] = Query(None, description="Filtrar solo rutinas activas/completadas"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener lista de rutinas asignadas a un usuario específico.
    
    Si el usuario no es administrador, solo podrá ver sus propias rutinas.
    """
    # Verificar permisos
    if not current_user.es_admin and usuario_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para ver rutinas de otros usuarios"
        )
    
    return await obtener_rutinas_usuario(db=db, usuario_id=usuario_id, activas=activas)


@router.put("/asignacion/{asignacion_id}", response_model=RutinaUsuario)
async def actualizar_asignacion(
    asignacion_id: int = Path(..., gt=0, description="ID de la asignación a actualizar"),
    asignacion_update: RutinaUsuarioUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualizar los datos de una asignación de rutina.
    
    Permite actualizar fecha de finalización, notas y estado de completado.
    Los administradores pueden actualizar cualquier asignación.
    Los usuarios normales solo pueden actualizar sus propias asignaciones.
    """
    return await actualizar_asignacion_rutina(
        db=db, 
        asignacion_id=asignacion_id, 
        asignacion_update=asignacion_update,
        usuario=current_user
    )


@router.delete("/asignacion/{asignacion_id}", status_code=204)
async def eliminar_asignacion(
    asignacion_id: int = Path(..., gt=0, description="ID de la asignación a eliminar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Eliminar una asignación de rutina.
    
    Los administradores pueden eliminar cualquier asignación.
    Los usuarios normales solo pueden eliminar sus propias asignaciones.
    """
    await eliminar_asignacion_rutina(db=db, asignacion_id=asignacion_id, usuario=current_user)
    return None


# Endpoints para seguimiento de progreso en rutinas

@router.post("/progreso", response_model=ProgresoRutina, status_code=201)
async def registrar_progreso(
    progreso: ProgresoRutina,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registrar progreso en una rutina asignada.
    
    - **usuario_id**: ID del usuario
    - **rutina_usuario_id**: ID de la asignación de rutina
    - **fecha**: Fecha del progreso
    - **ejercicios_completados**: Lista de IDs de ejercicios completados
    - **porcentaje_completado**: Porcentaje de completitud de la sesión
    - **notas**: Notas adicionales (opcional)
    - **carga_incrementada**: Si se incrementó la carga/peso
    - **estado_animo**: Estado de ánimo durante la sesión (1-5)
    - **dificultad_percibida**: Dificultad percibida (1-5)
    """
    # Verificar permisos
    if not current_user.es_admin and current_user.id != progreso.usuario_id:
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para registrar progreso de otros usuarios"
        )
    
    return await registrar_progreso_rutina(db=db, progreso=progreso)


@router.get("/progreso/{rutina_usuario_id}", response_model=List[ProgresoRutina])
async def obtener_progreso(
    rutina_usuario_id: int = Path(..., gt=0, description="ID de la asignación de rutina"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener el historial de progreso de una rutina asignada.
    
    Los administradores pueden ver cualquier progreso.
    Los usuarios normales solo pueden ver su propio progreso.
    """
    return await obtener_progreso_rutina(db=db, rutina_usuario_id=rutina_usuario_id, usuario=current_user)
