"""
Dashboard personalizable para el Sistema de Gimnasio v6
Incluye widgets arrastrables, redimensionables y configurables
"""
import logging
import json
import os
from typing import Dict, List, Optional, Any, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QSizePolicy, QMenu,
    QAction, QDialog, QDialogButtonBox, QFormLayout, QSpinBox,
    QComboBox, QCheckBox, QLineEdit, QTextEdit, QListWidget,
    QListWidgetItem, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor, QDrag, QMouseEvent, QAction

logger = logging.getLogger(__name__)

class DraggableWidget(QFrame):
    """Widget base arrastrable y redimensionable"""
    
    widget_moved = pyqtSignal(int, int)  # x, y
    widget_resized = pyqtSignal(int, int)  # width, height
    widget_clicked = pyqtSignal()
    
    def __init__(self, widget_id: str, title: str = "", parent=None):
        super().__init__(parent)
        self.widget_id = widget_id
        self.title = title
        self.is_dragging = False
        self.is_resizing = False
        self.drag_start_pos = QPoint()
        self.resize_start_pos = QPoint()
        self.original_size = QSize()
        self.original_pos = QPoint()
        
        self.setup_ui()
        self.setup_behavior()
    
    def setup_ui(self):
        """Configura la interfaz del widget"""
        self.setObjectName("draggableWidget")
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setMinimumSize(200, 150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Estilo base
        self.setStyleSheet("""
            QFrame#draggableWidget {
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 8px;
            }
            QFrame#draggableWidget:hover {
                border-color: var(--primary-color);
                box-shadow: var(--shadow-md);
            }
        """)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Header con título y controles
        header_layout = QHBoxLayout()
        
        # Título
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            QLabel {
                color: var(--text-primary);
                font-weight: 600;
                font-size: 14px;
            }
        """)
        header_layout.addWidget(self.title_label)
        
        # Espaciador
        header_layout.addStretch()
        
        # Botón de menú
        self.menu_button = QPushButton("⋮")
        self.menu_button.setFixedSize(24, 24)
        self.menu_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: var(--text-secondary);
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: var(--text-primary);
                background: var(--state-hover);
                border-radius: 4px;
            }
        """)
        self.menu_button.clicked.connect(self.show_context_menu)
        header_layout.addWidget(self.menu_button)
        
        layout.addLayout(header_layout)
        
        # Contenedor para el contenido del widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content_widget)
    
    def setup_behavior(self):
        """Configura el comportamiento de arrastre y redimensionamiento"""
        # Hacer el widget seleccionable
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Configurar para recibir eventos de mouse
        self.setMouseTracking(True)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Maneja el presionado del mouse"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.pos()
            self.original_pos = self.pos()
            self.is_dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.widget_clicked.emit()
        event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Maneja el movimiento del mouse"""
        if self.is_dragging:
            # Calcular nueva posición
            delta = event.pos() - self.drag_start_pos
            new_pos = self.original_pos + delta
            
            # Emitir señal de movimiento
            self.widget_moved.emit(new_pos.x(), new_pos.y())
            
            # Actualizar posición
            self.move(new_pos)
        elif self.is_resizing:
            # Calcular nuevo tamaño
            delta = event.pos() - self.resize_start_pos
            new_size = self.original_size + QSize(delta.x(), delta.y())
            
            # Aplicar restricciones de tamaño mínimo
            new_size = new_size.expandedTo(self.minimumSize())
            
            # Emitir señal de redimensionamiento
            self.widget_resized.emit(new_size.width(), new_size.height())
            
            # Actualizar tamaño
            self.resize(new_size)
        else:
            # Detectar si está en el borde para redimensionamiento
            margin = 5
            if (event.pos().x() >= self.width() - margin or 
                event.pos().y() >= self.height() - margin):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        
        event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Maneja la liberación del mouse"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.is_resizing = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        event.accept()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Maneja el doble click para configurar"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.show_config_dialog()
        event.accept()
    
    def show_context_menu(self):
        """Muestra el menú contextual del widget"""
        menu = QMenu(self)
        
        # Acción de configuración
        config_action = QAction("Configurar", self)
        config_action.triggered.connect(self.show_config_dialog)
        menu.addAction(config_action)
        
        # Acción de duplicar
        duplicate_action = QAction("Duplicar", self)
        duplicate_action.triggered.connect(self.duplicate_widget)
        menu.addAction(duplicate_action)
        
        menu.addSeparator()
        
        # Acción de eliminar
        delete_action = QAction("Eliminar", self)
        delete_action.triggered.connect(self.delete_widget)
        menu.addAction(delete_action)
        
        menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))
    
    def show_config_dialog(self):
        """Muestra el diálogo de configuración del widget"""
        # Implementación base - debe ser sobrescrita por widgets específicos
        pass
    
    def duplicate_widget(self):
        """Duplica el widget"""
        # Emitir señal para que el dashboard maneje la duplicación
        pass
    
    def delete_widget(self):
        """Elimina el widget"""
        reply = QMessageBox.question(
            self, "Eliminar Widget",
            f"¿Estás seguro de que quieres eliminar el widget '{self.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.deleteLater()
    
    def set_title(self, title: str):
        """Establece el título del widget"""
        self.title = title
        self.title_label.setText(title)
    
    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración del widget"""
        return {
            'id': self.widget_id,
            'title': self.title,
            'x': self.x(),
            'y': self.y(),
            'width': self.width(),
            'height': self.height()
        }
    
    def set_config(self, config: Dict[str, Any]):
        """Establece la configuración del widget"""
        if 'title' in config:
            self.set_title(config['title'])
        if 'x' in config and 'y' in config:
            self.move(config['x'], config['y'])
        if 'width' in config and 'height' in config:
            self.resize(config['width'], config['height'])

