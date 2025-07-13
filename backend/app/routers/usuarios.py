"""
Router para operaciones con usuarios
"""
from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioOut, ChangePassword
from app.models.usuarios import Usuario
from app.core.auth import get_current_user, get_current_admin_user, get_password_hash, verify_password
from app.core.database import get_db

router = APIRouter()

def _apply_active_filter(query, active_only: bool):
    """Aplica filtro de usuarios activos"""
    if active_only:
        return query.filter(Usuario.esta_activo == True)
    return query

def _apply_search_filter(query, search: str):
    """Aplica filtro de búsqueda en usuarios"""
    if not search:
        return query
    
    search_term = f"%{search}%"
    return query.filter(
        or_(
            Usuario.nombre.ilike(search_term),
            Usuario.apellido.ilike(search_term),
            Usuario.email.ilike(search_term),
            Usuario.username.ilike(search_term)
        )
    )

def _apply_pagination(query, skip: int, limit: int):
    """Aplica paginación a la consulta"""
    return query.offset(skip).limit(limit)

@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UsuarioCreate,
    current_user: Annotated[Usuario, Depends(get_current_admin_user)],
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo usuario (solo admin)
    """
    # Validación específica de permisos por operación
    if not current_user.es_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador para crear usuarios"
        )
    
    # Verificar si el username o email ya existe
    user_exists = db.query(Usuario).filter(
        or_(
            Usuario.username == user_data.username,
            Usuario.email == user_data.email
        )
    ).first()
    
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario o email ya está en uso"
        )
    
    # Generar hash de la contraseña
    hashed_password = get_password_hash(user_data.password)
    
    # Crear objeto de usuario
    new_user = Usuario(
        username=user_data.username,
        email=user_data.email,
        nombre=user_data.nombre,
        apellido=user_data.apellido,
        fecha_nacimiento=user_data.fecha_nacimiento,
        telefono=user_data.telefono,
        direccion=user_data.direccion,
        objetivo=user_data.objetivo,
        notas=user_data.notas,
        peso_inicial=user_data.peso_inicial,
        altura=user_data.altura,
        hashed_password=hashed_password,
        es_admin=user_data.es_admin
    )
    
    # Guardar en la base de datos
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.get("/", response_model=List[UsuarioOut])
async def get_users(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = True
):
    """
    Obtiene la lista de usuarios con consultas optimizadas
    """
    # Construir la query base con índices optimizados
    query = db.query(Usuario)
    
    # Aplicar filtros usando funciones auxiliares
    query = _apply_active_filter(query, active_only)
    query = _apply_search_filter(query, search)
    
    # Aplicar paginación y ordenamiento
    query = _apply_pagination(query, skip, limit)
    users = query.order_by(Usuario.nombre, Usuario.apellido).all()
    
    return users

@router.get("/{user_id}", response_model=UsuarioOut)
async def get_user(
    user_id: str,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Obtiene un usuario por su ID
    """
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return user

@router.put("/{user_id}", response_model=UsuarioOut)
async def update_user(
    user_id: str,
    user_data: UsuarioUpdate,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Actualiza los datos de un usuario
    """
    # Verificar permisos (solo admin o el propio usuario)
    if current_user.es_admin is not True and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar este usuario"
        )
    
    # Buscar el usuario a actualizar
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar los campos proporcionados
    user_data_dict = user_data.dict(exclude_unset=True)
    for key, value in user_data_dict.items():
        setattr(user, key, value)
    
    # Guardar cambios
    db.commit()
    db.refresh(user)
    
    return user

@router.post("/{user_id}/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    user_id: str,
    password_data: ChangePassword,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Cambia la contraseña de un usuario
    """
    # Verificar permisos (solo admin o el propio usuario)
    if current_user.es_admin is not True and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cambiar la contraseña de este usuario"
        )
    
    # Buscar el usuario
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar contraseña actual (excepto para admin)
    if current_user.es_admin is not True:
        if verify_password(password_data.current_password, user.hashed_password) is not True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta"
            )
    
    # Generar nuevo hash
    hashed_password = get_password_hash(password_data.new_password)
    
    # Actualizar contraseña
    user.hashed_password = hashed_password
    
    # Guardar cambios
    db.commit()
    
    return {"detail": "Contraseña actualizada correctamente"}
