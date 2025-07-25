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

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --verbose -r requirements.txt

# Copy the entire project
COPY . .

# Expose port (Railway will set the PORT environment variable)
EXPOSE $PORT

# Command to run the application
CMD python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT