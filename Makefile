BUILD_DIR ?= /build
MAKO_FILES = docker-compose.yaml.mako $(shell find .tx doc docker geoportal/tests/functional -type f -name "*.mako" -print)
VARS_FILE ?= vars.yaml
VARS_FILES += vars.yaml

DEVELOPMENT ?= FALSE

# PRERULE_CMD display the files imply that the rule is running with the files dates
ifeq ($(DEBUG), TRUE)
ifeq ($(OPERATING_SYSTEM), WINDOWS)
PRERULE_CMD ?= @echo "Build $@ due mofification on $?"; ls -t --full-time --reverse $? $@ || true
else
PRERULE_CMD ?= @echo "Build \033[1;34m$@\033[0m due modification on \033[1;34m$?\033[0m" 1>&2; ls -t --full-time --reverse $? $@ 1>&2 || true
endif
endif

export MAJOR_VERSION = 2.3
export MAIN_BRANCH = master
ifdef TRAVIS_TAG
export VERSION = $(TRAVIS_TAG)
else
export VERSION = $(MAJOR_VERSION)
endif

DOCKER_BASE = camptocamp/geomapfish
DOCKER_TEST_BASE = $(DOCKER_BASE)-test

VALIDATE_PY_FOLDERS = commons admin \
	geoportal/setup.py \
	geoportal/c2cgeoportal_geoportal/*.py \
	geoportal/c2cgeoportal_geoportal/lib \
	geoportal/c2cgeoportal_geoportal/scripts \
	geoportal/c2cgeoportal_geoportal/views
VALIDATE_TEMPLATE_PY_FOLDERS = geoportal/c2cgeoportal_geoportal/scaffolds
VALIDATE_PY_TEST_FOLDERS = geoportal/tests

SPHINX_FILES = $(shell find doc -name "*.rst" -print)
SPHINX_MAKO_FILES = $(shell find doc -name "*.rst.mako" -print)

export TX_VERSION = $(shell echo $(MAJOR_VERSION) | awk -F . '{{print $$1"_"$$2}}')
TX_DEPENDENCIES = $(HOME)/.transifexrc .tx/config
ifeq (,$(wildcard $(HOME)/.transifexrc))
TOUCHBACK_TXRC := touch --no-create --date "$(shell date --iso-8601=seconds)" $(HOME)/.transifexrc
else
TOUCHBACK_TXRC := touch --no-create --date "$(shell stat -c '%y' $(HOME)/.transifexrc)" $(HOME)/.transifexrc
endif
LANGUAGES = fr de it
export LANGUAGES
ALL_LANGUAGES = en $(LANGUAGES)
L10N_PO_FILES = $(addprefix geoportal/c2cgeoportal_geoportal/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal_geoportal.po, $(LANGUAGES))) \
	$(addprefix geoportal/c2cgeoportal_geoportal/locale/,$(addsuffix /LC_MESSAGES/ngeo.po, $(LANGUAGES))) \
	$(addprefix geoportal/c2cgeoportal_geoportal/locale/,$(addsuffix /LC_MESSAGES/gmf.po, $(LANGUAGES))) \
	$(addprefix geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/,$(addsuffix /LC_MESSAGES/+package+_geoportal-client.po, $(ALL_LANGUAGES)))
PO_FILES = $(addprefix geoportal/c2cgeoportal_geoportal/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal_geoportal.po, $(LANGUAGES)))
PO_FILES += $(addprefix admin/c2cgeoportal_admin/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal_admin.po, $(LANGUAGES)))
MO_FILES = $(addprefix $(BUILD_DIR)/,$(addsuffix .mo.timestamp,$(basename $(PO_FILES))))
SRC_FILES = $(shell ls -1 geoportal/c2cgeoportal_geoportal/*.py) \
	$(shell find geoportal/c2cgeoportal_geoportal/lib -name "*.py" -print) \
	$(shell find geoportal/c2cgeoportal_geoportal/views -name "*.py" -print) \
	$(filter-out geoportal/c2cgeoportal_geoportal/scripts/theme2fts.py, $(shell find geoportal/c2cgeoportal_geoportal/scripts -name "*.py" -print))
ADMIN_SRC_FILES = $(shell ls -1 commons/c2cgeoportal_commons/models/*.py) \
	$(shell find admin/c2cgeoportal_admin -name "*.py" -print) \
	$(shell find admin/c2cgeoportal_admin/templates -name "*.jinja2" -print) \
	$(shell find admin/c2cgeoportal_admin/templates/widgets -name "*.pt" -print)

APPS += desktop mobile
APPS_PACKAGE_PATH = geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal
APPS_HTML_FILES = $(addprefix $(APPS_PACKAGE_PATH)/static-ngeo/js/apps/, $(addsuffix .html.ejs_tmpl, $(APPS)))
APPS_JS_FILES = $(addprefix $(APPS_PACKAGE_PATH)/static-ngeo/js/apps/Controller, $(addsuffix .js_tmpl, $(APPS)))
APPS_ALT += desktop_alt mobile_alt oeedit oeview
APPS_PACKAGE_PATH_ALT = geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/geoportal/+package+_geoportal/
APPS_HTML_FILES += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/, $(addsuffix .html.ejs_tmpl, $(APPS_ALT)))
APPS_JS_FILES += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/Controller, $(addsuffix .js_tmpl, $(APPS_ALT)))
APPS_FILES = $(APPS_HTML_FILES) $(APPS_JS_FILES) \
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/contextualdata.html \
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/background-layer-button.png \
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/favicon.ico \
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/logo.png

.PHONY: help
help:
	@echo "Usage: $(MAKE) <target>"
	@echo
	@echo "Main targets:"
	@echo
	@echo  "- docker-build   	Pull all the needed Docker images, build all (Outside Docker)"
	@echo  "- build 		Build and configure the project"
	@echo  "- doc 			Build the project documentation"
	@echo  "- tests 		Perform a number of tests on the code"
	@echo  "- checks		Perform a number of checks on the code"
	@echo  "- clean 		Remove generated files"
	@echo  "- clean-all 		Remove all the build artifacts"
	@echo  "- transifex-send	Send the localisation to Transifex"

.PHONY: docker-build
docker-build:
	for image in `find -name Dockerfile -o -name Dockerfile.mako | xargs grep --no-filename FROM | awk '{print $$2}' | sort -u`; do docker pull $$image; done
	docker build --tag=camptocamp/geomapfish-build-dev:${MAJOR_VERSION} docker/build
	./docker-run make build

.PHONY: build
build: \
	docker-build-build \
	docker-build-testdb \
	prepare-tests

.PHONY: doc
doc: $(BUILD_DIR)/sphinx.timestamp

.PHONY: checks
checks: flake8 mypy git-attributes quote spell yamllint pylint eof-newline additionallint

.PHONY: clean
clean:
	rm --force $(BUILD_DIR)/venv.timestamp
	rm --force $(BUILD_DIR)/c2ctemplate-cache.json
	rm --force geoportal/c2cgeoportal_geoportal/locale/*.pot
	rm --force geoportal/c2cgeoportal_admin/locale/*.pot
	rm --force geoportal/c2cgeoportal_geoportal/locale/en/LC_MESSAGES/c2cgeoportal_geoportal.po
	rm --force geoportal/c2cgeoportal_admin/locale/en/LC_MESSAGES/c2cgeoportal_admin.po
	rm --recursive --force geoportal/c2cgeoportal_geoportal/static/build
	rm --force $(MAKO_FILES:.mako=)
	rm --force $(APPS_FILES)
	rm --force geoportal/tests/functional/alembic.yaml

.PHONY: clean-all
clean-all: clean
	rm --recursive --force ngeo
	rm --force $(PO_FILES)
	rm --recursive --force $(BUILD_DIR)/*

$(BUILD_DIR)/sphinx.timestamp: $(SPHINX_FILES) $(SPHINX_MAKO_FILES:.mako=)
	$(PRERULE_CMD)
	mkdir --parent doc/_build/html
	doc/build.sh
	touch $@

.PHONY: docker-build-gisdb
docker-build-gisdb: $(shell docker-required --path docker/gis-db)
	docker build --tag=$(DOCKER_TEST_BASE)-gis-db:latest docker/gis-db

geoportal/tests/functional/alembic.yaml: $(BUILD_DIR)/c2ctemplate-cache.json
	$(PRERULE_CMD)
	c2c-template --cache $(BUILD_DIR)/c2ctemplate-cache.json --get-config $@ srid schema schema_static sqlalchemy.url

docker/test-db/12-alembic.sql: \
		geoportal/tests/functional/alembic.ini \
		geoportal/tests/functional/alembic.yaml \
		$(shell ls -1 commons/c2cgeoportal_commons/alembic/main/*.py) \
		$(BUILD_DIR)/commons.timestamp
	$(PRERULE_CMD)
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/alembic --config=$< --name=main upgrade --sql head > $@

docker/test-db/13-alembic-static.sql: \
		geoportal/tests/functional/alembic.ini \
		geoportal/tests/functional/alembic.yaml \
		$(shell ls -1 commons/c2cgeoportal_commons/alembic/static/*.py) \
		$(BUILD_DIR)/commons.timestamp
	$(PRERULE_CMD)
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/alembic --config=$< --name=static upgrade --sql head > $@

docker-build-testdb: $(shell docker-required --path docker/test-db) \
		docker/test-db/12-alembic.sql docker/test-db/13-alembic-static.sql \
		docker-build-gisdb
	docker build --tag=$(DOCKER_TEST_BASE)-db:latest docker/test-db

docker-build-testmapserver: $(shell docker-required --path docker/test-mapserver)
	docker build --tag=$(DOCKER_TEST_BASE)-mapserver:latest docker/test-mapserver

.PHONY: docker-build-build
docker-build-build: $(shell docker-required --path . --replace-pattern='^test(.*).mako$/test/\1') \
		geoportal/c2cgeoportal_geoportal/scaffolds/create/docker-run \
		npm-packages admin/npm-packages \
		geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/ \
		geoportal/c2cgeoportal_geoportal/scaffolds/nondockerupdate/CONST_create_template/ \
		$(MO_FILES) \
		$(L10N_PO_FILES) \
		$(APPS_FILES)
	docker build --build-arg=VERSION=$(VERSION) --tag=$(DOCKER_BASE)-build:$(MAJOR_VERSION) .

.PHONY: prepare-tests
prepare-tests: \
		geoportal/tests/functional/test.ini \
		commons/tests.yaml \
		admin/tests.ini \
		docker-compose.yaml \
		docker-build-testmapserver \
		docker-build-testdb \
		$(addprefix geoportal/c2cgeoportal_geoportal/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal_geoportal.po, $(LANGUAGES))) \
		$(addprefix admin/c2cgeoportal_admin/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal_admin.po, $(LANGUAGES))) \
		docker/test-mapserver/mapserver.map

.PHONY: tests
tests:
	py.test --color=yes --cov=commons/c2cgeoportal_commons commons/acceptance_tests
	py.test --color=yes --cov-append --cov=geoportal/c2cgeoportal_geoportal geoportal/tests
	py.test --color=yes --cov-append --cov=admin/c2cgeoportal_admin admin/acceptance_tests

.PHONY: flake8
flake8:
	# E712 is not compatible with SQLAlchemy
	find $(VALIDATE_PY_FOLDERS) \
		-not \( -path "*/.build" -prune \) \
		-not \( -path "*/node_modules" -prune \) \
		-name \*.py | xargs flake8 \
		--ignore=E712 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"
	git grep --files-with-match '/usr/bin/env python' | grep -v Makefile | xargs flake8 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"
	find $(VALIDATE_TEMPLATE_PY_FOLDERS) -name \*.py | xargs flake8 --config=setup.cfg
	find $(VALIDATE_PY_TEST_FOLDERS) -name \*.py | xargs flake8 \
		--ignore=E501 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"

