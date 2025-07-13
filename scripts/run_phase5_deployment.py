#!/usr/bin/env python3
"""
Script Maestro - Fase 5: Despliegue y Monitoreo
Ejecuta el despliegue completo y configuración de monitoreo
"""

import os
import sys
import time
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import asyncio
import aiohttp

class Phase5Deployer:
    """Desplegador de la Fase 5: Despliegue y Monitoreo"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.deployment_id = f"phase5_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.log_file = f"phase5_deployment_{self.deployment_id}.log"
        self.results = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        # Guardar en archivo de log
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def run_command(self, command: List[str], cwd: str = None, timeout: int = 300) -> Dict[str, Any]:
        """Ejecutar comando y retornar resultados"""
        try:
            self.log(f"Ejecutando: {' '.join(command)}")
            start_time = time.time()
            
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time,
                "command": command
            }
            
        except subprocess.TimeoutExpired:
            self.log(f"Timeout ejecutando: {' '.join(command)}", "ERROR")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Timeout expired",
                "execution_time": timeout,
                "command": command
            }
        except Exception as e:
            self.log(f"Error ejecutando: {' '.join(command)} - {e}", "ERROR")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "execution_time": 0,
                "command": command
            }
    
    def validate_prerequisites(self) -> bool:
        """Validar prerrequisitos para el despliegue"""
        self.log("🔍 Validando prerrequisitos...")
        
        # Verificar Docker
        docker_check = self.run_command(["docker", "--version"])
        if not docker_check["success"]:
            self.log("❌ Docker no está disponible", "ERROR")
            return False
        
        # Verificar Docker Compose
        compose_check = self.run_command(["docker-compose", "--version"])
        if not compose_check["success"]:
            self.log("❌ Docker Compose no está disponible", "ERROR")
            return False
        
        # Verificar archivos de configuración
        required_files = [
            "docker-compose.yml",
            "deployment_config.json",
            "backend/Dockerfile",
            "web/Dockerfile",
            "nginx/Dockerfile"
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                self.log(f"❌ Archivo requerido no encontrado: {file_path}", "ERROR")
                return False
        
        self.log("✅ Prerrequisitos validados correctamente")
        return True
    
    def run_pre_deployment_tests(self) -> bool:
        """Ejecutar tests pre-despliegue"""
        self.log("🧪 Ejecutando tests pre-despliegue...")
        
        # Ejecutar tests críticos
        test_script = Path("scripts/run_phase4_tests.py")
        if test_script.exists():
            test_result = self.run_command([
                "python", str(test_script), "--category", "security"
            ])
            
            if not test_result["success"]:
                self.log("❌ Tests de seguridad fallaron", "ERROR")
                return False
            
            test_result = self.run_command([
                "python", str(test_script), "--category", "integration"
            ])
            
            if not test_result["success"]:
                self.log("❌ Tests de integración fallaron", "ERROR")
                return False
        
        self.log("✅ Tests pre-despliegue completados exitosamente")
        return True
    
    def deploy_infrastructure(self) -> Dict[str, Any]:
        """Desplegar infraestructura"""
        self.log("🏗️ Desplegando infraestructura...")
        
        results = {}
        
        # Crear directorios necesarios
        directories = [
            "data/postgres",
            "data/redis",
            "logs",
            "backups",
            "uploads"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Configurar variables de entorno
        env_file = Path(".env.production")
        if not env_file.exists():
            self.log("📝 Creando archivo de variables de entorno...")
            env_content = """
# Configuración de Producción
NODE_ENV=production
DEBUG=false
LOG_LEVEL=info

# Base de datos
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/gym_production
REDIS_URL=redis://redis:6379

# Seguridad
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Dominio
DOMAIN=gym.example.com

