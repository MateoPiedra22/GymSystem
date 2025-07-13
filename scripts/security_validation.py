#!/usr/bin/env python3
"""
Script de validación de seguridad para el sistema de gimnasio
Sistema de Gestión de Gimnasio v6.0
"""
import os
import re
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

class SecurityValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.project_root = Path(__file__).parent.parent

    def validate_environment_files(self):
        """Validar archivos de configuración de entorno"""
        print("🔍 Validando archivos de configuración...")
        
        env_files = [
            "config/env/production.env",
            "config/env/security.env",
            "config/env/database.env"
        ]
        
        for env_file in env_files:
            file_path = self.project_root / env_file
            if not file_path.exists():
                self.warnings.append(f"Archivo de configuración no encontrado: {env_file}")
                continue
                
            self.validate_env_file(file_path)
    
    def validate_env_file(self, file_path: Path):
        """Validar un archivo de configuración específico"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Verificar claves secretas inseguras
            insecure_patterns = [
                r'CHANGE_THIS_TO_SECURE',
                r'your_secret_key_here',
                r'your_jwt_secret_key_here',
                r'your_backup_key_here',
                r'password123',
                r'admin123',
                r'changeme',
                r'default',
                r'localhost',
                r'127\.0\.0\.1'
            ]
            
            for pattern in insecure_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.errors.append(f"Valores inseguros detectados en {file_path.name}: {pattern}")
            
            # Verificar configuración de producción
            if 'production.env' in str(file_path):
                if 'GYM_FORCE_HTTPS=false' in content:
                    self.errors.append(f"HTTPS deshabilitado en producción: {file_path.name}")
                
                if 'localhost' in content or '127.0.0.1' in content:
                    self.warnings.append(f"Localhost detectado en configuración de producción: {file_path.name}")
                
                if 'GYM_SECURE_COOKIES=false' in content:
                    self.errors.append(f"Cookies inseguras en producción: {file_path.name}")
                
                if 'GYM_SAMESITE_COOKIES=lax' in content:
                    self.warnings.append(f"SameSite cookies configurado como 'lax' en producción: {file_path.name}")
                
                if 'GYM_RATE_LIMIT=200' in content:
                    self.warnings.append(f"Rate limit muy alto para producción: {file_path.name}")
                
                if 'GYM_MAX_LOGIN_ATTEMPTS=10' in content:
                    self.warnings.append(f"Demasiados intentos de login permitidos en producción: {file_path.name}")
        
        except Exception as e:
            self.errors.append(f"Error validando {file_path}: {str(e)}")
    
    def validate_docker_configuration(self):
        """Validar configuración de Docker"""
        print("🐳 Validando configuración de Docker...")
        
        docker_files = [
            "docker-compose.yml",
            "backend/Dockerfile",
            "web/Dockerfile"
        ]
        
        for docker_file in docker_files:
            file_path = self.project_root / docker_file
            if not file_path.exists():
                self.warnings.append(f"Archivo Docker no encontrado: {docker_file}")
                continue
                
            self.validate_docker_file(file_path)
    
    def validate_docker_file(self, file_path: Path):
        """Validar un archivo Docker específico"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Verificar configuración de seguridad
            if 'Dockerfile' in str(file_path):
                if 'USER root' in content and 'USER gymapp' not in content:
                    self.warnings.append(f"Usuario root detectado en {file_path.name}")
                
                if 'RUN chmod 777' in content:
                    self.errors.append(f"Permisos inseguros detectados en {file_path.name}")
                
                if 'EXPOSE' in content and '127.0.0.1' not in content:
                    self.warnings.append(f"Puertos expuestos sin restricción en {file_path.name}")
            
            # Verificar docker-compose
            if 'docker-compose.yml' in str(file_path):
                if 'ports:' in content and '127.0.0.1:' not in content:
                    self.warnings.append(f"Puertos expuestos sin restricción en {file_path.name}")
                
                if 'security_opt:' not in content:
                    self.warnings.append(f"Opciones de seguridad no configuradas en {file_path.name}")
                
                if 'read_only: true' not in content:
                    self.warnings.append(f"Contenedores no configurados como read-only en {file_path.name}")
        
        except Exception as e:
            self.errors.append(f"Error validando {file_path}: {str(e)}")
    
    def validate_backend_security(self):
        """Validar seguridad del backend"""
        print("🔧 Validando seguridad del backend...")
        
        backend_files = [
            "backend/app/main.py",
            "backend/app/core/config/security.py",
            "backend/app/core/config/database.py"
        ]
        
        for backend_file in backend_files:
            file_path = self.project_root / backend_file
            if not file_path.exists():
                self.warnings.append(f"Archivo backend no encontrado: {backend_file}")
                continue
                
            self.validate_backend_file(file_path)
    
    def validate_backend_file(self, file_path: Path):
        """Validar un archivo del backend específico"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Verificar logging de información sensible
            sensitive_patterns = [
                r'logger\.(info|debug|error).*password',
                r'logger\.(info|debug|error).*secret',
                r'logger\.(info|debug|error).*key',
                r'print.*password',
                r'print.*secret',
                r'print.*key'
            ]
            
            for pattern in sensitive_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.warnings.append(f"Posible logging de información sensible en {file_path.name}")
            
            # Verificar manejo de errores
            if 'except Exception as e:' in content and 'logger.error' not in content:
                self.warnings.append(f"Manejo de errores genérico detectado en {file_path.name}")
            
            # Verificar validaciones de entrada
            if 'request' in content and 'validation' not in content:
                self.warnings.append(f"Posible falta de validación de entrada en {file_path.name}")
        
        except Exception as e:
            self.errors.append(f"Error validando {file_path}: {str(e)}")
    
    def validate_frontend_security(self):
        """Validar seguridad del frontend"""
        print("🌐 Validando seguridad del frontend...")
        
        frontend_files = [
            "web/app/utils/api.ts",
            "web/next.config.js",
            "web/package.json"
        ]
        
        for frontend_file in frontend_files:
            file_path = self.project_root / frontend_file
            if not file_path.exists():
                self.warnings.append(f"Archivo frontend no encontrado: {frontend_file}")
                continue
                
            self.validate_frontend_file(file_path)
    
    def validate_frontend_file(self, file_path: Path):
        """Validar un archivo del frontend específico"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Verificar configuración de seguridad
            if 'next.config.js' in str(file_path):
                if 'X-Frame-Options' not in content:
                    self.warnings.append(f"Headers de seguridad no configurados en {file_path.name}")
                
                if 'localhost' in content:
                    self.warnings.append(f"Localhost detectado en configuración de producción: {file_path.name}")
            
            # Verificar dependencias inseguras
            if 'package.json' in str(file_path):
                try:
                    package_data = json.loads(content)
                    dependencies = package_data.get('dependencies', {})
                    
                    # Verificar versiones conocidas como inseguras
                    insecure_versions = {
                        'axios': '<1.6.0',
                        'react': '<18.0.0',
                        'next': '<14.0.0'
                    }
                    
                    for dep, min_version in insecure_versions.items():
                        if dep in dependencies:
                            version = dependencies[dep]
                            if version.startswith('<'):
                                self.warnings.append(f"Versión potencialmente insegura de {dep}: {version}")
                
                except json.JSONDecodeError:
                    self.errors.append(f"Error parseando {file_path.name}")
        
        except Exception as e:
            self.errors.append(f"Error validando {file_path}: {str(e)}")
    
    def validate_nginx_configuration(self):
        """Validar configuración de Nginx"""
        print("🔒 Validando configuración de Nginx...")
        
        nginx_files = [
            "nginx/conf.d/security.conf",
            "nginx/nginx.conf"
        ]
        
        for nginx_file in nginx_files:
            file_path = self.project_root / nginx_file
            if not file_path.exists():
                self.warnings.append(f"Archivo Nginx no encontrado: {nginx_file}")
                continue
                
            self.validate_nginx_file(file_path)
    
    def validate_nginx_file(self, file_path: Path):
        """Validar un archivo de Nginx específico"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Verificar headers de seguridad
            security_headers = [
                'X-Frame-Options',
                'X-Content-Type-Options',
                'X-XSS-Protection',
                'Strict-Transport-Security',
                'Content-Security-Policy'
            ]
            
            for header in security_headers:
                if header not in content:
                    self.warnings.append(f"Header de seguridad faltante en {file_path.name}: {header}")
            
            # Verificar configuración SSL
            if 'ssl_protocols' not in content:
                self.warnings.append(f"Configuración SSL no encontrada en {file_path.name}")
            
            # Verificar rate limiting
            if 'limit_req_zone' not in content:
                self.warnings.append(f"Rate limiting no configurado en {file_path.name}")
            
            # Verificar ocultación de versión
            if 'server_tokens off' not in content:
                self.warnings.append(f"Versión de Nginx no oculta en {file_path.name}")
        
        except Exception as e:
            self.errors.append(f"Error validando {file_path}: {str(e)}")
    
    def run_security_tests(self):
        """Ejecutar tests de seguridad"""
        print("🧪 Ejecutando tests de seguridad...")
        
        # Verificar si hay tests de seguridad
        test_files = [
            "backend/tests/security/",
            "web/tests/"
        ]
        
        for test_path in test_files:
            path = self.project_root / test_path
            if path.exists():
                self.info.append(f"Tests de seguridad encontrados en: {test_path}")
            else:
                self.warnings.append(f"Tests de seguridad no encontrados en: {test_path}")
    
    def generate_report(self):
        """Generar reporte de seguridad"""
        print("\n" + "="*60)
        print("📊 REPORTE DE VALIDACIÓN DE SEGURIDAD")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ ERRORES CRÍTICOS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.info:
            print(f"\nℹ️  INFORMACIÓN ({len(self.info)}):")
            for info in self.info:
                print(f"  • {info}")
        
        print(f"\n📈 RESUMEN:")
        print(f"  • Errores críticos: {len(self.errors)}")
        print(f"  • Advertencias: {len(self.warnings)}")
        print(f"  • Información: {len(self.info)}")
        
        if not self.errors and not self.warnings:
            print("\n✅ ¡Excelente! No se encontraron problemas de seguridad críticos.")
        elif not self.errors:
            print("\n⚠️  Se encontraron advertencias menores. Revisa las recomendaciones.")
        else:
            print("\n❌ Se encontraron errores críticos. Corrige estos problemas antes de desplegar.")
        
        return len(self.errors) == 0

def main():
    validator = SecurityValidator()
    
    print("🔐 Iniciando validación de seguridad del sistema...")
    print("="*60)
    
    # Ejecutar todas las validaciones
    validator.validate_environment_files()
    validator.validate_docker_configuration()
    validator.validate_backend_security()
    validator.validate_frontend_security()
    validator.validate_nginx_configuration()
    validator.run_security_tests()
    
    # Generar reporte
    success = validator.generate_report()
    
    # Retornar código de salida apropiado
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 