#!/usr/bin/env python3
"""
Script de Hardening de Contenedores - Sistema de Gimnasio v6
Aplica medidas de seguridad y hardening a contenedores Docker
"""

import os
import sys
import json
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import logging
import argparse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContainerHardener:
    """Aplicador de hardening para contenedores Docker"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "containers": {},
            "recommendations": [],
            "summary": {
                "total_containers": 0,
                "hardened": 0,
                "failed": 0,
                "recommendations": 0
            }
        }
    
    def harden_all_containers(self, dry_run: bool = False) -> Dict[str, Any]:
        """Aplicar hardening a todos los contenedores"""
        logger.info("🔒 Iniciando hardening de contenedores...")
        
        # Buscar archivos Dockerfile
        dockerfiles = self._find_dockerfiles()
        
        for dockerfile in dockerfiles:
            self._harden_dockerfile(dockerfile, dry_run)
        
        # Hardening del docker-compose.yml
        docker_compose = self.project_root / "docker-compose.yml"
        if docker_compose.exists():
            self._harden_docker_compose(docker_compose, dry_run)
        
        # Generar recomendaciones
        self._generate_hardening_recommendations()
        
        return self.results
    
    def _find_dockerfiles(self) -> List[Path]:
        """Encontrar todos los Dockerfiles en el proyecto"""
        dockerfiles = []
        
        # Buscar en directorios principales
        search_dirs = ["backend", "web", "docker"]
        
        for search_dir in search_dirs:
            dir_path = self.project_root / search_dir
            if dir_path.exists():
                for dockerfile in dir_path.glob("Dockerfile*"):
                    dockerfiles.append(dockerfile)
        
        # Buscar en raíz del proyecto
        for dockerfile in self.project_root.glob("Dockerfile*"):
            dockerfiles.append(dockerfile)
        
        return dockerfiles
    
    def _harden_dockerfile(self, dockerfile_path: Path, dry_run: bool):
        """Aplicar hardening a un Dockerfile"""
        logger.info(f"🔧 Hardening Dockerfile: {dockerfile_path}")
        
        container_name = dockerfile_path.parent.name
        content = dockerfile_path.read_text()
        
        hardening_results = {
            "file": str(dockerfile_path),
            "checks": {},
            "recommendations": []
        }
        
        # Verificar usuario no-root
        if "USER root" in content and "USER " not in content.replace("USER root", ""):
            hardening_results["checks"]["non_root_user"] = {
                "status": "FAILED",
                "message": "Contenedor ejecutándose como root"
            }
            if not dry_run:
                self._add_non_root_user(dockerfile_path)
                hardening_results["checks"]["non_root_user"]["status"] = "FIXED"
        else:
            hardening_results["checks"]["non_root_user"] = {
                "status": "PASSED",
                "message": "Usuario no-root configurado"
            }
        
        # Verificar actualización de paquetes
        if "apt-get update" in content and "apt-get upgrade" not in content:
            hardening_results["checks"]["package_updates"] = {
                "status": "WARNING",
                "message": "Actualizaciones de paquetes incompletas"
            }
            if not dry_run:
                self._add_package_updates(dockerfile_path)
                hardening_results["checks"]["package_updates"]["status"] = "FIXED"
        else:
            hardening_results["checks"]["package_updates"] = {
                "status": "PASSED",
                "message": "Actualizaciones de paquetes configuradas"
            }
        
        # Verificar limpieza de caché
        if "apt-get install" in content and "rm -rf /var/lib/apt/lists/*" not in content:
            hardening_results["checks"]["cache_cleanup"] = {
                "status": "WARNING",
                "message": "Caché de paquetes no limpiado"
            }
            if not dry_run:
                self._add_cache_cleanup(dockerfile_path)
                hardening_results["checks"]["cache_cleanup"]["status"] = "FIXED"
        else:
            hardening_results["checks"]["cache_cleanup"] = {
                "status": "PASSED",
                "message": "Caché de paquetes limpiado"
            }
        
        # Verificar vulnerabilidades conocidas
        vulnerable_packages = [
            "openssl", "curl", "wget", "bash", "glibc"
        ]
        
        for package in vulnerable_packages:
            if package in content:
                hardening_results["checks"][f"vulnerable_{package}"] = {
                    "status": "WARNING",
                    "message": f"Paquete potencialmente vulnerable: {package}"
                }
        
        # Verificar permisos de archivos
        if "chmod" not in content:
            hardening_results["checks"]["file_permissions"] = {
                "status": "WARNING",
                "message": "Permisos de archivos no configurados"
            }
            if not dry_run:
                self._add_file_permissions(dockerfile_path)
                hardening_results["checks"]["file_permissions"]["status"] = "FIXED"
        else:
            hardening_results["checks"]["file_permissions"] = {
                "status": "PASSED",
                "message": "Permisos de archivos configurados"
            }
        
        # Verificar health checks
        if "HEALTHCHECK" not in content:
            hardening_results["checks"]["health_check"] = {
                "status": "WARNING",
                "message": "Health check no configurado"
            }
            if not dry_run:
                self._add_health_check(dockerfile_path)
                hardening_results["checks"]["health_check"]["status"] = "FIXED"
        else:
            hardening_results["checks"]["health_check"] = {
                "status": "PASSED",
                "message": "Health check configurado"
            }
        
        # Verificar labels de seguridad
        security_labels = [
            "maintainer", "version", "description"
        ]
        
        for label in security_labels:
            if f"LABEL {label}" not in content:
                hardening_results["checks"][f"label_{label}"] = {
                    "status": "INFO",
                    "message": f"Label {label} no configurado"
                }
        
        self.results["containers"][container_name] = hardening_results
    
    def _harden_docker_compose(self, compose_path: Path, dry_run: bool):
        """Aplicar hardening al docker-compose.yml"""
        logger.info(f"🔧 Hardening docker-compose.yml: {compose_path}")
        
        try:
            with open(compose_path, 'r') as f:
                compose_data = yaml.safe_load(f)
            
            hardening_results = {
                "file": str(compose_path),
                "checks": {},
                "recommendations": []
            }
            
            services = compose_data.get("services", {})
            
            for service_name, service_config in services.items():
                service_checks = {}
                
                # Verificar usuario no-root
                if "user" in service_config and service_config["user"] == "root":
                    service_checks["non_root_user"] = {
                        "status": "FAILED",
                        "message": "Servicio ejecutándose como root"
                    }
                    if not dry_run:
                        service_config["user"] = "1000:1000"
                        service_checks["non_root_user"]["status"] = "FIXED"
                else:
                    service_checks["non_root_user"] = {
                        "status": "PASSED",
                        "message": "Usuario no-root configurado"
                    }
                
                # Verificar modo privilegiado
                if service_config.get("privileged", False):
                    service_checks["privileged_mode"] = {
                        "status": "FAILED",
                        "message": "Modo privilegiado habilitado"
                    }
                    if not dry_run:
                        service_config["privileged"] = False
                        service_checks["privileged_mode"]["status"] = "FIXED"
                else:
                    service_checks["privileged_mode"] = {
                        "status": "PASSED",
                        "message": "Modo privilegiado deshabilitado"
                    }
                
                # Verificar capabilities
                if "cap_add" in service_config:
                    dangerous_caps = ["SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE"]
                    for cap in dangerous_caps:
                        if cap in service_config["cap_add"]:
                            service_checks[f"dangerous_cap_{cap}"] = {
                                "status": "WARNING",
                                "message": f"Capability peligrosa: {cap}"
                            }
                
                # Verificar volúmenes sensibles
                volumes = service_config.get("volumes", [])
                sensitive_paths = ["/etc/passwd", "/etc/shadow", "/proc", "/sys"]
                
                for volume in volumes:
                    if isinstance(volume, str):
                        for path in sensitive_paths:
                            if path in volume:
                                service_checks[f"sensitive_volume_{path}"] = {
                                    "status": "WARNING",
                                    "message": f"Volumen sensible montado: {path}"
                                }
                
                # Verificar variables de entorno
                environment = service_config.get("environment", {})
                sensitive_vars = ["password", "secret", "key", "token"]
                
                for var in environment:
                    if isinstance(var, str):
                        for sensitive in sensitive_vars:
                            if sensitive in var.lower():
                                service_checks[f"sensitive_env_{sensitive}"] = {
                                    "status": "WARNING",
                                    "message": f"Variable de entorno sensible: {var}"
                                }
                
                # Verificar restart policy
                restart_policy = service_config.get("restart", "no")
                if restart_policy == "always":
                    service_checks["restart_policy"] = {
                        "status": "WARNING",
                        "message": "Restart policy 'always' puede causar problemas"
                    }
                else:
                    service_checks["restart_policy"] = {
                        "status": "PASSED",
                        "message": "Restart policy apropiada"
                    }
                
                # Verificar límites de recursos
                if "deploy" not in service_config or "resources" not in service_config["deploy"]:
                    service_checks["resource_limits"] = {
                        "status": "WARNING",
                        "message": "Límites de recursos no configurados"
                    }
                    if not dry_run:
                        if "deploy" not in service_config:
                            service_config["deploy"] = {}
                        service_config["deploy"]["resources"] = {
                            "limits": {
                                "cpus": "1.0",
                                "memory": "512M"
                            },
                            "reservations": {
                                "cpus": "0.5",
                                "memory": "256M"
                            }
                        }
                        service_checks["resource_limits"]["status"] = "FIXED"
                else:
                    service_checks["resource_limits"] = {
                        "status": "PASSED",
                        "message": "Límites de recursos configurados"
                    }
                
                hardening_results["checks"][service_name] = service_checks
            
            # Guardar cambios
            if not dry_run:
                with open(compose_path, 'w') as f:
                    yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)
            
            self.results["containers"]["docker_compose"] = hardening_results
            
        except Exception as e:
            logger.error(f"Error hardening docker-compose.yml: {e}")
            self.results["containers"]["docker_compose"] = {
                "file": str(compose_path),
                "error": str(e)
            }
    
    def _add_non_root_user(self, dockerfile_path: Path):
        """Agregar usuario no-root al Dockerfile"""
        content = dockerfile_path.read_text()
        
        # Buscar la línea USER root y reemplazarla
        if "USER root" in content:
            # Agregar creación de usuario antes de USER
            user_creation = """
