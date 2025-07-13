"""
Router para gestión de empleados
"""
from typing import List, Optional, Annotated
from datetime import datetime, date
import uuid
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_admin_user
from app.models.empleados import Empleado, AsistenciaEmpleado, Nomina, EstadoEmpleado
from app.models.usuarios import Usuario
from app.schemas.empleados import (
    EmpleadoCreate, EmpleadoUpdate, EmpleadoOut, EmpleadoList,
    AsistenciaEmpleadoCreate, AsistenciaEmpleadoUpdate, AsistenciaEmpleadoOut,
    NominaCreate, NominaUpdate, NominaOut
)
from app.utils.pagination import paginate, apply_filters

router = APIRouter()

# Endpoints para empleados

@router.get("/", response_model=EmpleadoList)
async def listar_empleados(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    departamento: Optional[str] = None,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todos los empleados con filtros opcionales
    """
    query = db.query(Empleado)
    
    # Aplicar filtros
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Empleado.nombre.ilike(search_filter),
                Empleado.apellido.ilike(search_filter),
                Empleado.numero_empleado.ilike(search_filter),
                Empleado.dni.ilike(search_filter),
                Empleado.email.ilike(search_filter)
            )
        )
    
    if departamento:
        query = query.filter(Empleado.departamento == departamento)
    
    if estado:
        query = query.filter(Empleado.estado == estado)
    
    # Aplicar filtros y paginación usando utilitario
    filtros_dict = {
        'search': search,
        'departamento': departamento,
        'estado': estado
    }
    query = apply_filters(query, filtros_dict)
    total, empleados = paginate(query, skip=skip, limit=limit)
    
    # Convertir a schema con campos calculados
    return EmpleadoList(
        total=total,
        items=[
            EmpleadoOut(**{
                **EmpleadoOut.from_orm(emp).dict(),
                'edad': emp.edad,
                'antiguedad_anos': emp.antiguedad_anos,
                'nombre_completo': emp.nombre_completo
            }) for emp in empleados
        ]
    )

@router.get("/{empleado_id}", response_model=EmpleadoOut)
async def obtener_empleado(
    empleado_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un empleado por ID
    """
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado"
        )
    
    # Convertir con campos calculados
    emp_dict = EmpleadoOut.from_orm(empleado).dict()
    emp_dict['edad'] = empleado.edad
    emp_dict['antiguedad_anos'] = empleado.antiguedad_anos
    emp_dict['nombre_completo'] = empleado.nombre_completo
    
    return EmpleadoOut(**emp_dict)

@router.post("/", response_model=EmpleadoOut)
async def crear_empleado(
    empleado: EmpleadoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Crea un nuevo empleado (requiere permisos de administrador)
    """
    # Verificar que no exista el DNI
    existing = db.query(Empleado).filter(
        or_(
            Empleado.dni == empleado.dni,
            Empleado.email == empleado.email
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un empleado con ese DNI o email"
        )
    
    # Generar número de empleado
    year = datetime.now().year
    count = db.query(Empleado).filter(
        Empleado.numero_empleado.like(f"EMP-{year}-%")
    ).count() + 1
    numero_empleado = f"EMP-{year}-{count:03d}"
    
    # Crear empleado
    db_empleado = Empleado(
        **empleado.dict(exclude={'certificaciones'}),
        id=str(uuid.uuid4()),
        numero_empleado=numero_empleado,
        estado=EstadoEmpleado.ACTIVO,
        certificaciones=json.dumps(empleado.certificaciones or []),
        creado_por=current_user.id
    )
    
    db.add(db_empleado)
    db.commit()
    db.refresh(db_empleado)
    
    # Convertir con campos calculados
    emp_dict = EmpleadoOut.from_orm(db_empleado).dict()
    emp_dict['edad'] = db_empleado.edad
    emp_dict['antiguedad_anos'] = db_empleado.antiguedad_anos
    emp_dict['nombre_completo'] = db_empleado.nombre_completo
    
    return EmpleadoOut(**emp_dict)

@router.put("/{empleado_id}", response_model=EmpleadoOut)
async def actualizar_empleado(
    empleado_id: str,
    empleado: EmpleadoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Actualiza un empleado (requiere permisos de administrador)
    """
    db_empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    
    if not db_empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado"
        )
    
    # Verificar email único si se está actualizando
    if empleado.email and empleado.email != db_empleado.email:
        existing = db.query(Empleado).filter(
            Empleado.email == empleado.email,
            Empleado.id != empleado_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro empleado con ese email"
            )
    
    # Actualizar campos
    update_data = empleado.dict(exclude_unset=True)
    if 'certificaciones' in update_data and update_data['certificaciones'] is not None:
        update_data['certificaciones'] = json.dumps(update_data['certificaciones'])
    
    for field, value in update_data.items():
        setattr(db_empleado, field, value)
    
    db_empleado.modificado_por = current_user.id
    db.commit()
    db.refresh(db_empleado)
    
    # Convertir con campos calculados
    emp_dict = EmpleadoOut.from_orm(db_empleado).dict()
    emp_dict['edad'] = db_empleado.edad
    emp_dict['antiguedad_anos'] = db_empleado.antiguedad_anos
    emp_dict['nombre_completo'] = db_empleado.nombre_completo
    
    return EmpleadoOut(**emp_dict)

