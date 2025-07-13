# /cliente/widgets/rutinas_tab_widget.py
"""
Widget mejorado para la gestión de rutinas de ejercicios
Incluye planificación, asignación a usuarios y seguimiento
"""

from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QMessageBox, QHeaderView, QAbstractItemView, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox, QCheckBox,
    QTabWidget, QSplitter, QTextEdit, QGroupBox, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon, QColor

from ..api_client import ApiClient
from .multimedia_widget import MultimediaWidget

class RutinasLoadWorker(QThread):
    """Worker para cargar rutinas en background"""
    
    rutinas_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_client: ApiClient, usuario_id: Optional[int] = None):
        super().__init__()
        self.api_client = api_client
        self.usuario_id = usuario_id
        
    def run(self):
        """Carga la lista de rutinas"""
        try:
            params = {"usuario_id": self.usuario_id} if self.usuario_id else {}
            rutinas = self.api_client.get_rutinas(**params)
            self.rutinas_loaded.emit(rutinas)
        except Exception as e:
            self.error_occurred.emit(str(e))

class EjerciciosLoadWorker(QThread):
    """Worker para cargar ejercicios en background"""
    
    ejercicios_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_client: ApiClient, categoria: Optional[str] = None):
        super().__init__()
        self.api_client = api_client
        self.categoria = categoria
        
    def run(self):
        """Carga la lista de ejercicios"""
        try:
            params = {"categoria": self.categoria} if self.categoria else {}
            ejercicios = self.api_client.get_ejercicios(**params)
            self.ejercicios_loaded.emit(ejercicios)
        except Exception as e:
            self.error_occurred.emit(str(e))

