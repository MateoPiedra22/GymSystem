"""
Widget de Estado de Sincronización en Tiempo Real
Sistema de Gestión de Gimnasio v6 - Fase 5.1

Widget para monitorear el estado de la sincronización en tiempo real:
- Estado de conexión WebSocket
- Estadísticas de conflictos resueltos
- Métricas de compresión de datos
- Rendimiento de sincronización
- Indicadores visuales de estado
"""

import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QProgressBar, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap

from utils.realtime_sync import SyncStatus, get_realtime_sync_manager
from utils.performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)

class RealtimeStatusWidget(QWidget):
    """
    Widget de estado de sincronización en tiempo real
    
    Muestra información en tiempo real sobre:
    - Estado de conexión WebSocket
    - Estadísticas de sincronización
    - Conflictos resueltos
    - Compresión de datos
    - Rendimiento general
    """
    
    # Señales
    status_changed = pyqtSignal(str)  # Nuevo estado
    conflict_detected = pyqtSignal(dict)  # Conflicto detectado
    sync_stats_updated = pyqtSignal(dict)  # Estadísticas actualizadas
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Gestor de sincronización
        self.sync_manager = get_realtime_sync_manager()
        self.performance_monitor = get_performance_monitor()
        
        # Estado actual
        self.current_status = SyncStatus.DISCONNECTED
        self.last_stats = {}
        
        # Timers
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(1000)  # Actualizar cada segundo
        
        # UI
        self.setup_ui()
        
        # Conectar callbacks
        if self.sync_manager:
            self.sync_manager.add_status_callback(self._on_status_changed)
            self.sync_manager.add_conflict_callback(self._on_conflict_detected)
            
    def setup_ui(self):
        """Configurar interfaz del widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("🔄 Sincronización en Tiempo Real")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Estado de conexión
        self._create_connection_status_group(layout)
        
        # Estadísticas de sincronización
        self._create_sync_stats_group(layout)
        
        # Estadísticas de conflictos
        self._create_conflict_stats_group(layout)
        
        # Estadísticas de compresión
        self._create_compression_stats_group(layout)
        
        # Controles
        self._create_controls_group(layout)
        
        # Aplicar estilos
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid var(--border-color);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: var(--text-color);
            }
            QPushButton {
                background: var(--primary-color);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: var(--primary-hover);
            }
            QPushButton:pressed {
                background: var(--primary-pressed);
            }
            QProgressBar {
                border: 1px solid var(--border-color);
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: var(--success-color);
                border-radius: 3px;
            }
        """)
        
    def _create_connection_status_group(self, parent_layout):
        """Crear grupo de estado de conexión"""
        group = QGroupBox("Estado de Conexión")
        layout = QVBoxLayout(group)
        
        # Indicador de estado principal
        self.status_indicator = QLabel("Desconectado")
        self.status_indicator.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_indicator.setStyleSheet("""
            QLabel {
                padding: 10px;
                border-radius: 6px;
                background: var(--error-color);
                color: white;
            }
        """)
        layout.addWidget(self.status_indicator)
        
        # Información adicional
        info_layout = QGridLayout()
        
        # Tiempo de conexión
        self.uptime_label = QLabel("Tiempo conectado: --")
        info_layout.addWidget(QLabel("⏱️ Tiempo:"), 0, 0)
        info_layout.addWidget(self.uptime_label, 0, 1)
        
        # Intentos de reconexión
        self.reconnect_label = QLabel("Intentos: 0")
        info_layout.addWidget(QLabel("🔄 Reconexiones:"), 1, 0)
        info_layout.addWidget(self.reconnect_label, 1, 1)
        
        # URL del servidor
        self.server_label = QLabel("Servidor: --")
        info_layout.addWidget(QLabel("🌐 Servidor:"), 2, 0)
        info_layout.addWidget(self.server_label, 2, 1)
        
        layout.addLayout(info_layout)
        parent_layout.addWidget(group)
        
    def _create_sync_stats_group(self, parent_layout):
        """Crear grupo de estadísticas de sincronización"""
        group = QGroupBox("Estadísticas de Sincronización")
        layout = QGridLayout(group)
        
        # Operaciones enviadas
        self.sent_label = QLabel("0")
        layout.addWidget(QLabel("📤 Enviadas:"), 0, 0)
        layout.addWidget(self.sent_label, 0, 1)
        
        # Operaciones recibidas
        self.received_label = QLabel("0")
        layout.addWidget(QLabel("📥 Recibidas:"), 1, 0)
        layout.addWidget(self.received_label, 1, 1)
        
        # Última sincronización
        self.last_sync_label = QLabel("--")
        layout.addWidget(QLabel("🕐 Última sync:"), 2, 0)
        layout.addWidget(self.last_sync_label, 2, 1)
        
        # Tasa de sincronización
        self.sync_rate_label = QLabel("0 ops/s")
        layout.addWidget(QLabel("⚡ Tasa:"), 3, 0)
        layout.addWidget(self.sync_rate_label, 3, 1)
        
        parent_layout.addWidget(group)
        
    def _create_conflict_stats_group(self, parent_layout):
        """Crear grupo de estadísticas de conflictos"""
        group = QGroupBox("Resolución de Conflictos")
        layout = QGridLayout(group)
        
        # Conflictos resueltos
        self.conflicts_label = QLabel("0")
        layout.addWidget(QLabel("✅ Resueltos:"), 0, 0)
        layout.addWidget(self.conflicts_label, 0, 1)
        
        # Estrategia de resolución
        self.strategy_label = QLabel("Automática")
        layout.addWidget(QLabel("🎯 Estrategia:"), 1, 0)
        layout.addWidget(self.strategy_label, 1, 1)
        
        # Tiempo promedio de resolución
        self.resolve_time_label = QLabel("--")
        layout.addWidget(QLabel("⏱️ Tiempo avg:"), 2, 0)
        layout.addWidget(self.resolve_time_label, 2, 1)
        
        # Barra de progreso de conflictos
        self.conflict_progress = QProgressBar()
        self.conflict_progress.setMaximum(100)
        self.conflict_progress.setValue(0)
        layout.addWidget(QLabel("📊 Progreso:"), 3, 0)
        layout.addWidget(self.conflict_progress, 3, 1)
        
        parent_layout.addWidget(group)
        
    def _create_compression_stats_group(self, parent_layout):
        """Crear grupo de estadísticas de compresión"""
        group = QGroupBox("Compresión de Datos")
        layout = QGridLayout(group)
        
        # Tasa de compresión
        self.compression_rate_label = QLabel("0%")
        layout.addWidget(QLabel("🗜️ Tasa:"), 0, 0)
        layout.addWidget(self.compression_rate_label, 0, 1)
        
        # Ratio de compresión
        self.compression_ratio_label = QLabel("1.0x")
        layout.addWidget(QLabel("📏 Ratio:"), 1, 0)
        layout.addWidget(self.compression_ratio_label, 1, 1)
        
        # Mensajes comprimidos
        self.compressed_label = QLabel("0")
        layout.addWidget(QLabel("📦 Comprimidos:"), 2, 0)
        layout.addWidget(self.compressed_label, 2, 1)
        
        # Mensajes sin comprimir
        self.uncompressed_label = QLabel("0")
        layout.addWidget(QLabel("📄 Sin comprimir:"), 3, 0)
        layout.addWidget(self.uncompressed_label, 3, 1)
        
        parent_layout.addWidget(group)
        
    def _create_controls_group(self, parent_layout):
        """Crear grupo de controles"""
        group = QGroupBox("Controles")
        layout = QHBoxLayout(group)
        
        # Botón de reconexión
        self.reconnect_button = QPushButton("🔄 Reconectar")
        self.reconnect_button.clicked.connect(self._reconnect)
        layout.addWidget(self.reconnect_button)
        
        # Botón de estadísticas
        self.stats_button = QPushButton("📊 Estadísticas")
        self.stats_button.clicked.connect(self._show_detailed_stats)
        layout.addWidget(self.stats_button)
        
        # Botón de configuración
        self.config_button = QPushButton("⚙️ Configurar")
        self.config_button.clicked.connect(self._show_config)
        layout.addWidget(self.config_button)
        
        parent_layout.addWidget(group)
        
    def _on_status_changed(self, new_status: SyncStatus, old_status: SyncStatus):
        """Callback para cambios de estado"""
        try:
            self.current_status = new_status
            self._update_status_display(new_status)
            self.status_changed.emit(new_status.value)
            
        except Exception as e:
            logger.error(f"Error manejando cambio de estado: {e}")
            
    def _on_conflict_detected(self, conflict_data):
        """Callback para conflictos detectados"""
        try:
            self.conflict_detected.emit(conflict_data)
            
        except Exception as e:
            logger.error(f"Error manejando conflicto: {e}")
            
    def _update_display(self):
        """Actualizar display con información en tiempo real"""
        try:
            if not self.sync_manager:
                return
                
            # Obtener estadísticas actuales
            stats = self.sync_manager.get_stats()
            
            # Actualizar solo si hay cambios
            if stats != self.last_stats:
                self._update_stats_display(stats)
                self.last_stats = stats
                self.sync_stats_updated.emit(stats)
                
        except Exception as e:
            logger.error(f"Error actualizando display: {e}")
            
    def _update_status_display(self, status: SyncStatus):
        """Actualizar display de estado"""
        try:
            # Configurar indicador de estado
            if status == SyncStatus.CONNECTED:
                self.status_indicator.setText("🟢 Conectado")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-radius: 6px;
                        background: var(--success-color);
                        color: white;
                    }
                """)
            elif status == SyncStatus.CONNECTING:
                self.status_indicator.setText("🟡 Conectando...")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-radius: 6px;
                        background: var(--warning-color);
                        color: white;
                    }
                """)
            elif status == SyncStatus.RECONNECTING:
                self.status_indicator.setText("🔄 Reconectando...")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-radius: 6px;
                        background: var(--warning-color);
                        color: white;
                    }
                """)
            elif status == SyncStatus.SYNCING:
                self.status_indicator.setText("⚡ Sincronizando...")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-radius: 6px;
                        background: var(--info-color);
                        color: white;
                    }
                """)
            elif status == SyncStatus.CONFLICT:
                self.status_indicator.setText("⚠️ Conflicto")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-radius: 6px;
                        background: var(--warning-color);
                        color: white;
                    }
                """)
            elif status == SyncStatus.ERROR:
                self.status_indicator.setText("🔴 Error")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-radius: 6px;
                        background: var(--error-color);
                        color: white;
                    }
                """)
            else:  # DISCONNECTED
                self.status_indicator.setText("🔴 Desconectado")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-radius: 6px;
                        background: var(--error-color);
                        color: white;
                    }
                """)
                
        except Exception as e:
            logger.error(f"Error actualizando display de estado: {e}")
            
    def _update_stats_display(self, stats: Dict[str, Any]):
        """Actualizar display de estadísticas"""
        try:
            # Estadísticas de conexión
            uptime = stats.get("connection_uptime", 0)
            if uptime > 0:
                uptime_str = self._format_uptime(uptime)
                self.uptime_label.setText(f"Tiempo conectado: {uptime_str}")
                
            reconnect_attempts = stats.get("reconnect_attempts", 0)
            self.reconnect_label.setText(f"Intentos: {reconnect_attempts}")
            
            # Estadísticas de sincronización
            operations_sent = stats.get("operations_sent", 0)
            self.sent_label.setText(str(operations_sent))
            
            operations_received = stats.get("operations_received", 0)
            self.received_label.setText(str(operations_received))
            
            # Calcular tasa de sincronización
            if hasattr(self, '_last_operations_count'):
                time_diff = 1  # 1 segundo entre actualizaciones
                rate = (operations_sent + operations_received - self._last_operations_count) / time_diff
                self.sync_rate_label.setText(f"{rate:.1f} ops/s")
            self._last_operations_count = operations_sent + operations_received
            
            # Última sincronización
            last_sync = stats.get("last_sync")
            if last_sync:
                self.last_sync_label.setText(self._format_timestamp(last_sync))
                
            # Estadísticas de conflictos
            conflicts_resolved = stats.get("conflicts_resolved", 0)
            self.conflicts_label.setText(str(conflicts_resolved))
            
            conflict_stats = stats.get("conflict_stats", {})
            total_conflicts = conflict_stats.get("total_conflicts", 0)
            if total_conflicts > 0:
                progress = min(100, (conflicts_resolved / total_conflicts) * 100)
                self.conflict_progress.setValue(int(progress))
                
            # Estadísticas de compresión
            compression_stats = stats.get("compression_stats", {})
            compression_rate = compression_stats.get("compression_rate", 0)
            self.compression_rate_label.setText(f"{compression_rate:.1f}%")
            
            avg_ratio = compression_stats.get("avg_compression_ratio", 1.0)
            self.compression_ratio_label.setText(f"{avg_ratio:.2f}x")
            
            compressed_messages = compression_stats.get("compressed_messages", 0)
            self.compressed_label.setText(str(compressed_messages))
            
            uncompressed_messages = compression_stats.get("uncompressed_messages", 0)
            self.uncompressed_label.setText(str(uncompressed_messages))
            
        except Exception as e:
            logger.error(f"Error actualizando display de estadísticas: {e}")
            
    def _format_uptime(self, seconds: float) -> str:
        """Formatear tiempo de conexión"""
        try:
            if seconds < 60:
                return f"{seconds:.0f}s"
            elif seconds < 3600:
                minutes = seconds / 60
                return f"{minutes:.0f}m"
            else:
                hours = seconds / 3600
                return f"{hours:.1f}h"
        except Exception as e:
            logger.error(f"Error formateando uptime: {e}")
            return "--"
            
    def _format_timestamp(self, timestamp) -> str:
        """Formatear timestamp"""
        try:
            if isinstance(timestamp, str):
                # Parsear timestamp ISO
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime("%H:%M:%S")
            else:
                return str(timestamp)
        except Exception as e:
            logger.error(f"Error formateando timestamp: {e}")
            return "--"
            
    def _reconnect(self):
        """Reconectar manualmente"""
        try:
            if self.sync_manager:
                # Forzar reconexión
                self.sync_manager.stop()
                # Reiniciar después de un breve delay
                QTimer.singleShot(1000, self._restart_sync)
                
        except Exception as e:
            logger.error(f"Error reconectando: {e}")
            
    def _restart_sync(self):
        """Reiniciar sincronización"""
        try:
            if self.sync_manager:
                # El gestor se reiniciará automáticamente
                pass
                
        except Exception as e:
            logger.error(f"Error reiniciando sincronización: {e}")
            
    def _show_detailed_stats(self):
        """Mostrar estadísticas detalladas"""
        try:
            if not self.sync_manager:
                return
                
            stats = self.sync_manager.get_stats()
            
            # Crear diálogo con estadísticas detalladas
            from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Estadísticas Detalladas de Sincronización")
            dialog.setModal(True)
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Área de texto con estadísticas
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            
            # Formatear estadísticas
            stats_text = self._format_detailed_stats(stats)
            text_edit.setPlainText(stats_text)
            
            layout.addWidget(text_edit)
            
            # Botón de cerrar
            close_button = QPushButton("Cerrar")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error mostrando estadísticas detalladas: {e}")
            
    def _format_detailed_stats(self, stats: Dict[str, Any]) -> str:
        """Formatear estadísticas detalladas"""
        try:
            text = "ESTADÍSTICAS DETALLADAS DE SINCRONIZACIÓN\n"
            text += "=" * 50 + "\n\n"
            
            # Estado general
            text += f"Estado: {stats.get('status', 'unknown')}\n"
            text += f"Operaciones enviadas: {stats.get('operations_sent', 0)}\n"
            text += f"Operaciones recibidas: {stats.get('operations_received', 0)}\n"
            text += f"Conflictos resueltos: {stats.get('conflicts_resolved', 0)}\n"
            text += f"Tiempo conectado: {self._format_uptime(stats.get('connection_uptime', 0))}\n"
            text += f"Intentos de reconexión: {stats.get('reconnect_attempts', 0)}\n\n"
            
            # Estadísticas de compresión
            compression_stats = stats.get("compression_stats", {})
            text += "COMPRESIÓN DE DATOS\n"
            text += "-" * 20 + "\n"
            text += f"Total de mensajes: {compression_stats.get('total_messages', 0)}\n"
            text += f"Mensajes comprimidos: {compression_stats.get('compressed_messages', 0)}\n"
            text += f"Mensajes sin comprimir: {compression_stats.get('uncompressed_messages', 0)}\n"
            text += f"Tasa de compresión: {compression_stats.get('compression_rate', 0):.1f}%\n"
            text += f"Ratio promedio: {compression_stats.get('avg_compression_ratio', 1.0):.2f}x\n\n"
            
            # Estadísticas de conflictos
            conflict_stats = stats.get("conflict_stats", {})
            text += "RESOLUCIÓN DE CONFLICTOS\n"
            text += "-" * 25 + "\n"
            text += f"Total de conflictos: {conflict_stats.get('total_conflicts', 0)}\n"
            text += f"Resolución automática: {'Sí' if conflict_stats.get('auto_resolve_enabled', False) else 'No'}\n"
            
            resolution_dist = conflict_stats.get("resolution_distribution", {})
            if resolution_dist:
                text += "Distribución de resoluciones:\n"
                for strategy, count in resolution_dist.items():
                    text += f"  - {strategy}: {count}\n"
                    
            return text
            
        except Exception as e:
            logger.error(f"Error formateando estadísticas detalladas: {e}")
            return "Error formateando estadísticas"
            
    def _show_config(self):
        """Mostrar configuración de sincronización"""
        try:
            # Crear diálogo de configuración
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Configuración de Sincronización")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            # URL del WebSocket
            url_layout = QHBoxLayout()
            url_layout.addWidget(QLabel("URL WebSocket:"))
            url_edit = QLineEdit()
            url_edit.setText(self.sync_manager.websocket_url if self.sync_manager else "")
            url_layout.addWidget(url_edit)
            layout.addLayout(url_layout)
            
            # Opciones de sincronización
            selective_check = QCheckBox("Sincronización selectiva")
            selective_check.setChecked(self.sync_manager.selective_sync if self.sync_manager else False)
            layout.addWidget(selective_check)
            
            compression_check = QCheckBox("Compresión de datos")
            compression_check.setChecked(True)
            layout.addWidget(compression_check)
            
            # Botones
            button_layout = QHBoxLayout()
            save_button = QPushButton("Guardar")
            cancel_button = QPushButton("Cancelar")
            button_layout.addWidget(save_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            # Conectar botones
            save_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)
            
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error mostrando configuración: {e}")
            
    def get_current_status(self) -> SyncStatus:
        """Obtener estado actual"""
        return self.current_status
        
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas actuales"""
        if self.sync_manager:
            return self.sync_manager.get_stats()
        return {}
        
    def refresh_display(self):
        """Refrescar display manualmente"""
        self._update_display()
        
    def set_update_interval(self, interval_ms: int):
        """Establecer intervalo de actualización"""
        self.update_timer.setInterval(interval_ms)
        
    def stop_updates(self):
        """Detener actualizaciones automáticas"""
        self.update_timer.stop()
        
    def start_updates(self):
        """Iniciar actualizaciones automáticas"""
        self.update_timer.start() 