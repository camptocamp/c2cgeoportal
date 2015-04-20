PYTHON_VERSION = $(shell .build/venv/bin/python -c "import sys; print('%i.%i' % (sys.version_info.major, sys.version_info.minor))" 2> /dev/null)
PACKAGE = {{package}}

# Don't minify the js / css, ...
DEVELOPMENT ?= FALSE
# Language provided by the application
LANGUAGES ?= en fr de
# Enable CGXP build
CGXP ?= TRUE
# Enable sencha touch build
MOBILE ?= TRUE
# Enable ngeo build
NGEO ?= FALSE
# Use TileCloud chain
TILECLOUD_CHAIN ?= TRUE
# Used print version
PRINT_VERSION ?= 3

PIP_CMD ?= .build/venv/bin/pip
PIP_INSTALL_ARGS += install --trusted-host pypi.camptocamp.net

ifeq ($(CGXP), TRUE)
DEFAULT_WEB_RULE += build-cgxp
endif
ifeq ($(MOBILE), TRUE)
DEFAULT_WEB_RULE += sencha-touch
endif
ifeq ($(NGEO), TRUE)
DEFAULT_WEB_RULE += build-ngeo
CLIENT_CHECK_RULE ?= lint-ngeo
endif
WEB_RULE ?= $(DEFAULT_WEB_RULE)

# Make rules

DEFAULT_BUILD_RULES ?= test-packages .build/requirements.timestamp $(WEB_RULE) build-server apache
ifeq ($(TILECLOUD_CHAIN), TRUE)
DEFAULT_BUILD_RULES += test-packages-tilecloud-chain
endif
ifeq ($(MOBLE), TRUE)
DEFAULT_BUILD_RULES += test-packages-mobile
endif
ifeq ($(NGEO), TRUE)
DEFAULT_BUILD_RULES += test-packages-ngeo
endif
ifeq ($(PRINT_VERSION), 2)
DEFAULT_BUILD_RULES += print
endif
ifeq ($(PRINT_VERSION), 3)
DEFAULT_BUILD_RULES += print
endif
BUILD_RULES ?= $(PRE_RULES) $(filter-out $(DISABLE_BUILD_RULES),$(DEFAULT_BUILD_RULES)) $(POST_RULES)

# Requirements

EGGS_DEPENDENCIES += .build/venv.timestamp-noclean setup.py CONST_versions.txt CONST_requirements.txt
REQUIREMENTS += -r CONST_requirements.txt
DEV_REQUIREMENTS += -r CONST_dev-requirements.txt
ifeq ($(TILECLOUD_CHAIN), TRUE)
DEV_REQUIREMENTS += 'tilecloud-chain>=1.0.0dev'
endif
ifeq ($(CGXP), TRUE)
DEV_REQUIREMENTS += JSTools 'c2c.cssmin>=0.7dev6'
endif
ifeq ($(NGEO), TRUE)
DEV_REQUIREMENTS += http://closure-linter.googlecode.com/files/closure_linter-latest.tar.gz
endif

OUTPUT_DIR = $(PACKAGE)/static/build

# Git

GIT_REMOTE ?= origin
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)

# ngeo
OL_JS_FILES = $(shell find node_modules/openlayers/src/ol -type f -name '*.js' 2> /dev/null)
NGEO_JS_FILES = $(shell find node_modules/ngeo/src -type f -name '*.js' 2> /dev/null)
APP_JS_FILES = $(shell find $(PACKAGE)/static/js -type f -name '*.js')
APP_HTML_FILES = $(shell find $(PACKAGE)/templates -type f -name '*.html')
APP_PARTIALS_FILES := $(shell find $(PACKAGE)/static/js -type f -name '*.html')
LESS_FILES = $(shell find $(PACKAGE)/static/less -type f -name '*.less' 2> /dev/null)
JSON_CLIENT_LOCALISATION_FILES = $(addprefix $(OUTPUT_DIR)/locale/, $(addsuffix /$(PACKAGE).json, $(LANGUAGES)))

