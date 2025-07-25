# GymSystem Backend Makefile
# This Makefile provides common development tasks for the GymSystem backend

.PHONY: help install install-dev clean test test-cov lint format check run dev migrate upgrade downgrade reset-db docker-build docker-run docker-stop logs backup restore

# Default target
help:
	@echo "GymSystem Backend - Available commands:"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  clean        - Clean cache and temporary files"
	@echo ""
	@echo "Development:"
	@echo "  run          - Run the application in production mode"
	@echo "  dev          - Run the application in development mode"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  lint         - Run linting (flake8, mypy)"
	@echo "  format       - Format code (black, isort)"
	@echo "  check        - Run all checks (lint + test)"
	@echo ""
	@echo "Database:"
	@echo "  migrate      - Generate new migration"
	@echo "  upgrade      - Apply migrations"
	@echo "  downgrade    - Rollback last migration"
	@echo "  reset-db     - Reset database (WARNING: destroys data)"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run with Docker Compose"
	@echo "  docker-stop  - Stop Docker containers"
	@echo "  logs         - Show Docker logs"
	@echo ""
	@echo "Maintenance:"
	@echo "  backup       - Create database backup"
	@echo "  restore      - Restore database from backup"

# Installation
install:
	@echo "Installing production dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "Installing development dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-mock black isort flake8 mypy pre-commit
	pre-commit install

# Cleaning
clean:
	@echo "Cleaning cache and temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

# Development
run:
	@echo "Starting application in production mode..."
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	@echo "Starting application in development mode..."
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# Testing
test:
	@echo "Running tests..."
	pytest -v

test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml

test-unit:
	@echo "Running unit tests..."
	pytest -v -m "unit"

test-integration:
	@echo "Running integration tests..."
	pytest -v -m "integration"

test-api:
	@echo "Running API tests..."
	pytest -v -m "api"

# Code Quality
lint:
	@echo "Running linting..."
	flake8 app/ tests/
	mypy app/

format:
	@echo "Formatting code..."
	black app/ tests/
	isort app/ tests/

check: lint test
	@echo "All checks completed!"

# Database
migrate:
	@echo "Generating new migration..."
	@read -p "Enter migration message: " message; \
	alembic revision --autogenerate -m "$$message"

upgrade:
	@echo "Applying migrations..."
	alembic upgrade head

downgrade:
	@echo "Rolling back last migration..."
	alembic downgrade -1

reset-db:
	@echo "WARNING: This will destroy all data!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "Database reset completed!"; \
	else \
		echo "Operation cancelled."; \
	fi

# Docker
docker-build:
	@echo "Building Docker image..."
	docker build -t gymsystem-backend .

docker-run:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d

docker-run-dev:
	@echo "Starting development services with Docker Compose..."
	docker-compose --profile development up -d

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down

logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

logs-api:
	@echo "Showing API logs..."
	docker-compose logs -f api

logs-db:
	@echo "Showing database logs..."
	docker-compose logs -f db

# Maintenance
backup:
	@echo "Creating database backup..."
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	docker-compose exec db pg_dump -U postgres gymsystem > backups/backup_$$timestamp.sql; \
	echo "Backup created: backups/backup_$$timestamp.sql"

restore:
	@echo "Available backups:"
	@ls -la backups/*.sql 2>/dev/null || echo "No backups found"
	@read -p "Enter backup filename: " filename; \
	if [ -f "backups/$$filename" ]; then \
		docker-compose exec -T db psql -U postgres -d gymsystem < "backups/$$filename"; \
		echo "Database restored from $$filename"; \
	else \
		echo "Backup file not found: $$filename"; \
	fi

# Environment
env-example:
	@echo "Creating .env from .env.example..."
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

# Security
security-check:
	@echo "Running security checks..."
	pip install safety bandit
	safety check
	bandit -r app/

# Performance
profile:
	@echo "Running performance profiling..."
	python -m cProfile -o profile.stats -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
	sleep 5
	curl http://localhost:8000/health
	kill %%1
	python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

# Documentation
docs:
	@echo "Generating API documentation..."
	@echo "API documentation available at: http://localhost:8000/docs"
	@echo "ReDoc documentation available at: http://localhost:8000/redoc"
	@echo "OpenAPI schema available at: http://localhost:8000/openapi.json"

# Deployment
deploy-staging:
	@echo "Deploying to staging..."
	@echo "This would deploy to staging environment"
	# Add your staging deployment commands here

deploy-production:
	@echo "Deploying to production..."
	@echo "WARNING: This will deploy to production!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "Deploying to production..."; \
		# Add your production deployment commands here; \
	else \
		echo "Deployment cancelled."; \
	fi

# Health checks
health:
	@echo "Checking application health..."
	curl -f http://localhost:8000/health || echo "Application is not responding"

# Load testing
load-test:
	@echo "Running load tests..."
	pip install locust
	locust -f tests/load_test.py --host=http://localhost:8000

# Git hooks
pre-commit:
	@echo "Running pre-commit checks..."
	pre-commit run --all-files

# Quick start
quick-start: install-dev env-example upgrade
	@echo "Quick start completed!"
	@echo "1. Edit .env file with your configuration"
	@echo "2. Run 'make dev' to start development server"
	@echo "3. Visit http://localhost:8000/docs for API documentation"

# Full setup for new developers
setup: clean install-dev env-example
	@echo "Setting up development environment..."
	mkdir -p logs uploads backups
	@echo "Development environment setup completed!"
	@echo "Next steps:"
	@echo "1. Edit .env file with your database configuration"
	@echo "2. Run 'make upgrade' to apply database migrations"
	@echo "3. Run 'make dev' to start development server"