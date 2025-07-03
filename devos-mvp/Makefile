# DevOS MVP Makefile
# Provides common development and deployment tasks

.PHONY: help install test lint format clean build run dev docs

# Default target
help:
	@echo "DevOS MVP - Available commands:"
	@echo ""
	@echo "  install     Install dependencies and setup development environment"
	@echo "  test        Run the test suite"
	@echo "  test-cov    Run tests with coverage reporting"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black and isort"
	@echo "  clean       Clean up build artifacts and cache files"
	@echo "  build       Build the package"
	@echo "  run         Run the DevOS daemon"
	@echo "  dev         Run in development mode with auto-reload"
	@echo "  docs        Generate documentation"
	@echo "  check       Run all quality checks (lint, format, test)"
	@echo ""

# Installation
install:
	pip install -e ".[dev]"
	pre-commit install

install-prod:
	pip install -e .

# Testing
test:
	pytest tests/

test-unit:
	pytest tests/ -m "unit" 

test-integration:
	pytest tests/ -m "integration"

test-cov:
	pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

test-watch:
	pytest-watch tests/

# Code quality
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

format-check:
	black --check src/ tests/
	isort --check-only src/ tests/

# Build and packaging
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

build: clean
	python setup.py sdist bdist_wheel

# Running
run:
	python -m daemon.main

dev:
	python -m daemon.main --reload

cli:
	python -m cli.main

# Development setup
setup-dev: install
	mkdir -p ~/.devos/config
	mkdir -p ~/.devos/logs
	mkdir -p ~/.devos/data
	cp config/config.yaml ~/.devos/config/ || true

# Docker commands
docker-build:
	docker build -t devos-mvp .

docker-run:
	docker run -p 8080:8080 -v ~/.devos:/root/.devos devos-mvp

# Database commands
db-init:
	python -c "import sys; sys.path.insert(0, 'src'); from daemon.database import init_database; import asyncio; asyncio.run(init_database())"

db-migrate:
	alembic upgrade head

db-reset:
	rm -f ~/.devos/data/devos.db
	$(MAKE) db-init

# Documentation
docs:
	sphinx-build -b html docs/ docs/_build/

docs-serve:
	python -m http.server 8000 --directory docs/_build/

# Quality checks
check: format-check lint test

check-all: format-check lint test-cov

# Pre-commit hooks
pre-commit:
	pre-commit run --all-files

# Deployment
deploy-staging:
	# Add staging deployment commands here
	@echo "Deploy to staging not implemented yet"

deploy-prod:
	# Add production deployment commands here
	@echo "Deploy to production not implemented yet"

# Monitoring
logs:
	tail -f ~/.devos/logs/devos.log

status:
	curl -s http://localhost:8080/health | jq

metrics:
	curl -s http://localhost:8081/metrics

# Utilities
generate-config:
	python -c "import yaml; import sys; sys.path.insert(0, 'src'); from daemon.config import generate_default_config; print(yaml.dump(generate_default_config()))"

validate-config:
	python -c "import sys; sys.path.insert(0, 'src'); from daemon.config import validate_config; validate_config('~/.devos/config/config.yaml')"

# Security
security-scan:
	bandit -r src/

dependency-check:
	safety check

audit: security-scan dependency-check

# Performance
benchmark:
	python -c "import sys; sys.path.insert(0, 'src'); from tests.benchmarks import run_benchmarks; run_benchmarks()"

profile:
	python -m cProfile -o profile.stats -m daemon.main

# Environment management
env-create:
	python -m venv venv
	@echo "Activate with: source venv/bin/activate"

env-update:
	pip install --upgrade pip
	pip install -e ".[dev]"

# Release management
version:
	python setup.py --version

bump-patch:
	bumpversion patch

bump-minor:
	bumpversion minor

bump-major:
	bumpversion major

release: check build
	twine upload dist/*

# Container orchestration
k8s-deploy:
	kubectl apply -f k8s/

k8s-delete:
	kubectl delete -f k8s/

helm-install:
	helm install devos ./helm/devos

helm-upgrade:
	helm upgrade devos ./helm/devos

# Backup and restore
backup:
	tar -czf devos-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz ~/.devos/

restore:
	@echo "Usage: make restore BACKUP=devos-backup-YYYYMMDD-HHMMSS.tar.gz"
	@if [ -z "$(BACKUP)" ]; then echo "BACKUP parameter is required"; exit 1; fi
	tar -xzf $(BACKUP) -C /

# Development utilities
reset-dev: clean db-reset setup-dev
	@echo "Development environment reset complete"

quick-start: install setup-dev db-init
	@echo "Quick start setup complete"
	@echo "Run 'make run' to start DevOS"

# CI/CD helpers
ci-test:
	pytest tests/ --junitxml=test-results.xml --cov=src --cov-report=xml

ci-lint:
	flake8 src/ tests/ --output-file=flake8-report.txt || true
	mypy src/ --junit-xml=mypy-report.xml || true

ci-security:
	bandit -r src/ -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true