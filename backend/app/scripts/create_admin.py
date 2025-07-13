"""
Script para asegurar la existencia del usuario administrador
"""
import logging
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.usuarios import Usuario
from app.core.auth import get_password_hash
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_admin_exists():
    """
    Verifica si el usuario administrador definido en la configuración existe.
    Si no existe, lo crea.
    """
    db: Session = SessionLocal()
    try:
        admin_username = settings.ADMIN_USERNAME
        admin_email = settings.ADMIN_EMAIL

        # Verificar si el admin ya existe por nombre de usuario o email
        existing_admin = db.query(Usuario).filter(
            (Usuario.username == admin_username) | (Usuario.email == admin_email)
        ).first()

        if existing_admin:
            logger.info(f"El usuario administrador '{admin_username}' ya existe.")
            return

        logger.info(f"Creando usuario administrador: {admin_username} ({admin_email})")

        # Crear el nuevo usuario administrador
        hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
        
        new_admin = Usuario(
            username=admin_username,
            email=admin_email,
            nombre="Administrador",
            apellido="Principal",
            hashed_password=hashed_password,
            es_admin=True,
            esta_activo=True
        )
        
        db.add(new_admin)
        db.commit()
        
        logger.info("✅ Usuario administrador creado con éxito.")

    except Exception as e:
        logger.error(f"❌ Error al crear el usuario administrador: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Ejecutando script para verificar/crear usuario administrador...")
    ensure_admin_exists() 