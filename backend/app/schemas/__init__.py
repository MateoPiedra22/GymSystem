"""
Inicialización del paquete de schemas
"""

# Importaciones básicas que sabemos que existen
from app.schemas.auth import TokenData, Token
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioOut, ChangePassword
from app.schemas.pagos import PagoCreate, PagoUpdate, PagoOut
from app.schemas.tipos_cuota import TipoCuotaCreate, TipoCuotaUpdate, TipoCuotaOut

# Otras importaciones se hacen directamente donde se necesiten
