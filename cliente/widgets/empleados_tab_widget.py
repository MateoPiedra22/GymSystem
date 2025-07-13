"""
Widget para la gestión de empleados
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QLabel, QComboBox,
    QTextEdit, QMessageBox, QFileDialog, QHeaderView, QTabWidget,
    QFormLayout, QDialog, QDialogButtonBox, QSpinBox, QDateEdit,
    QCheckBox, QListWidget, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QPixmap, QPalette, QColor, QFont
from datetime import datetime, date
import json
import os

from ..api_client import ApiClient

class EmpleadoDialog(QDialog):
    """Diálogo para crear/editar empleados"""
    
    def __init__(self, api_client, empleado=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.empleado = empleado
        self.setup_ui()
        
        if empleado:
            self.cargar_datos_empleado()
    
    def setup_ui(self):
        self.setWindowTitle("Nuevo Empleado" if not self.empleado else "Editar Empleado")
        self.setMinimumSize(800, 700)
        
        layout = QVBoxLayout()
        
        # Tabs para organizar información
        self.tabs = QTabWidget()
        
        # Tab de información personal
        personal_tab = QWidget()
        personal_layout = QFormLayout()
        
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Nombre del empleado")
        personal_layout.addRow("Nombre *:", self.nombre_input)
        
        self.apellido_input = QLineEdit()
        self.apellido_input.setPlaceholderText("Apellido del empleado")
        personal_layout.addRow("Apellido *:", self.apellido_input)
        
        self.dni_input = QLineEdit()
        self.dni_input.setPlaceholderText("12345678")
        personal_layout.addRow("DNI *:", self.dni_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("empleado@empresa.com")
        personal_layout.addRow("Email *:", self.email_input)
        
        self.telefono_input = QLineEdit()
        self.telefono_input.setPlaceholderText("999999999")
        personal_layout.addRow("Teléfono *:", self.telefono_input)
        
        self.telefono_emergencia_input = QLineEdit()
        self.telefono_emergencia_input.setPlaceholderText("Contacto de emergencia")
        personal_layout.addRow("Tel. Emergencia:", self.telefono_emergencia_input)
        
        self.direccion_input = QTextEdit()
        self.direccion_input.setMaximumHeight(60)
        self.direccion_input.setPlaceholderText("Dirección completa")
        personal_layout.addRow("Dirección *:", self.direccion_input)
        
        self.fecha_nacimiento_input = QDateEdit()
        self.fecha_nacimiento_input.setCalendarPopup(True)
        self.fecha_nacimiento_input.setDate(QDate.currentDate().addYears(-25))
        personal_layout.addRow("Fecha Nacimiento *:", self.fecha_nacimiento_input)
        
        personal_tab.setLayout(personal_layout)
        self.tabs.addTab(personal_tab, "Información Personal")
        
        # Tab de información laboral
        laboral_tab = QWidget()
        laboral_layout = QFormLayout()
        
        self.cargo_input = QLineEdit()
        self.cargo_input.setPlaceholderText("Ej: Instructor Senior")
        laboral_layout.addRow("Cargo *:", self.cargo_input)
        
        self.departamento_combo = QComboBox()
        self.departamento_combo.addItems([
            "Administración", "Entrenamiento", "Recepción", 
            "Limpieza", "Mantenimiento", "Ventas", "Marketing"
        ])
        laboral_layout.addRow("Departamento *:", self.departamento_combo)
        
        self.fecha_ingreso_input = QDateEdit()
        self.fecha_ingreso_input.setCalendarPopup(True)
        self.fecha_ingreso_input.setDate(QDate.currentDate())
        laboral_layout.addRow("Fecha Ingreso *:", self.fecha_ingreso_input)
        
        self.tipo_contrato_combo = QComboBox()
        self.tipo_contrato_combo.addItems([
            "Tiempo Completo", "Medio Tiempo", "Por Horas", "Temporal", "Prácticas"
        ])
        laboral_layout.addRow("Tipo Contrato *:", self.tipo_contrato_combo)
        
        self.salario_input = QSpinBox()
        self.salario_input.setRange(0, 999999)
        self.salario_input.setPrefix("$ ")
        self.salario_input.setValue(1000)
        laboral_layout.addRow("Salario Base *:", self.salario_input)
        
        self.comisiones_input = QSpinBox()
        self.comisiones_input.setRange(0, 100)
        self.comisiones_input.setSuffix(" %")
        laboral_layout.addRow("Comisiones:", self.comisiones_input)
        
        # Horario
        horario_group = QGroupBox("Horario de Trabajo")
        horario_layout = QFormLayout()
        
        self.horario_entrada_input = QLineEdit()
        self.horario_entrada_input.setPlaceholderText("08:00")
        horario_layout.addRow("Entrada:", self.horario_entrada_input)
        
        self.horario_salida_input = QLineEdit()
        self.horario_salida_input.setPlaceholderText("17:00")
        horario_layout.addRow("Salida:", self.horario_salida_input)
        
        self.dias_trabajo_input = QLineEdit()
        self.dias_trabajo_input.setPlaceholderText("L-V o L,M,X,J,V")
        horario_layout.addRow("Días:", self.dias_trabajo_input)
        
        horario_group.setLayout(horario_layout)
        laboral_layout.addRow(horario_group)
        
        laboral_tab.setLayout(laboral_layout)
        self.tabs.addTab(laboral_tab, "Información Laboral")
        
        # Tab de información adicional
        adicional_tab = QWidget()
        adicional_layout = QFormLayout()
        
        # Certificaciones
        cert_label = QLabel("Certificaciones:")
        self.certificaciones_list = QListWidget()
        self.certificaciones_list.setMaximumHeight(100)
        
        cert_buttons = QHBoxLayout()
        self.add_cert_btn = QPushButton("Agregar")
        self.add_cert_btn.clicked.connect(self.agregar_certificacion)
        self.remove_cert_btn = QPushButton("Eliminar")
        self.remove_cert_btn.clicked.connect(self.eliminar_certificacion)
        cert_buttons.addWidget(self.add_cert_btn)
        cert_buttons.addWidget(self.remove_cert_btn)
        cert_buttons.addStretch()
        
        adicional_layout.addRow(cert_label, self.certificaciones_list)
        adicional_layout.addRow("", cert_buttons)
        
        # Datos bancarios
        self.banco_input = QLineEdit()
        self.banco_input.setPlaceholderText("Nombre del banco")
        adicional_layout.addRow("Banco:", self.banco_input)
        
        self.numero_cuenta_input = QLineEdit()
        self.numero_cuenta_input.setPlaceholderText("Número de cuenta")
        adicional_layout.addRow("Número Cuenta:", self.numero_cuenta_input)
        
        self.tipo_cuenta_combo = QComboBox()
        self.tipo_cuenta_combo.addItems(["", "Ahorros", "Corriente"])
        adicional_layout.addRow("Tipo Cuenta:", self.tipo_cuenta_combo)
        
        # Notas
        self.notas_input = QTextEdit()
        self.notas_input.setMaximumHeight(80)
        self.notas_input.setPlaceholderText("Notas adicionales sobre el empleado")
        adicional_layout.addRow("Notas:", self.notas_input)
        
        adicional_tab.setLayout(adicional_layout)
        self.tabs.addTab(adicional_tab, "Información Adicional")
        
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
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {
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
    
    def agregar_certificacion(self):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Nueva Certificación", "Ingrese el nombre de la certificación:")
        if ok and text:
            self.certificaciones_list.addItem(text)
    
    def eliminar_certificacion(self):
        current = self.certificaciones_list.currentRow()
        if current >= 0:
            self.certificaciones_list.takeItem(current)
    
    def cargar_datos_empleado(self):
        """Carga los datos del empleado en el formulario"""
        if not self.empleado:
            return
            
        self.nombre_input.setText(self.empleado.get('nombre', ''))
        self.apellido_input.setText(self.empleado.get('apellido', ''))
        self.dni_input.setText(self.empleado.get('dni', ''))
        self.email_input.setText(self.empleado.get('email', ''))
        self.telefono_input.setText(self.empleado.get('telefono', ''))
        self.telefono_emergencia_input.setText(self.empleado.get('telefono_emergencia', ''))
        self.direccion_input.setText(self.empleado.get('direccion', ''))
        
        if self.empleado.get('fecha_nacimiento'):
            fecha = QDate.fromString(self.empleado['fecha_nacimiento'], "yyyy-MM-dd")
            self.fecha_nacimiento_input.setDate(fecha)
        
        self.cargo_input.setText(self.empleado.get('cargo', ''))
        
        # Mapear departamento
        depto_map = {
            'Administración': 0, 'Entrenamiento': 1, 'Recepción': 2,
            'Limpieza': 3, 'Mantenimiento': 4, 'Ventas': 5, 'Marketing': 6
        }
        self.departamento_combo.setCurrentIndex(depto_map.get(self.empleado.get('departamento', ''), 0))
        
        if self.empleado.get('fecha_ingreso'):
            fecha = QDate.fromString(self.empleado['fecha_ingreso'], "yyyy-MM-dd")
            self.fecha_ingreso_input.setDate(fecha)
        
        # Mapear tipo contrato
        contrato_map = {
            'Tiempo Completo': 0, 'Medio Tiempo': 1, 'Por Horas': 2,
            'Temporal': 3, 'Prácticas': 4
        }
        self.tipo_contrato_combo.setCurrentIndex(contrato_map.get(self.empleado.get('tipo_contrato', ''), 0))
        
        self.salario_input.setValue(int(self.empleado.get('salario_base', 0)))
        self.comisiones_input.setValue(int(self.empleado.get('comisiones_porcentaje', 0)))
        
        self.horario_entrada_input.setText(self.empleado.get('horario_entrada', ''))
        self.horario_salida_input.setText(self.empleado.get('horario_salida', ''))
        self.dias_trabajo_input.setText(self.empleado.get('dias_trabajo', ''))
        
        # Cargar certificaciones
        certificaciones = self.empleado.get('certificaciones', [])
        if isinstance(certificaciones, str):
            try:
                certificaciones = json.loads(certificaciones)
            except:
                certificaciones = []
        for cert in certificaciones:
            self.certificaciones_list.addItem(cert)
        
        self.banco_input.setText(self.empleado.get('banco', ''))
        self.numero_cuenta_input.setText(self.empleado.get('numero_cuenta', ''))
        
        tipo_cuenta_idx = 0
        if self.empleado.get('tipo_cuenta') == 'Ahorros':
            tipo_cuenta_idx = 1
        elif self.empleado.get('tipo_cuenta') == 'Corriente':
            tipo_cuenta_idx = 2
        self.tipo_cuenta_combo.setCurrentIndex(tipo_cuenta_idx)
        
        self.notas_input.setText(self.empleado.get('notas', ''))
    
    def get_empleado_data(self):
        """Obtiene los datos del formulario"""
        certificaciones = []
        for i in range(self.certificaciones_list.count()):
            certificaciones.append(self.certificaciones_list.item(i).text())
        
        data = {
            'nombre': self.nombre_input.text().strip(),
            'apellido': self.apellido_input.text().strip(),
            'dni': self.dni_input.text().strip(),
            'email': self.email_input.text().strip(),
            'telefono': self.telefono_input.text().strip(),
            'telefono_emergencia': self.telefono_emergencia_input.text().strip(),
            'direccion': self.direccion_input.toPlainText().strip(),
            'fecha_nacimiento': self.fecha_nacimiento_input.date().toString("yyyy-MM-dd"),
            'cargo': self.cargo_input.text().strip(),
            'departamento': self.departamento_combo.currentText(),
            'fecha_ingreso': self.fecha_ingreso_input.date().toString("yyyy-MM-dd"),
            'tipo_contrato': self.tipo_contrato_combo.currentText(),
            'salario_base': self.salario_input.value(),
            'comisiones_porcentaje': self.comisiones_input.value(),
            'horario_entrada': self.horario_entrada_input.text().strip(),
            'horario_salida': self.horario_salida_input.text().strip(),
            'dias_trabajo': self.dias_trabajo_input.text().strip(),
            'certificaciones': certificaciones,
            'banco': self.banco_input.text().strip(),
            'numero_cuenta': self.numero_cuenta_input.text().strip(),
            'tipo_cuenta': self.tipo_cuenta_combo.currentText() if self.tipo_cuenta_combo.currentIndex() > 0 else None,
            'notas': self.notas_input.toPlainText().strip()
        }
        
        # Eliminar campos vacíos opcionales
        optional_fields = ['telefono_emergencia', 'horario_entrada', 'horario_salida', 
                          'dias_trabajo', 'banco', 'numero_cuenta', 'tipo_cuenta', 'notas']
        for field in optional_fields:
            if not data[field]:
                data[field] = None
        
        return data

class EmpleadosTabWidget(QWidget):
    """Widget principal para la gestión de empleados"""
    
    empleadoSeleccionado = pyqtSignal(dict)
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.empleados = []
        self.empleado_seleccionado = None
        self.setup_ui()
        self.cargar_empleados()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Header con título y estadísticas
        header = QHBoxLayout()
        
        title_label = QLabel("👥 Gestión de Empleados")
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
        self.buscar_input.setPlaceholderText("🔍 Buscar empleado por nombre, DNI o cargo...")
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
        self.buscar_input.textChanged.connect(self.filtrar_empleados)
        
        # Filtros
        self.filtro_depto = QComboBox()
        self.filtro_depto.addItem("Todos los departamentos")
        self.filtro_depto.addItems([
            "Administración", "Entrenamiento", "Recepción", 
            "Limpieza", "Mantenimiento", "Ventas", "Marketing"
        ])
        self.filtro_depto.currentTextChanged.connect(self.filtrar_empleados)
        
        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems(["Todos", "Activos", "Inactivos"])
        self.filtro_estado.currentTextChanged.connect(self.filtrar_empleados)
        
        toolbar.addWidget(self.buscar_input, 3)
        toolbar.addWidget(self.filtro_depto, 1)
        toolbar.addWidget(self.filtro_estado, 1)
        
        layout.addLayout(toolbar)
        
        # Splitter para tabla y detalles
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo con tabla
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabla de empleados
        self.tabla_empleados = QTableWidget()
        self.tabla_empleados.setColumnCount(8)
        self.tabla_empleados.setHorizontalHeaderLabels([
            "Nro. Empleado", "Nombre Completo", "DNI", "Cargo", 
            "Departamento", "Teléfono", "Estado", "Acciones"
        ])
        
        # Configurar tabla
        self.tabla_empleados.setAlternatingRowColors(True)
        self.tabla_empleados.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_empleados.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_empleados.horizontalHeader().setStretchLastSection(True)
        self.tabla_empleados.verticalHeader().setVisible(False)
        self.tabla_empleados.itemSelectionChanged.connect(self.on_empleado_seleccionado)
        
        self.tabla_empleados.setStyleSheet("""
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
        
        left_layout.addWidget(self.tabla_empleados)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        self.btn_nuevo = QPushButton("➕ Nuevo Empleado")
        self.btn_nuevo.clicked.connect(self.nuevo_empleado)
        self.btn_nuevo.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.editar_empleado)
        self.btn_editar.setEnabled(False)
        
        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_empleado)
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
        self.btn_actualizar.clicked.connect(self.cargar_empleados)
        
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
        
        # Foto y nombre
        foto_nombre_layout = QHBoxLayout()
        
        self.foto_label = QLabel()
        self.foto_label.setFixedSize(120, 120)
        self.foto_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 60px;
                background-color: #f0f0f0;
            }
        """)
        self.foto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.foto_label.setText("📷")
        self.foto_label.setScaledContents(True)
        
        info_basica = QVBoxLayout()
        self.nombre_completo_label = QLabel("Seleccione un empleado")
        self.nombre_completo_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.cargo_label = QLabel("")
        self.cargo_label.setStyleSheet("font-size: 16px; color: #666;")
        self.departamento_label = QLabel("")
        self.departamento_label.setStyleSheet("font-size: 14px; color: #888;")
        
        info_basica.addWidget(self.nombre_completo_label)
        info_basica.addWidget(self.cargo_label)
        info_basica.addWidget(self.departamento_label)
        info_basica.addStretch()
        
        foto_nombre_layout.addWidget(self.foto_label)
        foto_nombre_layout.addLayout(info_basica)
        foto_nombre_layout.addStretch()
        
        detalles_layout.addLayout(foto_nombre_layout)
        
        # Tabs con información detallada
        self.detalles_tabs = QTabWidget()
        
        # Tab de información personal
        personal_tab = QWidget()
        personal_layout = QFormLayout()
        
        self.dni_label = QLabel("-")
        personal_layout.addRow("DNI:", self.dni_label)
        
        self.email_label = QLabel("-")
        personal_layout.addRow("Email:", self.email_label)
        
        self.telefono_label = QLabel("-")
        personal_layout.addRow("Teléfono:", self.telefono_label)
        
        self.direccion_label = QLabel("-")
        self.direccion_label.setWordWrap(True)
        personal_layout.addRow("Dirección:", self.direccion_label)
        
        self.edad_label = QLabel("-")
        personal_layout.addRow("Edad:", self.edad_label)
        
        personal_tab.setLayout(personal_layout)
        self.detalles_tabs.addTab(personal_tab, "Personal")
        
        # Tab de información laboral
        laboral_tab = QWidget()
        laboral_layout = QFormLayout()
        
        self.numero_empleado_label = QLabel("-")
        laboral_layout.addRow("Nro. Empleado:", self.numero_empleado_label)
        
        self.fecha_ingreso_label = QLabel("-")
        laboral_layout.addRow("Fecha Ingreso:", self.fecha_ingreso_label)
        
        self.antiguedad_label = QLabel("-")
        laboral_layout.addRow("Antigüedad:", self.antiguedad_label)
        
        self.tipo_contrato_label = QLabel("-")
        laboral_layout.addRow("Tipo Contrato:", self.tipo_contrato_label)
        
        self.horario_label = QLabel("-")
        laboral_layout.addRow("Horario:", self.horario_label)
        
        laboral_tab.setLayout(laboral_layout)
        self.detalles_tabs.addTab(laboral_tab, "Laboral")
        
        # Tab de asistencia
        asistencia_tab = QWidget()
        asistencia_layout = QVBoxLayout()
        
        self.btn_marcar_entrada = QPushButton("🟢 Marcar Entrada")
        self.btn_marcar_entrada.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_marcar_entrada.clicked.connect(self.marcar_entrada)
        
        self.btn_marcar_salida = QPushButton("🔴 Marcar Salida")
        self.btn_marcar_salida.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.btn_marcar_salida.clicked.connect(self.marcar_salida)
        
        asistencia_layout.addWidget(self.btn_marcar_entrada)
        asistencia_layout.addWidget(self.btn_marcar_salida)
        
        # Resumen de asistencia
        self.asistencia_resumen = QLabel("Cargando asistencia...")
        self.asistencia_resumen.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        asistencia_layout.addWidget(self.asistencia_resumen)
        
        asistencia_layout.addStretch()
        asistencia_tab.setLayout(asistencia_layout)
        self.detalles_tabs.addTab(asistencia_tab, "Asistencia")
        
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
    
    def cargar_empleados(self):
        """Carga la lista de empleados desde el servidor"""
        try:
            response = self.api_client.get("/empleados")
            if response and 'items' in response:
                self.empleados = response['items']
                self.actualizar_tabla()
                self.actualizar_estadisticas()
            else:
                QMessageBox.warning(self, "Advertencia", "No se pudieron cargar los empleados")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar empleados: {str(e)}")
    
    def actualizar_tabla(self):
        """Actualiza la tabla con los empleados"""
        self.tabla_empleados.setRowCount(len(self.empleados))
        
        for i, empleado in enumerate(self.empleados):
            # Número de empleado
            self.tabla_empleados.setItem(i, 0, QTableWidgetItem(empleado.get('numero_empleado', '')))
            
            # Nombre completo
            nombre_completo = f"{empleado.get('nombre', '')} {empleado.get('apellido', '')}"
            self.tabla_empleados.setItem(i, 1, QTableWidgetItem(nombre_completo))
            
            # DNI
            self.tabla_empleados.setItem(i, 2, QTableWidgetItem(empleado.get('dni', '')))
            
            # Cargo
            self.tabla_empleados.setItem(i, 3, QTableWidgetItem(empleado.get('cargo', '')))
            
            # Departamento
            self.tabla_empleados.setItem(i, 4, QTableWidgetItem(empleado.get('departamento', '')))
            
            # Teléfono
            self.tabla_empleados.setItem(i, 5, QTableWidgetItem(empleado.get('telefono', '')))
            
            # Estado
            estado = empleado.get('estado', 'Activo')
            estado_item = QTableWidgetItem(estado)
            if estado == 'Activo':
                estado_item.setForeground(QColor('#4CAF50'))
            else:
                estado_item.setForeground(QColor('#f44336'))
            self.tabla_empleados.setItem(i, 6, estado_item)
            
            # Botón de acciones
            acciones_widget = QWidget()
            acciones_layout = QHBoxLayout()
            acciones_layout.setContentsMargins(5, 5, 5, 5)
            
            btn_ver = QPushButton("👁")
            btn_ver.setToolTip("Ver detalles")
            btn_ver.clicked.connect(lambda checked, row=i: self.ver_detalles_empleado(row))
            btn_ver.setMaximumWidth(30)
            
            acciones_layout.addWidget(btn_ver)
            acciones_widget.setLayout(acciones_layout)
            
            self.tabla_empleados.setCellWidget(i, 7, acciones_widget)
        
        # Ajustar columnas
        self.tabla_empleados.resizeColumnsToContents()
    
    def actualizar_estadisticas(self):
        """Actualiza las estadísticas mostradas"""
        total = len(self.empleados)
        activos = sum(1 for e in self.empleados if e.get('estado') == 'Activo')
        inactivos = total - activos
        
        self.stats_label.setText(f"Total: {total} | Activos: {activos} | Inactivos: {inactivos}")
    
    def filtrar_empleados(self):
        """Filtra los empleados según los criterios seleccionados"""
        texto_busqueda = self.buscar_input.text().lower()
        depto_filtro = self.filtro_depto.currentText()
        estado_filtro = self.filtro_estado.currentText()
        
        for i in range(self.tabla_empleados.rowCount()):
            mostrar = True
            
            # Filtro por texto
            if texto_busqueda:
                nombre = self.tabla_empleados.item(i, 1).text().lower()
                dni = self.tabla_empleados.item(i, 2).text().lower()
                cargo = self.tabla_empleados.item(i, 3).text().lower()
                
                if texto_busqueda not in nombre and texto_busqueda not in dni and texto_busqueda not in cargo:
                    mostrar = False
            
            # Filtro por departamento
            if depto_filtro != "Todos los departamentos":
                depto = self.tabla_empleados.item(i, 4).text()
                if depto != depto_filtro:
                    mostrar = False
            
            # Filtro por estado
            if estado_filtro != "Todos":
                estado = self.tabla_empleados.item(i, 6).text()
                if estado_filtro == "Activos" and estado != "Activo":
                    mostrar = False
                elif estado_filtro == "Inactivos" and estado == "Activo":
                    mostrar = False
            
            self.tabla_empleados.setRowHidden(i, not mostrar)
    
    def on_empleado_seleccionado(self):
        """Maneja la selección de un empleado en la tabla"""
        current_row = self.tabla_empleados.currentRow()
        if 0 <= current_row < len(self.empleados):
            self.empleado_seleccionado = self.empleados[current_row]
            self.btn_editar.setEnabled(True)
            self.btn_eliminar.setEnabled(True)
            self.mostrar_detalles_empleado()
        else:
            self.empleado_seleccionado = None
            self.btn_editar.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
    
    def mostrar_detalles_empleado(self):
        """Muestra los detalles del empleado seleccionado"""
        if not self.empleado_seleccionado:
            return
        
        # Información básica
        self.nombre_completo_label.setText(self.empleado_seleccionado.get('nombre_completo', ''))
        self.cargo_label.setText(self.empleado_seleccionado.get('cargo', ''))
        self.departamento_label.setText(self.empleado_seleccionado.get('departamento', ''))
        
        # Información personal
        self.dni_label.setText(self.empleado_seleccionado.get('dni', '-'))
        self.email_label.setText(self.empleado_seleccionado.get('email', '-'))
        self.telefono_label.setText(self.empleado_seleccionado.get('telefono', '-'))
        self.direccion_label.setText(self.empleado_seleccionado.get('direccion', '-'))
        self.edad_label.setText(f"{self.empleado_seleccionado.get('edad', '-')} años")
        
        # Información laboral
        self.numero_empleado_label.setText(self.empleado_seleccionado.get('numero_empleado', '-'))
        self.fecha_ingreso_label.setText(self.empleado_seleccionado.get('fecha_ingreso', '-'))
        self.antiguedad_label.setText(f"{self.empleado_seleccionado.get('antiguedad_anos', 0)} años")
        self.tipo_contrato_label.setText(self.empleado_seleccionado.get('tipo_contrato', '-'))
        
        # Horario
        entrada = self.empleado_seleccionado.get('horario_entrada', '')
        salida = self.empleado_seleccionado.get('horario_salida', '')
        dias = self.empleado_seleccionado.get('dias_trabajo', '')
        if entrada and salida:
            self.horario_label.setText(f"{entrada} - {salida} ({dias})")
        else:
            self.horario_label.setText("-")
        
        # Cargar asistencia
        self.cargar_asistencia_empleado()
    
    def cargar_asistencia_empleado(self):
        """Carga el resumen de asistencia del empleado"""
        if not self.empleado_seleccionado:
            return
        
        try:
            # Obtener fecha actual
            hoy = date.today()
            inicio_mes = date(hoy.year, hoy.month, 1)
            
            response = self.api_client.get(
                f"/api/empleados/asistencia/reporte",
                params={
                    'empleado_id': self.empleado_seleccionado['id'],
                    'fecha_inicio': inicio_mes.isoformat(),
                    'fecha_fin': hoy.isoformat()
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                resumen = f"""
                Resumen del mes actual:
                • Días trabajados: {data.get('total_dias', 0)}
                • Horas totales: {data.get('total_horas', 0):.1f}
                • Horas extra: {data.get('total_horas_extra', 0):.1f}
                • Promedio diario: {data.get('promedio_horas_dia', 0):.1f} horas
                """
                self.asistencia_resumen.setText(resumen)
            else:
                self.asistencia_resumen.setText("No se pudo cargar la asistencia")
        except Exception as e:
            self.asistencia_resumen.setText(f"Error: {str(e)}")
    
    def ver_detalles_empleado(self, row):
        """Muestra los detalles de un empleado específico"""
        self.tabla_empleados.selectRow(row)
    
    def nuevo_empleado(self):
        """Abre el diálogo para crear un nuevo empleado"""
        dialog = EmpleadoDialog(self.api_client, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            empleado_data = dialog.get_empleado_data()
            self.crear_empleado(empleado_data)
    
    def crear_empleado(self, empleado_data):
        """Crea un nuevo empleado"""
        try:
            response = self.api_client.post("/empleados", empleado_data)
            QMessageBox.information(self, "Éxito", "Empleado creado exitosamente")
            self.cargar_empleados()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al crear empleado: {str(e)}")
    
    def editar_empleado(self):
        """Abre el diálogo para editar el empleado seleccionado"""
        if not self.empleado_seleccionado:
            return
        
        dialog = EmpleadoDialog(self.api_client, self.empleado_seleccionado, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            empleado_data = dialog.get_empleado_data()
            self.actualizar_empleado(empleado_data)
    
    def actualizar_empleado(self, empleado_data):
        """Actualiza un empleado existente"""
        try:
            response = self.api_client.put(f"/empleados/{self.empleado_seleccionado['id']}", empleado_data)
            QMessageBox.information(self, "Éxito", "Empleado actualizado exitosamente")
            self.cargar_empleados()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar empleado: {str(e)}")
    
    def eliminar_empleado(self):
        """Marca un empleado como inactivo"""
        if not self.empleado_seleccionado:
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirmar eliminación",
            f"¿Está seguro de marcar como inactivo al empleado {self.empleado_seleccionado.get('nombre_completo', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                response = self.api_client.delete(f"/empleados/{self.empleado_seleccionado['id']}")
                QMessageBox.information(self, "Éxito", "Empleado marcado como inactivo")
                self.cargar_empleados()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar empleado: {str(e)}")
    
    def marcar_entrada(self):
        """Marca la entrada del empleado seleccionado"""
        if not self.empleado_seleccionado:
            QMessageBox.warning(self, "Advertencia", "Seleccione un empleado")
            return
        
        try:
            asistencia_data = {
                'empleado_id': self.empleado_seleccionado['id'],
                'fecha': date.today().isoformat(),
                'hora_entrada': datetime.now().isoformat()
            }
            
            response = self.api_client.post("/empleados/asistencia/entrada", asistencia_data)
            QMessageBox.information(self, "Éxito", "Entrada registrada exitosamente")
            self.cargar_asistencia_empleado()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al registrar entrada: {str(e)}")
    
    def marcar_salida(self):
        """Marca la salida del empleado seleccionado"""
        if not self.empleado_seleccionado:
            QMessageBox.warning(self, "Advertencia", "Seleccione un empleado")
            return
        
        # TODO: Implementar búsqueda de asistencia abierta y marcar salida
        QMessageBox.information(self, "Info", "Función de marcar salida en desarrollo") 