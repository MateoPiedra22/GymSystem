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

# Clear pip cache to ensure clean installation
RUN pip cache purge
RUN pip install --upgrade pip==25.1.1 setuptools wheel

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose port (Railway will set the PORT environment variable)
EXPOSE 8000

# Make entrypoint script executable
RUN chmod +x backend/entrypoint.sh

# Make start script executable
RUN chmod +x start.py

# Command to run the application
CMD ["python", "start.py"]