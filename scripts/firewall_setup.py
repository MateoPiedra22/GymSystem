#!/usr/bin/env python3
"""
Script de Configuración de Firewall - Sistema de Gimnasio v6
Configura firewall y reglas de seguridad de red
"""

import os
import sys
import subprocess
import json
import platform
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

class FirewallManager:
    """Gestor de firewall para el sistema"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system": self.system,
            "rules": {},
            "status": {},
            "summary": {
                "total_rules": 0,
                "applied": 0,
                "failed": 0
            }
        }
        
        # Configuración de puertos del sistema
        self.ports_config = {
            "web": 80,
            "web_ssl": 443,
            "backend": 8000,
            "database": 5432,
            "redis": 6379,
            "prometheus": 9090,
            "grafana": 3000,
            "ssh": 22
        }
    
    def setup_firewall(self, dry_run: bool = False) -> Dict[str, Any]:
        """Configurar firewall completo"""
        logger.info(f"🛡️ Configurando firewall para {self.system}...")
        
        if self.system == "linux":
            return self._setup_linux_firewall(dry_run)
        elif self.system == "windows":
            return self._setup_windows_firewall(dry_run)
        elif self.system == "darwin":
            return self._setup_macos_firewall(dry_run)
        else:
            logger.error(f"Sistema operativo no soportado: {self.system}")
            return self.results
    
    def _setup_linux_firewall(self, dry_run: bool) -> Dict[str, Any]:
        """Configurar firewall en Linux (iptables/ufw)"""
        logger.info("🐧 Configurando firewall Linux...")
        
        # Detectar tipo de firewall
        if self._check_command("ufw"):
            return self._setup_ufw_firewall(dry_run)
        elif self._check_command("iptables"):
            return self._setup_iptables_firewall(dry_run)
        elif self._check_command("firewalld"):
            return self._setup_firewalld_firewall(dry_run)
        else:
            logger.error("No se encontró firewall compatible (ufw, iptables, firewalld)")
            return self.results
    
    def _setup_ufw_firewall(self, dry_run: bool) -> Dict[str, Any]:
        """Configurar UFW (Uncomplicated Firewall)"""
        logger.info("🔥 Configurando UFW...")
        
        rules = [
            # Reglas básicas
            ("ufw_default_incoming", "ufw default deny incoming"),
            ("ufw_default_outgoing", "ufw default allow outgoing"),
            
            # Puertos del sistema
            ("ufw_ssh", "ufw allow 22/tcp"),
            ("ufw_web", "ufw allow 80/tcp"),
            ("ufw_web_ssl", "ufw allow 443/tcp"),
            ("ufw_backend", "ufw allow 8000/tcp"),
            ("ufw_database", "ufw allow 5432/tcp"),
            ("ufw_redis", "ufw allow 6379/tcp"),
            ("ufw_prometheus", "ufw allow 9090/tcp"),
            ("ufw_grafana", "ufw allow 3000/tcp"),
            
            # Reglas de seguridad adicionales
            ("ufw_limit_ssh", "ufw limit 22/tcp"),
            ("ufw_deny_common_ports", "ufw deny 23/tcp"),  # Telnet
            ("ufw_deny_common_ports", "ufw deny 21/tcp"),  # FTP
            ("ufw_deny_common_ports", "ufw deny 3389/tcp"),  # RDP
        ]
        
        if not dry_run:
            # Habilitar UFW
            self._execute_command("ufw --force enable")
        
        for rule_name, rule_command in rules:
            if not dry_run:
                success = self._execute_command(rule_command)
                if success:
                    self._add_rule_result(rule_name, "APPLIED", rule_command)
                else:
                    self._add_rule_result(rule_name, "FAILED", rule_command)
            else:
                self._add_rule_result(rule_name, "DRY_RUN", rule_command)
        
        return self.results
    
    def _setup_iptables_firewall(self, dry_run: bool) -> Dict[str, Any]:
        """Configurar iptables"""
        logger.info("🔧 Configurando iptables...")
        
        rules = [
            # Flush reglas existentes
            ("iptables_flush", "iptables -F"),
            ("iptables_flush_nat", "iptables -t nat -F"),
            ("iptables_flush_mangle", "iptables -t mangle -F"),
            
            # Políticas por defecto
            ("iptables_policy_input", "iptables -P INPUT DROP"),
            ("iptables_policy_forward", "iptables -P FORWARD DROP"),
            ("iptables_policy_output", "iptables -P OUTPUT ACCEPT"),
            
            # Permitir tráfico local
            ("iptables_localhost", "iptables -A INPUT -i lo -j ACCEPT"),
            ("iptables_established", "iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT"),
            
            # Puertos del sistema
            ("iptables_ssh", "iptables -A INPUT -p tcp --dport 22 -j ACCEPT"),
            ("iptables_web", "iptables -A INPUT -p tcp --dport 80 -j ACCEPT"),
            ("iptables_web_ssl", "iptables -A INPUT -p tcp --dport 443 -j ACCEPT"),
            ("iptables_backend", "iptables -A INPUT -p tcp --dport 8000 -j ACCEPT"),
            ("iptables_database", "iptables -A INPUT -p tcp --dport 5432 -j ACCEPT"),
            ("iptables_redis", "iptables -A INPUT -p tcp --dport 6379 -j ACCEPT"),
            ("iptables_prometheus", "iptables -A INPUT -p tcp --dport 9090 -j ACCEPT"),
            ("iptables_grafana", "iptables -A INPUT -p tcp --dport 3000 -j ACCEPT"),
            
            # Protección contra ataques
            ("iptables_syn_flood", "iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT"),
            ("iptables_icmp", "iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT"),
        ]
        
        for rule_name, rule_command in rules:
            if not dry_run:
                success = self._execute_command(rule_command)
                if success:
                    self._add_rule_result(rule_name, "APPLIED", rule_command)
                else:
                    self._add_rule_result(rule_name, "FAILED", rule_command)
            else:
                self._add_rule_result(rule_name, "DRY_RUN", rule_command)
        
        # Guardar reglas
        if not dry_run:
            self._save_iptables_rules()
        
        return self.results
    
    def _setup_firewalld_firewall(self, dry_run: bool) -> Dict[str, Any]:
        """Configurar firewalld"""
        logger.info("🔥 Configurando firewalld...")
        
        commands = [
            ("firewalld_start", "systemctl start firewalld"),
            ("firewalld_enable", "systemctl enable firewalld"),
            ("firewalld_zone_public", "firewall-cmd --set-default-zone=public"),
            ("firewalld_remove_services", "firewall-cmd --remove-service=dhcpv6-client --permanent"),
            ("firewalld_add_ssh", "firewall-cmd --add-service=ssh --permanent"),
            ("firewalld_add_http", "firewall-cmd --add-service=http --permanent"),
            ("firewalld_add_https", "firewall-cmd --add-service=https --permanent"),
            ("firewalld_add_port_backend", "firewall-cmd --add-port=8000/tcp --permanent"),
            ("firewalld_add_port_database", "firewall-cmd --add-port=5432/tcp --permanent"),
            ("firewalld_add_port_redis", "firewall-cmd --add-port=6379/tcp --permanent"),
            ("firewalld_add_port_prometheus", "firewall-cmd --add-port=9090/tcp --permanent"),
            ("firewalld_add_port_grafana", "firewall-cmd --add-port=3000/tcp --permanent"),
            ("firewalld_reload", "firewall-cmd --reload"),
        ]
        
        for cmd_name, cmd in commands:
            if not dry_run:
                success = self._execute_command(cmd)
                if success:
                    self._add_rule_result(cmd_name, "APPLIED", cmd)
                else:
                    self._add_rule_result(cmd_name, "FAILED", cmd)
            else:
                self._add_rule_result(cmd_name, "DRY_RUN", cmd)
        
        return self.results
    
    def _setup_windows_firewall(self, dry_run: bool) -> Dict[str, Any]:
        """Configurar firewall de Windows"""
        logger.info("🪟 Configurando firewall de Windows...")
        
        rules = [
            # Habilitar firewall
            ("win_firewall_enable", "netsh advfirewall set allprofiles state on"),
            
            # Reglas de entrada
            ("win_rule_ssh_in", "netsh advfirewall firewall add rule name=\"SSH In\" dir=in action=allow protocol=TCP localport=22"),
            ("win_rule_web_in", "netsh advfirewall firewall add rule name=\"HTTP In\" dir=in action=allow protocol=TCP localport=80"),
            ("win_rule_web_ssl_in", "netsh advfirewall firewall add rule name=\"HTTPS In\" dir=in action=allow protocol=TCP localport=443"),
            ("win_rule_backend_in", "netsh advfirewall firewall add rule name=\"Backend In\" dir=in action=allow protocol=TCP localport=8000"),
            ("win_rule_database_in", "netsh advfirewall firewall add rule name=\"Database In\" dir=in action=allow protocol=TCP localport=5432"),
            ("win_rule_redis_in", "netsh advfirewall firewall add rule name=\"Redis In\" dir=in action=allow protocol=TCP localport=6379"),
            ("win_rule_prometheus_in", "netsh advfirewall firewall add rule name=\"Prometheus In\" dir=in action=allow protocol=TCP localport=9090"),
            ("win_rule_grafana_in", "netsh advfirewall firewall add rule name=\"Grafana In\" dir=in action=allow protocol=TCP localport=3000"),
            
            # Reglas de salida
            ("win_rule_all_out", "netsh advfirewall firewall add rule name=\"All Out\" dir=out action=allow"),
            
            # Bloquear puertos peligrosos
            ("win_block_telnet", "netsh advfirewall firewall add rule name=\"Block Telnet\" dir=in action=block protocol=TCP localport=23"),
            ("win_block_ftp", "netsh advfirewall firewall add rule name=\"Block FTP\" dir=in action=block protocol=TCP localport=21"),
            ("win_block_rdp", "netsh advfirewall firewall add rule name=\"Block RDP\" dir=in action=block protocol=TCP localport=3389"),
        ]
        
        for rule_name, rule_command in rules:
            if not dry_run:
                success = self._execute_command(rule_command)
                if success:
                    self._add_rule_result(rule_name, "APPLIED", rule_command)
                else:
                    self._add_rule_result(rule_name, "FAILED", rule_command)
            else:
                self._add_rule_result(rule_name, "DRY_RUN", rule_command)
        
        return self.results
    
    def _setup_macos_firewall(self, dry_run: bool) -> Dict[str, Any]:
        """Configurar firewall de macOS"""
        logger.info("🍎 Configurando firewall de macOS...")
        
        rules = [
            # Habilitar firewall
            ("macos_firewall_enable", "/usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on"),
            
            # Configurar reglas para aplicaciones
            ("macos_allow_signed", "/usr/libexec/ApplicationFirewall/socketfilterfw --setallowsigned on"),
            ("macos_allow_signed_strict", "/usr/libexec/ApplicationFirewall/socketfilterfw --setallowsignedstrict on"),
            
            # Agregar aplicaciones al firewall
            ("macos_add_docker", "/usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/Docker.app"),
            ("macos_add_nginx", "/usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/nginx"),
        ]
        
        for rule_name, rule_command in rules:
            if not dry_run:
                success = self._execute_command(rule_command)
                if success:
                    self._add_rule_result(rule_name, "APPLIED", rule_command)
                else:
                    self._add_rule_result(rule_name, "FAILED", rule_command)
            else:
                self._add_rule_result(rule_name, "DRY_RUN", rule_command)
        
        return self.results
    
    def check_firewall_status(self) -> Dict[str, Any]:
        """Verificar estado del firewall"""
        logger.info("🔍 Verificando estado del firewall...")
        
        if self.system == "linux":
            return self._check_linux_firewall_status()
        elif self.system == "windows":
            return self._check_windows_firewall_status()
        elif self.system == "darwin":
            return self._check_macos_firewall_status()
        
        return {}
    
    def _check_linux_firewall_status(self) -> Dict[str, Any]:
        """Verificar estado del firewall en Linux"""
        status = {}
        
        # Verificar UFW
        if self._check_command("ufw"):
            result = self._execute_command("ufw status verbose", capture_output=True)
            status["ufw"] = {
                "available": True,
                "status": result
            }
        
        # Verificar iptables
        if self._check_command("iptables"):
            result = self._execute_command("iptables -L -n", capture_output=True)
            status["iptables"] = {
                "available": True,
                "rules": result
            }
        
        # Verificar firewalld
        if self._check_command("firewall-cmd"):
            result = self._execute_command("firewall-cmd --state", capture_output=True)
            status["firewalld"] = {
                "available": True,
                "state": result
            }
        
        return status
    
    def _check_windows_firewall_status(self) -> Dict[str, Any]:
        """Verificar estado del firewall en Windows"""
        status = {}
        
        # Verificar estado del firewall
        result = self._execute_command("netsh advfirewall show allprofiles", capture_output=True)
        status["windows_firewall"] = {
            "profiles": result
        }
        
        return status
    
    def _check_macos_firewall_status(self) -> Dict[str, Any]:
        """Verificar estado del firewall en macOS"""
        status = {}
        
        # Verificar estado del firewall
        result = self._execute_command("/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate", capture_output=True)
        status["macos_firewall"] = {
            "state": result
        }
        
        return status
    
    def _check_command(self, command: str) -> bool:
        """Verificar si un comando está disponible"""
        try:
            subprocess.run([command, "--version"], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False
    
    def _execute_command(self, command: str, capture_output: bool = False) -> bool:
        """Ejecutar comando del sistema"""
        try:
            if capture_output:
                result = subprocess.run(command.split(), capture_output=True, text=True, timeout=30)
                return result.stdout
            else:
                result = subprocess.run(command.split(), timeout=30)
                return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError) as e:
            logger.error(f"Error ejecutando comando '{command}': {e}")
            return False
    
    def _save_iptables_rules(self):
        """Guardar reglas de iptables"""
        try:
            if self._check_command("iptables-save"):
                self._execute_command("iptables-save > /etc/iptables/rules.v4")
            elif self._check_command("service"):
                self._execute_command("service iptables save")
        except Exception as e:
            logger.error(f"Error guardando reglas de iptables: {e}")
    
    def _add_rule_result(self, rule_name: str, status: str, command: str):
        """Agregar resultado de regla"""
        self.results["rules"][rule_name] = {
            "status": status,
            "command": command,
            "timestamp": datetime.now().isoformat()
        }
        
        if status == "APPLIED":
            self.results["summary"]["applied"] += 1
        elif status == "FAILED":
            self.results["summary"]["failed"] += 1
        
        self.results["summary"]["total_rules"] += 1
    
    def save_report(self, output_file: str = None):
        """Guardar reporte de configuración"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"firewall_setup_{timestamp}.json"
        
        output_path = Path(__file__).parent.parent / "reports" / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Reporte guardado en: {output_path}")
        return output_path
    
    def print_summary(self):
        """Imprimir resumen de la configuración"""
        summary = self.results["summary"]
        
        print("\n" + "="*60)
        print("🛡️ RESUMEN DE CONFIGURACIÓN DE FIREWALL")
        print("="*60)
        print(f"🖥️  Sistema: {self.results['system']}")
        print(f"📊 Total de reglas: {summary['total_rules']}")
        print(f"✅ Aplicadas: {summary['applied']}")
        print(f"❌ Fallidas: {summary['failed']}")
        print("="*60)
        
        # Mostrar reglas aplicadas
        applied_rules = [
            (name, rule) for name, rule in self.results["rules"].items()
            if rule["status"] == "APPLIED"
        ]
        
        if applied_rules:
            print("\n✅ REGLAS APLICADAS:")
            for name, rule in applied_rules:
                print(f"  • {name}: {rule['command']}")
        
        # Mostrar reglas fallidas
        failed_rules = [
            (name, rule) for name, rule in self.results["rules"].items()
            if rule["status"] == "FAILED"
        ]
        
        if failed_rules:
            print("\n❌ REGLAS FALLIDAS:")
            for name, rule in failed_rules:
                print(f"  • {name}: {rule['command']}")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Configurador de Firewall - Sistema de Gimnasio v6")
    parser.add_argument("--dry-run", action="store_true", help="Simular configuración sin aplicar cambios")
    parser.add_argument("--check", action="store_true", help="Solo verificar estado del firewall")
    parser.add_argument("--output", help="Archivo de salida para el reporte")
    
    args = parser.parse_args()
    
    print("🛡️ Configurador de Firewall - Sistema de Gimnasio v6")
    print("="*60)
    
    firewall_manager = FirewallManager()
    
    try:
        if args.check:
            # Solo verificar estado
            status = firewall_manager.check_firewall_status()
            print("🔍 Estado del firewall:")
            print(json.dumps(status, indent=2))
        else:
            # Configurar firewall
            results = firewall_manager.setup_firewall(args.dry_run)
            
            # Imprimir resumen
            firewall_manager.print_summary()
            
            # Guardar reporte
            report_file = firewall_manager.save_report(args.output)
            
            print(f"\n📄 Reporte guardado en: {report_file}")
            print("\n✅ Configuración completada exitosamente")
        
        # Retornar código de salida
        if args.dry_run:
            sys.exit(0)
        elif firewall_manager.results["summary"]["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Error durante la configuración: {e}")
        print(f"\n❌ Error durante la configuración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 