from pydantic import BaseModel, Field, field_validator
from app.schemas.asistencias import TipoAsistencia

class AsistenciaBase(BaseModel):
    clase_id: int | None = Field(default=None)
    duracion_minutos: int | None = Field(default=None)

    @field_validator('clase_id')
    @classmethod
    def validar_clase_id(cls, v, values):
        tipo = values.get('tipo')
        if tipo and hasattr(tipo, 'name') and tipo.name == 'CLASE' and v is None:
            raise ValueError('El ID de la clase es requerido para asistencias a clases')
        return v

    @field_validator('duracion_minutos')
    @classmethod
    def duracion_positiva(cls, v):
        if v is not None and v <= 0:
            raise ValueError('La duración debe ser mayor que cero')
        return v 