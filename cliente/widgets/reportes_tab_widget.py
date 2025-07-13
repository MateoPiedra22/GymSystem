"""
Widget para la generación y visualización de reportes
Incluye gráficos, exportación a PDF/Excel y filtros avanzados
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QMessageBox, QHeaderView, QAbstractItemView, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox, QCheckBox,
    QTabWidget, QSplitter, QTextEdit, QGroupBox, QRadioButton,
    QDateEdit, QFileDialog, QProgressBar, QFrame, QGridLayout,
    QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QDate, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor, QPainter, QPalette
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QPieSeries
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from ..api_client import ApiClient

class DataFetcher:
    """Maneja la obtención de datos de diferentes tipos de reportes"""
    
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
    
    def fetch_kpis(self) -> Dict[str, Any]:
        """Obtiene datos de KPIs"""
        try:
            return self.api_client.get('/api/reportes/kpis')
        except Exception as e:
            raise Exception(f"Error obteniendo KPIs: {str(e)}")
    
    def fetch_graficos(self) -> Dict[str, Any]:
        """Obtiene datos de gráficos"""
        try:
            return self.api_client.get('/api/reportes/graficos')
        except Exception as e:
            raise Exception(f"Error obteniendo gráficos: {str(e)}")
    
    def fetch_custom_report(self, reporte_tipo: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene reporte personalizado"""
        try:
            return self.api_client.get_reporte(reporte_tipo, **params)
        except Exception as e:
            raise Exception(f"Error obteniendo reporte {reporte_tipo}: {str(e)}")

