DOCKER_BASE ?= camptocamp/geomapfish
MAJOR_VERSION ?= 2.4

.PHONY: prepare-tests  # local target for development purpose
prepare-tests:
	cd ../.. && ./docker-run make docker-build-testdb
	cd ../.. && ./docker-run docker build \
		--build-arg=VERSION=3.4 \
		--tag=$(DOCKER_BASE)-qgisserver:gmf$(MAJOR_VERSION)-qgis3.4 \
		docker/qgisserver
	cd ../.. && ./docker-run make docker/qgisserver/tests/geomapfish.yaml

.PHONY: build-tests
build-tests: ./tests/docker-entrypoint.d/wait-db tests/geomapfish.yaml
	cd tests && docker-compose build qgisserver-tests

.PHONY: tests
tests: build-tests
	cd tests && docker-compose run --rm qgisserver-tests

.PHONY: clean
clean:
	find . -type d -name __pycache__ | xargs rm -rf
	find . -type d -name .pytest_cache | xargs rm -rf
	rm --force tests/geomapfish.yaml
	rm --force ./tests/docker-entrypoint.d/wait-db

./tests/docker-entrypoint.d/wait-db: ../build/bin/wait-db
	mkdir -p $(dir $@)
	cp $< $@
