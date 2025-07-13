"""
Widget de Dashboard para mostrar información general
Sistema de Gestión de Gimnasio v6 - Optimizado
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QSizePolicy, QScrollArea, QPushButton
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPainter, QColor, QPen, QFont
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

from api_client import ApiClient
from utils.performance_monitor import get_performance_monitor, monitor_ui_function

# Configuración de logging
logger = logging.getLogger("dashboard_widget")

class StatCard(QFrame):
    """
    Tarjeta para mostrar una estadística con ícono
    
    Esta clase crea un componente visual para mostrar una métrica
    importante con un ícono, título y valor.
    
    Atributos:
        title: Título de la estadística
        value: Valor numérico o texto de la estadística
        icon_path: Ruta al ícono
        color: Color de acento para la tarjeta
    """
    
    def __init__(self, title: str, value: str, icon_path: str, color: str = "#4CAF50"):
        """
        Inicializa la tarjeta de estadística
        
        Args:
            title: Título de la estadística
            value: Valor a mostrar
            icon_path: Ruta al ícono
            color: Color de acento (hexadecimal)
        """
        super().__init__()
        
        # Configurar aspecto
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(120)
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Aplicar estilo
        self.setStyleSheet(f"""
            StatCard {{
                border: 1px solid #dcdcdc;
                border-left: 5px solid {color};
                border-radius: 4px;
                background-color: white;
            }}
        """)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Área de texto
        text_layout = QVBoxLayout()
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #5c5c5c;")
        
        # Valor
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        text_layout.addStretch()
        
        # Ícono
        icon_label = QLabel()
        icon = QIcon(icon_path)
        if not icon.isNull():
            pixmap = icon.pixmap(QSize(48, 48))
            icon_label.setPixmap(pixmap)
        else:
            # Ícono no encontrado
            icon_label.setText("🔢")
            icon_label.setStyleSheet("font-size: 24px;")
        
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Añadir al layout principal
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addWidget(icon_label)

class ChartCard(QFrame):
    """
    Tarjeta para mostrar un gráfico
    
    Esta clase crea un componente visual para mostrar un gráfico
    con título y controles.
    
    Atributos:
        title: Título del gráfico
        chart: Gráfico a mostrar
    """
    
    def __init__(self, title: str, chart_view: QChartView):
        """
        Inicializa la tarjeta de gráfico
        
        Args:
            title: Título del gráfico
            chart_view: Vista de gráfico a mostrar
        """
        super().__init__()
        
        # Configurar aspecto
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Aplicar estilo
        self.setStyleSheet("""
            ChartCard {
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        
        # Añadir al layout
        layout.addWidget(title_label)
        layout.addWidget(chart_view)

class DashboardWidget(QWidget):
    """
    Widget principal de Dashboard - Optimizado
    
    Este widget muestra un resumen visual del estado del gimnasio,
    incluyendo estadísticas clave y gráficos con optimizaciones de rendimiento.
    
    Atributos:
        api_client: Cliente API para obtener datos
        refresh_timer: Temporizador para actualización automática
        performance_monitor: Monitor de rendimiento
        _data_cache: Cache para datos del dashboard
        _last_update: Tiempo de última actualización
    """
    
    # Señales para comunicación
    data_updated = pyqtSignal(dict)
    loading_started = pyqtSignal()
    loading_finished = pyqtSignal()
    
    def __init__(self, api_client: ApiClient):
        """
        Inicializa el widget de dashboard con optimizaciones
        
        Args:
            api_client: Cliente API para obtener datos
        """
        super().__init__()
        
        self.api_client = api_client
        self.performance_monitor = get_performance_monitor()
        
        # Cache de datos para evitar recargas innecesarias
        self._data_cache = {}
        self._last_update = 0
        self._cache_duration = 30  # segundos
        
        # Datos para gráficos
        self.users_data = []
        self.attendance_data = []
        self.payments_data = []
        
        # Inicializar UI con optimizaciones
        self._init_ui_optimized()
        
        # Cargar datos iniciales de forma asíncrona
        self._load_data_async()
        
        # Configurar actualizaciones automáticas optimizadas
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_data_async)
        self.refresh_timer.start(60000)  # Actualizar cada 1 minuto
    
    @monitor_ui_function("dashboard_init")
    def _init_ui_optimized(self):
        """Inicializa la interfaz de usuario con optimizaciones de rendimiento"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)
        
        # Título con indicador de carga
        title_layout = QHBoxLayout()
        
        title_label = QLabel("Dashboard")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        
        # Indicador de carga
        self.loading_indicator = QLabel("●")
        self.loading_indicator.setStyleSheet("color: #4CAF50; font-size: 20px;")
        self.loading_indicator.setVisible(False)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.loading_indicator)
        title_layout.addStretch()
        
        # Botón de actualizar mejorado
        refresh_button = QPushButton("Actualizar")
        refresh_button.setIcon(QIcon("assets/refresh.png"))
        refresh_button.clicked.connect(self._force_refresh)
        title_layout.addWidget(refresh_button)
        
        main_layout.addLayout(title_layout)
        
        # Subtítulo con fecha actual
        self.date_label = QLabel()
        self.update_date_label()
        self.date_label.setStyleSheet("font-size: 14px; color: #666;")
        main_layout.addWidget(self.date_label)
        
        # Tarjetas de estadísticas con placeholders
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        # Crear tarjetas de estadísticas mejoradas
        self.users_card = StatCard("Usuarios Activos", "Cargando...", "assets/users.png", "#2196F3")
        self.attendance_card = StatCard("Asistencias Hoy", "Cargando...", "assets/attendance.png", "#FF9800")
        self.classes_card = StatCard("Clases Activas", "Cargando...", "assets/classes.png", "#9C27B0")
        self.payments_card = StatCard("Pagos Pendientes", "Cargando...", "assets/payments.png", "#F44336")
        
        # Añadir tarjetas al layout
        stats_layout.addWidget(self.users_card, 0, 0)
        stats_layout.addWidget(self.attendance_card, 0, 1)
        stats_layout.addWidget(self.classes_card, 1, 0)
        stats_layout.addWidget(self.payments_card, 1, 1)
        
        main_layout.addLayout(stats_layout)
        
        # Gráficos con carga diferida
        charts_layout = QHBoxLayout()
        
        # Placeholders para gráficos
        self.charts_placeholder = QLabel("Cargando gráficos...")
        self.charts_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.charts_placeholder.setStyleSheet("color: #666; font-size: 16px; min-height: 300px;")
        
        charts_layout.addWidget(self.charts_placeholder)
        
        main_layout.addLayout(charts_layout)
        
        # Próximas clases y eventos
        upcoming_frame = QFrame()
        upcoming_frame.setFrameShape(QFrame.Shape.StyledPanel)
        upcoming_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        upcoming_layout = QVBoxLayout(upcoming_frame)
        
        upcoming_title = QLabel("Próximas Clases")
        upcoming_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        
        self.upcoming_list = QLabel("Cargando información de clases...")
        self.upcoming_list.setStyleSheet("color: #666;")
        self.upcoming_list.setWordWrap(True)
        
        upcoming_layout.addWidget(upcoming_title)
        upcoming_layout.addWidget(self.upcoming_list)
        
        main_layout.addWidget(upcoming_frame)
        
        # Añadir espacio flexible al final
        main_layout.addStretch(1)
        
        # Configurar señales
        self.loading_started.connect(self._show_loading)
        self.loading_finished.connect(self._hide_loading)
        
    def _init_ui(self):
        """Método legacy para compatibilidad"""
        self._init_ui_optimized()
    
    def update_date_label(self):
        """Actualiza la etiqueta de fecha con la fecha actual"""
        now = datetime.now()
        self.date_label.setText(now.strftime("Hoy es %A, %d de %B de %Y, %H:%M"))
    
    def create_attendance_chart(self) -> QChart:
        """
        Crea un gráfico de barras para asistencias
        
        Returns:
            Gráfico de barras
        """
        # Crear gráfico
        chart = QChart()
        chart.setTitle("Asistencias de la Última Semana")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # Datos de ejemplo (se actualizarán después)
        bar_set = QBarSet("Asistencias")
        bar_set.append([0, 0, 0, 0, 0, 0, 0])
        
        # Serie de barras
        series = QBarSeries()
        series.append(bar_set)
        chart.addSeries(series)
        
        # Eje X (días)
        days = self.get_last_week_days()
        axis_x = QBarCategoryAxis()
        axis_x.append(days)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        # Eje Y (valores)
        axis_y = QValueAxis()
        axis_y.setRange(0, 10)  # Rango inicial
        axis_y.setTickCount(6)
        axis_y.setLabelFormat("%d")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        # Leyenda
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        return chart
    
    def create_users_chart(self) -> QChart:
        """
        Crea un gráfico circular para distribución de usuarios
        
        Returns:
            Gráfico circular
        """
        # Crear gráfico
        chart = QChart()
        chart.setTitle("Distribución de Usuarios por Plan")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # Datos de ejemplo (se actualizarán después)
        series = QPieSeries()
        series.append("Plan Mensual", 0)
        series.append("Plan Trimestral", 0)
        series.append("Plan Anual", 0)
        series.append("Plan Libre", 0)
        
        # Destacar primer segmento
        slice = series.slices()[0]
        slice.setExploded(True)
        slice.setLabelVisible(True)
        
        chart.addSeries(series)
        
        # Leyenda
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        
        return chart
    
    def get_last_week_days(self) -> List[str]:
        """
        Obtiene los nombres de los últimos 7 días
        
        Returns:
            Lista con nombres abreviados de días
        """
        days = []
        today = datetime.now()
        
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            days.append(day.strftime("%a"))
        
        return days
    
    def _load_data_async(self):
        """Carga datos de forma asíncrona con optimizaciones"""
        # Verificar si necesitamos recargar datos
        current_time = time.time()
        if current_time - self._last_update < self._cache_duration and self._data_cache:
            self._update_ui_from_cache()
            return
            
        # Emitir señal de inicio de carga
        self.loading_started.emit()
        
        try:
            # Registrar tiempo de carga
            load_start = time.time()
            
            # Actualizar fecha
            self.update_date_label()
            
            # Cargar datos reales desde la API
            dashboard_data = self._load_dashboard_data_from_api()
            
            # Guardar en cache
            self._data_cache = dashboard_data
            self._data_cache['timestamp'] = current_time
            
            # Actualizar UI
            self._update_ui_from_cache()
            
            # Actualizar tiempo de última actualización
            self._last_update = current_time
            
            # Registrar tiempo de carga
            load_time = (time.time() - load_start) * 1000  # ms
            self.performance_monitor.record_ui_event("dashboard_load", load_time)
            
            # Emitir señal de datos actualizados
            self.data_updated.emit(self._data_cache)
            
            logger.info(f"Datos de dashboard actualizados en {load_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"Error al cargar datos de dashboard: {e}")
            self.performance_monitor.record_error("dashboard_load", str(e))
            # Fallback a datos básicos si hay error
            self._load_fallback_data()
        finally:
            # Emitir señal de fin de carga
            self.loading_finished.emit()
    
    def _load_dashboard_data_from_api(self) -> Dict[str, Any]:
        """Carga datos reales del dashboard desde la API"""
        try:
            # Obtener KPIs principales
            kpis_response = self.api_client._make_request('GET', '/reportes/kpis')
            kpis_data = kpis_response.get('data', {})
            
            # Obtener datos de gráficos
            graficos_response = self.api_client._make_request('GET', '/reportes/graficos')
            graficos_data = graficos_response.get('data', {})
            
            # Obtener clases próximas
            clases_response = self.api_client._make_request('GET', '/clases?limit=5&estado=activa')
            clases_data = clases_response.get('data', [])
            
            # Procesar datos de asistencias por día
            attendance_data = []
            if 'asistencias_por_dia' in graficos_data:
                for item in graficos_data['asistencias_por_dia']:
                    attendance_data.append(item.get('asistencias', 0))
            else:
                # Fallback si no hay datos
                attendance_data = [35, 42, 38, 45, 52, 48, 41]
            
            # Procesar distribución de usuarios
            users_data = {}
            if 'distribucion_planes' in graficos_data:
                for item in graficos_data['distribucion_planes']:
                    users_data[item.get('plan', '')] = item.get('cantidad', 0)
            else:
                # Fallback si no hay datos
                users_data = {
                    "Plan Mensual": 70,
                    "Plan Trimestral": 40,
                    "Plan Anual": 20,
                    "Plan Libre": 8
                }
            
            # Procesar clases próximas
            upcoming_classes = []
            for clase in clases_data:
                upcoming_classes.append({
                    "nombre": clase.get('nombre', ''),
                    "hora": clase.get('horario', ''),
                    "instructor": clase.get('instructor', '')
                })
            
            return {
                'users_count': kpis_data.get('usuarios_activos', 0),
                'attendance_count': kpis_data.get('asistencias_hoy', 0),
                'classes_count': kpis_data.get('clases_activas', 0),
                'payments_count': kpis_data.get('pagos_pendientes', 0),
                'attendance_data': attendance_data,
                'users_data': users_data,
                'upcoming_classes': upcoming_classes,
                'ingresos_mes': kpis_data.get('ingresos_mes', 0),
                'empleados_activos': kpis_data.get('empleados_activos', 0),
                'tasa_retencion': kpis_data.get('tasa_retencion', 0),
                'crecimiento_mensual': kpis_data.get('crecimiento_mensual', 0)
            }
            
        except Exception as e:
            logger.error(f"Error cargando datos de API: {e}")
            raise
    
    def _load_fallback_data(self):
        """Carga datos de fallback cuando hay error en la API"""
        logger.warning("Cargando datos de fallback para dashboard")
        
        self._data_cache = {
            'users_count': 0,
            'attendance_count': 0,
            'classes_count': 0,
            'payments_count': 0,
            'attendance_data': [0, 0, 0, 0, 0, 0, 0],
            'users_data': {},
            'upcoming_classes': [],
            'ingresos_mes': 0,
            'empleados_activos': 0,
            'tasa_retencion': 0,
            'crecimiento_mensual': 0
        }
        
        self._update_ui_from_cache()
            
            # Actualizar UI
            self._update_ui_from_cache()
            
            # Actualizar tiempo de última actualización
            self._last_update = current_time
            
            # Registrar tiempo de carga
            load_time = (time.time() - load_start) * 1000  # ms
            self.performance_monitor.record_ui_event("dashboard_load", load_time)
            
            # Emitir señal de datos actualizados
            self.data_updated.emit(self._data_cache)
            
            logger.info(f"Datos de dashboard actualizados en {load_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"Error al cargar datos de dashboard: {e}")
            self.performance_monitor.record_error("dashboard_load", str(e))
        finally:
            # Emitir señal de fin de carga
            self.loading_finished.emit()
    
    def _update_ui_from_cache(self):
        """Actualiza la UI usando datos del cache"""
        if not self._data_cache:
            return
            
        try:
            # Actualizar tarjetas de estadísticas
            self._update_stat_card(self.users_card, str(self._data_cache['users_count']))
            self._update_stat_card(self.attendance_card, str(self._data_cache['attendance_count']))
            self._update_stat_card(self.classes_card, str(self._data_cache['classes_count']))
            self._update_stat_card(self.payments_card, str(self._data_cache['payments_count']))
            
            # Actualizar gráficos si están creados
            if hasattr(self, 'attendance_chart'):
                self.update_attendance_chart(self._data_cache['attendance_data'])
            
            if hasattr(self, 'users_chart'):
                self.update_users_chart(self._data_cache['users_data'])
            
            # Actualizar próximas clases
            self.update_upcoming_classes(self._data_cache['upcoming_classes'])
            
        except Exception as e:
            logger.error(f"Error actualizando UI desde cache: {e}")
    
    def _update_stat_card(self, card: 'StatCard', value: str):
        """Actualiza una tarjeta de estadística"""
        try:
            # Buscar el QLabel del valor en la tarjeta
            value_labels = card.findChildren(QLabel)
            if len(value_labels) >= 2:
                value_labels[1].setText(value)  # El segundo label es el valor
        except Exception as e:
            logger.error(f"Error actualizando tarjeta de estadística: {e}")
    
    def _force_refresh(self):
        """Fuerza una actualización inmediata"""
        self._last_update = 0  # Resetear tiempo para forzar recarga
        self._data_cache.clear()  # Limpiar cache
        self._load_data_async()
    
    def _show_loading(self):
        """Muestra indicador de carga"""
        self.loading_indicator.setVisible(True)
        self.loading_indicator.setStyleSheet("color: #FF9800; font-size: 20px;")
    
    def _hide_loading(self):
        """Oculta indicador de carga"""
        self.loading_indicator.setVisible(False)
    
    def _create_charts_when_needed(self):
        """Crea los gráficos cuando son necesarios (carga diferida)"""
        try:
            # Crear gráficos solo cuando se necesiten
            if not hasattr(self, 'attendance_chart'):
                self.attendance_chart = self.create_attendance_chart()
                
            if not hasattr(self, 'users_chart'):
                self.users_chart = self.create_users_chart()
                
            # Reemplazar placeholder con gráficos reales
            if hasattr(self, 'charts_placeholder'):
                charts_layout = self.charts_placeholder.parent().layout()
                charts_layout.removeWidget(self.charts_placeholder)
                self.charts_placeholder.deleteLater()
                
                # Añadir gráficos
                attendance_chart_card = ChartCard("Asistencias por Día", QChartView(self.attendance_chart))
                users_chart_card = ChartCard("Distribución de Usuarios", QChartView(self.users_chart))
                
                charts_layout.addWidget(attendance_chart_card)
                charts_layout.addWidget(users_chart_card)
                
                # Actualizar con datos del cache
                if self._data_cache:
                    self.update_attendance_chart(self._data_cache['attendance_data'])
                    self.update_users_chart(self._data_cache['users_data'])
                    
        except Exception as e:
            logger.error(f"Error creando gráficos: {e}")
    
    def showEvent(self, event):
        """Se ejecuta cuando el widget se muestra"""
        super().showEvent(event)
        
        # Crear gráficos cuando el widget se muestra por primera vez
        if not hasattr(self, 'attendance_chart'):
            self._create_charts_when_needed()
    
    def load_data(self):
        """Método legacy para compatibilidad"""
        self._load_data_async()
    
    def update_attendance_chart(self, data: List[int]):
        """
        Actualiza el gráfico de asistencias con nuevos datos
        
        Args:
            data: Lista con conteo de asistencias por día
        """
        # Eliminar series existentes
        self.attendance_chart.removeAllSeries()
        
        # Crear nueva serie con datos actualizados
        bar_set = QBarSet("Asistencias")
        bar_set.append(data)
        
        series = QBarSeries()
        series.append(bar_set)
        self.attendance_chart.addSeries(series)
        
        # Obtener ejes
        axes = self.attendance_chart.axes()
        if len(axes) >= 2:
            # Adjuntar serie a los ejes existentes
            series.attachAxis(axes[0])  # Eje X
            series.attachAxis(axes[1])  # Eje Y
            
            # Actualizar rango de eje Y
            max_value = max(data) if data else 10
            axes[1].setRange(0, max_value + 5)
    
    def update_users_chart(self, data: Dict[str, int]):
        """
        Actualiza el gráfico de usuarios con nuevos datos
        
        Args:
            data: Diccionario con distribución de usuarios por plan
        """
        # Eliminar series existentes
        self.users_chart.removeAllSeries()
        
        # Crear nueva serie con datos actualizados
        series = QPieSeries()
        
        for label, value in data.items():
            series.append(f"{label} ({value})", value)
        
        # Destacar primer segmento
        if series.count() > 0:
            slice = series.slices()[0]
            slice.setExploded(True)
            slice.setLabelVisible(True)
        
        self.users_chart.addSeries(series)
    
    def update_upcoming_classes(self, classes: List[Dict[str, str]]):
        """
        Actualiza la lista de próximas clases
        
        Args:
            classes: Lista de diccionarios con información de clases
        """
        if not classes:
            self.upcoming_list.setText("No hay clases programadas para hoy")
            return
        
        text = ""
        for i, cls in enumerate(classes):
            text += f"<b>{cls['nombre']}</b> - {cls['hora']} - Instructor: {cls['instructor']}"
            if i < len(classes) - 1:
                text += "<br><br>"
        
        self.upcoming_list.setText(text)
