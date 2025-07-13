#!/usr/bin/env python3
"""
Script para generar claves secretas seguras para producción
Sistema de Gestión de Gimnasio v6.0
"""
import secrets
import string
import argparse
import json
from pathlib import Path

def generate_secure_password(length=32):
    """Generar contraseña segura con caracteres especiales"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    # Asegurar que tenga al menos un carácter de cada tipo
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?")
    ]
    # Completar el resto
    password.extend(secrets.choice(characters) for _ in range(length - 4))
    # Mezclar la contraseña
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    return ''.join(password_list)

def generate_secret_key(length=64):
    """Generar clave secreta segura"""
    return secrets.token_urlsafe(length)

def generate_redis_password(length=32):
    """Generar contraseña para Redis"""
    return generate_secure_password(length)

def generate_database_password(length=32):
    """Generar contraseña para base de datos"""
    return generate_secure_password(length)

def main():
    parser = argparse.ArgumentParser(description="Generar claves secretas seguras para producción")
    parser.add_argument("--output", "-o", help="Archivo de salida para las claves")
    parser.add_argument("--length", "-l", type=int, default=64, help="Longitud de las claves secretas")
    parser.add_argument("--password-length", "-p", type=int, default=32, help="Longitud de las contraseñas")
    
    args = parser.parse_args()
    
    print("🔐 Generando claves secretas seguras para producción...")
    print("=" * 60)
    
    # Generar todas las claves
    keys = {
        "GYM_SECRET_KEY": generate_secret_key(args.length),
        "GYM_JWT_SECRET_KEY": generate_secret_key(args.length),
        "GYM_BACKUP_KEY": generate_secret_key(args.length // 2),
        "GYM_DB_PASSWORD": generate_database_password(args.password_length),
        "GYM_REDIS_PASSWORD": generate_redis_password(args.password_length),
        "GRAFANA_PASSWORD": generate_secure_password(args.password_length),
        "PROMETHEUS_PASSWORD": generate_secure_password(args.password_length)
    }
    
    # Mostrar las claves generadas
    for key, value in keys.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ Claves generadas exitosamente")
    print("\n📝 INSTRUCCIONES:")
    print("1. Copia estas claves a tu archivo de configuración de producción")
    print("2. NUNCA compartas estas claves o las subas a control de versiones")
    print("3. Guarda estas claves en un lugar seguro (gestor de contraseñas)")
    print("4. Rota estas claves periódicamente (cada 90 días)")
    
    # Guardar en archivo si se especifica
    if args.output:
        output_path = Path(args.output)
        
        # Crear contenido del archivo
        env_content = "# Claves secretas generadas automáticamente\n"
        env_content += "# IMPORTANTE: No subir este archivo a control de versiones\n"
        env_content += "# Fecha de generación: " + str(Path().cwd()) + "\n\n"
        
        for key, value in keys.items():
            env_content += f"{key}={value}\n"
        
        # Escribir archivo
        output_path.write_text(env_content, encoding='utf-8')
        print(f"\n💾 Claves guardadas en: {output_path}")
        print(f"🔒 Asegúrate de que el archivo tenga permisos restrictivos (600)")
        
        # También generar archivo JSON para uso programático
        json_path = output_path.with_suffix('.json')
        json_content = {
            "generated_at": str(Path().cwd()),
            "environment": "production",
            "keys": keys
        }
        json_path.write_text(json.dumps(json_content, indent=2), encoding='utf-8')
        print(f"📄 Archivo JSON generado: {json_path}")
    
    print("\n⚠️  ADVERTENCIAS DE SEGURIDAD:")
    print("- Estas claves son para PRODUCCIÓN únicamente")
    print("- No uses estas claves en desarrollo o testing")
    print("- Cambia las claves si sospechas que han sido comprometidas")
    print("- Usa un gestor de secretos en producción (HashiCorp Vault, AWS Secrets Manager, etc.)")

if __name__ == "__main__":
    main() 