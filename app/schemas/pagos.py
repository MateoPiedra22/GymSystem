from pydantic import BaseModel, Field, field_validator

class Pago(BaseModel):
    monto: float = Field(..., description="Monto del pago")
    fecha_fin_membresia: str | None = Field(None, description="Fecha de fin de membresía")
    tipo_cuota_id: int = Field(..., description="ID del tipo de cuota")
    saldo_pendiente: float = Field(..., description="Saldo pendiente del pago")

    @field_validator('monto')
    @classmethod
    def monto_debe_ser_positivo(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser mayor que cero')
        return round(v, 2)

    @field_validator('fecha_fin_membresia')
    @classmethod
    def validar_fechas_membresia(cls, v, values):
        if v and 'fecha_inicio_membresia' in values.data and values.data['fecha_inicio_membresia']:
            if v <= values.data['fecha_inicio_membresia']:
                raise ValueError('La fecha fin debe ser posterior a la fecha inicio')
        return v

    @field_validator('tipo_cuota_id')
    @classmethod
    def validate_tipo_cuota_id(cls, v):
        # (Lógica original aquí, si existe)
        return v

    @field_validator('saldo_pendiente', mode='before')
    @classmethod
    def validate_saldo_pendiente(cls, v):
        # (Lógica original aquí, si existe)
        return v 