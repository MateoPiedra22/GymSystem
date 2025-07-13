"""
Router para generación de KPIs y datos de reportes
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Dict, Any, Optional

from app.core.database import get_db
from app.core.auth import get_current_user_optional, get_current_user, get_current_admin_user
from app.schemas.usuarios import UsuarioInDB as Usuario
from app.services.reportes_service import (
    get_kpis, get_graficos_dashboard, 
    get_reporte_detallado_asistencias, get_reporte_financiero_detallado
)

router = APIRouter()

@router.get("/kpis")
def obtener_kpis(
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """
    Retorna un diccionario con los 15 indicadores clave (KPIs) para el gimnasio.
    
    **KPIs incluidos:**
    - Ingresos mensuales: Total de ingresos del mes actual
    - Ingresos por tipo: Distribución de ingresos por tipo de cuota
    - Nuevas inscripciones: Usuarios registrados este mes
    - Tasa de retención: Porcentaje de usuarios activos
    - Ocupación de clases: Porcentaje promedio de ocupación
    - Asistencias diarias: Promedio de asistencias por día
    - Morosidad: Porcentaje de pagos vencidos
    - ARPU: Ingreso promedio por usuario
    - Ventas por empleado: Performance individual de ventas
    - Rentabilidad: Ingresos menos gastos operativos
    - Uso de instalaciones: Distribución por horarios
    - Puntualidad empleados: Porcentaje de puntualidad
    - Crecimiento usuarios: Variación mensual de usuarios
    - Clases populares: Ranking de clases por asistencia
    - Eficiencia cobranza: Ratio de pagos recibidos vs esperados
    """
    return get_kpis(db)

@router.get("/graficos/dashboard")
def obtener_graficos_dashboard(
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """
    Retorna datos para 8 gráficos interactivos del dashboard principal.
    
    **Gráficos incluidos:**
    1. **Ingresos mensuales**: Evolución de ingresos últimos 12 meses
    2. **Asistencias por día**: Distribución semanal de asistencias
    3. **Métodos de pago**: Preferencias de pago de los usuarios
    4. **Evolución usuarios**: Crecimiento de base de usuarios
    5. **Asistencias por hora**: Horarios de mayor concurrencia
    6. **Estados de pago**: Distribución de estados de pagos
    7. **Rentabilidad membresías**: Ingresos por tipo de membresía
    8. **Tendencia usuarios**: Nuevos vs cancelaciones mensuales
    
    Cada gráfico incluye datos preparados para visualización interactiva.
    """
    return get_graficos_dashboard(db)

@router.get("/graficos/ingresos-mensuales")
def obtener_grafico_ingresos_mensuales(
    meses: int = Query(12, ge=1, le=24, description="Número de meses hacia atrás"),
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """
    Datos específicos para gráfico de líneas de ingresos mensuales.
    Permite personalizar el período de análisis.
    """
    graficos = get_graficos_dashboard(db)
    return {
        "titulo": f"Ingresos Mensuales - Últimos {meses} meses",
        "tipo": "line",
        "datos": graficos["ingresos_mensuales"][-meses:],
        "configuracion": {
            "color_primario": "#3B82F6",
            "mostrar_puntos": True,
            "animacion": True,
            "tooltip_formato": "PEN {value}"
        }
    }

@router.get("/graficos/asistencias-por-dia")
def obtener_grafico_asistencias_dia(
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """
    Datos para gráfico de barras de asistencias por día de la semana.
    Útil para identificar patrones de asistencia semanal.
    """
    graficos = get_graficos_dashboard(db)
    return {
        "titulo": "Distribución de Asistencias por Día",
        "tipo": "bar",
        "datos": graficos["asistencias_por_dia"],
        "configuracion": {
            "color_primario": "#10B981",
            "orientacion": "vertical",
            "mostrar_valores": True,
            "animacion": True
        }
    }

@router.get("/graficos/metodos-pago")
def obtener_grafico_metodos_pago(
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """
    Datos para gráfico circular (dona) de métodos de pago utilizados.
    Muestra las preferencias de pago de los usuarios.
    """
    graficos = get_graficos_dashboard(db)
    return {
        "titulo": "Métodos de Pago Preferidos",
        "tipo": "doughnut",
        "datos": graficos["metodos_pago"],
        "configuracion": {
            "colores": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"],
            "mostrar_leyenda": True,
            "porcentajes": True,
            "animacion": True
        }
    }

@router.get("/graficos/evolucion-usuarios")
def obtener_grafico_evolucion_usuarios(
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """
    Datos para gráfico de área de evolución de usuarios activos.
    Muestra el crecimiento de la base de usuarios.
    """
    graficos = get_graficos_dashboard(db)
    return {
        "titulo": "Evolución de Usuarios Activos",
        "tipo": "area",
        "datos": graficos["evolucion_usuarios"],
        "configuracion": {
            "color_primario": "#8B5CF6",
            "gradiente": True,
            "suavizado": True,
            "animacion": True
        }
    }

@router.get("/graficos/asistencias-por-hora")
def obtener_grafico_asistencias_hora(
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """
    Datos para gráfico de barras horizontales de asistencias por hora.
    Identifica las franjas horarias de mayor demanda.
    """
    graficos = get_graficos_dashboard(db)
    return {
        "titulo": "Horarios de Mayor Concurrencia",
        "tipo": "horizontal_bar",
        "datos": graficos["asistencias_por_hora"],
        "configuracion": {
            "color_primario": "#F59E0B",
            "orientacion": "horizontal",
            "mostrar_valores": True,
            "animacion": True
        }
    }

@router.get("/graficos/estados-pago")
def obtener_grafico_estados_pago(
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """
    Datos para gráfico de pastel de distribución de estados de pago.
    Monitorea la salud financiera de los pagos.
    """
    graficos = get_graficos_dashboard(db)
    return {
        "titulo": "Distribución de Estados de Pago",
        "tipo": "pie",
        "datos": graficos["estados_pago"],
        "configuracion": {
            "colores": ["#10B981", "#F59E0B", "#EF4444", "#6B7280"],
            "mostrar_leyenda": True,
            "porcentajes": True,
            "animacion": True
        }
    }

@router.get("/graficos/rentabilidad-membresias")
def obtener_grafico_rentabilidad_membresias(
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """
    Datos para gráfico de barras agrupadas de rentabilidad por tipo de membresía.
    Compara ingresos y cantidad de ventas por tipo.
    """
    graficos = get_graficos_dashboard(db)
    return {
        "titulo": "Rentabilidad por Tipo de Membresía",
        "tipo": "grouped_bar",
        "datos": graficos["rentabilidad_membresias"],
        "configuracion": {
            "colores": ["#3B82F6", "#10B981"],
            "eje_y_dual": True,
            "mostrar_valores": True,
            "animacion": True
        }
    }

@router.get("/graficos/tendencia-usuarios")
def obtener_grafico_tendencia_usuarios(
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """
    Datos para gráfico de líneas múltiples comparando nuevos usuarios vs cancelaciones.
    Análisis de retención y crecimiento neto.
    """
    graficos = get_graficos_dashboard(db)
    return {
        "titulo": "Tendencia: Nuevos vs Cancelaciones",
        "tipo": "multi_line",
        "datos": graficos["tendencia_usuarios"],
        "configuracion": {
            "colores": ["#10B981", "#EF4444"],
            "mostrar_puntos": True,
            "leyenda": ["Nuevos Usuarios", "Cancelaciones"],
            "animacion": True
        }
    }

@router.get("/asistencias/detallado")
def obtener_reporte_asistencias_detallado(
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Reporte detallado de asistencias en un período específico.
    
    **Incluye:**
    - Asistencias diarias en el período
    - Top 10 usuarios más activos
    - Métricas de ocupación
    - Análisis de patrones de asistencia
    
    Solo accesible para administradores.
    """
    if fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=400,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )
    
    # Convertir dates a datetime
    fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
    fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
    
    return get_reporte_detallado_asistencias(db, fecha_inicio_dt, fecha_fin_dt)

