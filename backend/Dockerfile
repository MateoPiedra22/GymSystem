# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    USE_UVICORN=1 \
    ENVIRONMENT=production \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        netcat-openbsd \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-minimal.txt .
COPY requirements.txt .

# Install Python dependencies with error handling
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements-minimal.txt \
    || (echo "Minimal requirements failed, trying full requirements" && pip install -r requirements.txt) \
    || (echo "Both requirements failed, installing core dependencies" && pip install fastapi uvicorn gunicorn sqlalchemy psycopg2-binary python-dotenv)

# Copy project files
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/uploads /app/backups /app/static /app/templates \
    && chmod -R 755 /app

# Make start.py executable
RUN chmod +x ./start.py

# Expose port
EXPOSE $PORT

# Health check with better error handling
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || curl -f http://localhost:$PORT/ || exit 1

# Run the application
CMD ["python", "start.py"]