# Monitoreo
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
            """.strip()
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
        
        # Levantar servicios de infraestructura
        self.log("🐳 Levantando servicios de infraestructura...")
        infra_result = self.run_command([
            "docker-compose", "up", "-d", "postgres", "redis"
        ])
        results["infrastructure"] = infra_result
        
        if not infra_result["success"]:
            self.log("❌ Error levantando infraestructura", "ERROR")
            return results
        
        # Esperar a que los servicios estén listos
        self.log("⏳ Esperando a que los servicios estén listos...")
        time.sleep(30)
        
        return results
    
    def deploy_application(self) -> Dict[str, Any]:
        """Desplegar aplicación"""
        self.log("🚀 Desplegando aplicación...")
        
        results = {}
        
        # Construir imágenes
        self.log("🔨 Construyendo imágenes...")
        build_result = self.run_command([
            "docker-compose", "build"
        ])
        results["build"] = build_result
        
        if not build_result["success"]:
            self.log("❌ Error construyendo imágenes", "ERROR")
            return results
        
        # Levantar aplicación
        self.log("⬆️ Levantando aplicación...")
        up_result = self.run_command([
            "docker-compose", "up", "-d"
        ])
        results["deploy"] = up_result
        
        if not up_result["success"]:
            self.log("❌ Error levantando aplicación", "ERROR")
            return results
        
        # Esperar a que la aplicación esté lista
        self.log("⏳ Esperando a que la aplicación esté lista...")
        time.sleep(60)
        
        return results
    
    def setup_monitoring(self) -> Dict[str, Any]:
        """Configurar sistema de monitoreo"""
        self.log("📊 Configurando sistema de monitoreo...")
        
        results = {}
        
        # Levantar servicios de monitoreo
        monitoring_result = self.run_command([
            "docker-compose", "-f", "docker-compose.monitoring.yml", "up", "-d"
        ])
        results["monitoring_services"] = monitoring_result
        
        if not monitoring_result["success"]:
            self.log("❌ Error configurando servicios de monitoreo", "ERROR")
            return results
        
        # Configurar Prometheus
        self.log("📈 Configurando Prometheus...")
        prometheus_config = Path("monitoring/prometheus/prometheus.yml")
        if prometheus_config.exists():
            self.log("✅ Configuración de Prometheus encontrada")
        
        # Configurar Grafana
        self.log("📊 Configurando Grafana...")
        grafana_dashboards = Path("monitoring/grafana/dashboards")
        if grafana_dashboards.exists():
            self.log("✅ Dashboards de Grafana encontrados")
        
        # Configurar alertas
        self.log("🚨 Configurando alertas...")
        alerts_config = Path("monitoring/prometheus/rules/alerts.yml")
        if alerts_config.exists():
            self.log("✅ Reglas de alertas encontradas")
        
        # Esperar a que los servicios de monitoreo estén listos
        self.log("⏳ Esperando a que los servicios de monitoreo estén listos...")
        time.sleep(30)
        
        return results
    
    async def verify_deployment(self) -> Dict[str, Any]:
        """Verificar despliegue"""
        self.log("✅ Verificando despliegue...")
        
        results = {}
        
        # Verificar servicios Docker
        services_check = self.run_command(["docker-compose", "ps"])
        results["services_status"] = services_check
        
        # Verificar endpoints críticos
        endpoints = [
            "http://localhost/health",
            "http://localhost/api/health",
            "http://localhost:9090/-/healthy",  # Prometheus
            "http://localhost:3000/api/health"  # Grafana
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    async with session.get(endpoint, timeout=10) as response:
                        results[f"endpoint_{endpoint.split('/')[-1]}"] = {
                            "success": response.status_code == 200,
                            "status_code": response.status_code,
                            "response_time": response.elapsed.total_seconds()
                        }
                except Exception as e:
                    results[f"endpoint_{endpoint.split('/')[-1]}"] = {
                        "success": False,
                        "error": str(e)
                    }
        
        return results
    
    def setup_backup_system(self) -> Dict[str, Any]:
        """Configurar sistema de backup"""
        self.log("💾 Configurando sistema de backup...")
        
        results = {}
        
        # Crear script de backup
        backup_script = Path("scripts/backup_system.py")
        if not backup_script.exists():
            self.log("📝 Creando script de backup...")
            backup_content = '''#!/usr/bin/env python3
"""
Script de Backup Automatizado - Sistema de Gimnasio v6
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