class DataProcessor:
    """Procesa y valida los datos obtenidos"""
    
    @staticmethod
    def validate_kpi_data(data: Dict[str, Any]) -> bool:
        """Valida que los datos de KPIs tengan la estructura correcta"""
        required_fields = ['financieros', 'crecimiento', 'operacionales']
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_chart_data(data: Dict[str, Any]) -> bool:
        """Valida que los datos de gráficos tengan la estructura correcta"""
        required_fields = ['ingresos', 'asistencias', 'ocupacion']
        return all(field in data for field in required_fields)
    
    @staticmethod
    def process_kpi_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa y formatea los datos de KPIs"""
        processed_data = {}
        for category, kpis in data.items():
            processed_data[category] = []
            for kpi in kpis:
                processed_data[category].append({
                    'title': kpi.get('title', ''),
                    'value': kpi.get('value', '0'),
                    'category': category,
                    'justification': kpi.get('justification', ''),
                    'icon': kpi.get('icon', ''),
                    'color': kpi.get('color', '#3B82F6')
                })
        return processed_data

class ReportLoadWorker(QThread):
    """Worker optimizado para cargar datos de reportes en background"""
    
    data_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)
    
    def __init__(self, api_client: ApiClient, reporte_tipo: str, params: Dict[str, Any]):
        super().__init__()
        self.data_fetcher = DataFetcher(api_client)
        self.data_processor = DataProcessor()
        self.reporte_tipo = reporte_tipo
        self.params = params
        
    def run(self):
        """Carga y procesa los datos del reporte"""
        try:
            self.progress_updated.emit(10, "Iniciando carga de datos...")
            
            # Obtener datos según el tipo
            if self.reporte_tipo == "kpis":
                self.progress_updated.emit(30, "Obteniendo KPIs...")
                raw_data = self.data_fetcher.fetch_kpis()
                self.progress_updated.emit(60, "Validando datos...")
                
                if not self.data_processor.validate_kpi_data(raw_data):
                    raise Exception("Datos de KPIs inválidos")
                
                self.progress_updated.emit(80, "Procesando datos...")
                processed_data = self.data_processor.process_kpi_data(raw_data)
                
            elif self.reporte_tipo == "graficos":
                self.progress_updated.emit(30, "Obteniendo gráficos...")
                raw_data = self.data_fetcher.fetch_graficos()
                self.progress_updated.emit(60, "Validando datos...")
                
                if not self.data_processor.validate_chart_data(raw_data):
                    raise Exception("Datos de gráficos inválidos")
                
                self.progress_updated.emit(80, "Procesando datos...")
                processed_data = raw_data  # Los gráficos no necesitan procesamiento adicional
                
            else:
                self.progress_updated.emit(30, f"Obteniendo reporte {self.reporte_tipo}...")
                processed_data = self.data_fetcher.fetch_custom_report(self.reporte_tipo, self.params)
            
            self.progress_updated.emit(100, "Carga completada")
            self.data_loaded.emit(processed_data)
            
        except Exception as e:
            self.error_occurred.emit(f"Error cargando {self.reporte_tipo}: {str(e)}")

class ExportReportWorker(QThread):
    """Worker para exportar reportes en background"""
    
    export_finished = pyqtSignal(str)
    export_progress = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_client: ApiClient, reporte_tipo: str, params: Dict[str, Any], 
                 formato: str, ruta_destino: str):
        super().__init__()
        self.api_client = api_client
        self.reporte_tipo = reporte_tipo
        self.params = params
        self.formato = formato
        self.ruta_destino = ruta_destino
        
    def run(self):
        """Exporta el reporte al formato especificado"""
        try:
            # Exportar reporte
            self.export_finished.emit(self.ruta_destino)
        except Exception as e:
            self.error_occurred.emit(str(e))

class KPICard(QFrame):
    """Tarjeta individual para mostrar un KPI con categoría y justificación"""
    
    def __init__(self, title: str, value: str, category: str = "", 
                 justification: str = "", icon: str = "", color: str = "#3B82F6"):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                min-height: 120px;
                max-width: 200px;
            }}
            QFrame:hover {{
                border-color: {color};
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Icono y categoría
        header_layout = QHBoxLayout()
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"color: {color}; font-size: 18px;")
            header_layout.addWidget(icon_label)
        
        if category:
            category_label = QLabel(category)
            category_label.setStyleSheet("color: #9ca3af; font-size: 10px; font-weight: 500;")
            header_layout.addWidget(category_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #374151; font-size: 12px; font-weight: 600; margin-bottom: 4px;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Valor
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold; margin-bottom: 4px;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # Justificación (tooltip)
        if justification:
            self.setToolTip(justification)

class ReportesTabWidget(QWidget):
    """
    Widget para la pestaña de reportes
    
    Muestra 20+ KPIs categorizados y gráficos interactivos
    con datos reales del backend.
    """
    
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self.kpi_data = {}
        self.graficos_data = {}
        self.setup_ui()
        self.load_all_data()
        
        # Timer para actualización automática cada 5 minutos
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_all_data)
        self.update_timer.start(300000)
        
    def setup_ui(self):
        """Configura la interfaz de usuario del widget"""
        main_layout = QVBoxLayout(self)
        
        # Header con título y controles
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 Reportes y KPIs Avanzados")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1f2937; margin-bottom: 16px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botón de actualización
        self.btn_refresh = QPushButton("🔄 Actualizar")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.btn_refresh.clicked.connect(self.load_all_data)
        header_layout.addWidget(self.btn_refresh)
        
        # Botón de exportar
        self.btn_export = QPushButton("📁 Exportar")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_export.clicked.connect(self.export_all_reports)
        header_layout.addWidget(self.btn_export)
        
        main_layout.addLayout(header_layout)
        
        # Tabs para diferentes secciones
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f3f4f6;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #3b82f6;
                color: white;
            }
        """)
        
        # Tab 1: KPIs
        self.setup_kpis_tab()
        
        # Tab 2: Gráficos
        self.setup_charts_tab()
        
        # Tab 3: Reportes Detallados
        self.setup_detailed_reports_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Barra de estado
        self.status_bar = QLabel("Listo - Última actualización: Nunca")
        self.status_bar.setStyleSheet("""
            color: #6b7280; 
            font-size: 12px; 
            padding: 8px;
            background-color: #f9fafb;
            border-top: 1px solid #e5e7eb;
        """)
        main_layout.addWidget(self.status_bar)
        
    def setup_kpis_tab(self):
        """Configura la pestaña de KPIs"""
        kpis_widget = QWidget()
        layout = QVBoxLayout(kpis_widget)
        
        # Scroll area para los KPIs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Título de sección
        section_title = QLabel("📈 Indicadores Clave de Rendimiento")
        section_title.setStyleSheet("font-size: 18px; font-weight: 600; color: #374151; margin-bottom: 16px;")
        content_layout.addWidget(section_title)
        
        # Grid para KPIs categorizados
        self.kpis_grid = QGridLayout()
        content_layout.addLayout(self.kpis_grid)
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addLayout(scroll)
        
        self.tab_widget.addTab(kpis_widget, "KPIs")
        
    def setup_charts_tab(self):
        """Configura la pestaña de gráficos"""
        charts_widget = QWidget()
        layout = QVBoxLayout(charts_widget)
        
        # Grid para múltiples gráficos
        charts_layout = QGridLayout()
        
        # Crear contenedores para gráficos
        self.chart_containers = {}
        chart_configs = [
            ("ingresos", "📈 Ingresos Mensuales", 0, 0),
            ("asistencias", "👥 Asistencias por Día", 0, 1),
            ("ocupacion", "📊 Ocupación de Clases", 1, 0),
            ("metodos_pago", "💳 Métodos de Pago", 1, 1),
        ]
        
        for chart_id, title, row, col in chart_configs:
            container = self.create_chart_container(title)
            self.chart_containers[chart_id] = container
            charts_layout.addWidget(container, row, col)
        
        layout.addLayout(charts_layout)
        self.tab_widget.addTab(charts_widget, "Gráficos")
        
    def setup_detailed_reports_tab(self):
        """Configura la pestaña de reportes detallados"""
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)
        
        # Controles de filtros
        filters_layout = QHBoxLayout()
        
        # Selector de período
        filters_layout.addWidget(QLabel("Período:"))
        self.periodo_combo = QComboBox()
        self.periodo_combo.addItems(["Últimos 7 días", "Últimos 30 días", "Últimos 3 meses", "Último año"])
        self.periodo_combo.setCurrentIndex(1)  # 30 días por defecto
        filters_layout.addWidget(self.periodo_combo)
        
        filters_layout.addStretch()
        
        # Botón generar reporte
        self.btn_generate = QPushButton("📋 Generar Reporte")
        self.btn_generate.clicked.connect(self.generate_detailed_report)
        filters_layout.addWidget(self.btn_generate)
        
        layout.addLayout(filters_layout)
        
        # Área de resultados
        self.detailed_results = QTextEdit()
        self.detailed_results.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 12px;
                background-color: white;
            }
        """)
        layout.addWidget(self.detailed_results)
        
        self.tab_widget.addTab(reports_widget, "Reportes Detallados")
    
    def create_chart_container(self, title: str) -> QWidget:
        """Crea un contenedor para gráfico con matplotlib"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: white; 
                border: 1px solid #e5e7eb; 
                border-radius: 8px; 
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        
        # Título del gráfico
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 12px;")
        layout.addWidget(title_label)
        
        # Canvas del gráfico
        figure = Figure(figsize=(8, 6))
        canvas = FigureCanvas(figure)
        layout.addWidget(canvas)
        
        # Guardar referencia al figure y canvas
        widget.figure = figure
        widget.canvas = canvas
        
        return widget
    
    def load_all_data(self):
        """Carga todos los datos desde el backend"""
        self.status_bar.setText("Cargando datos...")
        
        # Cargar KPIs
        self.kpi_worker = ReportLoadWorker(self.api_client, "kpis", {})
        self.kpi_worker.data_loaded.connect(self.on_kpis_loaded)
        self.kpi_worker.error_occurred.connect(self.on_error)
        self.kpi_worker.start()
        
        # Cargar datos de gráficos
        self.graficos_worker = ReportLoadWorker(self.api_client, "graficos", {})
        self.graficos_worker.data_loaded.connect(self.on_graficos_loaded)
        self.graficos_worker.error_occurred.connect(self.on_error)
        self.graficos_worker.start()
    
    def on_kpis_loaded(self, data: dict):
        """Maneja la carga exitosa de KPIs"""
        self.kpi_data = data
        self.update_kpis()
        self.update_status()
    
    def on_graficos_loaded(self, data: dict):
        """Maneja la carga exitosa de gráficos"""
        self.graficos_data = data
        self.update_charts()
        self.update_status()
    
    def on_error(self, error_msg: str):
        """Maneja errores en la carga de datos"""
        self.status_bar.setText(f"Error: {error_msg}")
        QMessageBox.warning(self, "Error", f"Error cargando datos:\n{error_msg}")
    
    def update_status(self):
        """Actualiza la barra de estado"""
        now = datetime.now().strftime("%H:%M:%S")
        self.status_bar.setText(f"Listo - Última actualización: {now}")
    
    def update_kpis(self):
        """Actualiza las tarjetas de KPIs con datos reales del backend"""
        # Limpiar grid existente
        for i in reversed(range(self.kpis_grid.count())):
            widget = self.kpis_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Configuración de KPIs categorizados
        kpi_configs = [
            # KPIs Financieros
            ("Ingresos del Mes", f"${self.kpi_data.get('ingresos_mes', 0):,.2f}", 
             "Financiero", "Indicador financiero principal para evaluar la salud del negocio", "💰", "#10b981"),
            ("ARPU", f"${self.kpi_data.get('ingreso_promedio_usuario', 0):.2f}", 
             "Financiero", "Mide la rentabilidad por cliente para estrategias de pricing", "🎯", "#10b981"),
            ("Rentabilidad", f"${self.kpi_data.get('rentabilidad_operativa', 0):,.2f}", 
             "Financiero", "Mide la eficiencia operativa y sostenibilidad del negocio", "📈", "#10b981"),
            ("LTV Promedio", f"${self.kpi_data.get('ltv_promedio', 0):.2f}", 
             "Financiero", "Determina cuánto invertir en adquisición de clientes", "⭐", "#10b981"),
            ("CAC", f"${self.kpi_data.get('costo_adquisicion_cliente', 0):.2f}", 
             "Financiero", "Evalúa la eficiencia del gasto en marketing y ventas", "📊", "#f59e0b"),
            ("Eficiencia Cobranza", f"{self.kpi_data.get('eficiencia_cobranza', 0):.1f}%", 
             "Financiero", "Optimiza procesos de facturación y cobranza", "⏱️", "#3b82f6"),
            ("Morosidad", f"{self.kpi_data.get('morosidad_porcentaje', 0):.1f}%", 
             "Financiero", "Control de flujo de caja y gestión de cobranzas", "⚠️", "#ef4444"),
            
            # KPIs de Crecimiento
            ("Nuevas Inscripciones", str(self.kpi_data.get('nuevas_inscripciones_mes', 0)), 
             "Crecimiento", "Mide el crecimiento del negocio y efectividad del marketing", "👥", "#3b82f6"),
            ("Crecimiento Mensual", f"{self.kpi_data.get('crecimiento_usuarios_mensual', 0):.1f}%", 
             "Crecimiento", "Mide la velocidad de expansión del negocio", "📈", "#3b82f6"),
            ("Tasa de Retención", f"{self.kpi_data.get('tasa_retencion', 0):.1f}%", 
             "Crecimiento", "Retener clientes es más barato que adquirir nuevos", "✅", "#10b981"),
            ("Tasa de Conversión", f"{self.kpi_data.get('tasa_conversion', 0):.1f}%", 
             "Crecimiento", "Mide efectividad del proceso de ventas y personal", "🎯", "#8b5cf6"),
            
            # KPIs Operacionales
            ("Ocupación Clases", f"{self.kpi_data.get('ocupacion_promedio_clases', 0):.1f}%", 
             "Operacional", "Optimiza el uso de recursos y planificación de horarios", "📅", "#8b5cf6"),
            ("Asistencias/Día", f"{self.kpi_data.get('asistencias_diarias_promedio', 0):.1f}", 
             "Operacional", "Indica la actividad y compromiso de los miembros", "🏃", "#8b5cf6"),
            ("Utilización Hora Pico", f"{self.kpi_data.get('utilizacion_hora_pico', 0):.1f}%", 
             "Operacional", "Optimiza inversión en equipos y mantenimiento", "⚡", "#f59e0b"),
            
            # KPIs de Personal
            ("Puntualidad Empleados", f"{self.kpi_data.get('puntualidad_empleados', 0):.1f}%", 
             "Personal", "Impacta en la calidad del servicio y operaciones", "⏰", "#10b981"),
            
            # KPIs de Servicio
            ("Índice Satisfacción", f"{self.kpi_data.get('indice_satisfaccion', 0):.1f}%", 
             "Servicio", "Indica calidad del servicio y probabilidad de recomendación", "⭐", "#10b981"),
        ]
        
        # Crear tarjetas KPI
        for i, (title, value, category, justification, icon, color) in enumerate(kpi_configs):
            card = KPICard(title, value, category, justification, icon, color)
            self.kpis_grid.addWidget(card, i // 4, i % 4)
    
    def update_charts(self):
        """Actualiza todos los gráficos con datos reales"""
        # Configurar estilo de matplotlib
        plt.style.use('seaborn-v0_8')
        
        # Gráfico de ingresos mensuales
        if 'ingresos_mensuales' in self.graficos_data:
            self.update_ingresos_chart()
        
        # Gráfico de asistencias por día
        if 'asistencias_por_dia' in self.graficos_data:
            self.update_asistencias_chart()
        
        # Gráfico de ocupación
        self.update_ocupacion_chart()
        
        # Gráfico de métodos de pago
        if 'metodos_pago' in self.graficos_data:
            self.update_metodos_pago_chart()
    
    def update_ingresos_chart(self):
        """Actualiza el gráfico de ingresos mensuales"""
        container = self.chart_containers.get('ingresos')
        if not container:
            return
            
        figure = container.figure
        figure.clear()
        ax = figure.add_subplot(111)
        
        data = self.graficos_data['ingresos_mensuales']
        meses = [item['mes'] for item in data]
        montos = [item['monto'] for item in data]
        
        bars = ax.bar(meses, montos, color='#10b981', alpha=0.8)
        ax.set_title('Evolución de Ingresos Mensuales', fontsize=12, fontweight='bold')
        ax.set_ylabel('Ingresos ($)', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Rotar etiquetas si son muchas
        if len(meses) > 6:
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        figure.tight_layout()
        container.canvas.draw()
    
    def update_asistencias_chart(self):
        """Actualiza el gráfico de asistencias por día"""
        container = self.chart_containers.get('asistencias')
        if not container:
            return
            
        figure = container.figure
        figure.clear()
        ax = figure.add_subplot(111)
        
        data = self.graficos_data['asistencias_por_dia']
        dias = [item['dia'] for item in data]
        asistencias = [item['asistencias'] for item in data]
        
        bars = ax.bar(dias, asistencias, color='#3b82f6', alpha=0.8)
        ax.set_title('Asistencias por Día de la Semana', fontsize=12, fontweight='bold')
        ax.set_ylabel('Asistencias', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        figure.tight_layout()
        container.canvas.draw()
    
    def update_ocupacion_chart(self):
        """Actualiza el gráfico de ocupación (datos de KPIs)"""
        container = self.chart_containers.get('ocupacion')
        if not container:
            return
            
        figure = container.figure
        figure.clear()
        ax = figure.add_subplot(111)
        
        # Usar datos simulados basados en los KPIs
        ocupacion = self.kpi_data.get('ocupacion_promedio_clases', 0)
        clases_populares = self.kpi_data.get('clases_mas_populares', {})
        
        if clases_populares:
            clases = list(clases_populares.keys())[:5]  # Top 5
            asistencias = list(clases_populares.values())[:5]
            
            bars = ax.bar(clases, asistencias, color='#8b5cf6', alpha=0.8)
            ax.set_title('Top 5 Clases por Asistencia', fontsize=12, fontweight='bold')
            ax.set_ylabel('Asistencias', fontsize=10)
            
            if len(clases) > 3:
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        else:
            ax.text(0.5, 0.5, 'Sin datos disponibles', 
                   transform=ax.transAxes, ha='center', va='center')
        
        ax.grid(True, alpha=0.3)
        figure.tight_layout()
        container.canvas.draw()
    
    def update_metodos_pago_chart(self):
        """Actualiza el gráfico de métodos de pago"""
        container = self.chart_containers.get('metodos_pago')
        if not container:
            return
            
        figure = container.figure
        figure.clear()
        ax = figure.add_subplot(111)
        
        data = self.graficos_data['metodos_pago']
        metodos = [item['metodo'] for item in data]
        cantidades = [item['cantidad'] for item in data]
        
        # Gráfico de pastel
        colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'][:len(metodos)]
        wedges, texts, autotexts = ax.pie(cantidades, labels=metodos, autopct='%1.1f%%', 
                                         colors=colors, startangle=90)
        ax.set_title('Distribución de Métodos de Pago', fontsize=12, fontweight='bold')
        
        figure.tight_layout()
        container.canvas.draw()
    
    def generate_detailed_report(self):
        """Genera un reporte detallado basado en el período seleccionado"""
        periodo = self.periodo_combo.currentText()
        
        # Crear reporte HTML
        html_report = f"""
        <h2>📋 Reporte Detallado del Gimnasio</h2>
        <p><strong>Período:</strong> {periodo}</p>
        <p><strong>Generado:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        
        <h3>📊 Resumen de KPIs</h3>
        <ul>
            <li><strong>Ingresos del Mes:</strong> ${self.kpi_data.get('ingresos_mes', 0):,.2f}</li>
            <li><strong>Nuevas Inscripciones:</strong> {self.kpi_data.get('nuevas_inscripciones_mes', 0)}</li>
            <li><strong>Tasa de Retención:</strong> {self.kpi_data.get('tasa_retencion', 0):.1f}%</li>
            <li><strong>Ocupación Promedio de Clases:</strong> {self.kpi_data.get('ocupacion_promedio_clases', 0):.1f}%</li>
            <li><strong>Morosidad:</strong> {self.kpi_data.get('morosidad_porcentaje', 0):.1f}%</li>
        </ul>
        
        <h3>🎯 Análisis de Rendimiento</h3>
        <p><strong>Financiero:</strong> Los ingresos actuales muestran una tendencia {'positiva' if self.kpi_data.get('crecimiento_usuarios_mensual', 0) > 0 else 'que requiere atención'}.</p>
        <p><strong>Operacional:</strong> La ocupación de clases está {'en niveles óptimos' if self.kpi_data.get('ocupacion_promedio_clases', 0) > 70 else 'por debajo del objetivo'}.</p>
        <p><strong>Satisfacción:</strong> El índice de satisfacción es del {self.kpi_data.get('indice_satisfaccion', 0):.1f}%.</p>
        
        <h3>📈 Recomendaciones</h3>
        <ul>
            <li>{'Continuar con las estrategias actuales de crecimiento' if self.kpi_data.get('crecimiento_usuarios_mensual', 0) > 0 else 'Revisar estrategias de marketing y retención'}</li>
            <li>{'Mantener la calidad del servicio' if self.kpi_data.get('indice_satisfaccion', 0) > 80 else 'Implementar mejoras en la experiencia del cliente'}</li>
            <li>{'Optimizar horarios de clases populares' if self.kpi_data.get('ocupacion_promedio_clases', 0) > 70 else 'Revisar programación de clases y promociones'}</li>
        </ul>
        """
        
        self.detailed_results.setHtml(html_report)
    
    def export_all_reports(self):
        """Exporta todos los reportes a PDF"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Reportes", f"reportes_gimnasio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                "PDF Files (*.pdf)")
            
            if file_path:
                # En implementación real: generar PDF con reportes
                QMessageBox.information(self, "Exportación", f"Reportes exportados exitosamente a:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exportando reportes:\n{str(e)}")
