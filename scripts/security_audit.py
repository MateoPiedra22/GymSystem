#!/usr/bin/env python3
"""
Script de Auditoría de Seguridad - Sistema de Gimnasio v6
Verifica configuraciones de seguridad, dependencias y vulnerabilidades
"""

import os
import sys
import json
import subprocess
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityAuditor:
    """Auditor de seguridad del sistema"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Ejecutar auditoría completa de seguridad"""
        logger.info("🔍 Iniciando auditoría de seguridad completa...")
        
        # Verificaciones de configuración
        self.check_environment_files()
        self.check_docker_security()
        self.check_nginx_security()
        self.check_database_security()
        self.check_dependencies()
        self.check_file_permissions()
        self.check_ssl_certificates()
        self.check_backup_security()
        self.check_monitoring_security()
        
        # Generar resumen
        self.generate_summary()
        
        return self.results
    
    def check_environment_files(self):
        """Verificar archivos de entorno"""
        logger.info("📋 Verificando archivos de entorno...")
        
        env_files = [
            ".env",
            ".env.example", 
            ".env.production.example",
            ".env.development"
        ]
        
        for env_file in env_files:
            file_path = self.project_root / env_file
            if file_path.exists():
                self._check_env_file_security(file_path)
            else:
                self._add_check_result(
                    f"env_file_{env_file}",
                    "WARNING",
                    f"Archivo {env_file} no encontrado",
                    "Considerar crear el archivo si es necesario"
                )
    
    def _check_env_file_security(self, file_path: Path):
        """Verificar seguridad de archivo de entorno"""
        filename = file_path.name
        content = file_path.read_text()
        
        # Verificar credenciales hardcodeadas
        hardcoded_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']'
        ]
        
        for pattern in hardcoded_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self._add_check_result(
                    f"env_hardcoded_{filename}",
                    "FAILED",
                    f"Credenciales hardcodeadas encontradas en {filename}",
                    "Remover credenciales hardcodeadas y usar variables de entorno"
                )
                return
        
        # Verificar permisos de archivo
        if filename == ".env" and file_path.stat().st_mode & 0o777 != 0o600:
            self._add_check_result(
                f"env_permissions_{filename}",
                "FAILED",
                f"Permisos inseguros en {filename}",
                "Cambiar permisos a 600 (solo propietario)"
            )
        else:
            self._add_check_result(
                f"env_security_{filename}",
                "PASSED",
                f"Archivo {filename} es seguro",
                "No se encontraron problemas de seguridad"
            )
    
    def check_docker_security(self):
        """Verificar seguridad de Docker"""
        logger.info("🐳 Verificando configuración de Docker...")
        
        docker_compose = self.project_root / "docker-compose.yml"
        if not docker_compose.exists():
            self._add_check_result(
                "docker_compose_exists",
                "FAILED",
                "docker-compose.yml no encontrado",
                "Archivo esencial para el despliegue"
            )
            return
        
        content = docker_compose.read_text()
        
        # Verificar credenciales hardcodeadas
        if re.search(r'password:\s*["\'][^"\']+["\']', content):
            self._add_check_result(
                "docker_hardcoded_passwords",
                "FAILED",
                "Contraseñas hardcodeadas en docker-compose.yml",
                "Usar variables de entorno para todas las credenciales"
            )
        else:
            self._add_check_result(
                "docker_credentials",
                "PASSED",
                "No se encontraron credenciales hardcodeadas en Docker",
                "Buenas prácticas de seguridad"
            )
        
        # Verificar configuración de seguridad
        security_checks = [
            ("docker_privileged", r'privileged:\s*true', "Contenedores privilegiados detectados"),
            ("docker_root_user", r'user:\s*root', "Contenedores ejecutándose como root"),
            ("docker_host_network", r'network_mode:\s*host', "Modo de red host detectado")
        ]
        
        for check_name, pattern, description in security_checks:
            if re.search(pattern, content):
                self._add_check_result(
                    check_name,
                    "WARNING",
                    description,
                    "Considerar alternativas más seguras"
                )
            else:
                self._add_check_result(
                    f"{check_name}_secure",
                    "PASSED",
                    f"No se encontró {description.lower()}",
                    "Configuración segura"
                )
    
    def check_nginx_security(self):
        """Verificar configuración de seguridad de Nginx"""
        logger.info("🌐 Verificando configuración de Nginx...")
        
        nginx_conf = self.project_root / "nginx" / "nginx.conf"
        if not nginx_conf.exists():
            self._add_check_result(
                "nginx_config_exists",
                "FAILED",
                "nginx.conf no encontrado",
                "Archivo de configuración esencial"
            )
            return
        
        content = nginx_conf.read_text()
        
        # Verificar headers de seguridad
        security_headers = [
            ("nginx_hsts", r'add_header\s+Strict-Transport-Security', "HSTS configurado"),
            ("nginx_csp", r'add_header\s+Content-Security-Policy', "CSP configurado"),
            ("nginx_xframe", r'add_header\s+X-Frame-Options', "X-Frame-Options configurado"),
            ("nginx_xss", r'add_header\s+X-XSS-Protection', "X-XSS-Protection configurado"),
            ("nginx_content_type", r'add_header\s+X-Content-Type-Options', "X-Content-Type-Options configurado")
        ]
        
        for check_name, pattern, description in security_headers:
            if re.search(pattern, content, re.IGNORECASE):
                self._add_check_result(
                    check_name,
                    "PASSED",
                    description,
                    "Header de seguridad configurado correctamente"
                )
            else:
                self._add_check_result(
                    check_name,
                    "WARNING",
                    f"{description} no configurado",
                    "Considerar agregar este header de seguridad"
                )
        
        # Verificar SSL/TLS
        if re.search(r'ssl_protocols', content):
            self._add_check_result(
                "nginx_ssl_protocols",
                "PASSED",
                "Protocolos SSL configurados",
                "SSL/TLS configurado correctamente"
            )
        else:
            self._add_check_result(
                "nginx_ssl_protocols",
                "WARNING",
                "Protocolos SSL no configurados",
                "Configurar protocolos SSL seguros"
            )
    
    def check_database_security(self):
        """Verificar seguridad de base de datos"""
        logger.info("🗄️ Verificando configuración de base de datos...")
        
        # Verificar configuración de PostgreSQL
        postgres_config = self.project_root / "data" / "postgres" / "postgresql.conf"
        if postgres_config.exists():
            content = postgres_config.read_text()
            
            # Verificar configuración de SSL
            if re.search(r'ssl\s*=\s*on', content):
                self._add_check_result(
                    "postgres_ssl",
                    "PASSED",
                    "SSL habilitado en PostgreSQL",
                    "Conexiones encriptadas"
                )
            else:
                self._add_check_result(
                    "postgres_ssl",
                    "WARNING",
                    "SSL no configurado en PostgreSQL",
                    "Considerar habilitar SSL para conexiones seguras"
                )
        
        # Verificar configuración de Redis
        redis_config = self.project_root / "data" / "redis" / "redis.conf"
        if redis_config.exists():
            content = redis_config.read_text()
            
            if re.search(r'requirepass', content):
                self._add_check_result(
                    "redis_auth",
                    "PASSED",
                    "Autenticación configurada en Redis",
                    "Redis protegido con contraseña"
                )
            else:
                self._add_check_result(
                    "redis_auth",
                    "WARNING",
                    "Autenticación no configurada en Redis",
                    "Considerar configurar autenticación"
                )
    
    def check_dependencies(self):
        """Verificar dependencias por vulnerabilidades"""
        logger.info("📦 Verificando dependencias...")
        
        # Verificar requirements.txt
        requirements_file = self.project_root / "backend" / "requirements.txt"
        if requirements_file.exists():
            self._check_python_dependencies(requirements_file)
        
        # Verificar package.json
        package_json = self.project_root / "web" / "package.json"
        if package_json.exists():
            self._check_node_dependencies(package_json)
    
    def _check_python_dependencies(self, requirements_file: Path):
        """Verificar dependencias de Python"""
        try:
            # Intentar usar safety si está disponible
            result = subprocess.run(
                ["safety", "check", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self._add_check_result(
                    "python_dependencies",
                    "PASSED",
                    "No se encontraron vulnerabilidades en dependencias de Python",
                    "Dependencias seguras"
                )
            else:
                self._add_check_result(
                    "python_dependencies",
                    "WARNING",
                    "Posibles vulnerabilidades en dependencias de Python",
                    f"Revisar: {result.stdout}"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._add_check_result(
                "python_dependencies",
                "WARNING",
                "No se pudo verificar dependencias de Python",
                "Instalar 'safety' para verificación automática"
            )
    
    def _check_node_dependencies(self, package_json: Path):
        """Verificar dependencias de Node.js"""
        try:
            # Verificar si npm audit está disponible
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=package_json.parent,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                audit_data = json.loads(result.stdout)
                vulnerabilities = audit_data.get("metadata", {}).get("vulnerabilities", {})
                
                if vulnerabilities.get("total", 0) == 0:
                    self._add_check_result(
                        "node_dependencies",
                        "PASSED",
                        "No se encontraron vulnerabilidades en dependencias de Node.js",
                        "Dependencias seguras"
                    )
                else:
                    self._add_check_result(
                        "node_dependencies",
                        "WARNING",
                        f"Se encontraron {vulnerabilities.get('total', 0)} vulnerabilidades en Node.js",
                        "Ejecutar 'npm audit fix' para corregir"
                    )
            else:
                self._add_check_result(
                    "node_dependencies",
                    "WARNING",
                    "No se pudo verificar dependencias de Node.js",
                    "Verificar instalación de npm"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            self._add_check_result(
                "node_dependencies",
                "WARNING",
                "No se pudo verificar dependencias de Node.js",
                "Verificar instalación de npm y ejecutar 'npm audit'"
            )
    
    def check_file_permissions(self):
        """Verificar permisos de archivos"""
        logger.info("📁 Verificando permisos de archivos...")
        
        critical_files = [
            ".env",
            "docker-compose.yml",
            "nginx/nginx.conf",
            "backend/app/core/security.py"
        ]
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                mode = full_path.stat().st_mode & 0o777
                
                if mode == 0o600 or mode == 0o644:
                    self._add_check_result(
                        f"file_permissions_{file_path.replace('/', '_')}",
                        "PASSED",
                        f"Permisos seguros en {file_path}",
                        f"Permisos: {oct(mode)}"
                    )
                else:
                    self._add_check_result(
                        f"file_permissions_{file_path.replace('/', '_')}",
                        "WARNING",
                        f"Permisos inseguros en {file_path}",
                        f"Cambiar permisos de {oct(mode)} a 600 o 644"
                    )
    
    def check_ssl_certificates(self):
        """Verificar certificados SSL"""
        logger.info("🔒 Verificando certificados SSL...")
        
        ssl_dir = self.project_root / "nginx" / "ssl"
        if ssl_dir.exists():
            cert_files = list(ssl_dir.glob("*.crt"))
            key_files = list(ssl_dir.glob("*.key"))
            
            if cert_files and key_files:
                self._add_check_result(
                    "ssl_certificates",
                    "PASSED",
                    "Certificados SSL encontrados",
                    f"{len(cert_files)} certificados y {len(key_files)} claves"
                )
                
                # Verificar permisos de claves privadas
                for key_file in key_files:
                    mode = key_file.stat().st_mode & 0o777
                    if mode == 0o600:
                        self._add_check_result(
                            f"ssl_key_permissions_{key_file.name}",
                            "PASSED",
                            f"Permisos seguros en {key_file.name}",
                            "Clave privada protegida"
                        )
                    else:
                        self._add_check_result(
                            f"ssl_key_permissions_{key_file.name}",
                            "FAILED",
                            f"Permisos inseguros en {key_file.name}",
                            f"Cambiar permisos de {oct(mode)} a 600"
                        )
            else:
                self._add_check_result(
                    "ssl_certificates",
                    "WARNING",
                    "Certificados SSL no encontrados",
                    "Generar certificados SSL para producción"
                )
        else:
            self._add_check_result(
                "ssl_certificates",
                "WARNING",
                "Directorio SSL no encontrado",
                "Crear directorio nginx/ssl y generar certificados"
            )
    
    def check_backup_security(self):
        """Verificar seguridad de backups"""
        logger.info("💾 Verificando seguridad de backups...")
        
        backup_dir = self.project_root / "backups"
        if backup_dir.exists():
            # Verificar permisos del directorio de backups
            mode = backup_dir.stat().st_mode & 0o777
            if mode == 0o700:
                self._add_check_result(
                    "backup_directory_permissions",
                    "PASSED",
                    "Permisos seguros en directorio de backups",
                    "Solo propietario puede acceder"
                )
            else:
                self._add_check_result(
                    "backup_directory_permissions",
                    "WARNING",
                    "Permisos inseguros en directorio de backups",
                    f"Cambiar permisos de {oct(mode)} a 700"
                )
            
            # Verificar si hay backups encriptados
            backup_files = list(backup_dir.glob("*.gpg"))
            if backup_files:
                self._add_check_result(
                    "backup_encryption",
                    "PASSED",
                    "Backups encriptados encontrados",
                    f"{len(backup_files)} archivos encriptados"
                )
            else:
                self._add_check_result(
                    "backup_encryption",
                    "WARNING",
                    "No se encontraron backups encriptados",
                    "Considerar habilitar encriptación de backups"
                )
        else:
            self._add_check_result(
                "backup_directory",
                "WARNING",
                "Directorio de backups no encontrado",
                "Crear directorio backups para almacenamiento seguro"
            )
    
    def check_monitoring_security(self):
        """Verificar seguridad del monitoreo"""
        logger.info("📊 Verificando seguridad del monitoreo...")
        
        # Verificar configuración de Prometheus
        prometheus_config = self.project_root / "monitoring" / "prometheus.yml"
        if prometheus_config.exists():
            content = prometheus_config.read_text()
            
            # Verificar si hay autenticación configurada
            if re.search(r'basic_auth', content):
                self._add_check_result(
                    "prometheus_auth",
                    "PASSED",
                    "Autenticación configurada en Prometheus",
                    "Acceso protegido"
                )
            else:
                self._add_check_result(
                    "prometheus_auth",
                    "WARNING",
                    "Autenticación no configurada en Prometheus",
                    "Considerar configurar autenticación básica"
                )
        
        # Verificar configuración de Grafana
        grafana_datasources = self.project_root / "monitoring" / "grafana" / "datasources"
        if grafana_datasources.exists():
            self._add_check_result(
                "grafana_config",
                "PASSED",
                "Configuración de Grafana encontrada",
                "Datasources configuradas"
            )
        else:
            self._add_check_result(
                "grafana_config",
                "WARNING",
                "Configuración de Grafana no encontrada",
                "Configurar datasources de Grafana"
            )
    
    def _add_check_result(self, check_name: str, status: str, message: str, recommendation: str):
        """Agregar resultado de verificación"""
        self.results["checks"][check_name] = {
            "status": status,
            "message": message,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        }
        
        if status == "PASSED":
            self.results["summary"]["passed"] += 1
        elif status == "FAILED":
            self.results["summary"]["failed"] += 1
        elif status == "WARNING":
            self.results["summary"]["warnings"] += 1
        
        self.results["summary"]["total_checks"] += 1
    
    def generate_summary(self):
        """Generar resumen de la auditoría"""
        summary = self.results["summary"]
        total = summary["total_checks"]
        
        if total > 0:
            pass_rate = (summary["passed"] / total) * 100
            fail_rate = (summary["failed"] / total) * 100
            warning_rate = (summary["warnings"] / total) * 100
            
            self.results["summary"]["pass_rate"] = round(pass_rate, 2)
            self.results["summary"]["fail_rate"] = round(fail_rate, 2)
            self.results["summary"]["warning_rate"] = round(warning_rate, 2)
            
            # Determinar nivel de seguridad general
            if fail_rate == 0 and warning_rate <= 20:
                self.results["summary"]["security_level"] = "EXCELLENT"
            elif fail_rate <= 10 and warning_rate <= 30:
                self.results["summary"]["security_level"] = "GOOD"
            elif fail_rate <= 20:
                self.results["summary"]["security_level"] = "FAIR"
            else:
                self.results["summary"]["security_level"] = "POOR"
    
    def save_report(self, output_file: str = None):
        """Guardar reporte de auditoría"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"security_audit_{timestamp}.json"
        
        output_path = self.project_root / "reports" / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Reporte guardado en: {output_path}")
        return output_path
    
    def print_summary(self):
        """Imprimir resumen de la auditoría"""
        summary = self.results["summary"]
        
        print("\n" + "="*60)
        print("🔍 RESUMEN DE AUDITORÍA DE SEGURIDAD")
        print("="*60)
        print(f"📊 Total de verificaciones: {summary['total_checks']}")
        print(f"✅ Exitosas: {summary['passed']} ({summary.get('pass_rate', 0)}%)")
        print(f"❌ Fallidas: {summary['failed']} ({summary.get('fail_rate', 0)}%)")
        print(f"⚠️  Advertencias: {summary['warnings']} ({summary.get('warning_rate', 0)}%)")
        print(f"🛡️  Nivel de seguridad: {summary.get('security_level', 'UNKNOWN')}")
        print("="*60)
        
        # Mostrar verificaciones fallidas
        failed_checks = [
            (name, check) for name, check in self.results["checks"].items()
            if check["status"] == "FAILED"
        ]
        
        if failed_checks:
            print("\n❌ VERIFICACIONES FALLIDAS:")
            for name, check in failed_checks:
                print(f"  • {check['message']}")
                print(f"    Recomendación: {check['recommendation']}")
                print()
        
        # Mostrar advertencias importantes
        warning_checks = [
            (name, check) for name, check in self.results["checks"].items()
            if check["status"] == "WARNING"
        ]
        
        if warning_checks:
            print("\n⚠️  ADVERTENCIAS IMPORTANTES:")
            for name, check in warning_checks[:5]:  # Mostrar solo las primeras 5
                print(f"  • {check['message']}")
                print(f"    Recomendación: {check['recommendation']}")
                print()

def main():
    """Función principal"""
    print("Auditoria de Seguridad - Sistema de Gimnasio v6")
    print("="*60)
    
    auditor = SecurityAuditor()
    
    try:
        # Ejecutar auditoría completa
        results = auditor.run_full_audit()
        
        # Imprimir resumen
        auditor.print_summary()
        
        # Guardar reporte
        report_file = auditor.save_report()
        
        print(f"\n📄 Reporte detallado guardado en: {report_file}")
        print("\n✅ Auditoría completada exitosamente")
        
        # Retornar código de salida basado en el nivel de seguridad
        security_level = results["summary"].get("security_level", "UNKNOWN")
        if security_level in ["EXCELLENT", "GOOD"]:
            sys.exit(0)
        elif security_level == "FAIR":
            sys.exit(1)
        else:
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"Error durante la auditoría: {e}")
        print(f"\n❌ Error durante la auditoría: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 