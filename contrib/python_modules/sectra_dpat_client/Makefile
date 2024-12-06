SHELL=bash

.PHONY: format
format:
	isort .;
	black .

.PHONY: lint
lint:
	flake8 sectra_dpat_client/
	bandit -c .bandit.yml -r sectra_dpat_client/
	isort --check sectra_dpat_client/
	black sectra_dpat_client/ --check --diff
	mypy sectra_dpat_client/