.PHONY: pylint
pylint: $(BUILD_DIR)/commons.timestamp
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only geoportal/c2cgeoportal_geoportal
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only geoportal/tests
	pylint --errors-only commons/c2cgeoportal_commons
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only commons/acceptance_tests
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only admin/c2cgeoportal_admin
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only admin/acceptance_tests

.PHONY: mypy
mypy:
	MYPYPATH=/usr/local/lib/python3.6/site-packages:/opt/c2cwsgiutils \
		mypy --disallow-untyped-defs --strict-optional --follow-imports skip \
			commons/c2cgeoportal_commons
	# TODO: add --disallow-untyped-defs
	MYPYPATH=/usr/local/lib/python3.6/site-packages/ \
		mypy --ignore-missing-imports --strict-optional --follow-imports skip \
			geoportal/c2cgeoportal_geoportal \
			admin/c2cgeoportal_admin \

.PHONY: git-attributes
git-attributes:
	git --no-pager diff --check `git log --oneline | tail -1 | cut --fields=1 --delimiter=' '`

.PHONY: quote
quote:
	travis/squote geoportal/setup.py \
		`find commons/c2cgeoportal_commons -name '*.py'` \
		`find admin/c2cgeoportal_admin -name '*.py'` \

.PHONY: spell
spell:
	codespell --ignore-words=spell-ignore-words.txt geoportal/setup.py \
		$(shell find commons/c2cgeoportal_commons -name '*.py' -print) \
		$(shell find geoportal/c2cgeoportal_geoportal -name static -prune -or -name '*.py' -print) \
		$(shell find admin/c2cgeoportal_admin -name '*.py' -print)

