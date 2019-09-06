MAJOR_VERSION ?= 2.5
VERSION ?= 2.5.0
DOCKER_TAG ?= latest

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets:"
	@grep --extended-regexp --no-filename '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "	%-20s%s\n", $$1, $$2}'

.PHONY: build
build: ## Build all docker images
build: build-tools build-runner build-config-build

.PHONY: checks
checks: ## Run the application checks
	docker build --target=checks \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=VERSION=$(VERSION) .

.PHONY: build-tools
build-tools:
	docker build --target=tools --tag=camptocamp/geomapfish-tools:$(DOCKER_TAG) \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=VERSION=$(VERSION) .

.PHONY: build-config-build
build-config-build:
	docker build --tag=camptocamp/geomapfish-config-build:$(DOCKER_TAG) \
		--build-arg=VERSION=$(MAJOR_VERSION) docker/config

.PHONY: build-runner
build-runner:
	docker build --target=runner --tag=camptocamp/geomapfish:$(DOCKER_TAG) \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=VERSION=$(VERSION) .

.PHONY: build-test-db
build-test-db: docker/test-db/12-alembic.sql docker/test-db/13-alembic-static.sql
	docker build --tag=camptocamp/geomapfish-test-db docker/test-db

.PHONY: build-test-mapserver
build-test-mapserver:
	docker build --tag=camptocamp/geomapfish-test-mapserver docker/test-mapserver

.PHONY: build-qgis-server-tests
build-qgis-server-tests:
	docker build --target=tests --build-arg=VERSION=3.4 \
		--tag=camptocamp/geomapfish-qgisserver-tests docker/qgisserver

docker/test-db/12-alembic.sql:
	docker run --rm camptocamp/geomapfish alembic \
		--config=/opt/c2cgeoportal/commons/alembic.ini --name=main upgrade --sql head > $@

docker/test-db/13-alembic-static.sql:
	docker run --rm camptocamp/geomapfish alembic \
		--config=/opt/c2cgeoportal/commons/alembic.ini --name=static upgrade --sql head > $@

.PHONY: preparetest
preparetest: ## Run the compositon used to run the tests
preparetest: stoptest build-tools build-test-db build-test-mapserver build-qgis-server-tests
	docker-compose up -d
	docker-compose exec tests wait-db
	docker-compose exec tests psql --command='DELETE FROM main_static.user_role'
	docker-compose exec tests psql --command='DELETE FROM main_static."user"'

.PHONY: stoptest
stoptest: ## Stop the compositon used to run the tests
	docker-compose stop --timeout=0
	docker-compose down --remove-orphans