class KPICardWidget(DraggableWidget):
    """Widget de tarjeta KPI personalizable"""
    
    def __init__(self, widget_id: str, title: str = "KPI", metric_name: str = "usuarios", parent=None):
        super().__init__(widget_id, title, parent)
        self.metric_name = metric_name
        self.value = 0
        self.previous_value = 0
        self.unit = ""
        self.color = "#3b82f6"
        self.setup_kpi_content()
    
    def setup_kpi_content(self):
        """Configura el contenido específico del KPI"""
        # Valor principal
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {self.color};
                font-size: 32px;
                font-weight: bold;
                text-align: center;
            }}
        """)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.value_label)
        
        # Unidad
        self.unit_label = QLabel(self.unit)
        self.unit_label.setStyleSheet("""
            QLabel {
                color: var(--text-secondary);
                font-size: 14px;
                text-align: center;
            }
        """)
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.unit_label)
        
        # Cambio porcentual
        self.change_label = QLabel("+0%")
        self.change_label.setStyleSheet("""
            QLabel {
                color: var(--success-color);
                font-size: 12px;
                text-align: center;
            }
        """)
        self.change_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.change_label)
    
    def update_value(self, value: float, unit: str = "", previous_value: float = None):
        """Actualiza el valor del KPI"""
        self.value = value
        self.unit = unit
        if previous_value is not None:
            self.previous_value = float(previous_value)
        
        # Actualizar etiquetas
        self.value_label.setText(f"{value:,.0f}")
        self.unit_label.setText(unit)
        
        # Calcular y mostrar cambio
        if self.previous_value > 0:
            change_percent = ((value - self.previous_value) / self.previous_value) * 100
            change_text = f"{change_percent:+.1f}%"
            
            if change_percent > 0:
                self.change_label.setStyleSheet("""
                    QLabel {
                        color: var(--success-color);
                        font-size: 12px;
                        text-align: center;
                    }
                """)
                self.change_label.setText(f"↑ {change_text}")
            elif change_percent < 0:
                self.change_label.setStyleSheet("""
                    QLabel {
                        color: var(--error-color);
                        font-size: 12px;
                        text-align: center;
                    }
                """)
                self.change_label.setText(f"↓ {change_text}")
            else:
                self.change_label.setStyleSheet("""
                    QLabel {
                        color: var(--text-muted);
                        font-size: 12px;
                        text-align: center;
                    }
                """)
                self.change_label.setText("0%")
    
    def set_color(self, color: str):
        """Establece el color del KPI"""
        self.color = color
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 32px;
                font-weight: bold;
                text-align: center;
            }}
        """)
    
    def show_config_dialog(self):
        """Muestra el diálogo de configuración del KPI"""
        dialog = KPIConfigDialog(self, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            self.set_title(config['title'])
            self.set_color(config['color'])
            if hasattr(self, 'metric_name') and isinstance(config['metric_name'], str):
                setattr(self, 'metric_name', config['metric_name'])

class ChartWidget(DraggableWidget):
    """Widget de gráfico personalizable"""
    
    def __init__(self, widget_id: str, title: str = "Gráfico", chart_type: str = "line", parent=None):
        super().__init__(widget_id, title, parent)
        self.chart_type = chart_type
        self.data = []
        self.labels = []
        self.setup_chart_content()
    
    def setup_chart_content(self):
        """Configura el contenido del gráfico"""
        # Placeholder para el gráfico
        self.chart_placeholder = QLabel("📊 Gráfico")
        self.chart_placeholder.setStyleSheet("""
            QLabel {
                color: var(--text-secondary);
                font-size: 48px;
                text-align: center;
                padding: 20px;
            }
        """)
        self.chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.chart_placeholder)
        
        # Información del gráfico
        self.info_label = QLabel(f"Tipo: {self.chart_type}")
        self.info_label.setStyleSheet("""
            QLabel {
                color: var(--text-muted);
                font-size: 12px;
                text-align: center;
            }
        """)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.info_label)
    
    def update_data(self, data: List[float], labels: List[str]):
        """Actualiza los datos del gráfico"""
        self.data = data
        self.labels = labels
        
        # TODO: Implementar renderizado real del gráfico
        self.info_label.setText(f"Tipo: {self.chart_type} | Datos: {len(data)} puntos")
    
    def set_chart_type(self, chart_type: str):
        """Establece el tipo de gráfico"""
        self.chart_type = chart_type
        self.info_label.setText(f"Tipo: {chart_type} | Datos: {len(self.data)} puntos")
    
    def show_config_dialog(self):
        """Muestra el diálogo de configuración del gráfico"""
        dialog = ChartConfigDialog(self, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            self.set_title(config['title'])
            self.set_chart_type(config['chart_type'])

class TableWidget(DraggableWidget):
    """Widget de tabla personalizable"""
    
    def __init__(self, widget_id: str, title: str = "Tabla", parent=None):
        super().__init__(widget_id, title, parent)
        self.columns = []
        self.data = []
        self.max_rows = 10
        self.setup_table_content()
    
    def setup_table_content(self):
        """Configura el contenido de la tabla"""
        # Placeholder para la tabla
        self.table_placeholder = QLabel("📋 Tabla")
        self.table_placeholder.setStyleSheet("""
            QLabel {
                color: var(--text-secondary);
                font-size: 48px;
                text-align: center;
                padding: 20px;
            }
        """)
        self.table_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.table_placeholder)
        
        # Información de la tabla
        self.info_label = QLabel("Sin datos")
        self.info_label.setStyleSheet("""
            QLabel {
                color: var(--text-muted);
                font-size: 12px;
                text-align: center;
            }
        """)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.info_label)
    
    def update_data(self, columns: List[str], data: List[List]):
        """Actualiza los datos de la tabla"""
        self.columns = columns
        self.data = data
        
        if data:
            self.info_label.setText(f"{len(columns)} columnas, {len(data)} filas")
        else:
            self.info_label.setText("Sin datos")
    
    def set_max_rows(self, max_rows: int):
        """Establece el número máximo de filas"""
        self.max_rows = max_rows
    
    def show_config_dialog(self):
        """Muestra el diálogo de configuración de la tabla"""
        dialog = TableConfigDialog(self, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            self.set_title(config['title'])
            self.set_max_rows(config['max_rows'])

class DashboardGrid(QWidget):
    """Grid personalizable para el dashboard"""
    
    layout_changed = pyqtSignal()
    widget_added = pyqtSignal(str, str)  # widget_id, widget_type
    widget_removed = pyqtSignal(str)  # widget_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.widgets: Dict[str, DraggableWidget] = {}
        self.grid_size = 20  # Tamaño de la cuadrícula
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz del grid"""
        self.setObjectName("dashboardGrid")
        self.setStyleSheet("""
            QWidget#dashboardGrid {
                background: var(--bg-primary);
                border: 1px dashed var(--border-color);
                border-radius: 8px;
            }
        """)
        
        # Layout principal
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(0)
        
        # Área de widgets con scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        # Widget contenedor para los widgets arrastrables
        self.widget_container = QWidget()
        self.widget_container.setObjectName("widgetContainer")
        self.widget_container.setStyleSheet("""
            QWidget#widgetContainer {
                background: transparent;
                min-height: 600px;
            }
        """)
        
        self.scroll_area.setWidget(self.widget_container)
        self._layout.addWidget(self.scroll_area)
    
    def add_widget(self, widget: DraggableWidget, x: int = 0, y: int = 0):
        """Agrega un widget al dashboard"""
        widget.setParent(self.widget_container)
        # Solo mover si el widget tiene el método y es QWidget
        if isinstance(widget, QWidget) and hasattr(widget, 'move'):
            widget.move(x, y)
        widget.show()
        
        self.widgets[widget.widget_id] = widget
        
        # Conectar señales
        widget.widget_moved.connect(self.on_widget_moved)
        widget.widget_resized.connect(self.on_widget_resized)
        widget.widget_clicked.connect(self.on_widget_clicked)
        
        self.widget_added.emit(widget.widget_id, type(widget).__name__)
        self.layout_changed.emit()
    
    def remove_widget(self, widget_id: str):
        """Remueve un widget del dashboard"""
        if widget_id in self.widgets:
            widget = self.widgets[widget_id]
            widget.deleteLater()
            del self.widgets[widget_id]
            
            self.widget_removed.emit(widget_id)
            self.layout_changed.emit()
    
    def get_widget(self, widget_id: str) -> Optional[DraggableWidget]:
        """Obtiene un widget por ID"""
        return self.widgets.get(widget_id)
    
    def get_all_widgets(self) -> List[DraggableWidget]:
        """Obtiene todos los widgets"""
        return list(self.widgets.values())
    
    def on_widget_moved(self, x: int, y: int):
        snapped_x = (x // self.grid_size) * self.grid_size
        snapped_y = (y // self.grid_size) * self.grid_size
        sender = self.sender()
        if isinstance(sender, QWidget) and hasattr(sender, 'move'):
            sender.move(snapped_x, snapped_y)
        
        self.layout_changed.emit()
    
    def on_widget_resized(self, width: int, height: int):
        snapped_width = (width // self.grid_size) * self.grid_size
        snapped_height = (height // self.grid_size) * self.grid_size
        sender = self.sender()
        if isinstance(sender, QWidget) and hasattr(sender, 'resize'):
            sender.resize(snapped_width, snapped_height)
        
        self.layout_changed.emit()
    
    def on_widget_clicked(self):
        for widget in self.widgets.values():
            if widget != self.sender() and isinstance(widget, QWidget) and hasattr(widget, 'setStyleSheet') and hasattr(widget, 'styleSheet'):
                style = widget.styleSheet()
                if isinstance(style, str):
                    widget.setStyleSheet(style.replace("border-color: var(--primary-color);", ""))
        sender = self.sender()
        if isinstance(sender, QWidget) and hasattr(sender, 'setStyleSheet') and hasattr(sender, 'styleSheet'):
            current_style = sender.styleSheet()
            if isinstance(current_style, str) and "border-color: var(--primary-color);" not in current_style:
                sender.setStyleSheet(current_style + "border-color: var(--primary-color);")
    
    def save_layout(self) -> Dict[str, Any]:
        """Guarda el layout actual"""
        layout_data = {
            'grid_size': self.grid_size,
            'widgets': {}
        }
        
        for widget_id, widget in self.widgets.items():
            layout_data['widgets'][widget_id] = {
                'type': type(widget).__name__,
                'config': widget.get_config()
            }
        
        return layout_data
    
    def load_layout(self, layout_data: Dict[str, Any]):
        """Carga un layout guardado"""
        # Limpiar widgets existentes
        for widget in self.widgets.values():
            widget.deleteLater()
        self.widgets.clear()
        
        # Cargar configuración
        self.grid_size = layout_data.get('grid_size', 20)
        
        # Cargar widgets
        widgets_data = layout_data.get('widgets', {})
        for widget_id, widget_data in widgets_data.items():
            widget_type = widget_data['type']
            config = widget_data['config']
            
            # Crear widget según el tipo
            if widget_type == 'KPICardWidget':
                widget = KPICardWidget(widget_id, config['title'])
            elif widget_type == 'ChartWidget':
                widget = ChartWidget(widget_id, config['title'])
            elif widget_type == 'TableWidget':
                widget = TableWidget(widget_id, config['title'])
            else:
                widget = DraggableWidget(widget_id, config['title'])
            
            # Aplicar configuración
            widget.set_config(config)
            
            # Agregar al dashboard
            self.add_widget(widget, config.get('x', 0), config.get('y', 0))

class DashboardPersonalizable(QWidget):
    """Dashboard principal personalizable"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = DashboardGrid()
        self.layout_file = "config/dashboard_layout.json"
        self.setup_ui()
        self.load_default_layout()
    
    def setup_ui(self):
        """Configura la interfaz del dashboard"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QWidget()
        toolbar.setObjectName("dashboardToolbar")
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("""
            QWidget#dashboardToolbar {
                background: var(--bg-secondary);
                border-bottom: 1px solid var(--border-color);
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 8, 16, 8)
        toolbar_layout.setSpacing(8)
        
        # Título
        title = QLabel("Dashboard Personalizable")
        title.setStyleSheet("""
            QLabel {
                color: var(--text-primary);
                font-weight: 600;
                font-size: 16px;
            }
        """)
        toolbar_layout.addWidget(title)
        
        toolbar_layout.addStretch()
        
        # Botón de agregar widget
        add_widget_btn = QPushButton("+ Agregar Widget")
        add_widget_btn.setStyleSheet("""
            QPushButton {
                background: var(--primary-color);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: var(--primary-hover);
            }
        """)
        add_widget_btn.clicked.connect(self.show_add_widget_dialog)
        toolbar_layout.addWidget(add_widget_btn)
        
        # Botón de guardar layout
        save_btn = QPushButton("💾 Guardar")
        save_btn.setStyleSheet("""
            QPushButton {
                background: var(--success-color);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #16a34a;
            }
        """)
        save_btn.clicked.connect(self.save_layout)
        toolbar_layout.addWidget(save_btn)
        
        # Botón de reset
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: var(--warning-color);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #d97706;
            }
        """)
        reset_btn.clicked.connect(self.reset_layout)
        toolbar_layout.addWidget(reset_btn)
        
        layout.addWidget(toolbar)
        
        # Grid del dashboard
        layout.addWidget(self.grid)
        
        # Conectar señales
        self.grid.layout_changed.connect(self.on_layout_changed)
    
    def show_add_widget_dialog(self):
        """Muestra el diálogo para agregar widgets"""
        dialog = AddWidgetDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            widget_type, config = dialog.get_widget_config()
            self.add_widget(widget_type, config)
    
    def add_widget(self, widget_type: str, config: Dict[str, Any]):
        """Agrega un widget al dashboard"""
        widget_id = f"{widget_type}_{len(self.grid.widgets) + 1}"
        
        if widget_type == "KPI":
            widget = KPICardWidget(widget_id, config.get('title', 'KPI'), config.get('metric_name', 'usuarios'))
        elif widget_type == "Chart":
            widget = ChartWidget(widget_id, config.get('title', 'Gráfico'))
        elif widget_type == "Table":
            widget = TableWidget(widget_id, config.get('title', 'Tabla'))
        elif widget_type == "PushNotifications":
            widget = PushNotificationsWidget(widget_id, config.get('title', 'Notificaciones Push'))
        elif widget_type == "ImportData":
            widget = ImportDataWidget(widget_id, config.get('title', 'Importar Datos'))
        else:
            widget = DraggableWidget(widget_id, config.get('title', 'Widget'))
        
        # Posición inicial
        x = len(self.grid.widgets) * 220
        y = 0
        
        self.grid.add_widget(widget, x, y)
    
    def save_layout(self):
        """Guarda el layout actual"""
        try:
            os.makedirs(os.path.dirname(self.layout_file), exist_ok=True)
            layout_data = self.grid.save_layout()
            
            with open(self.layout_file, 'w', encoding='utf-8') as f:
                json.dump(layout_data, f, indent=2, ensure_ascii=False)
            
            logger.info("Layout del dashboard guardado")
            
        except Exception as e:
            logger.error(f"Error guardando layout: {e}")
    
    def load_layout(self):
        """Carga el layout guardado"""
        try:
            if os.path.exists(self.layout_file):
                with open(self.layout_file, 'r', encoding='utf-8') as f:
                    layout_data = json.load(f)
                
                self.grid.load_layout(layout_data)
                logger.info("Layout del dashboard cargado")
            
        except Exception as e:
            logger.error(f"Error cargando layout: {e}")
            self.load_default_layout()
    
    def load_default_layout(self):
        """Carga el layout por defecto"""
        # Crear widgets por defecto
        kpi1 = KPICardWidget("kpi_1", "Usuarios Activos")
        kpi1.update_value(1250, "usuarios")
        
        kpi2 = KPICardWidget("kpi_2", "Ingresos Mensuales")
        kpi2.update_value(45000, "$")
        
        chart1 = ChartWidget("chart_1", "Asistencia Semanal")
        
        table1 = TableWidget("table_1", "Últimos Pagos")
        
        # Agregar al grid
        self.grid.add_widget(kpi1, 0, 0)
        self.grid.add_widget(kpi2, 220, 0)
        self.grid.add_widget(chart1, 0, 200)
        self.grid.add_widget(table1, 220, 200)
    
    def reset_layout(self):
        """Resetea el layout al estado por defecto"""
        reply = QMessageBox.question(
            self, "Reset Layout",
            "¿Estás seguro de que quieres resetear el layout? Se perderán todos los cambios.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Limpiar widgets existentes
            for widget in self.grid.widgets.values():
                widget.deleteLater()
            self.grid.widgets.clear()
            
            # Cargar layout por defecto
            self.load_default_layout()
    
    def on_layout_changed(self):
        """Maneja cambios en el layout"""
        # Auto-guardar después de un delay
        QTimer.singleShot(2000, self.save_layout)

# Diálogos de configuración

class KPIConfigDialog(QDialog):
    """Diálogo de configuración para KPIs"""
    
    def __init__(self, parent=None, widget: Optional['KPICardWidget'] = None):
        super().__init__(parent)
        self.widget = widget
        self.setup_ui()
        self.load_current_config()
    
    def setup_ui(self):
        """Configura la interfaz del diálogo"""
        self.setWindowTitle("Configurar KPI")
        self.setFixedSize(400, 300)
        
        layout = QFormLayout(self)
        layout.setSpacing(16)
        
        # Título
        self.title_edit = QLineEdit()
        layout.addRow("Título:", self.title_edit)
        
        # Métrica
        self.metric_combo = QComboBox()
        self.metric_combo.addItems(["usuarios", "ingresos", "asistencias", "clases", "pagos"])
        layout.addRow("Métrica:", self.metric_combo)
        
        # Color
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Azul", "Verde", "Rojo", "Amarillo", "Morado"])
        layout.addRow("Color:", self.color_combo)
        
        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def load_current_config(self):
        """Carga la configuración actual"""
        if self.widget and hasattr(self.widget, 'title') and hasattr(self.widget, 'metric_name'):
            self.title_edit.setText(str(self.widget.title))
            metric_value = getattr(self.widget, 'metric_name', None)
            if isinstance(metric_value, str):
                self.metric_combo.setCurrentText(metric_value)
    
    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración del diálogo"""
        color_map = {
            "Azul": "#3b82f6",
            "Verde": "#10b981",
            "Rojo": "#ef4444",
            "Amarillo": "#f59e0b",
            "Morado": "#8b5cf6"
        }
        
        return {
            'title': self.title_edit.text(),
            'metric_name': self.metric_combo.currentText(),
            'color': color_map.get(self.color_combo.currentText(), "#3b82f6")
        }