@router.delete("/{empleado_id}")
async def eliminar_empleado(
    empleado_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Marca un empleado como inactivo (requiere permisos de administrador)
    """
    db_empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    
    if not db_empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado"
        )
    
    # No eliminar físicamente, solo marcar como inactivo
    db_empleado.estado = EstadoEmpleado.INACTIVO.value
    db_empleado.fecha_salida = date.today()
    db_empleado.modificado_por = current_user.id
    
    db.commit()
    
    return {"message": "Empleado marcado como inactivo"}

# Endpoints para asistencia de empleados

@router.post("/asistencia/entrada", response_model=AsistenciaEmpleadoOut)
async def registrar_entrada(
    asistencia: AsistenciaEmpleadoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registra la entrada de un empleado
    """
    # Verificar que el empleado existe
    empleado = db.query(Empleado).filter(Empleado.id == asistencia.empleado_id).first()
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado"
        )
    
    # Verificar que no haya una entrada sin salida
    entrada_abierta = db.query(AsistenciaEmpleado).filter(
        AsistenciaEmpleado.empleado_id == asistencia.empleado_id,
        AsistenciaEmpleado.fecha == asistencia.fecha,
        AsistenciaEmpleado.hora_salida.is_(None)
    ).first()
    
    if entrada_abierta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El empleado ya tiene una entrada registrada sin salida"
        )
    
    # Crear registro de asistencia
    db_asistencia = AsistenciaEmpleado(
        **asistencia.dict(),
        id=str(uuid.uuid4()),
        registrado_por=current_user.id
    )
    
    db.add(db_asistencia)
    db.commit()
    db.refresh(db_asistencia)
    
    # Cargar relación
    db_asistencia.empleado = empleado
    
    return db_asistencia

