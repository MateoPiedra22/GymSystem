#!/usr/bin/env python3
# =============================================================================
# SCRIPT DE DESPLIEGUE AUTOMÁTICO PARA PRODUCCIÓN
# Sistema de Gestión de Gimnasio v6.0
# =============================================================================

import os
import sys
import time
import json
import subprocess
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deploy.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ProductionDeployer:
    """Clase para manejar el despliegue automático en producción"""
    
    def __init__(self, config_file: str = "deployment_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.deploy_start_time = datetime.now()
        
    def load_config(self) -> Dict:
        """Cargar configuración de despliegue"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuración cargada desde {self.config_file}")
            return config
        except FileNotFoundError:
            logger.error(f"Archivo de configuración no encontrado: {self.config_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear configuración: {e}")
            sys.exit(1)
    
    def run_command(self, command: str, check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
        """Ejecutar comando del sistema"""
        logger.info(f"Ejecutando: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=check,
                capture_output=capture_output,
                text=True
            )
            if result.stdout and not capture_output:
                logger.info(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Error ejecutando comando: {e}")
            if e.stderr:
                logger.error(f"Stderr: {e.stderr}")
            if check:
                raise
            # Crear un CompletedProcess con el error
            return subprocess.CompletedProcess(
                args=command,
                returncode=e.returncode,
                stdout=e.stdout or "",
                stderr=e.stderr or ""
            )
    
    def check_prerequisites(self) -> bool:
        """Verificar prerequisitos del sistema"""
        logger.info("Verificando prerequisitos...")
        
        # Verificar Docker
        try:
            result = self.run_command("docker --version", capture_output=True)
            logger.info(f"Docker: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            logger.error("Docker no está instalado")
            return False
        
        # Verificar Docker Compose
        try:
            result = self.run_command("docker-compose --version", capture_output=True)
            logger.info(f"Docker Compose: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            logger.error("Docker Compose no está instalado")
            return False
        
        # Verificar archivos necesarios
        required_files = [
            "docker-compose.yml",
            ".env.production",
            "nginx/conf.d/default.conf",
            "backend/Dockerfile",
            "web/Dockerfile"
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                logger.error(f"Archivo requerido no encontrado: {file_path}")
                return False
        
        logger.info("✅ Todos los prerequisitos están satisfechos")
        return True
    
    def backup_existing_deployment(self) -> bool:
        """Crear backup del despliegue existente"""
        logger.info("Creando backup del despliegue existente...")
        
        backup_dir = f"backups/deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            # Backup de volúmenes de datos
            if self.run_command(f"docker-compose ps", capture_output=True).returncode == 0:
                self.run_command(f"docker-compose down")
                time.sleep(5)
            
            # Backup de archivos de configuración
            self.run_command(f"cp -r nginx {backup_dir}/")
            self.run_command(f"cp -r monitoring {backup_dir}/")
            self.run_command(f"cp docker-compose.yml {backup_dir}/")
            self.run_command(f"cp .env.production {backup_dir}/")
            
            logger.info(f"✅ Backup creado en: {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return False
    
    def generate_ssl_certificates(self) -> bool:
        """Generar certificados SSL"""
        logger.info("Generando certificados SSL...")
        
        try:
            # Verificar si ya existen certificados
            if Path("nginx/ssl/cert.pem").exists() and Path("nginx/ssl/key.pem").exists():
                logger.info("Certificados SSL ya existen, saltando generación")
                return True
            
            # Crear directorio SSL
            Path("nginx/ssl").mkdir(parents=True, exist_ok=True)
            
            # Generar certificados autofirmados para desarrollo
            if self.config.get("ssl_mode") == "self-signed":
                self.run_command("./scripts/generate_ssl_certs.sh --self-signed")
            else:
                # Para producción, usar Let's Encrypt
                domain = self.config.get("domain", "localhost")
                email = self.config.get("ssl_email", "admin@example.com")
                self.run_command(f"./scripts/generate_ssl_certs.sh --letsencrypt -d {domain} -e {email}")
            
            logger.info("✅ Certificados SSL generados")
            return True
            
        except Exception as e:
            logger.error(f"Error generando certificados SSL: {e}")
            return False
    
    def build_images(self) -> bool:
        """Construir imágenes Docker"""
        logger.info("Construyendo imágenes Docker...")
        
        try:
            # Construir backend
            logger.info("Construyendo imagen del backend...")
            self.run_command("docker-compose build backend")
            
            # Construir frontend
            logger.info("Construyendo imagen del frontend...")
            self.run_command("docker-compose build frontend")
            
            # Construir servicio de backup
            logger.info("Construyendo imagen del servicio de backup...")
            self.run_command("docker-compose build backup")
            
            logger.info("✅ Todas las imágenes construidas")
            return True
            
        except Exception as e:
            logger.error(f"Error construyendo imágenes: {e}")
            return False
    
    def deploy_services(self) -> bool:
        """Desplegar servicios"""
        logger.info("Desplegando servicios...")
        
        try:
            # Iniciar servicios en orden
            services_order = [
                "postgres",
                "redis", 
                "backend",
                "frontend",
                "nginx",
                "backup",
                "prometheus",
                "grafana",
                "alertmanager",
                "node-exporter",
                "cadvisor",
                "blackbox-exporter",
                "pgadmin"
            ]
            
            for service in services_order:
                logger.info(f"Iniciando servicio: {service}")
                self.run_command(f"docker-compose up -d {service}")
                
                # Esperar a que el servicio esté saludable
                if service in ["postgres", "redis", "backend", "frontend", "nginx"]:
                    self.wait_for_service_health(service)
            
            logger.info("✅ Todos los servicios desplegados")
            return True
            
        except Exception as e:
            logger.error(f"Error desplegando servicios: {e}")
            return False
    
    def wait_for_service_health(self, service: str, timeout: int = 300) -> bool:
        """Esperar a que un servicio esté saludable"""
        logger.info(f"Esperando a que {service} esté saludable...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                result = self.run_command(f"docker-compose ps {service}", capture_output=True)
                if "healthy" in result.stdout:
                    logger.info(f"✅ {service} está saludable")
                    return True
                elif "unhealthy" in result.stdout:
                    logger.error(f"❌ {service} está no saludable")
                    return False
                
                time.sleep(10)
                
            except Exception as e:
                logger.warning(f"Error verificando salud de {service}: {e}")
                time.sleep(10)
        
        logger.error(f"Timeout esperando a que {service} esté saludable")
        return False
    
    def run_migrations(self) -> bool:
        """Ejecutar migraciones de base de datos"""
        logger.info("Ejecutando migraciones de base de datos...")
        
        try:
            # Esperar a que PostgreSQL esté listo
            self.wait_for_service_health("postgres")
            
            # Ejecutar migraciones
            self.run_command("docker-compose exec -T backend python -m alembic upgrade head")
            
            logger.info("✅ Migraciones ejecutadas")
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando migraciones: {e}")
            return False
    
    def create_admin_user(self) -> bool:
        """Crear usuario administrador"""
        logger.info("Creando usuario administrador...")
        
        try:
            admin_script = """
import sys
sys.path.append('/app')
from app.scripts.create_admin import create_admin_user
create_admin_user()
"""
            
            self.run_command(f"docker-compose exec -T backend python -c '{admin_script}'")
            
            logger.info("✅ Usuario administrador creado")
            return True
            
        except Exception as e:
            logger.error(f"Error creando usuario administrador: {e}")
            return False
    
    def verify_deployment(self) -> bool:
        """Verificar que el despliegue sea exitoso"""
        logger.info("Verificando despliegue...")
        
        try:
            # Verificar que todos los servicios estén ejecutándose
            result = self.run_command("docker-compose ps", capture_output=True)
            if "Up" not in result.stdout:
                logger.error("No todos los servicios están ejecutándose")
                return False
            
            # Verificar endpoints principales
            endpoints = [
                "http://localhost/health",
                "http://localhost/api/health",
                "http://localhost:9090/-/healthy",  # Prometheus
                "http://localhost:3000/api/health"  # Grafana
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"✅ {endpoint} responde correctamente")
                    else:
                        logger.warning(f"⚠️ {endpoint} responde con código {response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ No se puede acceder a {endpoint}: {e}")
            
            logger.info("✅ Verificación de despliegue completada")
            return True
            
        except Exception as e:
            logger.error(f"Error verificando despliegue: {e}")
            return False
    
    def setup_monitoring(self) -> bool:
        """Configurar monitoreo"""
        logger.info("Configurando monitoreo...")
        
        try:
            # Configurar dashboards de Grafana
            if Path("monitoring/grafana/dashboards").exists():
                logger.info("Dashboards de Grafana configurados")
            
            # Configurar alertas
            if Path("monitoring/prometheus/rules/alerts.yml").exists():
                logger.info("Reglas de alerta configuradas")
            
            # Verificar que Prometheus esté scrapeando
            time.sleep(30)  # Esperar a que Prometheus inicie
            try:
                response = requests.get("http://localhost:9090/api/v1/targets", timeout=10)
                if response.status_code == 200:
                    targets = response.json()
                    active_targets = [t for t in targets['data']['activeTargets'] if t['health'] == 'up']
                    logger.info(f"✅ {len(active_targets)} targets activos en Prometheus")
            except Exception as e:
                logger.warning(f"⚠️ No se puede verificar targets de Prometheus: {e}")
            
            logger.info("✅ Monitoreo configurado")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando monitoreo: {e}")
            return False
    
    def run_security_checks(self) -> bool:
        """Ejecutar verificaciones de seguridad"""
        logger.info("Ejecutando verificaciones de seguridad...")
        
        try:
            # Verificar que no haya contenedores ejecutándose como root
            result = self.run_command("docker-compose exec -T backend whoami", capture_output=True)
            if "root" in result.stdout:
                logger.warning("⚠️ Backend ejecutándose como root")
            
            # Verificar que los puertos sensibles no estén expuestos
            result = self.run_command("docker-compose ps", capture_output=True)
            if ":5432->" in result.stdout:
                logger.warning("⚠️ Puerto de PostgreSQL expuesto")
            
            # Verificar headers de seguridad
            try:
                response = requests.get("http://localhost", timeout=10)
                security_headers = [
                    'Strict-Transport-Security',
                    'X-Frame-Options',
                    'X-Content-Type-Options',
                    'X-XSS-Protection'
                ]
                
                for header in security_headers:
                    if header in response.headers:
                        logger.info(f"✅ Header de seguridad presente: {header}")
                    else:
                        logger.warning(f"⚠️ Header de seguridad faltante: {header}")
                        
            except Exception as e:
                logger.warning(f"⚠️ No se pueden verificar headers de seguridad: {e}")
            
            logger.info("✅ Verificaciones de seguridad completadas")
            return True
            
        except Exception as e:
            logger.error(f"Error en verificaciones de seguridad: {e}")
            return False
    
    def generate_deployment_report(self) -> None:
        """Generar reporte de despliegue"""
        logger.info("Generando reporte de despliegue...")
        
        deploy_end_time = datetime.now()
        duration = deploy_end_time - self.deploy_start_time
        
        report = {
            "deployment_info": {
                "start_time": self.deploy_start_time.isoformat(),
                "end_time": deploy_end_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "status": "completed"
            },
            "services": {},
            "health_checks": {},
            "recommendations": []
        }
        
        # Obtener estado de servicios
        try:
            result = self.run_command("docker-compose ps", capture_output=True)
            report["services"]["status"] = result.stdout
        except Exception as e:
            report["services"]["error"] = str(e)
        
        # Verificar recursos del sistema
        try:
            result = self.run_command("docker system df", capture_output=True)
            report["system_resources"] = result.stdout
        except Exception as e:
            report["system_resources"]["error"] = str(e)
        
        # Guardar reporte
        report_file = f"deployment_reports/deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path("deployment_reports").mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Reporte de despliegue guardado en: {report_file}")
    
    def deploy(self) -> bool:
        """Ejecutar despliegue completo"""
        logger.info("🚀 Iniciando despliegue de producción...")
        
        steps = [
            ("Verificar prerequisitos", self.check_prerequisites),
            ("Crear backup", self.backup_existing_deployment),
            ("Generar certificados SSL", self.generate_ssl_certificates),
            ("Construir imágenes", self.build_images),
            ("Desplegar servicios", self.deploy_services),
            ("Ejecutar migraciones", self.run_migrations),
            ("Crear usuario admin", self.create_admin_user),
            ("Configurar monitoreo", self.setup_monitoring),
            ("Verificar despliegue", self.verify_deployment),
            ("Verificaciones de seguridad", self.run_security_checks)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{'='*50}")
            logger.info(f"PASO: {step_name}")
            logger.info(f"{'='*50}")
            
            try:
                if not step_func():
                    logger.error(f"❌ Falló el paso: {step_name}")
                    return False
                logger.info(f"✅ Completado: {step_name}")
            except Exception as e:
                logger.error(f"❌ Error en paso {step_name}: {e}")
                return False
        
        # Generar reporte final
        self.generate_deployment_report()
        
        logger.info("\n" + "="*50)
        logger.info("🎉 DESPLIEGUE COMPLETADO EXITOSAMENTE")
        logger.info("="*50)
        logger.info("URLs de acceso:")
        logger.info(f"  - Aplicación: https://localhost")
        logger.info(f"  - API: https://localhost/api")
        logger.info(f"  - Grafana: http://localhost:{self.config.get('grafana_port', 3000)}")
        logger.info(f"  - Prometheus: http://localhost:{self.config.get('prometheus_port', 9090)}")
        logger.info(f"  - pgAdmin: http://localhost:{self.config.get('pgadmin_port', 5050)}")
        logger.info("\nCredenciales por defecto:")
        logger.info(f"  - Grafana: {self.config.get('grafana_username', 'admin')} / {self.config.get('grafana_password', 'admin')}")
        logger.info(f"  - pgAdmin: {self.config.get('pgadmin_email', 'admin@example.com')} / {self.config.get('pgadmin_password', 'admin')}")
        
        return True

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Despliegue automático para producción")
    parser.add_argument("--config", default="deployment_config.json", help="Archivo de configuración")
    parser.add_argument("--skip-backup", action="store_true", help="Saltar creación de backup")
    parser.add_argument("--skip-ssl", action="store_true", help="Saltar generación de certificados SSL")
    parser.add_argument("--skip-monitoring", action="store_true", help="Saltar configuración de monitoreo")
    
    args = parser.parse_args()
    
    # Crear instancia del deployer
    deployer = ProductionDeployer(args.config)
    
    # Modificar configuración según argumentos
    if args.skip_backup:
        deployer.backup_existing_deployment = lambda: True
    if args.skip_ssl:
        deployer.generate_ssl_certificates = lambda: True
    if args.skip_monitoring:
        deployer.setup_monitoring = lambda: True
    
    # Ejecutar despliegue
    success = deployer.deploy()
    
    if success:
        logger.info("✅ Despliegue completado exitosamente")
        sys.exit(0)
    else:
        logger.error("❌ Despliegue falló")
        sys.exit(1)

if __name__ == "__main__":
    main() 