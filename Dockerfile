# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Clear pip cache and upgrade pip
RUN pip cache purge || true
RUN pip install --upgrade pip==25.1.1 setuptools wheel

# Copy requirements and install Python dependencies with verbose output
COPY backend/requirements.txt .
RUN cat requirements.txt | grep phonevalidator
RUN pip install --no-cache-dir --force-reinstall --verbose phonevalidator==1.1.2
RUN pip install --no-cache-dir --force-reinstall -r requirements.txt

# Copy the entire project
COPY . .

# Expose port (Railway will set the PORT environment variable)
EXPOSE $PORT

# Command to run the application
CMD python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT