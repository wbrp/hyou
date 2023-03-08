POETRY := $(bash command -v poetry 2> /dev/null)

.PHONY: poetry_check
poetry_check:
ifndef POETRY
	@echo "Please, install poetry: https://python-poetry.org/docs/"
	@exit 1
endif

.PHONY: check_format
check_format:  ## Run code format checks
	poetry run black hyou test tools --check --diff

.PHONY: check_style
check_style:  ## Run style checks
	poetry run pylint hyou test tools

.PHONY: check
check: check_format check_style  ## Run the format and style checks

.PHONY: test
test:  ## Run the tests
	poetry install
	poetry run pytest -v --cov=hyou

.PHONY: quality
quality: check test  ## Run the format/style checks and the tests

.PHONY: help
help:  ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