# Crear usuario no-root
RUN groupadd -r appuser && useradd -r -g appuser appuser
"""
            content = content.replace("USER root", user_creation + "USER appuser")
            
            dockerfile_path.write_text(content)
    
    def _add_package_updates(self, dockerfile_path: Path):
        """Agregar actualizaciones de paquetes"""
        content = dockerfile_path.read_text()
        
        # Buscar línea de instalación de paquetes
        if "apt-get update" in content:
            # Agregar upgrade después de update
            content = content.replace(
                "apt-get update",
                "apt-get update && apt-get upgrade -y"
            )
            
            dockerfile_path.write_text(content)
    
    def _add_cache_cleanup(self, dockerfile_path: Path):
        """Agregar limpieza de caché"""
        content = dockerfile_path.read_text()
        
        # Buscar línea de instalación de paquetes
        if "apt-get install" in content:
            # Agregar limpieza después de instalación
            cleanup = " && rm -rf /var/lib/apt/lists/*"
            content = content.replace("apt-get install", "apt-get install" + cleanup)
            
            dockerfile_path.write_text(content)
    
    def _add_file_permissions(self, dockerfile_path: Path):
        """Agregar configuración de permisos"""
        content = dockerfile_path.read_text()
        
        # Agregar comandos de permisos al final
        permissions = """
