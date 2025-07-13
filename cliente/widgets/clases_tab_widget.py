# /cliente/widgets/clases_tab_widget.py
"""
Widget para la gestión de clases y horarios del gimnasio
"""

from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QMessageBox, QHeaderView, QAbstractItemView, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox, QCheckBox,
    QTabWidget, QSplitter, QTextEdit, QGroupBox, QTimeEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTime
from PyQt6.QtGui import QIcon, QFont, QColor

from api_client import ApiClient


class ClasesLoadWorker(QThread):
    """Worker para cargar clases en background"""
    
    clases_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        
    def run(self):
        """Carga la lista de clases"""
        try:
            clases = self.api_client.obtener_clases_sync()
            self.clases_loaded.emit(clases)
        except Exception as e:
            self.error_occurred.emit(f"Error al cargar clases: {str(e)}")


class HorariosLoadWorker(QThread):
    """Worker para cargar horarios de una clase en background"""
    
    horarios_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_client: ApiClient, clase_id: int):
        super().__init__()
        self.api_client = api_client
        self.clase_id = clase_id
        
    def run(self):
        """Carga los horarios de una clase"""
        try:
            horarios = self.api_client.obtener_horarios_clase_sync(self.clase_id)
            self.horarios_loaded.emit(horarios)
        except Exception as e:
            self.error_occurred.emit(f"Error al cargar horarios: {str(e)}")


class ClaseDialog(QDialog):
    """Diálogo para crear o editar una clase"""
    
    def __init__(self, parent=None, clase=None):
        super().__init__(parent)
        self.clase = clase  # None para crear, objeto para editar
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        self.setWindowTitle("Nueva Clase" if not self.clase else "Editar Clase")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Campos del formulario
        self.nombre_edit = QLineEdit()
        self.nombre_edit.setPlaceholderText("Nombre de la clase")
        if self.clase:
            self.nombre_edit.setText(self.clase.get("nombre", ""))
        
        self.descripcion_edit = QTextEdit()
        self.descripcion_edit.setPlaceholderText("Descripción detallada de la clase")
        if self.clase:
            self.descripcion_edit.setText(self.clase.get("descripcion", ""))
        
        self.instructor_edit = QLineEdit()
        self.instructor_edit.setPlaceholderText("Nombre del instructor")
        if self.clase:
            self.instructor_edit.setText(self.clase.get("instructor", ""))
        
        self.capacidad_spin = QSpinBox()
        self.capacidad_spin.setRange(1, 100)
        self.capacidad_spin.setValue(self.clase.get("capacidad_maxima", 20) if self.clase else 20)
        
        self.duracion_spin = QSpinBox()
        self.duracion_spin.setRange(15, 240)
        self.duracion_spin.setSingleStep(5)
        self.duracion_spin.setSuffix(" min")
        self.duracion_spin.setValue(self.clase.get("duracion_minutos", 60) if self.clase else 60)
        
        self.nivel_combo = QComboBox()
        self.nivel_combo.addItems(["principiante", "intermedio", "avanzado"])
        if self.clase:
            index = self.nivel_combo.findText(self.clase.get("nivel", "principiante"))
            if index >= 0:
                self.nivel_combo.setCurrentIndex(index)
        
        self.activa_check = QCheckBox()
        self.activa_check.setChecked(self.clase.get("activa", True) if self.clase else True)
        
        # Agregar campos al formulario
        form_layout.addRow("Nombre:", self.nombre_edit)
        form_layout.addRow("Descripción:", self.descripcion_edit)
        form_layout.addRow("Instructor:", self.instructor_edit)
        form_layout.addRow("Capacidad:", self.capacidad_spin)
        form_layout.addRow("Duración:", self.duracion_spin)
        form_layout.addRow("Nivel:", self.nivel_combo)
        form_layout.addRow("Activa:", self.activa_check)
        
        # Botones de acción
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
    
    def get_data(self) -> Dict[str, Any]:
        """Obtener datos del formulario"""
        return {
            "nombre": self.nombre_edit.text().strip(),
            "descripcion": self.descripcion_edit.toPlainText().strip(),
            "instructor": self.instructor_edit.text().strip(),
            "capacidad_maxima": self.capacidad_spin.value(),
            "duracion_minutos": self.duracion_spin.value(),
            "nivel": self.nivel_combo.currentText(),
            "activa": self.activa_check.isChecked()
        }


