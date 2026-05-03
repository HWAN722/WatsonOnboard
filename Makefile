.PHONY: install test lint format run clean help

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code"
	@echo "  make run        - Run API server"
	@echo "  make clean      - Clean cache and build files"

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

lint:
	ruff check src tests
	mypy src

format:
	black src tests
	ruff check --fix src tests

run:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

clean:
	rm -rf .cache .chroma __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Made with Bob
