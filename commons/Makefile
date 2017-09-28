BUILD_DIR?=.build
VENV?=${BUILD_DIR}/venv

.PHONY: install
install: ${BUILD_DIR}/requirements.timestamp

cleanall:
	rm -rf ${BUILD_DIR}

.PHONY: test
test: ${BUILD_DIR}/requirements.timestamp
	# regenerate the database schema
	#${VENV}/bin/initialize_db_main tests.ini#test_app --force=1
	#Run your project's tests.
	${VENV}/bin/pytest

${BUILD_DIR}/requirements.timestamp: ${BUILD_DIR}/venv.timestamp setup.py
	#Install the project in editable mode with its testing requirements.
	${VENV}/bin/pip install -r requirements.txt
	${VENV}/bin/pip install -e ".[testing]"
	touch $@

${BUILD_DIR}/venv.timestamp:
	#Create a Python virtual environment.
	python3 -m venv ${VENV}
	#Upgrade packaging tools.
	${VENV}/bin/pip install --upgrade pip==9.0.1 setuptools==36.5.0
	touch $@