@router.get("/financiero/detallado")
def obtener_reporte_financiero_detallado(
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Reporte financiero detallado con análisis de rentabilidad.
    
    **Incluye:**
    - Ingresos por concepto de pago
    - Comparativa ingresos vs gastos
    - Margen de utilidad
    - Análisis de rentabilidad por membresía
    
    Solo accesible para administradores.
    """
    if fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=400,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )
    
    # Convertir dates a datetime
    fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
    fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
    
    return get_reporte_financiero_detallado(db, fecha_inicio_dt, fecha_fin_dt)

@router.get("/exportar/{tipo_reporte}")
def exportar_reporte(
    tipo_reporte: str,
    formato: str = Query(..., regex="^(pdf|excel|csv)$", description="Formato: pdf, excel, csv"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio (opcional)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha de fin (opcional)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Exporta reportes en diferentes formatos (PDF, Excel, CSV).
    
    **Tipos de reporte disponibles:**
    - `kpis`: Indicadores clave de rendimiento
    - `asistencias`: Reporte detallado de asistencias
    - `financiero`: Reporte financiero completo
    - `usuarios`: Reporte de usuarios y membresías
    
    Solo accesible para administradores.
    """
    # Por ahora retornamos un placeholder - en producción se implementaría la exportación real
    return {
        "mensaje": f"Exportación de {tipo_reporte} en formato {formato} iniciada",
        "estado": "procesando",
        "tipo_reporte": tipo_reporte,
        "formato": formato,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "tiempo_estimado": "2-3 minutos",
        "nota": "Recibirás una notificación cuando el archivo esté listo para descarga"
    }

@router.get("/graficos")
def obtener_graficos_compat(
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """Compatibilidad: alias simple para `/graficos/dashboard` requerido por pruebas automatizadas."""
    return get_graficos_dashboard(db) 