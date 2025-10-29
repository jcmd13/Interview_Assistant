.PHONY: help install test test-verbose test-unit test-integration coverage lint format clean run dev setup

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Interview Assistant - Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# Setup and Installation
# ============================================================================

setup: ## Set up development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "$(GREEN)✓ Development environment ready$(NC)"
	@echo "Run: source venv/bin/activate"

install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-dev: install ## Install dev dependencies
	@echo "$(BLUE)Installing dev dependencies...$(NC)"
	pip install pytest pytest-asyncio pytest-cov pytest-mock black flake8 mypy
	@echo "$(GREEN)✓ Dev dependencies installed$(NC)"

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	python -m pytest tests/ -v --tb=short

test-verbose: ## Run all tests with verbose output
	@echo "$(BLUE)Running all tests (verbose)...$(NC)"
	python -m pytest tests/ -vv --tb=long

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	python -m pytest tests/ -v -m unit --tb=short

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	python -m pytest tests/ -v -m integration --tb=short

test-fast: ## Run fast tests (exclude slow marker)
	@echo "$(BLUE)Running fast tests...$(NC)"
	python -m pytest tests/ -v -m "not slow" --tb=short

test-single: ## Run a single test (use TEST=path/to/test.py::test_name)
	@echo "$(BLUE)Running test: $(TEST)$(NC)"
	python -m pytest $(TEST) -v --tb=short

coverage: ## Generate coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	python -m pytest tests/ \
		--cov=src \
		--cov-report=html:htmlcov \
		--cov-report=term-missing \
		--cov-report=xml \
		--cov-branch
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(NC)"
	flake8 src tests --max-line-length=100 --extend-ignore=E203,W503
	@echo "$(GREEN)✓ Linting passed$(NC)"

format: ## Format code with Black
	@echo "$(BLUE)Formatting code with Black...$(NC)"
	black src tests --line-length=100
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting without changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	black src tests --line-length=100 --check
	@echo "$(GREEN)✓ Code formatting is correct$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	mypy src --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking passed$(NC)"

quality: lint type-check ## Run all quality checks

# ============================================================================
# Running the Application
# ============================================================================

run: ## Run the server
	@echo "$(BLUE)Starting Interview Assistant server...$(NC)"
	python server.py

run-legacy: ## Run the legacy server (backward compatibility)
	@echo "$(BLUE)Starting legacy server...$(NC)"
	python optimized_stt_server_v3.py

dev: ## Run server with debug logging
	@echo "$(BLUE)Starting server in development mode...$(NC)"
	DEBUG=true VERBOSE_BUFFER=true python server.py

client: ## Run the audio client
	@echo "$(BLUE)Starting audio client...$(NC)"
	python stable_audio_client_multi_os.py

list-devices: ## List available audio devices
	@echo "$(BLUE)Listing audio devices...$(NC)"
	python stable_audio_client_multi_os.py --list-devices

# ============================================================================
# Cleanup
# ============================================================================

clean: clean-test clean-build clean-cache ## Remove all build, test, and Python artifacts

clean-build: ## Remove build artifacts
	@echo "$(BLUE)Removing build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.egg' -delete
	@echo "$(GREEN)✓ Build artifacts removed$(NC)"

clean-test: ## Remove test and coverage artifacts
	@echo "$(BLUE)Removing test artifacts...$(NC)"
	rm -rf .tox/
	rm -rf htmlcov/
	rm -f .coverage
	rm -f coverage.xml
	find . -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Test artifacts removed$(NC)"

clean-cache: ## Remove Python cache files
	@echo "$(BLUE)Removing Python cache files...$(NC)"
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.py[cod]' -delete
	find . -type f -name '*~' -delete
	@echo "$(GREEN)✓ Cache files removed$(NC)"

clean-all: clean ## Remove everything including virtual environment
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	rm -rf venv/
	@echo "$(GREEN)✓ All artifacts removed$(NC)"

# ============================================================================
# Docker (Future)
# ============================================================================

docker-build: ## Build Docker image (future)
	@echo "$(YELLOW)Docker build not yet implemented$(NC)"

docker-run: ## Run in Docker container (future)
	@echo "$(YELLOW)Docker support not yet implemented$(NC)"

# ============================================================================
# Development Utilities
# ============================================================================

status: ## Show git status
	git status

logs: ## Show recent commits
	git log --oneline -10

shell: ## Start Python shell with project context
	@echo "$(BLUE)Starting Python shell...$(NC)"
	python -c "from src.core import get_logger, get_config; log = get_logger('shell'); cfg = get_config(); print('Welcome to Interview Assistant shell'); print('Available: log, cfg')"

# ============================================================================
# CI/CD (Future)
# ============================================================================

ci-check: quality test ## Run all CI checks locally
	@echo "$(GREEN)✓ All CI checks passed$(NC)"

# ============================================================================
# Documentation (Future)
# ============================================================================

docs: ## Generate documentation (future)
	@echo "$(YELLOW)Documentation generation not yet implemented$(NC)"

# ============================================================================
# Version and Info
# ============================================================================

version: ## Show project version
	@python -c "from src import __version__; print('Interview Assistant v' + __version__)"

info: ## Show project information
	@echo "$(BLUE)Interview Assistant - Project Information$(NC)"
	@echo "Python version: $$(python --version)"
	@echo "Installed packages:"
	@pip list | grep -E "pytest|structlog|pydantic|websockets|torch|faster-whisper|ollama"
