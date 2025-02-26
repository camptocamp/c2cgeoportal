MAJOR_VERSION ?= $(shell scripts/get-version --major)
MAJOR_MINOR_VERSION ?= $(shell scripts/get-version --major-minor)
VERSION ?= $(shell scripts/get-version --full)
DOCKER_TAG ?= latest
MAIN_BRANCH ?= fake-local-branch
export MAJOR_VERSION
export DOCKER_BUILDKIT=1

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets:"
	@grep --extended-regexp --no-filename '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "	%-20s%s\n", $$1, $$2}'

.PHONY: build
build: ## Build all docker images
build: build-tools build-runner build-config

.PHONY: checks
checks: ## Run the application checks
checks: prospector additionallint

VALIDATE_PY_FOLDERS = commons admin \
	geoportal/setup.py \
	geoportal/c2cgeoportal_geoportal/*.py \
	geoportal/c2cgeoportal_geoportal/lib \
	geoportal/c2cgeoportal_geoportal/scripts \
	geoportal/c2cgeoportal_geoportal/views
VALIDATE_TEMPLATE_PY_FOLDERS = geoportal/c2cgeoportal_geoportal/scaffolds
VALIDATE_PY_TEST_FOLDERS = geoportal/tests

.PHONY: prospector
prospector: build-checks ## Run the prospector checker
	@docker run --rm camptocamp/geomapfish-checks:$(DOCKER_TAG) prospector --version
	@docker run --rm camptocamp/geomapfish-checks:$(DOCKER_TAG) mypy --version
	@docker run --rm camptocamp/geomapfish-checks:$(DOCKER_TAG) pylint --version --rcfile=/dev/null
	@docker run --rm camptocamp/geomapfish-checks:$(DOCKER_TAG) pyflakes --version
	docker run --rm --volume=$(shell pwd):/opt/c2cgeoportal camptocamp/geomapfish-checks:$(DOCKER_TAG) prospector --output-format=pylint --die-on-tool-error

.PHONY: additionallint
additionallint: ## Check that we should replace some strings in the code
	# Verify that we don't directly use the CI project name in the scaffolds
	@if [ "$(shell git grep testgeomapfish geoportal/c2cgeoportal_geoportal/scaffolds)" != "" ]; \
	then \
		echo "ERROR: You still have a testgeomapfish in one of your scaffolds"; \
		grep --recursive testgeomapfish geoportal/c2cgeoportal_geoportal/scaffolds; \
		false; \
	fi

	# Verify that we don't directly use the demo project name in the documentation
	@if [ "$(shell git grep demo_ doc|grep -v '^doc/integrator/extend_application.rst:')" != "" ]; \
	then \
		echo "ERROR: You still have a demo_ in your documentation"; \
		git grep demo_ doc; \
		false; \
	fi

.PHONY: build-tools
build-tools:
	docker build --target=tools --tag=camptocamp/geomapfish-tools:$(DOCKER_TAG) \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=MAJOR_MINOR_VERSION=$(MAJOR_MINOR_VERSION) --build-arg=VERSION=$(VERSION) .

.PHONY: build-checks
build-checks:
	docker build --target=checks --tag=camptocamp/geomapfish-checks:$(DOCKER_TAG) \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=VERSION=$(VERSION) .

.PHONY: build-config
build-config:
	docker build --tag=camptocamp/geomapfish-config:$(DOCKER_TAG) \
		--build-arg=VERSION=$(MAJOR_VERSION) --build-arg=MAJOR_MINOR_VERSION=$(MAJOR_MINOR_VERSION) docker/config

.PHONY: build-runner
build-runner:
	docker build --target=runner --tag=camptocamp/geomapfish:$(DOCKER_TAG) \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=MAJOR_MINOR_VERSION=$(MAJOR_MINOR_VERSION) --build-arg=VERSION=$(VERSION) .

QGIS_VERSION ?= 3.28-gdal3.7
.PHONY: build-qgisserver
build-qgisserver:
	docker build --target=runner --build-arg=VERSION=$(QGIS_VERSION) \
		--build-arg=GEOMAPFISH_VERSION=$(MAJOR_VERSION) \
		--tag=camptocamp/geomapfish-qgisserver:gmf${MAJOR_VERSION}-qgis$(QGIS_VERSION) docker/qgisserver

.PHONY: build-qgisserver-tests
build-qgisserver-tests:
	docker build --target=tests --build-arg=VERSION=$(QGIS_VERSION) \
		--build-arg=GEOMAPFISH_VERSION=$(MAJOR_VERSION) \
		--tag=camptocamp/geomapfish-qgisserver-tests docker/qgisserver

.PHONY: prospector-qgisserver
prospector-qgisserver: build-qgisserver-tests
	docker run --rm --volume=$(shell pwd)/docker/qgisserver:/src camptocamp/geomapfish-qgisserver-tests prospector --output-format=pylint --die-on-tool-error

.PHONY: build-test-db
build-test-db:
	docker build --tag=camptocamp/geomapfish-test-db docker/test-db

.PHONY: build-test-mapserver
build-test-mapserver:
	docker build --tag=camptocamp/geomapfish-test-mapserver docker/test-mapserver

.PHONY: tests
tests: ## Run all the unit tests
tests: tests-commons  tests-geoportal tests-admin tests-qgisserver

.PHONY: tests-commons
tests-commons: ## Run the commons unit tests
	docker compose exec -T tests pytest --verbose --color=yes \
		/opt/c2cgeoportal/commons/tests

.PHONY: tests-geoportal
tests-geoportal: ## Run the geoportal unit tests
	docker compose exec -T tests pytest --verbose --color=yes \
		/opt/c2cgeoportal/geoportal/tests

.PHONY: tests-admin
tests-admin: ## Run the admin unit tests
	docker compose exec -T tests pytest --verbose --color=yes \
		/opt/c2cgeoportal/admin/tests

.PHONY: tests-qgis
tests-qgisserver: ## Run the qgisserver unit tests
	docker compose exec -T qgisserver-tests pytest --verbose --color=yes \
		/src/tests/functional

.PHONY: preparetest
preparetest: ## Run the compositon used to run the tests
preparetest: stoptest build-tools build-test-db build-test-mapserver build-qgisserver-tests
	docker compose up -d
	docker compose exec -T tests wait-db
	docker compose exec -T tests alembic --config=/opt/c2cgeoportal/commons/alembic.ini --name=main \
		upgrade head
	docker compose exec -T tests alembic --config=/opt/c2cgeoportal/commons/alembic.ini --name=static \
		upgrade head
	docker compose exec -T tests psql --command='DELETE FROM main_static.user_role'
	docker compose exec -T tests psql --command='DELETE FROM main_static."user"'

.PHONY: stoptest
stoptest: ## Stop the compositon used to run the tests
	docker compose stop --timeout=0
	docker compose down --remove-orphans

.PHONY: doc
doc: build-tools ## Generate the documentation
	docker build --tag=camptocamp/geomapfish-doc \
	--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) \
	--build-arg=MAIN_BRANCH=$(MAIN_BRANCH) \
	doc
	ci/extract-documentation artifacts/documentations/


.PHONY: transifex
transifex:
	python3 -m pip install --user transifex-client

admin/c2cgeoportal_admin/locale/%/LC_MESSAGES/c2cgeoportal_admin.mo: transifex
	rm /tmp/c2ctemplate-cache.json
	make --makefile=build.mk $@

ADMIN_PO_FILES = admin/c2cgeoportal_admin/locale/fr/LC_MESSAGES/c2cgeoportal_admin.mo
.PHONY: dev
dev: $(ADMIN_PO_FILES) ## Generate a development environment that can be mount in a project container
	echo {} > geoportal/c2cgeoportal_geoportal/locale/en.json
	echo {} > geoportal/c2cgeoportal_geoportal/locale/fr.json
	echo {} > geoportal/c2cgeoportal_geoportal/locale/de.json
	echo {} > geoportal/c2cgeoportal_geoportal/locale/it.json
