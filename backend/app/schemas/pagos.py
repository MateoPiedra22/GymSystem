# /backend/app/schemas/pagos.py
"""
Esquemas Pydantic para la validación y serialización de datos de pagos
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

# Importar enums del modelo
from app.models.pagos import MetodoPago, EstadoPago, ConceptoPago

class PagoBase(BaseModel):
    """Esquema base para pagos"""
    monto: float = Field(..., gt=0, description="Monto del pago")
    fecha_pago: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora del pago")
    fecha_vencimiento: Optional[date] = Field(None, description="Fecha de vencimiento si aplica")
    metodo_pago: MetodoPago = Field(..., description="Método de pago utilizado")
    concepto: ConceptoPago = Field(..., description="Concepto del pago")
    usuario_id: str = Field(..., description="ID del usuario que realiza el pago")
    tipo_cuota_id: Optional[str] = Field(None, description="ID del tipo de cuota si es membresía")
    empleado_registro_id: Optional[str] = Field(None, description="ID del empleado que registra")
    descripcion: Optional[str] = Field(None, max_length=500)
    referencia: Optional[str] = Field(None, max_length=100, description="Número de referencia")
    comprobante_url: Optional[str] = Field(None, max_length=255, description="URL del comprobante")
    fecha_inicio_membresia: Optional[date] = None
    fecha_fin_membresia: Optional[date] = None
    descuento_monto: float = Field(0.0, ge=0)
    descuento_porcentaje: float = Field(0.0, ge=0, le=100)
    impuesto_monto: float = Field(0.0, ge=0)
    notas: Optional[str] = None
    
    @validator('monto')
    def monto_debe_ser_positivo(cls, v):
        """Validar que el monto sea positivo"""
        if v <= 0:
            raise ValueError('El monto debe ser mayor que cero')
        return round(v, 2)
    
    @validator('fecha_fin_membresia')
    def validar_fechas_membresia(cls, v, values):
        """Validar que la fecha fin sea posterior a la fecha inicio"""
        if v and 'fecha_inicio_membresia' in values and values['fecha_inicio_membresia']:
            if v <= values['fecha_inicio_membresia']:
                raise ValueError('La fecha fin debe ser posterior a la fecha inicio')
        return v

class PagoCreate(PagoBase):
    """Esquema para crear un nuevo pago"""
    detalles: Optional[List[Dict[str, Any]]] = Field(None, description="Detalles del pago")
    
    @validator('tipo_cuota_id')
    def validar_tipo_cuota_membresia(cls, v, values):
        """Si es pago de membresía, debe tener tipo de cuota"""
        if 'concepto' in values and values['concepto'] == ConceptoPago.MEMBRESIA:
            if not v:
                raise ValueError('Los pagos de membresía deben especificar el tipo de cuota')
        return v

class PagoUpdate(BaseModel):
    """Esquema para actualizar un pago existente"""
    monto_pagado: Optional[float] = Field(None, ge=0)
    estado: Optional[EstadoPago] = None
    metodo_pago: Optional[MetodoPago] = None
    referencia: Optional[str] = Field(None, max_length=100)
    comprobante_url: Optional[str] = Field(None, max_length=255)
    notas: Optional[str] = None
    motivo_cancelacion: Optional[str] = None

class PagoInDB(PagoBase):
    """Esquema para pago en base de datos"""
    id: str
    numero_recibo: str
    estado: EstadoPago = EstadoPago.PENDIENTE
    monto_pagado: float = 0.0
    monto_final: float
    dias_mora: int = 0
    cargo_mora: float = 0.0
    motivo_cancelacion: Optional[str] = None
    creado_por: Optional[str] = None
    modificado_por: Optional[str] = None
    fecha_creacion: datetime
    ultima_modificacion: datetime
    sync_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class PagoOut(PagoInDB):
    """Esquema para respuesta de pago"""
    usuario: Optional[Dict[str, Any]] = None
    tipo_cuota: Optional[Dict[str, Any]] = None
    empleado_registro: Optional[Dict[str, Any]] = None
    detalles_pago: Optional[List[Dict[str, Any]]] = []
    saldo_pendiente: float = Field(..., description="Saldo pendiente del pago")
    
    @validator('saldo_pendiente', pre=True, always=True)
    def calcular_saldo_pendiente(cls, v, values):
        """Calcula el saldo pendiente"""
        if 'monto_final' in values and 'monto_pagado' in values:
            return values['monto_final'] - values['monto_pagado']
        return 0

class PagoList(BaseModel):
    """Esquema para lista de pagos"""
    total: int
    items: List[PagoOut]
    total_monto: float
    total_pagado: float
    total_pendiente: float

class PagoEstadistica(BaseModel):
    """Esquema para estadísticas de pagos"""
    total_pagos: int
    monto_total: float
    monto_pagado: float
    monto_pendiente: float
    pagos_completados: int
    pagos_pendientes: int
    pagos_vencidos: int
    pagos_por_metodo: Dict[str, Dict[str, Any]]
    pagos_por_concepto: Dict[str, Dict[str, Any]]
    ingresos_por_mes: List[Dict[str, Any]]
    promedio_pago: float
    pago_mayor: Optional[Dict[str, Any]] = None
    usuarios_morosos: int

class ReportePagos(BaseModel):
    """Esquema para reportes de pagos"""
    periodo_inicio: date
    periodo_fin: date
    total_ingresos: float
    total_egresos: float
    balance: float
    pagos_por_dia: List[Dict[str, Any]]
    metodos_pago_utilizados: Dict[str, float]
    tipos_cuota_vendidos: Dict[str, int]
    empleados_top_ventas: List[Dict[str, Any]]

class PagoMasivo(BaseModel):
    """Esquema para crear pagos masivos (ej: mensualidades)"""
    usuarios_ids: List[str]
    tipo_cuota_id: str
    fecha_vencimiento: date
    aplicar_descuento: bool = False
    descuento_porcentaje: float = Field(0.0, ge=0, le=100)
    notas: Optional[str] = None

# Alias/Esquema para compatibilidad con routers existentes
# Representa la salida completa de un pago (detalle)
class Pago(PagoOut):
    """Alias para compatibilidad; contiene toda la información de un pago."""
    pass

# Representa un resumen simplificado de un pago para listados
class PagoResumen(BaseModel):
    id: str
    monto: float
    fecha_pago: datetime
    estado: EstadoPago

    class Config:
        from_attributes = True
