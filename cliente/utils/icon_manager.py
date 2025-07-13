"""
Sistema de gestión de íconos para el cliente desktop
Proporciona íconos consistentes en toda la aplicación
"""

import os
from typing import Dict, Optional
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QWidget

class IconManager:
    """
    Gestor centralizado de íconos para la aplicación desktop
    Proporciona íconos consistentes y gestión de temas
    """
    
    def __init__(self):
        self.icon_cache: Dict[str, QIcon] = {}
        self.icon_size = 24
        self.icon_color = QColor(60, 60, 60)  # Color por defecto
        self.theme = "light"  # light o dark
        
        # Definir colores por tema
        self.theme_colors = {
            "light": {
                "primary": QColor(59, 130, 246),      # Blue-500
                "success": QColor(16, 185, 129),      # Green-500
                "warning": QColor(245, 158, 11),      # Yellow-500
                "danger": QColor(239, 68, 68),        # Red-500
                "info": QColor(6, 182, 212),          # Cyan-500
                "secondary": QColor(107, 114, 128),   # Gray-500
                "text": QColor(60, 60, 60)            # Texto oscuro
            },
            "dark": {
                "primary": QColor(96, 165, 250),      # Blue-400
                "success": QColor(52, 211, 153),      # Green-400
                "warning": QColor(251, 191, 36),      # Yellow-400
                "danger": QColor(248, 113, 113),      # Red-400
                "info": QColor(34, 211, 238),         # Cyan-400
                "secondary": QColor(156, 163, 175),   # Gray-400
                "text": QColor(240, 240, 240)         # Texto claro
            }
        }
    
    def set_theme(self, theme: str):
        """Cambia el tema de íconos (light/dark)"""
        if theme in self.theme_colors:
            self.theme = theme
            self.icon_cache.clear()  # Limpiar caché para regenerar íconos
    
    def set_default_size(self, size: int):
        """Establece el tamaño por defecto de íconos"""
        self.icon_size = size
    
    def get_color(self, color_name: str) -> QColor:
        """Obtiene un color del tema actual"""
        return self.theme_colors[self.theme].get(color_name, self.theme_colors[self.theme]["text"])
    
    def create_text_icon(self, text: str, color_name: str = "text", size: Optional[int] = None) -> QIcon:
        """
        Crea un ícono usando texto (emoji o caracteres especiales)
        Útil para íconos simples cuando no tenemos archivos de imagen
        """
        icon_size = size or self.icon_size
        color = self.get_color(color_name)
        
        # Crear pixmap
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # Dibujar texto
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Configurar fuente
        font = painter.font()
        font.setPixelSize(int(icon_size * 0.7))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(color)
        
        # Dibujar texto centrado
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        
        return QIcon(pixmap)
    
    def create_colored_icon(self, icon_name: str, color_name: str = "text", size: Optional[int] = None) -> QIcon:
        """
        Crea un ícono coloreado desde un archivo base
        Si no existe el archivo, usa un ícono de texto como fallback
        """
        icon_size = size or self.icon_size
        cache_key = f"{icon_name}_{color_name}_{icon_size}_{self.theme}"
        
        # Verificar caché
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        # Intentar cargar desde archivo
        icon_path = os.path.join("assets", "icons", f"{icon_name}.svg")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            # Fallback: usar emoji/texto
            fallback_text = self.get_fallback_text(icon_name)
            icon = self.create_text_icon(fallback_text, color_name, size)
        
        # Colorear el ícono si es necesario
        if color_name != "text":
            icon = self.colorize_icon(icon, self.get_color(color_name), icon_size)
        
        # Guardar en caché
        self.icon_cache[cache_key] = icon
        return icon
    
    def colorize_icon(self, icon: QIcon, color: QColor, size: int) -> QIcon:
        """Coloriza un ícono con el color especificado"""
        pixmap = icon.pixmap(QSize(size, size))
        
        # Crear nuevo pixmap coloreado
        colored_pixmap = QPixmap(pixmap.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(colored_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar ícono original
        painter.drawPixmap(0, 0, pixmap)
        
        # Aplicar color
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), color)
        painter.end()
        
        return QIcon(colored_pixmap)
    
    def get_fallback_text(self, icon_name: str) -> str:
        """
        Mapeo de nombres de íconos a texto/emoji de fallback
        """
        fallback_map = {
            # Navegación
            "home": "🏠",
            "dashboard": "📊",
            "users": "👥",
            "calendar": "📅",
            "routines": "💪",
            "payments": "💳",
            "attendance": "✅",
            "settings": "⚙️",
            "reports": "📋",
            
            # Acciones
            "add": "➕",
            "edit": "✏️",
            "delete": "🗑️",
            "search": "🔍",
            "save": "💾",
            "copy": "📋",
            "share": "📤",
            "download": "⬇️",
            "upload": "⬆️",
            "refresh": "🔄",
            "view": "👁️",
            "hide": "🙈",
            "menu": "☰",
            "close": "❌",
            
            # Estados
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "loading": "⏳",
            "star": "⭐",
            "heart": "❤️",
            "shield": "🛡️",
            "award": "🏆",
            "trophy": "🏆",
            
            # Analytics
            "trend_up": "📈",
            "trend_down": "📉",
            "target": "🎯",
            "activity": "📊",
            "chart": "📊",
            
            # Fitness
            "dumbbell": "🏋️",
            "energy": "⚡",
            "weight": "⚖️",
            "timer": "⏰",
            "play": "▶️",
            "pause": "⏸️",
            "stop": "⏹️",
            
            # Finanzas
            "dollar": "💰",
            "card": "💳",
            "receipt": "🧾",
            "coins": "🪙",
            
            # Usuario
            "user": "👤",
            "profile": "👤",
            "notification": "🔔",
            "email": "📧",
            "phone": "📞",
            
            # Tiempo
            "clock": "🕐",
            "alarm": "⏰",
            "stopwatch": "⏱️",
            
            # Documentos
            "file": "📄",
            "folder": "📁",
            "archive": "📦",
            "print": "🖨️",
            
            # Configuración
            "config": "⚙️",
            "tools": "🔧",
            "palette": "🎨",
            "desktop": "🖥️",
            "mobile": "📱",
            
            # Conexión
            "wifi": "📶",
            "server": "🖥️",
            "database": "🗄️",
            "cloud": "☁️",
            
            # Tema
            "sun": "☀️",
            "moon": "🌙",
            
            # Utilidades
            "location": "📍",
            "camera": "📷",
            "key": "🔑",
            "tag": "🏷️",
            "help": "❓",
        }
        
        return fallback_map.get(icon_name, "⚪")  # Círculo blanco como último fallback
    
    # Métodos de conveniencia para obtener íconos específicos
    def navigation_icon(self, name: str, color: str = "primary") -> QIcon:
        """Obtiene íconos de navegación"""
        return self.create_colored_icon(name, color)
    
    def action_icon(self, name: str, color: str = "text") -> QIcon:
        """Obtiene íconos de acciones"""
        return self.create_colored_icon(name, color)
    
    def status_icon(self, name: str, color: str = "text") -> QIcon:
        """Obtiene íconos de estado"""
        color_map = {
            "success": "success",
            "error": "danger",
            "warning": "warning",
            "info": "info"
        }
        icon_color = color_map.get(name, color)
        return self.create_colored_icon(name, icon_color)
    
    def fitness_icon(self, name: str, color: str = "primary") -> QIcon:
        """Obtiene íconos relacionados con fitness"""
        return self.create_colored_icon(name, color)
    
    def finance_icon(self, name: str, color: str = "success") -> QIcon:
        """Obtiene íconos relacionados con finanzas"""
        return self.create_colored_icon(name, color)

# Instancia global del gestor de íconos
icon_manager = IconManager()

# Funciones de conveniencia para usar en toda la aplicación
def get_icon(name: str, color: str = "text", size: Optional[int] = None) -> QIcon:
    """Función de conveniencia para obtener cualquier ícono"""
    return icon_manager.create_colored_icon(name, color, size)

def get_navigation_icon(name: str) -> QIcon:
    """Obtiene íconos de navegación con color primario"""
    return icon_manager.navigation_icon(name)

def get_action_icon(name: str, color: str = "text") -> QIcon:
    """Obtiene íconos de acciones"""
    return icon_manager.action_icon(name, color)

def get_status_icon(name: str) -> QIcon:
    """Obtiene íconos de estado con colores apropiados"""
    return icon_manager.status_icon(name)

def set_icon_theme(theme: str):
    """Cambia el tema global de íconos"""
    icon_manager.set_theme(theme)

def set_icon_size(size: int):
    """Establece el tamaño por defecto de íconos"""
    icon_manager.set_default_size(size) 