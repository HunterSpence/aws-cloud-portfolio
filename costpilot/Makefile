.PHONY: install test analyze report lint clean

install:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v --tb=short

analyze:
	python -m costpilot.cli analyze --days 30

report:
	python -m costpilot.cli report --format html --output reports/

lint:
	ruff check costpilot/ tests/
	ruff format --check costpilot/ tests/

format:
	ruff format costpilot/ tests/

clean:
	rm -rf reports/ __pycache__ .pytest_cache *.egg-info
	find . -name __pycache__ -exec rm -rf {} +
