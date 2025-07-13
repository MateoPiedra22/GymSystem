"""
Fichero central para todas las enumeraciones de la base de datos.
"""
import enum

class TipoContrato(str, enum.Enum):
    TIEMPO_COMPLETO = "Tiempo Completo"
    MEDIO_TIEMPO = "Medio Tiempo"
    POR_HORAS = "Por Horas"
    TEMPORAL = "Temporal"
    PRACTICAS = "Prácticas"

class EstadoEmpleado(str, enum.Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"
    VACACIONES = "Vacaciones"
    BAJA_MEDICA = "Baja Médica"
    SUSPENDIDO = "Suspendido"

class Departamento(str, enum.Enum):
    ADMINISTRACION = "Administración"
    ENTRENAMIENTO = "Entrenamiento"
    RECEPCION = "Recepción"
    LIMPIEZA = "Limpieza"
    MANTENIMIENTO = "Mantenimiento"
    VENTAS = "Ventas"
    MARKETING = "Marketing"

class DiaSemana(str, enum.Enum):
    LUNES = "Lunes"
    MARTES = "Martes"
    MIERCOLES = "Miércoles"
    JUEVES = "Jueves"
    VIERNES = "Viernes"
    SABADO = "Sábado"
    DOMINGO = "Domingo"

class NivelDificultad(str, enum.Enum):
    PRINCIPIANTE = "Principiante"
    INTERMEDIO = "Intermedio"
    AVANZADO = "Avanzado"
    EXPERTO = "Experto"

class TipoEjercicio(str, enum.Enum):
    CARDIOVASCULAR = "Cardiovascular"
    FUERZA = "Fuerza"
    FLEXIBILIDAD = "Flexibilidad"
    EQUILIBRIO = "Equilibrio"
    RESISTENCIA = "Resistencia"
    OTRO = "Otro"

class MetodoPago(str, enum.Enum):
    EFECTIVO = "Efectivo"
    TRANSFERENCIA = "Transferencia"
    TARJETA_DEBITO = "Tarjeta Débito"
    TARJETA_CREDITO = "Tarjeta Crédito"
    PAYPAL = "PayPal"
    YAPE = "Yape"
    PLIN = "Plin"
    OTRO = "Otro"

class EstadoPago(str, enum.Enum):
    PENDIENTE = "Pendiente"
    PAGADO = "Pagado"
    PARCIAL = "Parcial"
    VENCIDO = "Vencido"
    CANCELADO = "Cancelado"
    REEMBOLSADO = "Reembolsado"

class ConceptoPago(str, enum.Enum):
    MEMBRESIA = "Membresía"
    CLASE_INDIVIDUAL = "Clase Individual"
    PRODUCTO = "Producto"
    SERVICIO_ADICIONAL = "Servicio Adicional"
    MULTA = "Multa"
    OTRO = "Otro"

class TipoMultimedia(str, enum.Enum):
    IMAGEN = "imagen"
    VIDEO = "video"
    GIF = "gif"
    AUDIO = "audio"
    DOCUMENTO = "documento"
    ANOTACION = "anotacion"

class EstadoMultimedia(str, enum.Enum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    ARCHIVADO = "archivado"

class CategoriaMultimedia(str, enum.Enum):
    DEMOSTRACION = "demostracion"
    TUTORIAL = "tutorial"
    TECNICA = "tecnica"
    VARIACION = "variacion"
    SEGURIDAD = "seguridad"
    MOTIVACIONAL = "motivacional"
    PROGRESO = "progreso" 