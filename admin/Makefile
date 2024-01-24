# Used for development purpose: please do not remove this file

DOCKER_BASE ?= camptocamp/c2cgeoportal
DOCKER_TAG ?= latest
export DOCKER_BUILDKIT ?= 1

default: help

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@grep -Eh '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "    %-20s%s\n", $$1, $$2}'

.PHONY: preparedev
preparedev: ## Run this once before serve
	make --directory=.. build-runner
	docker buildx rm --all-inactive --force # to be sure that we get the new image
	docker compose build
	docker compose up --detach db
	docker compose run --rm admin wait-db || (docker-compose logs db && false)
	docker compose run --rm admin alembic --config=/opt/c2cgeoportal/commons/alembic.ini --name=main upgrade head
	docker compose run --rm admin alembic --config=/opt/c2cgeoportal/commons/alembic.ini --name=static upgrade head

.PHONY: serve
serve: ## Run c2cgeoportal_admin in development mode
	docker compose up --detach

.PHONY: clean
clean: ## Stop composition, remove container and images
	docker compose down --remove-orphans
	docker image rm $(DOCKER_BASE)_admin:$(DOCKER_TAG)
