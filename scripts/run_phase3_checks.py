#!/usr/bin/env python3
"""
Script Maestro de Verificaciones Fase 3 - Sistema de Gimnasio v6
Ejecuta todas las verificaciones de seguridad y optimización de la Fase 3
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
import logging
import argparse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase3Checker:
    """Verificador maestro de la Fase 3"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Fase 3: Seguridad y Optimización",
            "checks": {},
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "skipped": 0
            }
        }
    
    def run_all_checks(self, dry_run: bool = False) -> Dict[str, Any]:
        """Ejecutar todas las verificaciones de la Fase 3"""
        logger.info("🚀 Iniciando verificaciones completas de la Fase 3...")
        
        print("\n" + "="*80)
        print("🛡️ FASE 3: SEGURIDAD Y OPTIMIZACIÓN - VERIFICACIONES COMPLETAS")
        print("="*80)
        
        # 1. Verificar módulos de seguridad y performance
        self._check_security_modules()
        self._check_performance_modules()
        
        # 2. Ejecutar auditoría de seguridad
        self._run_security_audit(dry_run)
        
        # 3. Ejecutar optimización de base de datos
        self._run_database_optimization(dry_run)
        
        # 4. Verificar configuración de firewall
        self._run_firewall_check(dry_run)
        
        # 5. Ejecutar hardening de contenedores
        self._run_container_hardening(dry_run)
        
        # 6. Verificar integración del sistema
        self._check_system_integration()
        
        # 7. Generar resumen final
        self._generate_final_summary()
        
        return self.results
    
    def _check_security_modules(self):
        """Verificar módulos de seguridad"""
        logger.info("🔒 Verificando módulos de seguridad...")
        
        security_file = self.project_root / "backend" / "app" / "core" / "security.py"
        
        if security_file.exists():
            content = security_file.read_text()
            
            # Verificar clases principales
            required_classes = [
                "SecurityConfig",
                "AdvancedRateLimiter", 
                "PasswordValidator",
                "FileValidator",
                "SecurityAuditor",
                "SecurityMiddleware"
            ]
            
            missing_classes = []
            for class_name in required_classes:
                if class_name not in content:
                    missing_classes.append(class_name)
            
            if missing_classes:
                self._add_check_result(
                    "security_modules_classes",
                    "FAILED",
                    f"Clases faltantes en security.py: {', '.join(missing_classes)}",
                    "Verificar implementación del módulo de seguridad"
                )
            else:
                self._add_check_result(
                    "security_modules_classes",
                    "PASSED",
                    "Todas las clases de seguridad implementadas",
                    "Módulo de seguridad completo"
                )
            
            # Verificar funciones principales
            required_functions = [
                "generate_secure_token",
                "hash_password",
                "verify_password",
                "sanitize_filename"
            ]
            
            missing_functions = []
            for func_name in required_functions:
                if f"def {func_name}" not in content:
                    missing_functions.append(func_name)
            
            if missing_functions:
                self._add_check_result(
                    "security_modules_functions",
                    "WARNING",
                    f"Funciones faltantes en security.py: {', '.join(missing_functions)}",
                    "Verificar implementación de funciones de seguridad"
                )
            else:
                self._add_check_result(
                    "security_modules_functions",
                    "PASSED",
                    "Todas las funciones de seguridad implementadas",
                    "Funciones de seguridad completas"
                )
        else:
            self._add_check_result(
                "security_modules_file",
                "FAILED",
                "Archivo security.py no encontrado",
                "Crear módulo de seguridad en backend/app/core/security.py"
            )
    
    def _check_performance_modules(self):
        """Verificar módulos de performance"""
        logger.info("⚡ Verificando módulos de performance...")
        
        performance_file = self.project_root / "backend" / "app" / "core" / "performance.py"
        
        if performance_file.exists():
            content = performance_file.read_text()
            
            # Verificar clases principales
            required_classes = [
                "PerformanceConfig",
                "AdvancedCache",
                "QueryOptimizer", 
                "ResponseOptimizer",
                "PerformanceMonitor",
                "PerformanceMiddleware"
            ]
            
            missing_classes = []
            for class_name in required_classes:
                if class_name not in content:
                    missing_classes.append(class_name)
            
            if missing_classes:
                self._add_check_result(
                    "performance_modules_classes",
                    "FAILED",
                    f"Clases faltantes en performance.py: {', '.join(missing_classes)}",
                    "Verificar implementación del módulo de performance"
                )
            else:
                self._add_check_result(
                    "performance_modules_classes",
                    "PASSED",
                    "Todas las clases de performance implementadas",
                    "Módulo de performance completo"
                )
            
            # Verificar funciones principales
            required_functions = [
                "cache_result",
                "batch_process",
                "performance_context",
                "initialize_cache",
                "get_cache"
            ]
            
            missing_functions = []
            for func_name in required_functions:
                if f"def {func_name}" not in content:
                    missing_functions.append(func_name)
            
            if missing_functions:
                self._add_check_result(
                    "performance_modules_functions",
                    "WARNING",
                    f"Funciones faltantes en performance.py: {', '.join(missing_functions)}",
                    "Verificar implementación de funciones de performance"
                )
            else:
                self._add_check_result(
                    "performance_modules_functions",
                    "PASSED",
                    "Todas las funciones de performance implementadas",
                    "Funciones de performance completas"
                )
        else:
            self._add_check_result(
                "performance_modules_file",
                "FAILED",
                "Archivo performance.py no encontrado",
                "Crear módulo de performance en backend/app/core/performance.py"
            )
    
    def _run_security_audit(self, dry_run: bool):
        """Ejecutar auditoría de seguridad"""
        logger.info("🔍 Ejecutando auditoría de seguridad...")
        
        audit_script = self.project_root / "scripts" / "security_audit.py"
        
        if audit_script.exists():
            try:
                cmd = [sys.executable, str(audit_script)]
                if dry_run:
                    cmd.append("--dry-run")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self._add_check_result(
                        "security_audit_execution",
                        "PASSED",
                        "Auditoría de seguridad ejecutada exitosamente",
                        "Verificar reporte generado en reports/"
                    )
                else:
                    self._add_check_result(
                        "security_audit_execution",
                        "FAILED",
                        f"Error en auditoría de seguridad: {result.stderr}",
                        "Revisar configuración y dependencias"
                    )
            except subprocess.TimeoutExpired:
                self._add_check_result(
                    "security_audit_execution",
                    "FAILED",
                    "Auditoría de seguridad excedió tiempo límite",
                    "Verificar rendimiento del sistema"
                )
            except Exception as e:
                self._add_check_result(
                    "security_audit_execution",
                    "FAILED",
                    f"Error ejecutando auditoría: {e}",
                    "Verificar instalación de dependencias"
                )
        else:
            self._add_check_result(
                "security_audit_script",
                "FAILED",
                "Script de auditoría de seguridad no encontrado",
                "Crear scripts/security_audit.py"
            )
    
    def _run_database_optimization(self, dry_run: bool):
        """Ejecutar optimización de base de datos"""
        logger.info("🗄️ Ejecutando optimización de base de datos...")
        
        db_script = self.project_root / "scripts" / "database_optimization.py"
        
        if db_script.exists():
            try:
                cmd = [sys.executable, str(db_script)]
                if dry_run:
                    cmd.append("--dry-run")
                else:
                    cmd.append("--check")  # Solo verificar, no aplicar cambios
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self._add_check_result(
                        "database_optimization_execution",
                        "PASSED",
                        "Optimización de base de datos ejecutada exitosamente",
                        "Verificar reporte generado en reports/"
                    )
                else:
                    self._add_check_result(
                        "database_optimization_execution",
                        "WARNING",
                        f"Advertencias en optimización de BD: {result.stderr}",
                        "Revisar configuración de base de datos"
                    )
            except subprocess.TimeoutExpired:
                self._add_check_result(
                    "database_optimization_execution",
                    "FAILED",
                    "Optimización de BD excedió tiempo límite",
                    "Verificar rendimiento de la base de datos"
                )
            except Exception as e:
                self._add_check_result(
                    "database_optimization_execution",
                    "FAILED",
                    f"Error ejecutando optimización: {e}",
                    "Verificar conexión a base de datos"
                )
        else:
            self._add_check_result(
                "database_optimization_script",
                "FAILED",
                "Script de optimización de BD no encontrado",
                "Crear scripts/database_optimization.py"
            )
    
    def _run_firewall_check(self, dry_run: bool):
        """Verificar configuración de firewall"""
        logger.info("🛡️ Verificando configuración de firewall...")
        
        firewall_script = self.project_root / "scripts" / "firewall_setup.py"
        
        if firewall_script.exists():
            try:
                cmd = [sys.executable, str(firewall_script), "--check"]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    self._add_check_result(
                        "firewall_check_execution",
                        "PASSED",
                        "Verificación de firewall ejecutada exitosamente",
                        "Firewall configurado correctamente"
                    )
                else:
                    self._add_check_result(
                        "firewall_check_execution",
                        "WARNING",
                        f"Advertencias en configuración de firewall: {result.stderr}",
                        "Revisar configuración de firewall del sistema"
                    )
            except subprocess.TimeoutExpired:
                self._add_check_result(
                    "firewall_check_execution",
                    "FAILED",
                    "Verificación de firewall excedió tiempo límite",
                    "Verificar estado del sistema"
                )
            except Exception as e:
                self._add_check_result(
                    "firewall_check_execution",
                    "FAILED",
                    f"Error verificando firewall: {e}",
                    "Verificar permisos de administrador"
                )
        else:
            self._add_check_result(
                "firewall_script",
                "FAILED",
                "Script de firewall no encontrado",
                "Crear scripts/firewall_setup.py"
            )
    
    def _run_container_hardening(self, dry_run: bool):
        """Ejecutar hardening de contenedores"""
        logger.info("🔒 Ejecutando hardening de contenedores...")
        
        hardening_script = self.project_root / "scripts" / "container_hardening.py"
        
        if hardening_script.exists():
            try:
                cmd = [sys.executable, str(hardening_script)]
                if dry_run:
                    cmd.append("--dry-run")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self._add_check_result(
                        "container_hardening_execution",
                        "PASSED",
                        "Hardening de contenedores ejecutado exitosamente",
                        "Verificar reporte generado en reports/"
                    )
                else:
                    self._add_check_result(
                        "container_hardening_execution",
                        "WARNING",
                        f"Advertencias en hardening: {result.stderr}",
                        "Revisar configuración de Docker"
                    )
            except subprocess.TimeoutExpired:
                self._add_check_result(
                    "container_hardening_execution",
                    "FAILED",
                    "Hardening excedió tiempo límite",
                    "Verificar estado de Docker"
                )
            except Exception as e:
                self._add_check_result(
                    "container_hardening_execution",
                    "FAILED",
                    f"Error ejecutando hardening: {e}",
                    "Verificar instalación de Docker"
                )
        else:
            self._add_check_result(
                "container_hardening_script",
                "FAILED",
                "Script de hardening no encontrado",
                "Crear scripts/container_hardening.py"
            )
    
    def _check_system_integration(self):
        """Verificar integración del sistema"""
        logger.info("🔗 Verificando integración del sistema...")
        
        # Verificar archivos de configuración
        config_files = [
            "docker-compose.yml",
            "nginx/nginx.conf",
            "monitoring/prometheus.yml",
            "monitoring/grafana/dashboards/gym-system-overview.json"
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                self._add_check_result(
                    f"config_file_{config_file.replace('/', '_')}",
                    "PASSED",
                    f"Archivo de configuración encontrado: {config_file}",
                    "Configuración del sistema completa"
                )
            else:
                self._add_check_result(
                    f"config_file_{config_file.replace('/', '_')}",
                    "FAILED",
                    f"Archivo de configuración faltante: {config_file}",
                    f"Crear archivo de configuración: {config_file}"
                )
        
        # Verificar directorios necesarios
        required_dirs = [
            "reports",
            "logs",
            "backups",
            "uploads"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                self._add_check_result(
                    f"directory_{dir_name}",
                    "PASSED",
                    f"Directorio encontrado: {dir_name}",
                    "Estructura del proyecto completa"
                )
            else:
                self._add_check_result(
                    f"directory_{dir_name}",
                    "WARNING",
                    f"Directorio faltante: {dir_name}",
                    f"Crear directorio: {dir_name}"
                )
        
        # Verificar variables de entorno
        env_files = [
            ".env.example",
            ".env.production.example"
        ]
        
        for env_file in env_files:
            file_path = self.project_root / env_file
            if file_path.exists():
                self._add_check_result(
                    f"env_file_{env_file}",
                    "PASSED",
                    f"Archivo de entorno encontrado: {env_file}",
                    "Configuración de entorno disponible"
                )
            else:
                self._add_check_result(
                    f"env_file_{env_file}",
                    "WARNING",
                    f"Archivo de entorno faltante: {env_file}",
                    f"Crear archivo de entorno: {env_file}"
                )
    
    def _generate_final_summary(self):
        """Generar resumen final"""
        logger.info("📊 Generando resumen final...")
        
        summary = self.results["summary"]
        total = summary["total_checks"]
        
        if total > 0:
            pass_rate = (summary["passed"] / total) * 100
            fail_rate = (summary["failed"] / total) * 100
            warning_rate = (summary["warnings"] / total) * 100
            
            # Determinar estado general
            if fail_rate == 0 and warning_rate <= 20:
                overall_status = "EXCELLENT"
                status_emoji = "🟢"
            elif fail_rate <= 10 and warning_rate <= 30:
                overall_status = "GOOD"
                status_emoji = "🟡"
            elif fail_rate <= 20:
                overall_status = "FAIR"
                status_emoji = "🟠"
            else:
                overall_status = "POOR"
                status_emoji = "🔴"
            
            self.results["overall_status"] = overall_status
            self.results["status_emoji"] = status_emoji
    
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
        elif status == "SKIPPED":
            self.results["summary"]["skipped"] += 1
        
        self.results["summary"]["total_checks"] += 1
    
    def save_report(self, output_file: str = None):
        """Guardar reporte de verificaciones"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"phase3_verification_{timestamp}.json"
        
        output_path = self.project_root / "reports" / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Reporte guardado en: {output_path}")
        return output_path
    
    def print_summary(self):
        """Imprimir resumen de verificaciones"""
        summary = self.results["summary"]
        overall_status = self.results.get("overall_status", "UNKNOWN")
        status_emoji = self.results.get("status_emoji", "⚪")
        
        print("\n" + "="*80)
        print(f"📊 RESUMEN DE VERIFICACIONES FASE 3 {status_emoji}")
        print("="*80)
        print(f"📋 Total de verificaciones: {summary['total_checks']}")
        print(f"✅ Exitosas: {summary['passed']}")
        print(f"❌ Fallidas: {summary['failed']}")
        print(f"⚠️  Advertencias: {summary['warnings']}")
        print(f"⏭️  Omitidas: {summary['skipped']}")
        print(f"🎯 Estado general: {overall_status}")
        print("="*80)
        
        # Mostrar verificaciones fallidas
        failed_checks = [
            (name, check) for name, check in self.results["checks"].items()
            if check["status"] == "FAILED"
        ]
        
        if failed_checks:
            print(f"\n❌ VERIFICACIONES FALLIDAS ({len(failed_checks)}):")
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
            print(f"\n⚠️  ADVERTENCIAS IMPORTANTES ({len(warning_checks)}):")
            for name, check in warning_checks[:10]:  # Solo las primeras 10
                print(f"  • {check['message']}")
                print(f"    Recomendación: {check['recommendation']}")
                print()
        
        # Mostrar estado general
        print(f"\n{status_emoji} ESTADO GENERAL: {overall_status}")
        
        if overall_status == "EXCELLENT":
            print("🎉 ¡Excelente! La Fase 3 está completamente implementada y lista.")
        elif overall_status == "GOOD":
            print("👍 Buen trabajo. Algunas mejoras menores recomendadas.")
        elif overall_status == "FAIR":
            print("⚠️  Estado aceptable. Se recomiendan correcciones.")
        else:
            print("🚨 Se requieren correcciones importantes antes de continuar.")
        
        print("\n" + "="*80)

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Verificador Maestro Fase 3 - Sistema de Gimnasio v6")
    parser.add_argument("--dry-run", action="store_true", help="Ejecutar en modo simulación")
    parser.add_argument("--output", help="Archivo de salida para el reporte")
    parser.add_argument("--quick", action="store_true", help="Ejecutar solo verificaciones rápidas")
    
    args = parser.parse_args()
    
    print("🚀 Verificador Maestro Fase 3 - Sistema de Gimnasio v6")
    print("🛡️ Seguridad y Optimización")
    print("="*80)
    
    checker = Phase3Checker()
    
    try:
        # Ejecutar verificaciones
        results = checker.run_all_checks(args.dry_run)
        
        # Imprimir resumen
        checker.print_summary()
        
        # Guardar reporte
        report_file = checker.save_report(args.output)
        
        print(f"\n📄 Reporte detallado guardado en: {report_file}")
        print("\n✅ Verificaciones completadas exitosamente")
        
        # Retornar código de salida basado en el estado general
        overall_status = results.get("overall_status", "UNKNOWN")
        if overall_status in ["EXCELLENT", "GOOD"]:
            sys.exit(0)
        elif overall_status == "FAIR":
            sys.exit(1)
        else:
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"Error durante las verificaciones: {e}")
        print(f"\n❌ Error durante las verificaciones: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 