"""
Sistema de accesibilidad para el Sistema de Gimnasio v6
Incluye controles de zoom, contraste, audio, navegación por teclado y anuncios para lectores de pantalla
"""
import logging
import json
import os
from typing import Dict, List, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QCheckBox, QComboBox, QFrame,
    QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QPalette, QColor

logger = logging.getLogger(__name__)

class AccessibilitySettings:
    """Configuración de accesibilidad"""
    
    def __init__(self):
        self.zoom_level = 100  # Porcentaje de zoom
        self.high_contrast = False
        self.large_text = False
        self.screen_reader = False
        self.keyboard_navigation = True
        self.audio_feedback = False
        self.reduced_motion = False
        self.focus_indicator = True
        self.color_blind_friendly = False
        self.font_size_base = 16
        self.line_spacing = 1.2
        self.letter_spacing = 0

class AccessibilityManager:
    """Gestor principal de accesibilidad"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.settings = AccessibilitySettings()
            self.main_window: Optional[QMainWindow] = None
            self.announcements: List[str] = []
            self.audio_enabled = False
            self.settings_file = "config/accessibility.json"
            self.load_settings()
            self.initialized = True
    
    def set_main_window(self, window: QMainWindow):
        """Establece la ventana principal"""
        self.main_window = window
        self.setup_global_shortcuts()
        self.apply_settings()
    
    def load_settings(self):
        """Carga la configuración desde archivo"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings.zoom_level = data.get('zoom_level', 100)
                    self.settings.high_contrast = data.get('high_contrast', False)
                    self.settings.large_text = data.get('large_text', False)
                    self.settings.screen_reader = data.get('screen_reader', False)
                    self.settings.keyboard_navigation = data.get('keyboard_navigation', True)
                    self.settings.audio_feedback = data.get('audio_feedback', False)
                    self.settings.reduced_motion = data.get('reduced_motion', False)
                    self.settings.focus_indicator = data.get('focus_indicator', True)
                    self.settings.color_blind_friendly = data.get('color_blind_friendly', False)
                    self.settings.font_size_base = data.get('font_size_base', 16)
                    self.settings.line_spacing = data.get('line_spacing', 1.2)
                    self.settings.letter_spacing = data.get('letter_spacing', 0)
        except Exception as e:
            logger.error(f"Error cargando configuración de accesibilidad: {e}")
    
    def save_settings(self):
        """Guarda la configuración en archivo"""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            data = {
                'zoom_level': self.settings.zoom_level,
                'high_contrast': self.settings.high_contrast,
                'large_text': self.settings.large_text,
                'screen_reader': self.settings.screen_reader,
                'keyboard_navigation': self.settings.keyboard_navigation,
                'audio_feedback': self.settings.audio_feedback,
                'reduced_motion': self.settings.reduced_motion,
                'focus_indicator': self.settings.focus_indicator,
                'color_blind_friendly': self.settings.color_blind_friendly,
                'font_size_base': self.settings.font_size_base,
                'line_spacing': self.settings.line_spacing,
                'letter_spacing': self.settings.letter_spacing
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando configuración de accesibilidad: {e}")
    
    def setup_global_shortcuts(self):
        """Configura atajos de teclado globales"""
        if not self.main_window:
            return
        
        # Ctrl + = para zoom in
        zoom_in_shortcut = QShortcut(QKeySequence("Ctrl+="), self.main_window)
        zoom_in_shortcut.activated.connect(self.zoom_in)
        
        # Ctrl + - para zoom out
        zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self.main_window)
        zoom_out_shortcut.activated.connect(self.zoom_out)
        
        # Ctrl + 0 para reset zoom
        zoom_reset_shortcut = QShortcut(QKeySequence("Ctrl+0"), self.main_window)
        zoom_reset_shortcut.activated.connect(self.zoom_reset)
        
        # Ctrl + Shift + C para toggle contraste
        contrast_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self.main_window)
        contrast_shortcut.activated.connect(self.toggle_high_contrast)
        
        # Ctrl + Shift + T para toggle texto grande
        text_shortcut = QShortcut(QKeySequence("Ctrl+Shift+T"), self.main_window)
        text_shortcut.activated.connect(self.toggle_large_text)
        
        # Ctrl + Shift + A para toggle audio
        audio_shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), self.main_window)
        audio_shortcut.activated.connect(self.toggle_audio_feedback)
        
        # Tab para navegación por teclado
        self.main_window.setTabOrder(self.main_window, self.main_window)
    
    def apply_settings(self):
        """Aplica la configuración actual"""
        if not self.main_window:
            return
        
        # Aplicar zoom
        self.apply_zoom()
        
        # Aplicar contraste alto
        self.apply_high_contrast()
        
        # Aplicar texto grande
        self.apply_large_text()
        
        # Aplicar indicadores de foco
        self.apply_focus_indicators()
        
        # Aplicar colores para daltónicos
        self.apply_color_blind_friendly()
        
        # Aplicar espaciado
        self.apply_spacing()
    
    def apply_zoom(self):
        """Aplica el nivel de zoom"""
        if not self.main_window:
            return
        
        # Calcular factor de zoom
        zoom_factor = self.settings.zoom_level / 100.0
        
        # Aplicar zoom a la fuente base
        font = self.main_window.font()
        font.setPointSize(int(self.settings.font_size_base * zoom_factor))
        self.main_window.setFont(font)
        
        # Aplicar zoom a todos los widgets hijos
        self.apply_zoom_to_widget(self.main_window, zoom_factor)
    
    def apply_zoom_to_widget(self, widget: QWidget, zoom_factor: float):
        """Aplica zoom a un widget y sus hijos"""
        # Aplicar zoom a la fuente del widget
        font = widget.font()
        if font.pointSize() > 0:
            font.setPointSize(int(font.pointSize() * zoom_factor))
            widget.setFont(font)
        
        # Aplicar zoom a los hijos
        for child in widget.findChildren(QWidget):
            self.apply_zoom_to_widget(child, zoom_factor)
    
    def apply_high_contrast(self):
        """Aplica modo de alto contraste"""
        if not self.main_window:
            return
        
        if self.settings.high_contrast:
            # Configurar paleta de alto contraste
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Link, QColor(255, 255, 0))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 255, 0))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
            
            self.main_window.setPalette(palette)
        else:
            # Restaurar paleta normal
            self.main_window.setPalette(self.main_window.style().standardPalette())
    
    def apply_large_text(self):
        """Aplica texto grande"""
        if not self.main_window:
            return
        
        base_size = self.settings.font_size_base
        if self.settings.large_text:
            base_size = int(base_size * 1.25)
        
        font = self.main_window.font()
        font.setPointSize(base_size)
        self.main_window.setFont(font)
    
    def apply_focus_indicators(self):
        """Aplica indicadores de foco mejorados"""
        if not self.main_window:
            return
        
        if self.settings.focus_indicator:
            # Configurar indicadores de foco visibles
            focus_style = """
                QWidget:focus {
                    outline: 3px solid #3b82f6;
                    outline-offset: 2px;
                }
                QPushButton:focus {
                    border: 3px solid #3b82f6;
                    border-radius: 8px;
                }
                QLineEdit:focus {
                    border: 3px solid #3b82f6;
                    border-radius: 8px;
                }
            """
            self.main_window.setStyleSheet(self.main_window.styleSheet() + focus_style)
    
    def apply_color_blind_friendly(self):
        """Aplica colores amigables para daltónicos"""
        if not self.main_window:
            return
        
        if self.settings.color_blind_friendly:
            # Usar colores que distinguen mejor los daltónicos
            color_style = """
                QPushButton.success {
                    background-color: #059669;
                    color: white;
                }
                QPushButton.warning {
                    background-color: #d97706;
                    color: white;
                }
                QPushButton.error {
                    background-color: #dc2626;
                    color: white;
                }
                QLabel.badge.success {
                    background-color: #059669;
                    color: white;
                }
                QLabel.badge.warning {
                    background-color: #d97706;
                    color: white;
                }
                QLabel.badge.error {
                    background-color: #dc2626;
                    color: white;
                }
            """
            self.main_window.setStyleSheet(self.main_window.styleSheet() + color_style)
    
    def apply_spacing(self):
        """Aplica espaciado mejorado"""
        if not self.main_window:
            return
        
        spacing_style = f"""
            QWidget {{
                line-height: {self.settings.line_spacing};
                letter-spacing: {self.settings.letter_spacing}px;
            }}
        """
        self.main_window.setStyleSheet(self.main_window.styleSheet() + spacing_style)
    
    def zoom_in(self):
        """Aumenta el zoom"""
        self.settings.zoom_level = min(200, self.settings.zoom_level + 10)
        self.apply_zoom()
        self.save_settings()
        self.announce("Zoom aumentado")
    
    def zoom_out(self):
        """Reduce el zoom"""
        self.settings.zoom_level = max(50, self.settings.zoom_level - 10)
        self.apply_zoom()
        self.save_settings()
        self.announce("Zoom reducido")
    
    def zoom_reset(self):
        """Resetea el zoom"""
        self.settings.zoom_level = 100
        self.apply_zoom()
        self.save_settings()
        self.announce("Zoom restablecido")
    
    def toggle_high_contrast(self):
        """Alterna el modo de alto contraste"""
        self.settings.high_contrast = not self.settings.high_contrast
        self.apply_high_contrast()
        self.save_settings()
        status = "activado" if self.settings.high_contrast else "desactivado"
        self.announce(f"Alto contraste {status}")
    
    def toggle_large_text(self):
        """Alterna el texto grande"""
        self.settings.large_text = not self.settings.large_text
        self.apply_large_text()
        self.save_settings()
        status = "activado" if self.settings.large_text else "desactivado"
        self.announce(f"Texto grande {status}")
    
    def toggle_audio_feedback(self):
        """Alterna el feedback de audio"""
        self.settings.audio_feedback = not self.settings.audio_feedback
        self.save_settings()
        status = "activado" if self.settings.audio_feedback else "desactivado"
        self.announce(f"Feedback de audio {status}")
    
    def announce(self, message: str):
        """Anuncia un mensaje para lectores de pantalla"""
        if self.settings.screen_reader:
            # Agregar a la lista de anuncios
            self.announcements.append(message)
            
            # Emitir señal para el lector de pantalla
            if self.main_window:
                self.main_window.setAccessibleDescription(message)
        
        # Reproducir audio si está habilitado
        if self.settings.audio_feedback:
            self.play_audio_feedback(message)
    
    def play_audio_feedback(self, message: str):
        """Reproduce feedback de audio"""
        # TODO: Implementar síntesis de voz o sonidos
        logger.info(f"Audio feedback: {message}")
    
    def get_announcements(self) -> List[str]:
        """Obtiene la lista de anuncios pendientes"""
        announcements = self.announcements.copy()
        self.announcements.clear()
        return announcements

