"""
Aplicación principal del Sistema de Gimnasio v6
Integra navegación moderna, notificaciones toast y accesibilidad
"""
import sys
import logging
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtGui import QIcon, QFont

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/client.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Importar módulos del sistema (usar imports absolutos para compatibilidad)
from cliente.widgets.navigation_widget import NavigationWidget
from cliente.widgets.toast_notifications import ToastContainer, toast_manager
from cliente.utils.accessibility import accessibility_manager
from cliente.utils.config_manager import ConfigManager
from cliente.api_client import ApiClient
from cliente.sync_service import SyncService

# Importar widgets de funcionalidad
from widgets.dashboard_widget import DashboardWidget
from widgets.usuarios_tab_widget import UsuariosTabWidget
from widgets.clases_tab_widget import ClasesTabWidget
from widgets.pagos_tab_widget import PagosTabWidget
from widgets.asistencias_tab_widget import AsistenciasTabWidget
from widgets.reportes_tab_widget import ReportesTabWidget
from widgets.configuracion_tab_widget import ConfiguracionTabWidget

logger = logging.getLogger(__name__)

class GymSystemMainWindow(QMainWindow):
    """Ventana principal del Sistema de Gimnasio v6"""
    
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.api_client = ApiClient()
        self.sync_service = SyncService()
        
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        self.initialize_system()
    
    def setup_ui(self):
        """Configura la interfaz principal"""
        self.setWindowTitle("Sistema de Gimnasio v6")
        self.setMinimumSize(1200, 800)
        self.setObjectName("mainWindow")
        
        # Configurar icono
        icon_path = Path("assets/icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sistema de navegación
        self.navigation = NavigationWidget()
        main_layout.addWidget(self.navigation)
        
        # Configurar páginas de contenido
        self.setup_content_pages()
        
        # Contenedor de notificaciones toast
        self.toast_container = ToastContainer(self)
        self.toast_container.setGeometry(
            self.width() - 470, 80, 450, self.height() - 160
        )
        self.toast_container.raise_()
        
        # Configurar gestor de notificaciones
        toast_manager.set_container(self.toast_container)
        
        # Configurar gestor de accesibilidad
        accessibility_manager.set_main_window(self)
        
        # Barra de estado
        self.statusBar().setObjectName("statusBar")
        self.statusBar().showMessage("Sistema listo")
    
    def setup_content_pages(self):
        """Configura las páginas de contenido"""
        # Dashboard
        self.dashboard_widget = DashboardWidget(self.api_client, self.config)
        self.navigation.add_content_page("dashboard", self.dashboard_widget)
        # Usuarios
        self.usuarios_widget = UsuariosTabWidget(self.api_client, self.config)
        self.navigation.add_content_page("usuarios", self.usuarios_widget)
        # Clases
        self.clases_widget = ClasesTabWidget(self.api_client, self.config)
        self.navigation.add_content_page("clases", self.clases_widget)
        # Pagos
        self.pagos_widget = PagosTabWidget(self.api_client, self.config)
        self.navigation.add_content_page("pagos", self.pagos_widget)
        # Asistencias
        self.asistencias_widget = AsistenciasTabWidget(self.api_client, self.config)
        self.navigation.add_content_page("asistencias", self.asistencias_widget)
        # Reportes
        self.reportes_widget = ReportesTabWidget(self.api_client, self.config)
        self.navigation.add_content_page("reportes", self.reportes_widget)
        # Configuración
        self.configuracion_widget = ConfiguracionTabWidget(self.api_client, self.config)
        self.navigation.add_content_page("configuracion", self.configuracion_widget)
        # Subpáginas
        self.setup_subpages()
    
    def setup_subpages(self):
        """Configura las subpáginas"""
        # Subpáginas de usuarios
        from cliente.widgets.usuarios_lista_widget import UsuariosListaWidget
        from cliente.widgets.usuarios_nuevo_widget import UsuariosNuevoWidget
        self.usuarios_lista_widget = UsuariosListaWidget(self.api_client, self.config)
        self.navigation.add_content_page("usuarios_lista", self.usuarios_lista_widget)
        self.usuarios_nuevo_widget = UsuariosNuevoWidget(self.api_client, self.config)
        self.navigation.add_content_page("usuarios_nuevo", self.usuarios_nuevo_widget)
        # Subpáginas de reportes
        from cliente.widgets.reportes_kpis_widget import ReportesKPIsWidget
        from cliente.widgets.reportes_graficos_widget import ReportesGraficosWidget
        self.reportes_kpis_widget = ReportesKPIsWidget(self.api_client, self.config)
        self.navigation.add_content_page("reportes_kpis", self.reportes_kpis_widget)
        self.reportes_graficos_widget = ReportesGraficosWidget(self.api_client, self.config)
        self.navigation.add_content_page("reportes_graficos", self.reportes_graficos_widget)
    
    def setup_connections(self):
        """Configura las conexiones entre componentes"""
        # Navegación
        self.navigation.navigation_changed.connect(self.on_navigation_changed)
        self.navigation.search_performed.connect(self.on_search_performed)
        
        # Dashboard
        self.dashboard_widget.refresh_requested.connect(self.refresh_dashboard)
        
        # Usuarios
        self.usuarios_widget.user_created.connect(self.on_user_created)
        self.usuarios_widget.user_updated.connect(self.on_user_updated)
        self.usuarios_widget.user_deleted.connect(self.on_user_deleted)
        
        # Clases
        self.clases_widget.class_created.connect(self.on_class_created)
        self.clases_widget.class_updated.connect(self.on_class_updated)
        self.clases_widget.class_deleted.connect(self.on_class_deleted)
        
        # Pagos
        self.pagos_widget.payment_created.connect(self.on_payment_created)
        self.pagos_widget.payment_updated.connect(self.on_payment_updated)
        self.pagos_widget.payment_deleted.connect(self.on_payment_deleted)
        
        # Asistencias
        self.asistencias_widget.attendance_created.connect(self.on_attendance_created)
        self.asistencias_widget.attendance_updated.connect(self.on_attendance_updated)
        self.asistencias_widget.attendance_deleted.connect(self.on_attendance_deleted)
        
        # Reportes
        self.reportes_widget.report_generated.connect(self.on_report_generated)
        
        # Configuración
        self.configuracion_widget.config_updated.connect(self.on_config_updated)
        
        # Sincronización
        self.sync_service.sync_started.connect(self.on_sync_started)
        self.sync_service.sync_completed.connect(self.on_sync_completed)
        self.sync_service.sync_error.connect(self.on_sync_error)
        
        # API Client
        self.api_client.connection_status_changed.connect(self.on_connection_status_changed)
        self.api_client.error_occurred.connect(self.on_api_error)
    
    def load_settings(self):
        """Carga la configuración de la aplicación"""
        try:
            # Cargar configuración de la ventana
            settings = QSettings('GymSystem', 'Client')
            geometry = settings.value('geometry')
            if geometry:
                self.restoreGeometry(geometry)
            
            # Cargar tema
            theme = self.config.get_setting('theme', 'claro')
            self.apply_theme(theme)
            
            # Cargar configuración de accesibilidad
            accessibility_manager.load_settings()
            
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            toast_manager.error("Error", "No se pudo cargar la configuración")
    
    def save_settings(self):
        """Guarda la configuración de la aplicación"""
        try:
            # Guardar configuración de la ventana
            settings = QSettings('GymSystem', 'Client')
            settings.setValue('geometry', self.saveGeometry())
            
            # Guardar configuración de accesibilidad
            accessibility_manager.save_settings()
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
    
    def initialize_system(self):
        """Inicializa el sistema"""
        try:
            # Verificar conexión al servidor
            if self.api_client.check_connection():
                toast_manager.success("Conexión establecida", "Servidor conectado correctamente")
                self.statusBar().showMessage("Conectado al servidor")
                
                # Iniciar sincronización
                self.sync_service.start_sync()
            else:
                toast_manager.warning("Sin conexión", "Modo offline activado")
                self.statusBar().showMessage("Modo offline")
            
            # Cargar datos iniciales
            self.load_initial_data()
            
            # Establecer página inicial
            self.navigation.set_current_navigation("dashboard")
            
        except Exception as e:
            logger.error(f"Error inicializando sistema: {e}")
            toast_manager.error("Error de inicialización", str(e))
    
    def load_initial_data(self):
        """Carga datos iniciales"""
        try:
            # Cargar dashboard
            self.dashboard_widget.load_data()
            
            # Cargar usuarios
            self.usuarios_widget.load_data()
            
            # Cargar clases
            self.clases_widget.load_data()
            
            # Cargar pagos
            self.pagos_widget.load_data()
            
            # Cargar asistencias
            self.asistencias_widget.load_data()
            
        except Exception as e:
            logger.error(f"Error cargando datos iniciales: {e}")
            toast_manager.error("Error", "No se pudieron cargar los datos iniciales")
    
    def apply_theme(self, theme_name: str):
        """Aplica un tema"""
        try:
            theme_file = f"themes/{theme_name}.qss"
            if os.path.exists(theme_file):
                with open(theme_file, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                self.setStyleSheet(stylesheet)
                self.config.set_setting('theme', theme_name)
                toast_manager.info("Tema aplicado", f"Tema {theme_name} activado")
            else:
                logger.warning(f"Archivo de tema no encontrado: {theme_file}")
        except Exception as e:
            logger.error(f"Error aplicando tema: {e}")
    
    def on_navigation_changed(self, item_id: str):
        """Maneja cambios en la navegación"""
        try:
            # Cambiar página
            self.navigation.set_current_page(item_id)
            
            # Cargar datos específicos de la página
            self.load_page_data(item_id)
            
            # Anunciar para accesibilidad
            accessibility_manager.announce(f"Navegando a {item_id}")
            
        except Exception as e:
            logger.error(f"Error en navegación: {e}")
            toast_manager.error("Error de navegación", str(e))
    
    def load_page_data(self, page_id: str):
        """Carga datos específicos de una página"""
        try:
            if page_id == "dashboard":
                self.dashboard_widget.load_data()
            elif page_id == "usuarios":
                self.usuarios_widget.load_data()
            elif page_id == "clases":
                self.clases_widget.load_data()
            elif page_id == "pagos":
                self.pagos_widget.load_data()
            elif page_id == "asistencias":
                self.asistencias_widget.load_data()
            elif page_id == "reportes":
                self.reportes_widget.load_data()
            elif page_id == "configuracion":
                self.configuracion_widget.load_data()
        except Exception as e:
            logger.error(f"Error cargando datos de página {page_id}: {e}")
    
    def on_search_performed(self, search_text: str):
        """Maneja búsquedas globales"""
        try:
            # Implementar búsqueda global
            results = self.perform_global_search(search_text)
            
            if results:
                toast_manager.info("Búsqueda completada", f"Se encontraron {len(results)} resultados")
                # TODO: Mostrar resultados en una ventana de búsqueda
            else:
                toast_manager.info("Búsqueda completada", "No se encontraron resultados")
                
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            toast_manager.error("Error de búsqueda", str(e))
    
    def perform_global_search(self, search_text: str) -> list:
        """Realiza una búsqueda global"""
        # TODO: Implementar búsqueda en todos los módulos
        return []
    
    def refresh_dashboard(self):
        """Actualiza el dashboard"""
        try:
            self.dashboard_widget.load_data()
            toast_manager.success("Dashboard actualizado", "Datos refrescados correctamente")
        except Exception as e:
            logger.error(f"Error actualizando dashboard: {e}")
            toast_manager.error("Error", "No se pudo actualizar el dashboard")
    
    # Eventos de usuarios
    def on_user_created(self, user_data: dict):
        """Maneja creación de usuario"""
        toast_manager.success("Usuario creado", f"Usuario {user_data.get('nombre', '')} creado exitosamente")
        self.dashboard_widget.load_data()  # Actualizar estadísticas
    
    def on_user_updated(self, user_data: dict):
        """Maneja actualización de usuario"""
        toast_manager.success("Usuario actualizado", f"Usuario {user_data.get('nombre', '')} actualizado exitosamente")
    
    def on_user_deleted(self, user_id: int):
        """Maneja eliminación de usuario"""
        toast_manager.success("Usuario eliminado", "Usuario eliminado exitosamente")
        self.dashboard_widget.load_data()  # Actualizar estadísticas
    
    # Eventos de clases
    def on_class_created(self, class_data: dict):
        """Maneja creación de clase"""
        toast_manager.success("Clase creada", f"Clase {class_data.get('nombre', '')} creada exitosamente")
        self.dashboard_widget.load_data()
    
    def on_class_updated(self, class_data: dict):
        """Maneja actualización de clase"""
        toast_manager.success("Clase actualizada", f"Clase {class_data.get('nombre', '')} actualizada exitosamente")
    
    def on_class_deleted(self, class_id: int):
        """Maneja eliminación de clase"""
        toast_manager.success("Clase eliminada", "Clase eliminada exitosamente")
        self.dashboard_widget.load_data()
    
    # Eventos de pagos
    def on_payment_created(self, payment_data: dict):
        """Maneja creación de pago"""
        toast_manager.success("Pago registrado", f"Pago de ${payment_data.get('monto', 0)} registrado exitosamente")
        self.dashboard_widget.load_data()
    
    def on_payment_updated(self, payment_data: dict):
        """Maneja actualización de pago"""
        toast_manager.success("Pago actualizado", "Pago actualizado exitosamente")
    
    def on_payment_deleted(self, payment_id: int):
        """Maneja eliminación de pago"""
        toast_manager.success("Pago eliminado", "Pago eliminado exitosamente")
        self.dashboard_widget.load_data()
    
    # Eventos de asistencias
    def on_attendance_created(self, attendance_data: dict):
        """Maneja creación de asistencia"""
        toast_manager.success("Asistencia registrada", "Asistencia registrada exitosamente")
        self.dashboard_widget.load_data()
    
    def on_attendance_updated(self, attendance_data: dict):
        """Maneja actualización de asistencia"""
        toast_manager.success("Asistencia actualizada", "Asistencia actualizada exitosamente")
    
    def on_attendance_deleted(self, attendance_id: int):
        """Maneja eliminación de asistencia"""
        toast_manager.success("Asistencia eliminada", "Asistencia eliminada exitosamente")
        self.dashboard_widget.load_data()
    
    # Eventos de reportes
    def on_report_generated(self, report_data: dict):
        """Maneja generación de reporte"""
        toast_manager.success("Reporte generado", f"Reporte {report_data.get('nombre', '')} generado exitosamente")
    
    # Eventos de configuración
    def on_config_updated(self, config_data: dict):
        """Maneja actualización de configuración"""
        toast_manager.success("Configuración actualizada", "Configuración guardada exitosamente")
        
        # Aplicar cambios si es necesario
        if 'theme' in config_data:
            self.apply_theme(config_data['theme'])
    
    # Eventos de sincronización
    def on_sync_started(self):
        """Maneja inicio de sincronización"""
        self.statusBar().showMessage("Sincronizando...")
        toast_manager.info("Sincronización", "Iniciando sincronización con el servidor")
    
    def on_sync_completed(self, sync_data: dict):
        """Maneja completación de sincronización"""
        self.statusBar().showMessage("Sincronización completada")
        toast_manager.success("Sincronización completada", 
                            f"Sincronizados {sync_data.get('items_synced', 0)} elementos")
        
        # Actualizar datos
        self.load_initial_data()
    
    def on_sync_error(self, error: str):
        """Maneja errores de sincronización"""
        self.statusBar().showMessage("Error de sincronización")
        toast_manager.error("Error de sincronización", error)
    
    # Eventos de conexión
    def on_connection_status_changed(self, connected: bool):
        """Maneja cambios en el estado de conexión"""
        if connected:
            self.statusBar().showMessage("Conectado al servidor")
            toast_manager.success("Conexión restaurada", "Conexión al servidor establecida")
        else:
            self.statusBar().showMessage("Sin conexión - Modo offline")
            toast_manager.warning("Conexión perdida", "Modo offline activado")
    
    def on_api_error(self, error: str):
        """Maneja errores de API"""
        toast_manager.error("Error de API", error)
    
    def resizeEvent(self, event):
        """Maneja cambios de tamaño de la ventana"""
        super().resizeEvent(event)
        
        # Reposicionar contenedor de notificaciones
        if hasattr(self, 'toast_container'):
            self.toast_container.setGeometry(
                self.width() - 470, 80, 450, self.height() - 160
            )
    
    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        try:
            # Guardar configuración
            self.save_settings()
            
            # Detener sincronización
            self.sync_service.stop_sync()
            
            # Cerrar conexiones
            self.api_client.close()
            
            logger.info("Aplicación cerrada correctamente")
            event.accept()
            
        except Exception as e:
            logger.error(f"Error cerrando aplicación: {e}")
            event.accept()

def main():
    """Función principal de la aplicación"""
    try:
        # Crear aplicación
        app = QApplication(sys.argv)
        app.setApplicationName("Sistema de Gimnasio v6")
        app.setApplicationVersion("6.0.0")
        app.setOrganizationName("GymSystem")
        
        # Configurar fuente por defecto
        font = QFont("Segoe UI", 10)
        app.setFont(font)
        
        # Crear y mostrar ventana principal
        window = GymSystemMainWindow()
        window.show()
        
        # Ejecutar aplicación
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Error iniciando aplicación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