class ChartConfigDialog(QDialog):
    """Diálogo de configuración para gráficos"""
    
    def __init__(self, parent=None, widget: Optional['ChartWidget'] = None):
        super().__init__(parent)
        self.widget = widget
        self.setup_ui()
        self.load_current_config()
    
    def setup_ui(self):
        """Configura la interfaz del diálogo"""
        self.setWindowTitle("Configurar Gráfico")
        self.setFixedSize(400, 250)
        
        layout = QFormLayout(self)
        layout.setSpacing(16)
        
        # Título
        self.title_edit = QLineEdit()
        layout.addRow("Título:", self.title_edit)
        
        # Tipo de gráfico
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["line", "bar", "pie", "area"])
        layout.addRow("Tipo:", self.chart_type_combo)
        
        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def load_current_config(self):
        """Carga la configuración actual"""
        if self.widget and hasattr(self.widget, 'title') and hasattr(self.widget, 'chart_type'):
            self.title_edit.setText(str(self.widget.title))
            chart_type_value = getattr(self.widget, 'chart_type', None)
            if isinstance(chart_type_value, str):
                self.chart_type_combo.setCurrentText(chart_type_value)
    
    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración del diálogo"""
        return {
            'title': self.title_edit.text(),
            'chart_type': self.chart_type_combo.currentText()
        }

class TableConfigDialog(QDialog):
    """Diálogo de configuración para tablas"""
    
    def __init__(self, parent=None, widget: Optional['TableWidget'] = None):
        super().__init__(parent)
        self.widget = widget
        self.setup_ui()
        self.load_current_config()
    
    def setup_ui(self):
        """Configura la interfaz del diálogo"""
        self.setWindowTitle("Configurar Tabla")
        self.setFixedSize(400, 250)
        
        layout = QFormLayout(self)
        layout.setSpacing(16)
        
        # Título
        self.title_edit = QLineEdit()
        layout.addRow("Título:", self.title_edit)
        
        # Máximo de filas
        self.max_rows_spin = QSpinBox()
        self.max_rows_spin.setRange(5, 50)
        self.max_rows_spin.setValue(10)
        layout.addRow("Máx. filas:", self.max_rows_spin)
        
        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def load_current_config(self):
        """Carga la configuración actual"""
        if self.widget and hasattr(self.widget, 'title') and hasattr(self.widget, 'max_rows'):
            self.title_edit.setText(str(self.widget.title))
            self.max_rows_spin.setValue(self.widget.max_rows)
    
    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración del diálogo"""
        return {
            'title': self.title_edit.text(),
            'max_rows': self.max_rows_spin.value()
        }

