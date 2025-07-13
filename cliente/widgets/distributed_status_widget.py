"""
Widget para mostrar el estado de la sincronización distribuida
Muestra información de sincronización y estado de conexión
"""

from typing import Dict, Any, Optional
import time
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QFrame, QSizePolicy, QRadioButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QColor

from ..api_client import ApiClient

class DistributedStatusWidget(QWidget):
    """
    Widget para mostrar el estado de la sincronización distribuida
    
    Muestra información sobre:
    - Estado de conexión con el servidor
    - Última sincronización
    - Elementos pendientes de sincronizar
    - Conflictos detectados
    """
    
    # Señal para notificar sobre cambios importantes
    sync_status_changed = pyqtSignal(dict)
    
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        
        # Estado inicial
        self.estado = {
            "conectado": True,
            "ultima_sync": datetime.now(),
            "elementos_pendientes": 0,
            "conflictos": 0,
            "sync_en_progreso": False,
            "progreso_sync": 0,
            "modo_offline": False
        }
        
        # Configurar temporizador para actualizaciones
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.actualizar_estado)
        self.update_timer.start(5000)  # Actualizar cada 5 segundos
        
        self.setupUI()
        self.actualizar_ui()
    
    def setupUI(self):
        """Configura la interfaz de usuario del widget"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Título
        title_frame = QFrame()
        title_frame.setFrameShape(QFrame.Shape.StyledPanel)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(5, 5, 5, 5)
        
        title_label = QLabel("Estado de Sincronización")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Indicador de estado
        self.indicator = QLabel()
        self.indicator.setFixedSize(12, 12)
        self.indicator.setStyleSheet("background-color: green; border-radius: 6px;")
        title_layout.addWidget(self.indicator)
        
        main_layout.addWidget(title_frame)
        
        # Panel de estado
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_layout = QVBoxLayout(status_frame)
        
        # Estado de conexión
        conn_layout = QHBoxLayout()
        conn_layout.addWidget(QLabel("Conexión:"))
        self.lbl_conexion = QLabel("Conectado")
        self.lbl_conexion.setStyleSheet("font-weight: bold; color: green;")
        conn_layout.addWidget(self.lbl_conexion)
        conn_layout.addStretch()
        status_layout.addLayout(conn_layout)
        
        # Última sincronización
        last_sync_layout = QHBoxLayout()
        last_sync_layout.addWidget(QLabel("Última sincronización:"))
        self.lbl_ultima_sync = QLabel("Hace 0 minutos")
        last_sync_layout.addWidget(self.lbl_ultima_sync)
        last_sync_layout.addStretch()
        status_layout.addLayout(last_sync_layout)
        
        # Elementos pendientes
        pending_layout = QHBoxLayout()
        pending_layout.addWidget(QLabel("Pendientes:"))
        self.lbl_pendientes = QLabel("0 elementos")
        pending_layout.addWidget(self.lbl_pendientes)
        pending_layout.addStretch()
        status_layout.addLayout(pending_layout)
        
        # Conflictos
        conflicts_layout = QHBoxLayout()
        conflicts_layout.addWidget(QLabel("Conflictos:"))
        self.lbl_conflictos = QLabel("0 conflictos")
        conflicts_layout.addWidget(self.lbl_conflictos)
        conflicts_layout.addStretch()
        status_layout.addLayout(conflicts_layout)
        
        # Modo offline
        offline_layout = QHBoxLayout()
        offline_layout.addWidget(QLabel("Modo:"))
        self.lbl_modo = QLabel("Online")
        self.lbl_modo.setStyleSheet("font-weight: bold;")
        offline_layout.addWidget(self.lbl_modo)
        offline_layout.addStretch()
        status_layout.addLayout(offline_layout)
        
        # Barra de progreso para sincronización
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(status_frame)
        
        # Botones de acción
        action_frame = QFrame()
        action_frame.setFrameShape(QFrame.Shape.StyledPanel)
        action_layout = QHBoxLayout(action_frame)
        
        # Botón sincronizar
        self.btn_sync = QPushButton("Sincronizar")
        self.btn_sync.setIcon(QIcon("assets/sync.png"))
        self.btn_sync.clicked.connect(self.iniciar_sincronizacion)
        action_layout.addWidget(self.btn_sync)
        
        # Botón resolver conflictos
        self.btn_resolve = QPushButton("Resolver")
        self.btn_resolve.setIcon(QIcon("assets/resolve.png"))
        self.btn_resolve.setEnabled(False)
        self.btn_resolve.clicked.connect(self.resolver_conflictos)
        action_layout.addWidget(self.btn_resolve)
        
        main_layout.addWidget(action_frame)
        
        # Espacio flexible
        main_layout.addStretch()
    
    def actualizar_estado(self):
        """Actualiza el estado desde el servidor"""
        try:
            # Consultar estado real desde la API
            self._obtener_estado_real()
            
            # Actualizar la UI con el nuevo estado
            self.actualizar_ui()
            
            # Emitir señal de cambio si hay algo importante
            if self.estado["elementos_pendientes"] > 0 or self.estado["conflictos"] > 0:
                self.sync_status_changed.emit(self.estado)
        
        except Exception as e:
            # Si hay error de conexión, marcar como desconectado
            self.estado["conectado"] = False
            self.estado["modo_offline"] = True
            self.actualizar_ui()
            logger.error(f"Error actualizando estado: {e}")
    
    def _obtener_estado_real(self):
        """Obtiene el estado real desde la API"""
        try:
            # Verificar conexión con el servidor
            ping_response = self.api_client._make_request('GET', '/health')
            self.estado["conectado"] = ping_response is not None
            
            if self.estado["conectado"]:
                # Obtener estado de sincronización
                sync_response = self.api_client._make_request('GET', '/sync/status')
                if sync_response and 'data' in sync_response:
                    sync_data = sync_response['data']
                    self.estado["elementos_pendientes"] = sync_data.get('elementos_pendientes', 0)
                    self.estado["conflictos"] = sync_data.get('conflictos', 0)
                    self.estado["modo_offline"] = sync_data.get('modo_offline', False)
                    
                    # Actualizar última sincronización si existe
                    if 'ultima_sincronizacion' in sync_data:
                        ultima_sync_str = sync_data['ultima_sincronizacion']
                        try:
                            self.estado["ultima_sync"] = datetime.fromisoformat(ultima_sync_str.replace('Z', '+00:00'))
                        except:
                            self.estado["ultima_sync"] = datetime.now()
                else:
                    # Si no hay datos de sync, asumir estado básico
                    self.estado["elementos_pendientes"] = 0
                    self.estado["conflictos"] = 0
                    self.estado["modo_offline"] = False
            else:
                # Si no hay conexión, activar modo offline
                self.estado["modo_offline"] = True
                self.estado["elementos_pendientes"] = 0
                self.estado["conflictos"] = 0
                
        except Exception as e:
            logger.error(f"Error obteniendo estado real: {e}")
            # En caso de error, mantener estado anterior pero marcar como desconectado
            self.estado["conectado"] = False
            self.estado["modo_offline"] = True
    
    def actualizar_ui(self):
        """Actualiza la interfaz con el estado actual"""
        # Actualizar indicador de conexión
        if self.estado["conectado"]:
            self.indicator.setStyleSheet("background-color: green; border-radius: 6px;")
            self.lbl_conexion.setText("Conectado")
            self.lbl_conexion.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.indicator.setStyleSheet("background-color: red; border-radius: 6px;")
            self.lbl_conexion.setText("Desconectado")
            self.lbl_conexion.setStyleSheet("font-weight: bold; color: red;")
        
        # Actualizar modo
        if self.estado["modo_offline"]:
            self.lbl_modo.setText("Offline")
            self.lbl_modo.setStyleSheet("font-weight: bold; color: orange;")
        else:
            self.lbl_modo.setText("Online")
            self.lbl_modo.setStyleSheet("font-weight: bold; color: green;")
        
        # Actualizar última sincronización
        tiempo_transcurrido = datetime.now() - self.estado["ultima_sync"]
        minutos = int(tiempo_transcurrido.total_seconds() / 60)
        
        if minutos < 1:
            self.lbl_ultima_sync.setText("Hace menos de 1 minuto")
        elif minutos == 1:
            self.lbl_ultima_sync.setText("Hace 1 minuto")
        else:
            self.lbl_ultima_sync.setText(f"Hace {minutos} minutos")
        
        # Actualizar elementos pendientes
        pendientes = self.estado["elementos_pendientes"]
        if pendientes == 0:
            self.lbl_pendientes.setText("0 elementos")
            self.lbl_pendientes.setStyleSheet("")
        elif pendientes == 1:
            self.lbl_pendientes.setText("1 elemento")
            self.lbl_pendientes.setStyleSheet("color: orange;")
        else:
            self.lbl_pendientes.setText(f"{pendientes} elementos")
            self.lbl_pendientes.setStyleSheet("color: orange;")
        
        # Actualizar conflictos
        conflictos = self.estado["conflictos"]
        if conflictos == 0:
            self.lbl_conflictos.setText("0 conflictos")
            self.lbl_conflictos.setStyleSheet("")
            self.btn_resolve.setEnabled(False)
        elif conflictos == 1:
            self.lbl_conflictos.setText("1 conflicto")
            self.lbl_conflictos.setStyleSheet("color: red; font-weight: bold;")
            self.btn_resolve.setEnabled(True)
        else:
            self.lbl_conflictos.setText(f"{conflictos} conflictos")
            self.lbl_conflictos.setStyleSheet("color: red; font-weight: bold;")
            self.btn_resolve.setEnabled(True)
        
        # Actualizar barra de progreso
        if self.estado["sync_en_progreso"]:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(self.estado["progreso_sync"])
            self.btn_sync.setEnabled(False)
        else:
            self.progress_bar.setVisible(False)
            self.btn_sync.setEnabled(True)
    
    def iniciar_sincronizacion(self):
        """Inicia el proceso de sincronización"""
        # Marcar como en progreso
        self.estado["sync_en_progreso"] = True
        self.estado["progreso_sync"] = 0
        self.actualizar_ui()
        
        # Simular progreso
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.avanzar_progreso)
        self.progress_timer.start(100)  # Actualizar cada 100ms
    
    def avanzar_progreso(self):
        """Avanza el progreso de sincronización"""
        if self.estado["progreso_sync"] < 100:
            self.estado["progreso_sync"] += 2
            self.actualizar_ui()
        else:
            # Sincronización completada
            self.progress_timer.stop()
            self.estado["sync_en_progreso"] = False
            self.estado["ultima_sync"] = datetime.now()
            self.estado["elementos_pendientes"] = 0
            self.actualizar_ui()
    
    def resolver_conflictos(self):
        """Muestra diálogo para resolver conflictos"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QListWidget, QListWidgetItem, QVBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Resolver Conflictos")
        dialog.resize(500, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Lista de conflictos
        layout.addWidget(QLabel("Seleccione los conflictos a resolver:"))
        
        conflict_list = QListWidget()
        
        # Agregar conflictos simulados
        for i in range(self.estado["conflictos"]):
            item = QListWidgetItem(f"Conflicto #{i+1}: Usuario modificado en local y servidor")
            item.setCheckState(Qt.CheckState.Checked)
            conflict_list.addItem(item)
        
        layout.addWidget(conflict_list)
        
        # Opciones de resolución
        resolution_layout = QHBoxLayout()
        
        rb_local = QRadioButton("Priorizar Local")
        rb_server = QRadioButton("Priorizar Servidor")
        rb_manual = QRadioButton("Resolver Manualmente")
        rb_server.setChecked(True)
        
        resolution_layout.addWidget(rb_local)
        resolution_layout.addWidget(rb_server)
        resolution_layout.addWidget(rb_manual)
        
        layout.addLayout(resolution_layout)
        
        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        
        # Mostrar diálogo
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Simular resolución
            self.estado["conflictos"] = 0
            self.actualizar_ui()
