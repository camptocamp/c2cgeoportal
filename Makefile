MAJOR_VERSION ?= 2.5
VERSION ?= 2.5.0

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets:"
	@grep --extended-regexp --no-filename '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "	%-20s%s\n", $$1, $$2}'

.PHONY: build
build: ## Build all docker images
build: build-main build-build build-scaffolds build-config-build

.PHONY: checks
checks: ## Run the application checks
	docker build --target=checks \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=VERSION=$(VERSION) .

.PHONY: build-build
build-build:
	docker build --target=builder --tag=camptocamp/geomapfish-build \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=VERSION=$(VERSION) .

.PHONY: build-scaffolds
build-scaffolds:
	docker build --target=upgrader --tag=camptocamp/geomapfish-scaffolds \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=VERSION=$(VERSION) .

.PHONY: build-config-build
build-config-build:
	docker build --tag=camptocamp/geomapfish-config-build \
		--build-arg=VERSION=$(MAJOR_VERSION) docker/config

.PHONY: build-tests
build-tests:
	docker build --target=build --tag=camptocamp/geomapfish-tests \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=VERSION=$(VERSION) .

.PHONY: build-main
build-main:
	docker build --target=runner --tag=camptocamp/geomapfish \
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
		--config=/opt/c2cgeoportal_commons/alembic.ini --name=main upgrade --sql head > $@

docker/test-db/13-alembic-static.sql:
	docker run --rm camptocamp/geomapfish alembic \
		--config=/opt/c2cgeoportal_commons/alembic.ini --name=static upgrade --sql head > $@

.PHONY: preparetest
preparetest: ## Run the compositon used to run the tests
preparetest: stoptest build-tests build-main build-test-db build-test-mapserver build-qgis-server-tests
	docker-compose up -d
	docker-compose exec tests wait-db
	docker-compose exec tests psql --command='DELETE FROM main_static.user_role'
	docker-compose exec tests psql --command='DELETE FROM main_static."user"'

.PHONY: stoptest
stoptest: ## Stop the compositon used to run the tests
	docker-compose stop --timeout=0
	docker-compose down --remove-orphans
