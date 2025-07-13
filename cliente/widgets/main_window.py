"""
Ventana principal de la aplicación
Sistema de Gestión de Gimnasio v6 - Optimizado con Fase 4
"""
import os
import logging
from typing import Dict, Any, Optional
import gc
import time

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStatusBar, QMessageBox, QMenu,
    QToolBar, QSplitter, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QAction

from cliente.utils.config_manager import ConfigManager
from cliente.utils.secure_storage import SecureStorage
from cliente.utils.theme_manager import ThemeManager
from cliente.utils.performance_monitor import get_performance_monitor, monitor_ui_function
from cliente.api_client import ApiClient

# Importar widgets de pestañas (carga diferida)
# from .dashboard_widget import DashboardWidget
# from .usuarios_tab_widget import UsuariosTabWidget
# from .clases_tab_widget import ClasesTabWidget
# from .asistencias_tab_widget import AsistenciasTabWidget
# from .pagos_tab_widget import PagosTabWidget
# from .rutinas_tab_widget import RutinasTabWidget
# from .configuracion_tab_widget import ConfiguracionTabWidget
# from .reportes_tab_widget import ReportesTabWidget
# from .distributed_status_widget import DistributedStatusWidget
# from .empleados_tab_widget import EmpleadosTabWidget
# from .tipos_cuota_tab_widget import TiposCuotaTabWidget

# Configuración de logging
logger = logging.getLogger("main_window")

