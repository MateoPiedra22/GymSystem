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

# Install latest pip and build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Copy the entire project
COPY . .

# Expose port (Railway will set the PORT environment variable)
EXPOSE 8000

# Make start script executable (entrypoint.sh not needed for Railway)
RUN chmod +x start.py

# Command to run the application
CMD ["python", "start.py"]