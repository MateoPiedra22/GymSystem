"""
Sistema de notificaciones toast para el Sistema de Gimnasio v6
Incluye notificaciones temporales, persistentes y accesibles
"""
import logging
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QIcon, QFont, QPixmap

logger = logging.getLogger(__name__)

class ToastNotification(QFrame):
    """Notificación toast individual"""
    
    dismissed = pyqtSignal()  # Emitida cuando se descarta la notificación
    
    def __init__(self, title: str, message: str = "", notification_type: str = "info", 
                 duration: int = 5000, parent=None):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.notification_type = notification_type
        self.duration = duration
        self.setup_ui()
        self.setup_animations()
        
        # Timer para auto-descarte
        if duration > 0:
            self.auto_dismiss_timer = QTimer()
            self.auto_dismiss_timer.timeout.connect(self.dismiss)
            self.auto_dismiss_timer.start(duration)
    
    def setup_ui(self):
        """Configura la interfaz del toast"""
        self.setObjectName("toast")
        self.setFixedWidth(400)
        self.setMaximumHeight(120)
        
        # Configurar estilo base
        self.setStyleSheet(f"""
            QFrame#toast {{
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 16px;
                box-shadow: var(--shadow-lg);
            }}
            QFrame#toast.{self.notification_type} {{
                border-left: 4px solid var(--{self.notification_type}-color);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Header con título y botón de cerrar
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # Icono según tipo
        icon_label = QLabel()
        icon_map = {
            "success": ":/icons/check-circle.svg",
            "warning": ":/icons/alert-triangle.svg",
            "error": ":/icons/x-circle.svg",
            "info": ":/icons/info.svg"
        }
        icon_path = icon_map.get(self.notification_type, ":/icons/info.svg")
        icon_label.setPixmap(QPixmap(icon_path).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio))
        header_layout.addWidget(icon_label)
        
        # Título
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            QLabel {
                color: var(--text-primary);
                font-weight: 600;
                font-size: 14px;
            }
        """)
        header_layout.addWidget(self.title_label)
        
        # Espaciador
        header_layout.addStretch()
        
        # Botón de cerrar
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: var(--text-muted);
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: var(--state-hover);
                color: var(--text-primary);
            }
        """)
        self.close_button.clicked.connect(self.dismiss)
        header_layout.addWidget(self.close_button)
        
        layout.addLayout(header_layout)
        
        # Mensaje (si existe)
        if self.message:
            self.message_label = QLabel(self.message)
            self.message_label.setWordWrap(True)
            self.message_label.setStyleSheet("""
                QLabel {
                    color: var(--text-secondary);
                    font-size: 13px;
                    line-height: 1.4;
                }
            """)
            layout.addWidget(self.message_label)
        
        # Configurar accesibilidad
        self.setAccessibleName(f"Notificación {self.notification_type}: {self.title}")
        if self.message:
            self.setAccessibleDescription(self.message)
    
    def setup_animations(self):
        """Configura las animaciones del toast"""
        # Efecto de opacidad
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        # Animación de entrada
        self.enter_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.enter_animation.setDuration(300)
        self.enter_animation.setStartValue(0.0)
        self.enter_animation.setEndValue(1.0)
        self.enter_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Animación de salida
        self.exit_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.exit_animation.setDuration(300)
        self.exit_animation.setStartValue(1.0)
        self.exit_animation.setEndValue(0.0)
        self.exit_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.exit_animation.finished.connect(self.on_exit_finished)
    
    def show_animation(self):
        """Ejecuta la animación de entrada"""
        self.enter_animation.start()
    
    def dismiss(self):
        """Descarta la notificación"""
        if hasattr(self, 'auto_dismiss_timer'):
            self.auto_dismiss_timer.stop()
        
        self.exit_animation.start()
    
    def on_exit_finished(self):
        """Maneja el final de la animación de salida"""
        self.dismissed.emit()
        self.deleteLater()

class ToastContainer(QWidget):
    """Contenedor para múltiples notificaciones toast"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.toasts: list[ToastNotification] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz del contenedor"""
        self.setFixedWidth(450)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        # El layout se llenará dinámicamente con toasts
    
    def add_toast(self, title: str, message: str = "", notification_type: str = "info", 
                  duration: int = 5000) -> ToastNotification:
        """Agrega una nueva notificación toast"""
        toast = ToastNotification(title, message, notification_type, duration, self)
        toast.dismissed.connect(lambda: self.remove_toast(toast))
        
        # Agregar al layout
        self.layout().addWidget(toast)
        self.toasts.append(toast)
        
        # Ejecutar animación de entrada
        toast.show_animation()
        
        # Anunciar para lectores de pantalla
        QApplication.instance().notify(self, f"Notificación {notification_type}: {title}")
        
        return toast
    
    def remove_toast(self, toast: ToastNotification):
        """Remueve una notificación toast"""
        if toast in self.toasts:
            self.toasts.remove(toast)
            self.layout().removeWidget(toast)
    
    def clear_all(self):
        """Limpia todas las notificaciones"""
        for toast in self.toasts[:]:  # Copia de la lista para evitar problemas de iteración
            toast.dismiss()