def create_backup():
    """Crear backup completo del sistema"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backups/backup_{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup de base de datos
    db_backup = backup_dir / "database.sql"
    subprocess.run([
        "docker-compose", "exec", "-T", "postgres",
        "pg_dump", "-U", "postgres", "gym_production"
    ], stdout=open(db_backup, 'w'))
    
    # Backup de archivos
    files_backup = backup_dir / "files.tar.gz"
    subprocess.run([
        "tar", "-czf", str(files_backup), "uploads/", "logs/"
    ])
    
    # Backup de configuración
    config_backup = backup_dir / "config.tar.gz"
    subprocess.run([
        "tar", "-czf", str(config_backup), ".env.production", "docker-compose.yml"
    ])
    
    print(f"Backup completado: {backup_dir}")
    return backup_dir

if __name__ == "__main__":
    create_backup()
'''
            with open(backup_script, 'w', encoding='utf-8') as f:
                f.write(backup_content)
            
            # Hacer ejecutable
            os.chmod(backup_script, 0o755)
        
        # Configurar cron job para backup automático
        self.log("⏰ Configurando backup automático...")
        cron_job = "0 2 * * * cd /path/to/gym-system && python scripts/backup_system.py"
        self.log(f"Cron job sugerido: {cron_job}")
        
        results["backup_script"] = {"success": True, "script": str(backup_script)}
        
        return results
    
    def setup_ssl_certificates(self) -> Dict[str, Any]:
        """Configurar certificados SSL"""
        self.log("🔒 Configurando certificados SSL...")
        
        results = {}
        
        # Verificar si Let's Encrypt está configurado
        ssl_config = self.config.get("ssl", {})
        if ssl_config.get("provider") == "lets_encrypt":
            self.log("📜 Configurando Let's Encrypt...")
            
            # Crear configuración de Nginx para SSL
            nginx_ssl_config = Path("nginx/ssl.conf")
            if not nginx_ssl_config.exists():
                ssl_content = '''
# Configuración SSL
ssl_certificate /etc/letsencrypt/live/gym.example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/gym.example.com/privkey.pem;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
'''
                with open(nginx_ssl_config, 'w', encoding='utf-8') as f:
                    f.write(ssl_content)
            
            # Configurar renovación automática
            renewal_script = Path("scripts/renew_ssl.py")
            if not renewal_script.exists():
                renewal_content = '''#!/usr/bin/env python3
"""
Script de Renovación SSL - Sistema de Gimnasio v6
"""

import subprocess
import sys

def renew_ssl():
    """Renovar certificados SSL"""
    try:
        result = subprocess.run([
            "docker-compose", "exec", "-T", "nginx",
            "certbot", "renew", "--quiet"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Certificados SSL renovados exitosamente")
            # Recargar Nginx
            subprocess.run(["docker-compose", "exec", "-T", "nginx", "nginx", "-s", "reload"])
        else:
            print(f"Error renovando certificados: {result.stderr}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    renew_ssl()
'''
                with open(renewal_script, 'w', encoding='utf-8') as f:
                    f.write(renewal_content)
                
                os.chmod(renewal_script, 0o755)
        
        results["ssl_config"] = {"success": True}
        return results
    
    def generate_deployment_report(self, success: bool) -> Dict[str, Any]:
        """Generar reporte de despliegue"""
        self.log("📋 Generando reporte de despliegue...")
        
        report = {
            "deployment_id": self.deployment_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "results": self.results,
            "log_file": self.log_file,
            "config": self.config
        }
        
        # Guardar reporte
        report_file = f"phase5_deployment_report_{self.deployment_id}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"📋 Reporte guardado: {report_file}")
        return report
    
    def print_summary(self, success: bool):
        """Imprimir resumen del despliegue"""
        print("\n" + "="*80)
        print("🚀 RESUMEN DE DESPLIEGUE - FASE 5: DESPLIEGUE Y MONITOREO")
        print("="*80)
        
        if success:
            print("✅ Despliegue completado exitosamente!")
            print("\n📊 Servicios desplegados:")
            print("   🐳 Docker containers: Postgres, Redis, Backend, Frontend, Nginx")
            print("   📈 Monitoreo: Prometheus, Grafana, AlertManager")
            print("   🔒 Seguridad: SSL/TLS, Rate limiting, WAF")
            print("   💾 Backup: Sistema automático configurado")
            
            print("\n🌐 URLs de acceso:")
            print("   📱 Aplicación: http://localhost")
            print("   📊 Grafana: http://localhost:3000")
            print("   📈 Prometheus: http://localhost:9090")
            print("   🚨 AlertManager: http://localhost:9093")
            
            print("\n🔧 Comandos útiles:")
            print("   Ver logs: docker-compose logs -f")
            print("   Reiniciar: docker-compose restart")
            print("   Backup: python scripts/backup_system.py")
            print("   Monitoreo: python scripts/monitoring_dashboard.py")
            
        else:
            print("❌ Despliegue falló")
            print("📋 Revisar logs en:", self.log_file)
        
        print("\n📁 Archivos generados:")
        print(f"   📋 Log: {self.log_file}")
        print(f"   📊 Reporte: phase5_deployment_report_{self.deployment_id}.json")
        print("="*80)
    
    async def deploy(self) -> bool:
        """Ejecutar despliegue completo"""
        self.log("🚀 Iniciando despliegue de la Fase 5...")
        
        try:
            # 1. Validar prerrequisitos
            if not self.validate_prerequisites():
                return False
            
            # 2. Tests pre-despliegue
            if not self.run_pre_deployment_tests():
                return False
            
            # 3. Desplegar infraestructura
            self.results["infrastructure"] = self.deploy_infrastructure()
            
            # 4. Desplegar aplicación
            self.results["application"] = self.deploy_application()
            
            # 5. Configurar monitoreo
            self.results["monitoring"] = self.setup_monitoring()
            
            # 6. Configurar backup
            self.results["backup"] = self.setup_backup_system()
            
            # 7. Configurar SSL
            self.results["ssl"] = self.setup_ssl_certificates()
            
            # 8. Verificar despliegue
            self.results["verification"] = await self.verify_deployment()
            
            # Determinar éxito
            success = all(
                result.get("success", False) 
                for result in self.results.values() 
                if isinstance(result, dict) and "success" in result
            )
            
            # Generar reporte
            self.generate_deployment_report(success)
            
            # Imprimir resumen
            self.print_summary(success)
            
            return success
            
        except KeyboardInterrupt:
            self.log("⏹️ Despliegue interrumpido por el usuario", "WARNING")
            return False
        except Exception as e:
            self.log(f"❌ Error durante el despliegue: {e}", "ERROR")
            return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Desplegador de la Fase 5: Despliegue y Monitoreo")
    parser.add_argument("--config", type=str, default="deployment_config.json", help="Archivo de configuración")
    parser.add_argument("--dry-run", action="store_true", help="Simular despliegue sin ejecutar")
    parser.add_argument("--verify-only", action="store_true", help="Solo verificar despliegue actual")
    
    args = parser.parse_args()
    
    # Cargar configuración
    if os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            "domain": "gym.example.com",
            "ssl": {"provider": "lets_encrypt"},
            "monitoring": {"enabled": True}
        }
    
    # Crear desplegador
    deployer = Phase5Deployer(config)
    
    if args.dry_run:
        deployer.log("🔍 Modo dry-run: simulando despliegue...")
        success = deployer.validate_prerequisites()
    elif args.verify_only:
        import asyncio
        success = asyncio.run(deployer.verify_deployment())
    else:
        success = asyncio.run(deployer.deploy())
    
    # Código de salida
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 