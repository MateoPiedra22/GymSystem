#!/usr/bin/env python3
"""
Script simple para crear usuario administrador
"""

import sys
import os
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.usuarios import Usuario
from app.core.auth import get_password_hash
import uuid
from datetime import datetime

def create_admin():
    """Crear usuario administrador"""
    
    print("🏋️‍♂️ Creando usuario administrador...")
    
    # Datos del admin
    email = "admin@gymnasium.com"
    username = "gym_admin"
    password = "admin123"
    nombre = "Administrador"
    apellido = "Sistema"
    
    # Conectar a la base de datos
    try:
        db = SessionLocal()
        
        # Verificar si ya existe un usuario con ese email
        existing_user = db.query(Usuario).filter(Usuario.email == email).first()
        if existing_user:
            print(f"⚠️ Ya existe un usuario con el email {email}")
            return False
        
        # Crear nuevo usuario administrador
        admin_user = Usuario(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            nombre=nombre,
            apellido=apellido,
            hashed_password=get_password_hash(password),
            es_admin=True,
            esta_activo=True,
            fecha_registro=datetime.utcnow(),
            fecha_inicio=datetime.utcnow(),
            ultima_modificacion=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Usuario administrador creado exitosamente")
        print(f"   📧 Email: {email}")
        print(f"   👤 Username: {username}")
        print(f"   🔐 Contraseña: {password}")
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

if __name__ == "__main__":
    create_admin() 