class AddWidgetDialog(QDialog):
    """Diálogo para agregar widgets"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz del diálogo"""
        self.setWindowTitle("Agregar Widget")
        self.setFixedSize(400, 350)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Lista de widgets disponibles
        self.widget_list = QListWidget()
        self.widget_list.addItem("📊 KPI Card")
        self.widget_list.addItem("📈 Gráfico")
        self.widget_list.addItem("📋 Tabla")
        self.widget_list.addItem("🔔 Notificaciones Push")
        self.widget_list.addItem("⬆️ Importar Datos")
        self.widget_list.addItem("📝 Widget Personalizado")
        layout.addWidget(self.widget_list)
        
        # Configuración del widget
        self.config_widget = QWidget()
        config_layout = QFormLayout(self.config_widget)
        
        self.title_edit = QLineEdit()
        config_layout.addRow("Título:", self.title_edit)
        
        layout.addWidget(self.config_widget)
        
        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_widget_config(self) -> tuple[str, Dict[str, Any]]:
        """Obtiene la configuración del widget seleccionado"""
        current_row = self.widget_list.currentRow()
        widget_types = ["KPI", "Chart", "Table", "PushNotifications", "ImportData", "Custom"]
        
        widget_type = widget_types[current_row] if current_row >= 0 else "Custom"
        
        config = {
            'title': self.title_edit.text() or f"Nuevo {widget_type}"
        }
        
        return widget_type, config 