# CGXP
JSBUILD_MAIN_FILES = $(shell find $(PACKAGE)/static/lib/cgxp $(PACKAGE)/static/js -name "*.js" -print 2> /dev/null)
JSBUILD_MAIN_CONFIG = jsbuild/app.cfg
JSBUILD_MAIN_OUTPUT_FILES ?= app.js edit.js routing.js api.js xapi.js
JSBUILD_MAIN_OUTPUT_FILES += $(addprefix lang-, $(addsuffix .js, $(LANGUAGES)))
JSBUILD_MAIN_OUTPUT_FILES += $(addprefix api-lang-, $(addsuffix .js, $(LANGUAGES)))
JSBUILD_MAIN_OUTPUT_FILES := $(addprefix $(OUTPUT_DIR)/, $(JSBUILD_MAIN_OUTPUT_FILES))
JSBUILD_ARGS = $(if ifeq($(DEVELOPMENT), ‘TRUE’),-u,)

ifeq ($(DEVELOPMENT), FALSE)
	CSSMIN_ARGS += --compress
endif
CSS_BASE_FILES += \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/ext-all.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/xtheme-gray.css \
	$(PACKAGE)/static/lib/cgxp/openlayers/theme/default/style.css \
	$(PACKAGE)/static/lib/cgxp/geoext/resources/css/popup.css \
	$(PACKAGE)/static/lib/cgxp/geoext/resources/css/gxtheme-gray.css \
	$(PACKAGE)/static/lib/cgxp/geoext.ux/ux/Measure/resources/css/measure.css \
	$(PACKAGE)/static/lib/cgxp/sandbox/FeatureEditing/resources/css/feature-editing.css \
	$(PACKAGE)/static/lib/cgxp/styler/theme/css/styler.css \
	$(PACKAGE)/static/lib/cgxp/gxp/src/theme/all.css \
	$(PACKAGE)/static/lib/cgxp/core/src/theme/all.css \
	$(PACKAGE)/static/lib/cgxp/ext.ux/ColorPicker/ressources/colorpicker.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/examples/ux/css/Spinner.css \
	$(PACKAGE)/static/css/proj.css \
	$(PACKAGE)/static/css/proj-map.css \
	$(PACKAGE)/static/css/proj-widgets.css
CSS_BASE_OUTPUT = $(OUTPUT_DIR)/app.css

CSS_API_FILES += \
	$(PACKAGE)/static/lib/cgxp/openlayers/theme/default/style.css \
	$(PACKAGE)/static/css/proj-map.css
CSS_API_OUTPUT = $(OUTPUT_DIR)/api.css

CSS_XAPI_FILES += \
	$(PACKAGE)/static/lib/cgxp/core/src/theme/reset.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/editor.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/pivotgrid.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/menu.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/panel.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/grid.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/debug.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/qtips.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/dd.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/form.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/resizable.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/toolbar.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/slider.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/combo.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/layout.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/dialog.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/core.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/button.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/progress.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/tabs.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/box.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/borders.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/date-picker.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/tree.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/window.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/visual/list-view.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/editor.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/pivotgrid.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/menu.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/panel.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/grid.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/debug.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/qtips.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/dd.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/form.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/resizable.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/toolbar.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/panel-reset.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/slider.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/combo.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/layout.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/dialog.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/core.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/button.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/progress.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/tabs.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/box.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/borders.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/date-picker.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/tree.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/window.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/structure/list-view.css \
	$(PACKAGE)/static/lib/cgxp/ext/Ext/resources/css/xtheme-gray.css \
	$(PACKAGE)/static/lib/cgxp/openlayers/theme/default/style.css \
	$(PACKAGE)/static/lib/cgxp/geoext/resources/css/gxtheme-gray.css \
	$(PACKAGE)/static/lib/cgxp/geoext.ux/ux/Measure/resources/css/measure.css \
	$(PACKAGE)/static/lib/cgxp/gxp/src/theme/all.css \
	$(PACKAGE)/static/lib/cgxp/core/src/theme/all.css \
	$(PACKAGE)/static/css/proj-map.css \
	$(PACKAGE)/static/css/proj-widgets.css
CSS_XAPI_OUTPUT = $(OUTPUT_DIR)/xapi.css

