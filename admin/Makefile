BUILD_DIR?=.build
VENV?=${BUILD_DIR}/venv

.PHONY: build
build: ${BUILD_DIR}/requirements.timestamp node_modules

.PHONY: cleanall
cleanall:
	rm -rf ${BUILD_DIR}
	rm -rf node_modules

.PHONY: test
test: build ${BUILD_DIR}/requirements-dev.timestamp
	#Run your project's tests.
	${VENV}/bin/pytest --driver Firefox

.PHONY: check
check: flake8

.PHONY: flake8
flake8: ${BUILD_DIR}/requirements-dev.timestamp
	${VENV}/bin/flake8 c2cgeoportal_admin acceptance_tests

.PHONY: init_db
init_db: ${BUILD_DIR}/requirements.timestamp
	#Configure the database:
	${VENV}/bin/initialize_db_main development.ini

.PHONY: serve
serve: build
	#Run your project.
	${VENV}/bin/pserve --reload development.ini

${BUILD_DIR}/venv.timestamp:
	#Create a Python virtual environment.
	virtualenv -p python3 ${VENV}
	#Upgrade packaging tools.
	${VENV}/bin/pip install --upgrade pip==9.0.1 setuptools==36.5.0
	touch $@

${BUILD_DIR}/requirements.timestamp: ${BUILD_DIR}/venv.timestamp ../commons/setup.py setup.py requirements.txt
	#Install the project in editable mode.
	${VENV}/bin/pip install -e "../commons"
	${VENV}/bin/pip install -r requirements.txt
	${VENV}/bin/pip install -e "."
	touch $@

${BUILD_DIR}/requirements-dev.timestamp: ${BUILD_DIR}/venv.timestamp setup.py
	#Install the project in editable mode with its testing requirements.
	${VENV}/bin/pip install -e ".[testing]"
	touch $@

.PHONY: node_modules
node_modules: package.json
	npm install
