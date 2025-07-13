#!/usr/bin/env python3
"""
Script para crear usuario administrador del Sistema de Gimnasio v6
"""

import sys
import os
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.usuarios import Usuario
from app.core.auth import get_password_hash
from app.core.config import settings
import getpass


def create_admin(email: str = None, password: str = None, nombre: str = None):
    """Crear usuario administrador"""
    
    print("🏋️‍♂️ Sistema de Gimnasio v6 - Crear Usuario Administrador")
    print("=" * 60)
    
    # Obtener datos si no se proporcionaron
    if not email:
        email = input("📧 Email del administrador: ").strip()
    
    if not email or "@" not in email:
        print("❌ Email inválido")
        return False
    
    if not password:
        password = getpass.getpass("🔐 Contraseña del administrador: ")
        confirm_password = getpass.getpass("🔐 Confirmar contraseña: ")
        
        if password != confirm_password:
            print("❌ Las contraseñas no coinciden")
            return False
    
    if len(password) < 8:
        print("❌ La contraseña debe tener al menos 8 caracteres")
        return False
    
    if not nombre:
        nombre = input("👤 Nombre del administrador (opcional): ").strip()
        if not nombre:
            nombre = "Administrador"
    
    # Conectar a la base de datos
    try:
        db = SessionLocal()
        
        # Verificar si ya existe un usuario con ese email
        existing_user = db.query(Usuario).filter(Usuario.email == email).first()
        if existing_user:
            print(f"⚠️ Ya existe un usuario con el email {email}")
            
            update = input("¿Deseas actualizar este usuario como administrador? (s/N): ").strip().lower()
            if update in ['s', 'si', 'sí', 'y', 'yes']:
                existing_user.es_admin = True
                existing_user.esta_activo = True
                existing_user.hashed_password = get_password_hash(password)
                existing_user.nombre = nombre
                
                db.commit()
                print(f"✅ Usuario {email} actualizado como administrador")
                return True
            else:
                print("❌ Operación cancelada")
                return False
        
        # Crear nuevo usuario administrador
        admin_user = Usuario(
            email=email,
            username=email.split('@')[0],  # Usar parte del email como username
            nombre=nombre,
            apellido="Sistema",
            hashed_password=get_password_hash(password),
            es_admin=True,
            esta_activo=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Usuario administrador creado exitosamente")
        print(f"   📧 Email: {email}")
        print(f"   👤 Nombre: {nombre}")
        print(f"   🆔 ID: {admin_user.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando usuario administrador: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    
    finally:
        if 'db' in locals():
            db.close()


def ensure_admin_exists():
    """Asegurar que existe al menos un usuario administrador"""
    
    try:
        db = SessionLocal()
        
        # Buscar usuarios administradores activos
        admin_count = db.query(Usuario).filter(
            Usuario.es_admin == True,
            Usuario.esta_activo == True
        ).count()
        
        if admin_count > 0:
            print(f"✅ Hay {admin_count} administrador(es) activo(s)")
            return True
        
        print("⚠️ No hay administradores activos")
        
        # En modo automático (para Docker), crear admin por defecto
        if settings.ENV == "production":
            # En producción, no crear admin automáticamente
            print("❌ En producción debes crear un administrador manualmente")
            return False
        
        # En desarrollo, crear admin por defecto
        default_email = "admin@gymnasium.com"
        default_password = "admin123"
        default_name = "Administrador del Sistema"
        
        print(f"🔧 Creando administrador por defecto para desarrollo:")
        print(f"   📧 Email: {default_email}")
        print(f"   🔐 Contraseña: {default_password}")
        
        return create_admin(default_email, default_password, default_name)
        
    except Exception as e:
        print(f"❌ Error verificando administradores: {e}")
        return False
    
    finally:
        if 'db' in locals():
            db.close()


def list_admins():
    """Listar usuarios administradores"""
    
    try:
        db = SessionLocal()
        
        admins = db.query(Usuario).filter(Usuario.is_admin == True).all()
        
        if not admins:
            print("📭 No hay usuarios administradores")
            return
        
        print(f"👥 Usuarios Administradores ({len(admins)}):")
        print("-" * 60)
        
        for admin in admins:
            status = "🟢 Activo" if admin.is_active else "🔴 Inactivo"
            created = admin.created_at.strftime("%Y-%m-%d %H:%M") if admin.created_at else "N/A"
            
            print(f"🆔 {admin.id:3d} | 📧 {admin.email:30s} | {status}")
            print(f"      👤 {admin.nombre or 'Sin nombre':30s} | 📅 {created}")
            print()
        
    except Exception as e:
        print(f"❌ Error listando administradores: {e}")
    
    finally:
        if 'db' in locals():
            db.close()


def main():
    """Función principal"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            list_admins()
            return
        
        elif command == "ensure":
            ensure_admin_exists()
            return
        
        elif command == "help":
            print("🏋️‍♂️ Sistema de Gimnasio v6 - Gestión de Administradores")
            print()
            print("USO:")
            print("  python create_admin.py [comando]")
            print()
            print("COMANDOS:")
            print("  (ninguno)  - Crear nuevo administrador interactivamente")
            print("  list       - Listar administradores existentes")
            print("  ensure     - Asegurar que existe al menos un admin")
            print("  help       - Mostrar esta ayuda")
            return
    
    # Modo interactivo por defecto
    try:
        success = create_admin()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 