VALIDATE_PY_FOLDERS = $(PACKAGE)/*.py $(PACKAGE)/lib $(PACKAGE)/scripts $(PACKAGE)/views
VALIDATE_PY_TEST_FOLDERS = $(PACKAGE)/tests

# Sencha touch

SENCHA_CMD ?= sencha-cmd

JSBUILD_MOBILE_CONFIG = jsbuild/mobile.cfg
JSBUILD_MOBILE_OUTPUT_DIR = $(PACKAGE)/static/mobile/
JSBUILD_MOBILE_OUTPUT_FILES = $(addprefix $(JSBUILD_MOBILE_OUTPUT_DIR), openlayers-mobile.js)
MOBILE_APP_JS_FILES = $(PACKAGE)/static/mobile/config.js $(PACKAGE)/static/mobile/app.js $(shell find $(PACKAGE)/static/mobile/app -type f -name '*.js')

# Documentation
SPHINX_FILES = $(shell find doc -name "*.rst" -print)

# Server localisation
SERVER_LOCALISATION_SOURCES_FILES += $(PACKAGE)/models.py $(shell find $(PACKAGE)/templates -type f -name '*.html')
SERVER_LOCALISATION_FILES = $(addprefix $(PACKAGE)/locale/, $(addsuffix /LC_MESSAGES/$(PACKAGE)-server.mo, $(LANGUAGES)))

# Print
PRINT_BASE_DIR ?= print
PRINT_WAR ?= print-$(INSTANCE_ID).war
PRINT_OUTPUT ?= /srv/tomcat/tomcat1/webapps
ifeq ($(PRINT_VERSION), 3)
PRINT_BASE_WAR ?= print-servlet.war
PRINT_INPUT += print-apps WEB-INF
PRINT_REQUIREMENT += \
	$(PRINT_BASE_DIR)/WEB-INF/lib/jasperreports-functions-5.5.0.jar \
	$(PRINT_BASE_DIR)/WEB-INF/lib/joda-time-1.6.jar \
	$(PRINT_BASE_DIR)/WEB-INF/lib/jasperreports-fonts-5.5.0.jar \
	$(PRINT_BASE_DIR)/WEB-INF/lib/postgresql-9.3-1102.jdbc41.jar \
	$(PRINT_BASE_DIR)/WEB-INF/classes/logback.xml \
	$(PRINT_BASE_DIR)/WEB-INF/classes/mapfish-spring-application-context-override.xml
TOMCAT_SERVICE_COMMAND ?= sudo /etc/init.d/tomcat-tomcat1

PRINT_REQUIREMENT += $(shell find $(PRINT_BASE_DIR)/print-apps 2> /dev/null)
endif
ifeq ($(PRINT_VERSION), 2)
PRINT_BASE_WAR ?= print-servlet-2.1-SNAPSHOT-IMG-MAGICK.war
PRINT_INPUT_LS ?= config.yaml WEB-INF/classes/log4j.properties
PRINT_INPUT_FIND ?= *.tif *.bmp *.jpg *.jpeg *.gif *.png *.pdf
PRINT_INPUT += $(shell cd $(PRINT_BASE_DIR) && ls -1 $(PRINT_INPUT_LS) 2> /dev/null)
PRINT_INPUT += $(foreach INPUT, $(PRINT_INPUT_FIND), $(shell cd $(PRINT_BASE_DIR) && find -name '$(INPUT)' -type f))
PRINT_REQUIREMENT += $(addprefix, $(PRINT_BASE_DIR)/, $(PRINT_INPUT))
endif
PRINT_REQUIREMENT += $(PRINT_BASE_DIR)/$(PRINT_BASE_WAR)

# Apache
APACHE_ENTRY_POINT ?= /$(INSTANCE_ID)/
APACHE_VHOST ?= $(PACKAGE)
APACHE_CONF_DIR ?= /var/www/vhosts/$(APACHE_VHOST)/conf
CONF_FILES_IN = $(shell ls -1 apache/*.conf.in 2> /dev/null)
CONF_FILES_MAKO = $(shell ls -1 apache/*.conf.mako 2> /dev/null)
CONF_FILES_JINJA = $(shell ls -1 apache/*.conf.jinja 2> /dev/null)
CONF_FILES = $(shell ls -1 apache/*.conf) $(CONF_FILES_IN:.in=) $(CONF_FILES_MAKO:.mako=) $(CONF_FILES_JINJA:.jinja=)
PY_FILES = $(shell find $(PACKAGE) -type f -name '*.py' -print)
TEMPLATES_FILES = $(shell find $(PACKAGE)/templates -type f -print)

# Templates
TEMPLATE_EXCLUDE += .build print/templates \
	CONST_alembic/main/script.py.mako CONST_alembic/static/script.py.mako
FIND_OPTS = $(foreach ELEM, $(TEMPLATE_EXCLUDE),-path ./$(ELEM) -prune -o) -type f
TEMPLATE_FILES = $(shell find $(FIND_OPTS) -name "*.in" -print)
MAKO_FILES = $(shell find $(FIND_OPTS) -name "*.mako" -print)
JINJA_FILES = $(shell find $(FIND_OPTS) -name "*.jinja" -print)
VARS_FILES += CONST_vars.yaml $(VARS_FILE)
VARS_DEPENDS += $(VARS_FILES) .build/node_modules.timestamp
CONFIG_VARS += sqlalchemy.url schema parentschema enable_admin_interface pyramid_closure \
	node_modules_path closure_library_path default_locale_name servers layers \
	available_locale_names cache admin_interface functionalities external_themes_url \
	raster shortener hide_capabilities use_security_metadata mapserverproxy \
	print_url tiles_url checker check_collector default_max_age jsbuild package srid
ENVIRONMENT_VARS += INSTANCE_ID=${INSTANCE_ID} \
	APACHE_ENTRY_POINT=$(APACHE_ENTRY_POINT) \
	DEVELOPMENT=${DEVELOPMENT} \
	PACKAGE=${PACKAGE}
C2C_TEMPLATE_CMD = $(ENVIRONMENT_VARS) .build/venv/bin/c2c-template --vars $(VARS_FILE)
MAKE_FILES = $(shell ls -1 *.mk) CONST_Makefile


.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Main targets:"
	@echo
	@echo "- build			Build and configure the project"
	@echo "- checks			Perform a number of checks on the code"
	@echo "- serve			Run the development server (Pserve)"
	@echo "- clean			Remove generated files"
	@echo "- cleanall		Remove all the build artefacts"
	@echo
	@echo "Utility targets:"
	@echo
	@echo "- update			Update the project (Git, Node, Pip)"
	@echo "- update-git-submodules	Update the Git submodules"
	@echo "- update-node-modules	Update node modules (using --force)"
ifdef UTILITY_HELP
	@echo $(UTILITY_HELP)
endif
	@echo
	@echo "Secondary targets:"
	@echo
	@echo "- build-cgxp		Build the javascript and the css for cgxp"
	@echo "- build-ngeo		Build the javascript and the css for ngeo"
	@echo "- build-server		Build the files required by the server"
	@echo "- compile-js-catalog	Compile the Angular translation catalog"
	@echo "- compile-py-catalog	Compile the Python translation catalog"
	@echo "- flake8			Run Flake8 checker on the Python code"
	@echo "- lint-ngeo		Check the JavaScript code with linters for ngeo"
	@echo "- template-clean	 	Clean the template file"
	@echo "- template-generate	Generate the template file"
ifdef SECONDARY_HELP
	@echo $(SECONDARY_HELP)
endif
	@echo

.PHONY: build
build: $(BUILD_RULES)

.PHONY: checks
checks: flake8 $(CLIENT_CHECK_RULE) $(WEB_RULE)

.PHONY: clean
clean: template-clean
	rm -f .build/*.timestamp
	rm -rf $(OUTPUT_DIR)/
	rm -f $(JSBUILD_MOBILE_OUTPUT_FILES)
	rm -rf $(PACKAGE)/static/mobile/build
	rm -rf $(PACKAGE)/static/mobile/archive

.PHONY: cleanall
cleanall: clean
	rm -rf .build
	rm -rf node_modules
	rm -f $(PRINT_OUTPUT)/$(PRINT_WAR)
	rm -rf $(PRINT_OUTPUT)/$(PRINT_WAR:.war=)
	rm -f $(APACHE_CONF_DIR)/$(INSTANCE_ID).conf

.PHONY: flake8
flake8: .build/venv/bin/flake8
	.build/venv/bin/flake8 $(PACKAGE)

.PHONY: build-server
build-server: template-generate compile-py-catalog $(SERVER_LOCALISATION_FILES)

.PHONY: build-cgxp
build-cgxp: $(JSBUILD_MAIN_OUTPUT_FILES) $(CSS_BASE_OUTPUT) $(CSS_API_OUTPUT) $(CSS_XAPI_OUTPUT)

.PHONY: lint-ngeo
lint-ngeo: .build/venv/bin/gjslint .build/node_modules.timestamp .build/gjslint.timestamp .build/jshint.timestamp

.PHONY: serve
serve: build development.ini
	.build/venv/bin/pserve --reload --monitor-restart development.ini

.PHONY: update-node-modules
update-node-modules:
	npm install --force
	touch .build/node_modules.timestamp

# Templates

.PHONY: template-clean
template-clean:
	rm -f $(TEMPLATE_FILES:.in=)
	rm -f $(MAKO_FILES:.mako=)
	rm -f $(JINJA_FILES:.jinja=)
	rm -f .build/config-*.timestamp
	rm -f .build/config.yaml

.PHONY: template-generate
template-generate: $(TEMPLATE_FILES:.in=) $(MAKO_FILES:.mako=) $(JINJA_FILES:.jinja=) .build/config-$(INSTANCE_ID).timestamp

$(TEMPLATE_FILES:.in=) $(MAKO_FILES:.mako=) $(JINJA_FILES:.jinja=): .build/venv/bin/c2c-template $(VARS_DEPENDS)

%: %.in
ifeq ($(origin VARS_FILE), undefined)
	@echo "Error: the variable VARS_FILE is required."
	exit 1
endif
	$(C2C_TEMPLATE_CMD) --engine template --files $<

%: %.mako
ifeq ($(origin VARS_FILE), undefined)
	@echo "Error: the variable VARS_FILE is required."
	exit 1
endif
	$(C2C_TEMPLATE_CMD) --engine mako --files $<

%: %.jinja
ifeq ($(origin VARS_FILE), undefined)
	@echo "Error: the variable VARS_FILE is required."
	exit 1
endif
	$(C2C_TEMPLATE_CMD) --engine jinja --files $<

.build/venv/bin/c2c-template: .build/dev-requirements.timestamp

.build/config-$(INSTANCE_ID).timestamp: .build/venv/bin/c2c-template $(VARS_DEPENDS) $(MAKE_FILES)
	rm -f .build/config-*.timestamp | true
	$(C2C_TEMPLATE_CMD) --get-config .build/config.yaml $(CONFIG_VARS)
	touch $@

# server localisation

.build/venv/bin/pot-create: .build/requirements.timestamp

.PHONY: compile-py-catalog
compile-py-catalog: $(SERVER_LOCALISATION_FILES)

# to don't delete them
.SECONDARY: $(SERVER_LOCALISATION_FILES:.mo=.po)

$(PACKAGE)/locale/$(PACKAGE)-server.pot: $(SERVER_LOCALISATION_SOURCES_FILES) .build/venv/bin/pot-create lingua.cfg
	.build/venv/bin/pot-create -c lingua.cfg -o $@ $(SERVER_LOCALISATION_SOURCES_FILES)
	# removes the allways changed date line
	sed -i '/^"POT-Creation-Date: /d' $@
	sed -i '/^"PO-Revision-Date: /d' $@

$(PACKAGE)/locale/%/LC_MESSAGES/$(PACKAGE)-server.po: $(PACKAGE)/locale/$(PACKAGE)-server.pot .build/dev-requirements.timestamp
	mkdir -p $(dir $@)
	touch $@
	msgmerge --update $@ $<

%.mo: %.po
	msgfmt -o $@ $<
	touch -c $@

# ngeo

.PHONY: build-ngeo
build-ngeo: \
	$(OUTPUT_DIR)/build.js \
	$(OUTPUT_DIR)/build.css \
	$(OUTPUT_DIR)/build.min.css \
	compile-js-catalog

.PHONY: compile-js-catalog
compile-js-catalog: $(JSON_CLIENT_LOCALISATION_FILES)

.build/venv/bin/db2pot: .build/requirements.timestamp

$(PACKAGE)/closure/%.py: $(CLOSURE_LIBRARY_PATH)/closure/bin/build/%.py
	cp $< $@

$(PACKAGE)/locale/$(PACKAGE)-js.pot: $(APP_HTML_FILES) .build/node_modules.timestamp
	node tasks/extract-messages.js $(APP_HTML_FILES) > $@

$(PACKAGE)/locale/$(PACKAGE)-db.pot: .build/venv/bin/db2pot development.ini .build/config-$(INSTANCE_ID).timestamp
	mkdir -p $(dir $@)
	.build/venv/bin/db2pot
	msguniq $@ -o $@

$(PACKAGE)/locale/$(PACKAGE)-client.pot: $(PACKAGE)/locale/$(PACKAGE)-js.pot $(PACKAGE)/locale/$(PACKAGE)-db.pot
	msgcat $^ > $@

$(JSON_CLIENT_LOCALISATION_FILES): .build/node_modules.timestamp

$(OUTPUT_DIR)/locale/%/$(PACKAGE).json: $(PACKAGE)/locale/%/LC_MESSAGES/$(PACKAGE)-client.po .build/node_modules.timestamp
	mkdir -p $(dir $@)
	node tasks/compile-catalog $< > $@

$(PACKAGE)/locale/%/LC_MESSAGES/%/$(PACKAGE)-client.po: $(PACKAGE)/locale/$(PACKAGE)-client.pot
	mkdir -p $(dir $@)
	touch $@
	msgmerge --update $@ $<

$(OUTPUT_DIR)/build.js: .build/node_modules.timestamp .build/build.js
	mkdir -p $(dir $@)
	awk 'FNR==1{print ""}1' $(addprefix node_modules/, \
		jquery/dist/jquery.min.js \
		angular/angular.min.js \
		angular-gettext/dist/angular-gettext.min.js \
		angular-animate/angular-animate.min.js \
		bootstrap/dist/js/bootstrap.min.js \
		proj4/dist/proj4.js \
		d3/d3.min.js \
		) .build/build.js > $@
	sed -i '/^\/\/# sourceMappingURL=.*\.map$$/d' $@

$(OUTPUT_DIR)/build.min.css: $(LESS_FILES) .build/node_modules.timestamp
	mkdir -p $(dir $@)
	./node_modules/.bin/lessc --clean-css $(PACKAGE)/static/less/$(PACKAGE).less $@

$(OUTPUT_DIR)/build.css: $(LESS_FILES) .build/node_modules.timestamp
	mkdir -p $(dir $@)
	./node_modules/.bin/lessc $(PACKAGE)/static/less/$(PACKAGE).less $@

.build/build.js: build.json $(OL_JS_FILES) $(NGEO_JS_FILES) $(APP_JS_FILES) \
		.build/templatecache.js \
		.build/externs/angular-1.3.js \
		.build/externs/angular-1.3-q.js \
		.build/externs/angular-1.3-http-promise.js \
		.build/externs/jquery-1.9.js \
		.build/node_modules.timestamp
	node tasks/build.js $< $@

.build/templatecache.js: templatecache.mako.js
	.build/venv/bin/mako-render --var "partials=$(APP_PARTIALS_FILES)" $< > $@

.build/externs/angular-1.3.js:
	mkdir -p $(dir $@)
	wget -O $@ https://raw.githubusercontent.com/google/closure-compiler/master/contrib/externs/angular-1.3.js
	touch $@

.build/externs/angular-1.3-q.js:
	mkdir -p $(dir $@)
	wget -O $@ https://raw.githubusercontent.com/google/closure-compiler/master/contrib/externs/angular-1.3-q.js
	touch $@

.build/externs/angular-1.3-http-promise.js:
	mkdir -p $(dir $@)
	wget -O $@ https://raw.githubusercontent.com/google/closure-compiler/master/contrib/externs/angular-1.3-http-promise.js
	touch $@

.build/externs/jquery-1.9.js:
	mkdir -p $(dir $@)
	wget -O $@ https://raw.githubusercontent.com/google/closure-compiler/master/contrib/externs/jquery-1.9.js
	touch $@

package.json:
ifeq ($(NGEO), TRUE)
	@echo Missing $@ required file by ngeo
	exit 1
else
	touch $@
endif

.build/node_modules.timestamp: package.json
	mkdir -p $(dir $@)
ifeq ($(NGEO), TRUE)
	npm install
endif
	touch $@

.build/gjslint.timestamp: $(APP_JS_FILES)
	mkdir -p $(dir $@)
	.build/venv/bin/gjslint --jslint_error=all --strict --custom_jsdoc_tags=event,fires,function,classdesc,api,observable $?
	touch $@

.build/jshint.timestamp: $(APP_JS_FILES)
	mkdir -p $(dir $@)
	./node_modules/.bin/jshint --verbose $?
	touch $@


# Git

.build/venv/bin/jsbuild: .build/dev-requirements.timestamp

.PHONY: update
update:
	git pull --rebase $(GIT_REMOTE) $(GIT_BRANCH)
	git submodule sync
	git submodule update
	git submodule foreach git submodule sync
	git submodule foreach git submodule update --init
ifeq ($(NGEO), TRUE)
	npm install --force
endif

.PHONY: update-git-submodules
update-git-submodules:
	git submodule sync
	git submodule update
	git submodule foreach git submodule sync
	git submodule foreach git submodule update --init

.git/modules/$(PACKAGE)/static/lib/cgxp/modules/%/HEAD: .git/modules/$(PACKAGE)/static/lib/cgxp/HEAD
	if [ -e $@ ]; then touch $@; else git submodule foreach git submodule update --init; fi

.git/modules/$(PACKAGE)/static/lib/cgxp/HEAD:
	git submodule update --init


# CGXP build

.build/venv/bin/cssmin: .build/dev-requirements.timestamp

.build/venv/bin/jsbuild: .build/dev-requirements.timestamp

$(JSBUILD_MAIN_OUTPUT_FILES): $(JSBUILD_MAIN_FILES) $(JSBUILD_MAIN_CONFIG) \
	.build/venv/bin/jsbuild \
	.git/modules/$(PACKAGE)/static/lib/cgxp/modules/openlayers/HEAD \
	.git/modules/$(PACKAGE)/static/lib/cgxp/HEAD
	mkdir -p $(dir $@)
	.build/venv/bin/jsbuild $(JSBUILD_MAIN_CONFIG) $(JSBUILD_ARGS) -j $(notdir $@) -o $(OUTPUT_DIR)

$(CSS_BASE_OUTPUT): .build/venv/bin/cssmin \
	.git/modules/$(PACKAGE)/static/lib/cgxp/modules/openlayers/HEAD \
	.git/modules/$(PACKAGE)/static/lib/cgxp/HEAD \
	$(CSS_BASE_FILES)
	.build/venv/bin/c2c-cssmin $(CSSMIN_ARGS) $@ $(CSS_BASE_FILES)

$(CSS_API_OUTPUT): .build/venv/bin/cssmin \
	.git/modules/$(PACKAGE)/static/lib/cgxp/modules/openlayers/HEAD \
	.git/modules/$(PACKAGE)/static/lib/cgxp/HEAD \
	$(CSS_API_FILES)
	.build/venv/bin/c2c-cssmin $(CSSMIN_ARGS) $@ $(CSS_API_FILES)

$(CSS_XAPI_OUTPUT): .build/venv/bin/cssmin \
	.git/modules/$(PACKAGE)/static/lib/cgxp/modules/openlayers/HEAD \
	.git/modules/$(PACKAGE)/static/lib/cgxp/HEAD \
	$(CSS_XAPI_FILES)
	.build/venv/bin/c2c-cssmin $(CSSMIN_ARGS) $@ $(CSS_XAPI_FILES)

# Sencha touch

.PHONY: sencha-touch
sencha-touch: $(PACKAGE)/static/mobile/build/production/App/app.js

$(JSBUILD_MOBILE_OUTPUT_FILES): $(JSBUILD_MOBILE_CONFIG) .build/venv/bin/jsbuild
	.build/venv/bin/jsbuild $(JSBUILD_MOBILE_CONFIG) $(JSBUILD_ARGS) -j $(notdir $@) -o $(JSBUILD_MOBILE_OUTPUT_DIR)

$(PACKAGE)/static/mobile/build/production/App/app.js: $(JSBUILD_MOBILE_OUTPUT_FILES) \
	$(PACKAGE)/static/mobile/custom.scss $(MOBILE_APP_JS_FILES)
	rm -rf $(PACKAGE)/static/mobile/build
	rm -rf $(PACKAGE)/static/mobile/archive
	cd $(PACKAGE)/static/mobile && $(SENCHA_CMD) app build production

# Check packages

.build/venv/bin/c2c-versions: .build/dev-requirements.timestamp

.PHONY: test-packages
test-packages: .build/test-packages.timestamp

.build/test-packages.timestamp: .build/venv/bin/c2c-versions CONST_packages.yaml
	.build/venv/bin/c2c-versions CONST_packages.yaml main
	touch $@

.PHONY: test-packages-mobile
test-packages-mobile: .build/test-packages-mobile.timestamp

.build/test-packages-mobile.timestamp: .build/venv/bin/c2c-versions CONST_packages.yaml
	.build/venv/bin/c2c-versions CONST_packages.yaml mobile
	touch $@

.PHONY: test-packages-tilecloud-chain
test-packages-tilecloud-chain: .build/test-packages-tilecloud-chain.timestamp

.build/test-packages-tilecloud-chain.timestamp: .build/venv/bin/c2c-versions CONST_packages.yaml
	.build/venv/bin/c2c-versions CONST_packages.yaml tilecloud-chain
	touch $@

.PHONY: test-packages-ngeo
test-packages-ngeo: .build/test-packages-ngeo.timestamp

.build/test-packages-ngeo.timestamp: .build/venv/bin/c2c-versions CONST_packages.yaml
	.build/venv/bin/c2c-versions CONST_packages.yaml ngeo
	touch $@

# Check

.build/venv/bin/gjslint: .build/dev-requirements.timestamp

.build/venv/bin/flake8: .build/dev-requirements.timestamp

# Venv

.build/dev-requirements.timestamp: .build/venv.timestamp-noclean CONST_dev-requirements.txt
	$(PIP_CMD) $(PIP_INSTALL_ARGS) $(DEV_REQUIREMENTS) $(PIP_REDIRECT)
	touch $@

.build/venv.timestamp-noclean:
	mkdir -p $(dir $@)
	virtualenv --setuptools --no-site-packages .build/venv
	$(PIP_CMD) install \
		--index-url http://pypi.camptocamp.net/pypi \
		'pip>=6' 'setuptools>=12'
	touch $@

.build/requirements.timestamp: $(EGGS_DEPENDENCIES)
	$(PIP_CMD) $(PIP_INSTALL_ARGS) $(REQUIREMENTS) $(PIP_REDIRECT)
	touch $@

# Print

.PHONY: print
print: $(PRINT_OUTPUT)/$(PRINT_WAR)

$(PRINT_OUTPUT)/$(PRINT_WAR): $(PRINT_REQUIREMENT)
	cp $(PRINT_BASE_DIR)/$(PRINT_BASE_WAR) /tmp/$(PRINT_WAR)
	cd $(PRINT_BASE_DIR) && jar -uf /tmp/$(PRINT_WAR) $(PRINT_INPUT)
	chmod g+r,o+r /tmp/$(PRINT_WAR)
ifneq ($(TOMCAT_SERVICE_COMMAND),)
	$(TOMCAT_SERVICE_COMMAND) stop
endif
	rm -rf $(PRINT_OUTPUT)/$(PRINT_WAR:.war=)
	mv /tmp/$(PRINT_WAR) $(PRINT_OUTPUT)
ifneq ($(TOMCAT_SERVICE_COMMAND),)
	$(TOMCAT_SERVICE_COMMAND) start
endif

print/WEB-INF/lib/jasperreports-functions-5.5.0.jar:
	mkdir -p $(dir $@)
	wget http://sourceforge.net/projects/jasperreports/files/jasperreports/JasperReports%205.5.0/jasperreports-functions-5.5.0.jar/download -O $@
	touch $@

print/WEB-INF/lib/joda-time-1.6.jar:
	mkdir -p $(dir $@)
	wget http://mirrors.ibiblio.org/pub/mirrors/maven2/joda-time/joda-time/1.6/joda-time-1.6.jar -O $@
	touch $@

print/WEB-INF/lib/jasperreports-fonts-5.5.0.jar:
	mkdir -p $(dir $@)
	wget http://sourceforge.net/projects/jasperreports/files/jasperreports/JasperReports%205.5.0/jasperreports-fonts-5.5.0.jar/download -O $@
	touch $@

print/WEB-INF/lib/postgresql-9.3-1102.jdbc41.jar:
	mkdir -p $(dir $@)
	wget http://jdbc.postgresql.org/download/postgresql-9.3-1102.jdbc41.jar -O $@
	touch $@

# Apache config
.PHONY: apache
apache: .build/apache.timestamp

$(APACHE_CONF_DIR)/$(INSTANCE_ID).conf:
	echo "Include $(shell pwd)/apache/*.conf" > $@

.build/apache.timestamp: \
		.build/config-$(INSTANCE_ID).timestamp \
		$(CONF_FILES) \
		$(PY_FILES) \
		$(TEMPLATES_FILES) \
		$(APACHE_CONF_DIR)/$(INSTANCE_ID).conf \
		.build/requirements.timestamp
	sudo /usr/sbin/apache2ctl graceful
	touch $@
