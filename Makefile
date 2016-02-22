TEMPLATE_EXCLUDE = MANIFEST.in .build .eggs c2cgeoportal/scaffolds c2cgeoportal/tests/testegg c2cgeoportal/templates ngeo
FIND_OPTS = $(foreach ELEM, $(TEMPLATE_EXCLUDE),-path ./$(ELEM) -prune -o) -type f
MAKO_FILES = $(shell find $(FIND_OPTS) -name "*.mako" -print)
VARS_FILE ?= vars.yaml
VARS_FILES += vars.yaml

DEVELOPPEMENT ?= FALSE

PIP_CMD ?= .build/venv/bin/pip

ADMIN_OUTPUT_DIR = c2cgeoportal/static/build/admin/

JSBUILD_ADMIN_FILES = $(shell find c2cgeoportal/static/lib c2cgeoportal/static/adminapp -name "*.js" -print)
JSBUILD_ADMIN_CONFIG = jsbuild/app.cfg
JSBUILD_ADMIN_OUTPUT_FILES = $(addprefix $(ADMIN_OUTPUT_DIR),admin.js)
JSBUILD_ARGS = $(if ifeq($(DEVELOPPEMENT), ‘TRUE’),-u,)

CSS_ADMIN_FILES = c2cgeoportal/static/adminapp/css/admin.css c2cgeoportal/static/lib/openlayers/theme/default/style.css c2cgeoportal/static/lib/checkboxtree-r253/jquery.checkboxtree.css
CSS_ADMIN_OUTPUT = c2cgeoportal/static/build/admin/admin.css
ifeq ($(DEVELOPMENT), FALSE)
	CSSMIN_ARGS += --compress
endif

