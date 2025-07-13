"""
Inicialización del paquete de modelos
"""
# Este archivo permite importar todos los modelos desde app.models

from app.models.usuarios import Usuario, Rol, usuario_rol
from app.models.clases import Clase, DiaSemana, inscripcion_horario
from app.models.asistencias import Asistencia
from app.models.pagos import Pago, MetodoPago, EstadoPago, ConceptoPago, DetallePago
from app.models.rutinas import (
    Rutina, Ejercicio, ProgresoRutina, RutinaUsuario,
    TipoEjercicio, NivelDificultad, rutina_ejercicio,
    ConfiguracionEstilos
)
from app.models.logos import LogoPersonalizado
from app.models.multimedia import (
    MultimediaEjercicio, MultimediaRutina, AnotacionMultimedia, HistorialMultimedia,
    ColeccionMultimedia, ItemColeccionMultimedia,
    TipoMultimedia, EstadoMultimedia, CategoriaMultimedia
)
from app.models.empleados import (
    Empleado, AsistenciaEmpleado, Nomina,
    TipoContrato, EstadoEmpleado, Departamento
)
from app.models.tipos_cuota import TipoCuota

# Exportar Base para facilitar importaciones externas (Alembic, scripts)
from app.core.database import Base

# Lista de todos los modelos para facilitar las importaciones
__all__ = [
    # Usuarios
    'Usuario', 'Rol', 'usuario_rol',
    
    # Clases
    'Clase', 'DiaSemana', 'inscripcion_horario',
    
    # Asistencias
    'Asistencia',
    
    # Pagos
    'Pago', 'MetodoPago', 'EstadoPago', 'ConceptoPago', 'DetallePago',
    
    # Rutinas
    'Rutina', 'Ejercicio', 'ProgresoRutina', 'RutinaUsuario',
    'TipoEjercicio', 'NivelDificultad', 'rutina_ejercicio',
    'ConfiguracionEstilos',
    
    # Logos
    'LogoPersonalizado',
    
    # Multimedia  
    'MultimediaEjercicio', 'MultimediaRutina', 'AnotacionMultimedia', 'HistorialMultimedia',
    'ColeccionMultimedia', 'ItemColeccionMultimedia',
    'TipoMultimedia', 'EstadoMultimedia', 'CategoriaMultimedia',
    
    # Empleados
    'Empleado', 'AsistenciaEmpleado', 'Nomina',
    'TipoContrato', 'EstadoEmpleado', 'Departamento',
    
    # Tipos de cuota
    'TipoCuota',
    'Base'
]
