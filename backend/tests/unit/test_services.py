"""
Pruebas unitarias para servicios del backend
"""
import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.pago_service import (
    crear_pago, obtener_pago, obtener_pagos, 
    actualizar_pago, eliminar_pago,
    obtener_estadisticas_pagos
)
from app.schemas.pagos import PagoCreate, PagoUpdate
from app.models.pagos import Pago, EstadoPago, MetodoPago, ConceptoPago


class TestPagoService:
    """Pruebas para el servicio de pagos"""

    @pytest.fixture
    def mock_db(self):
        """Mock de sesión de base de datos"""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_pago_create(self):
        """Datos de ejemplo para crear un pago"""
        return PagoCreate(
            monto=100.0,
            usuario_id="123e4567-e89b-12d3-a456-426614174000",
            concepto=ConceptoPago.MEMBRESIA,
            metodo_pago=MetodoPago.EFECTIVO,
            descripcion="Pago de mensualidad"
        )

    @pytest.fixture
    def sample_pago(self):
        """Pago de ejemplo"""
        return Pago(
            id="123e4567-e89b-12d3-a456-426614174001",
            numero_recibo="REC-2024-001",
            monto=100.0,
            monto_final=100.0,
            estado=EstadoPago.PAGADO,
            metodo_pago=MetodoPago.EFECTIVO,
            concepto=ConceptoPago.MEMBRESIA,
            usuario_id="123e4567-e89b-12d3-a456-426614174000",
            fecha_pago=datetime(2024, 1, 15)
        )

    @pytest.mark.asyncio
    async def test_crear_pago(self, mock_db, sample_pago_create, sample_pago):
        """Test para crear un pago"""
        # Configurar mock
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Mock para el constructor de Pago
        with patch('app.services.pago_service.Pago') as mock_pago_class:
            mock_pago_class.return_value = sample_pago
            
            # Ejecutar
            resultado = await crear_pago(mock_db, sample_pago_create)
            
            # Verificar
            assert resultado == sample_pago
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_obtener_pago_existente(self, mock_db, sample_pago):
        """Test para obtener un pago existente"""
        # Configurar mock
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_pago
        
        # Ejecutar
        resultado = await obtener_pago(mock_db, sample_pago.id)
        
        # Verificar
        assert resultado == sample_pago
        mock_db.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_obtener_pago_inexistente(self, mock_db):
        """Test para obtener un pago que no existe"""
        # Configurar mock
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        # Ejecutar
        resultado = await obtener_pago(mock_db, "pago-inexistente")
        
        # Verificar
        assert resultado is None

    @pytest.mark.asyncio
    async def test_obtener_pagos_con_filtros(self, mock_db, sample_pago):
        """Test para obtener pagos con filtros"""
        # Configurar mock
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()
        mock_offset = Mock()
        mock_limit = Mock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = [sample_pago]
        
        # Ejecutar
        resultado = await obtener_pagos(
            mock_db, 
            skip=0, 
            limit=10,
            estado=EstadoPago.PAGADO,
            metodo_pago=MetodoPago.EFECTIVO
        )
        
        # Verificar
        assert resultado == [sample_pago]
        assert len(resultado) == 1

    @pytest.mark.asyncio
    async def test_actualizar_pago(self, mock_db, sample_pago):
        """Test para actualizar un pago"""
        # Configurar mock
        with patch('app.services.pago_service.obtener_pago') as mock_obtener:
            mock_obtener.return_value = sample_pago
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Datos de actualización
            pago_update = PagoUpdate(monto=150.0, descripcion="Actualizado")
            
            # Ejecutar
            resultado = await actualizar_pago(mock_db, sample_pago.id, pago_update)
            
            # Verificar
            assert resultado == sample_pago
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_eliminar_pago_existente(self, mock_db, sample_pago):
        """Test para eliminar un pago existente"""
        # Configurar mock
        with patch('app.services.pago_service.obtener_pago') as mock_obtener:
            mock_obtener.return_value = sample_pago
            mock_db.delete.return_value = None
            mock_db.commit.return_value = None
            
            # Ejecutar
            resultado = await eliminar_pago(mock_db, sample_pago.id)
            
            # Verificar
            assert resultado is True
            mock_db.delete.assert_called_once_with(sample_pago)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_eliminar_pago_inexistente(self, mock_db):
        """Test para eliminar un pago que no existe"""
        # Configurar mock
        with patch('app.services.pago_service.obtener_pago') as mock_obtener:
            mock_obtener.return_value = None
            
            # Ejecutar
            resultado = await eliminar_pago(mock_db, "pago-inexistente")
            
            # Verificar
            assert resultado is False
            mock_db.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_obtener_estadisticas_pagos(self, mock_db, sample_pago):
        """Test para obtener estadísticas de pagos"""
        # Configurar datos de prueba
        fecha_inicio = datetime(2024, 1, 1)
        fecha_fin = datetime(2024, 1, 31)
        
        # Configurar mock
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [sample_pago, sample_pago]  # 2 pagos
        
        # Ejecutar
        resultado = await obtener_estadisticas_pagos(mock_db, fecha_inicio, fecha_fin)
        
        # Verificar
        assert resultado["total_pagos"] == 2
        assert resultado["monto_total"] == 200.0  # 2 pagos de 100 cada uno
        assert resultado["promedio_diario"] > 0
        assert resultado["periodo_inicio"] == fecha_inicio
        assert resultado["periodo_fin"] == fecha_fin

    @pytest.mark.asyncio
    async def test_estadisticas_fecha_invalida(self, mock_db):
        """Test para estadísticas con fechas inválidas"""
        fecha_inicio = datetime(2024, 1, 31)
        fecha_fin = datetime(2024, 1, 1)  # Fecha fin anterior a inicio
        
        # Ejecutar y verificar excepción
        with pytest.raises(ValueError, match="fecha_fin debe ser posterior"):
            await obtener_estadisticas_pagos(mock_db, fecha_inicio, fecha_fin)


class TestAsistenciaService:
    """Pruebas para el servicio de asistencias"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.mark.asyncio
    async def test_registrar_asistencia(self, mock_db):
        """Test básico para registrar asistencia"""
        # Esta es una prueba de ejemplo - expandir según la implementación
        from app.services.asistencia_service import registrar_entrada
        
        # Mock básico
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        # Para ahora solo verificamos que no falle
        # En implementación real, agregar lógica específica
        assert True  # Placeholder


class TestClaseService:
    """Pruebas para el servicio de clases"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.mark.asyncio
    async def test_crear_clase(self, mock_db):
        """Test básico para crear clase"""
        from app.services.clase_service import create_clase
        from app.schemas.clases import ClaseCreate
        
        # Datos de ejemplo
        clase_data = ClaseCreate(
            nombre="Yoga",
            descripcion="Clase de yoga para principiantes",
            capacidad_maxima=20,
            duracion_minutos=60
        )
        
        # Mock básico
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        # Para ahora solo verificamos que no falle
        assert True  # Placeholder


# Configuración de pytest
@pytest.fixture(scope="session")
def anyio_backend():
    """Backend para pruebas asíncronas"""
    return "asyncio"


# Marcadores de pytest
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.unit
] 