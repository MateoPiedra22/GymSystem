#!/usr/bin/env python3
"""
Script para crear usuario administrador con validaciones de seguridad mejoradas
ACTUALIZADO: Validaciones estrictas y configuraciones seguras
"""

import os
import sys
import re
import secrets
import hashlib
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/admin_creation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from app.core.config import settings
    from app.core.database import SessionLocal
    from app.models.usuarios import Usuario
    from app.core.auth import get_password_hash
    from sqlalchemy.orm import Session
    from sqlalchemy import text
except ImportError as e:
    logger.error(f"Error al importar módulos: {e}")
    logger.error("Asegúrate de que todas las dependencias estén instaladas")
    sys.exit(1)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valida la fortaleza de la contraseña según criterios estrictos
    
    Args:
        password: Contraseña a validar
        
    Returns:
        Tuple con (es_válida, mensaje_error)
    """
    if len(password) < 12:
        return False, "La contraseña debe tener al menos 12 caracteres"
    
    if len(password) > 128:
        return False, "La contraseña no puede exceder 128 caracteres"
    
    # Verificar complejidad
    checks = [
        (re.search(r'[a-z]', password), "debe contener al menos una letra minúscula"),
        (re.search(r'[A-Z]', password), "debe contener al menos una letra mayúscula"),
        (re.search(r'\d', password), "debe contener al menos un número"),
        (re.search(r'[!@#$%^&*()_+\-=\[\]{};:\",.<>?/\\|`~]', password), "debe contener al menos un símbolo especial"),
    ]
    
    for check, message in checks:
        if not check:
            return False, f"La contraseña {message}"
    
    # Verificar que no contenga patrones comunes inseguros
    insecure_patterns = [
        r'123456', r'password', r'admin', r'qwerty', r'letmein',
        r'welcome', r'monkey', r'1234567890', r'abcdefgh',
        r'gym', r'sistema', r'user', r'root'
    ]
    
    password_lower = password.lower()
    for pattern in insecure_patterns:
        if re.search(pattern, password_lower):
            return False, f"La contraseña no debe contener patrones comunes inseguros como '{pattern}'"
    
    # Verificar que no tenga secuencias repetitivas
    if re.search(r'(.)\1{3,}', password):
        return False, "La contraseña no debe contener más de 3 caracteres repetidos consecutivos"
    
    return True, "Contraseña válida"

def validate_email(email: str) -> bool:
    """Valida formato de email"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_username(username: str) -> tuple[bool, str]:
    """Valida formato de nombre de usuario"""
    if len(username) < 3:
        return False, "El nombre de usuario debe tener al menos 3 caracteres"
    
    if len(username) > 50:
        return False, "El nombre de usuario no puede exceder 50 caracteres"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "El nombre de usuario solo puede contener letras, números, guiones y guiones bajos"
    
    return True, "Nombre de usuario válido"

def generate_secure_password() -> str:
    """Genera una contraseña segura automáticamente"""
    # Generar contraseña con alta entropía
    password = secrets.token_urlsafe(16)
    
    # Asegurar que contenga al menos un carácter de cada tipo requerido
    password = password + secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    password = password + secrets.choice("abcdefghijklmnopqrstuvwxyz")
    password = password + secrets.choice("0123456789")
    password = password + secrets.choice("!@#$%^&*")
    
    # Mezclar los caracteres
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    
    return ''.join(password_list)

def check_admin_exists(db: Session) -> bool:
    """Verifica si ya existe un usuario administrador"""
    try:
        admin_count = db.query(Usuario).filter(Usuario.es_admin == True).count()
        return admin_count > 0
    except Exception as e:
        logger.error(f"Error al verificar existencia de admin: {e}")
        return False

def create_admin_user(db: Session, username: str, email: str, password: str) -> bool:
    """
    Crea el usuario administrador en la base de datos
    
    Args:
        db: Sesión de base de datos
        username: Nombre de usuario
        email: Email del administrador
        password: Contraseña
        
    Returns:
        True si fue creado exitosamente
    """
    try:
        # Verificar si el usuario ya existe
        existing_user = db.query(Usuario).filter(
            (Usuario.username == username) | (Usuario.email == email)
        ).first()
        
        if existing_user:
            logger.error(f"Ya existe un usuario con el nombre '{username}' o email '{email}'")
            return False
        
        # Crear hash de la contraseña
        hashed_password = get_password_hash(password)
        
        # Crear usuario administrador
        admin_user = Usuario(
            username=username,
            email=email,
            nombre="Administrador",
            apellido="Sistema",
            hashed_password=hashed_password,
            es_admin=True,
            es_activo=True,
            fecha_creacion=None,  # Se establece automáticamente
            ultimo_acceso=None
        )
        
        db.add(admin_user)
        db.commit()
        
        logger.info(f"Usuario administrador '{username}' creado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error al crear usuario administrador: {e}")
        db.rollback()
        return False

