# This file override and improve some rules for CONST_Makefile for non Docker production environment

DEPLOY ?= TRUE
ENVIRONEMENT ?= INSTANCE_ID
CONFIG_VARS += instanceid
MODWSGI_USER ?= www-data
export MODWSGI_USER
export INSTANCE_ID
VISIBLE_ENTRY_POINT ?= /$(INSTANCE_ID)/
export VISIBLE_ENTRY_POINT

ADDITIONAL_MAKO_FILES += $(shell find print $(FIND_OPTS) -name "*.mako" -print) \
	$(shell find apache $(FIND_OPTS) -name "*.mako" -print) \
	$(shell find deploy $(FIND_OPTS) -name "*.mako" -print) \
	geoportal/development.ini.mako geoportal/production.ini.mako


CONF_FILES += apache/application.wsgi
CONF_FILES_MAKO = $(shell ls -1 apache/*.conf.mako 2> /dev/null)
CONF_FILES_JINJA = $(shell ls -1 apache/*.conf.jinja 2> /dev/null)
CONF_FILES += $(shell ls -1 apache/*.conf 2> /dev/null) $(CONF_FILES_MAKO:.mako=) $(CONF_FILES_JINJA:.jinja=)

DEFAULT_BUILD_RULES ?= geoportal-docker \
	config-docker \
	project.yaml \
	alembic.ini \
	alembic.yaml

TILECLOUD_CHAIN ?= TRUE
ifeq ($(TILECLOUD_CHAIN), TRUE)
MAPCACHE_FILE = apache/mapcache.xml
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

/build/config-docker.timestamp:
	$(PRERULE_CMD)
	@echo "Nothing to do for $@"
	touch $@

node_modules/%: /usr/lib/node_modules/%
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	rm -rf $@
	cp -r $< $@

/build/geoportal-docker.timestamp: \
		node_modules/ngeo/src \
		node_modules/ngeo/contribs/gmf/src \
		node_modules/openlayers/src \
		node_modules/jquery/dist/jquery.min.js \
		node_modules/angular/angular.min.js \
		node_modules/angular-animate/angular-animate.min.js \
		node_modules/angular-float-thead/angular-floatThead.js \
		node_modules/angular-gettext/dist/angular-gettext.min.js \
		node_modules/angular-sanitize/angular-sanitize.min.js \
		node_modules/angular-touch/angular-touch.min.js \
		node_modules/angular-dynamic-locale/dist/tmhDynamicLocale.min.js \
		node_modules/angular-ui-date/dist/date.js \
		node_modules/angular-ui-slider/src/slider.js \
		node_modules/bootstrap/dist/js/bootstrap.min.js \
		node_modules/floatthead/dist/jquery.floatThead.min.js \
		node_modules/proj4/dist/proj4.js \
		node_modules/d3/build/d3.min.js \
		node_modules/file-saver/FileSaver.min.js \
		node_modules/corejs-typeahead/dist/typeahead.bundle.min.js \
		node_modules/jsts/dist/jsts.min.js \
		node_modules/moment/min/moment.min.js \
		node_modules/ngeo/third-party/jquery-ui/jquery-ui.min.js \
		$(CONF_FILES)
	$(PRERULE_CMD)
	@echo "Nothing to do for $@"
	touch $@

/build/testdb-docker.timestamp:
	$(PRERULE_CMD)
	@echo "Nothing to do for $@"
	touch $@