YAML_FILES ?= $(shell find -name node_modules -prune -or -name .build -prune -or -name ngeo -prune -or -name functional -prune -or \( -name "*.yml" -or -name "*.yaml" \) -print)
.PHONY: yamllint
yamllint:
	yamllint --strict --config-file=yamllint.yaml -s $(YAML_FILES)

.PHONY: eof-newline
eof-newline:
	travis/test-eof-newline

.PHONY: additionallint
additionallint:
	# Verify that we don't directly use the CI project name in the scaffolds
	if [ "`git grep testgeomapfish geoportal/c2cgeoportal_geoportal/scaffolds`" != "" ]; \
	then \
		echo "ERROR: You still have a testgeomapfish in one of your scaffolds"; \
		git grep testgeomapfish geoportal/c2cgeoportal_geoportal/scaffolds; \
		false; \
	fi

# i18n
$(HOME)/.transifexrc:
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	echo "[https://www.transifex.com]" > $@
	echo "hostname = https://www.transifex.com" >> $@
	echo "username = c2c" >> $@
	echo "password = c2cc2c" >> $@
	echo "token =" >> $@

.PHONY: transifex-get
transifex-get: $(L10N_PO_FILES)

.PHONY: transifex-send
transifex-send: $(TX_DEPENDENCIES) \
		geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot \
		admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot
	$(PRERULE_CMD)
	tx push --source --resource=geomapfish.c2cgeoportal_geoportal-$(TX_VERSION)
	tx push --source --resource=geomapfish.c2cgeoportal_admin-$(TX_VERSION)
	$(TOUCHBACK_TXRC)

