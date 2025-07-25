#!/usr/bin/env python3
"""
Script de verificación final para GymSystem v6
Verifica que el sistema esté listo para producción
"""

import os
import json

def check_file_exists(file_path, description):
    """Verifica que un archivo exista"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NO ENCONTRADO")
        return False

def check_env_file(file_path, required_vars):
    """Verifica variables de entorno en un archivo"""
    if not os.path.exists(file_path):
        print(f"❌ Archivo de entorno no encontrado: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables faltantes en {file_path}: {', '.join(missing_vars)}")
        return False
    else:
        print(f"✅ Variables de entorno correctas en {file_path}")
        return True

def main():
    """Función principal de verificación"""
    print("🔍 Verificación final - GymSystem v6 listo para producción\n")
    
    all_checks_passed = True
    
    # Verificar archivos críticos
    print("📁 Verificando archivos críticos...")
    critical_files = [
        ('backend/app/main.py', 'Backend principal'),
        ('backend/requirements.txt', 'Dependencias backend'),
        ('frontend/package.json', 'Package.json frontend'),
        ('frontend/.env.production', 'Variables de entorno producción'),
        ('vercel.json', 'Configuración Vercel'),
        ('railway.toml', 'Configuración Railway'),
        ('DEPLOYMENT_GUIDE.md', 'Guía de despliegue'),
    ]
    
    for file_path, description in critical_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    print("\n🔧 Verificando configuraciones críticas...")
    
    # Verificar variables de entorno del frontend
    frontend_env_vars = [
        'VITE_API_URL=https://gym-system-v6-production.up.railway.app',
        'NODE_ENV=production'
    ]
    
    if os.path.exists('frontend/.env.production'):
        with open('frontend/.env.production', 'r') as f:
            env_content = f.read()
        
        missing_configs = []
        for config in frontend_env_vars:
            if config not in env_content:
                missing_configs.append(config)
        
        if missing_configs:
            print(f"❌ Configuraciones faltantes en .env.production: {missing_configs}")
            all_checks_passed = False
        else:
            print("✅ Configuración de producción del frontend correcta")
    
    # Verificar configuración de Railway
    if os.path.exists('railway.toml'):
        with open('railway.toml', 'r') as f:
            railway_content = f.read()
        
        if 'https://gym-system-v6-frontend.vercel.app' in railway_content:
            print("✅ URL del frontend configurada en Railway")
        else:
            print("❌ URL del frontend no configurada en Railway")
            all_checks_passed = False
    
    # Verificar que el directorio dist existe (frontend compilado)
    if os.path.exists('frontend/dist'):
        print("✅ Frontend compilado (directorio dist existe)")
    else:
        print("❌ Frontend no compilado (ejecutar: cd frontend && pnpm run build)")
        all_checks_passed = False
    
    print("\n" + "="*60)
    
    if all_checks_passed:
        print("🎉 ¡SISTEMA LISTO PARA PRODUCCIÓN!")
        print("\n📋 Pasos finales para despliegue:")
        print("\n1️⃣ Commit y push al repositorio:")
        print("   git add .")
        print("   git commit -m 'feat: Sistema listo para producción'")
        print("   git push origin main")
        print("\n2️⃣ Desplegar en Railway (Backend):")
        print("   - Conectar repositorio en railway.app")
        print("   - Configurar variables de entorno")
        print("   - Desplegar automáticamente")
        print("\n3️⃣ Desplegar en Vercel (Frontend):")
        print("   - Conectar repositorio en vercel.com")
        print("   - Configurar variables de entorno")
        print("   - Desplegar automáticamente")
        print("\n📖 Ver DEPLOYMENT_GUIDE.md para instrucciones detalladas")
        return 0
    else:
        print("❌ CORRECCIONES NECESARIAS")
        print("🔧 Revisar los errores antes de desplegar")
        return 1

if __name__ == "__main__":
    exit(main())