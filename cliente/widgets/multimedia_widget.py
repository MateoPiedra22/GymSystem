"""
Widget para gestión de contenido multimedia en ejercicios y rutinas
"""

import os
import sys
import json
import mimetypes
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
    from PyQt6.QtMultimedia import *
    from PyQt6.QtMultimediaWidgets import *
except ImportError:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtMultimedia import *
    from PyQt5.QtMultimediaWidgets import *

# Agregar el directorio padre al path para importar api_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import ApiClient


class MultimediaItem:
    """Clase para representar un elemento multimedia"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id', '')
        self.nombre = data.get('nombre', '')
        self.descripcion = data.get('descripcion', '')
        self.tipo = data.get('tipo', '')
        self.categoria = data.get('categoria', '')
        self.archivo_url = data.get('archivo_url', '')
        self.thumbnail_url = data.get('thumbnail_url', '')
        self.formato = data.get('formato', '')
        self.tamaño_mb = data.get('tamaño_mb', 0.0)
        self.duracion_segundos = data.get('duracion_segundos')
        self.dimensiones = data.get('dimensiones', {})
        self.orden = data.get('orden', 0)
        self.es_principal = data.get('es_principal', False)
        self.etiquetas = data.get('etiquetas', [])
        self.nivel_dificultad = data.get('nivel_dificultad', '')
        self.es_premium = data.get('es_premium', False)
        self.estado = data.get('estado', '')
        self.fecha_subida = data.get('fecha_subida', '')
        self.estadisticas = data.get('estadisticas', {})


class MediaViewerDialog(QDialog):
    """Dialog para visualizar contenido multimedia"""
    
    def __init__(self, multimedia_item: MultimediaItem, parent=None):
        super().__init__(parent)
        self.multimedia_item = multimedia_item
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f"Visualizar: {self.multimedia_item.nombre}")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Header con información
        header_layout = QHBoxLayout()
        
        info_layout = QVBoxLayout()
        title_label = QLabel(self.multimedia_item.nombre)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        info_layout.addWidget(title_label)
        
        if self.multimedia_item.descripcion:
            desc_label = QLabel(self.multimedia_item.descripcion)
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
        
        # Metadatos
        meta_text = f"Tipo: {self.multimedia_item.tipo} | Formato: {self.multimedia_item.formato}"
        if self.multimedia_item.tamaño_mb:
            meta_text += f" | Tamaño: {self.multimedia_item.tamaño_mb:.1f} MB"
        if self.multimedia_item.duracion_segundos:
            meta_text += f" | Duración: {self.multimedia_item.duracion_segundos}s"
        
        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet("color: #666; font-size: 12px;")
        info_layout.addWidget(meta_label)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        # Botón cerrar
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc3333;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Área de contenido principal
        content_widget = self.create_content_widget()
        layout.addWidget(content_widget)
        
        # Footer con etiquetas
        if self.multimedia_item.etiquetas:
            tags_layout = QHBoxLayout()
            tags_layout.addWidget(QLabel("Etiquetas:"))
            
            for tag in self.multimedia_item.etiquetas:
                tag_label = QLabel(tag)
                tag_label.setStyleSheet("""
                    background-color: #e3f2fd;
                    color: #1976d2;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                """)
                tags_layout.addWidget(tag_label)
            
            tags_layout.addStretch()
            layout.addLayout(tags_layout)
        
    def create_content_widget(self):
        """Crear widget de contenido según el tipo de multimedia"""
        
        if self.multimedia_item.tipo in ['imagen', 'gif']:
            return self.create_image_widget()
        elif self.multimedia_item.tipo == 'video':
            return self.create_video_widget()
        elif self.multimedia_item.tipo == 'audio':
            return self.create_audio_widget()
        elif self.multimedia_item.tipo == 'documento':
            return self.create_document_widget()
        else:
            # Fallback
            label = QLabel("Vista previa no disponible para este tipo de archivo")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return label
    
    def create_image_widget(self):
        """Crear widget para mostrar imágenes"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("border: 1px solid #ddd;")
        
        # Cargar imagen
        if self.multimedia_item.archivo_url:
            pixmap = self.load_image_from_url(self.multimedia_item.archivo_url)
            if pixmap:
                # Escalar imagen manteniendo aspecto
                scaled_pixmap = pixmap.scaled(
                    700, 500, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                image_label.setPixmap(scaled_pixmap)
            else:
                image_label.setText("Error cargando imagen")
        
        scroll_area.setWidget(image_label)
        return scroll_area
    
    def create_video_widget(self):
        """Crear widget para reproducir videos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Media player
        self.media_player = QMediaPlayer()
        video_widget = QVideoWidget()
        self.media_player.setVideoOutput(video_widget)
        
        layout.addWidget(video_widget)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶")
        self.play_btn.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_btn)
        
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.position_slider)
        
        self.time_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.time_label)
        
        layout.addLayout(controls_layout)
        
        # Conectar señales
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.playback_state_changed)
        
        # Cargar video
        if self.multimedia_item.archivo_url:
            self.media_player.setSource(QUrl(self.multimedia_item.archivo_url))
        
        return widget
    
    def create_audio_widget(self):
        """Crear widget para reproducir audio"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Información del audio
        info_label = QLabel(f"🎵 {self.multimedia_item.nombre}")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("font-size: 16px; padding: 20px;")
        layout.addWidget(info_label)
        
        # Media player para audio
        self.media_player = QMediaPlayer()
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶")
        self.play_btn.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_btn)
        
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.position_slider)
        
        self.time_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.time_label)
        
        layout.addLayout(controls_layout)
        
        # Conectar señales
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.playback_state_changed)
        
        # Cargar audio
        if self.multimedia_item.archivo_url:
            self.media_player.setSource(QUrl(self.multimedia_item.archivo_url))
        
        return widget
    
    def create_document_widget(self):
        """Crear widget para documentos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Información del documento
        doc_label = QLabel(f"📄 {self.multimedia_item.nombre}")
        doc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        doc_label.setStyleSheet("font-size: 16px; padding: 20px;")
        layout.addWidget(doc_label)
        
        # Botón para abrir
        open_btn = QPushButton("Abrir Documento")
        open_btn.clicked.connect(self.open_document)
        layout.addWidget(open_btn)
        
        return widget
    
    def load_image_from_url(self, url: str) -> Optional[QPixmap]:
        """Cargar imagen desde URL"""
        try:
            # Para URLs locales, cargar directamente
            if url.startswith('file://') or os.path.exists(url):
                return QPixmap(url.replace('file://', ''))
            
            # Para URLs remotas, necesitaríamos implementar descarga
            # Por ahora, retornar None
            return None
            
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            return None
    
    def toggle_playback(self):
        """Alternar reproducción/pausa"""
        if hasattr(self, 'media_player'):
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
            else:
                self.media_player.play()
    
    def set_position(self, position):
        """Establecer posición del media player"""
        if hasattr(self, 'media_player'):
            self.media_player.setPosition(position)
    
    def position_changed(self, position):
        """Actualizar slider cuando cambie la posición"""
        if hasattr(self, 'position_slider'):
            self.position_slider.setValue(position)
            
        # Actualizar tiempo
        if hasattr(self, 'time_label') and hasattr(self, 'media_player'):
            duration = self.media_player.duration()
            current_time = self.format_time(position)
            total_time = self.format_time(duration)
            self.time_label.setText(f"{current_time} / {total_time}")
    
    def duration_changed(self, duration):
        """Actualizar slider cuando cambie la duración"""
        if hasattr(self, 'position_slider'):
            self.position_slider.setMaximum(duration)
    
    def playback_state_changed(self, state):
        """Actualizar botón cuando cambie el estado de reproducción"""
        if hasattr(self, 'play_btn'):
            if state == QMediaPlayer.PlaybackState.PlayingState:
                self.play_btn.setText("⏸")
            else:
                self.play_btn.setText("▶")
    
    def format_time(self, milliseconds):
        """Formatear tiempo en MM:SS"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def open_document(self):
        """Abrir documento con aplicación externa"""
        if self.multimedia_item.archivo_url:
            try:
                import webbrowser
                webbrowser.open(self.multimedia_item.archivo_url)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo abrir el documento: {e}")


class MultimediaUploadDialog(QDialog):
    """Dialog para subir nuevo contenido multimedia"""
    
    def __init__(self, ejercicio_id: str = None, rutina_id: str = None, parent=None):
        super().__init__(parent)
        self.ejercicio_id = ejercicio_id
        self.rutina_id = rutina_id
        self.selected_file = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Subir Contenido Multimedia")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Selección de archivo
        file_group = QGroupBox("Seleccionar Archivo")
        file_layout = QVBoxLayout(file_group)
        
        select_layout = QHBoxLayout()
        self.file_label = QLabel("No se ha seleccionado ningún archivo")
        self.file_label.setStyleSheet("padding: 10px; border: 2px dashed #ccc; border-radius: 5px;")
        select_layout.addWidget(self.file_label)
        
        select_btn = QPushButton("Seleccionar")
        select_btn.clicked.connect(self.select_file)
        select_layout.addWidget(select_btn)
        
        file_layout.addLayout(select_layout)
        layout.addWidget(file_group)
        
        # Metadatos
        meta_group = QGroupBox("Información del Archivo")
        meta_layout = QFormLayout(meta_group)
        
        self.nombre_edit = QLineEdit()
        meta_layout.addRow("Nombre:", self.nombre_edit)
        
        self.descripcion_edit = QTextEdit()
        self.descripcion_edit.setMaximumHeight(80)
        meta_layout.addRow("Descripción:", self.descripcion_edit)
        
        self.categoria_combo = QComboBox()
        self.categoria_combo.addItems([
            "demostracion", "tutorial", "tecnica", "variacion",
            "seguridad", "motivacional", "progreso"
        ])
        meta_layout.addRow("Categoría:", self.categoria_combo)
        
        self.etiquetas_edit = QLineEdit()
        self.etiquetas_edit.setPlaceholderText("Separar con comas: fuerza, principiante, brazos")
        meta_layout.addRow("Etiquetas:", self.etiquetas_edit)
        
        self.nivel_combo = QComboBox()
        self.nivel_combo.addItems(["principiante", "intermedio", "avanzado", "experto"])
        meta_layout.addRow("Nivel:", self.nivel_combo)
        
        self.orden_spin = QSpinBox()
        self.orden_spin.setMinimum(0)
        self.orden_spin.setMaximum(999)
        self.orden_spin.setValue(0)
        meta_layout.addRow("Orden:", self.orden_spin)
        
        self.principal_check = QCheckBox("Marcar como principal")
        meta_layout.addRow("", self.principal_check)
        
        self.premium_check = QCheckBox("Contenido premium")
        meta_layout.addRow("", self.premium_check)
        
        layout.addWidget(meta_group)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        self.upload_btn = QPushButton("Subir Archivo")
        self.upload_btn.clicked.connect(self.upload_file)
        self.upload_btn.setEnabled(False)
        buttons_layout.addWidget(self.upload_btn)
        
        layout.addLayout(buttons_layout)
    
    def select_file(self):
        """Seleccionar archivo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo multimedia",
            "",
            "Todos los archivos multimedia (*.jpg *.jpeg *.png *.gif *.mp4 *.avi *.mov *.mp3 *.wav *.pdf *.doc *.docx);;Imágenes (*.jpg *.jpeg *.png *.gif);;Videos (*.mp4 *.avi *.mov);;Audio (*.mp3 *.wav);;Documentos (*.pdf *.doc *.docx)"
        )
        
        if file_path:
            self.selected_file = file_path
            file_name = os.path.basename(file_path)
            self.file_label.setText(f"📁 {file_name}")
            self.file_label.setStyleSheet("padding: 10px; border: 2px solid #4CAF50; border-radius: 5px; color: #4CAF50;")
            
            # Auto-completar nombre si está vacío
            if not self.nombre_edit.text():
                name_without_ext = os.path.splitext(file_name)[0]
                self.nombre_edit.setText(name_without_ext)
            
            self.upload_btn.setEnabled(True)
    
    def upload_file(self):
        """Subir archivo"""
        if not self.selected_file:
            QMessageBox.warning(self, "Error", "Debe seleccionar un archivo")
            return
        
        if not self.nombre_edit.text().strip():
            QMessageBox.warning(self, "Error", "Debe ingresar un nombre")
            return
        
        # Preparar metadatos
        metadata = {
            'nombre': self.nombre_edit.text().strip(),
            'descripcion': self.descripcion_edit.toPlainText().strip(),
            'categoria': self.categoria_combo.currentText(),
            'etiquetas': [tag.strip() for tag in self.etiquetas_edit.text().split(',') if tag.strip()],
            'nivel_dificultad': self.nivel_combo.currentText(),
            'orden': self.orden_spin.value(),
            'es_principal': self.principal_check.isChecked(),
            'es_premium': self.premium_check.isChecked()
        }
        
        # Desactivar botón durante la subida
        self.upload_btn.setEnabled(False)
        self.upload_btn.setText("Subiendo...")
        
        try:
            # Aquí iría la lógica de subida usando ApiClient
            # Por ahora simulamos éxito
            QMessageBox.information(self, "Éxito", "Archivo subido correctamente")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al subir archivo: {e}")
            self.upload_btn.setEnabled(True)
            self.upload_btn.setText("Subir Archivo")


