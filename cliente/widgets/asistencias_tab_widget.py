# /cliente/widgets/asistencias_tab_widget.py
"""
Widget para la gestión de asistencias al gimnasio
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QMessageBox, QHeaderView, QAbstractItemView, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox, QDateEdit, QDateTimeEdit,
    QTabWidget, QSplitter, QTextEdit, QGroupBox, QTimeEdit,
    QCalendarWidget, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QDate, QTime, QDateTime
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette

from api_client import ApiClient


class AsistenciasLoadWorker(QThread):
    """Worker para cargar asistencias en background"""
    
    asistencias_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_client: ApiClient, filtros: Dict = None):
        super().__init__()
        self.api_client = api_client
        self.filtros = filtros or {}
        
    def run(self):
        """Carga la lista de asistencias"""
        try:
            asistencias = self.api_client.obtener_asistencias_sync(**self.filtros)
            self.asistencias_loaded.emit(asistencias)
        except Exception as e:
            self.error_occurred.emit(f"Error al cargar asistencias: {str(e)}")


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


class AsistenciaDialog(QDialog):
    """Diálogo para registrar o editar una asistencia"""
    
    def __init__(self, parent=None, api_client=None, asistencia=None):
        super().__init__(parent)
        self.api_client = api_client
        self.asistencia = asistencia  # None para crear, objeto para editar
        self.usuarios = []
        self.clases = []
        self.setup_ui()
        self.cargar_datos()
        
    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        self.setWindowTitle("Registrar Asistencia" if not self.asistencia else "Editar Asistencia")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Campos del formulario
        self.usuario_combo = QComboBox()
        
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["general", "clase", "entrenamiento_personal"])
        self.tipo_combo.currentIndexChanged.connect(self.actualizar_visibilidad_clase)
        if self.asistencia and "tipo" in self.asistencia:
            index = self.tipo_combo.findText(self.asistencia["tipo"])
            if index >= 0:
                self.tipo_combo.setCurrentIndex(index)
        
        self.clase_combo = QComboBox()
        self.clase_combo.setEnabled(False)  # Inicialmente desactivado
        
        self.fecha_time = QDateTimeEdit()
        self.fecha_time.setDateTime(QDateTime.currentDateTime())
        self.fecha_time.setCalendarPopup(True)
        if self.asistencia and "fecha" in self.asistencia:
            fecha_str = self.asistencia["fecha"]
            if isinstance(fecha_str, str):
                try:
                    fecha_dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                    self.fecha_time.setDateTime(QDateTime(
                        QDate(fecha_dt.year, fecha_dt.month, fecha_dt.day),
                        QTime(fecha_dt.hour, fecha_dt.minute)
                    ))
                except:
                    pass
        
        self.duracion_spin = QSpinBox()
        self.duracion_spin.setRange(0, 300)
        self.duracion_spin.setSingleStep(5)
        self.duracion_spin.setSuffix(" min")
        if self.asistencia and "duracion_minutos" in self.asistencia:
            self.duracion_spin.setValue(self.asistencia["duracion_minutos"])
        
        self.notas_edit = QTextEdit()
        self.notas_edit.setPlaceholderText("Notas adicionales (opcional)")
        if self.asistencia:
            self.notas_edit.setText(self.asistencia.get("notas", ""))
        
        # Agregar campos al formulario
        form_layout.addRow("Usuario:", self.usuario_combo)
        form_layout.addRow("Tipo:", self.tipo_combo)
        form_layout.addRow("Clase:", self.clase_combo)
        form_layout.addRow("Fecha y hora:", self.fecha_time)
        form_layout.addRow("Duración:", self.duracion_spin)
        form_layout.addRow("Notas:", self.notas_edit)
        
        # Botones de acción
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
    
    def cargar_datos(self):
        """Cargar datos de usuarios y clases"""
        if not self.api_client:
            return
            
        try:
            # Cargar usuarios
            self.usuarios = self.api_client.obtener_usuarios_sync()
            self.usuario_combo.clear()
            
            for usuario in self.usuarios:
                # Formato: ID - Nombre Apellido
                texto = f"{usuario['id']} - {usuario.get('nombre', '')} {usuario.get('apellido', '')}"
                self.usuario_combo.addItem(texto, usuario['id'])
            
            # Si es edición, seleccionar el usuario actual
            if self.asistencia and "usuario_id" in self.asistencia:
                for i in range(self.usuario_combo.count()):
                    if self.usuario_combo.itemData(i) == self.asistencia["usuario_id"]:
                        self.usuario_combo.setCurrentIndex(i)
                        break
            
            # Cargar clases
            self.clases = self.api_client.obtener_clases_sync()
            self.clase_combo.clear()
            
            for clase in self.clases:
                texto = f"{clase['id']} - {clase.get('nombre', '')}"
                self.clase_combo.addItem(texto, clase['id'])
            
            # Si es edición, seleccionar la clase actual
            if self.asistencia and "clase_id" in self.asistencia and self.asistencia["clase_id"]:
                for i in range(self.clase_combo.count()):
                    if self.clase_combo.itemData(i) == self.asistencia["clase_id"]:
                        self.clase_combo.setCurrentIndex(i)
                        break
            
            # Actualizar visibilidad del campo de clase
            self.actualizar_visibilidad_clase()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los datos: {str(e)}")
    
    def actualizar_visibilidad_clase(self):
        """Actualizar visibilidad del campo de clase según el tipo seleccionado"""
        tipo_actual = self.tipo_combo.currentText()
        self.clase_combo.setEnabled(tipo_actual == "clase")
    
    def get_data(self) -> Dict[str, Any]:
        """Obtener datos del formulario"""
        usuario_id = self.usuario_combo.currentData()
        tipo = self.tipo_combo.currentText()
        
        # Solo incluir clase_id si el tipo es "clase"
        clase_id = None
        if tipo == "clase":
            clase_id = self.clase_combo.currentData()
        
        fecha = self.fecha_time.dateTime().toString("yyyy-MM-ddTHH:mm:ss")
        
        return {
            "usuario_id": usuario_id,
            "tipo": tipo,
            "clase_id": clase_id,
            "fecha": fecha,
            "duracion_minutos": self.duracion_spin.value() if self.duracion_spin.value() > 0 else None,
            "notas": self.notas_edit.toPlainText().strip() or None
        }


class AsistenciasTabWidget(QWidget):
    """Widget principal para la gestión de asistencias"""
    
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self.asistencias = []
        self.asistencia_seleccionada = None
        self.filtros_actuales = {}
        
        self.setup_ui()
        self.cargar_asistencias()
    
    def setup_ui(self):
        """Configurar interfaz del widget"""
        main_layout = QVBoxLayout()
        
        # Título y botones principales
        title_layout = QHBoxLayout()
        title_label = QLabel("Control de Asistencias")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.setIcon(QIcon("assets/refresh.png"))
        self.refresh_button.clicked.connect(self.cargar_asistencias)
        
        self.registrar_button = QPushButton("Registrar Asistencia")
        self.registrar_button.setIcon(QIcon("assets/add.png"))
        self.registrar_button.clicked.connect(self.mostrar_dialog_nueva_asistencia)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.refresh_button)
        title_layout.addWidget(self.registrar_button)
        
        # Panel de filtros
        filtros_group = QGroupBox("Filtros")
        filtros_layout = QHBoxLayout()
        
        self.buscar_edit = QLineEdit()
        self.buscar_edit.setPlaceholderText("Buscar usuario...")
        self.buscar_edit.textChanged.connect(self.aplicar_filtros)
        
        self.tipo_filtro_combo = QComboBox()
        self.tipo_filtro_combo.addItems(["Todos", "General", "Clase", "Entrenamiento Personal"])
        self.tipo_filtro_combo.currentIndexChanged.connect(self.aplicar_filtros)
        
        self.desde_date = QDateEdit()
        self.desde_date.setCalendarPopup(True)
        # Establecer fecha desde hace 7 días
        fecha_semana = QDate.currentDate().addDays(-7)
        self.desde_date.setDate(fecha_semana)
        self.desde_date.dateChanged.connect(self.aplicar_filtros)
        
        self.hasta_date = QDateEdit()
        self.hasta_date.setCalendarPopup(True)
        self.hasta_date.setDate(QDate.currentDate())
        self.hasta_date.dateChanged.connect(self.aplicar_filtros)
        
        filtros_layout.addWidget(QLabel("Buscar:"))
        filtros_layout.addWidget(self.buscar_edit, 2)
        filtros_layout.addWidget(QLabel("Tipo:"))
        filtros_layout.addWidget(self.tipo_filtro_combo, 1)
        filtros_layout.addWidget(QLabel("Desde:"))
        filtros_layout.addWidget(self.desde_date, 1)
        filtros_layout.addWidget(QLabel("Hasta:"))
        filtros_layout.addWidget(self.hasta_date, 1)
        
        filtros_group.setLayout(filtros_layout)
        
        # Tabla de asistencias
        self.asistencias_table = QTableWidget()
        self.asistencias_table.setColumnCount(6)
        self.asistencias_table.setHorizontalHeaderLabels([
            "ID", "Usuario", "Fecha y Hora", "Tipo", "Clase", "Duración"
        ])
        self.asistencias_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.asistencias_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.asistencias_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.asistencias_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.asistencias_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.asistencias_table.setAlternatingRowColors(True)
        self.asistencias_table.clicked.connect(self.seleccionar_asistencia)
        
        # Panel de detalles
        detalles_group = QGroupBox("Detalles de la Asistencia")
        detalles_layout = QFormLayout()
        
        self.id_label = QLabel("")
        self.usuario_label = QLabel("")
        self.tipo_label = QLabel("")
        self.clase_label = QLabel("")
        self.fecha_label = QLabel("")
        self.duracion_label = QLabel("")
        self.notas_label = QLabel("")
        self.notas_label.setWordWrap(True)
        
        detalles_layout.addRow("ID:", self.id_label)
        detalles_layout.addRow("Usuario:", self.usuario_label)
        detalles_layout.addRow("Tipo:", self.tipo_label)
        detalles_layout.addRow("Clase:", self.clase_label)
        detalles_layout.addRow("Fecha y hora:", self.fecha_label)
        detalles_layout.addRow("Duración:", self.duracion_label)
        detalles_layout.addRow("Notas:", self.notas_label)
        
        # Botones de acción
        action_layout = QHBoxLayout()
        self.editar_button = QPushButton("Editar")
        self.editar_button.setIcon(QIcon("assets/edit.png"))
        self.editar_button.clicked.connect(self.mostrar_dialog_editar_asistencia)
        self.editar_button.setEnabled(False)
        
        self.eliminar_button = QPushButton("Eliminar")
        self.eliminar_button.setIcon(QIcon("assets/delete.png"))
        self.eliminar_button.clicked.connect(self.eliminar_asistencia)
        self.eliminar_button.setEnabled(False)
        
        action_layout.addWidget(self.editar_button)
        action_layout.addWidget(self.eliminar_button)
        
        detalles_widget = QWidget()
        detalles_main_layout = QVBoxLayout(detalles_widget)
        detalles_main_layout.addLayout(detalles_layout)
        detalles_main_layout.addLayout(action_layout)
        detalles_group.setLayout(detalles_main_layout)
        
        # Estadísticas rápidas
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("Total: 0 asistencias")
        self.total_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.promedio_label = QLabel("Promedio: 0 / día")
        self.promedio_label.setStyleSheet("font-size: 14px;")
        
        self.hoy_label = QLabel("Hoy: 0 asistencias")
        self.hoy_label.setStyleSheet("font-size: 14px;")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.promedio_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.hoy_label)
        
        stats_group.setLayout(stats_layout)
        
        # Layout principal
        main_layout.addLayout(title_layout)
        main_layout.addWidget(filtros_group)
        
        # Contenido principal (tabla y detalles)
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.asistencias_table, 2)
        content_layout.addWidget(detalles_group, 1)
        
        main_layout.addLayout(content_layout, 1)
        main_layout.addWidget(stats_group)
        
        self.setLayout(main_layout)
    
    def cargar_asistencias(self):
        """Cargar la lista de asistencias desde la API"""
        self.refresh_button.setEnabled(False)
        self.registrar_button.setEnabled(False)
        
        # Preparar filtros
        self.obtener_filtros_actuales()
        
        self.worker = AsistenciasLoadWorker(self.api_client, self.filtros_actuales)
        self.worker.asistencias_loaded.connect(self.actualizar_tabla_asistencias)
        self.worker.error_occurred.connect(self.mostrar_error)
        self.worker.finished.connect(lambda: self.refresh_button.setEnabled(True))
        self.worker.finished.connect(lambda: self.registrar_button.setEnabled(True))
        self.worker.start()
    
    def obtener_filtros_actuales(self):
        """Obtener los filtros actuales de la interfaz"""
        filtros = {}
        
        # Filtro de tipo
        tipo_index = self.tipo_filtro_combo.currentIndex()
        if tipo_index > 0:
            tipos = ["general", "clase", "entrenamiento_personal"]
            filtros["tipo"] = tipos[tipo_index - 1]
        
        # Filtro de fechas
        desde = self.desde_date.date().toString("yyyy-MM-dd")
        hasta = self.hasta_date.date().toString("yyyy-MM-dd")
        filtros["desde"] = desde
        filtros["hasta"] = hasta
        
        self.filtros_actuales = filtros
    
    def actualizar_tabla_asistencias(self, asistencias):
        """Actualizar la tabla con las asistencias cargadas"""
        self.asistencias = asistencias
        self.aplicar_filtros()
    
    def aplicar_filtros(self):
        """Filtrar las asistencias según los criterios de búsqueda"""
        texto_busqueda = self.buscar_edit.text().lower()
        
        asistencias_filtradas = []
        for asistencia in self.asistencias:
            # Filtrar por texto de búsqueda en usuario (solo ID por ahora)
            usuario_id = str(asistencia.get("usuario_id", ""))
            if texto_busqueda and texto_busqueda not in usuario_id:
                continue
            
            asistencias_filtradas.append(asistencia)
        
        self.mostrar_asistencias_en_tabla(asistencias_filtradas)
        self.actualizar_estadisticas(asistencias_filtradas)
    
    def mostrar_asistencias_en_tabla(self, asistencias):
        """Mostrar las asistencias filtradas en la tabla"""
        self.asistencias_table.setRowCount(0)
        
        for asistencia in asistencias:
            row = self.asistencias_table.rowCount()
            self.asistencias_table.insertRow(row)
            
            # Obtener información de usuario
            usuario_id = asistencia.get("usuario_id", "")
            usuario_texto = f"ID: {usuario_id}"
            
            # Formato de fecha y hora
            fecha_str = asistencia.get("fecha", "")
            fecha_formateada = fecha_str
            if fecha_str:
                try:
                    fecha_dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                    fecha_formateada = fecha_dt.strftime("%d/%m/%Y %H:%M")
                except:
                    pass
            
            # Duración
            duracion = asistencia.get("duracion_minutos")
            duracion_texto = f"{duracion} min" if duracion else "N/A"
            
            # Información de clase
            clase_id = asistencia.get("clase_id")
            clase_texto = f"ID: {clase_id}" if clase_id else "N/A"
            
            # Insertar datos en la fila
            self.asistencias_table.setItem(row, 0, QTableWidgetItem(str(asistencia.get("id", ""))))
            self.asistencias_table.setItem(row, 1, QTableWidgetItem(usuario_texto))
            self.asistencias_table.setItem(row, 2, QTableWidgetItem(fecha_formateada))
            self.asistencias_table.setItem(row, 3, QTableWidgetItem(asistencia.get("tipo", "").capitalize()))
            self.asistencias_table.setItem(row, 4, QTableWidgetItem(clase_texto))
            self.asistencias_table.setItem(row, 5, QTableWidgetItem(duracion_texto))
    
    def actualizar_estadisticas(self, asistencias):
        """Actualizar las estadísticas con los datos filtrados"""
        total = len(asistencias)
        
        # Calcular asistencias de hoy
        hoy = QDate.currentDate().toString("yyyy-MM-dd")
        asistencias_hoy = sum(1 for a in asistencias if a.get("fecha", "").startswith(hoy))
        
        # Calcular promedio diario
        dias_periodo = self.desde_date.date().daysTo(self.hasta_date.date()) + 1
        promedio = total / dias_periodo if dias_periodo > 0 else 0
        
        self.total_label.setText(f"Total: {total} asistencias")
        self.promedio_label.setText(f"Promedio: {promedio:.1f} / día")
        self.hoy_label.setText(f"Hoy: {asistencias_hoy} asistencias")
    
    def seleccionar_asistencia(self):
        """Manejar la selección de una asistencia en la tabla"""
        row = self.asistencias_table.currentRow()
        if row >= 0:
            asistencia_id = int(self.asistencias_table.item(row, 0).text())
            
            # Encontrar la asistencia seleccionada
            for asistencia in self.asistencias:
                if asistencia.get("id") == asistencia_id:
                    self.asistencia_seleccionada = asistencia
                    self.mostrar_detalles_asistencia(asistencia)
                    
                    # Habilitar botones
                    self.editar_button.setEnabled(True)
                    self.eliminar_button.setEnabled(True)
                    break
    
    def mostrar_detalles_asistencia(self, asistencia):
        """Mostrar los detalles de la asistencia seleccionada"""
        self.id_label.setText(str(asistencia.get("id", "")))
        self.usuario_label.setText(f"ID: {asistencia.get('usuario_id', '')}")
        self.tipo_label.setText(asistencia.get("tipo", "").capitalize())
        
        # Información de clase
        clase_id = asistencia.get("clase_id")
        self.clase_label.setText(f"ID: {clase_id}" if clase_id else "N/A")
        
        # Formato de fecha y hora
        fecha_str = asistencia.get("fecha", "")
        fecha_formateada = fecha_str
        if fecha_str:
            try:
                fecha_dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                fecha_formateada = fecha_dt.strftime("%d/%m/%Y %H:%M:%S")
            except:
                pass
        
        self.fecha_label.setText(fecha_formateada)
        
        # Duración
        duracion = asistencia.get("duracion_minutos")
        self.duracion_label.setText(f"{duracion} minutos" if duracion else "No especificada")
        
        # Notas
        self.notas_label.setText(asistencia.get("notas", "") or "Sin notas adicionales")
    
    def mostrar_dialog_nueva_asistencia(self):
        """Mostrar diálogo para registrar una nueva asistencia"""
        dialog = AsistenciaDialog(self, self.api_client)
        if dialog.exec():
            datos_asistencia = dialog.get_data()
            try:
                respuesta = self.api_client.registrar_asistencia_sync(datos_asistencia)
                QMessageBox.information(self, "Éxito", "Asistencia registrada correctamente")
                self.cargar_asistencias()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo registrar la asistencia: {str(e)}")
    
    def mostrar_dialog_editar_asistencia(self):
        """Mostrar diálogo para editar la asistencia seleccionada"""
        if not self.asistencia_seleccionada:
            return
        
        dialog = AsistenciaDialog(self, self.api_client, self.asistencia_seleccionada)
        if dialog.exec():
            datos_asistencia = dialog.get_data()
            try:
                respuesta = self.api_client.actualizar_asistencia_sync(
                    self.asistencia_seleccionada["id"], 
                    datos_asistencia
                )
                QMessageBox.information(self, "Éxito", "Asistencia actualizada correctamente")
                self.cargar_asistencias()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar la asistencia: {str(e)}")
    
    def eliminar_asistencia(self):
        """Eliminar la asistencia seleccionada"""
        if not self.asistencia_seleccionada:
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirmar eliminación", 
            "¿Está seguro de que desea eliminar esta asistencia? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.api_client.eliminar_asistencia_sync(self.asistencia_seleccionada["id"])
                QMessageBox.information(self, "Éxito", "Asistencia eliminada correctamente")
                self.cargar_asistencias()
                
                # Limpiar selección
                self.asistencia_seleccionada = None
                self.editar_button.setEnabled(False)
                self.eliminar_button.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar la asistencia: {str(e)}")
    
    def mostrar_error(self, mensaje):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, "Error", mensaje)
