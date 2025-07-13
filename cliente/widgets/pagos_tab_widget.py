# /cliente/widgets/pagos_tab_widget.py
"""
Widget para la gestión de pagos y membresías
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QMessageBox, QHeaderView, QAbstractItemView, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox, QDateEdit,
    QTabWidget, QSplitter, QTextEdit, QGroupBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QDate
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette

from api_client import ApiClient


class PagosLoadWorker(QThread):
    """Worker para cargar pagos en background"""
    
    pagos_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_client: ApiClient, filtros: Dict = None):
        super().__init__()
        self.api_client = api_client
        self.filtros = filtros or {}
        
    def run(self):
        """Carga la lista de pagos"""
        try:
            pagos = self.api_client.obtener_pagos_sync(**self.filtros)
            self.pagos_loaded.emit(pagos)
        except Exception as e:
            self.error_occurred.emit(f"Error al cargar pagos: {str(e)}")


class PagoDialog(QDialog):
    """Diálogo para crear o editar un pago"""
    
    def __init__(self, parent=None, api_client=None, pago=None):
        super().__init__(parent)
        self.api_client = api_client
        self.pago = pago  # None para crear, objeto para editar
        self.usuarios = []
        self.setup_ui()
        self.cargar_usuarios()
        
    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        self.setWindowTitle("Nuevo Pago" if not self.pago else "Editar Pago")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Campos del formulario
        self.usuario_combo = QComboBox()
        
        self.monto_spin = QDoubleSpinBox()
        self.monto_spin.setRange(0.01, 100000.00)
        self.monto_spin.setDecimals(2)
        self.monto_spin.setSingleStep(10.00)
        self.monto_spin.setSuffix(" $")
        if self.pago:
            self.monto_spin.setValue(self.pago.get("monto", 0.0))
        
        self.fecha_edit = QDateEdit()
        self.fecha_edit.setCalendarPopup(True)
        self.fecha_edit.setDate(QDate.currentDate())
        if self.pago and "fecha_pago" in self.pago:
            fecha_str = self.pago["fecha_pago"]
            if isinstance(fecha_str, str):
                try:
                    fecha_dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                    self.fecha_edit.setDate(QDate(fecha_dt.year, fecha_dt.month, fecha_dt.day))
                except:
                    pass
        
        self.metodo_combo = QComboBox()
        self.metodo_combo.addItems(["efectivo", "tarjeta", "transferencia", "deposito", "otro"])
        if self.pago and "metodo_pago" in self.pago:
            index = self.metodo_combo.findText(self.pago["metodo_pago"])
            if index >= 0:
                self.metodo_combo.setCurrentIndex(index)
        
        self.concepto_edit = QLineEdit()
        self.concepto_edit.setPlaceholderText("Concepto o razón del pago")
        if self.pago:
            self.concepto_edit.setText(self.pago.get("concepto", ""))
        
        self.notas_edit = QTextEdit()
        self.notas_edit.setPlaceholderText("Notas adicionales (opcional)")
        if self.pago:
            self.notas_edit.setText(self.pago.get("notas", ""))
        
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["pendiente", "completado", "cancelado", "reembolsado"])
        if self.pago and "estado" in self.pago:
            index = self.estado_combo.findText(self.pago["estado"])
            if index >= 0:
                self.estado_combo.setCurrentIndex(index)
        
        # Agregar campos al formulario
        form_layout.addRow("Usuario:", self.usuario_combo)
        form_layout.addRow("Monto:", self.monto_spin)
        form_layout.addRow("Fecha:", self.fecha_edit)
        form_layout.addRow("Método:", self.metodo_combo)
        form_layout.addRow("Concepto:", self.concepto_edit)
        form_layout.addRow("Notas:", self.notas_edit)
        form_layout.addRow("Estado:", self.estado_combo)
        
        # Botones de acción
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
    
    def cargar_usuarios(self):
        """Cargar la lista de usuarios para el combo"""
        if not self.api_client:
            return
            
        try:
            self.usuarios = self.api_client.obtener_usuarios_sync()
            self.usuario_combo.clear()
            
            for usuario in self.usuarios:
                # Formato: ID - Nombre Apellido
                texto = f"{usuario['id']} - {usuario.get('nombre', '')} {usuario.get('apellido', '')}"
                self.usuario_combo.addItem(texto, usuario['id'])
            
            # Si es edición, seleccionar el usuario actual
            if self.pago and "usuario_id" in self.pago:
                for i in range(self.usuario_combo.count()):
                    if self.usuario_combo.itemData(i) == self.pago["usuario_id"]:
                        self.usuario_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los usuarios: {str(e)}")
    
    def get_data(self) -> Dict[str, Any]:
        """Obtener datos del formulario"""
        usuario_id = self.usuario_combo.currentData()
        
        return {
            "usuario_id": usuario_id,
            "monto": self.monto_spin.value(),
            "fecha_pago": self.fecha_edit.date().toString("yyyy-MM-dd"),
            "metodo_pago": self.metodo_combo.currentText(),
            "concepto": self.concepto_edit.text().strip(),
            "notas": self.notas_edit.toPlainText().strip() or None,
            "estado": self.estado_combo.currentText()
        }


class PagosTabWidget(QWidget):
    """Widget principal para la gestión de pagos"""
    
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self.pagos = []
        self.pago_seleccionado = None
        self.filtros_actuales = {}
        
        self.setup_ui()
        self.cargar_pagos()
    
    def setup_ui(self):
        """Configurar interfaz del widget"""
        main_layout = QVBoxLayout()
        
        # Título y botones principales
        title_layout = QHBoxLayout()
        title_label = QLabel("Gestión de Pagos")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.setIcon(QIcon("assets/refresh.png"))
        self.refresh_button.clicked.connect(self.cargar_pagos)
        
        self.nuevo_pago_button = QPushButton("Nuevo Pago")
        self.nuevo_pago_button.setIcon(QIcon("assets/add.png"))
        self.nuevo_pago_button.clicked.connect(self.mostrar_dialog_nuevo_pago)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.refresh_button)
        title_layout.addWidget(self.nuevo_pago_button)
        
        # Panel de filtros
        filtros_group = QGroupBox("Filtros")
        filtros_layout = QHBoxLayout()
        
        self.buscar_edit = QLineEdit()
        self.buscar_edit.setPlaceholderText("Buscar por concepto...")
        self.buscar_edit.textChanged.connect(self.aplicar_filtros)
        
        self.estado_filtro_combo = QComboBox()
        self.estado_filtro_combo.addItems(["Todos", "Pendientes", "Completados", "Cancelados", "Reembolsados"])
        self.estado_filtro_combo.currentIndexChanged.connect(self.aplicar_filtros)
        
        self.desde_date = QDateEdit()
        self.desde_date.setCalendarPopup(True)
        # Establecer fecha desde hace 3 meses
        fecha_tres_meses = QDate.currentDate().addMonths(-3)
        self.desde_date.setDate(fecha_tres_meses)
        self.desde_date.dateChanged.connect(self.aplicar_filtros)
        
        self.hasta_date = QDateEdit()
        self.hasta_date.setCalendarPopup(True)
        self.hasta_date.setDate(QDate.currentDate())
        self.hasta_date.dateChanged.connect(self.aplicar_filtros)
        
        filtros_layout.addWidget(QLabel("Buscar:"))
        filtros_layout.addWidget(self.buscar_edit, 2)
        filtros_layout.addWidget(QLabel("Estado:"))
        filtros_layout.addWidget(self.estado_filtro_combo, 1)
        filtros_layout.addWidget(QLabel("Desde:"))
        filtros_layout.addWidget(self.desde_date, 1)
        filtros_layout.addWidget(QLabel("Hasta:"))
        filtros_layout.addWidget(self.hasta_date, 1)
        
        filtros_group.setLayout(filtros_layout)
        
        # Tabla de pagos
        self.pagos_table = QTableWidget()
        self.pagos_table.setColumnCount(7)
        self.pagos_table.setHorizontalHeaderLabels([
            "ID", "Usuario", "Monto", "Fecha", "Método", "Concepto", "Estado"
        ])
        self.pagos_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.pagos_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.pagos_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.pagos_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.pagos_table.setAlternatingRowColors(True)
        self.pagos_table.clicked.connect(self.seleccionar_pago)
        
        # Panel de detalles
        detalles_group = QGroupBox("Detalles del Pago")
        detalles_layout = QVBoxLayout()
        
        # Información del pago
        info_layout = QFormLayout()
        self.id_label = QLabel("")
        self.usuario_label = QLabel("")
        self.monto_label = QLabel("")
        self.fecha_label = QLabel("")
        self.metodo_label = QLabel("")
        self.concepto_label = QLabel("")
        self.estado_label = QLabel("")
        self.notas_label = QLabel("")
        self.notas_label.setWordWrap(True)
        
        info_layout.addRow("ID:", self.id_label)
        info_layout.addRow("Usuario:", self.usuario_label)
        info_layout.addRow("Monto:", self.monto_label)
        info_layout.addRow("Fecha:", self.fecha_label)
        info_layout.addRow("Método:", self.metodo_label)
        info_layout.addRow("Concepto:", self.concepto_label)
        info_layout.addRow("Estado:", self.estado_label)
        info_layout.addRow("Notas:", self.notas_label)
        
        # Botones de acción
        action_layout = QHBoxLayout()
        self.editar_button = QPushButton("Editar Pago")
        self.editar_button.setIcon(QIcon("assets/edit.png"))
        self.editar_button.clicked.connect(self.mostrar_dialog_editar_pago)
        self.editar_button.setEnabled(False)
        
        self.cambiar_estado_button = QPushButton("Marcar como Completado")
        self.cambiar_estado_button.setIcon(QIcon("assets/check.png"))
        self.cambiar_estado_button.clicked.connect(self.cambiar_estado_pago)
        self.cambiar_estado_button.setEnabled(False)
        
        action_layout.addWidget(self.editar_button)
        action_layout.addWidget(self.cambiar_estado_button)
        
        detalles_layout.addLayout(info_layout)
        detalles_layout.addLayout(action_layout)
        detalles_group.setLayout(detalles_layout)
        
        # Resumen financiero
        resumen_group = QGroupBox("Resumen Financiero")
        resumen_layout = QHBoxLayout()
        
        self.total_label = QLabel("Total: $0.00")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.pendiente_label = QLabel("Pendiente: $0.00")
        self.pendiente_label.setStyleSheet("font-size: 14px; color: orange;")
        
        self.completado_label = QLabel("Completado: $0.00")
        self.completado_label.setStyleSheet("font-size: 14px; color: green;")
        
        resumen_layout.addWidget(self.total_label)
        resumen_layout.addStretch()
        resumen_layout.addWidget(self.pendiente_label)
        resumen_layout.addWidget(self.completado_label)
        
        resumen_group.setLayout(resumen_layout)
        
        # Layout principal
        main_layout.addLayout(title_layout)
        main_layout.addWidget(filtros_group)
        main_layout.addWidget(self.pagos_table, 3)
        main_layout.addWidget(detalles_group, 1)
        main_layout.addWidget(resumen_group)
        self.setLayout(main_layout)
    
    def cargar_pagos(self):
        """Cargar la lista de pagos desde la API"""
        self.refresh_button.setEnabled(False)
        self.nuevo_pago_button.setEnabled(False)
        
        # Preparar filtros
        self.obtener_filtros_actuales()
        
        self.worker = PagosLoadWorker(self.api_client, self.filtros_actuales)
        self.worker.pagos_loaded.connect(self.actualizar_tabla_pagos)
        self.worker.error_occurred.connect(self.mostrar_error)
        self.worker.finished.connect(lambda: self.refresh_button.setEnabled(True))
        self.worker.finished.connect(lambda: self.nuevo_pago_button.setEnabled(True))
        self.worker.start()
    
    def obtener_filtros_actuales(self):
        """Obtener los filtros actuales de la interfaz"""
        filtros = {}
        
        # Filtro de estado
        estado_index = self.estado_filtro_combo.currentIndex()
        if estado_index > 0:
            estados = ["pendiente", "completado", "cancelado", "reembolsado"]
            filtros["estado"] = estados[estado_index - 1]
        
        # Filtro de fechas
        desde = self.desde_date.date().toString("yyyy-MM-dd")
        hasta = self.hasta_date.date().toString("yyyy-MM-dd")
        filtros["desde"] = desde
        filtros["hasta"] = hasta
        
        self.filtros_actuales = filtros
    
    def actualizar_tabla_pagos(self, pagos):
        """Actualizar la tabla con los pagos cargados"""
        self.pagos = pagos
        self.aplicar_filtros()
    
    def aplicar_filtros(self):
        """Filtrar los pagos según los criterios de búsqueda"""
        texto_busqueda = self.buscar_edit.text().lower()
        
        pagos_filtrados = []
        for pago in self.pagos:
            # Filtrar por texto de búsqueda en concepto
            if texto_busqueda and texto_busqueda not in pago.get("concepto", "").lower():
                continue
            
            pagos_filtrados.append(pago)
        
        self.mostrar_pagos_en_tabla(pagos_filtrados)
        self.actualizar_resumen_financiero(pagos_filtrados)
    
    def mostrar_pagos_en_tabla(self, pagos):
        """Mostrar los pagos filtrados en la tabla"""
        self.pagos_table.setRowCount(0)
        
        for pago in pagos:
            row = self.pagos_table.rowCount()
            self.pagos_table.insertRow(row)
            
            # Obtener nombre de usuario
            usuario_nombre = f"ID: {pago.get('usuario_id')}"
            
            # Formato de fecha
            fecha_str = pago.get("fecha_pago", "")
            fecha_formateada = fecha_str
            if fecha_str:
                try:
                    fecha_dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                    fecha_formateada = fecha_dt.strftime("%d/%m/%Y")
                except:
                    pass
            
            # Formato de monto
            monto = pago.get("monto", 0)
            monto_str = f"${monto:.2f}"
            
            # Insertar datos en la fila
            self.pagos_table.setItem(row, 0, QTableWidgetItem(str(pago.get("id", ""))))
            self.pagos_table.setItem(row, 1, QTableWidgetItem(usuario_nombre))
            self.pagos_table.setItem(row, 2, QTableWidgetItem(monto_str))
            self.pagos_table.setItem(row, 3, QTableWidgetItem(fecha_formateada))
            self.pagos_table.setItem(row, 4, QTableWidgetItem(pago.get("metodo_pago", "")))
            self.pagos_table.setItem(row, 5, QTableWidgetItem(pago.get("concepto", "")))
            
            # Estado con color
            estado_item = QTableWidgetItem(pago.get("estado", ""))
            if pago.get("estado") == "completado":
                estado_item.setForeground(QColor(0, 128, 0))  # Verde
            elif pago.get("estado") == "pendiente":
                estado_item.setForeground(QColor(255, 128, 0))  # Naranja
            elif pago.get("estado") == "cancelado":
                estado_item.setForeground(QColor(255, 0, 0))  # Rojo
            
            self.pagos_table.setItem(row, 6, estado_item)
    
    def actualizar_resumen_financiero(self, pagos):
        """Actualizar el resumen financiero con los datos filtrados"""
        total = sum(pago.get("monto", 0) for pago in pagos)
        
        pendiente = sum(pago.get("monto", 0) for pago in pagos 
                        if pago.get("estado") == "pendiente")
        
        completado = sum(pago.get("monto", 0) for pago in pagos 
                         if pago.get("estado") == "completado")
        
        self.total_label.setText(f"Total: ${total:.2f}")
        self.pendiente_label.setText(f"Pendiente: ${pendiente:.2f}")
        self.completado_label.setText(f"Completado: ${completado:.2f}")
    
    def seleccionar_pago(self):
        """Manejar la selección de un pago en la tabla"""
        row = self.pagos_table.currentRow()
        if row >= 0:
            pago_id = int(self.pagos_table.item(row, 0).text())
            
            # Encontrar el pago seleccionado
            for pago in self.pagos:
                if pago.get("id") == pago_id:
                    self.pago_seleccionado = pago
                    self.mostrar_detalles_pago(pago)
                    
                    # Habilitar botones
                    self.editar_button.setEnabled(True)
                    
                    # Configurar botón de cambio de estado
                    if pago.get("estado") == "pendiente":
                        self.cambiar_estado_button.setText("Marcar como Completado")
                        self.cambiar_estado_button.setEnabled(True)
                    elif pago.get("estado") == "completado":
                        self.cambiar_estado_button.setText("Marcar como Pendiente")
                        self.cambiar_estado_button.setEnabled(True)
                    else:
                        self.cambiar_estado_button.setEnabled(False)
                    
                    break
    
    def mostrar_detalles_pago(self, pago):
        """Mostrar los detalles del pago seleccionado"""
        self.id_label.setText(str(pago.get("id", "")))
        self.usuario_label.setText(f"ID: {pago.get('usuario_id')}")
        self.monto_label.setText(f"${pago.get('monto', 0):.2f}")
        
        # Formato de fecha
        fecha_str = pago.get("fecha_pago", "")
        fecha_formateada = fecha_str
        if fecha_str:
            try:
                fecha_dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                fecha_formateada = fecha_dt.strftime("%d/%m/%Y")
            except:
                pass
        
        self.fecha_label.setText(fecha_formateada)
        self.metodo_label.setText(pago.get("metodo_pago", ""))
        self.concepto_label.setText(pago.get("concepto", ""))
        
        # Estado con color
        estado = pago.get("estado", "")
        if estado == "completado":
            self.estado_label.setText(f'<span style="color: green;">{estado}</span>')
        elif estado == "pendiente":
            self.estado_label.setText(f'<span style="color: orange;">{estado}</span>')
        elif estado == "cancelado":
            self.estado_label.setText(f'<span style="color: red;">{estado}</span>')
        else:
            self.estado_label.setText(estado)
        
        self.notas_label.setText(pago.get("notas", "") or "Sin notas adicionales")
    
    def mostrar_dialog_nuevo_pago(self):
        """Mostrar diálogo para crear un nuevo pago"""
        dialog = PagoDialog(self, self.api_client)
        if dialog.exec():
            datos_pago = dialog.get_data()
            try:
                respuesta = self.api_client.crear_pago_sync(datos_pago)
                QMessageBox.information(self, "Éxito", "Pago registrado correctamente")
                self.cargar_pagos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo registrar el pago: {str(e)}")
    
    def mostrar_dialog_editar_pago(self):
        """Mostrar diálogo para editar el pago seleccionado"""
        if not self.pago_seleccionado:
            return
        
        dialog = PagoDialog(self, self.api_client, self.pago_seleccionado)
        if dialog.exec():
            datos_pago = dialog.get_data()
            try:
                respuesta = self.api_client.actualizar_pago_sync(self.pago_seleccionado["id"], datos_pago)
                QMessageBox.information(self, "Éxito", "Pago actualizado correctamente")
                self.cargar_pagos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el pago: {str(e)}")
    
    def cambiar_estado_pago(self):
        """Cambiar el estado del pago entre pendiente y completado"""
        if not self.pago_seleccionado:
            return
        
        estado_actual = self.pago_seleccionado.get("estado")
        nuevo_estado = "completado" if estado_actual == "pendiente" else "pendiente"
        
        try:
            respuesta = self.api_client.actualizar_pago_sync(
                self.pago_seleccionado["id"], 
                {"estado": nuevo_estado}
            )
            
            mensaje = "completado" if nuevo_estado == "completado" else "pendiente"
            QMessageBox.information(self, "Éxito", f"Pago marcado como {mensaje} correctamente")
            self.cargar_pagos()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cambiar el estado del pago: {str(e)}")
    
    def mostrar_error(self, mensaje):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, "Error", mensaje)
