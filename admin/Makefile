BUILD_DIR?=.build
VENV?=${BUILD_DIR}/venv

.PHONY: buid
build: ${BUILD_DIR}/venv.timestamp \
	${BUILD_DIR}/commons.timestamp \
	${BUILD_DIR}/requirements.timestamp

.PHONY: init_db
init_db:
	#Configure the database:
	${VENV}/bin/initialize_db_main development.ini --force=1

.PHONY: test
test:
	#Run your project's tests.
	${VENV}/bin/pytest

.PHONY: serve
serve:
	#Run your project.
	${VENV}/bin/pserve development.ini

${BUILD_DIR}/venv.timestamp:
	#Create a Python virtual environment.
	python3 -m venv ${VENV}
	#Upgrade packaging tools.
	${VENV}/bin/pip install --upgrade pip setuptools
	touch $@

${BUILD_DIR}/commons.timestamp: ../commons/setup.py
	${VENV}/bin/pip install -e "../commons"
	touch $@

${BUILD_DIR}/requirements.timestamp: setup.py
	#Install the project in editable mode with its testing requirements.
	${VENV}/bin/pip install -e ".[testing]"
	touch $@

