#!/usr/bin/env python3
"""
Script Maestro - Fase 4: Testing y QA
Ejecuta todos los tests de la Fase 4 de manera automatizada
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
import threading
import queue

class TestRunner:
    """Ejecutor principal de tests de la Fase 4"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = {}
        self.start_time = None
        self.end_time = None
        self.report_file = f"phase4_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
    def log(self, message: str, level: str = "INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
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
    
    def run_backend_tests(self) -> Dict[str, Any]:
        """Ejecutar tests del backend"""
        self.log("🧪 Iniciando tests del backend...")
        
        backend_dir = Path("backend")
        if not backend_dir.exists():
            return {"success": False, "error": "Directorio backend no encontrado"}
        
        results = {}
        
        # Tests de seguridad
        self.log("🔒 Ejecutando tests de seguridad...")
        results["security"] = self.run_command(
            ["python", "-m", "pytest", "tests/test_security.py", "-v", "--tb=short"],
            cwd=str(backend_dir)
        )
        
        # Tests de performance
        self.log("⚡ Ejecutando tests de performance...")
        results["performance"] = self.run_command(
            ["python", "-m", "pytest", "tests/test_performance.py", "-v", "--tb=short"],
            cwd=str(backend_dir)
        )
        
        # Tests de integración
        self.log("🔗 Ejecutando tests de integración...")
        results["integration"] = self.run_command(
            ["python", "-m", "pytest", "tests/test_integration.py", "-v", "--tb=short"],
            cwd=str(backend_dir)
        )
        
        # Tests de usabilidad
        self.log("👥 Ejecutando tests de usabilidad...")
        results["usability"] = self.run_command(
            ["python", "-m", "pytest", "tests/test_usability.py", "-v", "--tb=short"],
            cwd=str(backend_dir)
        )
        
        # Tests de carga
        self.log("📊 Ejecutando tests de carga...")
        results["load"] = self.run_command(
            ["python", "-m", "pytest", "tests/test_load.py", "-v", "--tb=short"],
            cwd=str(backend_dir),
            timeout=600  # 10 minutos para tests de carga
        )
        
        # Análisis de cobertura
        self.log("📈 Generando reporte de cobertura...")
        results["coverage"] = self.run_command(
            ["python", "-m", "pytest", "--cov=app", "--cov-report=html", "--cov-report=xml"],
            cwd=str(backend_dir)
        )
        
        return results
    
    def run_frontend_tests(self) -> Dict[str, Any]:
        """Ejecutar tests del frontend"""
        self.log("🌐 Iniciando tests del frontend...")
        
        web_dir = Path("web")
        if not web_dir.exists():
            return {"success": False, "error": "Directorio web no encontrado"}
        
        results = {}
        
        # Verificar dependencias
        self.log("📦 Verificando dependencias...")
        results["dependencies"] = self.run_command(
            ["npm", "ci"],
            cwd=str(web_dir)
        )
        
        if not results["dependencies"]["success"]:
            return results
        
        # Linting
        self.log("🔍 Ejecutando linting...")
        results["linting"] = self.run_command(
            ["npm", "run", "lint"],
            cwd=str(web_dir)
        )
        
        # Tests unitarios
        self.log("🧪 Ejecutando tests unitarios...")
        results["unit_tests"] = self.run_command(
            ["npm", "test", "--", "--coverage", "--watchAll=false"],
            cwd=str(web_dir)
        )
        
        # Build de producción
        self.log("🏗️ Ejecutando build de producción...")
        results["build"] = self.run_command(
            ["npm", "run", "build"],
            cwd=str(web_dir)
        )
        
        return results
    
    def run_security_audit(self) -> Dict[str, Any]:
        """Ejecutar auditoría de seguridad"""
        self.log("🔒 Iniciando auditoría de seguridad...")
        
        results = {}
        
        # Ejecutar script de auditoría de seguridad
        security_script = Path("scripts/security_audit.py")
        if security_script.exists():
            results["security_audit"] = self.run_command(
                ["python", str(security_script), "--ci-mode"]
            )
        else:
            results["security_audit"] = {"success": False, "error": "Script de auditoría no encontrado"}
        
        # Análisis de dependencias con safety
        self.log("🔍 Analizando vulnerabilidades en dependencias...")
        results["dependency_scan"] = self.run_command(
            ["python", "-m", "safety", "check", "--json"]
        )
        
        # Análisis de código con bandit
        self.log("🔍 Analizando código con Bandit...")
        results["code_analysis"] = self.run_command(
            ["python", "-m", "bandit", "-r", "backend/", "-f", "json"]
        )
        
        return results
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Ejecutar tests de performance"""
        self.log("⚡ Iniciando tests de performance...")
        
        results = {}
        
        # Tests de carga con Locust (si está disponible)
        try:
            results["load_test"] = self.run_command(
                ["python", "-m", "locust", "--headless", "--users", "10", "--spawn-rate", "2", "--run-time", "60s"]
            )
        except:
            results["load_test"] = {"success": False, "error": "Locust no disponible"}
        
        # Tests de stress
        self.log("📊 Ejecutando tests de stress...")
        backend_dir = Path("backend")
        if backend_dir.exists():
            results["stress_test"] = self.run_command(
                ["python", "-m", "pytest", "tests/test_load.py::TestStressTesting", "-v"],
                cwd=str(backend_dir),
                timeout=300
            )
        
        return results
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Ejecutar tests de integración completa"""
        self.log("🔗 Iniciando tests de integración completa...")
        
        results = {}
        
        # Verificar que Docker está disponible
        docker_check = self.run_command(["docker", "--version"])
        if not docker_check["success"]:
            return {"success": False, "error": "Docker no está disponible"}
        
        # Levantar servicios con Docker Compose
        self.log("🐳 Levantando servicios con Docker Compose...")
        results["docker_compose"] = self.run_command(
            ["docker-compose", "up", "-d", "postgres", "redis"]
        )
        
        if results["docker_compose"]["success"]:
            # Esperar a que los servicios estén listos
            self.log("⏳ Esperando a que los servicios estén listos...")
            time.sleep(30)
            
            # Ejecutar health checks
            self.log("🏥 Ejecutando health checks...")
            health_script = Path("scripts/healthcheck.py")
            if health_script.exists():
                results["health_checks"] = self.run_command(
                    ["python", str(health_script), "--all-services"]
                )
            
            # Tests de integración del sistema
            self.log("🧪 Ejecutando tests de integración del sistema...")
            backend_dir = Path("backend")
            if backend_dir.exists():
                results["system_integration"] = self.run_command(
                    ["python", "-m", "pytest", "tests/test_integration.py", "-v"],
                    cwd=str(backend_dir)
                )
            
            # Detener servicios
            self.log("🛑 Deteniendo servicios...")
            self.run_command(["docker-compose", "down"])
        
        return results
    
    def run_quality_checks(self) -> Dict[str, Any]:
        """Ejecutar verificaciones de calidad"""
        self.log("📊 Iniciando verificaciones de calidad...")
        
        results = {}
        
        # Verificar formato de código
        self.log("🎨 Verificando formato de código...")
        backend_dir = Path("backend")
        if backend_dir.exists():
            results["code_format"] = self.run_command(
                ["python", "-m", "black", "--check", "--diff", "."],
                cwd=str(backend_dir)
            )
        
        # Verificar tipos
        self.log("🔍 Verificando tipos...")
        if backend_dir.exists():
            results["type_check"] = self.run_command(
                ["python", "-m", "mypy", "."],
                cwd=str(backend_dir)
            )
        
        # Verificar complejidad ciclomática
        self.log("📈 Analizando complejidad...")
        if backend_dir.exists():
            results["complexity"] = self.run_command(
                ["python", "-m", "radon", "cc", ".", "-a"],
                cwd=str(backend_dir)
            )
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generar reporte completo"""
        self.log("📋 Generando reporte completo...")
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        # Contar resultados
        for category, results in self.results.items():
            if isinstance(results, dict):
                for test_name, result in results.items():
                    if isinstance(result, dict) and "success" in result:
                        total_tests += 1
                        if result["success"]:
                            passed_tests += 1
                        else:
                            failed_tests += 1
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "duration": self.end_time - self.start_time if self.end_time and self.start_time else 0,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "results": self.results,
            "config": self.config
        }
        
        # Guardar reporte
        with open(self.report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def print_summary(self, report: Dict[str, Any]):
        """Imprimir resumen de resultados"""
        print("\n" + "="*80)
        print("📊 RESUMEN DE TESTS - FASE 4: TESTING Y QA")
        print("="*80)
        
        summary = report["summary"]
        print(f"⏱️  Duración total: {report['duration']:.2f} segundos")
        print(f"🧪 Total de tests: {summary['total_tests']}")
        print(f"✅ Tests exitosos: {summary['passed_tests']}")
        print(f"❌ Tests fallidos: {summary['failed_tests']}")
        print(f"📈 Tasa de éxito: {summary['success_rate']:.1f}%")
        
        print("\n📋 Resultados por categoría:")
        print("-" * 50)
        
        for category, results in self.results.items():
            if isinstance(results, dict):
                category_passed = 0
                category_total = 0
                
                for test_name, result in results.items():
                    if isinstance(result, dict) and "success" in result:
                        category_total += 1
                        if result["success"]:
                            category_passed += 1
                
                if category_total > 0:
                    success_rate = (category_passed / category_total) * 100
                    status = "✅" if success_rate == 100 else "⚠️" if success_rate >= 80 else "❌"
                    print(f"{status} {category.upper()}: {category_passed}/{category_total} ({success_rate:.1f}%)")
        
        print("\n📁 Reporte guardado en:", self.report_file)
        print("="*80)
    
    def run_all_tests(self) -> bool:
        """Ejecutar todos los tests"""
        self.start_time = time.time()
        self.log("🚀 Iniciando ejecución completa de tests - Fase 4")
        
        try:
            # Ejecutar tests del backend
            self.results["backend"] = self.run_backend_tests()
            
            # Ejecutar tests del frontend
            self.results["frontend"] = self.run_frontend_tests()
            
            # Ejecutar auditoría de seguridad
            self.results["security"] = self.run_security_audit()
            
            # Ejecutar tests de performance
            self.results["performance"] = self.run_performance_tests()
            
            # Ejecutar tests de integración
            self.results["integration"] = self.run_integration_tests()
            
            # Ejecutar verificaciones de calidad
            self.results["quality"] = self.run_quality_checks()
            
        except KeyboardInterrupt:
            self.log("⏹️ Ejecución interrumpida por el usuario", "WARNING")
            return False
        except Exception as e:
            self.log(f"❌ Error durante la ejecución: {e}", "ERROR")
            return False
        finally:
            self.end_time = time.time()
        
        # Generar reporte
        report = self.generate_report()
        self.print_summary(report)
        
        # Determinar éxito general
        summary = report["summary"]
        success = summary["success_rate"] >= 90  # 90% de éxito mínimo
        
        if success:
            self.log("🎉 Todos los tests completados exitosamente!", "SUCCESS")
        else:
            self.log("⚠️ Algunos tests fallaron. Revisar reporte para detalles.", "WARNING")
        
        return success

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Ejecutor de tests - Fase 4: Testing y QA")
    parser.add_argument("--config", type=str, default="phase4_config.json", help="Archivo de configuración")
    parser.add_argument("--category", type=str, choices=["backend", "frontend", "security", "performance", "integration", "quality"], help="Ejecutar solo una categoría")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verbose")
    parser.add_argument("--timeout", type=int, default=1800, help="Timeout en segundos (default: 1800)")
    
    args = parser.parse_args()
    
    # Cargar configuración
    config = {
        "verbose": args.verbose,
        "timeout": args.timeout,
        "categories": ["backend", "frontend", "security", "performance", "integration", "quality"]
    }
    
    if args.category:
        config["categories"] = [args.category]
    
    if os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            config.update(json.load(f))
    
    # Crear ejecutor
    runner = TestRunner(config)
    
    # Ejecutar tests
    success = runner.run_all_tests()
    
    # Código de salida
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 