VALIDATE_PY_FOLDERS = setup.py c2cgeoportal/*.py c2cgeoportal/lib c2cgeoportal/scripts c2cgeoportal/views c2cgeoportal/scaffolds/update/CONST_alembic
VALIDATE_TEMPLATE_PY_FOLDERS = c2cgeoportal/scaffolds
VALIDATE_PY_TEST_FOLDERS = c2cgeoportal/tests

SPHINX_FILES = $(shell find doc -name "*.rst" -print)

TX_VERSION = $(shell python setup.py --version | awk -F . '{{print $$1"_"$$2}}')
TX_DEPENDENCIES = .build/venv/bin/tx $(HOME)/.transifexrc .tx/config
ifeq (,$(wildcard $(HOME)/.transifexrc))
TOUCHBACK_TXRC = touch --date "$(shell date --iso-8601=seconds)" $(HOME)/.transifexrc
else
TOUCHBACK_TXRC = touch --date "$(shell stat -c '%y' $(HOME)/.transifexrc)" $(HOME)/.transifexrc
endif
L10N_LANGUAGES = fr de
L10N_PO_FILES = $(addprefix c2cgeoportal/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal.po, $(L10N_LANGUAGES)))
LANGUAGES = en $(L10N_LANGUAGES)
PO_FILES = $(addprefix c2cgeoportal/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal.po, $(LANGUAGES)))
MO_FILES = $(addprefix .build/,$(addsuffix .mo.timestamp,$(basename $(PO_FILES))))
SRC_FILES = $(shell ls -1 c2cgeoportal/*.py) \
	$(shell find c2cgeoportal/lib -name "*.py" -print) \
	$(shell find c2cgeoportal/views -name "*.py" -print) \
	$(filter-out c2cgeoportal/scripts/theme2fts.py, $(shell find c2cgeoportal/scripts -name "*.py" -print))

APPS += mobile
APPS_PACAKGE_PATH = c2cgeoportal/scaffolds/create/+package+
APPS_HTML_FILES = $(addprefix $(APPS_PACAKGE_PATH)/templates/, $(addsuffix .html_tmpl, $(APPS)))
APPS_JS_FILES = $(addprefix $(APPS_PACAKGE_PATH)/static-ngeo/js/, $(addsuffix .js_tmpl, $(APPS)))

ENVIRONMENT_VARS += TX_VERSION=$(TX_VERSION)
C2C_TEMPLATE_CMD = $(ENVIRONMENT_VARS) .build/venv/bin/c2c-template --vars $(VARS_FILE)


.PHONY: help
help:
	@echo "Usage: $(MAKE) <target>"
	@echo
	@echo "Main targets:"
	@echo
	@echo  "- build 		Build and configure the project"
	@echo  "- buildall		Build, check and test the project"
	@echo  "- doc 			Build the project documentation"
	@echo  "- tests 		Perform a number of tests on the code"
	@echo  "- checks		Perform a number of checks on the code"
	@echo  "- clean 		Remove generated files"
	@echo  "- cleanall 		Remove all the build artefacts"
	@echo  "- transifex-send	Send the localisation to Transifex"

.PHONY: build
build: $(MAKO_FILES:.mako=) \
	c2c-egg \
	c2cgeoportal/version.py \
	$(JSBUILD_ADMIN_OUTPUT_FILES) \
	$(CSS_ADMIN_OUTPUT) \
	$(MO_FILES) \
	$(APPS_HTML_FILES) $(APPS_JS_FILES) \
	c2cgeoportal/scaffolds/update/+dot+tx/CONST_config_mako \
	c2cgeoportal/scaffolds/update/package.json_tmpl

.PHONY: buildall
buildall: build doc tests checks

.PHONY: doc
doc: .build/sphinx.timestamp

.PHONY: tests
tests: nose

.PHONY: checks
checks: flake8

.PHONY: clean
clean:
	rm -f .build/dev-requirements.timestamp
	rm -f .build/venv.timestamp
	rm -f c2cgeoportal/locale/*.pot
	rm -f c2cgeoportal/locale/en/LC_MESSAGES/c2cgeoportal.po
	rm -rf c2cgeoportal/static/build
	rm -f $(MAKO_FILES:.mako=)
	rm -rf ngeo
	rm -f $(APPS_HTML_FILES) $(APPS_JS_FILES)

.PHONY: cleanall
cleanall: clean
	rm -f $(PO_FILES)
	rm -rf .build

.PHONY: c2c-egg
c2c-egg: .build/requirements.timestamp

.build/sphinx.timestamp: .build/dev-requirements.timestamp $(SPHINX_FILES)
	mkdir -p doc/_build/html
	doc/build.sh
	touch $@

.PHONY: nose
nose: .build/dev-requirements.timestamp c2c-egg $(MAKO_FILES:.mako=)
	.build/venv/bin/python setup.py nosetests

.PHONY: flake8
flake8: .build/venv/bin/flake8
	# E712 is not compatible with SQLAlchemy
	find $(VALIDATE_PY_FOLDERS) -name \*.py | xargs .build/venv/bin/flake8 \
		--ignore=E712 \
		--max-complexity=20 \
		--max-line-length=100 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"
	.build/venv/bin/flake8 \
		--ignore=E712 \
		--max-complexity=20 \
		--max-line-length=100 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA" \
		travis/quote
	find $(VALIDATE_TEMPLATE_PY_FOLDERS) -name \*.py | xargs .build/venv/bin/flake8 --max-line-length=100
	find $(VALIDATE_PY_TEST_FOLDERS) -name \*.py | xargs .build/venv/bin/flake8 \
		--ignore=E501 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"

# i18n
$(HOME)/.transifexrc:
	echo "[https://www.transifex.com]" > $@
	echo "hostname = https://www.transifex.com" >> $@
	echo "username = c2c" >> $@
	echo "password = c2cc2c" >> $@
	echo "token =" >> $@

.build/venv/bin/tx: .build/dev-requirements.timestamp

.PHONY: transifex-get
transifex-get: c2cgeoportal/locale/c2cgeoportal.pot $(L10N_PO_FILES)

.PHONY: transifex-send
transifex-send: $(TX_DEPENDENCIES) c2cgeoportal/locale/c2cgeoportal.pot
	.build/venv/bin/tx push --source
	$(TOUCHBACK_TXRC)

.PHONY: transifex-init
transifex-init: $(TX_DEPENDENCIES) c2cgeoportal/locale/c2cgeoportal.pot
	.build/venv/bin/tx push --source
	.build/venv/bin/tx push --translations --force --no-interactive
	$(TOUCHBACK_TXRC)

# Import ngeo templates

.PHONY: import-ngeo-apps
import-ngeo-apps: $(APPS_HTML_FILES) $(APPS_JS_FILES)

ngeo: NGEO_GIT_ARGS ?= --branch=master
ngeo:
	git clone --depth 1 $(NGEO_GIT_ARGS) https://github.com/camptocamp/ngeo.git

.PRECIOUS: ngeo/contribs/gmf/apps/%/index.html
ngeo/contribs/gmf/apps/%/index.html: ngeo
	touch --no-create $@

.PRECIOUS: ngeo/contribs/gmf/apps/%/js/controller.js
ngeo/contribs/gmf/apps/%/js/controller.js: ngeo
	touch --no-create $@

$(APPS_PACAKGE_PATH)/templates/%.html_tmpl: ngeo/contribs/gmf/apps/%/index.html .build/requirements.timestamp c2cgeoportal/scripts/import_ngeo_apps.py
	.build/venv/bin/import-ngeo-apps --html $* $< $@

$(APPS_PACAKGE_PATH)/static-ngeo/js/%.js_tmpl: ngeo/contribs/gmf/apps/%/js/controller.js .build/requirements.timestamp c2cgeoportal/scripts/import_ngeo_apps.py
	.build/venv/bin/import-ngeo-apps --js $* $< $@

ngeo/.tx/config.mako: ngeo

c2cgeoportal/scaffolds/update/+dot+tx/CONST_config_mako: ngeo/.tx/config.mako
	mkdir -p $(dir $@)
	cp $< $@

.PRECIOUS: ngeo/package.json
ngeo/package.json: ngeo
	touch --no-create $@

c2cgeoportal/scaffolds/update/package.json_tmpl: ngeo/package.json .build/requirements.timestamp c2cgeoportal/scripts/import_ngeo_apps.py
	.build/venv/bin/import-ngeo-apps --package _ $< $@

# Templates

$(MAKO_FILES:.mako=): .build/venv/bin/c2c-template ${VARS_FILES}

%: %.mako
	$(C2C_TEMPLATE_CMD) --engine mako --files $<

c2cgeoportal/locale/c2cgeoportal.pot: lingua.cfg $(SRC_FILES) .build/requirements.timestamp
	mkdir -p $(dir $@)
	.build/venv/bin/pot-create --keyword _ --config $< --output $@ $(SRC_FILES)

c2cgeoportal/locale/en/LC_MESSAGES/c2cgeoportal.po: c2cgeoportal/locale/c2cgeoportal.pot .build/dev-requirements.timestamp
	mkdir -p $(dir $@)
	touch $@
	msgmerge --update $@ $<

c2cgeoportal/locale/%/LC_MESSAGES/c2cgeoportal.po: $(TX_DEPENDENCIES) .build/dev-requirements.timestamp
	mkdir -p $(dir $@)
	.build/venv/bin/tx pull -l $* --force
	$(TOUCHBACK_TXRC)

.build/%.mo.timestamp: %.po
	mkdir -p $(dir $@)
	msgfmt -o $*.mo $<
	touch $@

.build/venv/bin/flake8: .build/dev-requirements.timestamp

.build/venv/bin/c2c-template: .build/dev-requirements.timestamp

.build/venv/bin/jsbuild: .build/dev-requirements.timestamp

.build/venv/bin/c2c-cssmin: .build/dev-requirements.timestamp

.build/dev-requirements.timestamp: .build/venv.timestamp dev-requirements.txt
	$(PIP_CMD) install -r dev-requirements.txt
	touch $@

.build/venv.timestamp:
	mkdir -p $(dir $@)
	virtualenv --no-site-packages .build/venv
	$(PIP_CMD) install 'pip>=7' 'setuptools>=12'
	touch $@

.build/requirements.timestamp: .build/venv.timestamp setup.py \
		requirements.txt
	$(PIP_CMD) install -r requirements.txt
	touch $@

$(JSBUILD_ADMIN_OUTPUT_FILES): $(JSBUILD_ADMIN_FILES) $(JSBUILD_ADMIN_CONFIG)
	mkdir -p $(dir $@)
	.build/venv/bin/jsbuild $(JSBUILD_ADMIN_CONFIG) $(JSBUILD_ARGS) -j $(notdir $@) -o $(ADMIN_OUTPUT_DIR)

$(CSS_ADMIN_OUTPUT): .build/venv/bin/c2c-cssmin $(CSS_ADMIN_FILES)
	mkdir -p $(dir $@)
	.build/venv/bin/c2c-cssmin $(CSSMIN_ARGS) $@ $(CSS_ADMIN_FILES)

c2cgeoportal/version.py: gen_current_version

.PHONY: gen_current_version
gen_current_version:
	@echo "# Copyright (c) 2016, Camptocamp SA" > c2cgeoportal/version.py.new
	@echo "# All rights reserved." >> c2cgeoportal/version.py.new
	@echo  >> c2cgeoportal/version.py.new
	@echo "# Auto-generated file. Do not Edit!" >> c2cgeoportal/version.py.new
	@.build/venv/bin/python c2cgeoportal/scripts/gen_version.py >> c2cgeoportal/version.py.new
	@if `diff -q c2cgeoportal/version.py.new c2cgeoportal/version.py > /dev/null 2> /dev/null`; then rm c2cgeoportal/version.py.new; else echo "New version of c2cgeoportal/version.py"; mv c2cgeoportal/version.py.new c2cgeoportal/version.py; fi
