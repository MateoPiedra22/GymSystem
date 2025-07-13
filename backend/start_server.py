"""
Script de inicio del servidor backend
Ejecuta la aplicación FastAPI a través de uvicorn
"""
import os
import sys
import uvicorn
from pathlib import Path

# Asegurar que el directorio actual está en el path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Crear directorios de logs si no existen
log_dir = os.path.join(current_dir, "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configurar el puerto y host desde variables de entorno o usar valores por defecto
PORT = int(os.environ.get("API_PORT", 8000))
HOST = os.environ.get("API_HOST", "0.0.0.0")

if __name__ == "__main__":
    print(f"Iniciando servidor en http://{HOST}:{PORT}")
    print(f"Documentación API: http://localhost:{PORT}/docs")
    print("Presione Ctrl+C para detener el servidor")
    
    # Iniciar el servidor uvicorn
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=True if os.environ.get("GYM_ENV", "development") == "development" else False,
        log_level=os.environ.get("LOG_LEVEL", "info").lower(),
    )
