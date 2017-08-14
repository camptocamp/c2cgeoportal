BUILD_DIR ?= /build
TEMPLATE_EXCLUDE += MANIFEST.in $(BUILD_DIR) .eggs c2cgeoportal/scaffolds c2cgeoportal/tests/testegg c2cgeoportal/templates ngeo
FIND_OPTS = $(foreach ELEM, $(TEMPLATE_EXCLUDE),-path ./$(ELEM) -prune -o) -type f
MAKO_FILES = $(shell find $(FIND_OPTS) -name "*.mako" -print)
VARS_FILE ?= vars.yaml
VARS_FILES += vars.yaml

DEVELOPPEMENT ?= FALSE

ifdef TRAVIS_TAG
VERSION ?= $(TRAVIS_TAG)
else
VERSION ?= 2.2
endif

VALIDATE_PY_FOLDERS = setup.py c2cgeoportal/*.py c2cgeoportal/lib c2cgeoportal/scripts c2cgeoportal/views c2cgeoportal/scaffolds/update/CONST_alembic
VALIDATE_TEMPLATE_PY_FOLDERS = c2cgeoportal/scaffolds
VALIDATE_PY_TEST_FOLDERS = c2cgeoportal/tests

SPHINX_FILES = $(shell find doc -name "*.rst" -print)
SPHINX_MAKO_FILES = $(shell find doc -name "*.rst.mako" -print)

export TX_VERSION = $(shell python setup.py --version | awk -F . '{{print $$1"_"$$2}}')
TX_DEPENDENCIES = $(HOME)/.transifexrc .tx/config
ifeq (,$(wildcard $(HOME)/.transifexrc))
TOUCHBACK_TXRC = touch --date "$(shell date --iso-8601=seconds)" $(HOME)/.transifexrc
else
TOUCHBACK_TXRC = touch --date "$(shell stat -c '%y' $(HOME)/.transifexrc)" $(HOME)/.transifexrc
endif
L10N_LANGUAGES = fr de
L10N_PO_FILES = $(addprefix c2cgeoportal/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal.po, $(L10N_LANGUAGES))) \
	$(addprefix c2cgeoportal/scaffolds/create/+package+/locale/,$(addsuffix LC_MESSAGES/+package+-client.po, $(L10N_LANGUAGES)))
LANGUAGES = en $(L10N_LANGUAGES)
PO_FILES = $(addprefix c2cgeoportal/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal.po, $(LANGUAGES)))
MO_FILES = $(addprefix $(BUILD_DIR)/,$(addsuffix .mo.timestamp,$(basename $(PO_FILES))))
SRC_FILES = $(filter-out c2cgeoportal/version.py, $(shell ls -1 c2cgeoportal/*.py)) \
	$(shell find c2cgeoportal/lib -name "*.py" -print) \
	$(shell find c2cgeoportal/views -name "*.py" -print) \
	$(filter-out c2cgeoportal/scripts/theme2fts.py, $(shell find c2cgeoportal/scripts -name "*.py" -print))

APPS += desktop mobile
APPS_PACKAGE_PATH = c2cgeoportal/scaffolds/create/+package+
APPS_HTML_FILES = $(addprefix $(APPS_PACKAGE_PATH)/templates/, $(addsuffix .html_tmpl, $(APPS)))
APPS_JS_FILES = $(addprefix $(APPS_PACKAGE_PATH)/static-ngeo/js/, $(addsuffix .js_tmpl, $(APPS)))
APPS_FILES = $(APPS_HTML_FILES) $(APPS_JS_FILES) \
	$(addprefix $(APPS_PACKAGE_PATH)/static-ngeo/images/,favicon.ico logo.png background-layer-button.png) \
	$(APPS_PACKAGE_PATH)/static-ngeo/components/contextualdata/contextualdata.html

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
	$(MO_FILES) \
	$(APPS_FILES) \
	c2cgeoportal/scaffolds/update/+dot+tx/CONST_config_mako \
	c2cgeoportal/scaffolds/create/package.json_tmpl \
	c2cgeoportal/scaffolds/update/CONST_create_template/

.PHONY: buildall
buildall: build doc tests checks

.PHONY: doc
doc: $(BUILD_DIR)/sphinx.timestamp

.PHONY: tests
tests: nose

.PHONY: checks
checks: flake8 git-attributes quote spell

.PHONY: clean
clean:
	rm --force $(BUILD_DIR)/venv.timestamp
	rm --force $(BUILD_DIR)/c2ctemplate-cache.yaml
	rm --force c2cgeoportal/version.py
	rm --force c2cgeoportal/locale/*.pot
	rm --force c2cgeoportal/locale/en/LC_MESSAGES/c2cgeoportal.po
	rm --recursive --force c2cgeoportal/static/build
	rm --force $(MAKO_FILES:.mako=)
	rm --recursive --force ngeo
	rm --force $(APPS_FILES)

.PHONY: cleanall
cleanall: clean
	rm --force $(PO_FILES)
	rm --recursive --force $(BUILD_DIR)/*

.PHONY: c2c-egg
c2c-egg: $(BUILD_DIR)/requirements.timestamp

$(BUILD_DIR)/sphinx.timestamp: $(SPHINX_FILES) $(SPHINX_MAKO_FILES:.mako=)
	mkdir -p doc/_build/html
	doc/build.sh
	touch $@

.PHONY: nose
nose: c2c-egg $(MAKO_FILES:.mako=)
	nosetests

.PHONY: flake8
flake8:
	# E712 is not compatible with SQLAlchemy
	find $(VALIDATE_PY_FOLDERS) -name \*.py | xargs flake8 \
		--ignore=E712 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"
	flake8 \
		--ignore=E712 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA" \
		travis/quote
	find $(VALIDATE_TEMPLATE_PY_FOLDERS) -name \*.py | xargs flake8 --max-line-length=100
	find $(VALIDATE_PY_TEST_FOLDERS) -name \*.py | xargs flake8 \
		--ignore=E501 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"

.PHONY: git-attributes
git-attributes:
	git --no-pager diff --check `git log --oneline | tail -1 | cut --fields=1 --delimiter=' '`

.PHONY: quote
quote:
	travis/quote `find c2cgeoportal/lib c2cgeoportal/scaffolds/create c2cgeoportal/templates c2cgeoportal/tests c2cgeoportal/views -name '*.py'` c2cgeoportal/*.py setup.py
	travis/squote `find c2cgeoportal/scaffolds/update/CONST_alembic -name '*.py'`

.PHONY: spell
spell:
	@codespell setup.py $(shell find c2cgeoportal -name static -prune -or -name '*.py' -print)

# i18n
$(HOME)/.transifexrc:
	echo "[https://www.transifex.com]" > $@
	echo "hostname = https://www.transifex.com" >> $@
	echo "username = c2c" >> $@
	echo "password = c2cc2c" >> $@
	echo "token =" >> $@

.PHONY: transifex-get
transifex-get: c2cgeoportal/locale/c2cgeoportal.pot $(L10N_PO_FILES)

.PHONY: transifex-send
transifex-send: $(TX_DEPENDENCIES) c2cgeoportal/locale/c2cgeoportal.pot
	tx push --source
	$(TOUCHBACK_TXRC)

.PHONY: transifex-init
transifex-init: $(TX_DEPENDENCIES) c2cgeoportal/locale/c2cgeoportal.pot
	tx push --source --force --no-interactive
	tx push --translations --force --no-interactive
	$(TOUCHBACK_TXRC)

# Import ngeo templates

.PHONY: import-ngeo-apps
import-ngeo-apps: $(APPS_FILES)

ngeo: $(BUILD_DIR)/requirements.timestamp
	if [ ! -e "ngeo" ] ; then git clone --depth 1 --branch=$(shell $(BUILD_DIR)/venv/bin/ngeo-version) https://github.com/camptocamp/ngeo.git ; fi
	touch --no-create $@

.PRECIOUS: ngeo/contribs/gmf/apps/%/index.html
ngeo/contribs/gmf/apps/%/index.html: ngeo
	touch --no-create $@

.PRECIOUS: ngeo/contribs/gmf/apps/%/js/controller.js
ngeo/contribs/gmf/apps/%/js/controller.js: ngeo
	touch --no-create $@

$(APPS_PACKAGE_PATH)/templates/%.html_tmpl: ngeo/contribs/gmf/apps/%/index.html $(BUILD_DIR)/requirements.timestamp c2cgeoportal/scripts/import_ngeo_apps.py
	$(BUILD_DIR)/venv/bin/import-ngeo-apps --html $* $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/%.js_tmpl: ngeo/contribs/gmf/apps/%/js/controller.js $(BUILD_DIR)/requirements.timestamp c2cgeoportal/scripts/import_ngeo_apps.py
	$(BUILD_DIR)/venv/bin/import-ngeo-apps --js $* $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/components/contextualdata/contextualdata.html: ngeo/contribs/gmf/apps/desktop/contextualdata.html
	mkdir -p $(dir $@)
	cp $< $@

ngeo/.tx/config.mako: ngeo

c2cgeoportal/scaffolds/update/+dot+tx/CONST_config_mako: ngeo/.tx/config.mako
	mkdir -p $(dir $@)
	cp $< $@

.PRECIOUS: ngeo/package.json
ngeo/package.json: ngeo
	touch --no-create $@

c2cgeoportal/scaffolds/create/package.json_tmpl: ngeo/package.json $(BUILD_DIR)/requirements.timestamp c2cgeoportal/scripts/import_ngeo_apps.py
	$(BUILD_DIR)/venv/bin/import-ngeo-apps --package _ $< $@

.PRECIOUS: c2cgeoportal/scaffolds/update/CONST_create_template/
c2cgeoportal/scaffolds/update/CONST_create_template/: c2cgeoportal/scaffolds/create/
	rm -rf $@ || true
	cp -r $< $@

.PRECIOUS: ngeo/contribs/gmf/apps/desktop/image/%
ngeo/contribs/gmf/apps/desktop/image/%: ngeo
	touch --no-create $@

.PRECIOUS: $(APPS_PACKAGE_PATH)/static-ngeo/images/%
$(APPS_PACKAGE_PATH)/static-ngeo/images/%: ngeo/contribs/gmf/apps/desktop/image/%
	mkdir -p $(dir $@)
	cp $< $@

# Templates

$(BUILD_DIR)/c2ctemplate-cache.yaml: $(VARS_FILES)
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/c2c-template --vars $(VARS_FILE) --get-cache $@

$(MAKO_FILES:.mako=): $(BUILD_DIR)/c2ctemplate-cache.yaml

%: %.mako $(BUILD_DIR)/requirements.timestamp $(BUILD_DIR)/c2ctemplate-cache.yaml
	c2c-template --cache $(BUILD_DIR)/c2ctemplate-cache.yaml --engine mako --files $<

c2cgeoportal/locale/c2cgeoportal.pot: lingua.cfg $(SRC_FILES) $(BUILD_DIR)/requirements.timestamp
	mkdir -p $(dir $@)
	pot-create --keyword _ --config $< --output $@ $(SRC_FILES)

c2cgeoportal/locale/en/LC_MESSAGES/c2cgeoportal.po: c2cgeoportal/locale/c2cgeoportal.pot
	mkdir -p $(dir $@)
	touch $@
	msgmerge --update $@ $<

c2cgeoportal/locale/%/LC_MESSAGES/c2cgeoportal.po: $(TX_DEPENDENCIES)
	mkdir -p $(dir $@)
	tx pull -l $* --force
	$(TOUCHBACK_TXRC)
	test -s $@

c2cgeoportal/scaffolds/create/+package+/locale/%/LC_MESSAGES/+package+-client.po: \
		$(TX_DEPENDENCIES) $(BUILD_DIR)/dev-requirements.timestamp
	mkdir -p $(dir $@)
	$(BUILD_DIR)/venv/bin/tx pull -l $* --force
	$(TOUCHBACK_TXRC)
	test -s $@

$(BUILD_DIR)/%.mo.timestamp: %.po
	mkdir -p $(dir $@)
	msgfmt -o $*.mo $<
	touch $@

$(BUILD_DIR)/venv.timestamp:
	mkdir -p $(dir $@)
	virtualenv --system-site-packages $(BUILD_DIR)/venv
	touch $@

$(BUILD_DIR)/requirements.timestamp: setup.py $(BUILD_DIR)/venv.timestamp
	$(BUILD_DIR)/venv/bin/pip install -e .
	touch $@

c2cgeoportal/version.py:
	@echo "# Copyright (c) 2017, Camptocamp SA" > $@.new
	@echo "# All rights reserved." >> $@.new
	@echo  >> $@.new
	@echo "# Auto-generated file. Do not Edit!" >> $@.new
	@$(BUILD_DIR)/venv/bin/python c2cgeoportal/scripts/gen_version.py >> $@.new
	rm --force $@
	mv $@.new $@

.PHONY: gen_current_version
gen_current_versiion: c2cgeoportal/version.py
