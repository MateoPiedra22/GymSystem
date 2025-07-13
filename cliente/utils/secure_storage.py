"""
Módulo para almacenamiento seguro de credenciales y datos sensibles
"""
import os
import json
import base64
import logging
import hashlib
import secrets
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Configuración de logging
logger = logging.getLogger("secure_storage")

class SecureStorageError(Exception):
    """Excepción personalizada para errores de almacenamiento seguro"""
    pass

class SecureStorage:
    """
    Almacenamiento seguro para datos sensibles del cliente desktop
    Incluye cifrado de configuración en disco y validaciones de seguridad
    """
    
    def __init__(self, encryption_key: str = None):
        self.encryption_key = encryption_key or self._generate_key()
        self.cipher = self._create_cipher()
        self.storage_file = os.path.join(os.path.expanduser('~'), '.gym_secure_storage.dat')
    
    def _generate_key(self) -> str:
        """Generar clave de cifrado segura"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _create_cipher(self):
        """Crear cipher para cifrado"""
        from cryptography.fernet import Fernet
        # Convertir la clave a formato compatible con Fernet
        import base64
        key_bytes = self.encryption_key.encode()
        key_b64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
        return Fernet(key_b64)
    
    def encrypt_data(self, data: str) -> str:
        """Cifrar datos sensibles"""
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Error cifrando datos: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Descifrar datos sensibles"""
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error descifrando datos: {e}")
            raise
    
    def save_secure_config(self, config_data: dict, file_path: str):
        """Guardar configuración cifrada en disco"""
        try:
            # Cifrar datos sensibles
            sensitive_fields = ['api_key', 'password', 'token', 'secret']
            encrypted_config = config_data.copy()
            
            for field in sensitive_fields:
                if field in encrypted_config:
                    encrypted_config[field] = self.encrypt_data(str(encrypted_config[field]))
            
            # Guardar configuración cifrada
            with open(file_path, 'w') as f:
                json.dump(encrypted_config, f, indent=2)
            
            # Establecer permisos restrictivos
            os.chmod(file_path, 0o600)
            
            logger.info(f"Configuración segura guardada en: {file_path}")
            
        except Exception as e:
            logger.error(f"Error guardando configuración segura: {e}")
            raise
    
    def load_secure_config(self, file_path: str) -> dict:
        """Cargar configuración cifrada desde disco"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Archivo de configuración no encontrado: {file_path}")
                return {}
            
            # Verificar permisos
            if os.stat(file_path).st_mode & 0o777 != 0o600:
                logger.warning(f"Permisos inseguros en archivo de configuración: {file_path}")
            
            with open(file_path, 'r') as f:
                encrypted_config = json.load(f)
            
            # Descifrar datos sensibles
            sensitive_fields = ['api_key', 'password', 'token', 'secret']
            decrypted_config = encrypted_config.copy()
            
            for field in sensitive_fields:
                if field in decrypted_config:
                    try:
                        decrypted_config[field] = self.decrypt_data(decrypted_config[field])
                    except Exception as e:
                        logger.error(f"Error descifrando campo {field}: {e}")
                        decrypted_config[field] = None
            
            logger.info(f"Configuración segura cargada desde: {file_path}")
            return decrypted_config
            
        except Exception as e:
            logger.error(f"Error cargando configuración segura: {e}")
            return {}
    
    def validate_config_integrity(self, config_data: dict) -> bool:
        """Validar integridad de la configuración"""
        try:
            required_fields = ['api_url', 'app_name', 'version']
            for field in required_fields:
                if field not in config_data:
                    logger.error(f"Campo requerido faltante: {field}")
                    return False
            
            # Validar URL de API
            api_url = config_data.get('api_url', '')
            if not api_url.startswith(('http://', 'https://')):
                logger.error(f"URL de API inválida: {api_url}")
                return False
            
            # Validar que no contenga datos sensibles en texto plano
            sensitive_patterns = ['password', 'secret', 'key', 'token']
            config_str = json.dumps(config_data).lower()
            for pattern in sensitive_patterns:
                if pattern in config_str and not any(field in config_str for field in ['encrypted', 'cipher']):
                    logger.warning(f"Posible dato sensible en texto plano: {pattern}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando integridad de configuración: {e}")
            return False
    
    def store_data(self, data: Dict[str, Any]) -> bool:
        """
        Almacena datos de forma segura
        
        Args:
            data: Diccionario con datos a almacenar
            
        Returns:
            True si se almacenó correctamente, False en caso contrario
        """
        try:
            # Validar entrada
            if not isinstance(data, dict):
                raise ValueError("Los datos deben ser un diccionario")
            
            # Serializar datos
            json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            
            # Cifrar datos
            encrypted_data = self.cipher.encrypt(json_data)
            
            # Crear respaldo del archivo existente
            if os.path.exists(self.storage_file):
                backup_file = f"{self.storage_file}.backup"
                try:
                    os.rename(self.storage_file, backup_file)
                except Exception as e:
                    logger.warning(f"No se pudo crear respaldo: {e}")
            
            # Guardar datos cifrados
            with open(self.storage_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Establecer permisos restrictivos
            os.chmod(self.storage_file, 0o600)
            
            # Eliminar respaldo si todo salió bien
            backup_file = f"{self.storage_file}.backup"
            if os.path.exists(backup_file):
                os.remove(backup_file)
            
            logger.info("Datos almacenados de forma segura")
            return True
            
        except Exception as e:
            logger.error(f"Error al almacenar datos: {e}")
            
            # Restaurar respaldo si existe
            backup_file = f"{self.storage_file}.backup"
            if os.path.exists(backup_file):
                try:
                    os.rename(backup_file, self.storage_file)
                    logger.info("Respaldo restaurado")
                except Exception as restore_error:
                    logger.error(f"Error al restaurar respaldo: {restore_error}")
            
            return False
    
    def load_data(self) -> Dict[str, Any]:
        """
        Carga datos almacenados de forma segura
        
        Returns:
            Diccionario con datos almacenados, o diccionario vacío si hay error
        """
        try:
            # Verificar si el archivo existe
            if not os.path.exists(self.storage_file):
                logger.info("Archivo de almacenamiento seguro no encontrado")
                return {}
            
            # Verificar permisos del archivo
            file_mode = os.stat(self.storage_file).st_mode & 0o777
            if file_mode != 0o600:
                logger.warning(f"Permisos inseguros en archivo de almacenamiento: {oct(file_mode)}")
            
            # Leer datos cifrados
            with open(self.storage_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Verificar que no esté vacío
            if not encrypted_data:
                logger.warning("Archivo de almacenamiento vacío")
                return {}
            
            # Descifrar datos
            try:
                json_data = self.cipher.decrypt(encrypted_data)
            except Exception as e:
                logger.error(f"Error al descifrar datos: {e}")
                raise SecureStorageError("No se pudieron descifrar los datos. Clave incorrecta o datos corruptos.")
            
            # Convertir JSON a diccionario
            try:
                data = json.loads(json_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Error al decodificar JSON: {e}")
                raise SecureStorageError("Datos corruptos en el almacenamiento")
            
            logger.info("Datos cargados correctamente")
            return data
            
        except SecureStorageError:
            raise
        except Exception as e:
            logger.error(f"Error al cargar datos: {e}")
            return {}
    
    def store_credentials(self, username: str, password: str, remember: bool = True) -> bool:
        """
        Almacena credenciales de usuario
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            remember: Indica si se deben recordar las credenciales
            
        Returns:
            True si se almacenó correctamente, False en caso contrario
        """
        try:
            # Validar entrada
            if not username or not isinstance(username, str):
                raise ValueError("Username inválido")
            
            if not password or not isinstance(password, str):
                raise ValueError("Password inválido")
            
            # Sanitizar username
            username = username.strip().lower()
            
            # Cargar datos existentes
            data = self.load_data()
            
            # Actualizar credenciales
            data["credentials"] = {
                "username": username,
                "password": password if remember else "",
                "remember": remember,
                "last_updated": json.dumps({"timestamp": str(os.path.getmtime(self.storage_file)) if os.path.exists(self.storage_file) else "0"})
            }
            
            return self.store_data(data)
            
        except Exception as e:
            logger.error(f"Error al almacenar credenciales: {e}")
            return False
    
    def save_credentials(self, username: str, password: str, remember: bool = True) -> bool:
        """Alias para store_credentials por compatibilidad"""
        return self.store_credentials(username, password, remember)
    
    def get_credentials(self) -> Dict[str, str]:
        """
        Obtiene credenciales almacenadas
        
        Returns:
            Diccionario con username y password, o vacío si no hay
        """
        try:
            data = self.load_data()
            credentials = data.get("credentials", {})
            
            # Verificar si se deben recordar
            if not credentials.get("remember", False):
                credentials["password"] = ""
            
            # Remover campos internos
            result = {
                "username": credentials.get("username", ""),
                "password": credentials.get("password", ""),
                "remember": credentials.get("remember", False)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error al obtener credenciales: {e}")
            return {}
    
    def clear_credentials(self) -> bool:
        """
        Elimina credenciales almacenadas
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            data = self.load_data()
            
            if "credentials" in data:
                del data["credentials"]
                result = self.store_data(data)
                logger.info("Credenciales eliminadas")
                return result
            
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar credenciales: {e}")
            return False
    
    def store_token(self, token_data: Dict[str, Any]) -> bool:
        """
        Almacena datos de token de autenticación
        
        Args:
            token_data: Datos del token
            
        Returns:
            True si se almacenó correctamente, False en caso contrario
        """
        try:
            # Validar entrada
            if not isinstance(token_data, dict):
                raise ValueError("Token data debe ser un diccionario")
            
            data = self.load_data()
            
            # Actualizar token
            data["token"] = token_data
            
            return self.store_data(data)
            
        except Exception as e:
            logger.error(f"Error al almacenar token: {e}")
            return False
    
    def get_token(self) -> Dict[str, Any]:
        """
        Obtiene datos de token almacenados
        
        Returns:
            Diccionario con datos del token, o vacío si no hay
        """
        try:
            data = self.load_data()
            return data.get("token", {})
            
        except Exception as e:
            logger.error(f"Error al obtener token: {e}")
            return {}
    
    def clear_token(self) -> bool:
        """
        Elimina token almacenado
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            data = self.load_data()
            
            if "token" in data:
                del data["token"]
                result = self.store_data(data)
                logger.info("Token eliminado")
                return result
            
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar token: {e}")
            return False
    
    def wipe_storage(self) -> bool:
        """
        Elimina completamente el almacenamiento seguro
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            files_to_remove = [self.storage_file, self.salt_file, self.key_file]
            
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            logger.info("Almacenamiento seguro eliminado completamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar almacenamiento: {e}")
            return False
