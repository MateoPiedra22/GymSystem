"""
Utilidades de paginación y filtrado para consultas SQLAlchemy
"""
from typing import Dict, Any, Tuple, List, Optional
from sqlalchemy.orm import Query
from math import ceil


def paginate(query: Query, skip: int = 0, limit: int = 10) -> Tuple[int, List]:
    """
    Aplica paginación a una consulta SQLAlchemy.
    Retorna total de elementos y lista de resultados.
    
    Args:
        query: Query de SQLAlchemy
        skip: Número de registros a omitir
        limit: Límite de registros a retornar
        
    Returns:
        Tupla con (total, items)
    """
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return total, items


def paginate_with_metadata(
    query: Query, 
    page: int = 1, 
    per_page: int = 20
) -> Dict[str, Any]:
    """
    Aplica paginación a una consulta SQLAlchemy y retorna metadatos completos.
    
    Args:
        query: Query de SQLAlchemy
        page: Número de página (comenzando en 1)
        per_page: Registros por página
        
    Returns:
        Diccionario con items y metadatos de paginación
    """
    # Validar parámetros
    page = max(1, page)
    per_page = min(max(1, per_page), 100)  # Máximo 100 items por página
    
    # Calcular offset
    skip = (page - 1) * per_page
    
    # Obtener total y items
    total = query.count()
    items = query.offset(skip).limit(per_page).all()
    
    # Calcular metadatos
    total_pages = ceil(total / per_page) if per_page > 0 else 0
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": total_pages,
        "per_page": per_page,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


def apply_filters(query: Query, filters: dict) -> Query:
    """
    Aplica filtros de igualdad a la consulta basado en un dict de filtros.
    Sólo añade aquellos filtros cuyo valor no sea None.
    
    Args:
        query: Query de SQLAlchemy
        filters: Diccionario con filtros a aplicar
        
    Returns:
        Query con filtros aplicados
    """
    for key, value in filters.items():
        if value is not None:
            entity = query.column_descriptions[0]['entity']
            if hasattr(entity, key):
                column = getattr(entity, key)
                if isinstance(value, bool):
                    query = query.filter(column.is_(value))
                else:
                    query = query.filter(column == value)
    return query


def apply_search(
    query: Query, 
    search_term: Optional[str], 
    search_fields: List[str]
) -> Query:
    """
    Aplica búsqueda de texto en múltiples campos.
    
    Args:
        query: Query de SQLAlchemy
        search_term: Término de búsqueda
        search_fields: Lista de campos donde buscar
        
    Returns:
        Query con búsqueda aplicada
    """
    if not search_term or not search_fields:
        return query
    
    from sqlalchemy import or_
    
    entity = query.column_descriptions[0]['entity']
    search_term = f"%{search_term}%"
    
    conditions = []
    for field in search_fields:
        if hasattr(entity, field):
            conditions.append(getattr(entity, field).ilike(search_term))
    
    if conditions:
        query = query.filter(or_(*conditions))
    
    return query


def apply_sorting(
    query: Query, 
    sort_by: Optional[str], 
    sort_order: str = "asc"
) -> Query:
    """
    Aplica ordenamiento a la consulta.
    
    Args:
        query: Query de SQLAlchemy
        sort_by: Campo por el cual ordenar
        sort_order: Orden ('asc' o 'desc')
        
    Returns:
        Query con ordenamiento aplicado
    """
    if not sort_by:
        return query
    
    entity = query.column_descriptions[0]['entity']
    
    if hasattr(entity, sort_by):
        column = getattr(entity, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    
    return query 