class HorarioDialog(QDialog):
    """Diálogo para crear o editar un horario de clase"""
    
    def __init__(self, parent=None, clase_id=None, horario=None):
        super().__init__(parent)
        self.clase_id = clase_id
        self.horario = horario  # None para crear, objeto para editar
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        self.setWindowTitle("Nuevo Horario" if not self.horario else "Editar Horario")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Campos del formulario
        self.dia_combo = QComboBox()
        self.dia_combo.addItems([
            "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"
        ])
        if self.horario:
            index = self.dia_combo.findText(self.horario.get("dia", "lunes"))
            if index >= 0:
                self.dia_combo.setCurrentIndex(index)
        
        self.hora_edit = QTimeEdit()
        self.hora_edit.setDisplayFormat("HH:mm")
        if self.horario and "hora_inicio" in self.horario:
            hora_str = self.horario["hora_inicio"]
            if isinstance(hora_str, str) and ":" in hora_str:
                hora, minuto = map(int, hora_str.split(":")[:2])
                self.hora_edit.setTime(QTime(hora, minuto))
        else:
            self.hora_edit.setTime(QTime(8, 0))  # Default 8:00 AM
        
        self.salon_edit = QLineEdit()
        self.salon_edit.setPlaceholderText("Salón o ubicación de la clase")
        if self.horario:
            self.salon_edit.setText(self.horario.get("salon", ""))
        
        # Agregar campos al formulario
        form_layout.addRow("Día:", self.dia_combo)
        form_layout.addRow("Hora inicio:", self.hora_edit)
        form_layout.addRow("Salón:", self.salon_edit)
        
        # Botones de acción
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
    
    def get_data(self) -> Dict[str, Any]:
        """Obtener datos del formulario"""
        return {
            "clase_id": self.clase_id,
            "dia": self.dia_combo.currentText(),
            "hora_inicio": self.hora_edit.time().toString("HH:mm"),
            "salon": self.salon_edit.text().strip()
        }


