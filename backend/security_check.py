#!/usr/bin/env python3
"""
Script de verificación de seguridad para el sistema de gimnasio
Verifica configuraciones de seguridad, dependencias y configuración
"""

import os
import sys
import subprocess
import importlib.util
import json
import secrets
import ssl
import socket
# import requests  # Comentado para evitar dependencias externas
import hashlib
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path
from urllib.parse import urlparse

# Agregar el directorio del backend al path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.core.config import settings
    from app.core.security import SecurityValidator, SecurityConfig
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

class EnvironmentChecker:
    """Verificador de configuración de ambiente"""
    
    def __init__(self, settings):
        self.settings = settings
        self.issues = []
        self.warnings = []
        self.info = []
    
    def check_environment_config(self):
        """Verifica configuración de ambiente"""
        print("📋 Verificando configuración de ambiente...")
        
        # Verificar ambiente de producción
        if self.settings.ENV == "production":
            self.info.append("✅ Ambiente configurado como producción")
            
            # Verificar SECRET_KEY en producción
            secret_key = os.environ.get("GYM_SECRET_KEY")
            placeholder_key = "CAMBIAR_ESTA_CLAVE_SECRETA_ULTRA_SEGURA_DE_32_CARACTERES_MINIMO"
            if not secret_key or secret_key == placeholder_key:
                self.issues.append("❌ SECRET_KEY no configurada o usa valor por defecto en producción")
            elif len(secret_key) < 32:
                self.issues.append("❌ SECRET_KEY demasiado corto para producción (mínimo 32 caracteres)")
            else:
                self.info.append("✅ SECRET_KEY configurado apropiadamente")
        else:
            self.warnings.append("⚠️ Ambiente no configurado como producción")
        
        # Verificar DEBUG en producción
        if self.settings.ENV == "production" and self.settings.DEBUG:
            self.issues.append("❌ DEBUG activado en producción")
        else:
            self.info.append("✅ DEBUG apropiadamente configurado")
        
        # Verificar HTTPS
        if self.settings.ENV == "production" and not self.settings.FORCE_HTTPS:
            self.warnings.append("⚠️ HTTPS no forzado en producción")
        
        # Verificar variables críticas
        critical_vars = [
            "GYM_SECRET_KEY",
            "POSTGRES_PASSWORD",
            "REDIS_PASSWORD"
        ]
        
        for var in critical_vars:
            if not os.environ.get(var):
                self.warnings.append(f"⚠️ Variable crítica no configurada: {var}")
            else:
                self.info.append(f"✅ Variable crítica configurada: {var}")

class SecurityConfigChecker:
    """Verificador de configuración de seguridad"""
    
    def __init__(self, settings):
        self.settings = settings
        self.issues = []
        self.warnings = []
        self.info = []
    
    def check_security_config(self):
        """Verifica configuración específica de seguridad"""
        print("🔒 Verificando configuración de seguridad...")
        
        # Verificar headers de seguridad
        if self.settings.ENABLE_SECURITY_HEADERS:
            self.info.append("✅ Headers de seguridad habilitados")
        else:
            self.warnings.append("⚠️ Headers de seguridad deshabilitados")
        
        # Verificar validación de entrada
        if self.settings.ENABLE_INPUT_VALIDATION:
            self.info.append("✅ Validación de entrada habilitada")
        else:
            self.warnings.append("⚠️ Validación de entrada deshabilitada")
        
        # Verificar detección de ataques
        if self.settings.ENABLE_ATTACK_DETECTION:
            self.info.append("✅ Detección de ataques habilitada")
        else:
            self.warnings.append("⚠️ Detección de ataques deshabilitada")
        
        # Verificar configuración de tokens
        if self.settings.ACCESS_TOKEN_EXPIRE_MINUTES > 1440:  # 24 horas
            self.warnings.append("⚠️ Tiempo de expiración de tokens muy largo")
        
        # Verificar rate limiting
        if self.settings.RATE_LIMIT_PER_MINUTE < 60:
            self.info.append("✅ Rate limiting configurado apropiadamente")
        else:
            self.warnings.append("⚠️ Rate limiting muy permisivo")
        
        # Verificar algoritmos de hash
        if hasattr(self.settings, 'PASSWORD_HASH_ALGORITHM'):
            hash_algo = getattr(self.settings, 'PASSWORD_HASH_ALGORITHM', '')
            if hash_algo in ['md5', 'sha1']:
                self.issues.append("❌ Algoritmo de hash inseguro configurado")
            else:
                self.info.append("✅ Algoritmo de hash seguro configurado")

