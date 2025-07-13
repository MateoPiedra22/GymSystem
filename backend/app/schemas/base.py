"""
Esquemas base compartidos entre múltiples módulos
"""
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Esquema genérico para respuestas paginadas
    """
    items: List[T]
    total: int
    page: int
    pages: int
    per_page: int
    has_next: bool
    has_prev: bool
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "pages": 10,
                "per_page": 10,
                "has_next": True,
                "has_prev": False
            }
        }

class QueryParams(BaseModel):
    """
    Parámetros comunes de consulta para endpoints paginados
    """
    page: int = 1
    per_page: int = 20
    search: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    
    @property
    def skip(self) -> int:
        """Calcula el offset basado en la página actual"""
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        """Retorna el límite de registros por página"""
        return self.per_page
    
    def validate_page(self) -> None:
        """Valida que los parámetros de paginación sean correctos"""
        if self.page < 1:
            self.page = 1
        if self.per_page < 1:
            self.per_page = 20
        if self.per_page > 100:
            self.per_page = 100

class ErrorResponse(BaseModel):
    """
    Esquema para respuestas de error estándar
    """
    error: str
    detail: Optional[str] = None
    status_code: int
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Not Found",
                "detail": "El recurso solicitado no fue encontrado",
                "status_code": 404
            }
        } 