def audit_log_admin_creation(username: str, email: str, success: bool):
    """Registra la creación del admin en logs de auditoría"""
    action = "ADMIN_CREATION_SUCCESS" if success else "ADMIN_CREATION_FAILURE"
    
    audit_entry = {
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="audit", level=logging.INFO, pathname="", lineno=0,
            msg="", args=(), exc_info=None
        )),
        "action": action,
        "username": username,
        "email": email,
        "source": "create_admin_script"
    }
    
    # Escribir a archivo de auditoría
    audit_file = Path("logs/audit.log")
    audit_file.parent.mkdir(exist_ok=True)
    
    with open(audit_file, "a") as f:
        f.write(f"{audit_entry}\n")

def main():
    """Función principal del script"""
    logger.info("=== INICIANDO CREACIÓN DE USUARIO ADMINISTRADOR ===")
    
    # Verificar configuración de entorno
    if settings.ENV == "production":
        logger.warning("⚠️  MODO PRODUCCIÓN DETECTADO - Validaciones estrictas habilitadas")
    
    # Obtener credenciales desde variables de entorno
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@gymnasium.local")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    # Validar configuración
    if not admin_password:
        logger.error("❌ ERROR: La variable de entorno ADMIN_PASSWORD no está configurada")
        logger.info("📋 Configura la contraseña del administrador:")
        logger.info("   export ADMIN_PASSWORD='tu_contraseña_segura'")
        logger.info("   o configúrala en el archivo .env")
        return False
    
    # Validaciones de seguridad
    username_valid, username_msg = validate_username(admin_username)
    if not username_valid:
        logger.error(f"❌ ERROR: Nombre de usuario inválido: {username_msg}")
        return False
    
    if not validate_email(admin_email):
        logger.error(f"❌ ERROR: Email inválido: {admin_email}")
        return False
    
    # Validar contraseña insegura en producción
    if settings.ENV == "production":
        insecure_passwords = [
            "changeme123", "admin123", "password", "123456", "admin", 
            "gympass", "gymnasium", "sistema", "LocalDev2024!SecurePass"
        ]
        
        if admin_password in insecure_passwords:
            logger.error("❌ ERROR: La contraseña proporcionada es insegura para producción")
            logger.info("📋 Genera una contraseña segura:")
            logger.info("   python -c \"import secrets; print(secrets.token_urlsafe(16))\"")
            return False
    
    # Validar fortaleza de contraseña
    password_valid, password_msg = validate_password_strength(admin_password)
    if not password_valid:
        logger.error(f"❌ ERROR: Contraseña insegura: {password_msg}")
        
        if settings.ENV != "production":
            logger.info("💡 ¿Generar contraseña segura automáticamente? (y/n)")
            if input().lower() == 'y':
                admin_password = generate_secure_password()
                logger.info(f"🔐 Contraseña generada: {admin_password}")
                logger.warning("⚠️  GUARDA ESTA CONTRASEÑA EN UN LUGAR SEGURO")
            else:
                return False
        else:
            return False
    
    # Conectar a la base de datos
    try:
        db = SessionLocal()
        
        # Verificar conexión
        db.execute(text("SELECT 1"))
        logger.info("✅ Conexión a base de datos exitosa")
        
        # Verificar si ya existe un administrador
        if check_admin_exists(db):
            logger.warning("⚠️  Ya existe un usuario administrador en el sistema")
            logger.info("📋 Para crear un nuevo administrador:")
            logger.info("   1. Elimina el administrador existente desde la interfaz")
            logger.info("   2. O usa un nombre de usuario diferente")
            return False
        
        # Crear usuario administrador
        success = create_admin_user(db, admin_username, admin_email, admin_password)
        
        # Registrar en auditoría
        audit_log_admin_creation(admin_username, admin_email, success)
        
        if success:
            logger.info("✅ Usuario administrador creado exitosamente")
            logger.info("📋 Credenciales del administrador:")
            logger.info(f"   Usuario: {admin_username}")
            logger.info(f"   Email: {admin_email}")
            logger.info(f"   Contraseña: {'[CONFIGURADA]' if admin_password else '[NO CONFIGURADA]'}")
            logger.warning("⚠️  CAMBIA LA CONTRASEÑA EN EL PRIMER LOGIN")
            
            return True
        else:
            logger.error("❌ Error al crear el usuario administrador")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR de conexión a base de datos: {e}")
        logger.info("📋 Verifica:")
        logger.info("   • Que la base de datos esté ejecutándose")
        logger.info("   • Que la configuración en .env sea correcta")
        logger.info("   • Que las credenciales sean válidas")
        return False
    
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("❌ Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ ERROR inesperado: {e}")
        sys.exit(1)
