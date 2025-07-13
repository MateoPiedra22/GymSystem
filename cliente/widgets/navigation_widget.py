"""
Widget de navegación moderna para el Sistema de Gimnasio v6
Incluye menú lateral, breadcrumbs, búsqueda global y atajos de teclado
"""
import logging
from typing import Dict, List, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QFrame, QScrollArea, QSizePolicy, QSpacerItem,
    QMenu, QAction, QToolButton, QButtonGroup, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont, QKeySequence, QShortcut

logger = logging.getLogger(__name__)

class NavigationItem:
    """Elemento de navegación individual"""
    
    def __init__(self, id: str, title: str, icon: str = "", parent_id: str = None):
        self.id = id
        self.title = title
        self.icon = icon
        self.parent_id = parent_id
        self.children: List[NavigationItem] = []
        self.callback: Optional[Callable] = None
        self.shortcut: Optional[str] = None
        self.badge: Optional[str] = None
        self.enabled = True
        self.visible = True

class BreadcrumbWidget(QWidget):
    """Widget de breadcrumbs para navegación"""
    
    breadcrumb_clicked = pyqtSignal(str)  # Emite el ID del breadcrumb clickeado
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.breadcrumbs: List[Dict] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz del widget"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)
        
        # Contenedor para breadcrumbs
        self.breadcrumb_container = QHBoxLayout()
        self.breadcrumb_container.setSpacing(8)
        
        layout.addLayout(self.breadcrumb_container)
        layout.addStretch()
    
    def set_breadcrumbs(self, breadcrumbs: List[Dict]):
        """Establece los breadcrumbs a mostrar"""
        self.breadcrumbs = breadcrumbs
        self.update_display()
    
    def update_display(self):
        """Actualiza la visualización de breadcrumbs"""
        # Limpiar breadcrumbs existentes
        while self.breadcrumb_container.count():
            child = self.breadcrumb_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Agregar breadcrumbs
        for i, breadcrumb in enumerate(self.breadcrumbs):
            # Separador
            if i > 0:
                separator = QLabel(">")
                separator.setStyleSheet("color: var(--text-muted); font-size: 12px;")
                self.breadcrumb_container.addWidget(separator)
            
            # Breadcrumb
            breadcrumb_btn = QPushButton(breadcrumb['title'])
            breadcrumb_btn.setFlat(True)
            breadcrumb_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: var(--text-secondary);
                    font-size: 12px;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: var(--state-hover);
                    color: var(--text-primary);
                }
            """)
            
            # Conectar señal
            breadcrumb_btn.clicked.connect(
                lambda checked, bid=breadcrumb['id']: self.breadcrumb_clicked.emit(bid)
            )
            
            self.breadcrumb_container.addWidget(breadcrumb_btn)
    
    def add_breadcrumb(self, id: str, title: str):
        """Agrega un breadcrumb"""
        self.breadcrumbs.append({'id': id, 'title': title})
        self.update_display()
    
    def clear_breadcrumbs(self):
        """Limpia todos los breadcrumbs"""
        self.breadcrumbs.clear()
        self.update_display()

class SearchWidget(QWidget):
    """Widget de búsqueda global"""
    
    search_changed = pyqtSignal(str)  # Emite el texto de búsqueda
    search_submitted = pyqtSignal(str)  # Emite cuando se presiona Enter
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_shortcuts()
    
    def setup_ui(self):
        """Configura la interfaz del widget"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Campo de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar en toda la aplicación...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 14px;
                min-width: 300px;
            }
            QLineEdit:focus {
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)
        
        # Conectar señales
        self.search_input.textChanged.connect(self.search_changed.emit)
        self.search_input.returnPressed.connect(
            lambda: self.search_submitted.emit(self.search_input.text())
        )
        
        layout.addWidget(self.search_input)
        
        # Botón de búsqueda
        self.search_button = QPushButton()
        self.search_button.setIcon(QIcon(":/icons/search.svg"))
        self.search_button.setStyleSheet("""
            QPushButton {
                background: var(--primary-color);
                border: none;
                border-radius: 20px;
                padding: 8px;
                min-width: 36px;
                min-height: 36px;
            }
            QPushButton:hover {
                background: var(--primary-hover);
            }
        """)
        self.search_button.clicked.connect(
            lambda: self.search_submitted.emit(self.search_input.text())
        )
        
        layout.addWidget(self.search_button)
    
    def setup_shortcuts(self):
        """Configura atajos de teclado"""
        # Ctrl+F para enfocar búsqueda
        shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut.activated.connect(self.focus_search)
        
        # Escape para limpiar búsqueda
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self.clear_search)
    
    def focus_search(self):
        """Enfoca el campo de búsqueda"""
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    def clear_search(self):
        """Limpia el campo de búsqueda"""
        self.search_input.clear()
        self.search_input.clearFocus()
    
    def set_search_text(self, text: str):
        """Establece el texto de búsqueda"""
        self.search_input.setText(text)