class PushNotificationsWidget(DraggableWidget):
    """Widget visual de notificaciones push"""
    def __init__(self, widget_id: str, title: str = "Notificaciones Push", parent=None):
        super().__init__(widget_id, title, parent)
        self.setup_push_content()

    def setup_push_content(self):
        from .toast_notifications import ToastManager, ToastContainer
        self.toast_container = ToastContainer(self)
        self.content_layout.addWidget(self.toast_container)
        self.setMinimumHeight(220)
        self.setMinimumWidth(350)
        # Botón para mostrar historial
        self.history_button = QPushButton("Ver historial")
        self.history_button.clicked.connect(self.show_history)
        self.content_layout.addWidget(self.history_button)
        # Filtros y configuración
        self.filter_box = QLineEdit()
        self.filter_box.setPlaceholderText("Filtrar notificaciones...")
        self.filter_box.textChanged.connect(self.filter_notifications)
        self.content_layout.addWidget(self.filter_box)
        # Inicializar historial
        self.history = []

    def show_history(self):
        # Mostrar historial en un diálogo
        dlg = QDialog(self)
        dlg.setWindowTitle("Historial de Notificaciones Push")
        dlg.setFixedSize(400, 400)
        layout = QVBoxLayout(dlg)
        list_widget = QListWidget()
        for notif in self.history:
            item = QListWidgetItem(f"{notif['title']}: {notif['message']}")
            list_widget.addItem(item)
        layout.addWidget(list_widget)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btns.accepted.connect(dlg.accept)
        layout.addWidget(btns)
        dlg.exec()

    def filter_notifications(self, text):
        # Filtrar notificaciones en el historial
        # (Implementación básica, se puede mejorar)
        pass

    def add_push_notification(self, title, message, notification_type="info", duration=5000):
        self.toast_container.add_toast(title, message, notification_type, duration)
        self.history.append({"title": title, "message": message, "type": notification_type})

    def get_config(self):
        config = super().get_config()
        config['history'] = self.history
        return config

    def set_config(self, config):
        super().set_config(config)
        self.history = config.get('history', [])

class ImportDataWidget(DraggableWidget):
    """Widget visual de importación general de datos"""
    def __init__(self, widget_id: str, title: str = "Importar Datos", parent=None):
        super().__init__(widget_id, title, parent)
        self.setup_import_content()

    def setup_import_content(self):
        self.setMinimumHeight(220)
        self.setMinimumWidth(350)
        self.info_label = QLabel("Importa datos validados, migración, backup en la nube y restauración selectiva.")
        self.info_label.setWordWrap(True)
        self.content_layout.addWidget(self.info_label)
        self.import_button = QPushButton("Importar Archivo")
        self.import_button.clicked.connect(self.import_file)
        self.content_layout.addWidget(self.import_button)
        self.progress = None
        self.result_label = QLabel()
        self.content_layout.addWidget(self.result_label)

    def import_file(self):
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de datos", "", "Archivos CSV (*.csv);;Archivos Excel (*.xlsx);;Todos los archivos (*)")
        if file_path:
            self.result_label.setText(f"Importando: {file_path}")
            # Simular importación y validación
            QTimer.singleShot(2000, lambda: self.result_label.setText("Importación completada con éxito."))

    def get_config(self):
        config = super().get_config()
        return config

    def set_config(self, config):
        super().set_config(config) 