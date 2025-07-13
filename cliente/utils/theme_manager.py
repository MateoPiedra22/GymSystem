"""
Gestor de temas para el cliente local PyQt
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor, QPalette, QFont

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

class ThemeManager(QObject):
    """
    Gestor de temas para la aplicación PyQt
    
    Permite cargar y aplicar temas desde el servidor o usar temas locales
    """
    
    theme_changed = pyqtSignal(str)  # Señal emitida cuando cambia el tema
    
    def __init__(self, config_manager: ConfigManager, api_client=None):
        super().__init__()
        self.config_manager = config_manager
        self.api_client = api_client
        self.current_theme = None
        self.available_themes = {}
        
        # Directorio de temas locales
        self.themes_dir = os.path.join(os.path.dirname(__file__), '..', 'themes')
        os.makedirs(self.themes_dir, exist_ok=True)
        
        # Cargar temas predefinidos y del servidor
        self.load_predefined_themes()
        if self.api_client:
            self.load_server_themes()
    
    def load_predefined_themes(self):
        """Carga los temas predefinidos locales"""
        predefined_themes = {
            "clasico": {
                "nombre": "Clásico",
                "descripcion": "Tema clásico con colores tradicionales",
                "colors": {
                    "primary": "#2563eb",
                    "primary_light": "#3b82f6",
                    "primary_dark": "#1d4ed8",
                    "secondary": "#64748b",
                    "secondary_light": "#94a3b8",
                    "secondary_dark": "#475569",
                    "accent": "#10b981",
                    "background": "#ffffff",
                    "surface": "#f8fafc",
                    "text": "#1e293b",
                    "text_secondary": "#64748b",
                    "border": "#e2e8f0",
                    "error": "#ef4444",
                    "warning": "#f59e0b",
                    "success": "#10b981"
                },
                "fonts": {
                    "family": "Inter, Arial, sans-serif",
                    "size": 10,
                    "weight_normal": "normal",
                    "weight_bold": "bold"
                },
                "dimensions": {
                    "border_radius": 6,
                    "padding": 8,
                    "margin": 4
                }
            },
            "moderno": {
                "nombre": "Moderno",
                "descripcion": "Tema moderno con colores vibrantes",
                "colors": {
                    "primary": "#7c3aed",
                    "primary_light": "#8b5cf6",
                    "primary_dark": "#6d28d9",
                    "secondary": "#06b6d4",
                    "secondary_light": "#22d3ee",
                    "secondary_dark": "#0891b2",
                    "accent": "#f59e0b",
                    "background": "#ffffff",
                    "surface": "#f8fafc",
                    "text": "#1e293b",
                    "text_secondary": "#475569",
                    "border": "#e2e8f0",
                    "error": "#ef4444",
                    "warning": "#f59e0b",
                    "success": "#10b981"
                },
                "fonts": {
                    "family": "Poppins, Arial, sans-serif",
                    "size": 11,
                    "weight_normal": "normal",
                    "weight_bold": "600"
                },
                "dimensions": {
                    "border_radius": 12,
                    "padding": 12,
                    "margin": 8
                }
            },
            "minimalista": {
                "nombre": "Minimalista",
                "descripcion": "Tema minimalista con colores neutros",
                "colors": {
                    "primary": "#000000",
                    "primary_light": "#374151",
                    "primary_dark": "#000000",
                    "secondary": "#6b7280",
                    "secondary_light": "#9ca3af",
                    "secondary_dark": "#4b5563",
                    "accent": "#374151",
                    "background": "#ffffff",
                    "surface": "#f9fafb",
                    "text": "#111827",
                    "text_secondary": "#6b7280",
                    "border": "#d1d5db",
                    "error": "#dc2626",
                    "warning": "#d97706",
                    "success": "#059669"
                },
                "fonts": {
                    "family": "system-ui, Arial, sans-serif",
                    "size": 10,
                    "weight_normal": "300",
                    "weight_bold": "500"
                },
                "dimensions": {
                    "border_radius": 2,
                    "padding": 6,
                    "margin": 2
                }
            },
            "oscuro": {
                "nombre": "Oscuro",
                "descripcion": "Tema oscuro para ambientes con poca luz",
                "colors": {
                    "primary": "#3b82f6",
                    "primary_light": "#60a5fa",
                    "primary_dark": "#2563eb",
                    "secondary": "#6b7280",
                    "secondary_light": "#9ca3af",
                    "secondary_dark": "#4b5563",
                    "accent": "#10b981",
                    "background": "#111827",
                    "surface": "#1f2937",
                    "text": "#f9fafb",
                    "text_secondary": "#9ca3af",
                    "border": "#374151",
                    "error": "#f87171",
                    "warning": "#fbbf24",
                    "success": "#34d399"
                },
                "fonts": {
                    "family": "Inter, Arial, sans-serif",
                    "size": 10,
                    "weight_normal": "normal",
                    "weight_bold": "600"
                },
                "dimensions": {
                    "border_radius": 8,
                    "padding": 10,
                    "margin": 6
                }
            }
        }
        
        self.available_themes.update(predefined_themes)
        logger.info(f"Cargados {len(predefined_themes)} temas predefinidos")
    
    def load_server_themes(self):
        """Carga los temas disponibles desde el servidor"""
        try:
            if not self.api_client:
                return
            
            # Obtener temas del servidor
            response = self.api_client.get("/configuracion/estilos")
            
            if response:
                for tema_server in response:
                    # Convertir tema del servidor a formato local
                    tema_local = self.convert_server_theme_to_local(tema_server)
                    if tema_local:
                        self.available_themes[tema_server['id']] = tema_local
                
                logger.info(f"Cargados {len(response)} temas desde el servidor")
                
        except Exception as e:
            logger.warning(f"No se pudieron cargar temas del servidor: {e}")
    
    def convert_server_theme_to_local(self, server_theme: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convierte un tema del servidor al formato local"""
        try:
            # Mapear colores del servidor al formato local
            colors = {}
            
            # Colores primarios
            primary_colors = server_theme.get('colores_primarios', {})
            colors.update({
                'primary': primary_colors.get('primary', '#2563eb'),
                'primary_light': primary_colors.get('primary-light', primary_colors.get('primary', '#2563eb')),
                'primary_dark': primary_colors.get('primary-dark', primary_colors.get('primary', '#2563eb')),
                'secondary': primary_colors.get('secondary', '#64748b'),
                'secondary_light': primary_colors.get('secondary-light', primary_colors.get('secondary', '#64748b')),
                'secondary_dark': primary_colors.get('secondary-dark', primary_colors.get('secondary', '#64748b'))
            })
            
            # Colores secundarios
            secondary_colors = server_theme.get('colores_secundarios', {})
            colors.update({
                'accent': secondary_colors.get('accent', '#10b981'),
                'background': secondary_colors.get('background', '#ffffff'),
                'surface': secondary_colors.get('muted', '#f8fafc'),
                'text': secondary_colors.get('foreground', '#1e293b'),
                'text_secondary': secondary_colors.get('muted-foreground', '#64748b'),
                'border': '#e2e8f0',
                'error': '#ef4444',
                'warning': '#f59e0b',
                'success': '#10b981'
            })
            
            # Fuentes
            fonts_config = server_theme.get('fuentes', {})
            fonts = {
                'family': fonts_config.get('font-family', 'Arial, sans-serif'),
                'size': int(fonts_config.get('font-size-base', '10px').replace('px', '')),
                'weight_normal': fonts_config.get('font-weight-normal', 'normal'),
                'weight_bold': fonts_config.get('font-weight-bold', 'bold')
            }
            
            # Dimensiones
            dimensions_config = server_theme.get('tamaños', {})
            dimensions = {
                'border_radius': int(float(dimensions_config.get('border-radius', '0.375rem').replace('rem', '')) * 16),
                'padding': 8,
                'margin': 4
            }
            
            return {
                'nombre': server_theme.get('nombre_tema', 'Tema del servidor'),
                'descripcion': server_theme.get('descripcion', ''),
                'colors': colors,
                'fonts': fonts,
                'dimensions': dimensions,
                'server_id': server_theme.get('id')
            }
            
        except Exception as e:
            logger.error(f"Error convirtiendo tema del servidor: {e}")
            return None
    
    def get_available_themes(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todos los temas disponibles"""
        return self.available_themes
    
    def get_theme_names(self) -> List[str]:
        """Obtiene los nombres de todos los temas disponibles"""
        return list(self.available_themes.keys())
    
    def apply_theme(self, theme_name: str) -> bool:
        """
        Aplica un tema a la aplicación
        
        Args:
            theme_name: Nombre del tema a aplicar
            
        Returns:
            True si se aplicó correctamente, False en caso contrario
        """
        if theme_name not in self.available_themes:
            logger.error(f"Tema '{theme_name}' no encontrado")
            return False
        
        try:
            theme = self.available_themes[theme_name]
            
            # Generar QSS
            qss = self.generate_qss(theme)
            
            # Aplicar a la aplicación
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss)
                
                # Configurar paleta de colores
                self.apply_palette(theme)
                
                # Configurar fuente por defecto
                self.apply_font(theme)
                
                # Guardar tema actual
                self.current_theme = theme_name
                self.config_manager.set('current_theme', theme_name)
                self.config_manager.save_config()
                
                # Emitir señal de cambio
                self.theme_changed.emit(theme_name)
                
                logger.info(f"Tema '{theme_name}' aplicado exitosamente")
                return True
            
        except Exception as e:
            logger.error(f"Error aplicando tema '{theme_name}': {e}")
            return False
        
        return False
    
    def generate_qss(self, theme: Dict[str, Any]) -> str:
        """Genera el código QSS para un tema"""
        colors = theme['colors']
        fonts = theme['fonts']
        dims = theme['dimensions']
        
        qss = f"""
/* Tema: {theme['nombre']} */

/* Configuración global */
QWidget {{
    font-family: {fonts['family']};
    font-size: {fonts['size']}pt;
    color: {colors['text']};
    background-color: {colors['background']};
}}

/* Ventana principal */
QMainWindow {{
    background-color: {colors['background']};
    color: {colors['text']};
}}

/* Botones */
QPushButton {{
    background-color: {colors['primary']};
    color: white;
    border: none;
    border-radius: {dims['border_radius']}px;
    padding: {dims['padding']}px {dims['padding'] * 2}px;
    font-weight: {fonts['weight_bold']};
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {colors['primary_light']};
}}

QPushButton:pressed {{
    background-color: {colors['primary_dark']};
}}

QPushButton:disabled {{
    background-color: {colors['border']};
    color: {colors['text_secondary']};
}}

/* Botones secundarios */
QPushButton[class="secondary"] {{
    background-color: {colors['secondary']};
    color: white;
}}

QPushButton[class="secondary"]:hover {{
    background-color: {colors['secondary_light']};
}}

QPushButton[class="accent"] {{
    background-color: {colors['accent']};
    color: white;
}}

/* Campos de entrada */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: white;
    border: 2px solid {colors['border']};
    border-radius: {dims['border_radius']}px;
    padding: {dims['padding']}px;
    color: {colors['text']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {colors['primary']};
}}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
    background-color: {colors['surface']};
    color: {colors['text_secondary']};
}}