# Configurar permisos de archivos
RUN chmod 755 /app && chown -R appuser:appuser /app
"""
        content += permissions
        
        dockerfile_path.write_text(content)
    
    def _add_health_check(self, dockerfile_path: Path):
        """Agregar health check"""
        content = dockerfile_path.read_text()
        
        # Agregar health check al final
        health_check = """
# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1
"""
        content += health_check
        
        dockerfile_path.write_text(content)
    
    def _generate_hardening_recommendations(self):
        """Generar recomendaciones de hardening"""
        logger.info("💡 Generando recomendaciones de hardening...")
        
        recommendations = [
            {
                "type": "security_scan",
                "message": "Ejecutar escaneo de vulnerabilidades en imágenes",
                "command": "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image <image_name>"
            },
            {
                "type": "secrets_management",
                "message": "Usar Docker Secrets para credenciales",
                "command": "docker secret create <secret_name> <secret_file>"
            },
            {
                "type": "network_segmentation",
                "message": "Configurar redes Docker separadas por servicio",
                "command": "docker network create --driver bridge <network_name>"
            },
            {
                "type": "logging",
                "message": "Configurar logging con rotación",
                "command": "docker run --log-driver=json-file --log-opt max-size=10m --log-opt max-file=3 <image>"
            },
            {
                "type": "readonly_root",
                "message": "Configurar sistema de archivos de solo lectura",
                "command": "docker run --read-only <image>"
            },
            {
                "type": "no_new_privileges",
                "message": "Deshabilitar nuevos privilegios",
                "command": "docker run --security-opt=no-new-privileges <image>"
            },
            {
                "type": "apparmor",
                "message": "Configurar perfil AppArmor",
                "command": "docker run --security-opt apparmor=<profile> <image>"
            },
            {
                "type": "selinux",
                "message": "Configurar etiquetas SELinux",
                "command": "docker run --security-opt label=type:<type> <image>"
            }
        ]
        
        self.results["recommendations"] = recommendations
        self.results["summary"]["recommendations"] = len(recommendations)
    
    def scan_vulnerabilities(self, image_name: str = None) -> Dict[str, Any]:
        """Escanear vulnerabilidades en imágenes Docker"""
        logger.info("🔍 Escaneando vulnerabilidades...")
        
        scan_results = {
            "timestamp": datetime.now().isoformat(),
            "images": {},
            "summary": {
                "total_images": 0,
                "vulnerable_images": 0,
                "total_vulnerabilities": 0
            }
        }
        
        # Obtener imágenes del proyecto
        if image_name:
            images = [image_name]
        else:
            images = self._get_project_images()
        
        for image in images:
            try:
                # Usar Trivy si está disponible
                if self._check_command("trivy"):
                    result = self._execute_command(f"trivy image --format json {image}", capture_output=True)
                    if result:
                        vuln_data = json.loads(result)
                        scan_results["images"][image] = vuln_data
                        
                        # Contar vulnerabilidades
                        vulnerabilities = vuln_data.get("Results", [])
                        total_vulns = sum(len(result.get("Vulnerabilities", [])) for result in vulnerabilities)
                        
                        if total_vulns > 0:
                            scan_results["summary"]["vulnerable_images"] += 1
                            scan_results["summary"]["total_vulnerabilities"] += total_vulns
                
                # Usar Docker Scout como alternativa
                elif self._check_command("docker"):
                    result = self._execute_command(f"docker scout cves {image}", capture_output=True)
                    scan_results["images"][image] = {"raw_output": result}
                
                scan_results["summary"]["total_images"] += 1
                
            except Exception as e:
                logger.error(f"Error escaneando imagen {image}: {e}")
                scan_results["images"][image] = {"error": str(e)}
        
        return scan_results
    
    def _get_project_images(self) -> List[str]:
        """Obtener imágenes del proyecto"""
        images = []
        
        # Buscar en docker-compose.yml
        compose_path = self.project_root / "docker-compose.yml"
        if compose_path.exists():
            try:
                with open(compose_path, 'r') as f:
                    compose_data = yaml.safe_load(f)
                
                services = compose_data.get("services", {})
                for service_name, service_config in services.items():
                    if "image" in service_config:
                        images.append(service_config["image"])
                    elif "build" in service_config:
                        # Construir nombre de imagen
                        images.append(f"{self.project_root.name}_{service_name}:latest")
            except Exception as e:
                logger.error(f"Error leyendo docker-compose.yml: {e}")
        
        return images
    
    def _check_command(self, command: str) -> bool:
        """Verificar si un comando está disponible"""
        try:
            subprocess.run([command, "--version"], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False
    
    def _execute_command(self, command: str, capture_output: bool = False) -> Any:
        """Ejecutar comando del sistema"""
        try:
            if capture_output:
                result = subprocess.run(command.split(), capture_output=True, text=True, timeout=60)
                return result.stdout
            else:
                result = subprocess.run(command.split(), timeout=30)
                return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError) as e:
            logger.error(f"Error ejecutando comando '{command}': {e}")
            return False
    
    def save_report(self, output_file: str = None):
        """Guardar reporte de hardening"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"container_hardening_{timestamp}.json"
        
        output_path = self.project_root / "reports" / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Reporte guardado en: {output_path}")
        return output_path
    
    def print_summary(self):
        """Imprimir resumen del hardening"""
        summary = self.results["summary"]
        
        print("\n" + "="*60)
        print("🔒 RESUMEN DE HARDENING DE CONTENEDORES")
        print("="*60)
        print(f"📊 Total de contenedores: {summary['total_containers']}")
        print(f"✅ Hardened: {summary['hardened']}")
        print(f"❌ Fallidos: {summary['failed']}")
        print(f"💡 Recomendaciones: {summary['recommendations']}")
        print("="*60)
        
        # Mostrar contenedores procesados
        for container_name, container_data in self.results["containers"].items():
            print(f"\n📦 Contenedor: {container_name}")
            
            if "checks" in container_data:
                checks = container_data["checks"]
                for check_name, check_data in checks.items():
                    status = check_data["status"]
                    message = check_data["message"]
                    
                    if status == "PASSED":
                        print(f"  ✅ {message}")
                    elif status == "FAILED":
                        print(f"  ❌ {message}")
                    elif status == "WARNING":
                        print(f"  ⚠️  {message}")
                    elif status == "FIXED":
                        print(f"  🔧 {message} (CORREGIDO)")
        
        # Mostrar recomendaciones
        if self.results["recommendations"]:
            print(f"\n💡 RECOMENDACIONES DE HARDENING:")
            for i, rec in enumerate(self.results["recommendations"][:5], 1):
                print(f"  {i}. {rec['message']}")
                print(f"     Comando: {rec['command']}")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Hardening de Contenedores - Sistema de Gimnasio v6")
    parser.add_argument("--dry-run", action="store_true", help="Simular hardening sin aplicar cambios")
    parser.add_argument("--scan", action="store_true", help="Escanear vulnerabilidades en imágenes")
    parser.add_argument("--image", help="Imagen específica para escanear")
    parser.add_argument("--output", help="Archivo de salida para el reporte")
    
    args = parser.parse_args()
    
    print("🔒 Hardening de Contenedores - Sistema de Gimnasio v6")
    print("="*60)
    
    hardener = ContainerHardener()
    
    try:
        if args.scan:
            # Escanear vulnerabilidades
            scan_results = hardener.scan_vulnerabilities(args.image)
            print("🔍 Resultados del escaneo de vulnerabilidades:")
            print(json.dumps(scan_results, indent=2))
        else:
            # Aplicar hardening
            results = hardener.harden_all_containers(args.dry_run)
            
            # Imprimir resumen
            hardener.print_summary()
            
            # Guardar reporte
            report_file = hardener.save_report(args.output)
            
            print(f"\n📄 Reporte guardado en: {report_file}")
            print("\n✅ Hardening completado exitosamente")
        
        # Retornar código de salida
        if args.dry_run:
            sys.exit(0)
        elif hardener.results["summary"]["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Error durante el hardening: {e}")
        print(f"\n❌ Error durante el hardening: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 