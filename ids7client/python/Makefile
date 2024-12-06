SHELL=bash

.PHONY: format
format:
	isort .;
	black .

.PHONY: lint
lint:
	flake8 ids7client/
	bandit -c .bandit.yml -r ids7client/
	isort --check ids7client/
	black ids7client/ --check --diff
	mypy ids7client/
