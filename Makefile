.PHONY: help dev install test lint format migrate migrate-create clean

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev:  ## Run development server with auto-reload
	uvicorn src.main:app --reload

install:  ## Install dependencies (including dev dependencies)
	pip install -e ".[dev]"

test:  ## Run tests
	pytest

lint:  ## Lint code with ruff
	ruff check src tests

format:  ## Format code with ruff
	ruff format src tests

format-check:  ## Check if code is formatted (CI-friendly)
	ruff format --check src tests

lint-fix:  ## Lint and auto-fix issues
	ruff check --fix src tests

migrate:  ## Run database migrations
	alembic upgrade head

migrate-create:  ## Create a new migration (usage: make migrate-create MESSAGE="description")
	@if [ -z "$(MESSAGE)" ]; then \
		echo "Error: MESSAGE is required. Usage: make migrate-create MESSAGE=\"your message\""; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(MESSAGE)"

migrate-rollback:  ## Rollback last migration
	alembic downgrade -1

clean:  ## Clean Python cache files
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