class NuevaRutinaDialog(QDialog):
    """Dialog para crear o editar una rutina"""
    
    def __init__(self, parent=None, api_client: ApiClient = None, rutina: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.api_client = api_client
        self.rutina = rutina
        self.setWindowTitle("Nueva Rutina" if not rutina else "Editar Rutina")
        self.resize(500, 400)
        self.setupUI()
        
    def setupUI(self):
        """Configura la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Formulario principal
        form = QFormLayout()
        
        # Nombre de la rutina
        self.input_nombre = QLineEdit()
        if self.rutina:
            self.input_nombre.setText(self.rutina.get("nombre_rutina", ""))
        form.addRow("Nombre:", self.input_nombre)
        
        # Usuario asignado
        self.combo_usuario = QComboBox()
        # Cargar usuarios (simplificado - en una implementación real cargaríamos de la API)
        self.combo_usuario.addItem("Seleccione usuario...", None)
        self.combo_usuario.addItem("Todos los usuarios", 0)
        
        # Si hay usuarios cargados, agregarlos al combo
        try:
            usuarios = self.api_client.get_usuarios()
            for usuario in usuarios:
                self.combo_usuario.addItem(
                    f"{usuario.get('nombre')} {usuario.get('apellido')}",
                    usuario.get('id')
                )
                
            # Seleccionar usuario si estamos editando
            if self.rutina and self.rutina.get("usuario_id"):
                for i in range(self.combo_usuario.count()):
                    if self.combo_usuario.itemData(i) == self.rutina.get("usuario_id"):
                        self.combo_usuario.setCurrentIndex(i)
                        break
        except:
            # En caso de error, dejar solo las opciones por defecto
            pass
            
        form.addRow("Usuario:", self.combo_usuario)
        
        # Descripción
        self.input_descripcion = QTextEdit()
        self.input_descripcion.setMaximumHeight(100)
        if self.rutina:
            self.input_descripcion.setText(self.rutina.get("descripcion", ""))
        form.addRow("Descripción:", self.input_descripcion)
        
        # Objetivo
        self.combo_objetivo = QComboBox()
        self.combo_objetivo.addItems([
            "Pérdida de peso", "Tonificación", "Hipertrofia", "Fuerza", 
            "Resistencia", "Flexibilidad", "Rehabilitación", "General"
        ])
        if self.rutina:
            self.combo_objetivo.setCurrentText(self.rutina.get("objetivo", "General"))
        form.addRow("Objetivo:", self.combo_objetivo)
        
        # Nivel
        self.combo_nivel = QComboBox()
        self.combo_nivel.addItems(["Principiante", "Intermedio", "Avanzado"])
        if self.rutina:
            self.combo_nivel.setCurrentText(self.rutina.get("nivel", "Principiante"))
        form.addRow("Nivel:", self.combo_nivel)
        
        # Duración (semanas)
        self.input_duracion = QSpinBox()
        self.input_duracion.setMinimum(1)
        self.input_duracion.setMaximum(52)  # Un año máximo
        if self.rutina:
            self.input_duracion.setValue(self.rutina.get("duracion_semanas", 4))
        else:
            self.input_duracion.setValue(4)
        form.addRow("Duración (semanas):", self.input_duracion)
        
        # Días por semana
        self.input_dias = QSpinBox()
        self.input_dias.setMinimum(1)
        self.input_dias.setMaximum(7)
        if self.rutina:
            self.input_dias.setValue(self.rutina.get("dias_semana", 3))
        else:
            self.input_dias.setValue(3)
        form.addRow("Días por semana:", self.input_dias)
        
        # Activa
        self.input_activa = QCheckBox()
        if self.rutina:
            self.input_activa.setChecked(self.rutina.get("activa", True))
        else:
            self.input_activa.setChecked(True)
        form.addRow("Activa:", self.input_activa)
        
        layout.addLayout(form)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_data(self) -> Dict[str, Any]:
        """Obtiene los datos del formulario"""
        usuario_id = self.combo_usuario.currentData()
        
        # Si se selecciona "Todos los usuarios", usamos None como usuario_id
        if usuario_id == 0:
            usuario_id = None
            
        return {
            "nombre_rutina": self.input_nombre.text(),
            "usuario_id": usuario_id,
            "descripcion": self.input_descripcion.toPlainText(),
            "objetivo": self.combo_objetivo.currentText(),
            "nivel": self.combo_nivel.currentText(),
            "duracion_semanas": self.input_duracion.value(),
            "dias_semana": self.input_dias.value(),
            "activa": self.input_activa.isChecked()
        }

class AgregarEjercicioDialog(QDialog):
    """Dialog para agregar un ejercicio a una rutina"""
    
    def __init__(self, parent=None, api_client: ApiClient = None, rutina_id: int = None, 
                 ejercicio_rutina: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.api_client = api_client
        self.rutina_id = rutina_id
        self.ejercicio_rutina = ejercicio_rutina
        self.ejercicios = []
        self.setWindowTitle("Agregar Ejercicio" if not ejercicio_rutina else "Editar Ejercicio")
        self.resize(600, 500)
        self.setupUI()
        self.cargar_ejercicios()
        
    def setupUI(self):
        """Configura la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Formulario principal
        form = QFormLayout()
        
        # Día de la semana
        self.combo_dia = QComboBox()
        self.combo_dia.addItems(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        if self.ejercicio_rutina:
            # Convertir de número (1-7) a nombre del día
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            dia_num = self.ejercicio_rutina.get("dia_semana", 1)
            if 1 <= dia_num <= 7:
                self.combo_dia.setCurrentText(dias[dia_num - 1])
        form.addRow("Día:", self.combo_dia)
        
        # Categoría de ejercicio
        self.combo_categoria = QComboBox()
        self.combo_categoria.addItems([
            "Todas", "Pecho", "Espalda", "Hombros", "Brazos", "Piernas", 
            "Abdominales", "Cardio", "Estiramiento", "Otros"
        ])
        self.combo_categoria.currentTextChanged.connect(self.on_categoria_changed)
        form.addRow("Categoría:", self.combo_categoria)
        
        # Ejercicio
        self.combo_ejercicio = QComboBox()
        self.combo_ejercicio.setMinimumWidth(300)
        form.addRow("Ejercicio:", self.combo_ejercicio)
        
        # Series
        self.input_series = QSpinBox()
        self.input_series.setMinimum(1)
        self.input_series.setMaximum(20)
        if self.ejercicio_rutina:
            self.input_series.setValue(self.ejercicio_rutina.get("series", 3))
        else:
            self.input_series.setValue(3)
        form.addRow("Series:", self.input_series)
        
        # Repeticiones
        self.input_repeticiones = QLineEdit()
        if self.ejercicio_rutina:
            self.input_repeticiones.setText(self.ejercicio_rutina.get("repeticiones", "10-12"))
        else:
            self.input_repeticiones.setText("10-12")
        form.addRow("Repeticiones:", self.input_repeticiones)
        
        # Descanso (segundos)
        self.input_descanso = QSpinBox()
        self.input_descanso.setMinimum(10)
        self.input_descanso.setMaximum(300)
        self.input_descanso.setSingleStep(5)
        if self.ejercicio_rutina:
            self.input_descanso.setValue(self.ejercicio_rutina.get("descanso", 60))
        else:
            self.input_descanso.setValue(60)
        form.addRow("Descanso (seg):", self.input_descanso)
        
        # Peso (kg) - opcional
        self.input_peso = QLineEdit()
        if self.ejercicio_rutina:
            self.input_peso.setText(str(self.ejercicio_rutina.get("peso", "")))
        form.addRow("Peso (kg):", self.input_peso)
        
        # Intensidad (1-10)
        self.input_intensidad = QSpinBox()
        self.input_intensidad.setMinimum(1)
        self.input_intensidad.setMaximum(10)
        if self.ejercicio_rutina:
            self.input_intensidad.setValue(self.ejercicio_rutina.get("intensidad", 5))
        else:
            self.input_intensidad.setValue(5)
        form.addRow("Intensidad (1-10):", self.input_intensidad)
        
        # Orden
        self.input_orden = QSpinBox()
        self.input_orden.setMinimum(1)
        self.input_orden.setMaximum(50)
        if self.ejercicio_rutina:
            self.input_orden.setValue(self.ejercicio_rutina.get("orden", 1))
        else:
            self.input_orden.setValue(1)
        form.addRow("Orden:", self.input_orden)
        
        # Notas
        self.input_notas = QTextEdit()
        self.input_notas.setMaximumHeight(80)
        if self.ejercicio_rutina:
            self.input_notas.setText(self.ejercicio_rutina.get("notas", ""))
        form.addRow("Notas:", self.input_notas)
        
        layout.addLayout(form)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def cargar_ejercicios(self):
        """Carga los ejercicios desde la API"""
        categoria = None
        if self.combo_categoria.currentText() != "Todas":
            categoria = self.combo_categoria.currentText()
            
        try:
            worker = EjerciciosLoadWorker(self.api_client, categoria)
            worker.ejercicios_loaded.connect(self.on_ejercicios_loaded)
            worker.error_occurred.connect(self.on_error)
            worker.start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar ejercicios: {str(e)}")
    
    def on_ejercicios_loaded(self, ejercicios: List[Dict[str, Any]]):
        """Procesa los ejercicios cargados"""
        self.ejercicios = ejercicios
        
        # Guardar selección actual
        ejercicio_id_actual = self.combo_ejercicio.currentData()
        
        # Limpiar combo
        self.combo_ejercicio.clear()
        
        # Agregar ejercicios al combo
        for ejercicio in ejercicios:
            self.combo_ejercicio.addItem(
                ejercicio.get("nombre", ""), 
                ejercicio.get("id")
            )
        
        # Si estamos editando, seleccionar el ejercicio actual
        if self.ejercicio_rutina:
            for i in range(self.combo_ejercicio.count()):
                if self.combo_ejercicio.itemData(i) == self.ejercicio_rutina.get("ejercicio_id"):
                    self.combo_ejercicio.setCurrentIndex(i)
                    break
    
    def on_categoria_changed(self, categoria: str):
        """Maneja el cambio de categoría de ejercicio"""
        self.cargar_ejercicios()
    
    def on_error(self, mensaje: str):
        """Maneja errores en la carga de ejercicios"""
        QMessageBox.critical(self, "Error", mensaje)
    
    def get_data(self) -> Dict[str, Any]:
        """Obtiene los datos del formulario"""
        # Convertir nombre del día a número (1-7)
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_num = dias.index(self.combo_dia.currentText()) + 1
        
        # Convertir peso a float o None
        peso_str = self.input_peso.text().strip()
        peso = None
        if peso_str:
            try:
                peso = float(peso_str)
            except:
                peso = None
        
        return {
            "rutina_id": self.rutina_id,
            "ejercicio_id": self.combo_ejercicio.currentData(),
            "dia_semana": dia_num,
            "series": self.input_series.value(),
            "repeticiones": self.input_repeticiones.text(),
            "descanso": self.input_descanso.value(),
            "peso": peso,
            "intensidad": self.input_intensidad.value(),
            "orden": self.input_orden.value(),
            "notas": self.input_notas.toPlainText()
        }

class RutinasTabWidget(QWidget):
    """Widget principal para gestión de rutinas"""
    
    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.rutinas = []
        self.ejercicios_rutina = []
        self.rutina_seleccionada = None
        self.load_worker = None
        
        self.setupUI()
        self.cargar_rutinas()
        
    def setupUI(self):
        """Configura la interfaz"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Título
        titulo = QLabel("💪 Gestión de Rutinas")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(titulo)
        
        # Splitter principal
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo - Lista de rutinas
        self.panel_rutinas = QWidget()
        self.setup_panel_rutinas()
        self.splitter.addWidget(self.panel_rutinas)
        
        # Panel derecho - Detalle de rutina con tabs
        self.panel_detalle = QTabWidget()
        self.setup_panel_detalle()
        self.splitter.addWidget(self.panel_detalle)
        
        # Establecer tamaños iniciales
        self.splitter.setSizes([300, 700])
        
        layout.addWidget(self.splitter)
    
    def setup_panel_rutinas(self):
        """Configura el panel de lista de rutinas"""
        layout = QVBoxLayout(self.panel_rutinas)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de herramientas
        toolbar_layout = QHBoxLayout()
        
        # Búsqueda
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("🔍 Buscar rutina...")
        self.input_busqueda.textChanged.connect(self.filtrar_rutinas)
        toolbar_layout.addWidget(self.input_busqueda)
        
        # Filtro por usuario
        self.combo_usuario_filtro = QComboBox()
        self.combo_usuario_filtro.addItem("Todos los usuarios", None)
        
        # Intentar cargar usuarios (simplificado)
        try:
            usuarios = self.api_client.get_usuarios()
            for usuario in usuarios:
                self.combo_usuario_filtro.addItem(
                    f"{usuario.get('nombre')} {usuario.get('apellido')}",
                    usuario.get('id')
                )
        except:
            pass
            
        self.combo_usuario_filtro.currentIndexChanged.connect(self.on_filtro_usuario_changed)
        toolbar_layout.addWidget(self.combo_usuario_filtro)
        
        # Botones
        btn_nueva = QPushButton("➕ Nueva Rutina")
        btn_nueva.clicked.connect(self.nueva_rutina)
        toolbar_layout.addWidget(btn_nueva)
        
        btn_actualizar = QPushButton("🔄 Actualizar")
        btn_actualizar.clicked.connect(self.cargar_rutinas)
        toolbar_layout.addWidget(btn_actualizar)
        
        layout.addLayout(toolbar_layout)
        
        # Tabla de rutinas
        self.tabla_rutinas = QTableWidget()
        self.tabla_rutinas.setColumnCount(5)
        self.tabla_rutinas.setHorizontalHeaderLabels(["ID", "Nombre", "Usuario", "Nivel", "Acciones"])
        self.tabla_rutinas.verticalHeader().setVisible(False)
        self.tabla_rutinas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_rutinas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_rutinas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_rutinas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_rutinas.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_rutinas.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_rutinas.itemSelectionChanged.connect(self.on_rutina_selected)
        layout.addWidget(self.tabla_rutinas)
    
    def setup_panel_detalle(self):
        """Configura el panel de detalle de rutina con tabs"""
        # Tab 1: Información de rutina
        tab_info = QWidget()
        self.setup_tab_informacion(tab_info)
        self.panel_detalle.addTab(tab_info, "ℹ Información")
        
        # Tab 2: Multimedia
        self.tab_multimedia = MultimediaWidget()
        self.panel_detalle.addTab(self.tab_multimedia, "🎬 Multimedia")
        
    def setup_tab_informacion(self, tab_widget):
        """Configura el tab de información de rutina"""
        layout = QVBoxLayout(tab_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Información de rutina
        self.info_rutina = QGroupBox("Información de Rutina")
        info_layout = QFormLayout(self.info_rutina)
        
        self.lbl_nombre = QLabel("-")
        self.lbl_nombre.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addRow("Nombre:", self.lbl_nombre)
        
        self.lbl_usuario = QLabel("-")
        info_layout.addRow("Usuario:", self.lbl_usuario)
        
        self.lbl_objetivo = QLabel("-")
        info_layout.addRow("Objetivo:", self.lbl_objetivo)
        
        self.lbl_nivel = QLabel("-")
        info_layout.addRow("Nivel:", self.lbl_nivel)
        
        self.lbl_duracion = QLabel("-")
        info_layout.addRow("Duración:", self.lbl_duracion)
        
        self.lbl_descripcion = QLabel("-")
        self.lbl_descripcion.setWordWrap(True)
        info_layout.addRow("Descripción:", self.lbl_descripcion)
        
        layout.addWidget(self.info_rutina)
        
        # Ejercicios de la rutina
        self.grupo_ejercicios = QGroupBox("Ejercicios")
        ejercicios_layout = QVBoxLayout(self.grupo_ejercicios)
        
        # Barra de herramientas
        toolbar_ejercicios = QHBoxLayout()
        
        # Filtro por día
        self.combo_dia_filtro = QComboBox()
        self.combo_dia_filtro.addItem("Todos los días")
        self.combo_dia_filtro.addItems(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        self.combo_dia_filtro.currentTextChanged.connect(self.filtrar_ejercicios)
        toolbar_ejercicios.addWidget(self.combo_dia_filtro)
        
        # Botones
        self.btn_agregar_ejercicio = QPushButton("➕ Agregar Ejercicio")
        self.btn_agregar_ejercicio.clicked.connect(self.agregar_ejercicio)
        self.btn_agregar_ejercicio.setEnabled(False)
        toolbar_ejercicios.addWidget(self.btn_agregar_ejercicio)
        
        ejercicios_layout.addLayout(toolbar_ejercicios)
        
        # Tabla de ejercicios
        self.tabla_ejercicios = QTableWidget()
        self.tabla_ejercicios.setColumnCount(7)
        self.tabla_ejercicios.setHorizontalHeaderLabels(["ID", "Día", "Ejercicio", "Series", "Repeticiones", "Orden", "Acciones"])
        self.tabla_ejercicios.verticalHeader().setVisible(False)
        self.tabla_ejercicios.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_ejercicios.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_ejercicios.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_ejercicios.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla_ejercicios.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_ejercicios.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        ejercicios_layout.addWidget(self.tabla_ejercicios)
        
        layout.addWidget(self.grupo_ejercicios)
        
        # Botones de acción para rutina
        botones_layout = QHBoxLayout()
        
        self.btn_imprimir = QPushButton("🖨️ Imprimir Rutina")
        self.btn_imprimir.clicked.connect(self.imprimir_rutina)
        self.btn_imprimir.setEnabled(False)
        botones_layout.addWidget(self.btn_imprimir)
        
        self.btn_enviar = QPushButton("📧 Enviar por Email")
        self.btn_enviar.clicked.connect(self.enviar_rutina)
        self.btn_enviar.setEnabled(False)
        botones_layout.addWidget(self.btn_enviar)
        
        self.btn_editar = QPushButton("✏️ Editar Rutina")
        self.btn_editar.clicked.connect(self.editar_rutina)
        self.btn_editar.setEnabled(False)
        botones_layout.addWidget(self.btn_editar)
        
        self.btn_eliminar = QPushButton("❌ Eliminar Rutina")
        self.btn_eliminar.clicked.connect(self.eliminar_rutina)
        self.btn_eliminar.setEnabled(False)
        botones_layout.addWidget(self.btn_eliminar)
        
        layout.addLayout(botones_layout)
    
    def cargar_rutinas(self):
        """Carga la lista de rutinas desde el API"""
        if self.load_worker and self.load_worker.isRunning():
            return
            
        usuario_id = self.combo_usuario_filtro.currentData()
            
        self.load_worker = RutinasLoadWorker(self.api_client, usuario_id)
        self.load_worker.rutinas_loaded.connect(self.on_rutinas_loaded)
        self.load_worker.error_occurred.connect(self.on_error)
        self.load_worker.start()
    
    def on_rutinas_loaded(self, rutinas: List[Dict[str, Any]]):
        """Procesa las rutinas cargadas"""
        self.rutinas = rutinas
        self.actualizar_tabla_rutinas()
    
    def actualizar_tabla_rutinas(self):
        """Actualiza la tabla de rutinas con los datos cargados"""
        self.tabla_rutinas.setRowCount(0)
        
        # Aplicar filtros
        busqueda = self.input_busqueda.text().lower()
        
        rutinas_filtradas = []
        for rutina in self.rutinas:
            # Filtrar por búsqueda
            if busqueda and not (
                busqueda in rutina.get("nombre_rutina", "").lower() or 
                busqueda in rutina.get("descripcion", "").lower()
            ):
                continue
                
            rutinas_filtradas.append(rutina)
        
        # Llenar tabla
        self.tabla_rutinas.setRowCount(len(rutinas_filtradas))
        for i, rutina in enumerate(rutinas_filtradas):
            # ID
            item_id = QTableWidgetItem(str(rutina.get("id")))
            self.tabla_rutinas.setItem(i, 0, item_id)
            
            # Nombre
            item_nombre = QTableWidgetItem(rutina.get("nombre_rutina", ""))
            if not rutina.get("activa", True):
                item_nombre.setForeground(QColor(150, 150, 150))
            self.tabla_rutinas.setItem(i, 1, item_nombre)
            
            # Usuario
            nombre_usuario = rutina.get("usuario_nombre", "General")
            item_usuario = QTableWidgetItem(nombre_usuario)
            self.tabla_rutinas.setItem(i, 2, item_usuario)
            
            # Nivel
            item_nivel = QTableWidgetItem(rutina.get("nivel", ""))
            self.tabla_rutinas.setItem(i, 3, item_nivel)
            
            # Acciones
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(2)
            
            # Ver detalles
            btn_ver = QPushButton("👁️")
            btn_ver.setMaximumWidth(30)
            btn_ver.clicked.connect(lambda checked, rutina_id=rutina.get("id"): self.ver_rutina(rutina_id))
            btn_layout.addWidget(btn_ver)
            
            # Editar
            btn_editar = QPushButton("✏️")
            btn_editar.setMaximumWidth(30)
            btn_editar.clicked.connect(lambda checked, rutina_id=rutina.get("id"): self.editar_rutina_desde_lista(rutina_id))
            btn_layout.addWidget(btn_editar)
            
            # Eliminar
            btn_eliminar = QPushButton("❌")
            btn_eliminar.setMaximumWidth(30)
            btn_eliminar.clicked.connect(lambda checked, rutina_id=rutina.get("id"): self.eliminar_rutina_desde_lista(rutina_id))
            btn_layout.addWidget(btn_eliminar)
            
            # Contenedor para botones
            widget_container = QWidget()
            widget_container.setLayout(btn_layout)
            self.tabla_rutinas.setCellWidget(i, 4, widget_container)
    
    def on_rutina_selected(self):
        """Manejador para selección de rutina en la tabla"""
        selected_rows = self.tabla_rutinas.selectedItems()
        if not selected_rows:
            self.limpiar_detalle_rutina()
            self.rutina_seleccionada = None
            return
            
        row = selected_rows[0].row()
        rutina_id = int(self.tabla_rutinas.item(row, 0).text())
        
        # Buscar la rutina completa
        for rutina in self.rutinas:
            if rutina.get("id") == rutina_id:
                self.rutina_seleccionada = rutina
                self.mostrar_detalle_rutina(rutina)
                self.cargar_ejercicios_rutina(rutina_id)
                break
    
    def mostrar_detalle_rutina(self, rutina: Dict[str, Any]):
        """Muestra el detalle de una rutina"""
        self.lbl_nombre.setText(rutina.get("nombre_rutina", "-"))
        self.lbl_usuario.setText(rutina.get("usuario_nombre", "General"))
        self.lbl_objetivo.setText(rutina.get("objetivo", "-"))
        self.lbl_nivel.setText(rutina.get("nivel", "-"))
        self.lbl_duracion.setText(f"{rutina.get('duracion_semanas', '-')} semanas, {rutina.get('dias_semana', '-')} días/semana")
        self.lbl_descripcion.setText(rutina.get("descripcion", "-"))
        
        # Configurar multimedia para rutina
        if hasattr(self, 'tab_multimedia'):
            self.tab_multimedia.set_rutina(str(rutina.get("id", "")))
        
        # Habilitar botones
        self.btn_agregar_ejercicio.setEnabled(True)
        self.btn_imprimir.setEnabled(True)
        self.btn_enviar.setEnabled(True)
        self.btn_editar.setEnabled(True)
        self.btn_eliminar.setEnabled(True)
    
    def limpiar_detalle_rutina(self):
        """Limpia el detalle de rutina"""
        self.lbl_nombre.setText("-")
        self.lbl_usuario.setText("-")
        self.lbl_objetivo.setText("-")
        self.lbl_nivel.setText("-")
        self.lbl_duracion.setText("-")
        self.lbl_descripcion.setText("-")
        
        # Limpiar tabla de ejercicios
        self.tabla_ejercicios.setRowCount(0)
        
        # Deshabilitar botones
        self.btn_agregar_ejercicio.setEnabled(False)
        self.btn_imprimir.setEnabled(False)
        self.btn_enviar.setEnabled(False)
        self.btn_editar.setEnabled(False)
        self.btn_eliminar.setEnabled(False)
    
    def cargar_ejercicios_rutina(self, rutina_id: int):
        """Carga los ejercicios de una rutina"""
        try:
            ejercicios = self.api_client.get_ejercicios_rutina(rutina_id)
            self.ejercicios_rutina = ejercicios
            self.actualizar_tabla_ejercicios()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar ejercicios: {str(e)}")
    
    def actualizar_tabla_ejercicios(self):
        """Actualiza la tabla de ejercicios con los datos cargados"""
        self.tabla_ejercicios.setRowCount(0)
        
        # Aplicar filtros
        filtro_dia = self.combo_dia_filtro.currentText()
        
        ejercicios_filtrados = []
        for ejercicio in self.ejercicios_rutina:
            # Filtrar por día
            if filtro_dia != "Todos los días":
                dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                dia_num = ejercicio.get("dia_semana", 1)
                if 1 <= dia_num <= 7:
                    dia_nombre = dias[dia_num - 1]
                    if filtro_dia != dia_nombre:
                        continue
            
            ejercicios_filtrados.append(ejercicio)
        
        # Ordenar por día y orden
        ejercicios_filtrados.sort(key=lambda x: (x.get("dia_semana", 1), x.get("orden", 1)))
        
        # Llenar tabla
        self.tabla_ejercicios.setRowCount(len(ejercicios_filtrados))
        for i, ejercicio in enumerate(ejercicios_filtrados):
            # ID
            item_id = QTableWidgetItem(str(ejercicio.get("id")))
            self.tabla_ejercicios.setItem(i, 0, item_id)
            
            # Día
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            dia_num = ejercicio.get("dia_semana", 1)
            dia_nombre = dias[dia_num - 1] if 1 <= dia_num <= 7 else f"Día {dia_num}"
            item_dia = QTableWidgetItem(dia_nombre)
            self.tabla_ejercicios.setItem(i, 1, item_dia)
            
            # Ejercicio
            item_ejercicio = QTableWidgetItem(ejercicio.get("ejercicio_nombre", ""))
            self.tabla_ejercicios.setItem(i, 2, item_ejercicio)
            
            # Series
            item_series = QTableWidgetItem(str(ejercicio.get("series", "")))
            self.tabla_ejercicios.setItem(i, 3, item_series)
            
            # Repeticiones
            item_repeticiones = QTableWidgetItem(ejercicio.get("repeticiones", ""))
            self.tabla_ejercicios.setItem(i, 4, item_repeticiones)
            
            # Orden
            item_orden = QTableWidgetItem(str(ejercicio.get("orden", "")))
            self.tabla_ejercicios.setItem(i, 5, item_orden)
            
            # Acciones
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(2)
            
            # Editar
            btn_editar = QPushButton("✏️")
            btn_editar.setMaximumWidth(30)
            btn_editar.clicked.connect(lambda checked, ejercicio_id=ejercicio.get("id"): self.editar_ejercicio(ejercicio_id))
            btn_layout.addWidget(btn_editar)
            
            # Eliminar
            btn_eliminar = QPushButton("❌")
            btn_eliminar.setMaximumWidth(30)
            btn_eliminar.clicked.connect(lambda checked, ejercicio_id=ejercicio.get("id"): self.eliminar_ejercicio(ejercicio_id))
            btn_layout.addWidget(btn_eliminar)
            
            # Contenedor para botones
            widget_container = QWidget()
            widget_container.setLayout(btn_layout)
            self.tabla_ejercicios.setCellWidget(i, 6, widget_container)
    
    def on_filtro_usuario_changed(self, index: int):
        """Manejador para cambio de filtro de usuario"""
        self.cargar_rutinas()
    
    def filtrar_rutinas(self):
        """Filtra las rutinas según los criterios seleccionados"""
        self.actualizar_tabla_rutinas()
    
    def filtrar_ejercicios(self):
        """Filtra los ejercicios según los criterios seleccionados"""
        self.actualizar_tabla_ejercicios()
    
    def nueva_rutina(self):
        """Abre diálogo para crear una nueva rutina"""
        dialog = NuevaRutinaDialog(self, self.api_client)
        if dialog.exec():
            data = dialog.get_data()
            try:
                resultado = self.api_client.crear_rutina(data)
                QMessageBox.information(self, "Éxito", "Rutina creada correctamente.")
                self.cargar_rutinas()
                
                # Seleccionar la nueva rutina si es posible
                if resultado and "id" in resultado:
                    self.ver_rutina(resultado["id"])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la rutina: {str(e)}")
    
    def editar_rutina(self):
        """Edita la rutina seleccionada"""
        if not self.rutina_seleccionada:
            return
            
        self.editar_rutina_desde_lista(self.rutina_seleccionada.get("id"))
    
    def editar_rutina_desde_lista(self, rutina_id: int):
        """Edita una rutina desde la lista de rutinas"""
        # Buscar la rutina
        rutina = None
        for r in self.rutinas:
            if r.get("id") == rutina_id:
                rutina = r
                break
        
        if not rutina:
            QMessageBox.warning(self, "Advertencia", "Rutina no encontrada.")
            return
            
        dialog = NuevaRutinaDialog(self, self.api_client, rutina)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.api_client.actualizar_rutina(rutina_id, data)
                QMessageBox.information(self, "Éxito", "Rutina actualizada correctamente.")
                self.cargar_rutinas()
                
                # Actualizar detalle si es la rutina seleccionada
                if self.rutina_seleccionada and self.rutina_seleccionada.get("id") == rutina_id:
                    self.ver_rutina(rutina_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar la rutina: {str(e)}")
    
    def eliminar_rutina(self):
        """Elimina la rutina seleccionada"""
        if not self.rutina_seleccionada:
            return
            
        self.eliminar_rutina_desde_lista(self.rutina_seleccionada.get("id"))
    
    def eliminar_rutina_desde_lista(self, rutina_id: int):
        """Elimina una rutina desde la lista de rutinas"""
        reply = QMessageBox.question(
            self, "Confirmar eliminación", 
            "¿Está seguro de que desea eliminar esta rutina? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.api_client.eliminar_rutina(rutina_id)
                QMessageBox.information(self, "Éxito", "Rutina eliminada correctamente.")
                
                # Limpiar detalle si es la rutina seleccionada
                if self.rutina_seleccionada and self.rutina_seleccionada.get("id") == rutina_id:
                    self.limpiar_detalle_rutina()
                    self.rutina_seleccionada = None
                
                self.cargar_rutinas()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar la rutina: {str(e)}")
    
    def ver_rutina(self, rutina_id: int):
        """Muestra el detalle de una rutina específica"""
        # Buscar la rutina en la tabla
        for row in range(self.tabla_rutinas.rowCount()):
            if int(self.tabla_rutinas.item(row, 0).text()) == rutina_id:
                self.tabla_rutinas.selectRow(row)
                break
    
    def agregar_ejercicio(self):
        """Abre diálogo para agregar un ejercicio a la rutina"""
        if not self.rutina_seleccionada:
            return
            
        dialog = AgregarEjercicioDialog(self, self.api_client, self.rutina_seleccionada.get("id"))
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.api_client.agregar_ejercicio_rutina(data)
                QMessageBox.information(self, "Éxito", "Ejercicio agregado correctamente.")
                self.cargar_ejercicios_rutina(self.rutina_seleccionada.get("id"))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo agregar el ejercicio: {str(e)}")
    
    def editar_ejercicio(self, ejercicio_id: int):
        """Edita un ejercicio de la rutina"""
        # Buscar el ejercicio
        ejercicio = None
        for e in self.ejercicios_rutina:
            if e.get("id") == ejercicio_id:
                ejercicio = e
                break
        
        if not ejercicio:
            QMessageBox.warning(self, "Advertencia", "Ejercicio no encontrado.")
            return
            
        dialog = AgregarEjercicioDialog(
            self, 
            self.api_client, 
            self.rutina_seleccionada.get("id"),
            ejercicio
        )
        
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.api_client.actualizar_ejercicio_rutina(ejercicio_id, data)
                QMessageBox.information(self, "Éxito", "Ejercicio actualizado correctamente.")
                self.cargar_ejercicios_rutina(self.rutina_seleccionada.get("id"))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el ejercicio: {str(e)}")
    
    def eliminar_ejercicio(self, ejercicio_id: int):
        """Elimina un ejercicio de la rutina"""
        reply = QMessageBox.question(
            self, "Confirmar eliminación", 
            "¿Está seguro de que desea eliminar este ejercicio de la rutina? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.api_client.eliminar_ejercicio_rutina(ejercicio_id)
                QMessageBox.information(self, "Éxito", "Ejercicio eliminado correctamente.")
                self.cargar_ejercicios_rutina(self.rutina_seleccionada.get("id"))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el ejercicio: {str(e)}")
    
    def imprimir_rutina(self):
        """Imprime la rutina seleccionada"""
        if not self.rutina_seleccionada:
            return
            
        # Esta funcionalidad requeriría integración con un sistema de impresión
        QMessageBox.information(self, "Información", "Funcionalidad de impresión en desarrollo.")
    
    def enviar_rutina(self):
        """Envía la rutina por email"""
        if not self.rutina_seleccionada:
            return
            
        # Esta funcionalidad requeriría integración con un sistema de correo
        QMessageBox.information(self, "Información", "Funcionalidad de envío por email en desarrollo.")
    
    def on_error(self, mensaje: str):
        """Manejador de errores general"""
        QMessageBox.critical(self, "Error", mensaje)
