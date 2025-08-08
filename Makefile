 .PHONY: install lint test run

install:
	pip install -e .[dev]

lint:
	ruff check src tests

test:
	pytest

run:
	uvicorn core.api:app --reload