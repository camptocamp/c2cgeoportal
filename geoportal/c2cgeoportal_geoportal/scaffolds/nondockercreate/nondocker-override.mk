# This file override and improve some rules for CONST_Makefile for non Docker production environment

DEPLOY ?= TRUE
DOCKER ?= FALSE
ENVIRONMENT ?= INSTANCE_ID
CONFIG_VARS += instanceid
MODWSGI_USER ?= www-data
export MODWSGI_USER
export INSTANCE_ID
TINYOWS_URL ?= http://tinyows/
export TINYOWS_URL
MAPSERVER_URL ?= http://mapserver/
export MAPSERVER_URL
PRINT_URL ?= http://print:8080/print/
export PRINT_URL
PRINT_CONFIG_FILE ?= print/print-apps/$(PACKAGE)/config.yaml
ifeq ($(TILECLOUD_CHAIN), TRUE)
MAPCACHE_FILE ?= apache/mapcache.xml
endif
TILEGENERATION_CONFIG_FILE = tilegeneration/config.yaml

VISIBLE_WEB_PROTOCOL ?= https
VISIBLE_WEB_PORT ?= 443
VISIBLE_ENTRY_POINT ?= /$(INSTANCE_ID)/
export VISIBLE_WEB_HOST
export VISIBLE_WEB_PROTOCOL
export VISIBLE_ENTRY_POINT

ADDITIONAL_MAKO_FILES += $(shell find print $(FIND_OPTS) -name "*.mako" -print) \
	$(shell find apache $(FIND_OPTS) -name "*.mako" -print) \
	$(shell find deploy $(FIND_OPTS) -name "*.mako" -print) \
	geoportal/development.ini.mako geoportal/production.ini.mako


CONF_FILES += apache/application.wsgi
CONF_FILES_MAKO = $(shell ls -1 apache/*.conf.mako 2> /dev/null)
CONF_FILES_JINJA = $(shell ls -1 apache/*.conf.jinja 2> /dev/null)
CONF_FILES += $(shell ls -1 apache/*.conf 2> /dev/null) $(CONF_FILES_MAKO:.mako=) $(CONF_FILES_JINJA:.jinja=)

PGHOST ?= localhost
export PGHOST
PGHOST_SLAVE ?= localhost
export PGHOST_SLAVE
PGPORT ?= 5432
export PGPORT
PGUSER ?= www-data
export PGUSER
PGPASSWORD ?= www-data
export PGPASSWORD
PGDATABASE ?= geomapfish
export PGDATABASE
PGSCHEMA ?= main
export PGSCHEMA
PGSCHEMA_STATIC ?= main_static
export PGSCHEMA_STATIC

DEFAULT_BUILD_RULES ?= docker-build-geoportal \
	docker-build-config \
	project.yaml \
	geoportal/alembic.ini \
	geoportal/alembic.yaml

TILECLOUD_CHAIN ?= TRUE
ifeq ($(TILECLOUD_CHAIN), TRUE)
CONF_FILES += $(MAPCACHE_FILE)
endif

UPGRADE_ARGS += --nondocker --makefile=$(firstword $(MAKEFILE_LIST))

include CONST_Makefile

build: $(ADDITIONAL_MAKO_FILES:.mako=)
ifeq (${DEPOY}, TRUE)
build: deploy/deploy.cfg
endif

# Tile cloud chain
apache/mapcache.xml: tilegeneration/config.yaml
	$(PRERULE_CMD)
	generate_controller --generate-mapcache-config

docker-build-config:
	$(PRERULE_CMD)
	@echo "Nothing to do for $@"

docker-build-geoportal: $(CONF_FILES)
	$(PRERULE_CMD)
	@echo "Nothing to do for $@"

docker-build-testdb:
	$(PRERULE_CMD)
	@echo "Nothing to do for $@"
