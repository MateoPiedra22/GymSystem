#!/bin/bash

# GymSystem Backend Docker Entrypoint Script
# This script handles the startup process for the Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Default values
ENVIRONMENT=${ENVIRONMENT:-production}
DATABASE_HOST=${DATABASE_HOST:-db}
DATABASE_PORT=${DATABASE_PORT:-5432}
DATABASE_NAME=${DATABASE_NAME:-gymsystem}
REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}
MAX_RETRIES=${MAX_RETRIES:-30}
RETRY_INTERVAL=${RETRY_INTERVAL:-2}

log "Starting GymSystem Backend..."
info "Environment: $ENVIRONMENT"
info "Database: $DATABASE_HOST:$DATABASE_PORT/$DATABASE_NAME"
info "Redis: $REDIS_HOST:$REDIS_PORT"

# Function to wait for a service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local retries=0
    
    info "Waiting for $service_name to be ready at $host:$port..."
    
    while ! nc -z "$host" "$port" >/dev/null 2>&1; do
        retries=$((retries + 1))
        if [ $retries -gt $MAX_RETRIES ]; then
            error "$service_name is not available after $MAX_RETRIES attempts"
            exit 1
        fi
        warn "$service_name is not ready yet. Attempt $retries/$MAX_RETRIES. Retrying in ${RETRY_INTERVAL}s..."
        sleep $RETRY_INTERVAL
    done
    
    log "$service_name is ready!"
}

# Function to check database connection
check_database() {
    info "Checking database connection..."
    
    python3 -c "
import os
import sys
import psycopg2
from urllib.parse import urlparse

try:
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Parse DATABASE_URL
        parsed = urlparse(database_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password
        )
    else:
        # Use individual environment variables
        conn = psycopg2.connect(
            host=os.getenv('DATABASE_HOST', 'db'),
            port=int(os.getenv('DATABASE_PORT', 5432)),
            database=os.getenv('DATABASE_NAME', 'gymsystem'),
            user=os.getenv('DATABASE_USER', 'postgres'),
            password=os.getenv('DATABASE_PASSWORD', 'password')
        )
    
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()[0]
    print(f'Database connection successful: {version}')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        log "Database connection successful"
    else
        error "Database connection failed"
        exit 1
    fi
}

# Function to check Redis connection
check_redis() {
    if [ "$REDIS_ENABLED" = "true" ] || [ "$CELERY_ENABLED" = "true" ]; then
        info "Checking Redis connection..."
        
        python3 -c "
import os
import sys
import redis
from urllib.parse import urlparse

try:
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        r = redis.from_url(redis_url)
    else:
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD'),
            decode_responses=True
        )
    
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    sys.exit(1)
"
        
        if [ $? -eq 0 ]; then
            log "Redis connection successful"
        else
            error "Redis connection failed"
            exit 1
        fi
    else
        info "Redis check skipped (not enabled)"
    fi
}

# Function to run database migrations
run_migrations() {
    if [ "$RUN_MIGRATIONS" = "true" ] || [ "$ENVIRONMENT" = "development" ]; then
        info "Running database migrations..."
        
        # Check if alembic is configured
        if [ -f "alembic.ini" ]; then
            # Check current migration status
            alembic current
            
            # Run migrations
            alembic upgrade head
            
            if [ $? -eq 0 ]; then
                log "Database migrations completed successfully"
            else
                error "Database migrations failed"
                exit 1
            fi
        else
            warn "Alembic configuration not found, skipping migrations"
        fi
    else
        info "Database migrations skipped"
    fi
}

# Function to create initial data
create_initial_data() {
    if [ "$CREATE_INITIAL_DATA" = "true" ] || [ "$ENVIRONMENT" = "development" ]; then
        info "Creating initial data..."
        
        python3 -c "
import asyncio
from app.core.init_db import init_db

asyncio.run(init_db())
print('Initial data created successfully')
" 2>/dev/null || warn "Initial data creation failed or skipped"
    else
        info "Initial data creation skipped"
    fi
}

# Function to validate environment variables
validate_environment() {
    info "Validating environment variables..."
    
    # Required variables
    required_vars=("SECRET_KEY")
    
    # Check for database configuration
    if [ -z "$DATABASE_URL" ]; then
        required_vars+=("DATABASE_HOST" "DATABASE_NAME" "DATABASE_USER" "DATABASE_PASSWORD")
    fi
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
    
    log "Environment validation passed"
}

