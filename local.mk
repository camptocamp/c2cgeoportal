VARS_FILE ?= local.yaml
VARS_FILES += local.yaml

VERSION = 2.5

include Makefile

docker-tag:
	docker tag camptocamp/geomapfish:latest camptocamp/geomapfish:$(VERSION)
	docker tag camptocamp/geomapfish-tools:latest camptocamp/geomapfish-tools:$(VERSION)
	docker tag camptocamp/geomapfish-config:latest camptocamp/geomapfish-config:$(VERSION)
