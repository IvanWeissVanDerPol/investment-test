# Investment Analysis System Makefile
# Provides common development and analysis commands

.PHONY: help install dev-install clean test lint format type-check analysis monitor setup

# Default target
help:
	@echo "Investment Analysis System - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make setup         - Complete development environment setup"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format        - Format code with black and isort"
	@echo "  make lint          - Run linting checks"
	@echo "  make type-check    - Run type checking with mypy"
	@echo "  make test          - Run test suite"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo ""
	@echo "Investment Analysis:"
	@echo "  make quick         - Run quick daily analysis"
	@echo "  make comprehensive - Run comprehensive analysis"
	@echo "  make portfolio     - Check portfolio status"
	@echo "  make monitor       - Run system monitoring"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         - Clean cache and temporary files"
	@echo "  make clean-reports - Clean old reports (>30 days)"
	@echo "  make validate      - Run pre-analysis validation"

# Installation targets
install:
	@echo "Installing production dependencies..."
	pip install -r requirements.txt

dev-install: install
	@echo "Installing development dependencies..."
	pip install pytest pytest-cov black isort flake8 mypy pre-commit psutil memory-profiler

setup: dev-install
	@echo "Setting up development environment..."
	pre-commit install
	@echo "Creating test directories..."
	mkdir -p tests reports cache
	@echo "Setup complete!"

# Code quality targets
format:
	@echo "Formatting code with black..."
	cd tools && python -m black *.py
	@echo "Organizing imports with isort..."
	cd tools && python -m isort *.py

lint:
	@echo "Running flake8 linting..."
	cd tools && python -m flake8 *.py --max-line-length=88 --ignore=E203,W503

type-check:
	@echo "Running mypy type checking..."
	cd tools && python -m mypy *.py --ignore-missing-imports

# Testing targets
test:
	@echo "Running test suite..."
	python -m pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	python -m pytest tests/ --cov=tools --cov-report=term-missing --cov-report=html

test-quick:
	@echo "Running quick tests only..."
	python -m pytest tests/ -m "not slow" -v

# Investment analysis targets
quick:
	@echo "Running quick daily analysis..."
	cd tools && python quick_analysis.py

comprehensive:
	@echo "Running comprehensive analysis..."
	cd tools && python comprehensive_analyzer.py

portfolio:
	@echo "Checking portfolio status..."
	cd tools && python -c "from portfolio_analysis import get_portfolio_status; get_portfolio_status()"

monitor:
	@echo "Running system monitoring..."
	cd tools && python -c "exec(open('../.claude/hooks/pre_analysis_hook.py').read())"

# Validation and hooks
validate:
	@echo "Running pre-analysis validation..."
	python .claude/hooks/pre_analysis_hook.py

post-validate:
	@echo "Running post-analysis validation..."
	python .claude/hooks/post_analysis_hook.py

# Maintenance targets
clean:
	@echo "Cleaning cache and temporary files..."
	rm -rf tools/__pycache__/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

clean-reports:
	@echo "Cleaning old reports (>30 days)..."
	cd tools && python -c "from pathlib import Path; import time; [f.unlink() for f in Path('../reports').glob('*') if time.time() - f.stat().st_mtime > 2592000]"

clean-cache:
	@echo "Cleaning cache files..."
	rm -rf cache/*

# Analysis shortcuts for Windows
quick-win:
	@echo "Running quick analysis (Windows)..."
	cd tools && python quick_analysis.py
	@echo "Analysis complete! Check reports folder."

comprehensive-win:
	@echo "Running comprehensive analysis (Windows)..."
	cd tools && python comprehensive_analyzer.py
	@echo "Comprehensive analysis complete! Check reports folder."

# Development workflow
dev-check: format lint type-check test
	@echo "Development checks complete!"

ci-check: lint type-check test-cov
	@echo "CI checks complete!"

# Investment-specific targets
ai-analysis:
	@echo "Running AI/Robotics focused analysis..."
	cd tools && python -c "from comprehensive_analyzer import ComprehensiveAnalyzer; analyzer = ComprehensiveAnalyzer(); analyzer.analyze_ai_sector()"

risk-check:
	@echo "Running portfolio risk assessment..."
	cd tools && python risk_management.py --portfolio-analysis --balance=900

smart-money:
	@echo "Checking smart money activity..."
	cd tools && python smart_money_tracker.py --update

news-sentiment:
	@echo "Running news sentiment analysis..."
	cd tools && python news_sentiment_analyzer.py --target-stocks

# Documentation
docs:
	@echo "Key documentation files:"
	@echo "  README.md - Project overview"
	@echo "  CLAUDE.md - Claude Code guidance"
	@echo "  .claude/commands/ - Slash commands"
	@echo "  reports/ - Analysis reports"

# Aliases for common operations
all-checks: format lint type-check test
daily: validate quick post-validate
weekly: validate comprehensive post-validate risk-check
monthly: comprehensive ai-analysis smart-money news-sentiment

# System information
info:
	@echo "Investment Analysis System Information:"
	@echo "Python version: $(shell python --version)"
	@echo "Working directory: $(shell pwd)"
	@echo "Available balance: $900 (Dukascopy)"
	@echo "Risk tolerance: Medium"
	@echo "Target focus: AI/Robotics stocks and ETFs"