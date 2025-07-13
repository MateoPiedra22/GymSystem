"""
Servicio para gestión completa de empleados y recursos humanos
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract

from app.models.empleados import (
    Empleado, AsistenciaEmpleado, Nomina, SolicitudVacaciones,
    EvaluacionDesempeno, RegistroCapacitacion, SolicitudPermiso,
    HorarioTrabajo, ReemplazoEmpleado, EstadoEmpleado, Departamento
)
from app.schemas.empleados import (
    EmpleadoCreate, EmpleadoUpdate, AsistenciaEmpleadoCreate,
    SolicitudVacacionesCreate, EvaluacionDesempenoCreate,
    RegistroCapacitacionCreate, SolicitudPermisoCreate,
    HorarioTrabajoCreate, ReemplazoEmpleadoCreate
)

class EmpleadosService:
    """Servicio principal para gestión de empleados"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # CRUD básico de empleados
    
    def crear_empleado(self, empleado_data: EmpleadoCreate) -> Empleado:
        """Crear un nuevo empleado"""
        # Generar número de empleado único
        year = datetime.now().year
        count = self.db.query(Empleado).count() + 1
        numero_empleado = f"EMP-{year}-{count:04d}"
        
        db_empleado = Empleado(
            numero_empleado=numero_empleado,
            **empleado_data.dict()
        )
        
        self.db.add(db_empleado)
        self.db.commit()
        self.db.refresh(db_empleado)
        return db_empleado
    
    def obtener_empleado(self, empleado_id: str) -> Optional[Empleado]:
        """Obtener empleado por ID"""
        return self.db.query(Empleado).filter(Empleado.id == empleado_id).first()
    
    def obtener_empleados(
        self, 
        skip: int = 0, 
        limit: int = 100,
        departamento: Optional[str] = None,
        estado: Optional[str] = None,
        activos_solamente: bool = True
    ) -> List[Empleado]:
        """Obtener lista de empleados con filtros"""
        query = self.db.query(Empleado)
        
        if activos_solamente:
            query = query.filter(Empleado.estado == EstadoEmpleado.ACTIVO)
        
        if departamento:
            query = query.filter(Empleado.departamento == departamento)
        
        if estado:
            query = query.filter(Empleado.estado == estado)
        
        return query.offset(skip).limit(limit).all()
    
    def actualizar_empleado(self, empleado_id: str, empleado_data: EmpleadoUpdate) -> Optional[Empleado]:
        """Actualizar empleado"""
        db_empleado = self.obtener_empleado(empleado_id)
        if not db_empleado:
            return None
        
        for field, value in empleado_data.dict(exclude_unset=True).items():
            setattr(db_empleado, field, value)
        
        self.db.commit()
        self.db.refresh(db_empleado)
        return db_empleado
    
    def desactivar_empleado(self, empleado_id: str, fecha_salida: Optional[date] = None) -> bool:
        """Desactivar empleado (terminación de contrato)"""
        db_empleado = self.obtener_empleado(empleado_id)
        if not db_empleado:
            return False
        
        db_empleado.estado = EstadoEmpleado.INACTIVO
        db_empleado.fecha_salida = fecha_salida or date.today()
        
        self.db.commit()
        return True
    
    # Gestión de asistencias
    
    def registrar_entrada(self, empleado_id: str, fecha_hora: Optional[datetime] = None) -> AsistenciaEmpleado:
        """Registrar entrada de empleado"""
        fecha_hora = fecha_hora or datetime.now()
        fecha = fecha_hora.date()
        
        # Verificar si ya hay registro para hoy
        asistencia_existente = self.db.query(AsistenciaEmpleado).filter(
            and_(
                AsistenciaEmpleado.empleado_id == empleado_id,
                AsistenciaEmpleado.fecha == fecha
            )
        ).first()
        
        if asistencia_existente:
            # Si ya hay registro, actualizar hora de entrada si es más temprana
            if not asistencia_existente.hora_entrada or fecha_hora < asistencia_existente.hora_entrada:
                asistencia_existente.hora_entrada = fecha_hora
                self.db.commit()
                return asistencia_existente
            return asistencia_existente
        else:
            # Crear nuevo registro
            asistencia = AsistenciaEmpleado(
                empleado_id=empleado_id,
                fecha=fecha,
                hora_entrada=fecha_hora,
                estado="PRESENTE"
            )
            
            # Verificar si llegó tarde
            empleado = self.obtener_empleado(empleado_id)
            if empleado and empleado.horario_entrada:
                try:
                    hora_entrada_esperada = datetime.strptime(str(empleado.horario_entrada), "%H:%M").time()
                    if fecha_hora.time() > hora_entrada_esperada:
                        asistencia.estado = "TARDE"
                except ValueError:
                    pass  # Si no se puede parsear la hora, ignorar
            
            self.db.add(asistencia)
            self.db.commit()
            self.db.refresh(asistencia)
            return asistencia
    
    def registrar_salida(self, empleado_id: str, fecha_hora: Optional[datetime] = None) -> Optional[AsistenciaEmpleado]:
        """Registrar salida de empleado"""
        fecha_hora = fecha_hora or datetime.now()
        fecha = fecha_hora.date()
        
        asistencia = self.db.query(AsistenciaEmpleado).filter(
            and_(
                AsistenciaEmpleado.empleado_id == empleado_id,
                AsistenciaEmpleado.fecha == fecha
            )
        ).first()
        
        if not asistencia:
            return None
        
        asistencia.hora_salida = fecha_hora
        
        # Calcular horas trabajadas
        if asistencia.hora_entrada:
            delta = fecha_hora - asistencia.hora_entrada
            asistencia.horas_trabajadas = delta.total_seconds() / 3600
            
            # Calcular horas extra si aplica
            empleado = self.obtener_empleado(empleado_id)
            if empleado and empleado.horario_salida:
                try:
                    hora_salida_esperada = datetime.strptime(str(empleado.horario_salida), "%H:%M").time()
                    if fecha_hora.time() > hora_salida_esperada:
                        horas_regulares = 8  # Asumimos 8 horas regulares
                        if asistencia.horas_trabajadas and asistencia.horas_trabajadas > horas_regulares:
                            asistencia.horas_extra = asistencia.horas_trabajadas - horas_regulares
                except ValueError:
                    pass  # Si no se puede parsear la hora, ignorar
        
        self.db.commit()
        self.db.refresh(asistencia)
        return asistencia
    
    def obtener_asistencias_empleado(
        self, 
        empleado_id: str, 
        fecha_inicio: date, 
        fecha_fin: date
    ) -> List[AsistenciaEmpleado]:
        """Obtener asistencias de un empleado en un período"""
        return self.db.query(AsistenciaEmpleado).filter(
            and_(
                AsistenciaEmpleado.empleado_id == empleado_id,
                AsistenciaEmpleado.fecha >= fecha_inicio,
                AsistenciaEmpleado.fecha <= fecha_fin
            )
        ).order_by(AsistenciaEmpleado.fecha.desc()).all()
    
    def calcular_horas_totales(self, empleado_id: str, mes: int, ano: int) -> Dict[str, float]:
        """Calcular horas totales de un empleado en un mes"""
        inicio_mes = date(ano, mes, 1)
        fin_mes = date(ano, mes + 1, 1) - timedelta(days=1) if mes < 12 else date(ano, 12, 31)
        
        asistencias = self.obtener_asistencias_empleado(empleado_id, inicio_mes, fin_mes)
        
        horas_regulares = sum(a.horas_trabajadas or 0 for a in asistencias if a.horas_trabajadas)
        horas_extra = sum(a.horas_extra or 0 for a in asistencias if a.horas_extra)
        
        return {
            "horas_regulares": horas_regulares,
            "horas_extra": horas_extra,
            "horas_totales": horas_regulares + horas_extra,
            "dias_trabajados": len([a for a in asistencias if a.estado == "PRESENTE" or a.estado == "TARDE"])
        }
    
    # Gestión de solicitudes de vacaciones
    
    def crear_solicitud_vacaciones(self, solicitud_data: SolicitudVacacionesCreate) -> SolicitudVacaciones:
        """Crear solicitud de vacaciones"""
        # Calcular días solicitados
        delta = solicitud_data.fecha_fin - solicitud_data.fecha_inicio
        dias_solicitados = delta.days + 1
        
        solicitud = SolicitudVacaciones(
            **solicitud_data.dict(),
            dias_solicitados=dias_solicitados
        )
        
        self.db.add(solicitud)
        self.db.commit()
        self.db.refresh(solicitud)
        return solicitud
    
    def aprobar_solicitud_vacaciones(
        self, 
        solicitud_id: str, 
        aprobado_por: str, 
        comentarios: str = None
    ) -> Optional[SolicitudVacaciones]:
        """Aprobar o rechazar solicitud de vacaciones"""
        solicitud = self.db.query(SolicitudVacaciones).filter(
            SolicitudVacaciones.id == solicitud_id
        ).first()
        
        if not solicitud:
            return None
        
        solicitud.estado = "APROBADA"
        solicitud.fecha_respuesta = datetime.now()
        solicitud.respondido_por = aprobado_por
        solicitud.comentarios_respuesta = comentarios
        
        self.db.commit()
        self.db.refresh(solicitud)
        return solicitud
    
    # Gestión de evaluaciones de desempeño
    
    def crear_evaluacion_desempeno(self, evaluacion_data: EvaluacionDesempenoCreate) -> EvaluacionDesempeno:
        """Crear evaluación de desempeño"""
        # Calcular puntuación total
        puntuaciones = [
            evaluacion_data.puntualidad,
            evaluacion_data.calidad_trabajo,
            evaluacion_data.trabajo_equipo,
            evaluacion_data.comunicacion,
            evaluacion_data.iniciativa,
            evaluacion_data.cumplimiento_objetivos
        ]
        
        puntuacion_total = sum(puntuaciones) / len(puntuaciones)
        
        # Determinar nivel de desempeño
        if puntuacion_total >= 9:
            nivel = "EXCELENTE"
        elif puntuacion_total >= 7:
            nivel = "BUENO"
        elif puntuacion_total >= 5:
            nivel = "SATISFACTORIO"
        else:
            nivel = "NECESITA_MEJORA"
        
        evaluacion = EvaluacionDesempeno(
            **evaluacion_data.dict(),
            puntuacion_total=puntuacion_total,
            nivel_desempeno=nivel
        )
        
        self.db.add(evaluacion)
        self.db.commit()
        self.db.refresh(evaluacion)
        return evaluacion
    
    # Gestión de reemplazos
    
    def crear_reemplazo(self, reemplazo_data: ReemplazoEmpleadoCreate) -> ReemplazoEmpleado:
        """Crear reemplazo de empleado"""
        reemplazo = ReemplazoEmpleado(**reemplazo_data.dict())
        
        self.db.add(reemplazo)
        self.db.commit()
        self.db.refresh(reemplazo)
        return reemplazo
    
    def obtener_reemplazos_activos(self) -> List[ReemplazoEmpleado]:
        """Obtener todos los reemplazos activos"""
        hoy = date.today()
        return self.db.query(ReemplazoEmpleado).filter(
            and_(
                ReemplazoEmpleado.estado == "ACTIVO",
                ReemplazoEmpleado.fecha_inicio <= hoy,
                or_(
                    ReemplazoEmpleado.fecha_fin.is_(None),
                    ReemplazoEmpleado.fecha_fin >= hoy
                )
            )
        ).all()
    
    # Reportes y estadísticas
    
    def generar_reporte_asistencias(self, mes: int, ano: int) -> Dict[str, Any]:
        """Generar reporte de asistencias del mes"""
        inicio_mes = date(ano, mes, 1)
        fin_mes = date(ano, mes + 1, 1) - timedelta(days=1) if mes < 12 else date(ano, 12, 31)
        
        # Obtener todas las asistencias del mes
        asistencias = self.db.query(AsistenciaEmpleado).filter(
            and_(
                AsistenciaEmpleado.fecha >= inicio_mes,
                AsistenciaEmpleado.fecha <= fin_mes
            )
        ).all()
        
        # Estadísticas generales
        total_empleados = self.db.query(Empleado).filter(
            Empleado.estado == EstadoEmpleado.ACTIVO
        ).count()
        
        asistencias_totales = len(asistencias)
        llegadas_tarde = len([a for a in asistencias if a.estado == "TARDE"])
        ausencias = len([a for a in asistencias if a.estado == "AUSENTE"])
        
        # Estadísticas por empleado
        estadisticas_empleados = {}
        for empleado in self.obtener_empleados():
            emp_asistencias = [a for a in asistencias if a.empleado_id == empleado.id]
            horas_trabajadas = sum(a.horas_trabajadas or 0 for a in emp_asistencias)
            horas_extra = sum(a.horas_extra or 0 for a in emp_asistencias)
            
            estadisticas_empleados[empleado.id] = {
                "nombre": empleado.nombre_completo,
                "dias_trabajados": len(emp_asistencias),
                "horas_trabajadas": horas_trabajadas,
                "horas_extra": horas_extra,
                "llegadas_tarde": len([a for a in emp_asistencias if a.estado == "TARDE"])
            }
        
        return {
            "periodo": f"{mes:02d}/{ano}",
            "total_empleados": total_empleados,
            "asistencias_totales": asistencias_totales,
            "llegadas_tarde": llegadas_tarde,
            "ausencias": ausencias,
            "tasa_puntualidad": ((asistencias_totales - llegadas_tarde) / asistencias_totales * 100) if asistencias_totales else 0,
            "estadisticas_empleados": estadisticas_empleados
        }
    
    def obtener_cumpleanos_mes(self, mes: int = None) -> List[Empleado]:
        """Obtener empleados que cumplen años en el mes especificado"""
        mes = mes or datetime.now().month
        
        return self.db.query(Empleado).filter(
            and_(
                extract('month', Empleado.fecha_nacimiento) == mes,
                Empleado.estado == EstadoEmpleado.ACTIVO
            )
        ).all()
    
    def obtener_empleados_por_antiguedad(self) -> List[Dict[str, Any]]:
        """Obtener empleados ordenados por antigüedad"""
        empleados = self.db.query(Empleado).filter(
            Empleado.estado == EstadoEmpleado.ACTIVO
        ).order_by(Empleado.fecha_ingreso).all()
        
        resultado = []
        for empleado in empleados:
            resultado.append({
                "id": empleado.id,
                "nombre": empleado.nombre_completo,
                "fecha_ingreso": empleado.fecha_ingreso,
                "antiguedad_anos": empleado.antiguedad_anos,
                "departamento": empleado.departamento.value if empleado.departamento else None
            })
        
        return resultado 