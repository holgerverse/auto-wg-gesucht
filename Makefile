.ONESHELL:
SHELL = /bin/bash

THIS_FILE = $(lastword $(MAKEFILE_LIST))

CONDA_ENV_NAME = auto-wg-gesucht
CONDA_ACTIVATE = source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate $(CONDA_ENV_NAME)

.DEFAULT: help


.PHONY: help
help:
	@echo 'Makefile for "Auto-WG-Gesucht" development.'
	@echo ''
	@echo '  This Makefile only works with bash.'
	@echo ''
	@echo '  create-env           - Creates a virtual environemt using anaconda based on the environemt file.'
	@echo '  create-env-file      - Updates the environemt file based on the auto-wg-gesucht environment.'
	@echo '  activate-env         - Activates the auto-wg-gesucht environment. Only for usage inside the Makefile.'
	@echo '  deactivate-env       - Deactivates the auto-wg-gesucht environment.'
	@echo '  clean                - Runs all clean targets.'
	@echo '  clean-env            - Renoves the auto-wg-gesucht environment.'
	@echo '  clean-build          - Removes all by the build process generated files.'
	@echo '  clean-test           - Removes all by the test process generated files.'
	@echo '  clean-dist           - Removes all by the dist process generated files.'

.PHONY: create-env
create-env:
	conda env create -f environment.yml

.PHONY: activate-env
activate-env:
	$(CONDA_ACTIVATE)

.PHONY: create-env-file
create-env-file:
	@$(MAKE) -f $(THIS_FILE) activate-env
	conda env export -n $(CONDA_ENV_NAME) | grep -v "^prefix: " > environment.yml

.PHONY: deactivate-env
deactivate-env:
	conda deactivate

.PHONY: clean
clean: clean-env clean-build clean-test clean-dist

.PHONY: clean-env
clean-env:
	conda env remove -n $(CONDA_ENV_NAME) -y

.PHONY: clean-build
clean-build:
	-rm -rf __pycache__

.PHONY: clean-test
clean-test:
	-rm -rf .cache
	-rm -rf .coverage

.PHONY: clean-dist
clean-dist:
	-@rm -rf dist build