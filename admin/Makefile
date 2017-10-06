BUILD_DIR?=.build
VENV?=${BUILD_DIR}/venv

.PHONY: build
build: ${BUILD_DIR}/requirements.timestamp

.PHONY: cleanall
cleanall:
	rm -rf ${BUILD_DIR}

.PHONY: test
test: ${BUILD_DIR}/requirements.timestamp ${BUILD_DIR}/requirements-dev.timestamp
	#Run your project's tests.
	${VENV}/bin/pytest --driver Firefox

.PHONY: check
check: flake8

.PHONY: flake8
flake8: ${BUILD_DIR}/requirements-dev.timestamp
	${VENV}/bin/flake8 c2cgeoportal_admin acceptance_tests

.PHONY: init_db
init_db:
	#Configure the database:
	${VENV}/bin/initialize_db_main development.ini

.PHONY: serve
serve: ${BUILD_DIR}/requirements.timestamp
	#Run your project.
	${VENV}/bin/pserve development.ini

${BUILD_DIR}/venv.timestamp:
	#Create a Python virtual environment.
	python3 -m venv ${VENV}
	#Upgrade packaging tools.
	${VENV}/bin/pip install --upgrade pip==9.0.1 setuptools==36.5.0
	touch $@

${BUILD_DIR}/requirements.timestamp: ${BUILD_DIR}/venv.timestamp ../commons/setup.py setup.py
	#Install the project in editable mode.
	${VENV}/bin/pip install -e "../commons"
	${VENV}/bin/pip install -e "."
	touch $@

${BUILD_DIR}/requirements-dev.timestamp: ${BUILD_DIR}/venv.timestamp setup.py
	#Install the project in editable mode with its testing requirements.
	${VENV}/bin/pip install -e ".[testing]"
	touch $@
