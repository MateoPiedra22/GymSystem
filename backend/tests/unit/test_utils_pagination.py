import pytest
from sqlalchemy import select
from app.utils.pagination import apply_filters, paginate
from app.models.usuarios import Usuario


def test_apply_filters_and_paginate(db_session):
    """
    Prueba que apply_filters y paginate funcionan correctamente.
    """
    from app import models  # noqa: F401
    # Crear usuarios de prueba
    u1 = Usuario(email="a@a.com", username="a", nombre="A", apellido="A",
                 hashed_password="pw", salt="salt")
    u2 = Usuario(email="b@b.com", username="b", nombre="B", apellido="B",
                 hashed_password="pw", salt="salt", esta_activo=False)
    db_session.add_all([u1, u2])
    db_session.commit()

    # Query inicial
    query = db_session.query(Usuario)
    # Aplicar filtro de usuarios activos
    filtered = apply_filters(query, {"esta_activo": True})
    total, items = paginate(filtered, skip=0, limit=10)
    assert total >= 1
    assert len(items) == 1
    assert items[0].email == "a@a.com" 