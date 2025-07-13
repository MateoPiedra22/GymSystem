from pydantic import BaseModel, Field, field_validator
from datetime import date

class Empleado(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)
    fecha_nacimiento: date = Field(..., title="Fecha de Nacimiento")
    fecha_ingreso: date = Field(..., title="Fecha de Ingreso")
    certificaciones: list[str] = Field(default_factory=list, title="Certificaciones")
    fecha_fin: date | None = Field(default=None, title="Fecha de Fin")

    @field_validator('fecha_nacimiento')
    @classmethod
    def validate_fecha_nacimiento(cls, v):
        if v >= date.today():
            raise ValueError('La fecha de nacimiento debe ser en el pasado')
        edad = (date.today() - v).days / 365.25
        if edad < 18:
            raise ValueError('El empleado debe ser mayor de 18 años')
        if edad > 80:
            raise ValueError('Fecha de nacimiento no válida')
        return v

    @field_validator('fecha_ingreso')
    @classmethod
    def validate_fecha_ingreso(cls, v):
        if v > date.today():
            raise ValueError('La fecha de ingreso no puede ser futura')
        return v

    @field_validator('certificaciones', mode='before')
    @classmethod
    def parse_certificaciones(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return []
        return v or []

    @field_validator('fecha_fin')
    @classmethod
    def validate_fecha_fin(cls, v, values):
        if 'fecha_inicio' in values.data and v <= values.data['fecha_inicio']:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v 