class SidebarWidget(QWidget):
    """Widget de menú lateral moderno"""
    
    item_clicked = pyqtSignal(str)  # Emite el ID del elemento clickeado
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.navigation_items: Dict[str, NavigationItem] = {}
        self.button_group = QButtonGroup()
        self.current_item_id: Optional[str] = None
        self.setup_ui()
        self.setup_default_items()
    
    def setup_ui(self):
        """Configura la interfaz del widget"""
        self.setObjectName("sidebar")
        self.setFixedWidth(250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Logo/Título
        self.logo_label = QLabel("🏋️ GymSystem")
        self.logo_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: var(--text-primary);
                padding: 16px 0;
                text-align: center;
            }
        """)
        layout.addWidget(self.logo_label)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: var(--border-color);")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Área de navegación con scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        self.nav_container = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(4)
        
        scroll_area.setWidget(self.nav_container)
        layout.addWidget(scroll_area)
        
        # Espaciador
        layout.addStretch()
        
        # Información de usuario
        self.user_info = QLabel("Usuario: Admin")
        self.user_info.setStyleSheet("""
            QLabel {
                color: var(--text-secondary);
                font-size: 12px;
                padding: 8px;
                background: var(--bg-secondary);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.user_info)
    
    def setup_default_items(self):
        """Configura elementos de navegación por defecto"""
        self.add_navigation_item("dashboard", "Dashboard", ":/icons/dashboard.svg")
        self.add_navigation_item("usuarios", "Usuarios", ":/icons/users.svg")
        self.add_navigation_item("clases", "Clases", ":/icons/calendar.svg")
        self.add_navigation_item("pagos", "Pagos", ":/icons/payment.svg")
        self.add_navigation_item("asistencias", "Asistencias", ":/icons/attendance.svg")
        self.add_navigation_item("reportes", "Reportes", ":/icons/chart.svg")
        self.add_navigation_item("configuracion", "Configuración", ":/icons/settings.svg")
        
        # Subelementos
        self.add_navigation_item("usuarios_lista", "Lista de Usuarios", "", "usuarios")
        self.add_navigation_item("usuarios_nuevo", "Nuevo Usuario", "", "usuarios")
        self.add_navigation_item("reportes_kpis", "KPIs", "", "reportes")
        self.add_navigation_item("reportes_graficos", "Gráficos", "", "reportes")
    
    def add_navigation_item(self, id: str, title: str, icon: str = "", 
                           parent_id: str = None, callback: Callable = None,
                           shortcut: str = None, badge: str = None):
        """Agrega un elemento de navegación"""
        item = NavigationItem(id, title, icon, parent_id)
        item.callback = callback
        item.shortcut = shortcut
        item.badge = badge
        
        self.navigation_items[id] = item
        
        # Agregar a padre si existe
        if parent_id and parent_id in self.navigation_items:
            self.navigation_items[parent_id].children.append(item)
        
        self.update_navigation_display()
    
    def update_navigation_display(self):
        """Actualiza la visualización de navegación"""
        # Limpiar layout existente
        while self.nav_layout.count():
            child = self.nav_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Agregar elementos principales
        for item in self.navigation_items.values():
            if not item.parent_id:  # Solo elementos principales
                self.add_navigation_button(item)
    
    def add_navigation_button(self, item: NavigationItem):
        """Agrega un botón de navegación"""
        button = QPushButton()
        button.setCheckable(True)
        button.setObjectName(f"nav_{item.id}")
        
        # Configurar texto e icono
        if item.icon:
            button.setIcon(QIcon(item.icon))
        button.setText(f" {item.title}")
        
        # Configurar estilo
        button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                color: var(--text-secondary);
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background: var(--state-hover);
                color: var(--text-primary);
            }
            QPushButton:checked {
                background: var(--primary-color);
                color: var(--text-inverse);
            }
        """)
        
        # Agregar badge si existe
        if item.badge:
            badge_label = QLabel(item.badge)
            badge_label.setStyleSheet("""
                QLabel {
                    background: var(--error-color);
                    color: white;
                    border-radius: 10px;
                    padding: 2px 6px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            # TODO: Agregar badge al layout del botón
        
        # Conectar señal
        button.clicked.connect(lambda: self.on_item_clicked(item.id))
        
        # Agregar al grupo de botones
        self.button_group.addButton(button)
        
        # Agregar al layout
        self.nav_layout.addWidget(button)
        
        # Agregar subelementos si existen
        if item.children:
            for child in item.children:
                self.add_subnavigation_button(child, level=1)
    
    def add_subnavigation_button(self, item: NavigationItem, level: int = 1):
        """Agrega un botón de subnavegación"""
        button = QPushButton()
        button.setCheckable(True)
        button.setObjectName(f"nav_{item.id}")
        
        # Indentación para subelementos
        indent = "  " * level
        button.setText(f"{indent}{item.title}")
        
        # Estilo para subelementos
        button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                text-align: left;
                color: var(--text-muted);
                font-weight: 400;
                font-size: 13px;
                margin-left: {level * 16}px;
            }}
            QPushButton:hover {{
                background: var(--state-hover);
                color: var(--text-primary);
            }}
            QPushButton:checked {{
                background: var(--primary-light);
                color: var(--primary-color);
            }}
        """)
        
        # Conectar señal
        button.clicked.connect(lambda: self.on_item_clicked(item.id))
        
        # Agregar al grupo de botones
        self.button_group.addButton(button)
        
        # Agregar al layout
        self.nav_layout.addWidget(button)
    
    def on_item_clicked(self, item_id: str):
        """Maneja el click en un elemento de navegación"""
        self.current_item_id = item_id
        self.item_clicked.emit(item_id)
        
        # Ejecutar callback si existe
        if item_id in self.navigation_items:
            item = self.navigation_items[item_id]
            if item.callback:
                item.callback()
    
    def set_current_item(self, item_id: str):
        """Establece el elemento actual"""
        self.current_item_id = item_id
        
        # Actualizar botón seleccionado
        for button in self.button_group.buttons():
            if button.objectName() == f"nav_{item_id}":
                button.setChecked(True)
                break
    
    def update_badge(self, item_id: str, badge: str):
        """Actualiza el badge de un elemento"""
        if item_id in self.navigation_items:
            self.navigation_items[item_id].badge = badge
            self.update_navigation_display()

class NavigationWidget(QWidget):
    """Widget principal de navegación que combina todos los componentes"""
    
    navigation_changed = pyqtSignal(str)  # Emite cuando cambia la navegación
    search_performed = pyqtSignal(str)    # Emite cuando se realiza una búsqueda
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.breadcrumb_history: List[Dict] = []
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Configura la interfaz del widget"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = SidebarWidget()
        layout.addWidget(self.sidebar)
        
        # Contenedor principal
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header con breadcrumbs y búsqueda
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_layout.setSpacing(16)
        
        # Breadcrumbs
        self.breadcrumbs = BreadcrumbWidget()
        header_layout.addWidget(self.breadcrumbs)
        
        # Espaciador
        header_layout.addStretch()
        
        # Búsqueda
        self.search = SearchWidget()
        header_layout.addWidget(self.search)
        
        main_layout.addWidget(header)
        
        # Área de contenido
        self.content_area = QStackedWidget()
        self.content_area.setObjectName("contentArea")
        main_layout.addWidget(self.content_area)
        
        layout.addWidget(main_container)
    
    def setup_connections(self):
        """Configura las conexiones entre componentes"""
        # Sidebar -> Navegación
        self.sidebar.item_clicked.connect(self.on_navigation_changed)
        
        # Breadcrumbs -> Navegación
        self.breadcrumbs.breadcrumb_clicked.connect(self.on_breadcrumb_clicked)
        
        # Búsqueda
        self.search.search_submitted.connect(self.on_search_performed)
    
    def on_navigation_changed(self, item_id: str):
        """Maneja cambios en la navegación"""
        # Actualizar breadcrumbs
        self.update_breadcrumbs(item_id)
        
        # Emitir señal
        self.navigation_changed.emit(item_id)
    
    def on_breadcrumb_clicked(self, breadcrumb_id: str):
        """Maneja clicks en breadcrumbs"""
        # Navegar al breadcrumb
        self.sidebar.set_current_item(breadcrumb_id)
        self.navigation_changed.emit(breadcrumb_id)
    
    def on_search_performed(self, search_text: str):
        """Maneja búsquedas realizadas"""
        self.search_performed.emit(search_text)
    
    def update_breadcrumbs(self, item_id: str):
        """Actualiza los breadcrumbs basado en el elemento actual"""
        breadcrumbs = []
        
        # Construir breadcrumbs desde el elemento actual hacia arriba
        current_item = self.sidebar.navigation_items.get(item_id)
        while current_item:
            breadcrumbs.insert(0, {
                'id': current_item.id,
                'title': current_item.title
            })
            
            if current_item.parent_id:
                current_item = self.sidebar.navigation_items.get(current_item.parent_id)
            else:
                break
        
        # Agregar breadcrumb raíz
        if breadcrumbs:
            breadcrumbs.insert(0, {
                'id': 'home',
                'title': 'Inicio'
            })
        
        self.breadcrumbs.set_breadcrumbs(breadcrumbs)
    
    def add_content_page(self, page_id: str, widget: QWidget):
        """Agrega una página de contenido"""
        self.content_area.addWidget(widget)
        widget.setObjectName(f"page_{page_id}")
    
    def set_current_page(self, page_id: str):
        """Establece la página actual"""
        for i in range(self.content_area.count()):
            widget = self.content_area.widget(i)
            if widget.objectName() == f"page_{page_id}":
                self.content_area.setCurrentIndex(i)
                break
    
    def add_navigation_item(self, id: str, title: str, icon: str = "", 
                           parent_id: str = None, callback: Callable = None,
                           shortcut: str = None, badge: str = None):
        """Agrega un elemento de navegación"""
        self.sidebar.add_navigation_item(id, title, icon, parent_id, callback, shortcut, badge)
    
    def set_current_navigation(self, item_id: str):
        """Establece la navegación actual"""
        self.sidebar.set_current_item(item_id)
        self.update_breadcrumbs(item_id)
    
    def update_badge(self, item_id: str, badge: str):
        """Actualiza el badge de un elemento de navegación"""
        self.sidebar.update_badge(item_id, badge)
    
    def focus_search(self):
        """Enfoca el campo de búsqueda"""
        self.search.focus_search()
    
    def clear_search(self):
        """Limpia el campo de búsqueda"""
        self.search.clear_search() 