class DatabaseConfigChecker:
    """Verificador de configuración de base de datos"""
    
    def __init__(self, settings):
        self.settings = settings
        self.issues = []
        self.warnings = []
        self.info = []
    
    def check_database_config(self):
        """Verifica configuración de base de datos"""
        print("🗄️ Verificando configuración de base de datos...")
        
        if self.settings.ENV == "production":
            # Verificar que no use contraseñas por defecto en producción
            default_passwords = ["password", "123456", "admin", "gympass123"]
            postgres_password = getattr(self.settings, 'POSTGRES_PASSWORD', '')
            if postgres_password in default_passwords:
                self.issues.append("❌ Contraseña de base de datos usa valor por defecto en producción")
            else:
                self.info.append("✅ Contraseña de base de datos segura configurada para producción")
        
            # Verificar configuración SSL para producción
            if self.settings.DATABASE_URI and "sslmode=require" not in str(self.settings.DATABASE_URI):
                self.warnings.append("⚠️ SSL no requerido para conexión de BD en producción")
        else:
            self.info.append("✅ Verificación de contraseña de BD omitida en entorno de no producción")
        
        # Verificar configuración de pool de conexiones
        if hasattr(self.settings, 'DB_POOL_SIZE'):
            if self.settings.DB_POOL_SIZE > 20:
                self.warnings.append("⚠️ Pool de conexiones muy grande puede causar problemas")
            elif self.settings.DB_POOL_SIZE < 5:
                self.warnings.append("⚠️ Pool de conexiones muy pequeño para producción")
            else:
                self.info.append("✅ Pool de conexiones configurado apropiadamente")