.PHONY: transifex-init
transifex-init: $(TX_DEPENDENCIES) \
		geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot \
		admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot
	$(PRERULE_CMD)
	tx push --source --force --no-interactive --resource=geomapfish.c2cgeoportal_geoportal-$(TX_VERSION)
	tx push --source --force --no-interactive --resource=geomapfish.c2cgeoportal_admin-$(TX_VERSION)
	tx push --translations --force --no-interactive --resource=geomapfish.c2cgeoportal_geoportal-$(TX_VERSION)
	tx push --translations --force --no-interactive --resource=geomapfish.c2cgeoportal_admin-$(TX_VERSION)
	$(TOUCHBACK_TXRC)

# Import ngeo templates

.PHONY: import-ngeo-apps
import-ngeo-apps: $(APPS_FILES)

.PRECIOUS: ngeo
ngeo:
	$(PRERULE_CMD)
	if [ ! -e "ngeo" ] ; then git clone --depth 1 --branch=$(shell VERSION=$(MAIN_BRANCH) npm-packages --version) https://github.com/camptocamp/ngeo.git ; fi
	touch --no-create $@

.PRECIOUS: ngeo/contribs/gmf/apps/%/index.html.ejs
ngeo/contribs/gmf/apps/%/index.html.ejs: ngeo
	$(PRERULE_CMD)
	touch --no-create $@

.PRECIOUS: ngeo/contribs/gmf/apps/%/Controller.js
ngeo/contribs/gmf/apps/%/Controller.js: ngeo
	$(PRERULE_CMD)
	touch --no-create $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/%.html.ejs_tmpl: ngeo/contribs/gmf/apps/%/index.html.ejs
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	import-ngeo-apps --html $* $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/Controller%.js_tmpl: ngeo/contribs/gmf/apps/%/Controller.js
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	import-ngeo-apps --js $* $< $@

