#!/usr/bin/env python3
"""
Config Manager - Sistema de Gestión de Gimnasio v6
Herramienta para gestionar y validar configuraciones del sistema
"""

import os
import sys
import argparse
import secrets
import string
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
import json

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

class ConfigManager:
    """Gestor de configuraciones del sistema"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.environments = ['development', 'staging', 'production']
        
    def generate_secure_key(self, length: int = 64) -> str:
        """Genera una clave segura aleatoria"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_password(self, length: int = 24) -> str:
        """Genera una contraseña segura"""
        # Asegurar al menos un carácter de cada tipo
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*"
        
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Completar con caracteres aleatorios
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Mezclar la contraseña
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    def validate_config_file(self, config_path: Path) -> List[str]:
        """Valida un archivo de configuración"""
        issues = []
        
        if not config_path.exists():
            issues.append(f"Archivo no encontrado: {config_path}")
            return issues
        
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                
            # Buscar valores inseguros
            insecure_patterns = [
                'CAMBIAR_',
                'GENERAR_',
                'changeme',
                'password123',
                'admin123',
                'secret123'
            ]
            
            for pattern in insecure_patterns:
                if pattern in content:
                    issues.append(f"Valor inseguro encontrado: {pattern}")
            
            # Verificar claves vacías
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    if not value.strip():
                        issues.append(f"Línea {i}: Valor vacío para {key}")
                        
        except Exception as e:
            issues.append(f"Error leyendo archivo: {e}")
            
        return issues
    
    def create_env_file(self, environment: str, force: bool = False) -> bool:
        """Crea un archivo .env para el entorno especificado"""
        
        if environment not in self.environments:
            print(f"❌ Entorno inválido: {environment}")
            return False
        
        # Rutas de archivos
        template_path = self.project_root / f".env.{environment}.example"
        target_path = self.project_root / f".env.{environment}"
        
        if not template_path.exists():
            print(f"❌ Template no encontrado: {template_path}")
            return False
            
        if target_path.exists() and not force:
            print(f"⚠️  El archivo {target_path} ya existe. Usa --force para sobrescribir.")
            return False
        
        try:
            # Leer template
            with open(template_path, 'r') as f:
                content = f.read()
            
            # Generar valores seguros automáticamente
            replacements = {
                'CAMBIAR_': '',
                'GENERAR_': ''
            }
            
            # Reemplazar patrones comunes
            if 'CAMBIAR_' in content or 'GENERAR_' in content:
                # Generar claves secretas
                content = content.replace(
                    'CAMBIAR_staging_secret_key_64_chars_hex', 
                    self.generate_secure_key()
                )
                content = content.replace(
                    'CAMBIAR_staging_jwt_key_64_chars_hex', 
                    self.generate_secure_key()
                )
                content = content.replace(
                    'CAMBIAR_staging_backup_key_64_chars_hex', 
                    self.generate_secure_key()
                )
                
                # Generar contraseñas
                content = content.replace(
                    'CAMBIAR_staging_db_password_segura', 
                    self.generate_password()
                )
                content = content.replace(
                    'CAMBIAR_staging_redis_password', 
                    self.generate_password()
                )
                content = content.replace(
                    'CAMBIAR_admin_staging_password_compleja', 
                    self.generate_password()
                )
                content = content.replace(
                    'CAMBIAR_pgadmin_staging_password', 
                    self.generate_password()
                )
                content = content.replace(
                    'CAMBIAR_grafana_staging_password', 
                    self.generate_password()
                )
            
            # Escribir archivo
            with open(target_path, 'w') as f:
                f.write(content)
                
            print(f"✅ Archivo creado: {target_path}")
            
            # Validar el archivo creado
            issues = self.validate_config_file(target_path)
            if issues:
                print("⚠️  Advertencias en el archivo generado:")
                for issue in issues:
                    print(f"   - {issue}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creando archivo: {e}")
            return False
    
    def validate_all_configs(self) -> Dict[str, List[str]]:
        """Valida todas las configuraciones del sistema"""
        
        results = {}
        
        # Archivos de configuración a validar
        config_files = [
            self.project_root / ".env.development",
            self.project_root / ".env.staging", 
            self.project_root / ".env.production",
            self.project_root / "backend" / ".env",
            self.project_root / "web" / ".env.local",
            self.project_root / "docker-compose.yml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                results[str(config_file)] = self.validate_config_file(config_file)
            else:
                results[str(config_file)] = [f"Archivo no encontrado"]
        
        return results
    
    def setup_development_environment(self) -> bool:
        """Configura el entorno de desarrollo completo"""
        
        print("🔧 Configurando entorno de desarrollo...")
        
        steps = [
            ("Creando .env.development", lambda: self.create_env_file('development', force=True)),
            ("Creando backend/.env", self._setup_backend_env),
            ("Creando web/.env.local", self._setup_frontend_env),
            ("Verificando directorios", self._create_directories),
            ("Validando configuraciones", self._validate_development_setup)
        ]
        
        for step_name, step_func in steps:
            print(f"   {step_name}...")
            try:
                if not step_func():
                    print(f"❌ Error en: {step_name}")
                    return False
                print(f"   ✅ {step_name} completado")
            except Exception as e:
                print(f"❌ Error en {step_name}: {e}")
                return False
        
        print("🎉 Entorno de desarrollo configurado exitosamente!")
        print("\n📋 Próximos pasos:")
        print("   1. Revisar y ajustar las configuraciones generadas")
        print("   2. Ejecutar: docker-compose --env-file .env.development up")
        print("   3. O para desarrollo local: cd backend && python start_server.py")
        
        return True
    
    def _setup_backend_env(self) -> bool:
        """Configura el archivo .env del backend"""
        backend_env = self.project_root / "backend" / ".env"
        backend_example = self.project_root / "backend" / ".env.example"
        
        if backend_example.exists():
            with open(backend_example, 'r') as f:
                content = f.read()
            
            # Generar valores seguros para desarrollo
            content = content.replace(
                'dev_clave_secreta_para_desarrollo_cambiar_en_produccion',
                f"dev_{self.generate_secure_key(32)}"
            )
            content = content.replace(
                'dev_jwt_key_para_desarrollo_cambiar_en_produccion',
                f"jwt_{self.generate_secure_key(32)}"
            )
            content = content.replace(
                'dev_backup_key_para_desarrollo_cambiar_en_produccion',
                f"backup_{self.generate_secure_key(32)}"
            )
            
            with open(backend_env, 'w') as f:
                f.write(content)
                
            return True
        return False
    
    def _setup_frontend_env(self) -> bool:
        """Configura el archivo .env.local del frontend"""
        frontend_env = self.project_root / "web" / ".env.local"
        frontend_example = self.project_root / "web" / ".env.example"
        
        if frontend_example.exists():
            with open(frontend_example, 'r') as f:
                content = f.read()
            
            with open(frontend_env, 'w') as f:
                f.write(content)
                
            return True
        return False
    
    def _create_directories(self) -> bool:
        """Crea directorios necesarios"""
        directories = [
            self.project_root / "logs",
            self.project_root / "uploads", 
            self.project_root / "backups",
            self.project_root / "data" / "postgres",
            self.project_root / "data" / "redis"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        return True
    
    def _validate_development_setup(self) -> bool:
        """Valida la configuración de desarrollo"""
        results = self.validate_all_configs()
        
        critical_issues = []
        for file_path, issues in results.items():
            for issue in issues:
                if any(critical in issue for critical in ['CAMBIAR_', 'GENERAR_', 'no encontrado']):
                    critical_issues.append(f"{file_path}: {issue}")
        
        if critical_issues:
            print("⚠️  Issues críticos encontrados:")
            for issue in critical_issues[:5]:  # Mostrar solo los primeros 5
                print(f"   - {issue}")
            return False
            
        return True
    
    def check_docker_dependencies(self) -> bool:
        """Verifica dependencias de Docker"""
        try:
            # Verificar Docker
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker no está instalado o no está en PATH")
                return False
            
            # Verificar Docker Compose
            result = subprocess.run(['docker', 'compose', 'version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker Compose no está disponible")
                return False
                
            print("✅ Docker y Docker Compose están disponibles")
            return True
            
        except FileNotFoundError:
            print("❌ Docker no está instalado")
            return False
    
    def generate_security_report(self) -> Dict:
        """Genera un reporte de seguridad"""
        report = {
            'timestamp': '',
            'environment_files': {},
            'security_issues': [],
            'recommendations': []
        }
        
        # Validar todos los archivos de configuración
        results = self.validate_all_configs()
        
        for file_path, issues in results.items():
            report['environment_files'][file_path] = {
                'exists': Path(file_path).exists(),
                'issues': issues,
                'secure': len(issues) == 0
            }
            
            # Agregar issues críticos al reporte
            for issue in issues:
                if any(critical in issue for critical in ['CAMBIAR_', 'GENERAR_', 'changeme']):
                    report['security_issues'].append(f"{file_path}: {issue}")
        
        # Generar recomendaciones
        if report['security_issues']:
            report['recommendations'].extend([
                "Reemplazar todos los valores marcados con CAMBIAR_ o GENERAR_",
                "Usar claves aleatorias de al menos 32 caracteres",
                "Configurar HTTPS en producción",
                "Revisar y restringir CORS_ORIGINS",
                "Habilitar todas las medidas de seguridad en producción"
            ])
        
        return report

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Gestor de configuraciones del sistema')
    parser.add_argument('action', choices=[
        'init-dev', 'validate', 'create-env', 'security-report', 'check-docker'
    ], help='Acción a realizar')
    parser.add_argument('--env', choices=['development', 'staging', 'production'],
                       help='Entorno para crear archivo .env')
    parser.add_argument('--force', action='store_true',
                       help='Forzar sobrescritura de archivos existentes')
    
    args = parser.parse_args()
    
    config_manager = ConfigManager()
    
    if args.action == 'init-dev':
        success = config_manager.setup_development_environment()
        sys.exit(0 if success else 1)
        
    elif args.action == 'validate':
        print("🔍 Validando configuraciones...")
        results = config_manager.validate_all_configs()
        
        total_issues = 0
        for file_path, issues in results.items():
            if issues:
                print(f"\n📁 {file_path}:")
                for issue in issues:
                    print(f"   ⚠️  {issue}")
                    total_issues += 1
            else:
                print(f"✅ {file_path}: Sin issues")
        
        if total_issues == 0:
            print("\n🎉 Todas las configuraciones son válidas!")
        else:
            print(f"\n⚠️  Se encontraron {total_issues} issues")
            
        sys.exit(0 if total_issues == 0 else 1)
        
    elif args.action == 'create-env':
        if not args.env:
            print("❌ Especifica el entorno con --env")
            sys.exit(1)
            
        success = config_manager.create_env_file(args.env, args.force)
        sys.exit(0 if success else 1)
        
    elif args.action == 'security-report':
        print("🔐 Generando reporte de seguridad...")
        report = config_manager.generate_security_report()
        
        print(f"\n📊 Reporte de Seguridad")
        print("=" * 50)
        
        for file_path, info in report['environment_files'].items():
            status = "✅ SEGURO" if info['secure'] else "⚠️  REVISAR"
            print(f"{status} {file_path}")
        
        if report['security_issues']:
            print(f"\n⚠️  Issues de Seguridad ({len(report['security_issues'])}):")
            for issue in report['security_issues']:
                print(f"   - {issue}")
        
        if report['recommendations']:
            print(f"\n💡 Recomendaciones:")
            for rec in report['recommendations']:
                print(f"   - {rec}")
                
        # Guardar reporte en archivo
        report_file = Path('security_report.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Reporte guardado en: {report_file}")
        
    elif args.action == 'check-docker':
        success = config_manager.check_docker_dependencies()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 