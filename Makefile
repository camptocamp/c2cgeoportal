MAJOR_VERSION ?= $(shell scripts/get-version --major)
VERSION ?= $(shell scripts/get-version --full)
DOCKER_TAG ?= latest
PIPENV_PIPFILE ?= ci/Pipfile
export PIPENV_PIPFILE

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
checks: black gitattributes eol codespell yamllint otherchecks

pipenv.timestamp:
	pipenv install

.PHONY: black
black: ## Run Black check
black: pipenv.timestamp
	pipenv run black --version
	pipenv run black --check --diff $(shell \
		find -name .git -prune -or -type f -print | \
		file --mime-type --files-from - | \
		grep text/x-python | \
		grep --invert-match '\(\.mako\|\.rst\|_tmpl\):' | \
		awk -F: '{print $$1}' \
	)

.PHONY: black-fix
black-fix: ## Fix the application code style with black
black-fix: pipenv.timestamp
	pipenv run black $(shell \
		find -name .git -prune -or -type f -print | \
		file --mime-type --files-from - | \
		grep text/x-python | \
		grep --invert-match '\(\.mako\|\.rst\|_tmpl\):' | \
		awk -F: '{print $$1}' \
	)

.PHONY: gitattributes
gitattributes: ## Run git attributes check
	git --no-pager diff --check a6eacf93706d94606fb3c68a671f8254aea48e3b

.PHONY: eol
eol:
eol: ## Check end of lines
	python3 ci/test-eof-newline

.PHONY: codespell
codespell: ## Check code spell
codespell: pipenv.timestamp
	pipenv run codespell --quiet-level=2 --check-filenames --ignore-words=spell-ignore-words.txt \
		$(shell find -name .git -prune -print)

.PHONY: yamllint
yamllint: ## YAML lint
yamllint: pipenv.timestamp
	pipenv run yamllint --strict --config-file=yamllint.yaml -s $(shell \
		find -name .git -prune -or -name changelog.yaml -prune -or \
		\( -name "*.yml" -or -name "*.yaml" \) -print \
	)

.PHONY: otherchecks
otherchecks:
	docker build --target=checks \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=VERSION=$(VERSION) .

.PHONY: isort-fix
isort-fix: build-tools
isort-fix: ## Fix the application import order with isort
	docker run --rm --volume=`pwd`:/src camptocamp/geomapfish-tools:$(DOCKER_TAG) \
		make --makefile=checks.mk isort-fix


.PHONY: build-tools
build-tools:
	docker build --target=tools --tag=camptocamp/geomapfish-tools:$(DOCKER_TAG) \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=VERSION=$(VERSION) .

.PHONY: build-config
build-config:
	docker build --tag=camptocamp/geomapfish-config:$(DOCKER_TAG) \
		--build-arg=VERSION=$(MAJOR_VERSION) docker/config

.PHONY: build-runner
build-runner:
	docker build --target=runner --tag=camptocamp/geomapfish:$(DOCKER_TAG) \
		--build-arg=MAJOR_VERSION=$(MAJOR_VERSION) --build-arg=VERSION=$(VERSION) .

QGIS_VERSION ?= latest
.PHONY: build-qgisserver
build-qgisserver: build-runner
	docker tag camptocamp/geomapfish:$(DOCKER_TAG) camptocamp/geomapfish
	docker build --target=runner --build-arg=VERSION=$(QGIS_VERSION) \
		--tag=camptocamp/geomapfish-qgisserver:gmf${MAJOR_VERSION}-qgis$(QGIS_VERSION) docker/qgisserver

.PHONY: build-test-db
build-test-db:
	docker build --tag=camptocamp/geomapfish-test-db docker/test-db

.PHONY: build-test-mapserver
build-test-mapserver:
	docker build --tag=camptocamp/geomapfish-test-mapserver docker/test-mapserver

.PHONY: build-qgis-server-tests
build-qgis-server-tests: build-runner
	docker tag camptocamp/geomapfish:$(DOCKER_TAG) camptocamp/geomapfish
	docker build --target=tests --build-arg=VERSION=3.10 \
		--tag=camptocamp/geomapfish-qgisserver-tests docker/qgisserver

.PHONY: tests
tests: ## Run all the unit tests
tests: tests-commons  tests-geoportal tests-admin tests-qgisserver

.PHONY: tests-commons
tests-commons: ## Run the commons unit tests
	docker-compose exec -T tests pytest --verbose --color=yes \
		/opt/c2cgeoportal/commons/tests

.PHONY: tests-geoportal
tests-geoportal: ## Run the geoportal unit tests
	docker-compose exec -T tests pytest --verbose --color=yes \
		/opt/c2cgeoportal/geoportal/tests

.PHONY: tests-admin
tests-admin: ## Run the admin unit tests
	docker-compose exec -T tests pytest --verbose --color=yes \
		/opt/c2cgeoportal/admin/tests

.PHONY: tests-qgis
tests-qgisserver: ## Run the qgisserver unit tests
	docker-compose exec -T qgisserver-tests pytest --verbose --color=yes \
		/src/tests/functional

.PHONY: preparetest
preparetest: ## Run the compositon used to run the tests
preparetest: stoptest build-tools build-test-db build-test-mapserver build-qgis-server-tests
	docker-compose up -d
	docker-compose exec -T tests wait-db
	docker-compose exec -T tests alembic --config=/opt/c2cgeoportal/commons/alembic.ini --name=main \
		upgrade head
	docker-compose exec -T tests alembic --config=/opt/c2cgeoportal/commons/alembic.ini --name=static \
		upgrade head
	docker-compose exec -T tests psql --command='DELETE FROM main_static.user_role'
	docker-compose exec -T tests psql --command='DELETE FROM main_static."user"'

.PHONY: stoptest
stoptest: ## Stop the compositon used to run the tests
	docker-compose stop --timeout=0
	docker-compose down --remove-orphans
