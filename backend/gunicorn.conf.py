"""Gunicorn configuration for GymSystem Backend.

This configuration file provides production-ready settings for running
the FastAPI application with Gunicorn WSGI server.
"""

import multiprocessing
import os
from pathlib import Path

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Timeout settings
timeout = 120
keepalive = 5
graceful_timeout = 30

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Application
# wsgi_module not needed for FastAPI with UvicornWorker

# Logging
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)s'
)

# Log files
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

errorlog = str(log_dir / "gunicorn_error.log")
accesslog = str(log_dir / "gunicorn_access.log")
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)s %(p)s'
)

# Process naming
proc_name = "gymsystem-backend"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
# ssl_version = ssl.PROTOCOL_TLSv1_2
# ciphers = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"

# Environment variables
raw_env = [
    f"ENVIRONMENT={os.getenv('ENVIRONMENT', 'production')}",
    f"LOG_LEVEL={os.getenv('LOG_LEVEL', 'info')}",
]

# Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting GymSystem Backend server...")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Worker class: {worker_class}")
    server.log.info(f"Bind: {bind}")


def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading GymSystem Backend server...")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("GymSystem Backend server is ready. Listening on: %s", bind)


def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker received INT or QUIT signal")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)
    
    # Initialize worker-specific resources here
    # For example, database connections, cache connections, etc.
    

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info("Worker initialized (pid: %s)", worker.pid)


def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info("Worker aborted (pid: %s)", worker.pid)


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")


def pre_request(worker, req):
    """Called just before a worker processes the request."""
    # Add request ID for tracing
    worker.log.debug("%s %s", req.method, req.uri)


def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    # Log response details
    worker.log.debug(
        "%s %s - %s", 
        req.method, 
        req.uri, 
        resp.status_code if hasattr(resp, 'status_code') else 'Unknown'
    )


def child_exit(server, worker):
    """Called just after a worker has been exited, in the master process."""
    server.log.info("Worker exited (pid: %s)", worker.pid)


def worker_exit(server, worker):
    """Called just after a worker has been exited, in the worker process."""
    worker.log.info("Worker exiting (pid: %s)", worker.pid)


def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info("Number of workers changed from %s to %s", old_value, new_value)


def on_exit(server):
    """Called just before exiting."""
    server.log.info("Shutting down GymSystem Backend server...")


# Custom configuration based on environment
if os.getenv('ENVIRONMENT') == 'development':
    # Development settings
    workers = 1
    reload = True
    loglevel = 'debug'
    timeout = 0  # Disable timeout for debugging
    
elif os.getenv('ENVIRONMENT') == 'testing':
    # Testing settings
    workers = 1
    loglevel = 'warning'
    accesslog = None  # Disable access log in testing
    
elif os.getenv('ENVIRONMENT') == 'production':
    # Production settings (already set above)
    pass

# Performance tuning based on available memory
try:
    import psutil
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    if memory_gb < 2:
        # Low memory environment
        workers = min(workers, 2)
        worker_connections = 500
        max_requests = 500
    elif memory_gb > 8:
        # High memory environment
        worker_connections = 2000
        max_requests = 2000
except ImportError:
    # psutil not available, use defaults
    pass

# Docker-specific settings
if os.path.exists('/.dockerenv'):
    # Running in Docker
    bind = "0.0.0.0:8000"
    
    # Use environment variables for Docker
    if 'GUNICORN_CMD_ARGS' in os.environ:
        # Allow override via environment
        pass

# Kubernetes-specific settings
if os.getenv('KUBERNETES_SERVICE_HOST'):
    # Running in Kubernetes
    graceful_timeout = 60  # Allow more time for graceful shutdown
    
    # Health check endpoint should respond quickly
    timeout = 30

# Cloud platform specific settings
cloud_platform = os.getenv('CLOUD_PLATFORM', '').lower()

if cloud_platform == 'heroku':
    # Heroku-specific settings
    bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
    workers = int(os.getenv('WEB_CONCURRENCY', workers))
    
elif cloud_platform == 'aws':
    # AWS-specific settings
    # Use instance metadata to determine optimal worker count
    pass
    
elif cloud_platform == 'gcp':
    # Google Cloud Platform settings
    pass
    
elif cloud_platform == 'azure':
    # Azure-specific settings
    pass

# Monitoring and observability
if os.getenv('ENABLE_PROMETHEUS', 'false').lower() == 'true':
    # Enable Prometheus metrics
    try:
        from prometheus_client import multiprocess
        from prometheus_client import generate_latest
        from prometheus_client import CollectorRegistry
        
        def child_exit(server, worker):
            """Clean up Prometheus metrics on worker exit."""
            multiprocess.mark_process_dead(worker.pid)
    except ImportError:
        server.log.warning("Prometheus client not available")

# Security settings
if os.getenv('ENABLE_SECURITY_HEADERS', 'true').lower() == 'true':
    # Security headers will be handled by the application middleware
    pass

# Custom error handling
def on_starting(server):
    """Validate configuration on startup."""
    # Validate required environment variables
    required_vars = ['SECRET_KEY', 'DATABASE_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        server.log.error(f"Missing required environment variables: {missing_vars}")
        raise SystemExit(1)
    
    server.log.info("Configuration validation passed")
    server.log.info(f"Starting GymSystem Backend with {workers} workers")