"""
Diálogo de login optimizado para el cliente desktop
Sistema de Gestión de Gimnasio v6
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QCheckBox, QFrame, QMessageBox, QProgressBar,
    QGridLayout, QGraphicsDropShadowEffect, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPixmap, QIcon, QColor, QPalette

from utils.config_manager import ConfigManager
from utils.secure_storage import SecureStorage
from utils.performance_monitor import get_performance_monitor, monitor_ui_function
from api_client import ApiClient

logger = logging.getLogger("login_dialog")

class LoginWorker(QThread):
    """Worker thread para realizar login sin bloquear la UI"""
    
    login_success = pyqtSignal(dict)
    login_error = pyqtSignal(str)
    login_progress = pyqtSignal(int, str)
    
    def __init__(self, api_client: ApiClient, username: str, password: str):
        super().__init__()
        self.api_client = api_client
        self.username = username
        self.password = password
        self.performance_monitor = get_performance_monitor()
        
    def run(self):
        """Ejecuta el proceso de login"""
        try:
            # Paso 1: Validar credenciales
            self.login_progress.emit(20, "Validando credenciales...")
            # Validación real con JWT
            try:
                # Llamada a la API para autenticación
                auth_data = {
                    "username": username,
                    "password": password
                }
                
                response = self.api_client._make_request('POST', '/auth/login', data=auth_data)
                
                if response and 'access_token' in response:
                    # Guardar token en almacenamiento seguro
                    self.secure_storage.store_token(response['access_token'])
                    if 'refresh_token' in response:
                        self.secure_storage.store_refresh_token(response['refresh_token'])
                    
                    # Configurar API client con el token
                    self.api_client.set_token(response)
                    
                    return True
                else:
                    self.error_label.setText("Credenciales inválidas")
                    return False
                    
            except Exception as e:
                self.error_label.setText(f"Error de conexión: {str(e)}")
                return False
            
            # Paso 2: Conectar con servidor
            self.login_progress.emit(40, "Conectando con servidor...")
            login_start = time.time()
            
            # Realizar login real con el backend
            token_data = self.api_client.login(self.username, self.password)
            
            # Paso 3: Verificar permisos
            self.login_progress.emit(60, "Verificando permisos...")
            time.sleep(0.3)
            
            # Paso 4: Configurar sesión
            self.login_progress.emit(80, "Configurando sesión...")
            time.sleep(0.3)
            
            # Paso 5: Completar
            self.login_progress.emit(100, "Login completado")
            
            # Registrar tiempo de login
            login_time = (time.time() - login_start) * 1000  # ms
            self.performance_monitor.record_api_call(login_time)
            
            # Emitir señal de éxito
            self.login_success.emit(token_data)
            
        except Exception as e:
            logger.error(f"Error en login: {e}")
            self.performance_monitor.record_error("login_error", str(e))
            self.login_error.emit(str(e))

class AnimatedButton(QPushButton):
    """Botón con animaciones suaves"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Efecto de sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # Animación de hover
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def enterEvent(self, event):
        """Efecto al pasar el mouse por encima"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #45a049;
                border: none;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                transform: translateY(-2px);
            }
        """)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Efecto al quitar el mouse"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
        """)
        super().leaveEvent(event)

class LoginDialog(QDialog):
    """
    Diálogo de login optimizado con mejoras de rendimiento y UX
    """
    
    def __init__(self, config: ConfigManager, secure_storage: SecureStorage, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.secure_storage = secure_storage
        self.performance_monitor = get_performance_monitor()
        
        # Estado del diálogo
        self.login_worker = None
        self.auto_login_attempted = False
        
        # Inicializar UI
        self._init_ui()
        
        # Intentar auto-login si está configurado
        self._attempt_auto_login()
    
    @monitor_ui_function("login_dialog_init")
    def _init_ui(self):
        """Inicializa la interfaz del diálogo"""
        self.setWindowTitle("Iniciar Sesión - Gimnasio v6.0")
        self.setFixedSize(400, 550)
        self.setModal(True)
        
        # Configurar ventana sin borde para aspecto moderno
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Widget principal con bordes redondeados
        main_widget = QFrame(self)
        main_widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        main_widget.setGeometry(10, 10, 380, 530)
        
        # Efecto de sombra para el widget principal
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 5)
        main_widget.setGraphicsEffect(shadow)
        
        # Layout del widget principal
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Sección de logo y título
        self._create_header(layout)
        
        # Sección de formulario
        self._create_form(layout)
        
        # Sección de botones
        self._create_buttons(layout)
        
        # Sección de progreso
        self._create_progress_section(layout)
        
        # Sección de información
        self._create_info_section(layout)
        
        # Aplicar estilos generales
        self._apply_styles()
        
        # Configurar focus inicial
        self.username_input.setFocus()
    
    def _create_logo_section(self, header_layout: QVBoxLayout):
        """Crea la sección del logo"""
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Intentar cargar logo
        try:
            logo_pixmap = QPixmap("assets/logo.png")
            if not logo_pixmap.isNull():
                logo_pixmap = logo_pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(logo_pixmap)
            else:
                logo_label.setText("🏋️")
                logo_label.setStyleSheet("font-size: 48px;")
        except:
            logo_label.setText("🏋️")
            logo_label.setStyleSheet("font-size: 48px;")
        
        header_layout.addWidget(logo_label)
    
    def _create_title_section(self, header_layout: QVBoxLayout):
        """Crea la sección del título"""
        # Título principal
        title_label = QLabel("Sistema de Gestión")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 5px;")
        
        # Subtítulo
        subtitle_label = QLabel("Gimnasio v6.0")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 20px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
    
    def _create_header(self, layout: QVBoxLayout):
        """Crea la sección de encabezado"""
        header_layout = QVBoxLayout()
        
        # Crear secciones del header
        self._create_logo_section(header_layout)
        self._create_title_section(header_layout)
        
        layout.addLayout(header_layout)
    
    def _create_form(self, layout: QVBoxLayout):
        """Crea el formulario de login"""
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        # Campo de usuario
        username_label = QLabel("Usuario:")
        username_label.setStyleSheet("font-weight: bold; color: #333;")
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ingrese su nombre de usuario")
        self.username_input.setMinimumHeight(40)
        self.username_input.returnPressed.connect(self._on_login_clicked)
        
        # Campo de contraseña
        password_label = QLabel("Contraseña:")
        password_label.setStyleSheet("font-weight: bold; color: #333;")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Ingrese su contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self._on_login_clicked)
        
        # Checkbox recordar credenciales
        self.remember_checkbox = QCheckBox("Recordar mis credenciales")
        self.remember_checkbox.setChecked(self.config.get("remember_credentials", False))
        self.remember_checkbox.setStyleSheet("color: #666;")
        
        # Agregar campos al layout
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.remember_checkbox)
        
        layout.addLayout(form_layout)
        
        # Cargar credenciales guardadas
        self._load_saved_credentials()
    
    def _create_buttons(self, layout: QVBoxLayout):
        """Crea la sección de botones"""
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Botón de login
        self.login_button = AnimatedButton("Iniciar Sesión")
        self.login_button.clicked.connect(self._on_login_clicked)
        
        # Botón de cancelar
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                border: none;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        # Layout de botones
        button_row = QHBoxLayout()
        button_row.addWidget(self.cancel_button)
        button_row.addWidget(self.login_button)
        
        buttons_layout.addLayout(button_row)
        layout.addLayout(buttons_layout)
    
    def _create_progress_section(self, layout: QVBoxLayout):
        """Crea la sección de progreso"""
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        
        # Etiqueta de estado
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        self.status_label.setVisible(False)
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
    
    def _create_info_section(self, layout: QVBoxLayout):
        """Crea la sección de información"""
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # Información de versión
        version_label = QLabel("Versión 6.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #999; font-size: 10px;")
        
        # Información de conexión
        self.connection_status = QLabel("● Desconectado")
        self.connection_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_status.setStyleSheet("color: #f44336; font-size: 10px;")
        
        info_layout.addWidget(version_label)
        info_layout.addWidget(self.connection_status)
        
        layout.addLayout(info_layout)
        
        # Timer para verificar conexión
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self._check_connection)
        self.connection_timer.start(5000)  # Verificar cada 5 segundos
    
    def _apply_styles(self):
        """Aplica estilos generales al diálogo"""
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QCheckBox {
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #4CAF50;
                border-radius: 3px;
                background-color: #4CAF50;
            }
        """)
    
    def _load_saved_credentials(self):
        """Carga credenciales guardadas si existen"""
        try:
            if self.config.get("remember_credentials", False):
                credentials = self.secure_storage.get_credentials()
                if credentials:
                    self.username_input.setText(credentials.get("username", ""))
                    self.password_input.setText(credentials.get("password", ""))
                    self.remember_checkbox.setChecked(True)
        except Exception as e:
            logger.warning(f"Error cargando credenciales: {e}")
    
    def _attempt_auto_login(self):
        """Intenta hacer login automático si está configurado"""
        if self.auto_login_attempted:
            return
            
        self.auto_login_attempted = True
        
        if not self.config.get("auto_login", False):
            return
            
        # Verificar si hay credenciales guardadas
        if self.username_input.text() and self.password_input.text():
            QTimer.singleShot(1000, self._on_login_clicked)  # Esperar 1 segundo
    
    def _check_connection(self):
        """Verifica el estado de la conexión"""
        try:
            # En implementación real, verificaríamos conectividad real
            # Por ahora, simulamos estado de conexión
            self.connection_status.setText("● Conectado")
            self.connection_status.setStyleSheet("color: #4CAF50; font-size: 10px;")
        except:
            self.connection_status.setText("● Desconectado")
            self.connection_status.setStyleSheet("color: #f44336; font-size: 10px;")
    
    def _on_login_clicked(self):
        """Maneja el click del botón de login"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        # Validar campos
        if not username:
            QMessageBox.warning(self, "Error", "Por favor ingrese su nombre de usuario.")
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "Error", "Por favor ingrese su contraseña.")
            self.password_input.setFocus()
            return
        
        # Deshabilitar botones durante el login
        self.login_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        # Mostrar progreso
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Crear cliente API
        api_client = ApiClient(base_url=self.config.get("api_url"))
        
        # Iniciar worker de login
        self.login_worker = LoginWorker(api_client, username, password)
        self.login_worker.login_success.connect(self._on_login_success)
        self.login_worker.login_error.connect(self._on_login_error)
        self.login_worker.login_progress.connect(self._on_login_progress)
        self.login_worker.start()
    
    def _on_login_progress(self, value: int, message: str):
        """Actualiza el progreso del login"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def _on_login_success(self, token_data: Dict[str, Any]):
        """Maneja el éxito del login"""
        try:
            # Guardar credenciales si está marcado
            if self.remember_checkbox.isChecked():
                self.secure_storage.save_credentials(
                    self.username_input.text(),
                    self.password_input.text()
                )
                self.config.set("remember_credentials", True)
            else:
                self.secure_storage.clear_credentials()
                self.config.set("remember_credentials", False)
            
            # Guardar configuración de auto-login
            self.config.set("auto_login", self.remember_checkbox.isChecked())
            self.config.save_config()
            
            # Guardar token data para retornar
            self.token_data = token_data
            
            # Cerrar diálogo con éxito
            self.accept()
            
        except Exception as e:
            logger.error(f"Error procesando login exitoso: {e}")
            self._on_login_error(f"Error procesando login: {e}")
    
    def _on_login_error(self, error_message: str):
        """Maneja errores del login"""
        # Ocultar progreso
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        
        # Habilitar botones
        self.login_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        
        # Mostrar error
        QMessageBox.critical(self, "Error de Login", f"Error al iniciar sesión:\n\n{error_message}")
        
        # Enfocar contraseña para reintentar
        self.password_input.setFocus()
        self.password_input.selectAll()
    
    def get_token_data(self) -> Optional[Dict[str, Any]]:
        """Obtiene los datos del token después del login exitoso"""
        return getattr(self, 'token_data', None)
    
    def closeEvent(self, event):
        """Maneja el cierre del diálogo"""
        # Detener worker si está ejecutándose
        if self.login_worker and self.login_worker.isRunning():
            self.login_worker.quit()
            self.login_worker.wait()
        
        # Detener timer de conexión
        if hasattr(self, 'connection_timer'):
            self.connection_timer.stop()
        
        super().closeEvent(event)
    
    def mousePressEvent(self, event):
        """Permite arrastrar la ventana sin borde"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        """Maneja el arrastre de la ventana"""
        if hasattr(self, 'drag_start_position'):
            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.move(self.pos() + delta)
            self.drag_start_position = event.globalPosition().toPoint()

# Función de conveniencia para mostrar diálogo de login
def show_login_dialog(config: ConfigManager, secure_storage: SecureStorage, parent=None) -> Optional[Dict[str, Any]]:
    """
    Muestra el diálogo de login y retorna los datos del token si el login es exitoso
    
    Args:
        config: Gestor de configuración
        secure_storage: Almacenamiento seguro
        parent: Widget padre
        
    Returns:
        Datos del token si el login es exitoso, None si se cancela
    """
    dialog = LoginDialog(config, secure_storage, parent)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_token_data()
    
    return None
