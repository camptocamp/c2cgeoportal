.PHONY: build
build: build-config build-geoportal build-geoportal-dev .env

.PHONY: build-config
build-config:
	docker build --tag=$(DOCKER_BASE)-config$(DOCKER_TAG) \
		--build-arg=PGSCHEMA=$(PGSCHEMA) .

.PHONY: build-geoportal
build-geoportal:
	docker build --tag=$(DOCKER_BASE)-geoportal$(DOCKER_TAG) \
		--build-arg=PGSCHEMA=$(PGSCHEMA) --build-arg=GIT_HASH=$(GIT_HASH) geoportal

.PHONY: build-geoportal-dev
build-geoportal-dev:
	docker build --target=builder --tag=$(DOCKER_BASE)-geoportal-dev$(DOCKER_TAG) \
		--build-arg=PGSCHEMA=$(PGSCHEMA) --build-arg=GIT_HASH=$(GIT_HASH) geoportal

.env: $(ENV_FILES)
	cat $^ > $@
