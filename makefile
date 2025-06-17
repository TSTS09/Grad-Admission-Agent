
.PHONY: help install dev test lint format clean build docker-build docker-up docker-down migrate seed

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Run development server"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean cache and temp files"
	@echo "  build       - Build for production"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up   - Start Docker services"
	@echo "  docker-down - Stop Docker services"
	@echo "  migrate     - Run database migrations"
	@echo "  seed        - Seed database with sample data"

# Development setup
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Testing
test:
	pytest -v --cov=app --cov-report=html

test-watch:
	pytest-watch -- -v

# Code quality
lint:
	flake8 app
	mypy app

format:
	black app tests
	isort app tests

# Cleanup
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

# Build
build:
	python setup.py sdist bdist_wheel

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-shell:
	docker-compose exec api bash

# Database operations
migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(MSG)"

migrate-downgrade:
	alembic downgrade -1

seed:
	python scripts/seed_data.py

# Development with Docker
dev-docker:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production deployment
deploy:
	docker-compose -f docker-compose.yml --profile production up -d

# Monitoring
monitor:
	docker-compose --profile monitoring up -d

# Worker management
worker:
	celery -A app.worker.celery_app worker --loglevel=info

beat:
	celery -A app.worker.celery_app beat --loglevel=info

flower:
	celery -A app.worker.celery_app flower

# Backup and restore
backup-db:
	python scripts/backup_db.py

restore-db:
	python scripts/restore_db.py $(FILE)