# Function to setup logging
setup_logging() {
    info "Setting up logging..."
    
    # Create log directories
    mkdir -p /app/logs
    mkdir -p /app/uploads
    mkdir -p /app/backups
    
    # Set permissions
    chmod 755 /app/logs /app/uploads /app/backups
    
    log "Logging setup completed"
}

# Function to start the application
start_application() {
    info "Starting application..."
    
    case "$1" in
        "web"|"server"|"")
            if [ "$ENVIRONMENT" = "development" ]; then
                log "Starting development server with auto-reload..."
                exec uvicorn app.main:app \
                    --host 0.0.0.0 \
                    --port ${PORT:-8000} \
                    --reload \
                    --log-level debug
            else
                log "Starting production server with Gunicorn..."
                exec gunicorn app.main:app \
                    -c gunicorn.conf.py \
                    --bind 0.0.0.0:${PORT:-8000}
            fi
            ;;
        "worker"|"celery-worker")
            log "Starting Celery worker..."
            exec celery -A app.core.celery worker \
                --loglevel=${CELERY_LOG_LEVEL:-info} \
                --concurrency=${CELERY_WORKER_CONCURRENCY:-4}
            ;;
        "beat"|"celery-beat")
            log "Starting Celery beat scheduler..."
            exec celery -A app.core.celery beat \
                --loglevel=${CELERY_LOG_LEVEL:-info} \
                --schedule=/tmp/celerybeat-schedule
            ;;
        "flower")
            log "Starting Celery Flower monitoring..."
            exec celery -A app.core.celery flower \
                --port=${FLOWER_PORT:-5555} \
                --basic_auth=${FLOWER_BASIC_AUTH:-admin:admin}
            ;;
        "migrate")
            log "Running migrations only..."
            run_migrations
            exit 0
            ;;
        "init-db")
            log "Initializing database..."
            run_migrations
            create_initial_data
            exit 0
            ;;
        "shell")
            log "Starting interactive shell..."
            exec python3 -c "
import asyncio
from app.core.database import get_db
from app.models import *
print('GymSystem shell ready. Database and models imported.')
import IPython
IPython.start_ipython(argv=[])
"
            ;;
        "test")
            log "Running tests..."
            exec pytest "${@:2}"
            ;;
        "bash")
            log "Starting bash shell..."
            exec /bin/bash
            ;;
        *)
            log "Executing custom command: $*"
            exec "$@"
            ;;
    esac
}

# Function to handle shutdown
shutdown() {
    log "Received shutdown signal, gracefully stopping..."
    # Add any cleanup logic here
    exit 0
}

# Trap signals for graceful shutdown
trap shutdown SIGTERM SIGINT

# Main execution flow
main() {
    # Validate environment
    validate_environment
    
    # Setup logging
    setup_logging
    
    # Wait for dependencies (only for web/worker services)
    case "$1" in
        "web"|"server"|"worker"|"celery-worker"|"beat"|"celery-beat"|"flower"|"migrate"|"init-db"|"")
            # Wait for database
            wait_for_service "$DATABASE_HOST" "$DATABASE_PORT" "PostgreSQL"
            check_database
            
            # Wait for Redis (if enabled)
            if [ "$REDIS_ENABLED" = "true" ] || [ "$CELERY_ENABLED" = "true" ] || [ "$1" = "worker" ] || [ "$1" = "celery-worker" ] || [ "$1" = "beat" ] || [ "$1" = "celery-beat" ] || [ "$1" = "flower" ]; then
                wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
                check_redis
            fi
            
            # Run migrations (only for web service or explicit migrate command)
            if [ "$1" = "web" ] || [ "$1" = "server" ] || [ "$1" = "migrate" ] || [ "$1" = "init-db" ] || [ -z "$1" ]; then
                run_migrations
            fi
            
            # Create initial data (only for init-db command or development)
            if [ "$1" = "init-db" ]; then
                create_initial_data
            fi
            ;;
    esac
    
    # Start the application
    start_application "$@"
}

# Health check function
health_check() {
    if [ "$1" = "health" ]; then
        python3 -c "
import requests
import sys

try:
    response = requests.get('http://localhost:${PORT:-8000}/health', timeout=5)
    if response.status_code == 200:
        print('Health check passed')
        sys.exit(0)
    else:
        print(f'Health check failed with status {response.status_code}')
        sys.exit(1)
except Exception as e:
    print(f'Health check failed: {e}')
    sys.exit(1)
"
        exit $?
    fi
}

# Check for health check
health_check "$1"

# Run main function
main "$@"