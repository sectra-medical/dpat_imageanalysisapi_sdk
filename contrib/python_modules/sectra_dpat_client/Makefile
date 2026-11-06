SHELL=bash

.PHONY: format
format:
	uv run isort .;
	uv run black .

.PHONY: lint
lint:
	uv run flake8 sectra_dpat_client/
	uv run bandit -c .bandit.yml -r sectra_dpat_client/
	uv run isort --check sectra_dpat_client/
	uv run black sectra_dpat_client/ --check --diff
	uv run mypy sectra_dpat_client/
