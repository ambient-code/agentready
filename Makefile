.PHONY: help install test lint format clean demos demo-slides demo-validate demo-record demo-serve docs-serve

# Default target
help:
	@echo "AgentReady Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make install         - Install package in development mode"
	@echo "  make test            - Run test suite"
	@echo "  make lint            - Run linters (ruff, black --check, isort --check)"
	@echo "  make format          - Format code (black, isort)"
	@echo "  make clean           - Clean build artifacts"
	@echo ""
	@echo "Demo targets:"
	@echo "  make demos           - Build all demo assets (slides + validate)"
	@echo "  make demo-slides     - Generate reveal.js slides"
	@echo "  make demo-validate   - Validate all demo files"
	@echo "  make demo-record     - Record terminal demo (interactive)"
	@echo "  make demo-serve      - Serve documentation locally with Jekyll"
	@echo ""
	@echo "Documentation targets:"
	@echo "  make docs-serve      - Serve docs with Jekyll (requires bundle install)"
	@echo ""

# Installation
install:
	uv pip install -e .

# Testing
test:
	pytest

test-coverage:
	pytest --cov=src/agentready --cov-report=html --cov-report=term

# Linting
lint:
	@echo "Running ruff..."
	ruff check src/ tests/
	@echo "Running black (check only)..."
	black --check src/ tests/
	@echo "Running isort (check only)..."
	isort --check-only src/ tests/

# Formatting
format:
	@echo "Running black..."
	black src/ tests/
	@echo "Running isort..."
	isort src/ tests/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete

# Demo targets
demos: demo-slides demo-validate
	@echo ""
	@echo "✅ All demo assets built successfully!"

demo-slides:
	@echo "📊 Generating reveal.js slides..."
	python scripts/generate_slides.py --verbose

demo-validate:
	@echo "🔍 Validating demo files..."
	python scripts/build_demos.py validate --verbose

demo-record:
	@echo "🎬 Recording terminal demo..."
	@echo "This will launch an interactive recording session."
	@echo "Press Ctrl+C to cancel, or ENTER to continue..."
	@read -p "" && bash scripts/record_demo.sh

demo-preview-quick:
	@echo "🚀 Opening slides in default browser..."
	@if [ "$(shell uname)" = "Darwin" ]; then \
		open docs/demos/slides.html; \
	else \
		xdg-open docs/demos/slides.html 2>/dev/null || echo "Please open docs/demos/slides.html manually"; \
	fi

demo-serve: docs-serve

# Documentation
docs-serve:
	@echo "🌐 Starting Jekyll server..."
	@echo "Documentation will be available at http://localhost:4000/agentready/"
	@echo "Press Ctrl+C to stop the server."
	cd docs && bundle exec jekyll serve --livereload

# Build everything (for CI/CD)
build: format lint test demos
	@echo "✅ Build complete!"