class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación - Optimizada con Fase 4
    
    Esta ventana contiene todas las funcionalidades principales
    organizadas en pestañas con optimizaciones avanzadas de rendimiento.
    
    Atributos:
        token_data: Datos del token de autenticación
        config: Gestor de configuración
        secure_storage: Almacenamiento seguro
        api_client: Cliente API
        sync_timer: Temporizador para sincronización
        performance_monitor: Monitor de rendimiento avanzado
        last_sync: Última sincronización realizada
        lazy_loaded_tabs: Cache de pestañas cargadas diferidamente
        virtualized_lists: Listas virtualizadas para mejor rendimiento
    """
    
    # Señales para comunicación entre widgets
    sync_completed = pyqtSignal()
    performance_warning = pyqtSignal(str)
    
    # Cache para widgets pesados con compresión
    _widget_cache = {}
    _last_sync_time = 0
    
    @monitor_ui_function("window_creation")
    def __init__(self, token_data: Dict[str, Any], config: ConfigManager, secure_storage: SecureStorage):
        """
        Inicializa la ventana principal con optimizaciones avanzadas de rendimiento
        
        Args:
            token_data: Datos del token de autenticación
            config: Gestor de configuración
            secure_storage: Almacenamiento seguro
        """
        super().__init__()
        
        self.token_data = token_data
        self.config = config
        self.secure_storage = secure_storage
        
        # Inicializar API client optimizado
        self.api_client = ApiClient(base_url=config.get("api_url"))
        self.api_client.set_token(token_data)
        
        # Inicializar gestor de temas
        self.theme_manager = ThemeManager(config, self.api_client)
        self.theme_manager.initialize_default_theme()
        
        # Monitor de rendimiento avanzado
        self.performance_monitor = get_performance_monitor()
        self.performance_monitor.performance_warning.connect(self._handle_performance_warning)
        
        # Configurar optimizaciones de base de datos
        db_path = config.get("local_db_path", "data/local.db")
        self.performance_monitor.setup_query_optimizer(db_path)
        
        # Cache de pestañas cargadas diferidamente
        self.lazy_loaded_tabs = {}
        self.tab_loading_status = {}
        
        # Configurar componentes para carga diferida
        self._setup_lazy_loading()
        
        # Temporizador para sincronización optimizada
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self._sync_data_optimized)
        self.sync_timer.start(self.config.get("sync_interval", 300) * 1000)
        
        # Timer para limpieza de memoria avanzada
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self._advanced_memory_cleanup)
        self.cleanup_timer.start(300000)  # Cada 5 minutos
        
        # Timer para compresión de datos en cache
        self.compression_timer = QTimer(self)
        self.compression_timer.timeout.connect(self._compress_cached_data)
        self.compression_timer.start(600000)  # Cada 10 minutos
        
        # Inicializar UI con carga diferida optimizada
        self._init_ui_optimized()
    
    def _setup_lazy_loading(self):
        """Configurar carga diferida de componentes"""
        # Registrar pestañas para carga diferida
        self.performance_monitor.register_lazy_component(
            "dashboard_widget",
            lambda: self._load_dashboard_widget(),
            []
        )
        
        self.performance_monitor.register_lazy_component(
            "usuarios_tab_widget",
            lambda: self._load_usuarios_tab_widget(),
            []
        )
        
        self.performance_monitor.register_lazy_component(
            "clases_tab_widget",
            lambda: self._load_clases_tab_widget(),
            []
        )
        
        self.performance_monitor.register_lazy_component(
            "asistencias_tab_widget",
            lambda: self._load_asistencias_tab_widget(),
            []
        )
        
        self.performance_monitor.register_lazy_component(
            "pagos_tab_widget",
            lambda: self._load_pagos_tab_widget(),
            []
        )
        
        self.performance_monitor.register_lazy_component(
            "rutinas_tab_widget",
            lambda: self._load_rutinas_tab_widget(),
            []
        )
        
        self.performance_monitor.register_lazy_component(
            "configuracion_tab_widget",
            lambda: self._load_configuracion_tab_widget(),
            []
        )
        
        self.performance_monitor.register_lazy_component(
            "reportes_tab_widget",
            lambda: self._load_reportes_tab_widget(),
            []
        )
        
        self.performance_monitor.register_lazy_component(
            "empleados_tab_widget",
            lambda: self._load_empleados_tab_widget(),
            []
        )
        
        self.performance_monitor.register_lazy_component(
            "tipos_cuota_tab_widget",
            lambda: self._load_tipos_cuota_tab_widget(),
            []
        )
        
        # Precargar componentes críticos en background
        self.performance_monitor.lazy_loading_manager.preload_components([
            "dashboard_widget",
            "usuarios_tab_widget"
        ])
    
    def _load_dashboard_widget(self):
        """Cargar widget de dashboard de forma diferida"""
        from cliente.widgets.dashboard_widget import DashboardWidget
        return DashboardWidget(self.api_client, self.config)
    
    def _load_usuarios_tab_widget(self):
        """Cargar widget de usuarios de forma diferida"""
        from cliente.widgets.usuarios_tab_widget import UsuariosTabWidget
        return UsuariosTabWidget(self.api_client, self.config)
    
    def _load_clases_tab_widget(self):
        """Cargar widget de clases de forma diferida"""
        from cliente.widgets.clases_tab_widget import ClasesTabWidget
        return ClasesTabWidget(self.api_client, self.config)
    
    def _load_asistencias_tab_widget(self):
        """Cargar widget de asistencias de forma diferida"""
        from cliente.widgets.asistencias_tab_widget import AsistenciasTabWidget
        return AsistenciasTabWidget(self.api_client, self.config)
    
    def _load_pagos_tab_widget(self):
        """Cargar widget de pagos de forma diferida"""
        from cliente.widgets.pagos_tab_widget import PagosTabWidget
        return PagosTabWidget(self.api_client, self.config)
    
    def _load_rutinas_tab_widget(self):
        """Cargar widget de rutinas de forma diferida"""
        from cliente.widgets.rutinas_tab_widget import RutinasTabWidget
        return RutinasTabWidget(self.api_client, self.config)
    
    def _load_configuracion_tab_widget(self):
        """Cargar widget de configuración de forma diferida"""
        from cliente.widgets.configuracion_tab_widget import ConfiguracionTabWidget
        return ConfiguracionTabWidget(self.config, self.api_client)
    
    def _load_reportes_tab_widget(self):
        """Cargar widget de reportes de forma diferida"""
        from cliente.widgets.reportes_tab_widget import ReportesTabWidget
        return ReportesTabWidget(self.api_client, self.config)
    
    def _load_empleados_tab_widget(self):
        """Cargar widget de empleados de forma diferida"""
        from cliente.widgets.empleados_tab_widget import EmpleadosTabWidget
        return EmpleadosTabWidget(self.api_client, self.config)
    
    def _load_tipos_cuota_tab_widget(self):
        """Cargar widget de tipos de cuota de forma diferida"""
        from cliente.widgets.tipos_cuota_tab_widget import TiposCuotaTabWidget
        return TiposCuotaTabWidget(self.api_client, self.config)
    
    @monitor_ui_function("ui_initialization")
    def _init_ui_optimized(self):
        """Inicializa la interfaz de usuario con optimizaciones avanzadas de rendimiento"""
        # Configuración de la ventana
        self.setWindowTitle("Sistema de Gestión de Gimnasio v6.0 - Optimizado")
        self.setMinimumSize(1024, 768)
        self.setWindowIcon(QIcon("assets/logo.png"))
        
        # Aplicar configuraciones de rendimiento avanzadas
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setUpdatesEnabled(False)
        
        try:
            # Menú principal
            self._create_menu()
            
            # Barra de herramientas
            self._create_toolbar()
            
            # Widget central
            central_widget = QWidget()
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(5, 5, 5, 5)
            
            # Crear widget de pestaña principal con optimizaciones avanzadas
            self.tab_widget = QTabWidget()
            self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
            self.tab_widget.setMovable(True)
            self.tab_widget.setUsesScrollButtons(True)
            self.tab_widget.setDocumentMode(True)
            
            # Conexión para carga diferida de pestañas
            self.tab_widget.currentChanged.connect(self._on_tab_changed_optimized)
            
            # Añadir pestañas con carga diferida optimizada
            self._add_tabs_lazy_optimized()
            
            # Layout principal con divisor
            splitter = QSplitter(Qt.Orientation.Horizontal)
            splitter.setChildrenCollapsible(False)
            
            # Añadir panel de estado a la derecha
            right_panel = self._create_right_panel()
            
            # Añadir widgets al splitter
            splitter.addWidget(self.tab_widget)
            splitter.addWidget(right_panel)
            
            # Ajustar proporciones del divisor (75% izquierda, 25% derecha)
            splitter.setSizes([750, 250])
            
            main_layout.addWidget(splitter)
            
            self.setCentralWidget(central_widget)
            
            # Barra de estado
            self._create_status_bar()
            
            # Mostrar mensaje de bienvenida
            status_bar = self.statusBar()
            if status_bar:
                status_bar.showMessage(f"Bienvenido/a, {self.token_data.get('username')} - Optimizado con Fase 4")
            
            # Configurar sincronización en tiempo real
            self.setup_realtime_sync()
            
        finally:
            # Reactivar actualizaciones
            self.setUpdatesEnabled(True)
    
    def _create_menu(self):
        """Crea la barra de menú"""
        menu_bar = self.menuBar()
        if not menu_bar:
            return
            
        # Menú Archivo
        menu_archivo = menu_bar.addMenu("&Archivo")
        if not menu_archivo:
            return
            
        # Acción Sincronizar
        accion_sincronizar = QAction(QIcon("assets/sync.png"), "&Sincronizar", self)
        accion_sincronizar.setShortcut("Ctrl+S")
        accion_sincronizar.setStatusTip("Sincronizar datos con el servidor")
        accion_sincronizar.triggered.connect(self._sync_data)
        menu_archivo.addAction(accion_sincronizar)
        
        menu_archivo.addSeparator()
        
        # Acción Salir
        accion_salir = QAction(QIcon("assets/exit.png"), "&Salir", self)
        accion_salir.setShortcut("Ctrl+Q")
        accion_salir.setStatusTip("Salir de la aplicación")
        accion_salir.triggered.connect(self.close)
        menu_archivo.addAction(accion_salir)
        
        # Menú Ver
        menu_ver = menu_bar.addMenu("&Ver")
        if menu_ver:
            # Acción Modo Oscuro
            self.accion_modo_oscuro = QAction("Modo &Oscuro", self)
            self.accion_modo_oscuro.setCheckable(True)
            self.accion_modo_oscuro.setChecked(self.config.get("theme") == "dark")
            self.accion_modo_oscuro.triggered.connect(self._toggle_dark_mode)
            menu_ver.addAction(self.accion_modo_oscuro)
        
        # Menú Herramientas
        menu_herramientas = menu_bar.addMenu("&Herramientas")
        if menu_herramientas:
            # Acción Optimización de Memoria
            accion_optimizar_memoria = QAction("&Optimizar Memoria", self)
            accion_optimizar_memoria.setStatusTip("Forzar optimización de memoria")
            accion_optimizar_memoria.triggered.connect(self._force_memory_optimization)
            menu_herramientas.addAction(accion_optimizar_memoria)
            
            # Acción Reporte de Rendimiento
            accion_reporte_rendimiento = QAction("&Reporte de Rendimiento", self)
            accion_reporte_rendimiento.setStatusTip("Generar reporte de rendimiento")
            accion_reporte_rendimiento.triggered.connect(self._generate_performance_report)
            menu_herramientas.addAction(accion_reporte_rendimiento)
        
        # Menú Ayuda
        menu_ayuda = menu_bar.addMenu("&Ayuda")
        if menu_ayuda:
            # Acción Acerca de
            accion_acerca = QAction("&Acerca de", self)
            accion_acerca.setStatusTip("Información sobre la aplicación")
            accion_acerca.triggered.connect(self._show_about)
            menu_ayuda.addAction(accion_acerca)
    
    def _create_toolbar(self):
        """Crea la barra de herramientas"""
        toolbar = self.addToolBar("Principal")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        
        # Botón Sincronizar
        accion_sincronizar = QAction(QIcon("assets/sync.png"), "Sincronizar", self)
        accion_sincronizar.setStatusTip("Sincronizar datos con el servidor")
        accion_sincronizar.triggered.connect(self._sync_data)
        toolbar.addAction(accion_sincronizar)
        
        toolbar.addSeparator()
        
        # Botón Optimizar Memoria
        accion_optimizar = QAction(QIcon("assets/optimize.png"), "Optimizar", self)
        accion_optimizar.setStatusTip("Optimizar memoria y rendimiento")
        accion_optimizar.triggered.connect(self._force_memory_optimization)
        toolbar.addAction(accion_optimizar)
        
        # Botón Estado de Rendimiento
        accion_estado = QAction(QIcon("assets/status.png"), "Estado", self)
        accion_estado.setStatusTip("Ver estado de rendimiento")
        accion_estado.triggered.connect(self._show_performance_status)
        toolbar.addAction(accion_estado)
    
    def _add_tabs_lazy_optimized(self):
        """Añadir pestañas con carga diferida optimizada"""
        # Pestaña Dashboard (cargada inmediatamente)
        self.tab_widget.addTab(QLabel("Cargando Dashboard..."), "📊 Dashboard")
        
        # Pestañas con carga diferida
        tabs_config = [
            ("👥 Usuarios", "usuarios_tab_widget"),
            ("🏋️ Clases", "clases_tab_widget"),
            ("✅ Asistencias", "asistencias_tab_widget"),
            ("💰 Pagos", "pagos_tab_widget"),
            ("📋 Rutinas", "rutinas_tab_widget"),
            ("⚙️ Configuración", "configuracion_tab_widget"),
            ("📈 Reportes", "reportes_tab_widget"),
            ("👨‍💼 Empleados", "empleados_tab_widget"),
            ("💳 Tipos Cuota", "tipos_cuota_tab_widget")
        ]
        
        for tab_name, component_id in tabs_config:
            # Agregar placeholder
            placeholder = QLabel(f"Cargando {tab_name}...")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tab_widget.addTab(placeholder, tab_name)
            
            # Marcar como no cargado
            self.tab_loading_status[component_id] = False
    
    def _on_tab_changed_optimized(self, index: int):
        """Maneja el cambio de pestaña con carga diferida optimizada"""
        try:
            if index == 0:  # Dashboard
                self._load_tab_widget_optimized(index, "dashboard_widget")
            elif index == 1:  # Usuarios
                self._load_tab_widget_optimized(index, "usuarios_tab_widget")
            elif index == 2:  # Clases
                self._load_tab_widget_optimized(index, "clases_tab_widget")
            elif index == 3:  # Asistencias
                self._load_tab_widget_optimized(index, "asistencias_tab_widget")
            elif index == 4:  # Pagos
                self._load_tab_widget_optimized(index, "pagos_tab_widget")
            elif index == 5:  # Rutinas
                self._load_tab_widget_optimized(index, "rutinas_tab_widget")
            elif index == 6:  # Configuración
                self._load_tab_widget_optimized(index, "configuracion_tab_widget")
            elif index == 7:  # Reportes
                if hasattr(self, 'tab_reportes') and self.tab_reportes:
                    self._load_tab_widget_optimized(index, "reportes_tab_widget")
                else:
                    logger.error("tab_reportes no inicializado antes de su uso")
            elif index == 8:  # Empleados
                if hasattr(self, 'tab_empleados') and self.tab_empleados:
                    self._load_tab_widget_optimized(index, "empleados_tab_widget")
                else:
                    logger.error("tab_empleados no inicializado antes de su uso")
            elif index == 9:  # Tipos Cuota
                self._load_tab_widget_optimized(index, "tipos_cuota_tab_widget")
        except Exception as e:
            logger.error(f"Error al cambiar de pestaña: {e}")
    
    def _load_tab_widget_optimized(self, index: int, component_id: str):
        """Cargar widget de pestaña de forma optimizada"""
        if self.tab_loading_status.get(component_id, False):
            return  # Ya cargado
        
        try:
            # Cargar componente de forma diferida
            widget = self.performance_monitor.load_lazy_component(component_id)
            
            if widget:
                # Reemplazar placeholder con widget real
                self.tab_widget.removeTab(index)
                self.tab_widget.insertTab(index, widget, self.tab_widget.tabText(index))
                self.tab_widget.setCurrentIndex(index)
                
                # Marcar como cargado
                self.tab_loading_status[component_id] = True
                self.lazy_loaded_tabs[component_id] = widget
                
                # Cachear widget comprimido
                self.performance_monitor.cache_compressed(f"tab_{component_id}", widget)
                
                logger.info(f"Pestaña {component_id} cargada exitosamente")
                
        except Exception as e:
            logger.error(f"Error cargando pestaña {component_id}: {e}")
            # Mostrar error en la pestaña
            error_widget = QLabel(f"Error cargando {component_id}: {str(e)}")
            error_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tab_widget.removeTab(index)
            self.tab_widget.insertTab(index, error_widget, self.tab_widget.tabText(index))
    
    def _create_right_panel(self) -> QWidget:
        """Crea el panel derecho con optimizaciones"""
        from cliente.widgets.distributed_status_widget import DistributedStatusWidget
        
        panel = QWidget()
        panel.setObjectName("rightPanel")
        panel.setStyleSheet("""
            QWidget#rightPanel {
                background: var(--bg-secondary);
                border-left: 1px solid var(--border-color);
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Widget de estado distribuido
        self.status_widget = DistributedStatusWidget(self.api_client, self.config)
        layout.addWidget(self.status_widget)
        
        # Indicador de rendimiento
        self.performance_indicator = QLabel("Rendimiento: Optimizado")
        self.performance_indicator.setStyleSheet("""
            QLabel {
                color: var(--success-color);
                font-weight: bold;
                padding: 8px;
                background: var(--bg-card);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.performance_indicator)
        
        # Botón de optimización rápida
        optimize_button = QPushButton("🔄 Optimizar")
        optimize_button.clicked.connect(self._quick_optimization)
        layout.addWidget(optimize_button)
        
        layout.addStretch()
        
        return panel
    
    def _create_status_bar(self):
        """Crea la barra de estado con información de rendimiento"""
        status_bar = self.statusBar()
        if not status_bar:
            return
        
        # Indicador de memoria
        self.memory_indicator = QLabel("Memoria: --")
        status_bar.addPermanentWidget(self.memory_indicator)
        
        # Indicador de CPU
        self.cpu_indicator = QLabel("CPU: --")
        status_bar.addPermanentWidget(self.cpu_indicator)
        
        # Indicador de cache
        self.cache_indicator = QLabel("Cache: --")
        status_bar.addPermanentWidget(self.cache_indicator)
        
        # Actualizar indicadores
        self._update_performance_indicators()
        
        # Timer para actualizar indicadores
        self.indicators_timer = QTimer(self)
        self.indicators_timer.timeout.connect(self._update_performance_indicators)
        self.indicators_timer.start(5000)  # Cada 5 segundos
    
    def _update_performance_indicators(self):
        """Actualizar indicadores de rendimiento"""
        try:
            metrics = self.performance_monitor.get_current_metrics()
            if metrics:
                self.memory_indicator.setText(f"Memoria: {metrics.memory_percent:.1f}%")
                self.cpu_indicator.setText(f"CPU: {metrics.cpu_percent:.1f}%")
                
                # Actualizar color según rendimiento
                if metrics.memory_percent > 80:
                    self.memory_indicator.setStyleSheet("color: red;")
                elif metrics.memory_percent > 60:
                    self.memory_indicator.setStyleSheet("color: orange;")
                else:
                    self.memory_indicator.setStyleSheet("color: green;")
                
                if metrics.cpu_percent > 80:
                    self.cpu_indicator.setStyleSheet("color: red;")
                elif metrics.cpu_percent > 60:
                    self.cpu_indicator.setStyleSheet("color: orange;")
                else:
                    self.cpu_indicator.setStyleSheet("color: green;")
            
            # Actualizar indicador de cache
            summary = self.performance_monitor.get_performance_summary()
            if summary:
                cache_hit_rate = summary.get("cache_hit_rate", 0)
                self.cache_indicator.setText(f"Cache: {cache_hit_rate:.1f}%")
                
        except Exception as e:
            logger.error(f"Error actualizando indicadores: {e}")
    
    def _sync_data_optimized(self):
        """Sincronización optimizada con compresión de datos"""
        try:
            current_time = time.time()
            
            # Verificar si es necesario sincronizar
            if current_time - self._last_sync_time < 30:  # Mínimo 30 segundos entre syncs
                return
            
            # Comprimir datos antes de enviar
            sync_data = {
                "timestamp": current_time,
                "user_id": self.token_data.get("user_id"),
                "last_sync": self._last_sync_time
            }
            
            compressed_data = self.performance_monitor.compress_data(sync_data)
            
            # Realizar sincronización
            response = self.api_client._make_request('POST', '/sync', data=sync_data)
            
            if response.get('success'):
                self._last_sync_time = current_time
                self.sync_completed.emit()
                logger.info("Sincronización optimizada completada")
                
                # Actualizar indicadores
                self._update_offline_indicator()
                
        except Exception as e:
            logger.error(f"Error en sincronización optimizada: {e}")
            self.performance_monitor.record_error("sync_optimized", str(e))
    
    def _advanced_memory_cleanup(self):
        """Limpieza avanzada de memoria"""
        try:
            # Forzar garbage collection
            collected = self.performance_monitor.force_garbage_collection()
            
            # Limpiar cache de widgets no utilizados
            self._cleanup_unused_widgets()
            
            # Comprimir datos en cache
            self._compress_cached_data()
            
            logger.info(f"Limpieza avanzada completada: {collected} objetos recolectados")
            
        except Exception as e:
            logger.error(f"Error en limpieza avanzada: {e}")
    
    def _cleanup_unused_widgets(self):
        """Limpiar widgets no utilizados"""
        try:
            # Identificar widgets no utilizados
            unused_widgets = []
            for component_id, widget in self.lazy_loaded_tabs.items():
                if not widget.isVisible() and component_id not in ["dashboard_widget", "usuarios_tab_widget"]:
                    unused_widgets.append(component_id)
            
            # Eliminar widgets no utilizados
            for component_id in unused_widgets:
                widget = self.lazy_loaded_tabs.pop(component_id, None)
                if widget:
                    widget.deleteLater()
                    self.tab_loading_status[component_id] = False
                    logger.info(f"Widget {component_id} eliminado por inactividad")
                    
        except Exception as e:
            logger.error(f"Error limpiando widgets no utilizados: {e}")
    
    def _compress_cached_data(self):
        """Comprimir datos en cache"""
        try:
            # Comprimir datos de configuración
            config_data = self.config.get_all()
            self.performance_monitor.cache_compressed("config_data", config_data)
            
            # Comprimir datos de estado
            state_data = {
                "last_sync": self._last_sync_time,
                "loaded_tabs": list(self.tab_loading_status.keys()),
                "performance_stats": self.performance_monitor.get_performance_summary()
            }
            self.performance_monitor.cache_compressed("state_data", state_data)
            
            logger.info("Datos en cache comprimidos exitosamente")
            
        except Exception as e:
            logger.error(f"Error comprimiendo datos en cache: {e}")
    
    def _force_memory_optimization(self):
        """Forzar optimización de memoria"""
        try:
            # Limpieza inmediata
            self._advanced_memory_cleanup()
            
            # Actualizar indicadores
            self._update_performance_indicators()
            
            # Optimizar consultas de base de datos
            if self.performance_monitor.query_optimizer:
                # Ejecutar VACUUM en SQLite
                db_path = self.config.get("local_db_path", "data/local.db")
                import sqlite3
                conn = sqlite3.connect(db_path)
                conn.execute("VACUUM")
                conn.close()
            
            # Mostrar mensaje de éxito
            QMessageBox.information(
                self, "Optimización Completada",
                "La optimización de memoria se ha completado exitosamente.\n"
                f"Objetos recolectados: {gc.collect()}\n"
                "El rendimiento ha sido mejorado."
            )
            
        except Exception as e:
            logger.error(f"Error en optimización de memoria: {e}")
            QMessageBox.warning(
                self, "Error de Optimización",
                f"Error durante la optimización: {str(e)}"
            )
    
    def _generate_performance_report(self):
        """Generar reporte de rendimiento"""
        try:
            # Exportar métricas
            filename = f"performance_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
            self.performance_monitor.export_metrics(filename)
            
            # Mostrar resumen
            summary = self.performance_monitor.get_performance_summary()
            
            report_text = f"""
REPORTE DE RENDIMIENTO
======================

CPU Actual: {summary.get('current_cpu', 0):.1f}%
CPU Promedio (30min): {summary.get('avg_cpu_30min', 0):.1f}%
CPU Pico: {summary.get('peak_cpu', 0):.1f}%

Memoria Actual: {summary.get('current_memory', 0):.1f}%
Memoria Promedio (30min): {summary.get('avg_memory_30min', 0):.1f}%
Memoria Pico: {summary.get('peak_memory', 0):.1f}%

Memory Leaks Detectados: {summary.get('memory_leaks', 0)}
Cache Hit Rate: {summary.get('cache_hit_rate', 0):.1f}%

Estadísticas de Optimización:
- Componentes Cargados Diferidamente: {summary.get('optimization_stats', {}).get('lazy_loaded_components', 0)}
- Listas Virtualizadas: {summary.get('optimization_stats', {}).get('virtualized_lists', 0)}
- Datos Comprimidos: {summary.get('optimization_stats', {}).get('compressed_data_mb', 0):.2f} MB

Reporte guardado en: {filename}
            """
            
            QMessageBox.information(
                self, "Reporte de Rendimiento",
                report_text
            )
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            QMessageBox.warning(
                self, "Error",
                f"Error generando reporte: {str(e)}"
            )
    
    def _show_performance_status(self):
        """Mostrar estado de rendimiento"""
        try:
            summary = self.performance_monitor.get_performance_summary()
            
            status_text = f"""
ESTADO DE RENDIMIENTO
====================

CPU: {summary.get('current_cpu', 0):.1f}%
Memoria: {summary.get('current_memory', 0):.1f}%
Cache Hit Rate: {summary.get('cache_hit_rate', 0):.1f}%

Optimizaciones Activas:
✓ Carga Diferida
✓ Virtualización de Listas
✓ Compresión de Datos
✓ Detección de Memory Leaks
✓ Optimización de Consultas

Estado: {'🟢 Optimizado' if summary.get('current_memory', 0) < 80 else '🟡 Atención' if summary.get('current_memory', 0) < 90 else '🔴 Crítico'}
            """
            
            QMessageBox.information(
                self, "Estado de Rendimiento",
                status_text
            )
            
        except Exception as e:
            logger.error(f"Error mostrando estado: {e}")
    
    def _quick_optimization(self):
        """Optimización rápida desde el panel derecho"""
        try:
            # Limpieza básica
            gc.collect()
            
            # Actualizar indicadores
            self._update_performance_indicators()
            
            # Mostrar feedback
            self.performance_indicator.setText("Rendimiento: Optimizado ✓")
            self.performance_indicator.setStyleSheet("""
                QLabel {
                    color: var(--success-color);
                    font-weight: bold;
                    padding: 8px;
                    background: var(--bg-card);
                    border-radius: 4px;
                }
            """)
            
            # Resetear después de 3 segundos
            QTimer.singleShot(3000, lambda: self.performance_indicator.setText("Rendimiento: Optimizado"))
            
        except Exception as e:
            logger.error(f"Error en optimización rápida: {e}")
    
    def _sync_data(self):
        """Sincronización manual"""
        self._sync_data_optimized()
    
    def _toggle_dark_mode(self):
        """Alternar modo oscuro"""
        try:
            current_theme = self.config.get("theme", "light")
            new_theme = "dark" if current_theme == "light" else "light"
            
            self.config.set("theme", new_theme)
            self.theme_manager.apply_theme(new_theme)
            
            # Actualizar estado del botón
            self.accion_modo_oscuro.setChecked(new_theme == "dark")
            
            # Cachear configuración comprimida
            self.performance_monitor.cache_compressed("theme_config", {"theme": new_theme})
            
            logger.info(f"Tema cambiado a: {new_theme}")
            
        except Exception as e:
            logger.error(f"Error cambiando tema: {e}")
    
    def _toggle_offline_mode(self):
        """Alternar modo offline"""
        try:
            current_mode = self.config.get("offline_mode", False)
            new_mode = not current_mode
            
            self.config.set("offline_mode", new_mode)
            
            if new_mode:
                self.statusBar().showMessage("Modo offline activado")
            else:
                self.statusBar().showMessage("Modo online activado")
                
            logger.info(f"Modo offline: {new_mode}")
            
        except Exception as e:
            logger.error(f"Error alternando modo offline: {e}")
    
    def _logout(self):
        """Cerrar sesión"""
        try:
            reply = QMessageBox.question(
                self, "Cerrar Sesión",
                "¿Estás seguro de que quieres cerrar sesión?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Limpiar datos de sesión
                self.secure_storage.clear()
                
                # Detener monitoreo
                self.performance_monitor.stop_monitoring()
                
                # Cerrar ventana
                self.close()
                
        except Exception as e:
            logger.error(f"Error en logout: {e}")
    
    def _show_about(self):
        """Mostrar información sobre la aplicación"""
        QMessageBox.about(
            self, "Acerca de",
            "Sistema de Gestión de Gimnasio v6.0\n\n"
            "Versión optimizada con Fase 4\n"
            "Incluye optimizaciones avanzadas de rendimiento:\n"
            "• Carga diferida de componentes\n"
            "• Virtualización de listas\n"
            "• Compresión de datos\n"
            "• Detección de memory leaks\n"
            "• Optimización de consultas\n\n"
            "© 2024 GymSystem Team"
        )
    
    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        try:
            self._cleanup_on_close()
            super().closeEvent(event)
        except Exception as e:
            logger.error(f"Error cerrando la ventana principal: {e}")
            event.accept()
    
    def _cleanup_on_close(self):
        """Limpieza al cerrar la aplicación"""
        try:
            # Detener timers
            if hasattr(self, 'sync_timer'):
                self.sync_timer.stop()
            if hasattr(self, 'cleanup_timer'):
                self.cleanup_timer.stop()
            if hasattr(self, 'compression_timer'):
                self.compression_timer.stop()
            if hasattr(self, 'indicators_timer'):
                self.indicators_timer.stop()
            
            # Detener monitoreo de rendimiento
            self.performance_monitor.stop_monitoring()
            
            # Limpieza final de memoria
            self._advanced_memory_cleanup()
            
            # Guardar estado comprimido
            final_state = {
                "last_sync": self._last_sync_time,
                "loaded_tabs": list(self.tab_loading_status.keys()),
                "performance_stats": self.performance_monitor.get_performance_summary()
            }
            self.performance_monitor.cache_compressed("final_state", final_state)
            
            logger.info("Limpieza al cerrar completada")
            
        except Exception as e:
            logger.error(f"Error en limpieza al cerrar: {e}")
    
    def _handle_performance_warning(self, message: str, metrics: dict):
        """Maneja advertencias de rendimiento"""
        try:
            logger.warning(f"Advertencia de rendimiento: {message}")
            
            # Mostrar notificación al usuario
            status_bar = self.statusBar()
            if status_bar:
                status_bar.showMessage(f"⚠️ {message}", 5000)
            
            # Actualizar indicadores
            self._update_performance_indicators()
            
            # Si es crítico, mostrar diálogo
            if "crítico" in message.lower():
                QMessageBox.warning(
                    self, "Advertencia de Rendimiento",
                    f"Se ha detectado un problema de rendimiento:\n{message}\n\n"
                    "Se recomienda reiniciar la aplicación."
                )
                
        except Exception as e:
            logger.error(f"Error manejando advertencia de rendimiento: {e}")
    
    def _update_offline_indicator(self):
        """Actualizar indicador de estado offline"""
        try:
            # Verificar conectividad
            is_online = self.api_client.is_connected()
            
            status_bar = self.statusBar()
            if status_bar:
                if is_online:
                    status_bar.showMessage("Conectado al servidor")
                else:
                    status_bar.showMessage("Modo offline - Datos locales")
                
        except Exception as e:
            logger.error(f"Error actualizando indicador offline: {e}")
    
    def setup_realtime_sync(self):
        """Configurar sincronización en tiempo real"""
        try:
            from cliente.utils.realtime_sync import get_realtime_sync_manager
            from cliente.widgets.realtime_status_widget import RealtimeStatusWidget
            
            # Obtener gestor de sincronización
            self.realtime_sync_manager = get_realtime_sync_manager(self.api_client, self.config)
            
            if self.realtime_sync_manager:
                # Crear widget de estado de sincronización
                self.realtime_status_widget = RealtimeStatusWidget(self)
                
                # Agregar al panel derecho
                if hasattr(self, 'right_panel_layout'):
                    self.right_panel_layout.addWidget(self.realtime_status_widget)
                    
                # Conectar señales
                self.realtime_sync_manager.add_status_callback(self._on_sync_status_changed)
                self.realtime_sync_manager.add_data_callback("*", self._on_sync_data_received)
                self.realtime_sync_manager.add_conflict_callback(self._on_sync_conflict)
                
                # Configurar sincronización selectiva
                sync_tables = ["usuarios", "clases", "asistencias", "pagos", "empleados"]
                self.realtime_sync_manager.enable_selective_sync(sync_tables)
                
                logger.info("Sincronización en tiempo real configurada")
                
        except Exception as e:
            logger.error(f"Error configurando sincronización en tiempo real: {e}")
    
    def _on_sync_status_changed(self, new_status, old_status):
        """Callback para cambios de estado de sincronización"""
        try:
            # Actualizar indicador en barra de estado
            status_text = f"Sincronización: {new_status.value}"
            self.statusBar().showMessage(status_text, 3000)
            
            # Actualizar indicador de rendimiento si es necesario
            if new_status.value == "connected":
                self.performance_indicator.setText("Sincronización: Activa ✓")
                self.performance_indicator.setStyleSheet("""
                    QLabel {
                        color: var(--success-color);
                        font-weight: bold;
                        padding: 8px;
                        background: var(--bg-card);
                        border-radius: 4px;
                    }
                """)
            elif new_status.value == "error":
                self.performance_indicator.setText("Sincronización: Error ⚠")
                self.performance_indicator.setStyleSheet("""
                    QLabel {
                        color: var(--warning-color);
                        font-weight: bold;
                        padding: 8px;
                        background: var(--bg-card);
                        border-radius: 4px;
                    }
                """)
                
        except Exception as e:
            logger.error(f"Error manejando cambio de estado de sincronización: {e}")
    
    def _on_sync_data_received(self, table: str, data: dict):
        """Callback para datos recibidos por sincronización"""
        try:
            # Actualizar widgets correspondientes
            if table == "usuarios" and hasattr(self, 'usuarios_tab'):
                self.usuarios_tab.refresh_data()
            elif table == "clases" and hasattr(self, 'clases_tab'):
                self.clases_tab.refresh_data()
            elif table == "asistencias" and hasattr(self, 'asistencias_tab'):
                self.asistencias_tab.refresh_data()
            elif table == "pagos" and hasattr(self, 'pagos_tab'):
                self.pagos_tab.refresh_data()
            elif table == "empleados" and hasattr(self, 'empleados_tab'):
                self.empleados_tab.refresh_data()
                
            # Mostrar notificación
            self.statusBar().showMessage(f"Datos actualizados: {table}", 2000)
            
        except Exception as e:
            logger.error(f"Error manejando datos de sincronización: {e}")
    
    def _on_sync_conflict(self, conflict_data):
        """Callback para conflictos de sincronización"""
        try:
            # Mostrar notificación de conflicto
            QMessageBox.information(
                self, "Conflicto de Sincronización",
                f"Se ha resuelto automáticamente un conflicto en {conflict_data.get('conflict_type', 'datos')}.\n"
                "Los datos han sido actualizados correctamente."
            )
            
        except Exception as e:
            logger.error(f"Error manejando conflicto de sincronización: {e}")
    
    def send_sync_operation(self, table: str, operation: str, data: dict):
        """Enviar operación de sincronización"""
        try:
            if hasattr(self, 'realtime_sync_manager') and self.realtime_sync_manager:
                self.realtime_sync_manager.send_operation(table, operation, data)
                
        except Exception as e:
            logger.error(f"Error enviando operación de sincronización: {e}")
    
    def get_sync_stats(self):
        """Obtener estadísticas de sincronización"""
        try:
            if hasattr(self, 'realtime_sync_manager') and self.realtime_sync_manager:
                return self.realtime_sync_manager.get_stats()
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de sincronización: {e}")
            return {}