/* ComboBox */
QComboBox {{
    background-color: white;
    border: 2px solid {colors['border']};
    border-radius: {dims['border_radius']}px;
    padding: {dims['padding']}px;
    color: {colors['text']};
}}

QComboBox:focus {{
    border-color: {colors['primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {colors['text']};
    width: 0px;
    height: 0px;
}}

QComboBox QAbstractItemView {{
    background-color: white;
    border: 1px solid {colors['border']};
    selection-background-color: {colors['primary']};
    selection-color: white;
}}

/* SpinBox */
QSpinBox, QDoubleSpinBox {{
    background-color: white;
    border: 2px solid {colors['border']};
    border-radius: {dims['border_radius']}px;
    padding: {dims['padding']}px;
    color: {colors['text']};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {colors['primary']};
}}

/* Tablas */
QTableWidget {{
    background-color: white;
    alternate-background-color: {colors['surface']};
    gridline-color: {colors['border']};
    border: 1px solid {colors['border']};
    border-radius: {dims['border_radius']}px;
}}

QTableWidget::item {{
    padding: {dims['padding']}px;
    border-bottom: 1px solid {colors['border']};
}}

QTableWidget::item:selected {{
    background-color: {colors['primary']};
    color: white;
}}

QHeaderView::section {{
    background-color: {colors['surface']};
    color: {colors['text']};
    padding: {dims['padding']}px;
    border: none;
    border-bottom: 2px solid {colors['border']};
    font-weight: {fonts['weight_bold']};
}}

/* Pestañas */
QTabWidget::pane {{
    border: 1px solid {colors['border']};
    background-color: white;
    border-radius: {dims['border_radius']}px;
}}

QTabBar::tab {{
    background-color: {colors['surface']};
    color: {colors['text']};
    padding: {dims['padding']}px {dims['padding'] * 2}px;
    margin-right: 2px;
    border-top-left-radius: {dims['border_radius']}px;
    border-top-right-radius: {dims['border_radius']}px;
}}

QTabBar::tab:selected {{
    background-color: white;
    border-bottom: 3px solid {colors['primary']};
}}

QTabBar::tab:hover {{
    background-color: {colors['primary_light']};
    color: white;
}}

/* GroupBox */
QGroupBox {{
    font-weight: {fonts['weight_bold']};
    border: 2px solid {colors['border']};
    border-radius: {dims['border_radius']}px;
    margin-top: 10px;
    padding-top: 10px;
    background-color: white;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 {dims['padding']}px 0 {dims['padding']}px;
    color: {colors['primary']};
    background-color: white;
}}

/* Etiquetas */
QLabel {{
    color: {colors['text']};
    background-color: transparent;
}}

QLabel[class="title"] {{
    font-size: {fonts['size'] + 6}pt;
    font-weight: {fonts['weight_bold']};
    color: {colors['primary']};
}}

QLabel[class="subtitle"] {{
    font-size: {fonts['size'] + 2}pt;
    color: {colors['text_secondary']};
}}

QLabel[class="error"] {{
    color: {colors['error']};
    font-weight: {fonts['weight_bold']};
}}

QLabel[class="success"] {{
    color: {colors['success']};
    font-weight: {fonts['weight_bold']};
}}

QLabel[class="warning"] {{
    color: {colors['warning']};
    font-weight: {fonts['weight_bold']};
}}

/* Menús */
QMenuBar {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border-bottom: 1px solid {colors['border']};
}}

QMenuBar::item {{
    padding: {dims['padding']}px {dims['padding'] * 2}px;
}}

QMenuBar::item:selected {{
    background-color: {colors['primary']};
    color: white;
}}

QMenu {{
    background-color: white;
    border: 1px solid {colors['border']};
    color: {colors['text']};
}}

QMenu::item {{
    padding: {dims['padding']}px {dims['padding'] * 2}px;
}}

QMenu::item:selected {{
    background-color: {colors['primary']};
    color: white;
}}

/* Barras de herramientas */
QToolBar {{
    background-color: {colors['surface']};
    border: none;
    spacing: {dims['margin']}px;
}}

QToolButton {{
    background-color: transparent;
    color: {colors['text']};
    border: none;
    border-radius: {dims['border_radius']}px;
    padding: {dims['padding']}px;
}}

QToolButton:hover {{
    background-color: {colors['primary']};
    color: white;
}}

/* Barras de estado */
QStatusBar {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border-top: 1px solid {colors['border']};
}}

