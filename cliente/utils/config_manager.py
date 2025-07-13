"""
Gestor de configuración para la aplicación cliente
"""
import os
import json
import logging
from typing import Dict, Any, Optional, Union

# Configuración de logging
logger = logging.getLogger("config_manager")

class ConfigManager:
    """
    Gestor de configuración para la aplicación cliente
    
    Esta clase maneja la carga, guardado y acceso a la configuración
    de la aplicación, almacenada en un archivo JSON.
    
    Atributos:
        config_dir: Directorio de configuración
        config_file: Ruta completa al archivo de configuración
        config: Diccionario con la configuración actual
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_file: Ruta al archivo de configuración (opcional)
        """
        # Determinar directorio de configuración
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
        
        # Asegurar que el directorio existe
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # Ruta al archivo de configuración
        self.config_file = config_file or os.path.join(self.config_dir, "settings.json")
        
        # Configuración por defecto
        self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración por defecto
        
        Returns:
            Diccionario con configuración por defecto
        """
        return {
            "api_url": "http://localhost:8000/api",
            "auto_login": False,
            "remember_credentials": False,
            "sync_interval": 300,  # 5 minutos
            "offline_mode": False,
            "theme": "light",
            "language": "es",
            "debug_mode": False,
            "client_id": os.urandom(16).hex(),  # ID único para sincronización
            "max_log_size_mb": 10,
            "backup_interval_days": 7
        }
    
    def load_config(self) -> Dict[str, Any]:
        """
        Carga la configuración desde el archivo
        
        Si el archivo no existe o es inválido, se usa la configuración por defecto
        
        Returns:
            Diccionario con la configuración cargada
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Actualizar la configuración manteniendo los valores por defecto
                # para claves que no están en el archivo
                self.config.update(loaded_config)
                logger.info(f"Configuración cargada desde {self.config_file}")
            else:
                logger.warning(f"Archivo de configuración no encontrado, usando valores por defecto")
                self.save_config()  # Crear archivo con configuración por defecto
        except Exception as e:
            logger.error(f"Error al cargar la configuración: {e}")
            logger.info("Usando configuración por defecto")
        
        return self.config
    
    def save_config(self) -> bool:
        """
        Guarda la configuración actual en el archivo
        
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            
            logger.info(f"Configuración guardada en {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar la configuración: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor de configuración o valor por defecto
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Establece un valor de configuración
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
        """
        self.config[key] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Actualiza múltiples valores de configuración
        
        Args:
            config_dict: Diccionario con valores a actualizar
        """
        self.config.update(config_dict)
    
    def reset(self, key: Optional[str] = None) -> None:
        """
        Restablece la configuración a valores por defecto
        
        Args:
            key: Clave específica a restablecer, o None para restablecer todo
        """
        default_config = self._get_default_config()
        
        if key:
            if key in default_config:
                self.config[key] = default_config[key]
        else:
            self.config = default_config
    
    def sync_with_server(self, api_client=None) -> bool:
        """Sincroniza configuración con el servidor"""
        try:
            logger.info("Sincronizando configuración con servidor...")
            
            if not api_client:
                logger.warning("API client no disponible para sincronización")
                return False
            
            # Obtener configuración del servidor
            server_config = self._get_server_config(api_client)
            if server_config:
                # Fusionar configuración local con la del servidor
                self._merge_configs(server_config)
                
                # Guardar configuración actualizada
                self.save_config()
                
                logger.info("Configuración sincronizada exitosamente")
                return True
            else:
                logger.warning("No se pudo obtener configuración del servidor")
                return False
                
        except Exception as e:
            logger.error(f"Error sincronizando configuración: {e}")
            return False
    
    def _get_server_config(self, api_client) -> Optional[Dict[str, Any]]:
        """Obtiene configuración del servidor"""
        try:
            response = api_client._make_request('GET', '/configuracion/sistema')
            if response and 'data' in response:
                return response['data']
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración del servidor: {e}")
            return None
    
    def _merge_configs(self, server_config: Dict[str, Any]):
        """Fusiona configuración local con la del servidor"""
        try:
            # Configuraciones que se pueden sobrescribir desde el servidor
            server_overridable = [
                'theme', 'language', 'auto_backup', 'sync_interval',
                'notifications_enabled', 'performance_mode'
            ]
            
            for key in server_overridable:
                if key in server_config:
                    self.config[key] = server_config[key]
            
            # Configuraciones que solo se actualizan si no existen localmente
            server_defaults = [
                'api_url', 'app_name', 'version', 'features'
            ]
            
            for key in server_defaults:
                if key in server_config and key not in self.config:
                    self.config[key] = server_config[key]
                    
        except Exception as e:
            logger.error(f"Error fusionando configuraciones: {e}")
    
    def update_server_config(self, api_client, config_data: Dict[str, Any]) -> bool:
        """Actualiza configuración en el servidor"""
        try:
            response = api_client._make_request('PUT', '/configuracion/sistema', data=config_data)
            return response is not None
            
        except Exception as e:
            logger.error(f"Error actualizando configuración en servidor: {e}")
            return False
