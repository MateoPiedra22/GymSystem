"""
Widget para la gestión de tipos de cuota
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QLabel, QComboBox,
    QTextEdit, QMessageBox, QHeaderView, QTabWidget,
    QFormLayout, QDialog, QDialogButtonBox, QSpinBox, QDateEdit,
    QCheckBox, QListWidget, QSplitter, QFrame, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPalette, QColor, QFont
from datetime import datetime, date
import json

from ..api_client import ApiClient

class TipoCuotaDialog(QDialog):
    """Diálogo para crear/editar tipos de cuota"""
    
    def __init__(self, api_client, tipo_cuota=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.tipo_cuota = tipo_cuota
        self.setup_ui()
        
        if tipo_cuota:
            self.cargar_datos_tipo_cuota()
    
    def setup_ui(self):
        self.setWindowTitle("Nuevo Tipo de Cuota" if not self.tipo_cuota else "Editar Tipo de Cuota")
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout()
        
        # Tabs para organizar información
        self.tabs = QTabWidget()
        
        # Tab de información básica
        basica_tab = QWidget()
        basica_layout = QFormLayout()
        
        self.codigo_input = QLineEdit()
        self.codigo_input.setPlaceholderText("Ej: MENSUAL_BASIC")
        basica_layout.addRow("Código *:", self.codigo_input)
        
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Ej: Membresía Mensual Básica")
        basica_layout.addRow("Nombre *:", self.nombre_input)
        
        self.descripcion_input = QTextEdit()
        self.descripcion_input.setMaximumHeight(80)
        self.descripcion_input.setPlaceholderText("Descripción del tipo de cuota")
        basica_layout.addRow("Descripción:", self.descripcion_input)
        
        self.duracion_dias_input = QSpinBox()
        self.duracion_dias_input.setRange(1, 365)
        self.duracion_dias_input.setValue(30)
        basica_layout.addRow("Duración (días) *:", self.duracion_dias_input)
        
        self.precio_input = QDoubleSpinBox()
        self.precio_input.setRange(0, 999999)
        self.precio_input.setPrefix("S/ ")
        self.precio_input.setValue(100.0)
        basica_layout.addRow("Precio *:", self.precio_input)
        
        self.precio_promocional_input = QDoubleSpinBox()
        self.precio_promocional_input.setRange(0, 999999)
        self.precio_promocional_input.setPrefix("S/ ")
        basica_layout.addRow("Precio Promocional:", self.precio_promocional_input)
        
        basica_tab.setLayout(basica_layout)
        self.tabs.addTab(basica_tab, "Información Básica")
        
        # Tab de configuración de acceso
        acceso_tab = QWidget()
        acceso_layout = QFormLayout()
        
        self.incluye_clases_checkbox = QCheckBox()
        self.incluye_clases_checkbox.setChecked(True)
        acceso_layout.addRow("Incluye Clases:", self.incluye_clases_checkbox)
        
        self.limite_clases_mes_input = QSpinBox()
        self.limite_clases_mes_input.setRange(0, 999)
        self.limite_clases_mes_input.setSpecialValueText("Ilimitado")
        acceso_layout.addRow("Límite Clases/Mes:", self.limite_clases_mes_input)
        
        self.acceso_24h_checkbox = QCheckBox()
        acceso_layout.addRow("Acceso 24 Horas:", self.acceso_24h_checkbox)
        
        self.incluye_evaluacion_checkbox = QCheckBox()
        self.incluye_evaluacion_checkbox.setChecked(True)
        acceso_layout.addRow("Incluye Evaluación:", self.incluye_evaluacion_checkbox)
        
        self.incluye_rutina_checkbox = QCheckBox()
        self.incluye_rutina_checkbox.setChecked(True)
        acceso_layout.addRow("Incluye Rutina:", self.incluye_rutina_checkbox)
        
        self.invitados_mes_input = QSpinBox()
        self.invitados_mes_input.setRange(0, 50)
        acceso_layout.addRow("Invitados por Mes:", self.invitados_mes_input)
        
        acceso_tab.setLayout(acceso_layout)
        self.tabs.addTab(acceso_tab, "Configuración de Acceso")
        
        # Tab de restricciones
        restricciones_tab = QWidget()
        restricciones_layout = QFormLayout()
        
        self.edad_minima_input = QSpinBox()
        self.edad_minima_input.setRange(0, 100)
        self.edad_minima_input.setSpecialValueText("Sin límite")
        restricciones_layout.addRow("Edad Mínima:", self.edad_minima_input)
        
        self.edad_maxima_input = QSpinBox()
        self.edad_maxima_input.setRange(0, 100)
        self.edad_maxima_input.setSpecialValueText("Sin límite")
        restricciones_layout.addRow("Edad Máxima:", self.edad_maxima_input)
        
        self.horario_restringido_checkbox = QCheckBox()
        restricciones_layout.addRow("Horario Restringido:", self.horario_restringido_checkbox)
        
        self.horario_inicio_input = QLineEdit()
        self.horario_inicio_input.setPlaceholderText("08:00")
        restricciones_layout.addRow("Horario Inicio:", self.horario_inicio_input)
        
        self.horario_fin_input = QLineEdit()
        self.horario_fin_input.setPlaceholderText("22:00")
        restricciones_layout.addRow("Horario Fin:", self.horario_fin_input)
        
        restricciones_tab.setLayout(restricciones_layout)
        self.tabs.addTab(restricciones_tab, "Restricciones")
        
        # Tab de configuración
        config_tab = QWidget()
        config_layout = QFormLayout()
        
        self.activo_checkbox = QCheckBox()
        self.activo_checkbox.setChecked(True)
        config_layout.addRow("Activo:", self.activo_checkbox)
        
        self.visible_web_checkbox = QCheckBox()
        self.visible_web_checkbox.setChecked(True)
        config_layout.addRow("Visible en Web:", self.visible_web_checkbox)
        
        self.requiere_aprobacion_checkbox = QCheckBox()
        config_layout.addRow("Requiere Aprobación:", self.requiere_aprobacion_checkbox)
        
        self.renovacion_automatica_checkbox = QCheckBox()
        self.renovacion_automatica_checkbox.setChecked(True)
        config_layout.addRow("Renovación Automática:", self.renovacion_automatica_checkbox)
        
        self.dias_aviso_vencimiento_input = QSpinBox()
        self.dias_aviso_vencimiento_input.setRange(1, 30)
        self.dias_aviso_vencimiento_input.setValue(7)
        config_layout.addRow("Días Aviso Vencimiento:", self.dias_aviso_vencimiento_input)
        
        self.orden_visualizacion_input = QSpinBox()
        self.orden_visualizacion_input.setRange(1, 100)
        self.orden_visualizacion_input.setValue(1)
        config_layout.addRow("Orden Visualización:", self.orden_visualizacion_input)
        
        # Beneficios adicionales
        beneficios_label = QLabel("Beneficios Adicionales:")
        self.beneficios_list = QListWidget()
        self.beneficios_list.setMaximumHeight(100)
        
        beneficios_buttons = QHBoxLayout()
        self.add_beneficio_btn = QPushButton("Agregar")
        self.add_beneficio_btn.clicked.connect(self.agregar_beneficio)
        self.remove_beneficio_btn = QPushButton("Eliminar")
        self.remove_beneficio_btn.clicked.connect(self.eliminar_beneficio)
        beneficios_buttons.addWidget(self.add_beneficio_btn)
        beneficios_buttons.addWidget(self.remove_beneficio_btn)
        beneficios_buttons.addStretch()
        
        config_layout.addRow(beneficios_label, self.beneficios_list)
        config_layout.addRow("", beneficios_buttons)
        
        config_tab.setLayout(config_layout)
        self.tabs.addTab(config_tab, "Configuración")
        
        layout.addWidget(self.tabs)
        
        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Aplicar estilos
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #2196F3;
            }
            QPushButton {
                padding: 8px 16px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
    
    def agregar_beneficio(self):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Nuevo Beneficio", "Ingrese el beneficio:")
        if ok and text:
            self.beneficios_list.addItem(text)
    
    def eliminar_beneficio(self):
        current = self.beneficios_list.currentRow()
        if current >= 0:
            self.beneficios_list.takeItem(current)
    
    def cargar_datos_tipo_cuota(self):
        """Carga los datos del tipo de cuota en el formulario"""
        if not self.tipo_cuota:
            return
            
        self.codigo_input.setText(self.tipo_cuota.get('codigo', ''))
        self.nombre_input.setText(self.tipo_cuota.get('nombre', ''))
        self.descripcion_input.setText(self.tipo_cuota.get('descripcion', ''))
        self.duracion_dias_input.setValue(self.tipo_cuota.get('duracion_dias', 30))
        self.precio_input.setValue(self.tipo_cuota.get('precio', 0))
        self.precio_promocional_input.setValue(self.tipo_cuota.get('precio_promocional', 0))
        
        self.incluye_clases_checkbox.setChecked(self.tipo_cuota.get('incluye_clases', True))
        self.limite_clases_mes_input.setValue(self.tipo_cuota.get('limite_clases_mes', 0))
        self.acceso_24h_checkbox.setChecked(self.tipo_cuota.get('acceso_24h', False))
        self.incluye_evaluacion_checkbox.setChecked(self.tipo_cuota.get('incluye_evaluacion', True))
        self.incluye_rutina_checkbox.setChecked(self.tipo_cuota.get('incluye_rutina', True))
        self.invitados_mes_input.setValue(self.tipo_cuota.get('invitados_mes', 0))
        
        self.edad_minima_input.setValue(self.tipo_cuota.get('edad_minima', 0))
        self.edad_maxima_input.setValue(self.tipo_cuota.get('edad_maxima', 0))
        self.horario_restringido_checkbox.setChecked(self.tipo_cuota.get('horario_restringido', False))
        self.horario_inicio_input.setText(self.tipo_cuota.get('horario_inicio', ''))
        self.horario_fin_input.setText(self.tipo_cuota.get('horario_fin', ''))
        
        self.activo_checkbox.setChecked(self.tipo_cuota.get('activo', True))
        self.visible_web_checkbox.setChecked(self.tipo_cuota.get('visible_web', True))
        self.requiere_aprobacion_checkbox.setChecked(self.tipo_cuota.get('requiere_aprobacion', False))
        self.renovacion_automatica_checkbox.setChecked(self.tipo_cuota.get('renovacion_automatica', True))
        self.dias_aviso_vencimiento_input.setValue(self.tipo_cuota.get('dias_aviso_vencimiento', 7))
        self.orden_visualizacion_input.setValue(self.tipo_cuota.get('orden_visualizacion', 1))
        
        # Cargar beneficios
        beneficios = self.tipo_cuota.get('beneficios', [])
        if isinstance(beneficios, str):
            try:
                beneficios = json.loads(beneficios)
            except:
                beneficios = []
        for beneficio in beneficios:
            self.beneficios_list.addItem(beneficio)
    
    def get_tipo_cuota_data(self):
        """Obtiene los datos del formulario"""
        beneficios = []
        for i in range(self.beneficios_list.count()):
            beneficios.append(self.beneficios_list.item(i).text())
        
        data = {
            'codigo': self.codigo_input.text().strip(),
            'nombre': self.nombre_input.text().strip(),
            'descripcion': self.descripcion_input.toPlainText().strip(),
            'duracion_dias': self.duracion_dias_input.value(),
            'precio': self.precio_input.value(),
            'precio_promocional': self.precio_promocional_input.value() if self.precio_promocional_input.value() > 0 else None,
            'incluye_clases': self.incluye_clases_checkbox.isChecked(),
            'limite_clases_mes': self.limite_clases_mes_input.value() if self.limite_clases_mes_input.value() > 0 else None,
            'acceso_24h': self.acceso_24h_checkbox.isChecked(),
            'incluye_evaluacion': self.incluye_evaluacion_checkbox.isChecked(),
            'incluye_rutina': self.incluye_rutina_checkbox.isChecked(),
            'invitados_mes': self.invitados_mes_input.value(),
            'edad_minima': self.edad_minima_input.value() if self.edad_minima_input.value() > 0 else None,
            'edad_maxima': self.edad_maxima_input.value() if self.edad_maxima_input.value() > 0 else None,
            'horario_restringido': self.horario_restringido_checkbox.isChecked(),
            'horario_inicio': self.horario_inicio_input.text().strip() if self.horario_inicio_input.text().strip() else None,
            'horario_fin': self.horario_fin_input.text().strip() if self.horario_fin_input.text().strip() else None,
            'beneficios': beneficios,
            'activo': self.activo_checkbox.isChecked(),
            'visible_web': self.visible_web_checkbox.isChecked(),
            'requiere_aprobacion': self.requiere_aprobacion_checkbox.isChecked(),
            'renovacion_automatica': self.renovacion_automatica_checkbox.isChecked(),
            'dias_aviso_vencimiento': self.dias_aviso_vencimiento_input.value(),
            'orden_visualizacion': self.orden_visualizacion_input.value()
        }
        
        return data

class TiposCuotaTabWidget(QWidget):
    """Widget principal para la gestión de tipos de cuota"""
    
    tipoCuotaSeleccionado = pyqtSignal(dict)
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.tipos_cuota = []
        self.tipo_cuota_seleccionado = None
        self.setup_ui()
        self.cargar_tipos_cuota()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Header con título y estadísticas
        header = QHBoxLayout()
        
        title_label = QLabel("💳 Gestión de Tipos de Cuota")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1976D2;
                padding: 10px;
            }
        """)
        header.addWidget(title_label)
        
        # Estadísticas rápidas
        self.stats_label = QLabel("Total: 0 | Activos: 0 | Inactivos: 0")
        self.stats_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
            }
        """)
        header.addStretch()
        header.addWidget(self.stats_label)
        
        layout.addLayout(header)
        
        # Barra de herramientas
        toolbar = QHBoxLayout()
        
        # Búsqueda
        self.buscar_input = QLineEdit()
        self.buscar_input.setPlaceholderText("🔍 Buscar tipo de cuota por código o nombre...")
        self.buscar_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        self.buscar_input.textChanged.connect(self.filtrar_tipos_cuota)
        
        # Filtros
        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems(["Todos", "Activos", "Inactivos"])
        self.filtro_estado.currentTextChanged.connect(self.filtrar_tipos_cuota)
        
        self.filtro_promocion = QComboBox()
        self.filtro_promocion.addItems(["Todos", "En Promoción", "Precio Normal"])
        self.filtro_promocion.currentTextChanged.connect(self.filtrar_tipos_cuota)
        
        toolbar.addWidget(self.buscar_input, 3)
        toolbar.addWidget(self.filtro_estado, 1)
        toolbar.addWidget(self.filtro_promocion, 1)
        
        layout.addLayout(toolbar)
        
        # Splitter para tabla y detalles
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo con tabla
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabla de tipos de cuota
        self.tabla_tipos_cuota = QTableWidget()
        self.tabla_tipos_cuota.setColumnCount(8)
        self.tabla_tipos_cuota.setHorizontalHeaderLabels([
            "Código", "Nombre", "Precio", "Duración", 
            "Promoción", "Estado", "Orden", "Acciones"
        ])
        
        # Configurar tabla
        self.tabla_tipos_cuota.setAlternatingRowColors(True)
        self.tabla_tipos_cuota.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_tipos_cuota.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_tipos_cuota.horizontalHeader().setStretchLastSection(True)
        self.tabla_tipos_cuota.verticalHeader().setVisible(False)
        self.tabla_tipos_cuota.itemSelectionChanged.connect(self.on_tipo_cuota_seleccionado)
        
        self.tabla_tipos_cuota.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: black;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: none;
                font-weight: bold;
                text-align: left;
            }
        """)
        
        left_layout.addWidget(self.tabla_tipos_cuota)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        self.btn_nuevo = QPushButton("➕ Nuevo Tipo de Cuota")
        self.btn_nuevo.clicked.connect(self.nuevo_tipo_cuota)
        self.btn_nuevo.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.editar_tipo_cuota)
        self.btn_editar.setEnabled(False)
        
        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_tipo_cuota)
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        self.btn_actualizar = QPushButton("🔄 Actualizar")
        self.btn_actualizar.clicked.connect(self.cargar_tipos_cuota)
        
        button_layout.addWidget(self.btn_nuevo)
        button_layout.addWidget(self.btn_editar)
        button_layout.addWidget(self.btn_eliminar)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_actualizar)
        
        left_layout.addLayout(button_layout)
        left_panel.setLayout(left_layout)
        
        # Panel derecho con detalles
        self.detalles_panel = QWidget()
        detalles_layout = QVBoxLayout()
        
        # Información básica del tipo de cuota
        info_layout = QVBoxLayout()
        
        self.nombre_label = QLabel("Seleccione un tipo de cuota")
        self.nombre_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.codigo_label = QLabel("")
        self.codigo_label.setStyleSheet("font-size: 14px; color: #666;")
        
        self.precio_label = QLabel("")
        self.precio_label.setStyleSheet("font-size: 16px; color: #2196F3; font-weight: bold;")
        
        info_layout.addWidget(self.nombre_label)
        info_layout.addWidget(self.codigo_label)
        info_layout.addWidget(self.precio_label)
        
        detalles_layout.addLayout(info_layout)
        
        # Tabs con detalles
        self.detalles_tabs = QTabWidget()
        
        # Tab de características
        caracteristicas_tab = QWidget()
        caracteristicas_layout = QFormLayout()
        
        self.duracion_label = QLabel("-")
        caracteristicas_layout.addRow("Duración:", self.duracion_label)
        
        self.incluye_clases_label = QLabel("-")
        caracteristicas_layout.addRow("Incluye Clases:", self.incluye_clases_label)
        
        self.limite_clases_label = QLabel("-")
        caracteristicas_layout.addRow("Límite Clases/Mes:", self.limite_clases_label)
        
        self.acceso_24h_label = QLabel("-")
        caracteristicas_layout.addRow("Acceso 24h:", self.acceso_24h_label)
        
        self.incluye_evaluacion_label = QLabel("-")
        caracteristicas_layout.addRow("Incluye Evaluación:", self.incluye_evaluacion_label)
        
        self.incluye_rutina_label = QLabel("-")
        caracteristicas_layout.addRow("Incluye Rutina:", self.incluye_rutina_label)
        
        self.invitados_mes_label = QLabel("-")
        caracteristicas_layout.addRow("Invitados/Mes:", self.invitados_mes_label)
        
        caracteristicas_tab.setLayout(caracteristicas_layout)
        self.detalles_tabs.addTab(caracteristicas_tab, "Características")
        
        # Tab de configuración
        config_detalles_tab = QWidget()
        config_detalles_layout = QFormLayout()
        
        self.estado_label = QLabel("-")
        config_detalles_layout.addRow("Estado:", self.estado_label)
        
        self.visible_web_label = QLabel("-")
        config_detalles_layout.addRow("Visible en Web:", self.visible_web_label)
        
        self.renovacion_automatica_label = QLabel("-")
        config_detalles_layout.addRow("Renovación Automática:", self.renovacion_automatica_label)
        
        self.orden_visualizacion_label = QLabel("-")
        config_detalles_layout.addRow("Orden Visualización:", self.orden_visualizacion_label)
        
        config_detalles_tab.setLayout(config_detalles_layout)
        self.detalles_tabs.addTab(config_detalles_tab, "Configuración")
        
        detalles_layout.addWidget(self.detalles_tabs)
        self.detalles_panel.setLayout(detalles_layout)
        
        # Agregar paneles al splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.detalles_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # Aplicar estilos generales
        self.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
    
    def cargar_tipos_cuota(self):
        """Carga la lista de tipos de cuota desde el servidor"""
        try:
            response = self.api_client.get("/tipos-cuota")
            if response and 'items' in response:
                self.tipos_cuota = response['items']
                self.actualizar_tabla()
                self.actualizar_estadisticas()
            else:
                QMessageBox.warning(self, "Advertencia", "No se pudieron cargar los tipos de cuota")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar tipos de cuota: {str(e)}")
    
    def actualizar_tabla(self):
        """Actualiza la tabla con los tipos de cuota"""
        self.tabla_tipos_cuota.setRowCount(len(self.tipos_cuota))
        
        for i, tipo in enumerate(self.tipos_cuota):
            # Código
            self.tabla_tipos_cuota.setItem(i, 0, QTableWidgetItem(tipo.get('codigo', '')))
            
            # Nombre
            self.tabla_tipos_cuota.setItem(i, 1, QTableWidgetItem(tipo.get('nombre', '')))
            
            # Precio
            precio = tipo.get('precio', 0)
            precio_promocional = tipo.get('precio_promocional')
            if precio_promocional and precio_promocional < precio:
                precio_text = f"S/ {precio_promocional:.2f} (S/ {precio:.2f})"
            else:
                precio_text = f"S/ {precio:.2f}"
            self.tabla_tipos_cuota.setItem(i, 2, QTableWidgetItem(precio_text))
            
            # Duración
            duracion = tipo.get('duracion_dias', 30)
            if duracion == 30:
                duracion_text = "1 mes"
            elif duracion == 365:
                duracion_text = "1 año"
            else:
                duracion_text = f"{duracion} días"
            self.tabla_tipos_cuota.setItem(i, 3, QTableWidgetItem(duracion_text))
            
            # Promoción
            es_promocion = precio_promocional and precio_promocional < precio
            promocion_item = QTableWidgetItem("Sí" if es_promocion else "No")
            if es_promocion:
                promocion_item.setForeground(QColor('#f44336'))
            self.tabla_tipos_cuota.setItem(i, 4, promocion_item)
            
            # Estado
            estado = tipo.get('activo', True)
            estado_item = QTableWidgetItem("Activo" if estado else "Inactivo")
            if estado:
                estado_item.setForeground(QColor('#4CAF50'))
            else:
                estado_item.setForeground(QColor('#f44336'))
            self.tabla_tipos_cuota.setItem(i, 5, estado_item)
            
            # Orden
            orden = tipo.get('orden_visualizacion', 1)
            self.tabla_tipos_cuota.setItem(i, 6, QTableWidgetItem(str(orden)))
            
            # Botón de acciones
            acciones_widget = QWidget()
            acciones_layout = QHBoxLayout()
            acciones_layout.setContentsMargins(5, 5, 5, 5)
            
            btn_ver = QPushButton("👁")
            btn_ver.setToolTip("Ver detalles")
            btn_ver.clicked.connect(lambda checked, row=i: self.ver_detalles_tipo_cuota(row))
            btn_ver.setMaximumWidth(30)
            
            acciones_layout.addWidget(btn_ver)
            acciones_widget.setLayout(acciones_layout)
            
            self.tabla_tipos_cuota.setCellWidget(i, 7, acciones_widget)
        
        # Ajustar columnas
        self.tabla_tipos_cuota.resizeColumnsToContents()
    
    def actualizar_estadisticas(self):
        """Actualiza las estadísticas mostradas"""
        total = len(self.tipos_cuota)
        activos = sum(1 for t in self.tipos_cuota if t.get('activo', True))
        inactivos = total - activos
        
        self.stats_label.setText(f"Total: {total} | Activos: {activos} | Inactivos: {inactivos}")
    
    def filtrar_tipos_cuota(self):
        """Filtra los tipos de cuota según los criterios seleccionados"""
        texto_busqueda = self.buscar_input.text().lower()
        estado_filtro = self.filtro_estado.currentText()
        promocion_filtro = self.filtro_promocion.currentText()
        
        for i in range(self.tabla_tipos_cuota.rowCount()):
            mostrar = True
            
            # Filtro por texto
            if texto_busqueda:
                codigo = self.tabla_tipos_cuota.item(i, 0).text().lower()
                nombre = self.tabla_tipos_cuota.item(i, 1).text().lower()
                
                if texto_busqueda not in codigo and texto_busqueda not in nombre:
                    mostrar = False
            
            # Filtro por estado
            if estado_filtro != "Todos":
                estado = self.tabla_tipos_cuota.item(i, 5).text()
                if estado_filtro == "Activos" and estado != "Activo":
                    mostrar = False
                elif estado_filtro == "Inactivos" and estado == "Activo":
                    mostrar = False
            
            # Filtro por promoción
            if promocion_filtro != "Todos":
                promocion = self.tabla_tipos_cuota.item(i, 4).text()
                if promocion_filtro == "En Promoción" and promocion != "Sí":
                    mostrar = False
                elif promocion_filtro == "Precio Normal" and promocion == "Sí":
                    mostrar = False
            
            self.tabla_tipos_cuota.setRowHidden(i, not mostrar)
    
    def on_tipo_cuota_seleccionado(self):
        """Maneja la selección de un tipo de cuota en la tabla"""
        current_row = self.tabla_tipos_cuota.currentRow()
        if 0 <= current_row < len(self.tipos_cuota):
            self.tipo_cuota_seleccionado = self.tipos_cuota[current_row]
            self.btn_editar.setEnabled(True)
            self.btn_eliminar.setEnabled(True)
            self.mostrar_detalles_tipo_cuota()
        else:
            self.tipo_cuota_seleccionado = None
            self.btn_editar.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
    
    def mostrar_detalles_tipo_cuota(self):
        """Muestra los detalles del tipo de cuota seleccionado"""
        if not self.tipo_cuota_seleccionado:
            return
        
        # Información básica
        self.nombre_label.setText(self.tipo_cuota_seleccionado.get('nombre', ''))
        self.codigo_label.setText(f"Código: {self.tipo_cuota_seleccionado.get('codigo', '')}")
        
        precio = self.tipo_cuota_seleccionado.get('precio', 0)
        precio_promocional = self.tipo_cuota_seleccionado.get('precio_promocional')
        if precio_promocional and precio_promocional < precio:
            precio_text = f"S/ {precio_promocional:.2f} (antes S/ {precio:.2f})"
        else:
            precio_text = f"S/ {precio:.2f}"
        self.precio_label.setText(precio_text)
        
        # Características
        duracion = self.tipo_cuota_seleccionado.get('duracion_dias', 30)
        if duracion == 30:
            duracion_text = "1 mes (30 días)"
        elif duracion == 365:
            duracion_text = "1 año (365 días)"
        else:
            duracion_text = f"{duracion} días"
        self.duracion_label.setText(duracion_text)
        
        self.incluye_clases_label.setText("Sí" if self.tipo_cuota_seleccionado.get('incluye_clases', True) else "No")
        
        limite_clases = self.tipo_cuota_seleccionado.get('limite_clases_mes')
        self.limite_clases_label.setText("Ilimitado" if not limite_clases else str(limite_clases))
        
        self.acceso_24h_label.setText("Sí" if self.tipo_cuota_seleccionado.get('acceso_24h', False) else "No")
        self.incluye_evaluacion_label.setText("Sí" if self.tipo_cuota_seleccionado.get('incluye_evaluacion', True) else "No")
        self.incluye_rutina_label.setText("Sí" if self.tipo_cuota_seleccionado.get('incluye_rutina', True) else "No")
        
        invitados = self.tipo_cuota_seleccionado.get('invitados_mes', 0)
        self.invitados_mes_label.setText(str(invitados) if invitados > 0 else "No incluye")
        
        # Configuración
        self.estado_label.setText("Activo" if self.tipo_cuota_seleccionado.get('activo', True) else "Inactivo")
        self.visible_web_label.setText("Sí" if self.tipo_cuota_seleccionado.get('visible_web', True) else "No")
        self.renovacion_automatica_label.setText("Sí" if self.tipo_cuota_seleccionado.get('renovacion_automatica', True) else "No")
        self.orden_visualizacion_label.setText(str(self.tipo_cuota_seleccionado.get('orden_visualizacion', 1)))
    
    def ver_detalles_tipo_cuota(self, row):
        """Muestra los detalles de un tipo de cuota específico"""
        self.tabla_tipos_cuota.selectRow(row)
    
    def nuevo_tipo_cuota(self):
        """Abre el diálogo para crear un nuevo tipo de cuota"""
        dialog = TipoCuotaDialog(self.api_client, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tipo_cuota_data = dialog.get_tipo_cuota_data()
            self.crear_tipo_cuota(tipo_cuota_data)
    
    def crear_tipo_cuota(self, tipo_cuota_data):
        """Crea un nuevo tipo de cuota"""
        try:
            response = self.api_client.post("/tipos-cuota", tipo_cuota_data)
            QMessageBox.information(self, "Éxito", "Tipo de cuota creado exitosamente")
            self.cargar_tipos_cuota()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al crear tipo de cuota: {str(e)}")
    
    def editar_tipo_cuota(self):
        """Abre el diálogo para editar el tipo de cuota seleccionado"""
        if not self.tipo_cuota_seleccionado:
            return
        
        dialog = TipoCuotaDialog(self.api_client, self.tipo_cuota_seleccionado, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tipo_cuota_data = dialog.get_tipo_cuota_data()
            self.actualizar_tipo_cuota(tipo_cuota_data)
    
    def actualizar_tipo_cuota(self, tipo_cuota_data):
        """Actualiza un tipo de cuota existente"""
        try:
            response = self.api_client.put(f"/tipos-cuota/{self.tipo_cuota_seleccionado['id']}", tipo_cuota_data)
            QMessageBox.information(self, "Éxito", "Tipo de cuota actualizado exitosamente")
            self.cargar_tipos_cuota()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar tipo de cuota: {str(e)}")
    
    def eliminar_tipo_cuota(self):
        """Elimina un tipo de cuota"""
        if not self.tipo_cuota_seleccionado:
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirmar eliminación",
            f"¿Está seguro de eliminar el tipo de cuota '{self.tipo_cuota_seleccionado.get('nombre', '')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                response = self.api_client.delete(f"/tipos-cuota/{self.tipo_cuota_seleccionado['id']}")
                QMessageBox.information(self, "Éxito", "Tipo de cuota eliminado exitosamente")
                self.cargar_tipos_cuota()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar tipo de cuota: {str(e)}") 