/* Checkbox y RadioButton */
QCheckBox, QRadioButton {{
    color: {colors['text']};
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {colors['border']};
    border-radius: 3px;
    background-color: white;
}}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {colors['primary']};
    border-color: {colors['primary']};
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: {colors['surface']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background: {colors['border']};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background: {colors['primary']};
}}

QScrollBar:horizontal {{
    background: {colors['surface']};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background: {colors['border']};
    border-radius: 6px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {colors['primary']};
}}

/* Sliders */
QSlider::groove:horizontal {{
    border: 1px solid {colors['border']};
    height: 8px;
    background: {colors['surface']};
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: {colors['primary']};
    border: 1px solid {colors['primary']};
    width: 18px;
    border-radius: 9px;
    margin: -5px 0;
}}

QSlider::handle:horizontal:hover {{
    background: {colors['primary_light']};
}}

/* ProgressBar */
QProgressBar {{
    border: 2px solid {colors['border']};
    border-radius: {dims['border_radius']}px;
    background-color: {colors['surface']};
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {colors['primary']};
    border-radius: {dims['border_radius'] - 2}px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {colors['border']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* Frame */
QFrame {{
    border: 1px solid {colors['border']};
    border-radius: {dims['border_radius']}px;
    background-color: white;
}}

QFrame[frameShape="4"] {{ /* StyledPanel */
    background-color: white;
}}

/* ListWidget */
QListWidget {{
    background-color: white;
    border: 1px solid {colors['border']};
    border-radius: {dims['border_radius']}px;
    color: {colors['text']};
}}

QListWidget::item {{
    padding: {dims['padding']}px;
    border-bottom: 1px solid {colors['border']};
}}

QListWidget::item:selected {{
    background-color: {colors['primary']};
    color: white;
}}

QListWidget::item:hover {{
    background-color: {colors['surface']};
}}

/* TreeWidget */
QTreeWidget {{
    background-color: white;
    border: 1px solid {colors['border']};
    border-radius: {dims['border_radius']}px;
    color: {colors['text']};
}}

QTreeWidget::item {{
    padding: {dims['padding']}px;
}}

QTreeWidget::item:selected {{
    background-color: {colors['primary']};
    color: white;
}}

QTreeWidget::item:hover {{
    background-color: {colors['surface']};
}}

/* DateEdit y TimeEdit */
QDateEdit, QTimeEdit, QDateTimeEdit {{
    background-color: white;
    border: 2px solid {colors['border']};
    border-radius: {dims['border_radius']}px;
    padding: {dims['padding']}px;
    color: {colors['text']};
}}

QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
    border-color: {colors['primary']};
}}

/* Calendar Widget */
QCalendarWidget {{
    background-color: white;
    border: 1px solid {colors['border']};
}}

QCalendarWidget QTableView {{
    selection-background-color: {colors['primary']};
    selection-color: white;
}}
"""
        
        return qss
    
    def apply_palette(self, theme: Dict[str, Any]):
        """Aplica la paleta de colores del tema"""
        try:
            app = QApplication.instance()
            if not app:
                return
            
            colors = theme['colors']
            palette = QPalette()
            
            # Colores básicos
            palette.setColor(QPalette.ColorRole.Window, QColor(colors['background']))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(colors['text']))
            palette.setColor(QPalette.ColorRole.Base, QColor('#ffffff'))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors['surface']))
            palette.setColor(QPalette.ColorRole.Text, QColor(colors['text']))
            palette.setColor(QPalette.ColorRole.Button, QColor(colors['primary']))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor('#ffffff'))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(colors['primary']))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#ffffff'))
            
            # Aplicar paleta
            app.setPalette(palette)
            
        except Exception as e:
            logger.error(f"Error aplicando paleta: {e}")
    
    def apply_font(self, theme: Dict[str, Any]):
        """Aplica la configuración de fuente del tema"""
        try:
            app = QApplication.instance()
            if not app:
                return
            
            fonts = theme['fonts']
            
            # Crear fuente
            font = QFont()
            font.setFamily(fonts['family'].split(',')[0].strip())
            font.setPointSize(fonts['size'])
            
            # Aplicar fuente por defecto
            app.setFont(font)
            
        except Exception as e:
            logger.error(f"Error aplicando fuente: {e}")
    
    def get_current_theme(self) -> Optional[str]:
        """Obtiene el tema actual"""
        return self.current_theme
    
    def save_theme_to_file(self, theme_name: str, file_path: str) -> bool:
        """Guarda un tema en un archivo JSON"""
        try:
            if theme_name not in self.available_themes:
                return False
            
            theme_data = self.available_themes[theme_name]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Tema '{theme_name}' guardado en {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando tema: {e}")
            return False
    
    def load_theme_from_file(self, file_path: str, theme_name: str = None) -> bool:
        """Carga un tema desde un archivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            if not theme_name:
                theme_name = os.path.splitext(os.path.basename(file_path))[0]
            
            self.available_themes[theme_name] = theme_data
            logger.info(f"Tema '{theme_name}' cargado desde {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando tema desde archivo: {e}")
            return False
    
    def apply_system_theme(self):
        """Aplica el tema del sistema operativo"""
        try:
            app = QApplication.instance()
            if not app:
                return False
            
            # Resetear estilos
            app.setStyleSheet("")
            
            # Usar paleta del sistema
            app.setPalette(app.style().standardPalette())
            
            self.current_theme = "system"
            self.config_manager.set('current_theme', 'system')
            self.config_manager.save_config()
            
            self.theme_changed.emit("system")
            logger.info("Tema del sistema aplicado")
            return True
            
        except Exception as e:
            logger.error(f"Error aplicando tema del sistema: {e}")
            return False
    
    def sync_with_server_theme(self) -> bool:
        """Sincroniza con el tema activo del servidor"""
        try:
            if not self.api_client:
                return False
            
            # Obtener configuración del servidor
            response = self.api_client.get("/configuracion/sistema")
            
            if response and response.get('tema_activo'):
                server_theme = response['tema_activo']
                
                # Convertir y aplicar tema del servidor
                local_theme = self.convert_server_theme_to_local(server_theme)
                if local_theme:
                    theme_name = f"server_{server_theme['id']}"
                    self.available_themes[theme_name] = local_theme
                    return self.apply_theme(theme_name)
            
            return False
            
        except Exception as e:
            logger.error(f"Error sincronizando con tema del servidor: {e}")
            return False
    
    def initialize_default_theme(self):
        """Inicializa el tema por defecto"""
        # Intentar cargar el tema guardado en configuración
        saved_theme = self.config_manager.get('current_theme', 'clasico')
        
        if saved_theme == 'system':
            self.apply_system_theme()
        elif saved_theme in self.available_themes:
            self.apply_theme(saved_theme)
        else:
            # Aplicar tema clásico por defecto
            self.apply_theme('clasico') 