class ClasesTabWidget(QWidget):
    """Widget principal para la gestión de clases"""
    
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self.clases = []
        self.horarios = []
        self.clase_seleccionada = None
        
        self.setup_ui()
        self.cargar_clases()
    
    def setup_ui(self):
        """Configurar interfaz del widget"""
        main_layout = QVBoxLayout()
        
        # Título y botones principales
        title_layout = QHBoxLayout()
        title_label = QLabel("Gestión de Clases")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.setIcon(QIcon("assets/refresh.png"))
        self.refresh_button.clicked.connect(self.cargar_clases)
        
        self.nueva_clase_button = QPushButton("Nueva Clase")
        self.nueva_clase_button.setIcon(QIcon("assets/add.png"))
        self.nueva_clase_button.clicked.connect(self.mostrar_dialog_nueva_clase)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.refresh_button)
        title_layout.addWidget(self.nueva_clase_button)
        
        # Contenedor principal con splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo: Lista de clases
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        filter_layout = QHBoxLayout()
        self.buscar_edit = QLineEdit()
        self.buscar_edit.setPlaceholderText("Buscar clase...")
        self.buscar_edit.textChanged.connect(self.filtrar_clases)
        
        self.filtro_combo = QComboBox()
        self.filtro_combo.addItems(["Todas", "Activas", "Inactivas"])
        self.filtro_combo.currentIndexChanged.connect(self.filtrar_clases)
        
        filter_layout.addWidget(QLabel("Filtrar:"))
        filter_layout.addWidget(self.buscar_edit)
        filter_layout.addWidget(self.filtro_combo)
        
        self.clases_table = QTableWidget()
        self.clases_table.setColumnCount(4)
        self.clases_table.setHorizontalHeaderLabels(["ID", "Nombre", "Instructor", "Nivel"])
        self.clases_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.clases_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.clases_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.clases_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.clases_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clases_table.clicked.connect(self.seleccionar_clase)
        
        left_layout.addLayout(filter_layout)
        left_layout.addWidget(self.clases_table)
        
        # Panel derecho: Detalles de clase y horarios
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.detalles_group = QGroupBox("Detalles de la Clase")
        detalles_layout = QVBoxLayout()
        
        self.nombre_label = QLabel("")
        self.nombre_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.descripcion_label = QLabel("")
        self.descripcion_label.setWordWrap(True)
        self.instructor_label = QLabel("")
        self.capacidad_label = QLabel("")
        self.duracion_label = QLabel("")
        self.nivel_label = QLabel("")
        self.estado_label = QLabel("")
        
        detalles_layout.addWidget(self.nombre_label)
        detalles_layout.addWidget(self.descripcion_label)
        
        info_layout = QHBoxLayout()
        info_left = QVBoxLayout()
        info_left.addWidget(QLabel("Instructor:"))
        info_left.addWidget(QLabel("Capacidad:"))
        info_left.addWidget(QLabel("Duración:"))
        
        info_right = QVBoxLayout()
        info_right.addWidget(QLabel("Nivel:"))
        info_right.addWidget(QLabel("Estado:"))
        
        info_layout.addLayout(info_left)
        info_layout.addLayout(info_right)
        
        detalles_layout.addLayout(info_layout)
        
        # Botones de acción para la clase
        action_layout = QHBoxLayout()
        self.editar_clase_button = QPushButton("Editar Clase")
        self.editar_clase_button.setIcon(QIcon("assets/edit.png"))
        self.editar_clase_button.clicked.connect(self.mostrar_dialog_editar_clase)
        self.editar_clase_button.setEnabled(False)
        
        self.toggle_estado_button = QPushButton("Desactivar")
        self.toggle_estado_button.setIcon(QIcon("assets/toggle.png"))
        self.toggle_estado_button.clicked.connect(self.toggle_estado_clase)
        self.toggle_estado_button.setEnabled(False)
        
        action_layout.addWidget(self.editar_clase_button)
        action_layout.addWidget(self.toggle_estado_button)
        
        detalles_layout.addLayout(action_layout)
        self.detalles_group.setLayout(detalles_layout)
        
        # Sección de horarios
        self.horarios_group = QGroupBox("Horarios")
        horarios_layout = QVBoxLayout()
        
        horarios_header = QHBoxLayout()
        horarios_header.addWidget(QLabel("Horarios de la Clase"))
        horarios_header.addStretch()
        
        self.nuevo_horario_button = QPushButton("Nuevo Horario")
        self.nuevo_horario_button.setIcon(QIcon("assets/clock-add.png"))
        self.nuevo_horario_button.clicked.connect(self.mostrar_dialog_nuevo_horario)
        self.nuevo_horario_button.setEnabled(False)
        
        horarios_header.addWidget(self.nuevo_horario_button)
        
        self.horarios_table = QTableWidget()
        self.horarios_table.setColumnCount(4)
        self.horarios_table.setHorizontalHeaderLabels(["ID", "Día", "Hora", "Salón"])
        self.horarios_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horarios_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.horarios_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.horarios_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.horarios_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Botones de acción para horarios
        horarios_action = QHBoxLayout()
        self.editar_horario_button = QPushButton("Editar Horario")
        self.editar_horario_button.setIcon(QIcon("assets/edit.png"))
        self.editar_horario_button.clicked.connect(self.mostrar_dialog_editar_horario)
        self.editar_horario_button.setEnabled(False)
        
        self.eliminar_horario_button = QPushButton("Eliminar Horario")
        self.eliminar_horario_button.setIcon(QIcon("assets/delete.png"))
        self.eliminar_horario_button.clicked.connect(self.eliminar_horario)
        self.eliminar_horario_button.setEnabled(False)
        
        horarios_action.addWidget(self.editar_horario_button)
        horarios_action.addWidget(self.eliminar_horario_button)
        
        horarios_layout.addLayout(horarios_header)
        horarios_layout.addWidget(self.horarios_table)
        horarios_layout.addLayout(horarios_action)
        self.horarios_group.setLayout(horarios_layout)
        
        self.horarios_table.clicked.connect(self.seleccionar_horario)
        
        right_layout.addWidget(self.detalles_group)
        right_layout.addWidget(self.horarios_group)
        
        # Agregar paneles al splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 400])
        
        main_layout.addLayout(title_layout)
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def cargar_clases(self):
        """Cargar la lista de clases desde la API"""
        self.refresh_button.setEnabled(False)
        self.nueva_clase_button.setEnabled(False)
        
        self.worker = ClasesLoadWorker(self.api_client)
        self.worker.clases_loaded.connect(self.actualizar_tabla_clases)
        self.worker.error_occurred.connect(self.mostrar_error)
        self.worker.finished.connect(lambda: self.refresh_button.setEnabled(True))
        self.worker.finished.connect(lambda: self.nueva_clase_button.setEnabled(True))
        self.worker.start()
    
    def actualizar_tabla_clases(self, clases):
        """Actualizar la tabla con las clases cargadas"""
        self.clases = clases
        self.filtrar_clases()
    
    def filtrar_clases(self):
        """Filtrar las clases según los criterios de búsqueda"""
        texto_busqueda = self.buscar_edit.text().lower()
        filtro_index = self.filtro_combo.currentIndex()
        
        clases_filtradas = []
        for clase in self.clases:
            # Filtrar por texto
            if texto_busqueda and texto_busqueda not in clase.get("nombre", "").lower() and \
               texto_busqueda not in clase.get("instructor", "").lower():
                continue
            
            # Filtrar por estado
            if filtro_index == 1 and not clase.get("activa", True):  # Solo activas
                continue
            elif filtro_index == 2 and clase.get("activa", True):  # Solo inactivas
                continue
            
            clases_filtradas.append(clase)
        
        self.mostrar_clases_en_tabla(clases_filtradas)
    
    def mostrar_clases_en_tabla(self, clases):
        """Mostrar las clases filtradas en la tabla"""
        self.clases_table.setRowCount(0)
        
        for clase in clases:
            row = self.clases_table.rowCount()
            self.clases_table.insertRow(row)
            
            # Insertar datos en la fila
            self.clases_table.setItem(row, 0, QTableWidgetItem(str(clase.get("id", ""))))
            self.clases_table.setItem(row, 1, QTableWidgetItem(clase.get("nombre", "")))
            self.clases_table.setItem(row, 2, QTableWidgetItem(clase.get("instructor", "")))
            self.clases_table.setItem(row, 3, QTableWidgetItem(clase.get("nivel", "")))
            
            # Color de fondo según estado
            if not clase.get("activa", True):
                for col in range(self.clases_table.columnCount()):
                    item = self.clases_table.item(row, col)
                    if item:
                        item.setBackground(QColor(240, 240, 240))
    
    def seleccionar_clase(self):
        """Manejar la selección de una clase en la tabla"""
        row = self.clases_table.currentRow()
        if row >= 0:
            clase_id = int(self.clases_table.item(row, 0).text())
            
            # Encontrar la clase seleccionada
            for clase in self.clases:
                if clase.get("id") == clase_id:
                    self.clase_seleccionada = clase
                    self.mostrar_detalles_clase(clase)
                    self.cargar_horarios_clase(clase_id)
                    
                    # Habilitar botones
                    self.editar_clase_button.setEnabled(True)
                    self.toggle_estado_button.setEnabled(True)
                    self.nuevo_horario_button.setEnabled(True)
                    
                    # Actualizar texto del botón de toggle
                    if clase.get("activa", True):
                        self.toggle_estado_button.setText("Desactivar")
                    else:
                        self.toggle_estado_button.setText("Activar")
                    
                    break
    
    def mostrar_detalles_clase(self, clase):
        """Mostrar los detalles de la clase seleccionada"""
        self.nombre_label.setText(clase.get("nombre", ""))
        self.descripcion_label.setText(clase.get("descripcion", ""))
        self.instructor_label.setText(f"Instructor: {clase.get('instructor', '')}")
        self.capacidad_label.setText(f"Capacidad: {clase.get('capacidad_maxima', 0)} personas")
        self.duracion_label.setText(f"Duración: {clase.get('duracion_minutos', 0)} minutos")
        self.nivel_label.setText(f"Nivel: {clase.get('nivel', 'N/A')}")
        
        # Estado con estilo
        estado_texto = "Activa" if clase.get("activa", True) else "Inactiva"
        estado_color = "green" if clase.get("activa", True) else "red"
        self.estado_label.setText(f"Estado: <span style='color: {estado_color};'>{estado_texto}</span>")
    
    def cargar_horarios_clase(self, clase_id):
        """Cargar los horarios de la clase seleccionada"""
        self.horarios_table.setRowCount(0)
        self.editar_horario_button.setEnabled(False)
        self.eliminar_horario_button.setEnabled(False)
        
        self.worker_horarios = HorariosLoadWorker(self.api_client, clase_id)
        self.worker_horarios.horarios_loaded.connect(self.actualizar_tabla_horarios)
        self.worker_horarios.error_occurred.connect(self.mostrar_error)
        self.worker_horarios.start()
    
    def actualizar_tabla_horarios(self, horarios):
        """Actualizar la tabla con los horarios cargados"""
        self.horarios = horarios
        self.horarios_table.setRowCount(0)
        
        for horario in horarios:
            row = self.horarios_table.rowCount()
            self.horarios_table.insertRow(row)
            
            # Insertar datos en la fila
            self.horarios_table.setItem(row, 0, QTableWidgetItem(str(horario.get("id", ""))))
            self.horarios_table.setItem(row, 1, QTableWidgetItem(horario.get("dia", "").capitalize()))
            self.horarios_table.setItem(row, 2, QTableWidgetItem(horario.get("hora_inicio", "")))
            self.horarios_table.setItem(row, 3, QTableWidgetItem(horario.get("salon", "")))
    
    def seleccionar_horario(self):
        """Manejar la selección de un horario en la tabla"""
        if self.horarios_table.currentRow() >= 0:
            self.editar_horario_button.setEnabled(True)
            self.eliminar_horario_button.setEnabled(True)
    
    def mostrar_dialog_nueva_clase(self):
        """Mostrar diálogo para crear una nueva clase"""
        dialog = ClaseDialog(self)
        if dialog.exec():
            datos_clase = dialog.get_data()
            try:
                respuesta = self.api_client.crear_clase_sync(datos_clase)
                QMessageBox.information(self, "Éxito", "Clase creada correctamente")
                self.cargar_clases()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la clase: {str(e)}")
    
    def mostrar_dialog_editar_clase(self):
        """Mostrar diálogo para editar la clase seleccionada"""
        if not self.clase_seleccionada:
            return
        
        dialog = ClaseDialog(self, self.clase_seleccionada)
        if dialog.exec():
            datos_clase = dialog.get_data()
            try:
                respuesta = self.api_client.actualizar_clase_sync(self.clase_seleccionada["id"], datos_clase)
                QMessageBox.information(self, "Éxito", "Clase actualizada correctamente")
                self.cargar_clases()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar la clase: {str(e)}")
    
    def toggle_estado_clase(self):
        """Cambiar el estado (activa/inactiva) de la clase seleccionada"""
        if not self.clase_seleccionada:
            return
        
        nuevo_estado = not self.clase_seleccionada.get("activa", True)
        try:
            respuesta = self.api_client.actualizar_clase_sync(
                self.clase_seleccionada["id"], 
                {"activa": nuevo_estado}
            )
            
            mensaje = "activada" if nuevo_estado else "desactivada"
            QMessageBox.information(self, "Éxito", f"Clase {mensaje} correctamente")
            self.cargar_clases()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cambiar el estado de la clase: {str(e)}")
    
    def mostrar_dialog_nuevo_horario(self):
        """Mostrar diálogo para crear un nuevo horario"""
        if not self.clase_seleccionada:
            return
        
        dialog = HorarioDialog(self, self.clase_seleccionada["id"])
        if dialog.exec():
            datos_horario = dialog.get_data()
            try:
                respuesta = self.api_client.crear_horario_clase_sync(
                    self.clase_seleccionada["id"], 
                    datos_horario
                )
                QMessageBox.information(self, "Éxito", "Horario creado correctamente")
                self.cargar_horarios_clase(self.clase_seleccionada["id"])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el horario: {str(e)}")
    
    def mostrar_dialog_editar_horario(self):
        """Mostrar diálogo para editar el horario seleccionado"""
        row = self.horarios_table.currentRow()
        if row < 0:
            return
        
        horario_id = int(self.horarios_table.item(row, 0).text())
        
        # Encontrar el horario seleccionado
        horario = None
        for h in self.horarios:
            if h.get("id") == horario_id:
                horario = h
                break
        
        if not horario:
            return
        
        dialog = HorarioDialog(self, self.clase_seleccionada["id"], horario)
        if dialog.exec():
            datos_horario = dialog.get_data()
            try:
                respuesta = self.api_client.actualizar_horario_clase_sync(horario_id, datos_horario)
                QMessageBox.information(self, "Éxito", "Horario actualizado correctamente")
                self.cargar_horarios_clase(self.clase_seleccionada["id"])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el horario: {str(e)}")
    
    def eliminar_horario(self):
        """Eliminar el horario seleccionado"""
        row = self.horarios_table.currentRow()
        if row < 0:
            return
        
        horario_id = int(self.horarios_table.item(row, 0).text())
        
        reply = QMessageBox.question(
            self, 
            "Confirmar eliminación", 
            "¿Está seguro de que desea eliminar este horario? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.api_client.eliminar_horario_clase_sync(horario_id)
                QMessageBox.information(self, "Éxito", "Horario eliminado correctamente")
                self.cargar_horarios_clase(self.clase_seleccionada["id"])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el horario: {str(e)}")
    
    def mostrar_error(self, mensaje):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, "Error", mensaje)
