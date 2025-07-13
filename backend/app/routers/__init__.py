"""
Inicialización del paquete de routers
"""
# Este archivo permite importar todos los routers desde app.routers

from app.routers.auth import router as auth_router
from app.routers.usuarios import router as usuarios_router
from app.routers.clases import router as clases_router
from app.routers.asistencias import router as asistencias_router
from app.routers.pagos import router as pagos_router
from app.routers.rutinas import router as rutinas_router
from app.routers.sync import router as sync_router

# Lista de todos los routers para ser incluidos en la app principal
routers = [
    auth_router,
    usuarios_router,
    clases_router,
    asistencias_router,
    pagos_router,
    rutinas_router,
    sync_router
]
