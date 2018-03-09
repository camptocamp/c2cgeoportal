BUILD_DIR ?= .build
VENV ?= ${BUILD_DIR}/venv

.PHONY: build
build: ${BUILD_DIR}/requirements.timestamp

.PHONY: cleanall
cleanall:
	rm -rf ${BUILD_DIR}

.PHONY: test
test: ${BUILD_DIR}/requirements.timestamp ${BUILD_DIR}/requirements-dev.timestamp
	# regenerate the database schema
	# ${VENV}/bin/initialize_db_main tests.ini#test_app --force=1
	# Run your project's tests.
	${VENV}/bin/pytest

.PHONY: check
check: flake8

.PHONY: flake8
flake8: ${BUILD_DIR}/requirements-dev.timestamp
	${VENV}/bin/flake8 c2cgeoportal_commons acceptance_tests

${BUILD_DIR}/venv.timestamp:
	# Create a Python virtual environment.
	virtualenv -p python3 ${VENV}
	touch $@

${BUILD_DIR}/requirements.timestamp: ${BUILD_DIR}/venv.timestamp requirements.txt setup.py
	#Install the project in editable mode.
	${VENV}/bin/pip install -r requirements.txt
	${VENV}/bin/pip install -e "."
	touch $@

${BUILD_DIR}/requirements-dev.timestamp: ${BUILD_DIR}/venv.timestamp setup.py
	# Install the project in editable mode with its testing requirements.
	${VENV}/bin/pip install -e .[testing]
	touch $@