class MultimediaWidget(QWidget):
    """Widget principal para gestión de multimedia"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_client = ApiClient()
        self.current_ejercicio_id = None
        self.current_rutina_id = None
        self.multimedia_items = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🎬 Contenido Multimedia")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Filtros
        self.tipo_filter = QComboBox()
        self.tipo_filter.addItems(["Todos", "imagen", "video", "audio", "documento"])
        self.tipo_filter.currentTextChanged.connect(self.filter_multimedia)
        header_layout.addWidget(QLabel("Tipo:"))
        header_layout.addWidget(self.tipo_filter)
        
        # Botón subir
        upload_btn = QPushButton("📤 Subir Archivo")
        upload_btn.clicked.connect(self.upload_multimedia)
        header_layout.addWidget(upload_btn)
        
        layout.addLayout(header_layout)
        
        # Lista de multimedia
        self.multimedia_list = QListWidget()
        self.multimedia_list.setIconSize(QSize(120, 90))
        self.multimedia_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.multimedia_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.multimedia_list.setUniformItemSizes(True)
        self.multimedia_list.setGridSize(QSize(140, 140))
        self.multimedia_list.itemDoubleClicked.connect(self.view_multimedia)
        
        # Menú contextual
        self.multimedia_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.multimedia_list.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.multimedia_list)
        
        # Status
        self.status_label = QLabel("No hay contenido multimedia")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; padding: 20px;")
        layout.addWidget(self.status_label)
    
    def set_ejercicio(self, ejercicio_id: str):
        """Establecer ejercicio actual"""
        self.current_ejercicio_id = ejercicio_id
        self.current_rutina_id = None
        self.load_multimedia()
    
    def set_rutina(self, rutina_id: str):
        """Establecer rutina actual"""
        self.current_rutina_id = rutina_id
        self.current_ejercicio_id = None
        self.load_multimedia()
    
    def load_multimedia(self):
        """Cargar multimedia del ejercicio o rutina actual"""
        self.multimedia_list.clear()
        self.multimedia_items = []
        
        if not self.current_ejercicio_id and not self.current_rutina_id:
            self.status_label.setText("Seleccione un ejercicio o rutina")
            self.status_label.show()
            return
        
        # Aquí iría la llamada a la API
        # Por ahora, mostramos datos de ejemplo
        self.multimedia_items = []
        self.populate_multimedia_list()
    
    def populate_multimedia_list(self):
        """Poblar lista con elementos multimedia"""
        self.multimedia_list.clear()
        
        if not self.multimedia_items:
            self.status_label.setText("No hay contenido multimedia disponible")
            self.status_label.show()
            return
        
        self.status_label.hide()
        
        for item_data in self.multimedia_items:
            multimedia_item = MultimediaItem(item_data)
            list_item = QListWidgetItem()
            
            # Icono según tipo
            if multimedia_item.tipo == 'imagen':
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
            elif multimedia_item.tipo == 'video':
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            elif multimedia_item.tipo == 'audio':
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume)
            else:
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
            
            list_item.setIcon(icon)
            list_item.setText(multimedia_item.nombre)
            list_item.setData(Qt.ItemDataRole.UserRole, multimedia_item)
            
            # Tooltip con información
            tooltip = f"Nombre: {multimedia_item.nombre}\n"
            tooltip += f"Tipo: {multimedia_item.tipo}\n"
            tooltip += f"Formato: {multimedia_item.formato}\n"
            if multimedia_item.tamaño_mb:
                tooltip += f"Tamaño: {multimedia_item.tamaño_mb:.1f} MB\n"
            if multimedia_item.descripcion:
                tooltip += f"Descripción: {multimedia_item.descripcion}"
            
            list_item.setToolTip(tooltip)
            
            self.multimedia_list.addItem(list_item)
    
    def filter_multimedia(self, tipo_filter: str):
        """Filtrar multimedia por tipo"""
        for i in range(self.multimedia_list.count()):
            item = self.multimedia_list.item(i)
            multimedia_item = item.data(Qt.ItemDataRole.UserRole)
            
            if tipo_filter == "Todos" or multimedia_item.tipo == tipo_filter:
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def view_multimedia(self, item: QListWidgetItem):
        """Ver elemento multimedia"""
        multimedia_item = item.data(Qt.ItemDataRole.UserRole)
        dialog = MediaViewerDialog(multimedia_item, self)
        dialog.exec()
    
    def upload_multimedia(self):
        """Subir nuevo contenido multimedia"""
        dialog = MultimediaUploadDialog(
            self.current_ejercicio_id,
            self.current_rutina_id,
            self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_multimedia()  # Recargar lista
    
    def show_context_menu(self, position):
        """Mostrar menú contextual"""
        item = self.multimedia_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        view_action = menu.addAction("👁 Ver")
        view_action.triggered.connect(lambda: self.view_multimedia(item))
        
        menu.addSeparator()
        
        edit_action = menu.addAction("✏ Editar")
        edit_action.triggered.connect(lambda: self.edit_multimedia(item))
        
        principal_action = menu.addAction("⭐ Marcar como principal")
        principal_action.triggered.connect(lambda: self.set_as_principal(item))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑 Eliminar")
        delete_action.triggered.connect(lambda: self.delete_multimedia(item))
        
        menu.exec(self.multimedia_list.mapToGlobal(position))
    
    def edit_multimedia(self, item: QListWidgetItem):
        """Editar elemento multimedia"""
        multimedia_item = item.data(Qt.ItemDataRole.UserRole)
        # Aquí iría el diálogo de edición
        QMessageBox.information(self, "Info", f"Editando: {multimedia_item.nombre}")
    
    def set_as_principal(self, item: QListWidgetItem):
        """Marcar como elemento principal"""
        multimedia_item = item.data(Qt.ItemDataRole.UserRole)
        # Aquí iría la lógica para marcar como principal
        QMessageBox.information(self, "Info", f"Marcado como principal: {multimedia_item.nombre}")
    
    def delete_multimedia(self, item: QListWidgetItem):
        """Eliminar elemento multimedia"""
        multimedia_item = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar '{multimedia_item.nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Aquí iría la lógica de eliminación
            QMessageBox.information(self, "Info", f"Eliminado: {multimedia_item.nombre}")
            self.load_multimedia()  # Recargar lista


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Crear widget de prueba
    widget = MultimediaWidget()
    widget.show()
    
    sys.exit(app.exec()) 