class ToastManager:
    """Gestor global de notificaciones toast"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.container: Optional[ToastContainer] = None
            self.initialized = True
    
    def set_container(self, container: ToastContainer):
        """Establece el contenedor de notificaciones"""
        self.container = container
    
    def show_toast(self, title: str, message: str = "", notification_type: str = "info", 
                   duration: int = 5000) -> Optional[ToastNotification]:
        """Muestra una notificación toast"""
        if not self.container:
            logger.warning("Toast container no configurado")
            return None
        
        return self.container.add_toast(title, message, notification_type, duration)
    
    def success(self, title: str, message: str = "", duration: int = 5000):
        """Muestra una notificación de éxito"""
        return self.show_toast(title, message, "success", duration)
    
    def warning(self, title: str, message: str = "", duration: int = 5000):
        """Muestra una notificación de advertencia"""
        return self.show_toast(title, message, "warning", duration)
    
    def error(self, title: str, message: str = "", duration: int = 8000):
        """Muestra una notificación de error"""
        return self.show_toast(title, message, "error", duration)
    
    def info(self, title: str, message: str = "", duration: int = 5000):
        """Muestra una notificación informativa"""
        return self.show_toast(title, message, "info", duration)
    
    def clear_all(self):
        """Limpia todas las notificaciones"""
        if self.container:
            self.container.clear_all()

# Instancia global del gestor
toast_manager = ToastManager()

class LoadingIndicator(QWidget):
    """Indicador de carga animado"""
    
    def __init__(self, text: str = "Cargando...", parent=None):
        super().__init__(parent)
        self.text = text
        self.setup_ui()
        self.setup_animation()
    
    def setup_ui(self):
        """Configura la interfaz del indicador"""
        self.setFixedSize(200, 100)
        self.setStyleSheet("""
            QWidget {
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Spinner (simulado con texto)
        self.spinner_label = QLabel("⏳")
        self.spinner_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                text-align: center;
            }
        """)
        self.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.spinner_label)
        
        # Texto
        self.text_label = QLabel(self.text)
        self.text_label.setStyleSheet("""
            QLabel {
                color: var(--text-secondary);
                font-size: 14px;
                text-align: center;
            }
        """)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text_label)
    
    def setup_animation(self):
        """Configura la animación del spinner"""
        # TODO: Implementar animación real del spinner
        pass
    
    def set_text(self, text: str):
        """Cambia el texto del indicador"""
        self.text = text
        self.text_label.setText(text)

class ProgressIndicator(QWidget):
    """Indicador de progreso con texto"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz del indicador"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Título
        if self.title:
            self.title_label = QLabel(self.title)
            self.title_label.setStyleSheet("""
                QLabel {
                    color: var(--text-primary);
                    font-weight: 600;
                    font-size: 14px;
                }
            """)
            layout.addWidget(self.title_label)
        
        # Barra de progreso
        self.progress_bar = QWidget()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QWidget {
                background: var(--bg-tertiary);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Contenedor para el progreso
        self.progress_container = QWidget()
        self.progress_container.setFixedHeight(4)
        self.progress_container.setStyleSheet("""
            QWidget {
                background: var(--primary-color);
                border-radius: 2px;
            }
        """)
        self.progress_container.setMaximumWidth(0)
        
        # Layout para el contenedor de progreso
        progress_layout = QHBoxLayout(self.progress_bar)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.addWidget(self.progress_container)
        progress_layout.addStretch()
        
        # Texto de progreso
        self.progress_text = QLabel("0%")
        self.progress_text.setStyleSheet("""
            QLabel {
                color: var(--text-secondary);
                font-size: 12px;
            }
        """)
        layout.addWidget(self.progress_text)
    
    def set_progress(self, value: int, text: str = None):
        """Establece el progreso (0-100)"""
        value = max(0, min(100, value))
        
        # Actualizar barra de progreso
        progress_width = int((value / 100) * self.progress_bar.width())
        self.progress_container.setMaximumWidth(progress_width)
        
        # Actualizar texto
        if text:
            self.progress_text.setText(text)
        else:
            self.progress_text.setText(f"{value}%")
    
    def set_title(self, title: str):
        """Cambia el título del indicador"""
        self.title = title
        if hasattr(self, 'title_label'):
            self.title_label.setText(title)

class StatusIndicator(QWidget):
    """Indicador de estado con icono y texto"""
    
    def __init__(self, text: str = "", status_type: str = "info", parent=None):
        super().__init__(parent)
        self.text = text
        self.status_type = status_type
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz del indicador"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Icono
        self.icon_label = QLabel()
        icon_map = {
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
            "info": "ℹ"
        }
        icon = icon_map.get(self.status_type, "ℹ")
        self.icon_label.setText(icon)
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                color: var(--{self.status_type}-color);
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(self.icon_label)
        
        # Texto
        self.text_label = QLabel(self.text)
        self.text_label.setStyleSheet("""
            QLabel {
                color: var(--text-primary);
                font-size: 13px;
            }
        """)
        layout.addWidget(self.text_label)
        
        # Estilo del contenedor
        self.setStyleSheet(f"""
            QWidget {{
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 6px;
            }}
        """)
    
    def set_text(self, text: str):
        """Cambia el texto del indicador"""
        self.text = text
        self.text_label.setText(text)
    
    def set_status(self, status_type: str):
        """Cambia el tipo de estado"""
        self.status_type = status_type
        icon_map = {
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
            "info": "ℹ"
        }
        icon = icon_map.get(status_type, "ℹ")
        self.icon_label.setText(icon)
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                color: var(--{status_type}-color);
                font-size: 16px;
                font-weight: bold;
            }}
        """) 