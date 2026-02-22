# Makefile for common development tasks

.PHONY: help install migrate test run docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make migrate       - Run database migrations"
	@echo "  make test          - Run tests"
	@echo "  make run           - Start development server"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make clean         - Remove cache and temp files"

install:
	pip install -r requirements.txt

migrate:
	alembic upgrade head

test:
	pytest tests/ -v --cov=app --cov-report=term

run:
	uvicorn app.main:app --reload --port 8000

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

format:
	black app tests
	isort app tests

lint:
	flake8 app tests
	mypy app

celery-worker:
	celery -A app.core.celery worker --loglevel=info

celery-beat:
	celery -A app.core.celery beat --loglevel=info