@router.put("/asistencia/{asistencia_id}/salida", response_model=AsistenciaEmpleadoOut)
async def registrar_salida(
    asistencia_id: str,
    salida: AsistenciaEmpleadoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registra la salida de un empleado
    """
    db_asistencia = db.query(AsistenciaEmpleado).filter(
        AsistenciaEmpleado.id == asistencia_id
    ).first()
    
    if not db_asistencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de asistencia no encontrado"
        )
    
    if db_asistencia.hora_salida is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya se registró la salida para esta asistencia"
        )
    
    # Actualizar salida
    db_asistencia.hora_salida = salida.hora_salida
    if salida.observaciones:
        db_asistencia.observaciones = salida.observaciones
    
    # Calcular horas trabajadas
    delta = salida.hora_salida - db_asistencia.hora_entrada
    horas = delta.total_seconds() / 3600
    db_asistencia.horas_trabajadas = round(horas, 2)
    
    # Calcular horas extra (asumiendo 8 horas normales)
    if horas > 8:
        db_asistencia.horas_extra = round(horas - 8, 2)
    
    db.commit()
    db.refresh(db_asistencia)
    
    # Cargar relación
    db_asistencia.empleado
    
    return db_asistencia

@router.get("/asistencia/reporte")
async def reporte_asistencia(
    empleado_id: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera un reporte de asistencias
    """
    query = db.query(AsistenciaEmpleado)
    
    if empleado_id:
        query = query.filter(AsistenciaEmpleado.empleado_id == empleado_id)
    
    if fecha_inicio:
        query = query.filter(AsistenciaEmpleado.fecha >= fecha_inicio)
    
    if fecha_fin:
        query = query.filter(AsistenciaEmpleado.fecha <= fecha_fin)
    
    asistencias = query.all()
    
    # Calcular estadísticas
    total_dias = len(set(a.fecha for a in asistencias))
    total_horas = sum(float(a.horas_trabajadas or 0) for a in asistencias)
    total_horas_extra = sum(float(a.horas_extra or 0) for a in asistencias)
    
    return {
        "total_registros": len(asistencias),
        "total_dias": total_dias,
        "total_horas": round(total_horas, 2),
        "total_horas_extra": round(total_horas_extra, 2),
        "promedio_horas_dia": round(total_horas / total_dias, 2) if total_dias > 0 else 0
    }

# Endpoints para nómina

@router.post("/nomina", response_model=NominaOut)
async def generar_nomina(
    nomina: NominaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Genera una nómina para un empleado (requiere permisos de administrador)
    """
    # Verificar que el empleado existe
    empleado = db.query(Empleado).filter(Empleado.id == nomina.empleado_id).first()
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado"
        )
    
    # Verificar que no exista nómina para el mismo periodo
    existing = db.query(Nomina).filter(
        Nomina.empleado_id == nomina.empleado_id,
        Nomina.mes == nomina.mes,
        Nomina.anio == nomina.anio
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una nómina para este empleado en el periodo indicado"
        )
    
    # Calcular totales
    total_ingresos = (
        nomina.salario_base +
        nomina.horas_extra +
        nomina.comisiones +
        nomina.bonos +
        nomina.otros_ingresos
    )
    
    total_deducciones = (
        nomina.seguro_social +
        nomina.impuestos +
        nomina.prestamos +
        nomina.otras_deducciones
    )
    
    salario_neto = total_ingresos - total_deducciones
    
    # Crear nómina
    db_nomina = Nomina(
        **nomina.dict(),
        id=str(uuid.uuid4()),
        total_ingresos=total_ingresos,
        total_deducciones=total_deducciones,
        salario_neto=salario_neto,
        generado_por=current_user.id
    )
    
    db.add(db_nomina)
    db.commit()
    db.refresh(db_nomina)
    
    # Cargar relación
    db_nomina.empleado = empleado
    
    return db_nomina

@router.get("/nomina/empleado/{empleado_id}")
async def listar_nominas_empleado(
    empleado_id: str,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista las nóminas de un empleado
    """
    query = db.query(Nomina).filter(Nomina.empleado_id == empleado_id)
    
    if anio:
        query = query.filter(Nomina.anio == anio)
    
    nominas = query.order_by(Nomina.anio.desc(), Nomina.mes.desc()).all()
    
    return nominas

@router.put("/nomina/{nomina_id}/aprobar", response_model=NominaOut)
async def aprobar_nomina(
    nomina_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Aprueba una nómina (requiere permisos de administrador)
    """
    db_nomina = db.query(Nomina).filter(Nomina.id == nomina_id).first()
    
    if not db_nomina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nómina no encontrada"
        )
    
    if db_nomina.estado != "PENDIENTE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden aprobar nóminas pendientes"
        )
    
    db_nomina.estado = "PAGADA"
    db_nomina.fecha_aprobacion = datetime.utcnow()
    db_nomina.aprobado_por = current_user.id
    
    db.commit()
    db.refresh(db_nomina)
    
    # Cargar relación
    db_nomina.empleado
    
    return db_nomina

# Endpoint para subir foto del empleado
@router.post("/{empleado_id}/foto")
async def subir_foto_empleado(
    empleado_id: str,
    foto: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Sube la foto de un empleado (requiere permisos de administrador)
    """
    # Verificar que el empleado existe
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado"
        )
    
    # Validar tipo de archivo
    if not foto.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser una imagen"
        )
    
    # TODO: Implementar guardado de archivo y actualización de URL
    # Por ahora solo retornamos éxito
    
    return {"message": "Foto subida exitosamente"} 