.PHONY: help docker-up docker-down docker-build docker-logs docker-restart fastapi-dev fastapi-run streamlit-run test test-verbose clean install

# Default target
help:
	@echo "Available commands:"
	@echo "  make help              - Show this help message"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up         - Start all services with docker-compose"
	@echo "  make docker-down       - Stop all services"
	@echo "  make docker-build      - Build docker images"
	@echo "  make docker-logs       - View logs from all services"
	@echo "  make docker-restart    - Restart all services"
	@echo ""
	@echo "Local Development:"
	@echo "  make fastapi-dev       - Run FastAPI in development mode"
	@echo "  make fastapi-run       - Run FastAPI in production mode"
	@echo "  make streamlit-run     - Run Streamlit dashboard"
	@echo ""
	@echo "Testing:"
	@echo "  make test              - Run pytest"
	@echo "  make test-verbose      - Run pytest with verbose output"
	@echo ""
	@echo "Utilities:"
	@echo "  make install           - Install dependencies"
	@echo "  make clean             - Clean cache and temporary files"

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

# Local development commands
fastapi-dev:
	fastapi dev ./app/main.py

fastapi-run:
	fastapi run ./app/main.py --host 0.0.0.0 --port 8000

streamlit-run:
	streamlit run streamlit_reports.py

# Testing commands
test:
	pytest

test-verbose:
	pytest -v

# Utility commands
install:
	pip install -r requirements.txt

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
