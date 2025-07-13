"""
Widget de Lista Virtualizada Optimizada
Sistema de Gestión de Gimnasio v6 - Fase 4

Implementa una lista virtualizada para manejar grandes cantidades de datos
con rendimiento eficiente, integrando con el sistema de optimización.
"""

import logging
from typing import List, Dict, Any, Callable, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QPushButton, QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QColor

from utils.performance_monitor import get_performance_monitor, monitor_ui_function

logger = logging.getLogger(__name__)

class VirtualizedListItem(QFrame):
    """Item individual de la lista virtualizada"""
    
    item_clicked = pyqtSignal(int)  # Emite el índice del item
    item_double_clicked = pyqtSignal(int)
    
    def __init__(self, index: int, data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.index = index
        self.data = data
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interfaz del item"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        self.setMidLineWidth(0)
        
        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        
        # Contenido del item
        self._create_content(layout)
        
        # Estilo
        self.setStyleSheet("""
            VirtualizedListItem {
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 4px;
                margin: 1px;
            }
            VirtualizedListItem:hover {
                background: var(--bg-hover);
                border-color: var(--primary-color);
            }
            VirtualizedListItem:selected {
                background: var(--primary-color);
                color: white;
            }
        """)
        
    def _create_content(self, layout: QHBoxLayout):
        """Crear contenido del item basado en los datos"""
        # Implementación básica - puede ser sobrescrita
        for key, value in self.data.items():
            if key != 'id':  # Evitar mostrar ID
                label = QLabel(f"{key}: {value}")
                label.setWordWrap(True)
                layout.addWidget(label)
        
        layout.addStretch()
        
    def mousePressEvent(self, event):
        """Manejar clic del mouse"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.item_clicked.emit(self.index)
        super().mousePressEvent(event)
        
    def mouseDoubleClickEvent(self, event):
        """Manejar doble clic"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.item_double_clicked.emit(self.index)
        super().mouseDoubleClickEvent(event)

class VirtualizedListWidget(QWidget):
    """
    Widget de lista virtualizada optimizada
    
    Características:
    - Renderizado solo de items visibles
    - Carga diferida de datos
    - Compresión de datos en memoria
    - Optimización de scroll
    - Cache inteligente
    """
    
    item_selected = pyqtSignal(int, Dict[str, Any])
    item_double_clicked = pyqtSignal(int, Dict[str, Any])
    selection_changed = pyqtSignal(list)  # Lista de índices seleccionados
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Datos y estado
        self.all_data: List[Dict[str, Any]] = []
        self.visible_data: List[Dict[str, Any]] = []
        self.item_height = 60
        self.visible_count = 0
        self.scroll_offset = 0
        self.selected_indices: List[int] = []
        
        # Performance monitor
        self.performance_monitor = get_performance_monitor()
        
        # Cache de items
        self.item_cache = {}
        self.max_cache_size = 100
        
        # Configuración de virtualización
        self.preload_distance = 5  # Items a precargar
        self.chunk_size = 20  # Tamaño de chunk para carga
        
        # UI
        self.setup_ui()
        
        # Timers para optimización
        self.scroll_timer = QTimer(self)
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self._update_visible_items)
        
        self.cache_timer = QTimer(self)
        self.cache_timer.timeout.connect(self._cleanup_cache)
        self.cache_timer.start(30000)  # Cada 30 segundos
        
    def setup_ui(self):
        """Configurar interfaz del widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget contenedor
        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(2)
        
        # Conectar scroll
        scroll_bar = self.scroll_area.verticalScrollBar()
        if scroll_bar:
            scroll_bar.valueChanged.connect(self._on_scroll)
        
        # Configurar scroll area
        self.scroll_area.setWidget(self.container_widget)
        layout.addWidget(self.scroll_area)
        
        # Indicador de estado
        self.status_label = QLabel("Lista vacía")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: var(--text-muted); padding: 20px;")
        layout.addWidget(self.status_label)
        
    @monitor_ui_function("virtualized_list_set_data")
    def set_data(self, data: List[Dict[str, Any]]):
        """Establecer datos para la lista"""
        try:
            # Comprimir datos en cache
            self.performance_monitor.cache_compressed("virtualized_list_data", data)
            
            self.all_data = data
            self.visible_data = data[:self.chunk_size]  # Cargar primer chunk
            
            # Calcular altura total
            total_height = len(data) * self.item_height
            self.container_widget.setFixedHeight(total_height)
            
            # Limpiar cache
            self._clear_cache()
            
            # Actualizar items visibles
            self._update_visible_items()
            
            # Actualizar estado
            self._update_status()
            
            logger.info(f"Lista virtualizada configurada con {len(data)} items")
            
        except Exception as e:
            logger.error(f"Error configurando datos de lista virtualizada: {e}")
            
    def _update_visible_items(self):
        """Actualizar items visibles basado en scroll"""
        try:
            # Obtener rango visible
            scroll_bar = self.scroll_area.verticalScrollBar()
            viewport = self.scroll_area.viewport()
            
            if not scroll_bar or not viewport:
                return
                
            scroll_value = scroll_bar.value()
            viewport_height = viewport.height()
            
            start_index = max(0, scroll_value // self.item_height - self.preload_distance)
            end_index = min(
                len(self.all_data),
                (scroll_value + viewport_height) // self.item_height + self.preload_distance
            )
            
            # Limpiar items no visibles
            self._cleanup_invisible_items(start_index, end_index)
            
            # Crear items visibles
            self._create_visible_items(start_index, end_index)
            
            # Actualizar scroll offset
            self.scroll_offset = start_index
            
        except Exception as e:
            logger.error(f"Error actualizando items visibles: {e}")
            
    def _cleanup_invisible_items(self, start_index: int, end_index: int):
        """Limpiar items que ya no son visibles"""
        try:
            # Identificar items a remover
            to_remove = []
            for index, item_widget in self.item_cache.items():
                if index < start_index or index >= end_index:
                    to_remove.append(index)
                    
            # Remover items
            for index in to_remove:
                item_widget = self.item_cache.pop(index)
                if item_widget:
                    item_widget.deleteLater()
                    
        except Exception as e:
            logger.error(f"Error limpiando items invisibles: {e}")
            
    def _create_visible_items(self, start_index: int, end_index: int):
        """Crear items visibles en el rango especificado"""
        try:
            viewport = self.scroll_area.viewport()
            if not viewport:
                return
                
            for index in range(start_index, end_index):
                if index not in self.item_cache and index < len(self.all_data):
                    # Crear item
                    item_data = self.all_data[index]
                    item_widget = VirtualizedListItem(index, item_data, self.container_widget)
                    
                    # Conectar señales
                    item_widget.item_clicked.connect(self._on_item_clicked)
                    item_widget.item_double_clicked.connect(self._on_item_double_clicked)
                    
                    # Posicionar item
                    item_widget.move(0, index * self.item_height)
                    item_widget.setFixedSize(viewport.width(), self.item_height)
                    item_widget.show()
                    
                    # Agregar al cache
                    self.item_cache[index] = item_widget
                    
                    # Marcar como seleccionado si corresponde
                    if index in self.selected_indices:
                        item_widget.setProperty("selected", True)
                        style = item_widget.style()
                        if style:
                            style.unpolish(item_widget)
                            style.polish(item_widget)
                        
        except Exception as e:
            logger.error(f"Error creando items visibles: {e}")
            
    def _on_scroll(self, value: int):
        """Manejar evento de scroll"""
        # Usar timer para evitar actualizaciones muy frecuentes
        self.scroll_timer.start(50)  # 50ms delay
        
    def _on_item_clicked(self, index: int):
        """Manejar clic en item"""
        try:
            # Actualizar selección
            if index in self.selected_indices:
                self.selected_indices.remove(index)
            else:
                self.selected_indices.append(index)
                
            # Actualizar apariencia
            self._update_item_selection(index)
            
            # Emitir señales
            if index < len(self.all_data):
                self.item_selected.emit(index, self.all_data[index])
                self.selection_changed.emit(self.selected_indices.copy())
                
        except Exception as e:
            logger.error(f"Error manejando clic en item: {e}")
            
    def _on_item_double_clicked(self, index: int):
        """Manejar doble clic en item"""
        try:
            if index < len(self.all_data):
                self.item_double_clicked.emit(index, self.all_data[index])
                
        except Exception as e:
            logger.error(f"Error manejando doble clic en item: {e}")
            
    def _update_item_selection(self, index: int):
        """Actualizar apariencia de selección del item"""
        try:
            if index in self.item_cache:
                item_widget = self.item_cache[index]
                is_selected = index in self.selected_indices
                
                item_widget.setProperty("selected", is_selected)
                style = item_widget.style()
                if style:
                    style.unpolish(item_widget)
                    style.polish(item_widget)
                
        except Exception as e:
            logger.error(f"Error actualizando selección de item: {e}")
            
    def _clear_cache(self):
        """Limpiar cache de items"""
        try:
            for item_widget in self.item_cache.values():
                if item_widget:
                    item_widget.deleteLater()
            self.item_cache.clear()
            
        except Exception as e:
            logger.error(f"Error limpiando cache: {e}")
            
    def _cleanup_cache(self):
        """Limpieza periódica del cache"""
        try:
            # Remover items más antiguos si el cache es muy grande
            if len(self.item_cache) > self.max_cache_size:
                # Mantener solo los items más recientes
                sorted_items = sorted(self.item_cache.items())
                items_to_remove = sorted_items[:-self.max_cache_size]
                
                for index, item_widget in items_to_remove:
                    if item_widget:
                        item_widget.deleteLater()
                    del self.item_cache[index]
                    
            logger.debug(f"Cache limpiado: {len(self.item_cache)} items")
            
        except Exception as e:
            logger.error(f"Error en limpieza de cache: {e}")
            
    def _update_status(self):
        """Actualizar indicador de estado"""
        try:
            if not self.all_data:
                self.status_label.setText("Lista vacía")
                self.status_label.show()
            else:
                self.status_label.hide()
                
        except Exception as e:
            logger.error(f"Error actualizando estado: {e}")
            
    def get_selected_items(self) -> List[Dict[str, Any]]:
        """Obtener items seleccionados"""
        try:
            return [self.all_data[i] for i in self.selected_indices if i < len(self.all_data)]
        except Exception as e:
            logger.error(f"Error obteniendo items seleccionados: {e}")
            return []
            
    def select_item(self, index: int, selected: bool = True):
        """Seleccionar/deseleccionar item específico"""
        try:
            if selected and index not in self.selected_indices:
                self.selected_indices.append(index)
            elif not selected and index in self.selected_indices:
                self.selected_indices.remove(index)
                
            self._update_item_selection(index)
            
        except Exception as e:
            logger.error(f"Error seleccionando item: {e}")
            
    def select_all(self):
        """Seleccionar todos los items"""
        try:
            self.selected_indices = list(range(len(self.all_data)))
            for index in self.selected_indices:
                self._update_item_selection(index)
                
        except Exception as e:
            logger.error(f"Error seleccionando todos los items: {e}")
            
    def clear_selection(self):
        """Limpiar selección"""
        try:
            for index in self.selected_indices:
                self._update_item_selection(index)
            self.selected_indices.clear()
            
        except Exception as e:
            logger.error(f"Error limpiando selección: {e}")
            
    def filter_data(self, filter_func: Callable[[Dict[str, Any]], bool]):
        """Filtrar datos usando función personalizada"""
        try:
            filtered_data = [item for item in self.all_data if filter_func(item)]
            self.set_data(filtered_data)
            
        except Exception as e:
            logger.error(f"Error filtrando datos: {e}")
            
    def sort_data(self, key_func: Callable[[Dict[str, Any]], Any], reverse: bool = False):
        """Ordenar datos usando función personalizada"""
        try:
            sorted_data = sorted(self.all_data, key=key_func, reverse=reverse)
            self.set_data(sorted_data)
            
        except Exception as e:
            logger.error(f"Error ordenando datos: {e}")
            
    def get_item_at_position(self, y: int) -> Optional[int]:
        """Obtener índice del item en posición Y"""
        try:
            scroll_bar = self.scroll_area.verticalScrollBar()
            if not scroll_bar:
                return None
                
            scroll_value = scroll_bar.value()
            adjusted_y = y + scroll_value
            index = adjusted_y // self.item_height
            
            if 0 <= index < len(self.all_data):
                return index
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo item en posición: {e}")
            return None
            
    def scroll_to_item(self, index: int):
        """Hacer scroll hasta un item específico"""
        try:
            if 0 <= index < len(self.all_data):
                scroll_bar = self.scroll_area.verticalScrollBar()
                if scroll_bar:
                    y_position = index * self.item_height
                    scroll_bar.setValue(y_position)
                
        except Exception as e:
            logger.error(f"Error haciendo scroll a item: {e}")
            
    def refresh(self):
        """Refrescar la lista"""
        try:
            # Limpiar cache
            self._clear_cache()
            
            # Recrear items visibles
            self._update_visible_items()
            
            # Actualizar estado
            self._update_status()
            
        except Exception as e:
            logger.error(f"Error refrescando lista: {e}")
            
    def resizeEvent(self, event):
        """Manejar redimensionamiento"""
        super().resizeEvent(event)
        
        # Ajustar tamaño de items visibles
        viewport = self.scroll_area.viewport()
        if viewport:
            for item_widget in self.item_cache.values():
                if item_widget:
                    item_widget.setFixedWidth(viewport.width())
                
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de rendimiento"""
        try:
            return {
                "total_items": len(self.all_data),
                "visible_items": len(self.item_cache),
                "cache_size": len(self.item_cache),
                "selected_items": len(self.selected_indices),
                "memory_usage_mb": len(self.item_cache) * self.item_height * 0.001  # Estimación
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {} 