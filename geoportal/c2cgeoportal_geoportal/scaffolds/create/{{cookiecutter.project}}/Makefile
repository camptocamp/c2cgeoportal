PROJECT_PUBLIC_URL=https://example.camptocamp.com/
PACKAGE={{cookiecutter.package}}
LANGUAGES=en fr de it

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets:"
	@grep --extended-regexp --no-filename '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "	%-20s%s\n", $$1, $$2}'

.PHONY: update-po-from-url
update-po-from-url: ## Update the po files from the URL provide by PROJECT_PUBLIC_URL
	curl $(PROJECT_PUBLIC_URL)locale.pot > geoportal/${PACKAGE}_geoportal/locale/${PACKAGE}_geoportal-client${SUFFIX}.pot
	sed -i '/^"POT-Creation-Date: /d' geoportal/${PACKAGE}_geoportal/locale/${PACKAGE}_geoportal-client${SUFFIX}.pot
	docker-compose run --rm -T tools update-po-only `id --user` `id --group` $(LANGUAGES)

.PHONY: update-po
update-po: ## Update the po files from the running composition
	docker-compose exec -T tools sh -c "USER_ID=`id --user` GROUP_ID=`id --group` make --directory=geoportal update-po"

.PHONY: checks
checks: prospector eslint ## Runs the checks

.PHONY: prospector
prospector: ## Runs the Prospector checks
	docker-compose run --entrypoint= --no-deps --rm --volume=$(pwd)/geoportal:/app geoportal \
		prospector --output-format=pylint --die-on-tool-error

.PHONY: eslint
eslint: ## Runs the eslint checks
	docker-compose run --entrypoint= --no-deps --rm --volume=$(pwd)/geoportal:/app geoportal \
		eslint $(find {{cookiecutter.package}} -type f -name '*.js' -print 2> /dev/null)
	docker-compose run --entrypoint= --no-deps --rm --volume=$(pwd)/geoportal:/app geoportal \
		eslint $(find {{cookiecutter.package}} -type f -name '*.ts' -print 2> /dev/null)