class NetworkSecurityChecker:
    """Verificador de seguridad de red"""
    
    def __init__(self, settings):
        self.settings = settings
        self.issues = []
        self.warnings = []
        self.info = []
    
    def check_cors_config(self):
        """Verifica configuración CORS"""
        print("🌐 Verificando configuración CORS...")
        
        allowed_origins = self.settings.ALLOWED_ORIGINS
        
        if self.settings.ENV == "production":
            # En producción no debe permitir wildcard
            if "*" in allowed_origins:
                self.issues.append("❌ CORS permitiendo todos los orígenes en producción")
            
            # Verificar que use HTTPS
            http_origins = [origin for origin in allowed_origins if origin.startswith("http://")]
            if http_origins:
                self.warnings.append(f"⚠️ Orígenes HTTP en producción: {http_origins}")
            
            # Verificar que tenga dominios específicos
            if not allowed_origins or len(allowed_origins) == 0:
                self.issues.append("❌ No hay orígenes CORS configurados en producción")
            else:
                self.info.append("✅ CORS configurado apropiadamente para producción")
        else:
            self.info.append("✅ Verificación CORS omitida en entorno de no producción")
    
    def check_network_security(self):
        """Verifica configuración de seguridad de red"""
        print("🌐 Verificando seguridad de red...")
        
        # Verificar puertos abiertos
        critical_ports = [22, 80, 443, 5432, 6379]
        for port in critical_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    if port in [5432, 6379] and self.settings.ENV == "production":
                        self.warnings.append(f"⚠️ Puerto {port} abierto en producción")
                    else:
                        self.info.append(f"✅ Puerto {port} accesible")
                else:
                    if port in [80, 443]:
                        self.warnings.append(f"⚠️ Puerto {port} no accesible")
            except Exception as e:
                self.warnings.append(f"⚠️ Error verificando puerto {port}: {e}")
    
    def check_ssl_certificates(self):
        """Verifica certificados SSL"""
        print("🔐 Verificando certificados SSL...")
        
        if self.settings.ENV == "production":
            # Verificar certificados de dominio principal
            domain = getattr(self.settings, 'DOMAIN', 'localhost')
            if domain != 'localhost':
                self.check_domain_ssl_certificates(domain)
            else:
                self.warnings.append("⚠️ Dominio no configurado para verificación SSL")
        else:
            self.info.append("✅ Verificación SSL omitida en entorno de no producción")
    
    def check_domain_ssl_certificates(self, domain: str):
        """Verifica certificados SSL de dominios configurados"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Verificar fecha de expiración
                    import datetime
                    if cert and isinstance(cert, dict):
                        not_after_str = cert.get('notAfter')
                        if not_after_str and isinstance(not_after_str, str):
                            not_after = datetime.datetime.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z')
                            days_until_expiry = (not_after - datetime.datetime.now()).days
                        else:
                            days_until_expiry = 0
                    else:
                        days_until_expiry = 0
                    
                    if days_until_expiry < 30:
                        self.warnings.append(f"⚠️ Certificado SSL de {domain} expira en {days_until_expiry} días")
                    else:
                        self.info.append(f"✅ Certificado SSL de {domain} válido por {days_until_expiry} días")
                        
        except Exception as e:
            self.warnings.append(f"⚠️ Error verificando certificado SSL de {domain}: {e}")

class SecurityChecker:
    """Verificador de configuración de seguridad - Coordinador principal"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
        
        # Inicializar verificadores específicos
        self.env_checker = EnvironmentChecker(settings)
        self.security_checker = SecurityConfigChecker(settings)
        self.db_checker = DatabaseConfigChecker(settings)
        self.network_checker = NetworkSecurityChecker(settings)
        
    def check_all(self) -> Dict[str, Any]:
        """Ejecuta todas las verificaciones de seguridad"""
        print("🔍 Iniciando verificación de seguridad...\n")
        
        # Verificaciones de configuración
        self.env_checker.check_environment_config()
        self.security_checker.check_security_config()
        self.db_checker.check_database_config()
        self.network_checker.check_cors_config()
        
        # Verificaciones de dependencias
        self.check_dependencies()
        
        # Verificaciones de archivos y permisos
        self.check_file_permissions()
        self.check_sensitive_files()
        
        # Verificaciones de logs
        self.check_logging_config()
        
        # Verificaciones de red y SSL
        self.network_checker.check_network_security()
        self.network_checker.check_ssl_certificates()
        
        # Verificaciones avanzadas de seguridad
        self.check_advanced_security()
        self.check_code_quality()
        self.check_encryption_config()
        
        # Consolidar resultados
        self._consolidate_results()
        
        # Generar reporte
        return self.generate_report()
    
    def _consolidate_results(self):
        """Consolida resultados de todos los verificadores"""
        self.issues.extend(self.env_checker.issues)
        self.issues.extend(self.security_checker.issues)
        self.issues.extend(self.db_checker.issues)
        self.issues.extend(self.network_checker.issues)
        
        self.warnings.extend(self.env_checker.warnings)
        self.warnings.extend(self.security_checker.warnings)
        self.warnings.extend(self.db_checker.warnings)
        self.warnings.extend(self.network_checker.warnings)
        
        self.info.extend(self.env_checker.info)
        self.info.extend(self.security_checker.info)
        self.info.extend(self.db_checker.info)
        self.info.extend(self.network_checker.info)
    
    def check_dependencies(self):
        """Verifica dependencias de seguridad"""
        print("📦 Verificando dependencias de seguridad...")
        
        required_security_packages = [
            "bleach",
            "cryptography", 
            "passlib",
            "python-jose",
            "python-magic"
        ]
        
        for package in required_security_packages:
            try:
                __import__(package)
                self.info.append(f"✅ {package} instalado")
            except ImportError:
                self.warnings.append(f"⚠️ {package} no instalado")
        
        # Verificar versiones de dependencias críticas
        self.check_critical_dependency_versions()
    
    def check_critical_dependency_versions(self):
        """Verifica versiones de dependencias críticas"""
        critical_deps = {
            "cryptography": "3.0.0",
            "passlib": "1.7.0",
            "python-jose": "3.3.0"
        }
        
        for package, min_version in critical_deps.items():
            try:
                module = __import__(package)
                version = getattr(module, '__version__', '0.0.0')
                if self.compare_versions(version, min_version) < 0:
                    self.warnings.append(f"⚠️ {package} versión {version} es menor que {min_version}")
                else:
                    self.info.append(f"✅ {package} versión {version} es segura")
            except ImportError:
                self.warnings.append(f"⚠️ {package} no instalado")
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """Compara versiones semánticas"""
        def normalize(v):
            return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
        
        v1_norm = normalize(v1)
        v2_norm = normalize(v2)
        
        for i in range(max(len(v1_norm), len(v2_norm))):
            v1_part = v1_norm[i] if i < len(v1_norm) else 0
            v2_part = v2_norm[i] if i < len(v2_norm) else 0
            if v1_part > v2_part:
                return 1
            elif v1_part < v2_part:
                return -1
        return 0
    
    def check_file_permissions(self):
        """Verifica permisos de archivos críticos"""
        print("🔐 Verificando permisos de archivos...")
        
        critical_files = [
            "app/core/config.py",
            "app/core/auth.py",
            "app/core/security.py",
            ".env"
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                file_stat = os.stat(file_path)
                # Verificar que no sea world-readable (no termina en 4, 5, 6, 7)
                permissions = oct(file_stat.st_mode)[-1]
                if permissions in ["4", "5", "6", "7"]:
                    self.warnings.append(f"⚠️ {file_path} es legible por todos los usuarios")
                else:
                    self.info.append(f"✅ {file_path} tiene permisos apropiados")
            else:
                self.warnings.append(f"⚠️ Archivo crítico no encontrado: {file_path}")
    
    def check_sensitive_files(self):
        """Verifica existencia de archivos sensibles"""
        print("📄 Verificando archivos sensibles...")
        
        # Archivos que no deberían estar en producción
        sensitive_files = [
            ".env",
            "debug.log",
            "test.db",
            "*.key",
            "*.pem"
        ]
        
        if settings.ENV == "production":
            for pattern in sensitive_files:
                if "*" in pattern:
                    # Usar glob para patrones
                    import glob
                    matches = glob.glob(pattern)
                    if matches:
                        self.warnings.append(f"⚠️ Archivos sensibles encontrados: {matches}")
                else:
                    if os.path.exists(pattern):
                        self.warnings.append(f"⚠️ Archivo sensible en producción: {pattern}")
        
        # Verificar que existe directorio de logs
        if not os.path.exists("logs"):
            self.warnings.append("⚠️ Directorio de logs no existe")
        else:
            self.info.append("✅ Directorio de logs configurado")
    
    def check_logging_config(self):
        """Verifica configuración de logging"""
        print("📊 Verificando configuración de logging...")
        
        # Verificar nivel de log apropiado
        if settings.LOG_LEVEL == "DEBUG" and settings.ENV == "production":
            self.warnings.append("⚠️ Nivel de log DEBUG en producción")
        else:
            self.info.append("✅ Nivel de log apropiado")
        
        # Verificar que existe archivo de log
        log_dir = os.path.dirname(settings.LOG_FILE)
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
                self.info.append(f"✅ Directorio de logs creado: {log_dir}")
            except Exception as e:
                self.warnings.append(f"⚠️ No se pudo crear directorio de logs: {e}")
    
    def check_advanced_security(self):
        """Verificaciones avanzadas de seguridad"""
        print("🛡️ Verificaciones avanzadas de seguridad...")
        
        # Verificar configuración de sesiones
        if hasattr(settings, 'SESSION_COOKIE_SECURE'):
            session_secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
            if not session_secure and settings.ENV == "production":
                self.warnings.append("⚠️ Cookies de sesión no seguras en producción")
            else:
                self.info.append("✅ Cookies de sesión configuradas apropiadamente")
        
        # Verificar configuración de CSRF
        if hasattr(settings, 'CSRF_ENABLED'):
            csrf_enabled = getattr(settings, 'CSRF_ENABLED', False)
            if not csrf_enabled:
                self.warnings.append("⚠️ Protección CSRF deshabilitada")
            else:
                self.info.append("✅ Protección CSRF habilitada")
        
        # Verificar configuración de rate limiting avanzado
        if hasattr(settings, 'RATE_LIMIT_BURST'):
            rate_burst = getattr(settings, 'RATE_LIMIT_BURST', 0)
            if rate_burst > 100:
                self.warnings.append("⚠️ Rate limiting de burst muy permisivo")
            else:
                self.info.append("✅ Rate limiting de burst configurado apropiadamente")
    
    def check_code_quality(self):
        """Verifica calidad del código"""
        # Verificar archivos Python por problemas de seguridad
        python_files = []
        for root, dirs, files in os.walk("app"):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        
        security_patterns = [
            (r"eval\(", "Uso de eval() detectado"),
            (r"exec\(", "Uso de exec() detectado"),
            (r"subprocess\.call\(", "Uso de subprocess.call() sin shell=False"),
            (r"os\.system\(", "Uso de os.system() detectado"),
            (r"password.*=.*['\"]\w+['\"]", "Contraseña hardcodeada detectada"),
            (r"secret.*=.*['\"]\w+['\"]", "Secreto hardcodeado detectado")
        ]
        
        for file_path in python_files[:10]:  # Limitar a 10 archivos para rendimiento
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, message in security_patterns:
                    if re.search(pattern, content):
                        self.warnings.append(f"⚠️ {message} en {file_path}")
                        
            except Exception as e:
                self.warnings.append(f"⚠️ Error verificando {file_path}: {e}")
        
        self.info.append("✅ Verificación de calidad de código completada")
    
    def check_encryption_config(self):
        """Verifica configuración de encriptación"""
        # Verificar algoritmos de encriptación
        if hasattr(settings, 'ENCRYPTION_ALGORITHM'):
            weak_algorithms = ['DES', '3DES', 'RC4', 'MD5', 'SHA1']
            encryption_algo = getattr(settings, 'ENCRYPTION_ALGORITHM', '')
            if encryption_algo in weak_algorithms:
                self.issues.append("❌ Algoritmo de encriptación débil configurado")
            else:
                self.info.append("✅ Algoritmo de encriptación seguro configurado")
        
        # Verificar longitud de claves
        if hasattr(settings, 'ENCRYPTION_KEY_LENGTH'):
            key_length = getattr(settings, 'ENCRYPTION_KEY_LENGTH', 0)
            if key_length < 256:
                self.warnings.append("⚠️ Longitud de clave de encriptación muy corta")
            else:
                self.info.append("✅ Longitud de clave de encriptación apropiada")
        
        # Verificar configuración de salt
        if hasattr(settings, 'PASSWORD_SALT_LENGTH'):
            salt_length = getattr(settings, 'PASSWORD_SALT_LENGTH', 0)
            if salt_length < 16:
                self.warnings.append("⚠️ Longitud de salt muy corta")
            else:
                self.info.append("✅ Longitud de salt apropiada")
    
    def run_dependency_audit(self):
        """Ejecuta auditoría de dependencias"""
        try:
            # Intentar ejecutar safety check
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.info.append("✅ Auditoría de dependencias completada sin vulnerabilidades")
            else:
                vulnerabilities = json.loads(result.stdout)
                self.warnings.append(f"⚠️ Vulnerabilidades encontradas: {len(vulnerabilities)}")
                
        except FileNotFoundError:
            self.warnings.append("⚠️ 'safety' no instalado para auditoría de dependencias")
        except Exception as e:
            self.warnings.append(f"⚠️ Error en auditoría de dependencias: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Genera reporte final"""
        total_checks = len(self.issues) + len(self.warnings) + len(self.info)
        
        print("\n" + "="*60)
        print("📋 REPORTE DE SEGURIDAD")
        print("="*60)
        
        # Mostrar issues críticos
        if self.issues:
            print("\n❌ PROBLEMAS CRÍTICOS:")
            for issue in self.issues:
                print(f"  {issue}")
        
        # Mostrar advertencias
        if self.warnings:
            print("\n⚠️ ADVERTENCIAS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        # Mostrar información
        if self.info:
            print("\n✅ CONFIGURACIONES CORRECTAS:")
            for info in self.info:
                print(f"  {info}")
        
        # Resumen
        print(f"\n📊 RESUMEN:")
        print(f"  • Problemas críticos: {len(self.issues)}")
        print(f"  • Advertencias: {len(self.warnings)}")
        print(f"  • Configuraciones correctas: {len(self.info)}")
        print(f"  • Total verificaciones: {total_checks}")
        
        # Puntuación de seguridad
        if len(self.issues) == 0:
            if len(self.warnings) == 0:
                score = "EXCELENTE"
                color = "🟢"
            elif len(self.warnings) <= 3:
                score = "BUENO"
                color = "🟡"
            else:
                score = "REGULAR"
                color = "🟠"
        else:
            score = "DEFICIENTE"
            color = "🔴"
        
        print(f"\n{color} PUNTUACIÓN DE SEGURIDAD: {score}")
        
        # Recomendaciones
        if self.issues or self.warnings:
            print(f"\n💡 RECOMENDACIONES:")
            if self.issues:
                print("  • Corregir todos los problemas críticos antes de producción")
            if len(self.warnings) > 5:
                print("  • Revisar y resolver las advertencias de seguridad")
            print("  • Ejecutar esta verificación regularmente")
            print("  • Considerar implementar monitoreo continuo de seguridad")
        
        return {
            "critical_issues": len(self.issues),
            "warnings": len(self.warnings),
            "correct_configs": len(self.info),
            "total_checks": total_checks,
            "security_score": score,
            "issues": self.issues,
            "warnings": self.warnings,
            "recommendations": self.info
        }

def main():
    """Función principal"""
    print("🛡️ VERIFICADOR DE SEGURIDAD - SISTEMA DE GIMNASIO")
    print("="*60)
    
    checker = SecurityChecker()
    report = checker.check_all()
    
    # Guardar reporte en archivo
    timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"logs/security_report_{timestamp}.json"
    
    try:
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Reporte guardado en: {report_file}")
    except Exception as e:
        print(f"\n❌ Error guardando reporte: {e}")
    
    # Código de salida basado en problemas críticos
    exit_code = len(checker.issues)
    if exit_code > 0:
        print(f"\n🚨 Saliendo con código {exit_code} debido a problemas críticos")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 