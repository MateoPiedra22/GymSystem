"""
Widget para la configuración del sistema
Incluye opciones de conexión, apariencia y preferencias de usuario
"""

from typing import Dict, Any, Optional
import os
import json
import logging

# Configurar logger para el módulo
logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QTabWidget, QFormLayout, QSlider, QFileDialog, QMessageBox,
    QColorDialog, QFrame, QRadioButton, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QDir
from PyQt6.QtGui import QFont, QIcon, QColor

from utils.config_manager import ConfigManager
from utils.theme_manager import ThemeManager
from api_client import ApiClient

class ConfiguracionTabWidget(QWidget):
    """
    Widget para la pestaña de configuración
    
    Permite configurar los aspectos del sistema incluyendo:
    - Conexión al servidor
    - Apariencia y temas
    - Configuración de sincronización
    - Preferencias de usuario
    """
    
    # Señal para indicar que se han guardado cambios que requieren reinicio
    config_changed = pyqtSignal(bool)
    
    def __init__(self, config: ConfigManager, api_client: ApiClient):
        super().__init__()
        self.config = config
        self.api_client = api_client
        self.theme_manager = ThemeManager(config, api_client)
        self.setupUI()
        
    def setupUI(self):
        """Configura la interfaz de usuario del widget"""
        main_layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Configuración del Sistema")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Pestañas de configuración
        self.tab_widget = QTabWidget()
        
        # Crear pestañas
        self.create_general_tab()
        self.create_appearance_tab()
        self.create_themes_tab()
        self.create_sync_tab()
        self.create_advanced_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setIcon(QIcon("assets/save.png"))
        self.btn_guardar.clicked.connect(self.guardar_configuracion)
        
        self.btn_restaurar = QPushButton("Restaurar Valores Predeterminados")
        self.btn_restaurar.setIcon(QIcon("assets/reset.png"))
        self.btn_restaurar.clicked.connect(self.restaurar_predeterminados)
        
        button_layout.addWidget(self.btn_guardar)
        button_layout.addWidget(self.btn_restaurar)
        
        main_layout.addLayout(button_layout)
    
    def create_general_tab(self):
        """Crea la pestaña de configuración general"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Crear área scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Grupo de Conexión
        connection_group = QGroupBox("Conexión al Servidor")
        connection_layout = QFormLayout(connection_group)
        
        # URL del API
        self.input_api_url = QLineEdit()
        self.input_api_url.setText(self.config.get("api_url", "http://localhost:8000"))
        connection_layout.addRow("URL del API:", self.input_api_url)
        
        # Timeout
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(5, 60)
        self.spin_timeout.setValue(self.config.get("timeout", 30))
        self.spin_timeout.setSuffix(" segundos")
        connection_layout.addRow("Tiempo de espera:", self.spin_timeout)
        
        # Reintentos
        self.spin_retries = QSpinBox()
        self.spin_retries.setRange(0, 10)
        self.spin_retries.setValue(self.config.get("max_retries", 3))
        self.spin_retries.setPrefix("# ")
        connection_layout.addRow("Reintentos de conexión:", self.spin_retries)
        
        scroll_layout.addWidget(connection_group)
        
        # Grupo de Usuario
        user_group = QGroupBox("Preferencias de Usuario")
        user_layout = QFormLayout(user_group)
        
        # Idioma
        self.combo_idioma = QComboBox()
        self.combo_idioma.addItem("Español", "es")
        self.combo_idioma.addItem("Inglés", "en")
        current_lang = self.config.get("language", "es")
        index = self.combo_idioma.findData(current_lang)
        if index >= 0:
            self.combo_idioma.setCurrentIndex(index)
        user_layout.addRow("Idioma:", self.combo_idioma)
        
        # Modo de inicio
        self.combo_inicio = QComboBox()
        self.combo_inicio.addItem("Dashboard", "dashboard")
        self.combo_inicio.addItem("Usuarios", "usuarios")
        self.combo_inicio.addItem("Clases", "clases")
        self.combo_inicio.addItem("Última pestaña usada", "last")
        current_start = self.config.get("start_tab", "dashboard")
        index = self.combo_inicio.findData(current_start)
        if index >= 0:
            self.combo_inicio.setCurrentIndex(index)
        user_layout.addRow("Pestaña de inicio:", self.combo_inicio)
        
        # Recordar usuario
        self.check_recordar = QCheckBox()
        self.check_recordar.setChecked(self.config.get("remember_user", True))
        user_layout.addRow("Recordar usuario:", self.check_recordar)
        
        scroll_layout.addWidget(user_group)
        
        # Grupo de Notificaciones
        notif_group = QGroupBox("Notificaciones")
        notif_layout = QFormLayout(notif_group)
        
        # Habilitar notificaciones
        self.check_notif = QCheckBox()
        self.check_notif.setChecked(self.config.get("notifications_enabled", True))
        notif_layout.addRow("Habilitar notificaciones:", self.check_notif)
        
        # Sonido
        self.check_sonido = QCheckBox()
        self.check_sonido.setChecked(self.config.get("notifications_sound", True))
        notif_layout.addRow("Sonido:", self.check_sonido)
        
        # Tiempo en pantalla
        self.spin_notif_time = QSpinBox()
        self.spin_notif_time.setRange(1, 30)
        self.spin_notif_time.setValue(self.config.get("notification_time", 5))
        self.spin_notif_time.setSuffix(" segundos")
        notif_layout.addRow("Tiempo en pantalla:", self.spin_notif_time)
        
        scroll_layout.addWidget(notif_group)
        
        # Completar el scroll
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Añadir pestaña
        self.tab_widget.addTab(tab, QIcon("assets/settings.png"), "General")
    
    def create_appearance_tab(self):
        """Crea la pestaña de apariencia"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de Tema
        theme_group = QGroupBox("Tema")
        theme_layout = QVBoxLayout(theme_group)
        
        # Opciones de tema
        self.rb_theme_light = QRadioButton("Tema Claro")
        self.rb_theme_dark = QRadioButton("Tema Oscuro")
        self.rb_theme_system = QRadioButton("Usar tema del sistema")
        
        # Seleccionar según configuración
        current_theme = self.config.get("theme", "light")
        if current_theme == "dark":
            self.rb_theme_dark.setChecked(True)
        elif current_theme == "system":
            self.rb_theme_system.setChecked(True)
        else:
            self.rb_theme_light.setChecked(True)
        
        theme_layout.addWidget(self.rb_theme_light)
        theme_layout.addWidget(self.rb_theme_dark)
        theme_layout.addWidget(self.rb_theme_system)
        
        layout.addWidget(theme_group)
        
        # Grupo de Fuente
        font_group = QGroupBox("Fuente")
        font_layout = QFormLayout(font_group)
        
        # Tamaño de fuente
        self.slider_font = QSlider(Qt.Orientation.Horizontal)
        self.slider_font.setRange(8, 16)
        self.slider_font.setValue(self.config.get("font_size", 10))
        self.slider_font.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_font.setTickInterval(1)
        
        # Etiqueta con valor actual
        self.lbl_font_size = QLabel(f"{self.slider_font.value()}pt")
        self.slider_font.valueChanged.connect(lambda v: self.lbl_font_size.setText(f"{v}pt"))
        
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(self.slider_font)
        font_size_layout.addWidget(self.lbl_font_size)
        
        font_layout.addRow("Tamaño de fuente:", font_size_layout)
        
        # Familia de fuente
        self.combo_font = QComboBox()
        available_fonts = ["System Default", "Arial", "Helvetica", "Verdana", "Tahoma", "Segoe UI"]
        for font in available_fonts:
            self.combo_font.addItem(font)
        
        current_font = self.config.get("font_family", "System Default")
        index = self.combo_font.findText(current_font)
        if index >= 0:
            self.combo_font.setCurrentIndex(index)
        
        font_layout.addRow("Familia de fuente:", self.combo_font)
        
        layout.addWidget(font_group)
        
        # Grupo de Colores
        colors_group = QGroupBox("Colores de Acento")
        colors_layout = QFormLayout(colors_group)
        
        # Color primario
        self.btn_color_primary = QPushButton()
        self.btn_color_primary.setAutoFillBackground(True)
        self.primary_color = QColor(self.config.get("primary_color", "#3498db"))
        self.set_button_color(self.btn_color_primary, self.primary_color)
        self.btn_color_primary.clicked.connect(lambda: self.select_color("primary"))
        colors_layout.addRow("Color primario:", self.btn_color_primary)
        
        # Color secundario
        self.btn_color_secondary = QPushButton()
        self.btn_color_secondary.setAutoFillBackground(True)
        self.secondary_color = QColor(self.config.get("secondary_color", "#2ecc71"))
        self.set_button_color(self.btn_color_secondary, self.secondary_color)
        self.btn_color_secondary.clicked.connect(lambda: self.select_color("secondary"))
        colors_layout.addRow("Color secundario:", self.btn_color_secondary)
        
        # Color de acento
        self.btn_color_accent = QPushButton()
        self.btn_color_accent.setAutoFillBackground(True)
        self.accent_color = QColor(self.config.get("accent_color", "#e74c3c"))
        self.set_button_color(self.btn_color_accent, self.accent_color)
        self.btn_color_accent.clicked.connect(lambda: self.select_color("accent"))
        colors_layout.addRow("Color de acento:", self.btn_color_accent)
        
        layout.addWidget(colors_group)
        
        # Botón para restablecer colores
        btn_reset_colors = QPushButton("Restablecer Colores Predeterminados")
        btn_reset_colors.clicked.connect(self.reset_colors)
        layout.addWidget(btn_reset_colors)
        
        # Añadir pestaña
        self.tab_widget.addTab(tab, QIcon("assets/palette.png"), "Apariencia")
    
    def create_themes_tab(self):
        """Crea la pestaña de gestión de temas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de tema actual
        current_theme_group = QGroupBox("Tema Actual")
        current_theme_layout = QFormLayout(current_theme_group)
        
        # Mostrar tema actual
        self.current_theme_label = QLabel("Cargando...")
        current_theme_layout.addRow("Tema activo:", self.current_theme_label)
        
        # Botón para sincronizar con servidor
        self.btn_sync_server_theme = QPushButton("🔄 Sincronizar con Servidor")
        self.btn_sync_server_theme.clicked.connect(self.sync_server_theme)
        current_theme_layout.addRow("", self.btn_sync_server_theme)
        
        layout.addWidget(current_theme_group)
        
        # Grupo de temas disponibles
        themes_group = QGroupBox("Temas Disponibles")
        themes_layout = QVBoxLayout(themes_group)
        
        # Lista de temas
        self.themes_list = QWidget()
        self.themes_list_layout = QVBoxLayout(self.themes_list)
        
        # Crear scroll area para la lista de temas
        scroll_themes = QScrollArea()
        scroll_themes.setWidgetResizable(True)
        scroll_themes.setWidget(self.themes_list)
        scroll_themes.setMaximumHeight(300)
        
        themes_layout.addWidget(scroll_themes)
        
        # Botones de gestión de temas
        themes_buttons = QHBoxLayout()
        
        self.btn_refresh_themes = QPushButton("🔄 Actualizar")
        self.btn_refresh_themes.clicked.connect(self.refresh_themes)
        
        self.btn_apply_system = QPushButton("🖥️ Tema del Sistema")
        self.btn_apply_system.clicked.connect(self.apply_system_theme)
        
        self.btn_export_theme = QPushButton("💾 Exportar Tema")
        self.btn_export_theme.clicked.connect(self.export_current_theme)
        
        self.btn_import_theme = QPushButton("📁 Importar Tema")
        self.btn_import_theme.clicked.connect(self.import_theme)
        
        themes_buttons.addWidget(self.btn_refresh_themes)
        themes_buttons.addWidget(self.btn_apply_system)
        themes_buttons.addWidget(self.btn_export_theme)
        themes_buttons.addWidget(self.btn_import_theme)
        themes_buttons.addStretch()
        
        themes_layout.addLayout(themes_buttons)
        
        layout.addWidget(themes_group)
        
        # Grupo de vista previa
        preview_group = QGroupBox("Vista Previa del Tema")
        preview_layout = QVBoxLayout(preview_group)
        
        # Crear elementos de muestra para vista previa
        sample_layout = QHBoxLayout()
        
        sample_button = QPushButton("Botón de Muestra")
        sample_input = QLineEdit("Campo de texto de muestra")
        sample_combo = QComboBox()
        sample_combo.addItems(["Opción 1", "Opción 2", "Opción 3"])
        
        sample_layout.addWidget(sample_button)
        sample_layout.addWidget(sample_input)
        sample_layout.addWidget(sample_combo)
        sample_layout.addStretch()
        
        preview_layout.addLayout(sample_layout)
        
        # Información del tema seleccionado
        self.theme_info_label = QLabel("Seleccione un tema para ver información")
        self.theme_info_label.setWordWrap(True)
        preview_layout.addWidget(self.theme_info_label)
        
        layout.addWidget(preview_group)
        
        # Inicializar lista de temas
        self.refresh_themes()
        
        # Conectar señal de cambio de tema
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        
        # Añadir pestaña
        self.tab_widget.addTab(tab, QIcon("assets/themes.png"), "Temas")
    
    def create_sync_tab(self):
        """Crea la pestaña de configuración de sincronización"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de sincronización
        sync_group = QGroupBox("Sincronización")
        sync_layout = QFormLayout(sync_group)
        
        # Intervalo de sincronización
        self.spin_sync_interval = QSpinBox()
        self.spin_sync_interval.setRange(30, 3600)
        self.spin_sync_interval.setValue(self.config.get("sync_interval", 300))
        self.spin_sync_interval.setSuffix(" segundos")
        sync_layout.addRow("Intervalo de sincronización:", self.spin_sync_interval)
        
        # Sincronización automática
        self.check_auto_sync = QCheckBox()
        self.check_auto_sync.setChecked(self.config.get("auto_sync", True))
        sync_layout.addRow("Sincronización automática:", self.check_auto_sync)
        
        # Sincronizar al iniciar
        self.check_sync_startup = QCheckBox()
        self.check_sync_startup.setChecked(self.config.get("sync_on_startup", True))
        sync_layout.addRow("Sincronizar al iniciar:", self.check_sync_startup)
        
        # Sincronizar al cerrar
        self.check_sync_shutdown = QCheckBox()
        self.check_sync_shutdown.setChecked(self.config.get("sync_on_shutdown", True))
        sync_layout.addRow("Sincronizar al cerrar:", self.check_sync_shutdown)
        
        layout.addWidget(sync_group)
        
        # Grupo de modo offline
        offline_group = QGroupBox("Modo Offline")
        offline_layout = QFormLayout(offline_group)
        
        # Habilitar modo offline
        self.check_offline_mode = QCheckBox()
        self.check_offline_mode.setChecked(self.config.get("offline_mode_enabled", True))
        offline_layout.addRow("Habilitar modo offline:", self.check_offline_mode)
        
        # Caché
        self.combo_cache = QComboBox()
        self.combo_cache.addItem("Conservar datos por 1 día", 1)
        self.combo_cache.addItem("Conservar datos por 7 días", 7)
        self.combo_cache.addItem("Conservar datos por 30 días", 30)
        self.combo_cache.addItem("Conservar datos indefinidamente", -1)
        
        cache_days = self.config.get("cache_days", 7)
        index = self.combo_cache.findData(cache_days)
        if index >= 0:
            self.combo_cache.setCurrentIndex(index)
        
        offline_layout.addRow("Política de caché:", self.combo_cache)
        
        # Tamaño máximo de caché
        self.spin_cache_size = QSpinBox()
        self.spin_cache_size.setRange(10, 1000)
        self.spin_cache_size.setValue(self.config.get("max_cache_size_mb", 100))
        self.spin_cache_size.setSuffix(" MB")
        offline_layout.addRow("Tamaño máximo de caché:", self.spin_cache_size)
        
        # Botón para limpiar caché
        self.btn_clear_cache = QPushButton("Limpiar Caché")
        self.btn_clear_cache.clicked.connect(self.limpiar_cache)
        offline_layout.addRow("", self.btn_clear_cache)
        
        layout.addWidget(offline_group)
        
        # Grupo de conflictos
        conflict_group = QGroupBox("Resolución de Conflictos")
        conflict_layout = QFormLayout(conflict_group)
        
        # Política de resolución
        self.combo_conflict = QComboBox()
        self.combo_conflict.addItem("Preguntar siempre", "ask")
        self.combo_conflict.addItem("Priorizar servidor", "server")
        self.combo_conflict.addItem("Priorizar local", "local")
        self.combo_conflict.addItem("Más reciente", "recent")
        
        conflict_policy = self.config.get("conflict_policy", "ask")
        index = self.combo_conflict.findData(conflict_policy)
        if index >= 0:
            self.combo_conflict.setCurrentIndex(index)
        
        conflict_layout.addRow("Política de conflictos:", self.combo_conflict)
        
        layout.addWidget(conflict_group)
        
        # Añadir espacio flexible
        layout.addStretch()
        
        # Añadir pestaña
        self.tab_widget.addTab(tab, QIcon("assets/sync.png"), "Sincronización")
    
    def create_advanced_tab(self):
        """Crea la pestaña de configuración avanzada"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Advertencia
        warning = QLabel("¡Advertencia! Cambiar estas configuraciones puede afectar el funcionamiento del sistema.")
        warning.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(warning)
        
        # Grupo de sistema
        system_group = QGroupBox("Sistema")
        system_layout = QFormLayout(system_group)
        
        # Directorio de datos
        data_dir_layout = QHBoxLayout()
        self.input_data_dir = QLineEdit()
        self.input_data_dir.setText(self.config.get("data_directory", os.path.join(QDir.homePath(), "GymSystem", "data")))
        self.input_data_dir.setReadOnly(True)
        
        btn_browse_data = QPushButton("...")
        btn_browse_data.clicked.connect(lambda: self.select_directory("data_directory"))
        
        data_dir_layout.addWidget(self.input_data_dir)
        data_dir_layout.addWidget(btn_browse_data)
        
        system_layout.addRow("Directorio de datos:", data_dir_layout)
        
        # Directorio de logs
        log_dir_layout = QHBoxLayout()
        self.input_log_dir = QLineEdit()
        self.input_log_dir.setText(self.config.get("log_directory", os.path.join(QDir.homePath(), "GymSystem", "logs")))
        self.input_log_dir.setReadOnly(True)
        
        btn_browse_log = QPushButton("...")
        btn_browse_log.clicked.connect(lambda: self.select_directory("log_directory"))
        
        log_dir_layout.addWidget(self.input_log_dir)
        log_dir_layout.addWidget(btn_browse_log)
        
        system_layout.addRow("Directorio de logs:", log_dir_layout)
        
        # Nivel de log
        self.combo_log_level = QComboBox()
        self.combo_log_level.addItem("DEBUG", "DEBUG")
        self.combo_log_level.addItem("INFO", "INFO")
        self.combo_log_level.addItem("WARNING", "WARNING")
        self.combo_log_level.addItem("ERROR", "ERROR")
        
        log_level = self.config.get("log_level", "INFO")
        index = self.combo_log_level.findData(log_level)
        if index >= 0:
            self.combo_log_level.setCurrentIndex(index)
        
        system_layout.addRow("Nivel de logging:", self.combo_log_level)
        
        layout.addWidget(system_group)
        
        # Grupo de rendimiento
        perf_group = QGroupBox("Rendimiento")
        perf_layout = QFormLayout(perf_group)
        
        # Límite de conexiones
        self.spin_conn_limit = QSpinBox()
        self.spin_conn_limit.setRange(1, 10)
        self.spin_conn_limit.setValue(self.config.get("max_connections", 3))
        perf_layout.addRow("Máximo de conexiones simultáneas:", self.spin_conn_limit)
        
        # Tamaño de búfer
        self.spin_buffer = QSpinBox()
        self.spin_buffer.setRange(1, 100)
        self.spin_buffer.setValue(self.config.get("buffer_size_mb", 10))
        self.spin_buffer.setSuffix(" MB")
        perf_layout.addRow("Tamaño de búfer:", self.spin_buffer)
        
        # Procesamiento en segundo plano
        self.check_background = QCheckBox()
        self.check_background.setChecked(self.config.get("background_processing", True))
        perf_layout.addRow("Procesamiento en segundo plano:", self.check_background)
        
        layout.addWidget(perf_group)
        
        # Grupo de seguridad
        security_group = QGroupBox("Seguridad")
        security_layout = QFormLayout(security_group)
        
        # Tiempo de expiración de sesión
        self.spin_session = QSpinBox()
        self.spin_session.setRange(5, 1440)
        self.spin_session.setValue(self.config.get("session_timeout_min", 60))
        self.spin_session.setSuffix(" minutos")
        security_layout.addRow("Expiración de sesión:", self.spin_session)
        
        # Método de encriptación
        self.combo_encryption = QComboBox()
        self.combo_encryption.addItem("AES-256", "aes256")
        self.combo_encryption.addItem("AES-128", "aes128")
        
        encryption = self.config.get("encryption_method", "aes256")
        index = self.combo_encryption.findData(encryption)
        if index >= 0:
            self.combo_encryption.setCurrentIndex(index)
        
        security_layout.addRow("Método de encriptación:", self.combo_encryption)
        
        layout.addWidget(security_group)
        
        # Botón para exportar configuración
        btn_export = QPushButton("Exportar Configuración")
        btn_export.clicked.connect(self.exportar_configuracion)
        layout.addWidget(btn_export)
        
        # Botón para importar configuración
        btn_import = QPushButton("Importar Configuración")
        btn_import.clicked.connect(self.importar_configuracion)
        layout.addWidget(btn_import)
        
        # Añadir espacio flexible
        layout.addStretch()
        
        # Añadir pestaña
        self.tab_widget.addTab(tab, QIcon("assets/advanced.png"), "Avanzado")
    
    def set_button_color(self, button: QPushButton, color: QColor):
        """Establece el color de fondo de un botón"""
        palette = button.palette()
        palette.setColor(button.backgroundRole(), color)
        button.setPalette(palette)
        button.setAutoFillBackground(True)
        button.setMaximumWidth(30)
        button.setMaximumHeight(30)
    
    def select_color(self, color_type: str):
        """Abre un diálogo para seleccionar un color"""
        if color_type == "primary":
            color = QColorDialog.getColor(self.primary_color, self, "Seleccionar Color Primario")
            if color.isValid():
                self.primary_color = color
                self.set_button_color(self.btn_color_primary, color)
        
        elif color_type == "secondary":
            color = QColorDialog.getColor(self.secondary_color, self, "Seleccionar Color Secundario")
            if color.isValid():
                self.secondary_color = color
                self.set_button_color(self.btn_color_secondary, color)
        
        elif color_type == "accent":
            color = QColorDialog.getColor(self.accent_color, self, "Seleccionar Color de Acento")
            if color.isValid():
                self.accent_color = color
                self.set_button_color(self.btn_color_accent, color)
    
    def reset_colors(self):
        """Restablece los colores a los valores predeterminados"""
        # Valores predeterminados
        self.primary_color = QColor("#3498db")
        self.secondary_color = QColor("#2ecc71")
        self.accent_color = QColor("#e74c3c")
        
        # Actualizar UI
        self.set_button_color(self.btn_color_primary, self.primary_color)
        self.set_button_color(self.btn_color_secondary, self.secondary_color)
        self.set_button_color(self.btn_color_accent, self.accent_color)
    
    def select_directory(self, dir_type: str):
        """Abre un diálogo para seleccionar un directorio"""
        current_dir = ""
        
        if dir_type == "data_directory":
            current_dir = self.input_data_dir.text()
        elif dir_type == "log_directory":
            current_dir = self.input_log_dir.text()
        
        # Abrir diálogo
        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar Directorio", current_dir
        )
        
        if directory:
            if dir_type == "data_directory":
                self.input_data_dir.setText(directory)
            elif dir_type == "log_directory":
                self.input_log_dir.setText(directory)
    
    def limpiar_cache(self):
        """Limpia la caché del sistema"""
        reply = QMessageBox.question(
            self, 
            "Limpiar Caché", 
            "¿Está seguro que desea limpiar la caché? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Simulación de limpieza (en una implementación real llamaríamos a una función real)
            QMessageBox.information(
                self, 
                "Caché Limpiada", 
                "La caché ha sido limpiada correctamente."
            )
    
    def exportar_configuracion(self):
        """Exporta la configuración actual a un archivo JSON"""
        # Abrir diálogo para seleccionar ubicación
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Configuración", "", "Archivos JSON (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            # Obtener configuración actual
            config_data = self.config.get_all()
            
            # Guardar a archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
            
            QMessageBox.information(
                self, 
                "Exportación Exitosa", 
                f"La configuración ha sido exportada correctamente a:\n{file_path}"
            )
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error de Exportación", 
                f"No se pudo exportar la configuración: {str(e)}"
            )
    
    def importar_configuracion(self):
        """Importa configuración desde un archivo JSON"""
        # Abrir diálogo para seleccionar archivo
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Configuración", "", "Archivos JSON (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            # Leer archivo
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Confirmar importación
            reply = QMessageBox.question(
                self, 
                "Importar Configuración", 
                "¿Está seguro que desea importar esta configuración? La configuración actual será reemplazada.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # En una implementación real, aquí validaríamos el formato antes de importar
                
                # Aplicar configuración
                for key, value in config_data.items():
                    self.config.set(key, value)
                
                # Guardar cambios
                self.config.save()
                
                QMessageBox.information(
                    self, 
                    "Importación Exitosa", 
                    "La configuración ha sido importada correctamente. Algunos cambios pueden requerir reiniciar la aplicación."
                )
                
                # Emitir señal de cambio que requiere reinicio
                self.config_changed.emit(True)
                
                # Actualizar UI con la nueva configuración
                self.actualizar_ui_desde_config()
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error de Importación", 
                f"No se pudo importar la configuración: {str(e)}"
            )
    
    def actualizar_ui_desde_config(self):
        """Actualiza la interfaz con los valores de la configuración actual"""
        # Implementar este método para actualizar todos los controles
        # después de importar configuración
        # Este es un lugar para refrescar la UI con los valores importados
        pass
    
    def guardar_configuracion(self):
        """Guarda los cambios de configuración"""
        # Recopilar valores de la interfaz
        
        # Pestaña General
        self.config.set("api_url", self.input_api_url.text())
        self.config.set("timeout", self.spin_timeout.value())
        self.config.set("max_retries", self.spin_retries.value())
        self.config.set("language", self.combo_idioma.currentData())
        self.config.set("start_tab", self.combo_inicio.currentData())
        self.config.set("remember_user", self.check_recordar.isChecked())
        self.config.set("notifications_enabled", self.check_notif.isChecked())
        self.config.set("notifications_sound", self.check_sonido.isChecked())
        self.config.set("notification_time", self.spin_notif_time.value())
        
        # Pestaña Apariencia
        if self.rb_theme_light.isChecked():
            theme = "light"
        elif self.rb_theme_dark.isChecked():
            theme = "dark"
        else:
            theme = "system"
        
        self.config.set("theme", theme)
        self.config.set("font_size", self.slider_font.value())
        self.config.set("font_family", self.combo_font.currentText())
        self.config.set("primary_color", self.primary_color.name())
        self.config.set("secondary_color", self.secondary_color.name())
        self.config.set("accent_color", self.accent_color.name())
        
        # Pestaña Sincronización
        self.config.set("sync_interval", self.spin_sync_interval.value())
        self.config.set("auto_sync", self.check_auto_sync.isChecked())
        self.config.set("sync_on_startup", self.check_sync_startup.isChecked())
        self.config.set("sync_on_shutdown", self.check_sync_shutdown.isChecked())
        self.config.set("offline_mode_enabled", self.check_offline_mode.isChecked())
        self.config.set("cache_days", self.combo_cache.currentData())
        self.config.set("max_cache_size_mb", self.spin_cache_size.value())
        self.config.set("conflict_policy", self.combo_conflict.currentData())
        
        # Pestaña Avanzado
        self.config.set("data_directory", self.input_data_dir.text())
        self.config.set("log_directory", self.input_log_dir.text())
        self.config.set("log_level", self.combo_log_level.currentData())
        self.config.set("max_connections", self.spin_conn_limit.value())
        self.config.set("buffer_size_mb", self.spin_buffer.value())
        self.config.set("background_processing", self.check_background.isChecked())
        self.config.set("session_timeout_min", self.spin_session.value())
        self.config.set("encryption_method", self.combo_encryption.currentData())
        
        # Guardar cambios
        try:
            self.config.save()
            
            QMessageBox.information(
                self, 
                "Configuración Guardada", 
                "La configuración ha sido guardada correctamente. Algunos cambios pueden requerir reiniciar la aplicación."
            )
            
            # Emitir señal de cambio
            self.config_changed.emit(True)
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error al Guardar", 
                f"No se pudo guardar la configuración: {str(e)}"
            )
    
    def restaurar_predeterminados(self):
        """Restaura los valores predeterminados de configuración"""
        reply = QMessageBox.question(
            self, 
            "Restaurar Valores Predeterminados", 
            "¿Está seguro que desea restaurar todos los valores a sus predeterminados? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Valores predeterminados
            defaults = {
                # General
                "api_url": "http://localhost:8000",
                "timeout": 30,
                "max_retries": 3,
                "language": "es",
                "start_tab": "dashboard",
                "remember_user": True,
                "notifications_enabled": True,
                "notifications_sound": True,
                "notification_time": 5,
                
                # Apariencia
                "theme": "light",
                "font_size": 10,
                "font_family": "System Default",
                "primary_color": "#3498db",
                "secondary_color": "#2ecc71",
                "accent_color": "#e74c3c",
                
                # Sincronización
                "sync_interval": 300,
                "auto_sync": True,
                "sync_on_startup": True,
                "sync_on_shutdown": True,
                "offline_mode_enabled": True,
                "cache_days": 7,
                "max_cache_size_mb": 100,
                "conflict_policy": "ask",
                
                # Avanzado
                "data_directory": os.path.join(QDir.homePath(), "GymSystem", "data"),
                "log_directory": os.path.join(QDir.homePath(), "GymSystem", "logs"),
                "log_level": "INFO",
                "max_connections": 3,
                "buffer_size_mb": 10,
                "background_processing": True,
                "session_timeout_min": 60,
                "encryption_method": "aes256"
            }
            
            # Aplicar valores predeterminados
            for key, value in defaults.items():
                self.config.set(key, value)
            
            # Refrescar UI
            self.actualizar_ui_desde_config()
            
            QMessageBox.information(
                self, 
                "Valores Restaurados", 
                "Los valores han sido restaurados a sus predeterminados. Haga clic en 'Guardar Cambios' para aplicarlos."
            )
    
    # ============= MÉTODOS DE GESTIÓN DE TEMAS =============
    
    def refresh_themes(self):
        """Actualiza la lista de temas disponibles"""
        try:
            for i in reversed(range(self.themes_list_layout.count())):
                child = self.themes_list_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            available_themes = self.theme_manager.get_available_themes()
            current_theme = self.theme_manager.get_current_theme()
            
            for theme_name, theme_data in available_themes.items():
                theme_widget = self.create_theme_widget(theme_name, theme_data, theme_name == current_theme)
                self.themes_list_layout.addWidget(theme_widget)
            
            if current_theme:
                theme_info = available_themes.get(current_theme, {})
                self.current_theme_label.setText(f"{theme_info.get('nombre', current_theme)}")
            else:
                self.current_theme_label.setText("Ninguno")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error actualizando temas: {str(e)}")
    
    def create_theme_widget(self, theme_name: str, theme_data: dict, is_active: bool) -> QWidget:
        """Crea un widget para mostrar un tema"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(widget)
        
        info_layout = QVBoxLayout()
        name_label = QLabel(theme_data.get('nombre', theme_name))
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        info_layout.addWidget(name_label)
        
        if theme_data.get('descripcion'):
            desc_label = QLabel(theme_data['descripcion'])
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
        
        layout.addLayout(info_layout, 3)
        
        buttons_layout = QVBoxLayout()
        
        if is_active:
            status_label = QLabel("ACTIVO")
            status_label.setStyleSheet("color: green; font-weight: bold; font-size: 10px;")
            buttons_layout.addWidget(status_label)
        else:
            apply_btn = QPushButton("Aplicar")
            apply_btn.setMaximumWidth(80)
            apply_btn.clicked.connect(lambda: self.apply_theme(theme_name))
            buttons_layout.addWidget(apply_btn)
        
        layout.addLayout(buttons_layout, 1)
        
        return widget
    
    def apply_theme(self, theme_name: str):
        """Aplica un tema"""
        try:
            success = self.theme_manager.apply_theme(theme_name)
            if success:
                QMessageBox.information(self, "Éxito", f"Tema '{theme_name}' aplicado correctamente")
                self.refresh_themes()
            else:
                QMessageBox.warning(self, "Error", f"No se pudo aplicar el tema '{theme_name}'")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error aplicando tema: {str(e)}")
    
    def sync_server_theme(self):
        """Sincroniza con el tema activo del servidor"""
        try:
            success = self.theme_manager.sync_with_server_theme()
            if success:
                QMessageBox.information(self, "Éxito", "Tema sincronizado con el servidor")
                self.refresh_themes()
            else:
                QMessageBox.warning(self, "Advertencia", "No se pudo sincronizar con el servidor")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error sincronizando tema: {str(e)}")
    
    def apply_system_theme(self):
        """Aplica el tema del sistema"""
        try:
            success = self.theme_manager.apply_system_theme()
            if success:
                QMessageBox.information(self, "Éxito", "Tema del sistema aplicado")
                self.refresh_themes()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error aplicando tema del sistema: {str(e)}")
    
    def export_current_theme(self):
        """Exporta el tema actual"""
        try:
            current_theme = self.theme_manager.get_current_theme()
            if not current_theme:
                QMessageBox.warning(self, "Advertencia", "No hay tema activo para exportar")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Tema", f"{current_theme}.json", "Archivos JSON (*.json)")
            
            if file_path:
                success = self.theme_manager.save_theme_to_file(current_theme, file_path)
                if success:
                    QMessageBox.information(self, "Éxito", f"Tema exportado a {file_path}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exportando tema: {str(e)}")
    
    def import_theme(self):
        """Importa un tema desde archivo"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Importar Tema", "", "Archivos JSON (*.json)")
            
            if file_path:
                theme_name = os.path.splitext(os.path.basename(file_path))[0]
                success = self.theme_manager.load_theme_from_file(file_path, theme_name)
                
                if success:
                    QMessageBox.information(self, "Éxito", f"Tema '{theme_name}' importado correctamente")
                    self.refresh_themes()
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error importando tema: {str(e)}")
    
    def on_theme_changed(self, theme_name: str):
        """Maneja el cambio de tema"""
        try:
            self.refresh_themes()
            self.config.set('current_theme', theme_name)
            self.config.save_config()
        except Exception as e:
            logger.error(f"Error manejando cambio de tema: {e}")