$(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/%.html.ejs_tmpl: ngeo/contribs/gmf/apps/%/index.html.ejs
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	import-ngeo-apps --html $* $< $@

$(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/Controller%.js_tmpl: ngeo/contribs/gmf/apps/%/Controller.js
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	import-ngeo-apps --js $* $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/contextualdata.html: ngeo/contribs/gmf/apps/desktop/contextualdata.html
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/%: ngeo/contribs/gmf/apps/desktop/image/%
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp $< $@

geoportal/c2cgeoportal_geoportal/scaffolds/create/docker-run: docker-run
	$(PRERULE_CMD)
	cp $< $@

npm-packages: ngeo package.json
	$(PRERULE_CMD)
	npm-packages --ngeo \
		coveralls gaze jasmine-core jsdoc jsdom karma karma-chrome-launcher karma-coverage \
		karma-jasmine karma-sourcemap-loader karma-webpack \
		--src=ngeo/package.json --src=package.json --dst=$@

admin/npm-packages: ngeo package.json
	$(PRERULE_CMD)
	npm-packages --src=package.json --dst=$@

geoportal/package.json: ngeo/package.json
	$(PRERULE_CMD)
	import-ngeo-apps --package _ $< $@

.PRECIOUS: geoportal/c2cgeoportal_geoportal/scaffolds%update/CONST_create_template/
geoportal/c2cgeoportal_geoportal/scaffolds%update/CONST_create_template/: \
		geoportal/c2cgeoportal_geoportal/scaffolds%create/ \
		$(addprefix geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/,$(addsuffix /LC_MESSAGES/+package+_geoportal-client.po, $(ALL_LANGUAGES))) \
		geoportal/c2cgeoportal_geoportal/scaffolds/create/docker-run \
		$(APPS_FILES)
	$(PRERULE_CMD)
	rm -rf $@ || true
	cp -r $< $@

.PRECIOUS: ngeo/contribs/gmf/apps/desktop/image/%
ngeo/contribs/gmf/apps/desktop/image/%: ngeo
	$(PRERULE_CMD)
	touch --no-create $@

.PRECIOUS: $(APPS_PACKAGE_PATH)/static-ngeo/images/%
$(APPS_PACKAGE_PATH)/static-ngeo/images/%: ngeo/contribs/gmf/apps/desktop/image/%
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp $< $@

# Templates

$(BUILD_DIR)/c2ctemplate-cache.json: $(VARS_FILES)
	$(PRERULE_CMD)
	c2c-template --vars $(VARS_FILE) --get-cache $@

%: %.mako $(BUILD_DIR)/c2ctemplate-cache.json
	$(PRERULE_CMD)
	c2c-template --cache $(BUILD_DIR)/c2ctemplate-cache.json --engine mako --files $<

geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot: \
		lingua.cfg $(SRC_FILES)
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	pot-create --config $< --keyword _ --output $@ $(SRC_FILES)

admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot: \
		lingua.cfg $(ADMIN_SRC_FILES)
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	pot-create --config $< --keyword _ --output $@ $(ADMIN_SRC_FILES)

geoportal/c2cgeoportal_geoportal/locale/en/LC_MESSAGES/c2cgeoportal_geoportal.po: geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	touch $@
	msgmerge --update $@ $<

admin/c2cgeoportal_admin/locale/en/LC_MESSAGES/c2cgeoportal_admin.po: admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	touch $@
	msgmerge --update $@ $<

geoportal/c2cgeoportal_geoportal/locale/%/LC_MESSAGES/c2cgeoportal_geoportal.po: $(TX_DEPENDENCIES)
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	tx pull --language $* --resource geomapfish.c2cgeoportal_geoportal-$(TX_VERSION) --force
	$(TOUCHBACK_TXRC)
	test -s $@

geoportal/c2cgeoportal_geoportal/locale/%/LC_MESSAGES/ngeo.po: $(TX_DEPENDENCIES)
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	tx pull --language $* --resource ngeo.ngeo-$(TX_VERSION) --force
	$(TOUCHBACK_TXRC)
	test -s $@

geoportal/c2cgeoportal_geoportal/locale/%/LC_MESSAGES/gmf.po: $(TX_DEPENDENCIES)
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	tx pull --language $* --resource ngeo.gmf-$(TX_VERSION) --force
	$(TOUCHBACK_TXRC)
	test -s $@

admin/c2cgeoportal_admin/locale/%/LC_MESSAGES/c2cgeoportal_admin.po: $(TX_DEPENDENCIES)
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	tx pull --language $* --resource geomapfish.c2cgeoportal_admin-$(TX_VERSION) --force
	$(TOUCHBACK_TXRC)
	test -s $@

geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/%/LC_MESSAGES/+package+_geoportal-client.po: \
		$(TX_DEPENDENCIES)
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	tx pull --language $* --resource ngeo.gmf-apps-$(TX_VERSION) --force
	$(TOUCHBACK_TXRC)
	test -s $@

geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/en/LC_MESSAGES/+package+_geoportal-client.po:
	$(PRERULE_CMD)
	@echo "Nothing to be done for $@"

.PHONY: buildlocales
buildlocales: $(MO_FILES)

$(BUILD_DIR)/%.mo.timestamp: %.po
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	msgfmt -o $*.mo $<
	touch $@

$(BUILD_DIR)/venv.timestamp:
	$(PRERULE_CMD)
	virtualenv --system-site-packages $(BUILD_DIR)/venv
	touch $@

$(BUILD_DIR)/commons.timestamp: $(BUILD_DIR)/venv.timestamp
	$(PRERULE_CMD)
	$(BUILD_DIR)/venv/bin/pip install --editable=commons
	touch $@
