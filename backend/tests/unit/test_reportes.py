import pytest


def test_kpis_empty_db(client):
    """
    Si la BD está vacía, los KPIs deben ser cero o nulos según corresponda.
    """
    response = client.get("/api/reportes/kpis")
    assert response.status_code == 200
    data = response.json()
    assert data["ingresos_mes"] == 0.0
    assert data["nuevas_inscripciones_mes"] == 0
    assert data["indice_satisfaccion"] is None


def test_graficos_empty_db(client):
    """
    Si la BD está vacía, la lista anual de ingresos debe tener 12 entradas a 0.0.
    """
    response = client.get("/api/reportes/graficos")
    assert response.status_code == 200
    data = response.json()
    assert "ingresos_anual" in data
    assert isinstance(data["ingresos_anual"], list)
    assert len(data["ingresos_anual"]) == 12
    assert all(item["monto"] == 0.0 for item in data["ingresos_anual"]) 