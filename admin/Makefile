BUILD_DIR?=.build
VENV?=${BUILD_DIR}/venv

GIT_HASH := $(shell git rev-parse HEAD)
DOCKER_BASE = camptocamp/c2cgeoportal
DOCKER_TAG ?= latest

.PHONY: buid
build: ${BUILD_DIR}/venv.timestamp \
	${BUILD_DIR}/commons.timestamp \
	${BUILD_DIR}/requirements.timestamp

.PHONY: init_db
init_db:
	#Configure the database:
	${VENV}/bin/initialize_db_main production.ini --force=1

.PHONY: test
test:
	#Run your project's tests.
	${VENV}/bin/pytest

.PHONY: serve
serve:
	#Run your project.
	${VENV}/bin/pserve production.ini

${BUILD_DIR}/venv.timestamp:
	#Create a Python virtual environment.
	python3 -m venv ${VENV}
	#Upgrade packaging tools.
	${VENV}/bin/pip install --upgrade pip==9.0.1 setuptools==36.5.0
	touch $@

${BUILD_DIR}/commons.timestamp: ../commons/setup.py
	${VENV}/bin/pip install -e "../commons"
	touch $@

${BUILD_DIR}/requirements.timestamp: setup.py
	#Install the project in editable mode with its testing requirements.
	${VENV}/bin/pip install -e ".[testing]"
	touch $@

.PHONY: build_admin
build_admin:
	cd .. ; \
	docker build -t $(DOCKER_BASE)_admin:$(DOCKER_TAG) --build-arg "GIT_HASH=$(GIT_HASH)" -f admin/Dockerfile .

.PHONY: pull
pull:
	for image in `find -name Dockerfile | xargs grep --no-filename FROM | awk '{print $$2}' | sort -u`; do docker pull $$image; done
	for image in `find -name "docker-compose*.yml" | xargs grep --no-filename "image:" | awk '{print $$2}' | sort -u | grep -v $(DOCKER_BASE) | grep -v rancher`; do docker pull $$image; done