# Instancia global del gestor
accessibility_manager = AccessibilityManager()

class AccessibilityDialog(QDialog):
    """Diálogo de configuración de accesibilidad"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.accessibility_manager = accessibility_manager
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Configura la interfaz del diálogo"""
        self.setWindowTitle("Configuración de Accesibilidad")
        self.setFixedSize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Configuración de Accesibilidad")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: var(--text-primary);
                padding: 16px 0;
            }
        """)
        layout.addWidget(title)
        
        # Controles de zoom
        zoom_group = QGroupBox("Zoom y Tamaño de Texto")
        zoom_layout = QFormLayout(zoom_group)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setTickInterval(25)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        
        self.zoom_label = QLabel("100%")
        zoom_layout.addRow("Nivel de zoom:", self.zoom_slider)
        zoom_layout.addRow("", self.zoom_label)
        
        # Botones de zoom
        zoom_buttons_layout = QHBoxLayout()
        zoom_in_btn = QPushButton("Zoom +")
        zoom_in_btn.clicked.connect(self.accessibility_manager.zoom_in)
        zoom_out_btn = QPushButton("Zoom -")
        zoom_out_btn.clicked.connect(self.accessibility_manager.zoom_out)
        zoom_reset_btn = QPushButton("Reset")
        zoom_reset_btn.clicked.connect(self.accessibility_manager.zoom_reset)
        
        zoom_buttons_layout.addWidget(zoom_in_btn)
        zoom_buttons_layout.addWidget(zoom_out_btn)
        zoom_buttons_layout.addWidget(zoom_reset_btn)
        zoom_buttons_layout.addStretch()
        
        zoom_layout.addRow("", zoom_buttons_layout)
        layout.addWidget(zoom_group)
        
        # Controles de visualización
        display_group = QGroupBox("Visualización")
        display_layout = QFormLayout(display_group)
        
        self.high_contrast_cb = QCheckBox("Alto contraste")
        self.high_contrast_cb.toggled.connect(self.on_high_contrast_toggled)
        display_layout.addRow("", self.high_contrast_cb)
        
        self.large_text_cb = QCheckBox("Texto grande")
        self.large_text_cb.toggled.connect(self.on_large_text_toggled)
        display_layout.addRow("", self.large_text_cb)
        
        self.color_blind_cb = QCheckBox("Colores para daltónicos")
        self.color_blind_cb.toggled.connect(self.on_color_blind_toggled)
        display_layout.addRow("", self.color_blind_cb)
        
        self.focus_indicator_cb = QCheckBox("Indicadores de foco")
        self.focus_indicator_cb.toggled.connect(self.on_focus_indicator_toggled)
        display_layout.addRow("", self.focus_indicator_cb)
        
        layout.addWidget(display_group)
        
        # Controles de navegación
        navigation_group = QGroupBox("Navegación")
        navigation_layout = QFormLayout(navigation_group)
        
        self.keyboard_nav_cb = QCheckBox("Navegación por teclado")
        self.keyboard_nav_cb.toggled.connect(self.on_keyboard_nav_toggled)
        navigation_layout.addRow("", self.keyboard_nav_cb)
        
        self.screen_reader_cb = QCheckBox("Lector de pantalla")
        self.screen_reader_cb.toggled.connect(self.on_screen_reader_toggled)
        navigation_layout.addRow("", self.screen_reader_cb)
        
        self.audio_feedback_cb = QCheckBox("Feedback de audio")
        self.audio_feedback_cb.toggled.connect(self.on_audio_feedback_toggled)
        navigation_layout.addRow("", self.audio_feedback_cb)
        
        layout.addWidget(navigation_group)
        
        # Controles de movimiento
        motion_group = QGroupBox("Movimiento")
        motion_layout = QFormLayout(motion_group)
        
        self.reduced_motion_cb = QCheckBox("Reducir movimiento")
        self.reduced_motion_cb.toggled.connect(self.on_reduced_motion_toggled)
        motion_layout.addRow("", self.reduced_motion_cb)
        
        layout.addWidget(motion_group)
        
        # Controles de espaciado
        spacing_group = QGroupBox("Espaciado")
        spacing_layout = QFormLayout(spacing_group)
        
        self.line_spacing_spin = QSpinBox()
        self.line_spacing_spin.setRange(10, 30)
        self.line_spacing_spin.setValue(12)
        self.line_spacing_spin.setSuffix(" (x0.1)")
        self.line_spacing_spin.valueChanged.connect(self.on_line_spacing_changed)
        spacing_layout.addRow("Espaciado de línea:", self.line_spacing_spin)
        
        self.letter_spacing_spin = QSpinBox()
        self.letter_spacing_spin.setRange(0, 10)
        self.letter_spacing_spin.setValue(0)
        self.letter_spacing_spin.setSuffix(" px")
        self.letter_spacing_spin.valueChanged.connect(self.on_letter_spacing_changed)
        spacing_layout.addRow("Espaciado de letras:", self.letter_spacing_spin)
        
        layout.addWidget(spacing_group)
        
        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Reset
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self.reset_settings)
        layout.addWidget(buttons)
    
    def load_current_settings(self):
        """Carga la configuración actual"""
        settings = self.accessibility_manager.settings
        
        self.zoom_slider.setValue(settings.zoom_level)
        self.zoom_label.setText(f"{settings.zoom_level}%")
        
        self.high_contrast_cb.setChecked(settings.high_contrast)
        self.large_text_cb.setChecked(settings.large_text)
        self.color_blind_cb.setChecked(settings.color_blind_friendly)
        self.focus_indicator_cb.setChecked(settings.focus_indicator)
        
        self.keyboard_nav_cb.setChecked(settings.keyboard_navigation)
        self.screen_reader_cb.setChecked(settings.screen_reader)
        self.audio_feedback_cb.setChecked(settings.audio_feedback)
        
        self.reduced_motion_cb.setChecked(settings.reduced_motion)
        
        self.line_spacing_spin.setValue(int(settings.line_spacing * 10))
        self.letter_spacing_spin.setValue(settings.letter_spacing)
    
    def on_zoom_changed(self, value):
        """Maneja cambios en el zoom"""
        self.zoom_label.setText(f"{value}%")
        self.accessibility_manager.settings.zoom_level = value
        self.accessibility_manager.apply_zoom()
    
    def on_high_contrast_toggled(self, checked):
        """Maneja cambios en alto contraste"""
        self.accessibility_manager.settings.high_contrast = checked
        self.accessibility_manager.apply_high_contrast()
    
    def on_large_text_toggled(self, checked):
        """Maneja cambios en texto grande"""
        self.accessibility_manager.settings.large_text = checked
        self.accessibility_manager.apply_large_text()
    
    def on_color_blind_toggled(self, checked):
        """Maneja cambios en colores para daltónicos"""
        self.accessibility_manager.settings.color_blind_friendly = checked
        self.accessibility_manager.apply_color_blind_friendly()
    
    def on_focus_indicator_toggled(self, checked):
        """Maneja cambios en indicadores de foco"""
        self.accessibility_manager.settings.focus_indicator = checked
        self.accessibility_manager.apply_focus_indicators()
    
    def on_keyboard_nav_toggled(self, checked):
        """Maneja cambios en navegación por teclado"""
        self.accessibility_manager.settings.keyboard_navigation = checked
    
    def on_screen_reader_toggled(self, checked):
        """Maneja cambios en lector de pantalla"""
        self.accessibility_manager.settings.screen_reader = checked
    
    def on_audio_feedback_toggled(self, checked):
        """Maneja cambios en feedback de audio"""
        self.accessibility_manager.settings.audio_feedback = checked
    
    def on_reduced_motion_toggled(self, checked):
        """Maneja cambios en movimiento reducido"""
        self.accessibility_manager.settings.reduced_motion = checked
    
    def on_line_spacing_changed(self, value):
        """Maneja cambios en espaciado de línea"""
        self.accessibility_manager.settings.line_spacing = value / 10.0
        self.accessibility_manager.apply_spacing()
    
    def on_letter_spacing_changed(self, value):
        """Maneja cambios en espaciado de letras"""
        self.accessibility_manager.settings.letter_spacing = value
        self.accessibility_manager.apply_spacing()
    
    def reset_settings(self):
        """Resetea la configuración a valores por defecto"""
        self.accessibility_manager.settings = AccessibilitySettings()
        self.load_current_settings()
        self.accessibility_manager.apply_settings()
    
    def accept(self):
        """Guarda la configuración y cierra el diálogo"""
        self.accessibility_manager.save_settings()
        super().accept()

class KeyboardNavigator:
    """Navegador por teclado para widgets"""
    
    def __init__(self, parent_widget: QWidget):
        self.parent_widget = parent_widget
        self.focusable_widgets: List[QWidget] = []
        self.current_index = 0
        self.setup_navigation()
    
    def setup_navigation(self):
        """Configura la navegación por teclado"""
        # Encontrar widgets enfocables
        self.find_focusable_widgets(self.parent_widget)
        
        # Configurar atajos
        if self.parent_widget:
            # Tab para siguiente
            tab_shortcut = QShortcut(QKeySequence("Tab"), self.parent_widget)
            tab_shortcut.activated.connect(self.next_widget)
            
            # Shift+Tab para anterior
            shift_tab_shortcut = QShortcut(QKeySequence("Shift+Tab"), self.parent_widget)
            shift_tab_shortcut.activated.connect(self.previous_widget)
            
            # Flechas para navegación
            up_shortcut = QShortcut(QKeySequence("Up"), self.parent_widget)
            up_shortcut.activated.connect(self.previous_widget)
            
            down_shortcut = QShortcut(QKeySequence("Down"), self.parent_widget)
            down_shortcut.activated.connect(self.next_widget)
    
    def find_focusable_widgets(self, widget: QWidget):
        """Encuentra widgets enfocables"""
        if widget.isEnabled() and widget.isVisible():
            if widget.focusPolicy() != Qt.FocusPolicy.NoFocus:
                self.focusable_widgets.append(widget)
        
        for child in widget.findChildren(QWidget):
            self.find_focusable_widgets(child)
    
    def next_widget(self):
        """Navega al siguiente widget"""
        if not self.focusable_widgets:
            return
        
        self.current_index = (self.current_index + 1) % len(self.focusable_widgets)
        self.focusable_widgets[self.current_index].setFocus()
    
    def previous_widget(self):
        """Navega al widget anterior"""
        if not self.focusable_widgets:
            return
        
        self.current_index = (self.current_index - 1) % len(self.focusable_widgets)
        self.focusable_widgets[self.current_index].setFocus()
    
    def focus_widget(self, widget: QWidget):
        """Enfoca un widget específico"""
        if widget in self.focusable_widgets:
            self.current_index = self.focusable_widgets.index(widget)
            widget.setFocus() 