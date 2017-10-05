# This file override and improve some rules for CONST_Makefile for non Docker production environment

DEPLOY ?= TRUE
ENVIRONEMENT ?= INSTANCE_ID
CONFIG_VARS += instanceid
MODWSGI_USER ?= www-data
export MODWSGI_USER

ADDITIONAL_MAKO_FILES += $(shell find apache $(FIND_OPTS) -name "*.mako" -print) \
	$(shell find deploy $(FIND_OPTS) -name "*.mako" -print)
POST_RULES += $(ADDITIONAL_MAKO_FILES)
ifeq (${DEPOY}, TRUE)
POST_RULES += deploy/deploy.cfg
endif

CONF_FILES += apache/application.wsgi
CONF_FILES_MAKO = $(shell ls -1 apache/*.conf.mako 2> /dev/null)
CONF_FILES_JINJA = $(shell ls -1 apache/*.conf.jinja 2> /dev/null)
CONF_FILES += $(shell ls -1 apache/*.conf 2> /dev/null) $(CONF_FILES_MAKO:.mako=) $(CONF_FILES_JINJA:.jinja=)

TILECLOUD_CHAIN ?= TRUE
ifeq ($(TILECLOUD_CHAIN), TRUE)
CONF_FILES += apache/tiles.conf apache/mapcache.xml
DEFAULT_BUILD_RULES += apache/tiles.conf
endif

UPGRADE_ARGS += --nondocker --makefile=$(firstword $(MAKEFILE_LIST))

include CONST_Makefile

# Tile cloud chain
apache/mapcache.xml: tilegeneration/config.yaml
	$(PRERULE_CMD)
	generate_controller --generate-mapcache-config

apache/tiles.conf: tilegeneration/config.yaml apache/mapcache.xml
	$(PRERULE_CMD)
	generate_controller --generate-apache-config

/build/print-docker.timestamp:
	$(PRERULE_CMD)
	@echo "Nothing to do for $@"
	touch $@

/build/mapserver-docker.timestamp:
	$(PRERULE_CMD)
	@echo "Nothing to do fo $@"
	touch $@

node_modules/%: /usr/lib/node_modules/%
	$(PRERULE_CMD)
	mkdir -p $(dir $@)
	rm -rf $@
	cp -r $< $@

/build/wsgi-docker.timestamp: \
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
