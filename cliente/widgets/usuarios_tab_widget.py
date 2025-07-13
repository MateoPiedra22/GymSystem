"""
Widget para la gestión de usuarios del gimnasio
Incluye creación, edición, eliminación y búsqueda de usuarios
"""

from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QMessageBox, QHeaderView, QAbstractItemView, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox, QCheckBox,
    QTabWidget, QDateEdit, QGroupBox, QRadioButton, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QDate
from PyQt6.QtGui import QFont, QIcon, QColor, QPixmap

from api_client import ApiClient

class UsuariosLoadWorker(QThread):
    """Worker para cargar usuarios en background"""
    
    usuarios_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_client: ApiClient, filtro: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.api_client = api_client
        self.filtro = filtro or {}
        
    def run(self):
        """Carga la lista de usuarios"""
        try:
            usuarios = self.api_client.get_usuarios(**self.filtro)
            self.usuarios_loaded.emit(usuarios)
        except Exception as e:
            self.error_occurred.emit(str(e))

class NuevoUsuarioDialog(QDialog):
    """Dialog para crear o editar un usuario"""
    
    def __init__(self, parent=None, api_client: ApiClient = None, usuario: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.api_client = api_client
        self.usuario = usuario
        self.setWindowTitle("Nuevo Usuario" if not usuario else "Editar Usuario")
        self.resize(500, 600)
        self.setupUI()
        
    def setupUI(self):
        """Configura la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Pestañas para organizar los datos
        self.tab_widget = QTabWidget()
        
        # Pestaña de datos personales
        self.create_personal_tab()
        
        # Pestaña de membresía
        self.create_membership_tab()
        
        # Pestaña de datos médicos
        self.create_medical_tab()
        
        # Pestaña de notas
        self.create_notes_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Botones de acción
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
    
    def create_personal_tab(self):
        """Crea la pestaña de datos personales"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form = QFormLayout()
        
        # Nombre
        self.input_nombre = QLineEdit()
        if self.usuario:
            self.input_nombre.setText(self.usuario.get("nombre", ""))
        form.addRow("Nombre:", self.input_nombre)
        
        # Apellido
        self.input_apellido = QLineEdit()
        if self.usuario:
            self.input_apellido.setText(self.usuario.get("apellido", ""))
        form.addRow("Apellido:", self.input_apellido)
        
        # DNI/Identificación
        self.input_dni = QLineEdit()
        if self.usuario:
            self.input_dni.setText(self.usuario.get("dni", ""))
        form.addRow("DNI/ID:", self.input_dni)
        
        # Fecha de nacimiento
        self.date_nacimiento = QDateEdit()
        self.date_nacimiento.setCalendarPopup(True)
        if self.usuario and self.usuario.get("fecha_nacimiento"):
            fecha = QDate.fromString(self.usuario.get("fecha_nacimiento"), "yyyy-MM-dd")
            self.date_nacimiento.setDate(fecha)
        else:
            self.date_nacimiento.setDate(QDate.currentDate().addYears(-20))
        form.addRow("Fecha de nacimiento:", self.date_nacimiento)
        
        # Género
        self.combo_genero = QComboBox()
        self.combo_genero.addItem("Masculino", "M")
        self.combo_genero.addItem("Femenino", "F")
        self.combo_genero.addItem("Otro", "O")
        if self.usuario and self.usuario.get("genero"):
            index = self.combo_genero.findData(self.usuario.get("genero"))
            if index >= 0:
                self.combo_genero.setCurrentIndex(index)
        form.addRow("Género:", self.combo_genero)
        
        # Teléfono
        self.input_telefono = QLineEdit()
        if self.usuario:
            self.input_telefono.setText(self.usuario.get("telefono", ""))
        form.addRow("Teléfono:", self.input_telefono)
        
        # Email
        self.input_email = QLineEdit()
        if self.usuario:
            self.input_email.setText(self.usuario.get("email", ""))
        form.addRow("Email:", self.input_email)
        
        # Dirección
        self.input_direccion = QLineEdit()
        if self.usuario:
            self.input_direccion.setText(self.usuario.get("direccion", ""))
        form.addRow("Dirección:", self.input_direccion)
        
        # Ciudad
        self.input_ciudad = QLineEdit()
        if self.usuario:
            self.input_ciudad.setText(self.usuario.get("ciudad", ""))
        form.addRow("Ciudad:", self.input_ciudad)
        
        # CP
        self.input_cp = QLineEdit()
        if self.usuario:
            self.input_cp.setText(self.usuario.get("codigo_postal", ""))
        form.addRow("Código Postal:", self.input_cp)
        
        layout.addLayout(form)
        
        # Foto de perfil (simulado - en implementación real permitiría seleccionar archivo)
        photo_frame = QFrame()
        photo_frame.setFrameShape(QFrame.Shape.StyledPanel)
        photo_layout = QHBoxLayout(photo_frame)
        
        photo_label = QLabel("Foto de perfil:")
        
        # Placeholder para la foto
        self.photo_preview = QLabel()
        self.photo_preview.setFixedSize(100, 100)
        self.photo_preview.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        
        btn_select_photo = QPushButton("Seleccionar...")
        btn_select_photo.clicked.connect(self.select_photo)
        
        photo_layout.addWidget(photo_label)
        photo_layout.addWidget(self.photo_preview)
        photo_layout.addWidget(btn_select_photo)
        photo_layout.addStretch()
        
        layout.addWidget(photo_frame)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Datos Personales")
    
    def create_membership_tab(self):
        """Crea la pestaña de membresía"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form = QFormLayout()
        
        # Usuario del sistema
        self.input_username = QLineEdit()
        if self.usuario:
            self.input_username.setText(self.usuario.get("username", ""))
        form.addRow("Usuario:", self.input_username)
        
        # Contraseña (solo para nuevos usuarios)
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        # Solo requerida para nuevos usuarios
        if not self.usuario:
            form.addRow("Contraseña:", self.input_password)
        
        # Tipo de membresía
        self.combo_plan = QComboBox()
        self.combo_plan.addItem("Básico", "basico")
        self.combo_plan.addItem("Estándar", "estandar")
        self.combo_plan.addItem("Premium", "premium")
        self.combo_plan.addItem("Entrenador", "entrenador")
        self.combo_plan.addItem("Administrador", "admin")
        if self.usuario and self.usuario.get("tipo_plan"):
            index = self.combo_plan.findData(self.usuario.get("tipo_plan"))
            if index >= 0:
                self.combo_plan.setCurrentIndex(index)
        form.addRow("Plan:", self.combo_plan)
        
        # Fecha de inicio
        self.date_inicio = QDateEdit()
        self.date_inicio.setCalendarPopup(True)
        if self.usuario and self.usuario.get("fecha_inicio"):
            fecha = QDate.fromString(self.usuario.get("fecha_inicio"), "yyyy-MM-dd")
            self.date_inicio.setDate(fecha)
        else:
            self.date_inicio.setDate(QDate.currentDate())
        form.addRow("Fecha de inicio:", self.date_inicio)
        
        # Fecha de vencimiento
        self.date_vencimiento = QDateEdit()
        self.date_vencimiento.setCalendarPopup(True)
        if self.usuario and self.usuario.get("fecha_vencimiento"):
            fecha = QDate.fromString(self.usuario.get("fecha_vencimiento"), "yyyy-MM-dd")
            self.date_vencimiento.setDate(fecha)
        else:
            self.date_vencimiento.setDate(QDate.currentDate().addMonths(1))
        form.addRow("Fecha de vencimiento:", self.date_vencimiento)
        
        # Estado
        self.combo_estado = QComboBox()
        self.combo_estado.addItem("Activo", "activo")
        self.combo_estado.addItem("Inactivo", "inactivo")
        self.combo_estado.addItem("Suspendido", "suspendido")
        if self.usuario and self.usuario.get("estado"):
            index = self.combo_estado.findData(self.usuario.get("estado"))
            if index >= 0:
                self.combo_estado.setCurrentIndex(index)
        form.addRow("Estado:", self.combo_estado)
        
        # Es administrador
        self.check_admin = QCheckBox()
        if self.usuario:
            self.check_admin.setChecked(self.usuario.get("es_admin", False))
        form.addRow("Es administrador:", self.check_admin)
        
        layout.addLayout(form)
        
        # Grupo de accesos permitidos
        access_group = QGroupBox("Accesos Permitidos")
        access_layout = QVBoxLayout(access_group)
        
        self.check_access_clases = QCheckBox("Clases")
        self.check_access_rutinas = QCheckBox("Rutinas")
        self.check_access_pagos = QCheckBox("Pagos")
        self.check_access_reportes = QCheckBox("Reportes")
        
        if self.usuario:
            accesos = self.usuario.get("accesos", {})
            self.check_access_clases.setChecked(accesos.get("clases", True))
            self.check_access_rutinas.setChecked(accesos.get("rutinas", True))
            self.check_access_pagos.setChecked(accesos.get("pagos", True))
            self.check_access_reportes.setChecked(accesos.get("reportes", False))
        else:
            # Valores predeterminados para nuevo usuario
            self.check_access_clases.setChecked(True)
            self.check_access_rutinas.setChecked(True)
            self.check_access_pagos.setChecked(True)
            self.check_access_reportes.setChecked(False)
        
        access_layout.addWidget(self.check_access_clases)
        access_layout.addWidget(self.check_access_rutinas)
        access_layout.addWidget(self.check_access_pagos)
        access_layout.addWidget(self.check_access_reportes)
        
        layout.addWidget(access_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Membresía")
    
    def create_medical_tab(self):
        """Crea la pestaña de datos médicos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form = QFormLayout()
        
        # Altura
        height_layout = QHBoxLayout()
        self.spin_altura = QSpinBox()
        self.spin_altura.setRange(100, 250)
        if self.usuario and self.usuario.get("altura"):
            self.spin_altura.setValue(self.usuario.get("altura"))
        else:
            self.spin_altura.setValue(170)
        self.spin_altura.setSuffix(" cm")
        height_layout.addWidget(self.spin_altura)
        height_layout.addStretch()
        form.addRow("Altura:", height_layout)
        
        # Peso
        weight_layout = QHBoxLayout()
        self.spin_peso = QSpinBox()
        self.spin_peso.setRange(30, 200)
        if self.usuario and self.usuario.get("peso"):
            self.spin_peso.setValue(self.usuario.get("peso"))
        else:
            self.spin_peso.setValue(70)
        self.spin_peso.setSuffix(" kg")
        weight_layout.addWidget(self.spin_peso)
        weight_layout.addStretch()
        form.addRow("Peso:", weight_layout)
        
        # Condición física
        self.combo_condicion = QComboBox()
        self.combo_condicion.addItem("Principiante", "principiante")
        self.combo_condicion.addItem("Intermedio", "intermedio")
        self.combo_condicion.addItem("Avanzado", "avanzado")
        if self.usuario and self.usuario.get("condicion_fisica"):
            index = self.combo_condicion.findData(self.usuario.get("condicion_fisica"))
            if index >= 0:
                self.combo_condicion.setCurrentIndex(index)
        form.addRow("Condición física:", self.combo_condicion)
        
        # Enfermedades
        self.input_enfermedades = QLineEdit()
        if self.usuario:
            self.input_enfermedades.setText(self.usuario.get("enfermedades", ""))
        form.addRow("Enfermedades:", self.input_enfermedades)
        
        # Alergias
        self.input_alergias = QLineEdit()
        if self.usuario:
            self.input_alergias.setText(self.usuario.get("alergias", ""))
        form.addRow("Alergias:", self.input_alergias)
        
        # Lesiones
        self.input_lesiones = QLineEdit()
        if self.usuario:
            self.input_lesiones.setText(self.usuario.get("lesiones", ""))
        form.addRow("Lesiones:", self.input_lesiones)
        
        # Contacto de emergencia
        self.input_contacto_emergencia = QLineEdit()
        if self.usuario:
            self.input_contacto_emergencia.setText(self.usuario.get("contacto_emergencia", ""))
        form.addRow("Contacto de emergencia:", self.input_contacto_emergencia)
        
        # Teléfono de emergencia
        self.input_telefono_emergencia = QLineEdit()
        if self.usuario:
            self.input_telefono_emergencia.setText(self.usuario.get("telefono_emergencia", ""))
        form.addRow("Teléfono de emergencia:", self.input_telefono_emergencia)
        
        layout.addLayout(form)
        
        # Grupo de objetivos
        goals_group = QGroupBox("Objetivos")
        goals_layout = QVBoxLayout(goals_group)
        
        self.rb_goal_weight_loss = QRadioButton("Pérdida de peso")
        self.rb_goal_muscle = QRadioButton("Aumento de masa muscular")
        self.rb_goal_fitness = QRadioButton("Mejora de estado físico")
        self.rb_goal_health = QRadioButton("Salud general")
        self.rb_goal_other = QRadioButton("Otro")
        
        # Establecer objetivo seleccionado
        if self.usuario and self.usuario.get("objetivo"):
            objetivo = self.usuario.get("objetivo")
            if objetivo == "perdida_peso":
                self.rb_goal_weight_loss.setChecked(True)
            elif objetivo == "masa_muscular":
                self.rb_goal_muscle.setChecked(True)
            elif objetivo == "estado_fisico":
                self.rb_goal_fitness.setChecked(True)
            elif objetivo == "salud":
                self.rb_goal_health.setChecked(True)
            else:
                self.rb_goal_other.setChecked(True)
        else:
            self.rb_goal_fitness.setChecked(True)
        
        goals_layout.addWidget(self.rb_goal_weight_loss)
        goals_layout.addWidget(self.rb_goal_muscle)
        goals_layout.addWidget(self.rb_goal_fitness)
        goals_layout.addWidget(self.rb_goal_health)
        goals_layout.addWidget(self.rb_goal_other)
        
        layout.addWidget(goals_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Datos Médicos")
    
    def create_notes_tab(self):
        """Crea la pestaña de notas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Notas
        layout.addWidget(QLabel("Notas:"))
        self.text_notas = QTextEdit()
        if self.usuario:
            self.text_notas.setPlainText(self.usuario.get("notas", ""))
        layout.addWidget(self.text_notas)
        
        self.tab_widget.addTab(tab, "Notas")
    
    def select_photo(self):
        """Selecciona una foto de perfil (simulado)"""
        # En una implementación real, aquí abriríamos un diálogo para seleccionar archivo
        QMessageBox.information(
            self, 
            "Selección de Foto", 
            "En una implementación real, aquí se abriría un diálogo para seleccionar una imagen."
        )
    
    def accept(self) -> None:
        """Valida los datos antes de aceptar"""
        # Verificar campos obligatorios
        if not self.input_nombre.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "El nombre es obligatorio.")
            return
        
        if not self.input_apellido.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "El apellido es obligatorio.")
            return
        
        if not self.input_dni.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "El DNI/ID es obligatorio.")
            return
        
        if not self.input_username.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "El nombre de usuario es obligatorio.")
            return
        
        # Verificar contraseña para nuevos usuarios
        if not self.usuario and not self.input_password.text():
            QMessageBox.warning(self, "Datos incompletos", "La contraseña es obligatoria para nuevos usuarios.")
            return
        
        # Verificar fecha de vencimiento posterior a fecha de inicio
        if self.date_inicio.date() >= self.date_vencimiento.date():
            QMessageBox.warning(
                self, 
                "Fechas inválidas", 
                "La fecha de vencimiento debe ser posterior a la fecha de inicio."
            )
            return
        
        # Todos los campos validados, aceptar
        super().accept()
    
    def get_datos_usuario(self) -> Dict[str, Any]:
        """Obtiene los datos del formulario en formato para la API"""
        # Determinar objetivo
        objetivo = ""
        if self.rb_goal_weight_loss.isChecked():
            objetivo = "perdida_peso"
        elif self.rb_goal_muscle.isChecked():
            objetivo = "masa_muscular"
        elif self.rb_goal_fitness.isChecked():
            objetivo = "estado_fisico"
        elif self.rb_goal_health.isChecked():
            objetivo = "salud"
        else:
            objetivo = "otro"
        
        # Construir datos de accesos
        accesos = {
            "clases": self.check_access_clases.isChecked(),
            "rutinas": self.check_access_rutinas.isChecked(),
            "pagos": self.check_access_pagos.isChecked(),
            "reportes": self.check_access_reportes.isChecked()
        }
        
        # Construir objeto de usuario
        usuario = {
            "nombre": self.input_nombre.text().strip(),
            "apellido": self.input_apellido.text().strip(),
            "dni": self.input_dni.text().strip(),
            "fecha_nacimiento": self.date_nacimiento.date().toString("yyyy-MM-dd"),
            "genero": self.combo_genero.currentData(),
            "telefono": self.input_telefono.text().strip(),
            "email": self.input_email.text().strip(),
            "direccion": self.input_direccion.text().strip(),
            "ciudad": self.input_ciudad.text().strip(),
            "codigo_postal": self.input_cp.text().strip(),
            "username": self.input_username.text().strip(),
            "tipo_plan": self.combo_plan.currentData(),
            "fecha_inicio": self.date_inicio.date().toString("yyyy-MM-dd"),
            "fecha_vencimiento": self.date_vencimiento.date().toString("yyyy-MM-dd"),
            "estado": self.combo_estado.currentData(),
            "es_admin": self.check_admin.isChecked(),
            "accesos": accesos,
            "altura": self.spin_altura.value(),
            "peso": self.spin_peso.value(),
            "condicion_fisica": self.combo_condicion.currentData(),
            "enfermedades": self.input_enfermedades.text().strip(),
            "alergias": self.input_alergias.text().strip(),
            "lesiones": self.input_lesiones.text().strip(),
            "contacto_emergencia": self.input_contacto_emergencia.text().strip(),
            "telefono_emergencia": self.input_telefono_emergencia.text().strip(),
            "objetivo": objetivo,
            "notas": self.text_notas.toPlainText().strip()
        }
        
        # Agregar contraseña solo para nuevos usuarios
        if not self.usuario and self.input_password.text():
            usuario["password"] = self.input_password.text()
        
        # Si estamos editando, incluir ID
        if self.usuario and "id" in self.usuario:
            usuario["id"] = self.usuario["id"]
        
        return usuario

class UsuariosTabWidget(QWidget):
    """
    Widget para la pestaña de usuarios
    
    Permite gestionar (crear, editar, eliminar, buscar) usuarios del gimnasio.
    """
    
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self.usuarios = []
        self.setupUI()
        
    def setupUI(self):
        """Configura la interfaz de usuario del widget"""
        main_layout = QVBoxLayout(self)
        
        # Barra superior (título y botones)
        top_bar = QHBoxLayout()
        
        # Título
        title_label = QLabel("Gestión de Usuarios")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        # Botón para agregar usuario
        btn_add = QPushButton("Nuevo Usuario")
        btn_add.setIcon(QIcon("assets/add_user.png"))
        btn_add.clicked.connect(self.show_new_user_dialog)
        top_bar.addWidget(btn_add)
        
        # Botón para refrescar
        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setIcon(QIcon("assets/refresh.png"))
        btn_refresh.clicked.connect(self.cargar_usuarios)
        top_bar.addWidget(btn_refresh)
        
        main_layout.addLayout(top_bar)
        
        # Barra de búsqueda y filtros
        filter_bar = QHBoxLayout()
        
        filter_bar.addWidget(QLabel("Buscar:"))
        
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Buscar por nombre, apellido, email o DNI...")
        self.input_search.textChanged.connect(self.aplicar_filtros)
        filter_bar.addWidget(self.input_search)
        
        filter_bar.addWidget(QLabel("Estado:"))
        
        self.combo_filter_estado = QComboBox()
        self.combo_filter_estado.addItem("Todos", None)
        self.combo_filter_estado.addItem("Activo", "activo")
        self.combo_filter_estado.addItem("Inactivo", "inactivo")
        self.combo_filter_estado.addItem("Suspendido", "suspendido")
        self.combo_filter_estado.currentIndexChanged.connect(self.aplicar_filtros)
        filter_bar.addWidget(self.combo_filter_estado)
        
        filter_bar.addWidget(QLabel("Plan:"))
        
        self.combo_filter_plan = QComboBox()
        self.combo_filter_plan.addItem("Todos", None)
        self.combo_filter_plan.addItem("Básico", "basico")
        self.combo_filter_plan.addItem("Estándar", "estandar")
        self.combo_filter_plan.addItem("Premium", "premium")
        self.combo_filter_plan.addItem("Entrenador", "entrenador")
        self.combo_filter_plan.currentIndexChanged.connect(self.aplicar_filtros)
        filter_bar.addWidget(self.combo_filter_plan)
        
        main_layout.addLayout(filter_bar)
        
        # Tabla de usuarios
        self.table_usuarios = QTableWidget()
        self.table_usuarios.setColumnCount(9)
        self.table_usuarios.setHorizontalHeaderLabels([
            "ID", "Nombre", "Apellido", "DNI", "Email", "Teléfono", "Plan", "Estado", "Acciones"
        ])
        self.table_usuarios.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_usuarios.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_usuarios.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_usuarios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_usuarios.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.table_usuarios.verticalHeader().setVisible(False)
        
        main_layout.addWidget(self.table_usuarios)
        
        # Barra de estado
        status_bar = QHBoxLayout()
        
        self.lbl_total = QLabel("Total: 0 usuarios")
        status_bar.addWidget(self.lbl_total)
        
        status_bar.addStretch()
        
        self.lbl_filtrados = QLabel("Mostrando: 0 usuarios")
        status_bar.addWidget(self.lbl_filtrados)
        
        main_layout.addLayout(status_bar)
        
        # Cargar datos iniciales
        self.cargar_usuarios()
    
    def cargar_usuarios(self):
        """Carga la lista de usuarios desde la API"""
        # Mostrar indicador de carga
        self.table_usuarios.setRowCount(0)
        self.lbl_total.setText("Cargando usuarios...")
        self.lbl_filtrados.setText("")
        
        # Crear worker para cargar usuarios en background
        self.load_worker = UsuariosLoadWorker(self.api_client)
        self.load_worker.usuarios_loaded.connect(self.on_usuarios_loaded)
        self.load_worker.error_occurred.connect(self.on_load_error)
        self.load_worker.start()
    
    def on_usuarios_loaded(self, usuarios: List[Dict[str, Any]]):
        """Callback cuando se cargan los usuarios exitosamente"""
        self.usuarios = usuarios
        self.actualizar_tabla()
        self.lbl_total.setText(f"Total: {len(usuarios)} usuarios")
        self.lbl_filtrados.setText("")
    
    def on_load_error(self, error_message: str):
        """Callback cuando hay error al cargar usuarios"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Error", f"Error al cargar usuarios: {error_message}")
        self.lbl_total.setText("Error al cargar usuarios")
        self.lbl_filtrados.setText("")
    
    def cargar_usuarios_sync(self):
        """Carga usuarios de forma síncrona (fallback)"""
        try:
            # Llamada directa a la API
            response = self.api_client._make_request('GET', '/usuarios')
            if response and 'data' in response:
                self.usuarios = response['data']
                self.actualizar_tabla()
                self.lbl_total.setText(f"Total: {len(self.usuarios)} usuarios")
            else:
                self.usuarios = []
                self.lbl_total.setText("No se pudieron cargar usuarios")
        except Exception as e:
            logger.error(f"Error cargando usuarios: {e}")
            self.usuarios = []
            self.lbl_total.setText("Error al cargar usuarios")
    
    def actualizar_tabla(self, filtrados: Optional[List[Dict[str, Any]]] = None):
        """
        Actualiza la tabla con los datos de usuarios
        
        Args:
            filtrados: Lista opcional de usuarios filtrados para mostrar
        """
        # Usar la lista filtrada si se proporciona, de lo contrario usar todos
        datos = filtrados if filtrados is not None else self.usuarios
        
        # Limpiar tabla
        self.table_usuarios.setRowCount(0)
        
        # Llenar con datos
        for row_idx, usuario in enumerate(datos):
            self.table_usuarios.insertRow(row_idx)
            
            # Columnas básicas
            self.table_usuarios.setItem(row_idx, 0, QTableWidgetItem(str(usuario.get("id", ""))))
            self.table_usuarios.setItem(row_idx, 1, QTableWidgetItem(usuario.get("nombre", "")))
            self.table_usuarios.setItem(row_idx, 2, QTableWidgetItem(usuario.get("apellido", "")))
            self.table_usuarios.setItem(row_idx, 3, QTableWidgetItem(usuario.get("dni", "")))
            self.table_usuarios.setItem(row_idx, 4, QTableWidgetItem(usuario.get("email", "")))
            self.table_usuarios.setItem(row_idx, 5, QTableWidgetItem(usuario.get("telefono", "")))
            
            # Plan con formato amigable
            plan_item = QTableWidgetItem(self.formato_plan(usuario.get("tipo_plan", "")))
            self.table_usuarios.setItem(row_idx, 6, plan_item)
            
            # Estado con formato y color
            estado_item = QTableWidgetItem(self.formato_estado(usuario.get("estado", "")))
            if usuario.get("estado") == "activo":
                estado_item.setBackground(QColor(200, 255, 200))  # Verde claro
            elif usuario.get("estado") == "suspendido":
                estado_item.setBackground(QColor(255, 200, 200))  # Rojo claro
            elif usuario.get("estado") == "inactivo":
                estado_item.setBackground(QColor(240, 240, 240))  # Gris claro
            self.table_usuarios.setItem(row_idx, 7, estado_item)
            
            # Botones de acción
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            # Botón editar
            btn_edit = QPushButton()
            btn_edit.setIcon(QIcon("assets/edit.png"))
            btn_edit.setToolTip("Editar usuario")
            btn_edit.setMaximumWidth(30)
            btn_edit.clicked.connect(lambda checked, u=usuario: self.edit_usuario(u))
            action_layout.addWidget(btn_edit)
            
            # Botón eliminar
            btn_delete = QPushButton()
            btn_delete.setIcon(QIcon("assets/delete.png"))
            btn_delete.setToolTip("Eliminar usuario")
            btn_delete.setMaximumWidth(30)
            btn_delete.clicked.connect(lambda checked, u=usuario: self.delete_usuario(u))
            action_layout.addWidget(btn_delete)
            
            # Botón ver detalles
            btn_view = QPushButton()
            btn_view.setIcon(QIcon("assets/view.png"))
            btn_view.setToolTip("Ver detalles")
            btn_view.setMaximumWidth(30)
            btn_view.clicked.connect(lambda checked, u=usuario: self.view_usuario(u))
            action_layout.addWidget(btn_view)
            
            action_layout.addStretch()
            
            self.table_usuarios.setCellWidget(row_idx, 8, action_widget)
        
        # Actualizar contadores
        self.lbl_total.setText(f"Total: {len(self.usuarios)} usuarios")
        self.lbl_filtrados.setText(f"Mostrando: {len(datos)} usuarios")
    
    def formato_plan(self, plan: str) -> str:
        """Formatea el tipo de plan para mostrar"""
        if plan == "basico":
            return "Básico"
        elif plan == "estandar":
            return "Estándar"
        elif plan == "premium":
            return "Premium"
        elif plan == "entrenador":
            return "Entrenador"
        elif plan == "admin":
            return "Administrador"
        else:
            return plan.capitalize()
    
    def formato_estado(self, estado: str) -> str:
        """Formatea el estado para mostrar"""
        if estado == "activo":
            return "Activo"
        elif estado == "inactivo":
            return "Inactivo"
        elif estado == "suspendido":
            return "Suspendido"
        else:
            return estado.capitalize()
    
    def aplicar_filtros(self):
        """Aplica los filtros seleccionados a la lista de usuarios"""
        texto_busqueda = self.input_search.text().lower()
        estado_filtro = self.combo_filter_estado.currentData()
        plan_filtro = self.combo_filter_plan.currentData()
        
        filtrados = []
        
        for usuario in self.usuarios:
            # Filtro de texto
            if texto_busqueda:
                matches = (
                    texto_busqueda in usuario.get("nombre", "").lower() or
                    texto_busqueda in usuario.get("apellido", "").lower() or
                    texto_busqueda in usuario.get("email", "").lower() or
                    texto_busqueda in usuario.get("dni", "").lower()
                )
                if not matches:
                    continue
            
            # Filtro de estado
            if estado_filtro and usuario.get("estado") != estado_filtro:
                continue
            
            # Filtro de plan
            if plan_filtro and usuario.get("tipo_plan") != plan_filtro:
                continue
            
            # Si pasa todos los filtros, incluir
            filtrados.append(usuario)
        
        # Actualizar tabla con resultados filtrados
        self.actualizar_tabla(filtrados)
    
    def show_new_user_dialog(self):
        """Muestra el diálogo para crear un nuevo usuario"""
        dialog = NuevoUsuarioDialog(self, self.api_client)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Obtener datos del formulario
            datos_usuario = dialog.get_datos_usuario()
            
            # En una implementación real, enviaríamos a la API
            # api_client.create_usuario(datos_usuario)
            
            # Simular creación exitosa
            # Asignar ID (en una implementación real vendría de la API)
            next_id = max([u.get("id", 0) for u in self.usuarios], default=0) + 1
            datos_usuario["id"] = next_id
            
            # Agregar a la lista
            self.usuarios.append(datos_usuario)
            
            # Actualizar tabla
            self.actualizar_tabla()
            
            QMessageBox.information(self, "Usuario Creado", "El usuario ha sido creado correctamente.")
    
    def edit_usuario(self, usuario: Dict[str, Any]):
        """Muestra el diálogo para editar un usuario"""
        dialog = NuevoUsuarioDialog(self, self.api_client, usuario)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Obtener datos actualizados
            datos_usuario = dialog.get_datos_usuario()
            
            # En una implementación real, enviaríamos a la API
            # api_client.update_usuario(datos_usuario)
            
            # Simular actualización exitosa
            # Actualizar en la lista local
            for i, u in enumerate(self.usuarios):
                if u.get("id") == usuario.get("id"):
                    self.usuarios[i] = datos_usuario
                    break
            
            # Actualizar tabla
            self.actualizar_tabla()
            
            QMessageBox.information(self, "Usuario Actualizado", "El usuario ha sido actualizado correctamente.")
    
    def delete_usuario(self, usuario: Dict[str, Any]):
        """Elimina un usuario"""
        reply = QMessageBox.question(
            self, 
            "Confirmar Eliminación", 
            f"¿Está seguro que desea eliminar al usuario {usuario.get('nombre')} {usuario.get('apellido')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # En una implementación real, enviaríamos a la API
            # api_client.delete_usuario(usuario.get("id"))
            
            # Simular eliminación exitosa
            self.usuarios = [u for u in self.usuarios if u.get("id") != usuario.get("id")]
            
            # Actualizar tabla
            self.actualizar_tabla()
            
            QMessageBox.information(self, "Usuario Eliminado", "El usuario ha sido eliminado correctamente.")
    
    def view_usuario(self, usuario: Dict[str, Any]):
        """Muestra los detalles completos de un usuario"""
        # En una implementación real, podríamos mostrar una ventana de detalles más completa
        # Por ahora, mostramos un diálogo simple con la información
        
        # Crear mensaje con detalles
        detalles = f"<h2>{usuario.get('nombre')} {usuario.get('apellido')}</h2>"
        detalles += "<hr>"
        detalles += f"<p><b>ID:</b> {usuario.get('id')}</p>"
        detalles += f"<p><b>DNI/ID:</b> {usuario.get('dni')}</p>"
        detalles += f"<p><b>Email:</b> {usuario.get('email')}</p>"
        detalles += f"<p><b>Teléfono:</b> {usuario.get('telefono')}</p>"
        detalles += f"<p><b>Fecha de nacimiento:</b> {usuario.get('fecha_nacimiento')}</p>"
        detalles += f"<p><b>Plan:</b> {self.formato_plan(usuario.get('tipo_plan', ''))}</p>"
        detalles += f"<p><b>Estado:</b> {self.formato_estado(usuario.get('estado', ''))}</p>"
        detalles += f"<p><b>Fecha de inicio:</b> {usuario.get('fecha_inicio')}</p>"
        detalles += f"<p><b>Fecha de vencimiento:</b> {usuario.get('fecha_vencimiento')}</p>"
        
        # Mostrar el diálogo
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Detalles del Usuario")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(detalles)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
