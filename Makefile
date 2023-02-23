BUILD_DIR ?= /build
MAKO_FILES = Dockerfile.mako docker-compose.yaml.mako $(shell find doc docker geoportal/tests/functional -type f -name "*.mako" -print)
VARS_FILE ?= vars.yaml
VARS_FILES += vars.yaml

DEVELOPMENT ?= FALSE

# PRERULE_CMD display the files imply that the rule is running with the files dates
ifeq ($(DEBUG), TRUE)
ifeq ($(OPERATING_SYSTEM), WINDOWS)
PRERULE_CMD ?= @echo "Build $@ due modification on $?"; ls -t --full-time --reverse $? $@ || true
else
PRERULE_CMD ?= @echo "Build \033[1;34m$@\033[0m due modification on \033[1;34m$?\033[0m" 1>&2; ls -t --full-time --reverse $? $@ 1>&2 || true
endif
endif

export MAJOR_VERSION = 2.4
export MAIN_BRANCH = 2.4
ifdef RELEASE_TAG
export VERSION = $(RELEASE_TAG)
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
	geoportal/c2cgeoportal_geoportal/views \
	docker/qgisserver/geomapfish_qgisserver
VALIDATE_TEMPLATE_PY_FOLDERS = geoportal/c2cgeoportal_geoportal/scaffolds
VALIDATE_PY_TEST_FOLDERS = geoportal/tests

SPHINX_FILES = $(shell find doc -name "*.rst" -print)
SPHINX_MAKO_FILES = $(shell find doc -name "*.rst.mako" -print)

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

APPS += desktop mobile iframe_api
APPS_PACKAGE_PATH_NONDOCKER = geoportal/c2cgeoportal_geoportal/scaffolds/nondockercreate/geoportal/+package+_geoportal
APPS_PACKAGE_PATH = geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal
APPS_HTML_FILES = $(addprefix $(APPS_PACKAGE_PATH_NONDOCKER)/static-ngeo/js/apps/, $(addsuffix .html.ejs_tmpl, $(APPS)))
APPS_HTML_FILES += $(addprefix $(APPS_PACKAGE_PATH)/static-ngeo/js/apps/, $(addsuffix .html.ejs_tmpl, $(APPS)))
APPS_JS_FILES = $(addprefix $(APPS_PACKAGE_PATH)/static-ngeo/js/apps/Controller, $(addsuffix .js_tmpl, $(APPS)))
APPS_SASS_FILES += $(addprefix $(APPS_PACKAGE_PATH)/static-ngeo/js/apps/sass/, $(addsuffix .scss, $(filter-out iframe_api, $(APPS))))
APPS_SASS_FILES += $(addprefix $(APPS_PACKAGE_PATH)/static-ngeo/js/apps/sass/vars_, $(addsuffix .scss, $(filter-out iframe_api, $(APPS))))
APPS_FILES = $(APPS_HTML_FILES) $(APPS_JS_FILES) $(APPS_SASS_FILES) \
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/contextualdata.html \
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/background-layer-button.png \
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/favicon.ico \
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/logo.png \
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/logo.svg \
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/crosshair.svg

APPS_ALT += desktop_alt mobile_alt oeedit oeview
APPS_PACKAGE_PATH_ALT_NONDOCKER = geoportal/c2cgeoportal_geoportal/scaffolds/nondockerupdate/CONST_create_template/geoportal/+package+_geoportal
APPS_PACKAGE_PATH_ALT = geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/geoportal/+package+_geoportal
APPS_HTML_FILES_ALT = $(addprefix $(APPS_PACKAGE_PATH_ALT_NONDOCKER)/static-ngeo/js/apps/, $(addsuffix .html.ejs_tmpl, $(APPS_ALT)))
APPS_HTML_FILES_ALT += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/, $(addsuffix .html.ejs_tmpl, $(APPS_ALT)))
APPS_JS_FILES_ALT += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/Controller, $(addsuffix .js_tmpl, $(APPS_ALT)))
APPS_SASS_FILES_ALT += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/sass/, $(addsuffix .scss, $(APPS_ALT)))
APPS_SASS_FILES_ALT += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/sass/vars_, $(addsuffix .scss, $(APPS_ALT)))
APPS_FILES_ALT = $(APPS_HTML_FILES_ALT) $(APPS_JS_FILES_ALT) $(APPS_SASS_FILES_ALT)

API_FILES = $(APPS_PACKAGE_PATH)/static-ngeo/api/api.css $(APPS_PACKAGE_PATH)/static-ngeo/api/apihelp

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

.PHONY: docker-pull
docker-pull:
	for image in `find -name Dockerfile -o -name Dockerfile.mako | xargs grep --no-filename FROM | awk '{print $$2}' | sort -u`; do docker pull $$image; done
	docker pull camptocamp/qgis-server:3.16  # LTR

.PHONY: docker-build
docker-build: docker-pull
	docker build --tag=camptocamp/geomapfish-build-dev:${MAJOR_VERSION} docker/build
	./docker-run --env=RELEASE_TAG make build

.PHONY: build
build: \
	docker-build-build \
	docker-build-config \
	docker-build-qgisserver \
	prepare-tests

.PHONY: doc
doc: $(BUILD_DIR)/sphinx.timestamp

.PHONY: checks
checks: flake8 mypy git-attributes quote spell yamllint pylint eof-newline additionallint

.PHONY: clean
clean:
	rm --force $(BUILD_DIR)/venv.timestamp
	rm --force $(BUILD_DIR)/c2ctemplate-cache.json
	rm --force $(BUILD_DIR)/ngeo.timestamp
	rm --force geoportal/c2cgeoportal_geoportal/locale/*.pot
	rm --force geoportal/c2cgeoportal_admin/locale/*.pot
	rm --force geoportal/c2cgeoportal_geoportal/locale/en/LC_MESSAGES/c2cgeoportal_geoportal.po
	rm --force geoportal/c2cgeoportal_admin/locale/en/LC_MESSAGES/c2cgeoportal_admin.po
	rm --recursive --force geoportal/c2cgeoportal_geoportal/static/build
	rm --force $(MAKO_FILES:.mako=)
	rm --force $(API_FILES) $(APPS_FILES) $(APPS_FILES_ALT)
	rm --force geoportal/tests/functional/alembic.yaml
	rm --force docker/qgisserver/tests/geomapfish.yaml

.PHONY: clean-all
clean-all: clean
	rm --recursive --force geoportal/node_modules
	rm --force $(PO_FILES)
	rm --recursive --force $(BUILD_DIR)/*

$(BUILD_DIR)/sphinx.timestamp: $(SPHINX_FILES) $(SPHINX_MAKO_FILES:.mako=)
	$(PRERULE_CMD)
	mkdir --parent doc/_build/html
	doc/build.sh
	touch $@

geoportal/tests/functional/alembic.yaml: $(BUILD_DIR)/c2ctemplate-cache.json
	$(PRERULE_CMD)
	c2c-template --cache $(BUILD_DIR)/c2ctemplate-cache.json --get-config $@ srid schema schema_static sqlalchemy.url

docker/qgisserver/tests/geomapfish.yaml: $(BUILD_DIR)/c2ctemplate-cache.json
	$(PRERULE_CMD)
	c2c-template --cache $(BUILD_DIR)/c2ctemplate-cache.json --get-config $@ srid schema schema_static sqlalchemy_slave.url

docker-build-test: docker-build-testdb docker-build-testexternaldb docker-build-testmapserver

docker/test-db/12-alembic.sql: \
		geoportal/tests/functional/alembic.ini \
		geoportal/tests/functional/alembic.yaml \
		$(shell ls -1 commons/c2cgeoportal_commons/alembic/main/*.py)
	$(PRERULE_CMD)
	alembic --config=$< --name=main upgrade --sql head > $@

docker/test-db/13-alembic-static.sql: \
		geoportal/tests/functional/alembic.ini \
		geoportal/tests/functional/alembic.yaml \
		$(shell ls -1 commons/c2cgeoportal_commons/alembic/static/*.py)
	$(PRERULE_CMD)
	alembic --config=$< --name=static upgrade --sql head > $@

.PHONY: docker-build-gisdb
docker-build-gisdb: $(shell docker-required --path docker/gis-db)
	docker build --tag=$(DOCKER_TEST_BASE)-gis-db:latest docker/gis-db

.PHONY: docker-build-testdb
docker-build-testdb: docker/test-db/12-alembic.sql docker/test-db/13-alembic-static.sql \
		docker-build-gisdb
	docker build --tag=$(DOCKER_TEST_BASE)-db:latest docker/test-db

.PHONY: docker-build-testexternaldb
docker-build-testexternaldb: docker-build-gisdb
	docker build --tag=$(DOCKER_TEST_BASE)-external-db:latest docker/test-external-db

.PHONY: docker-build-testmapserver
docker-build-testmapserver: $(shell docker-required --path docker/test-mapserver)
	docker build --tag=$(DOCKER_TEST_BASE)-mapserver:latest docker/test-mapserver

.PHONY: docker-build-build
docker-build-build: $(shell docker-required --path . --replace-pattern='^test(.*).mako$/test/\1') \
		webpack.config.js \
		npm-packages admin/npm-packages \
		geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/ \
		geoportal/c2cgeoportal_geoportal/scaffolds/nondockerupdate/CONST_create_template/ \
		$(APPS_FILES_ALT) \
		$(MO_FILES)
	docker build --build-arg=VERSION=$(VERSION) --tag=$(DOCKER_BASE)-build:$(MAJOR_VERSION) .

.PHONY: docker-build-config
docker-build-config:
	docker build --tag=$(DOCKER_BASE)-config-build:$(MAJOR_VERSION) docker/config

docker/qgisserver/commons: commons
	rm --recursive --force $@
	cp --recursive $< $@
	rm --recursive --force $@/c2cgeoportal_commons/alembic
	rm $@/tests.yaml.mako
	touch $@

.PHONY: docker-build-qgisserver
docker-build-qgisserver: $(shell docker-required --path docker/qgisserver) docker/qgisserver/commons
	# LTR
	docker build --build-arg=VERSION=3.16 \
		--tag=$(DOCKER_BASE)-qgisserver:gmf$(MAJOR_VERSION)-qgis3.16 docker/qgisserver

.PHONY: prepare-tests
prepare-tests: \
		geoportal/tests/functional/test.ini \
		geoportal/tests/functional/alembic.ini \
		commons/tests.yaml \
		admin/tests.ini \
		docker/qgisserver/tests/geomapfish.yaml \
		docker-compose.yaml \
		docker-build-testmapserver \
		docker-build-testdb \
		$(addprefix geoportal/c2cgeoportal_geoportal/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal_geoportal.po, $(LANGUAGES))) \
		$(addprefix admin/c2cgeoportal_admin/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal_admin.po, $(LANGUAGES))) \
		docker/test-mapserver/mapserver.map

.PHONY: tests
tests:
	py.test --verbose --color=yes --cov=commons/c2cgeoportal_commons commons/tests
	py.test --verbose --color=yes --cov-append --cov=geoportal/c2cgeoportal_geoportal geoportal/tests
	py.test --verbose --color=yes --cov-append --cov=admin/c2cgeoportal_admin admin/tests

.PHONY: flake8
flake8:
	# E712 is not compatible with SQLAlchemy
	find $(VALIDATE_PY_FOLDERS) \
		-not \( -path "*/.build" -prune \) \
		-not \( -path "*/node_modules" -prune \) \
		-name \*.py | xargs flake8 \
		--ignore=W503 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"
	git grep --files-with-match '/usr/bin/env python' | grep -v Makefile | xargs flake8 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"
	find $(VALIDATE_TEMPLATE_PY_FOLDERS) -name \*.py | xargs flake8 --config=setup.cfg
	find $(VALIDATE_PY_TEST_FOLDERS) -name \*.py | xargs flake8 \
		--ignore=E501,W503 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"

.PHONY: pylint
pylint: $(BUILD_DIR)/commons.timestamp
	pylint --errors-only commons/c2cgeoportal_commons
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only commons/tests
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only --disable=assignment-from-no-return \
		geoportal/c2cgeoportal_geoportal
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only geoportal/tests
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only admin/c2cgeoportal_admin
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only admin/tests
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only --disable=import-error \
		docker/qgisserver/geomapfish_qgisserver
	$(BUILD_DIR)/venv/bin/python /usr/local/bin/pylint --errors-only --disable=import-error \
		docker/qgisserver/tests/functional

.PHONY: mypy
mypy:
	MYPYPATH=/opt/c2cwsgiutils \
		mypy --ignore-missing-imports --disallow-untyped-defs --strict-optional --follow-imports skip \
			commons/c2cgeoportal_commons
	# TODO: add --disallow-untyped-defs
	mypy --ignore-missing-imports --strict-optional --follow-imports skip \
		geoportal/c2cgeoportal_geoportal \
		admin/c2cgeoportal_admin \
		docker/qgisserver/geomapfish_qgisserver

.PHONY: git-attributes
git-attributes:
	git --no-pager diff --check a6eacf93706d94606fb3c68a671f8254aea48e3b

.PHONY: quote
quote:
	travis/squote geoportal/setup.py \
		`find commons/c2cgeoportal_commons -name '*.py'` \
		`find admin/c2cgeoportal_admin -name '*.py'` \

.PHONY: spell
spell:
	codespell --quiet-level=2 --check-filenames --ignore-words=spell-ignore-words.txt \
		$(shell find \
		-name node_modules -prune -or \
		-name ngeo -prune -or \
		-name .build -prune -or \
		-name .git -prune -or \
		-name .venv -prune -or \
		-name .mypy_cache -prune -or \
		-name '__pycache__' -prune -or \
		-name _build -prune -or \
		\( -type f \
		-and -not -name '*.png' \
		-and -not -name '*.mo' \
		-and -not -name '*.po*' \
		-and -not -name 'CONST_Makefile_tmpl' \
		-and -not -name 'package-lock.json' \
		-and -not -name 'changelog.yaml' \
		-and -not -name 'CHANGELOG.md' \) -print)


YAML_FILES ?= $(shell find \
	-name node_modules -prune -or \
	-name .git -prune -or \
	-name .venv -prune -or \
	-name .mypy_cache -prune -or \
	-name functional -prune -or \
	-name geomapfish.yaml -prune -or \
	-name changelog.yaml -prune -or \
	\( -name "*.yml" -or -name "*.yaml" \) -print)
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

# Import ngeo templates

.PHONY: import-ngeo-apps
import-ngeo-apps: $(API_FILES) $(APPS_FILES) $(APPS_FILES_ALT)

.PRECIOUS: $(BUILD_DIR)/ngeo.timestamp
$(BUILD_DIR)/ngeo.timestamp: geoportal/package.json
	$(PRERULE_CMD)
	(cd geoportal; npm install)
	touch $@

.PRECIOUS: ngeo/contribs/gmf/apps/%/index.html.ejs
geoportal/node_modules/ngeo/contribs/gmf/apps/%/index.html.ejs: $(BUILD_DIR)/ngeo.timestamp
	$(PRERULE_CMD)
	touch --no-create $@

.PRECIOUS: ngeo/contribs/gmf/apps/%/Controller.js
geoportal/node_modules/ngeo/contribs/gmf/apps/%/Controller.js: $(BUILD_DIR)/ngeo.timestamp
	$(PRERULE_CMD)
	touch --no-create $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/%.html.ejs_tmpl: geoportal/node_modules/ngeo/contribs/gmf/apps/%/index.html.ejs
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	import-ngeo-apps --html $* $< $@

$(APPS_PACKAGE_PATH_NONDOCKER)/static-ngeo/js/apps/%.html.ejs_tmpl: geoportal/node_modules/ngeo/contribs/gmf/apps/%/index.html.ejs
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	import-ngeo-apps --html --non-docker $* $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/Controller%.js_tmpl: geoportal/node_modules/ngeo/contribs/gmf/apps/%/Controller.js
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	import-ngeo-apps --js $* $< $@

$(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/%.html.ejs_tmpl: \
		geoportal/node_modules/ngeo/contribs/gmf/apps/%/index.html.ejs \
		geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	import-ngeo-apps --html $* $< $@

$(APPS_PACKAGE_PATH_ALT_NONDOCKER)/static-ngeo/js/apps/%.html.ejs_tmpl: \
		geoportal/node_modules/ngeo/contribs/gmf/apps/%/index.html.ejs \
		geoportal/c2cgeoportal_geoportal/scaffolds/nondockerupdate/CONST_create_template/
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	import-ngeo-apps --html --non-docker $* $< $@

$(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/Controller%.js_tmpl: \
		geoportal/node_modules/ngeo/contribs/gmf/apps/%/Controller.js \
		geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	import-ngeo-apps --js $* $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/sass/%.scss: $(BUILD_DIR)/ngeo.timestamp
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp geoportal/node_modules/ngeo/contribs/gmf/apps/$*/sass/$*.scss $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/sass/vars_%.scss: $(BUILD_DIR)/ngeo.timestamp
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp geoportal/node_modules/ngeo/contribs/gmf/apps/$*/sass/vars_$*.scss $@

$(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/sass/%.scss: $(BUILD_DIR)/ngeo.timestamp \
		geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp geoportal/node_modules/ngeo/contribs/gmf/apps/$*/sass/$*.scss $@

$(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/sass/vars_%.scss: $(BUILD_DIR)/ngeo.timestamp \
		geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp geoportal/node_modules/ngeo/contribs/gmf/apps/$*/sass/vars_$*.scss $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/contextualdata.html: geoportal/node_modules/ngeo/contribs/gmf/apps/desktop/contextualdata.html
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp $< $@

.PRECIOUS: geoportal/node_modules/ngeo/contribs/gmf/apps/desktop/image/%
geoportal/node_modules/ngeo/contribs/gmf/apps/desktop/image/%: $(BUILD_DIR)/ngeo.timestamp
	$(PRERULE_CMD)
	touch --no-create $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/%: geoportal/node_modules/ngeo/contribs/gmf/apps/desktop/image/%
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp $< $@ || cp geoportal/node_modules/ngeo/contribs/gmf/apps/desktop_alt/image/$* $@

$(APPS_PACKAGE_PATH)/static-ngeo/api/api.css: geoportal/node_modules/ngeo/api/src/api.css
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/api/apihelp: geoportal/node_modules/ngeo/api/dist/apihelp
	$(PRERULE_CMD)
	rm --recursive --force $@
	cp -r $< $@
	mv $@/apihelp.html $@/index.html.tmpl_tmpl
	sed -i -e 's#https://geomapfish-demo-2-4.camptocamp.com/#$${VISIBLE_WEB_PROTOCOL}://$${VISIBLE_WEB_HOST}$${VISIBLE_ENTRY_POINT}#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#var map = new demo.Map#var map = new {{package}}.Map#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#\.\./api\.js#../api.js?version=2#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#github\.css#../static-ngeo/api/apihelp/github.css#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#rainbow-custom\.min\.js#../static-ngeo/api/apihelp/rainbow-custom.min.js#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#"data\.txt"#"../static-ngeo/api/apihelp/data.txt"#g' $@/index.html.tmpl_tmpl
	sed -i -e "s#'data\.txt'#'../static-ngeo/api/apihelp/data.txt'#g" $@/index.html.tmpl_tmpl
	sed -i -e 's#img/#../static-ngeo/api/apihelp/img/#g' $@/index.html.tmpl_tmpl


geoportal/c2cgeoportal_geoportal/scaffolds/create/docker-run: docker-run
	$(PRERULE_CMD)
	cp $< $@

npm-packages: $(BUILD_DIR)/ngeo.timestamp
	$(PRERULE_CMD)
	npm-packages \
		@camptocamp/cesium @type jasmine-core karma karma-chrome-launcher karma-coverage \
		karma-coverage-istanbul-reporter karma-jasmine karma-sourcemap-loader karma-webpack \
		typedoc typescript \
		--src=geoportal/node_modules/ngeo/package.json --src=geoportal/package.json --dst=$@

admin/npm-packages: admin/package.json
	$(PRERULE_CMD)
	npm-packages --src=admin/package.json --dst=$@

.PRECIOUS: geoportal/c2cgeoportal_geoportal/scaffolds%update/CONST_create_template/
geoportal/c2cgeoportal_geoportal/scaffolds%update/CONST_create_template/: \
		geoportal/c2cgeoportal_geoportal/scaffolds%create/ \
		$(addprefix geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/,$(addsuffix /LC_MESSAGES/+package+_geoportal-client.po, $(ALL_LANGUAGES))) \
		geoportal/c2cgeoportal_geoportal/scaffolds/create/docker-run \
		$(API_FILES) \
		$(APPS_FILES) \
		$(L10N_PO_FILES) \
		geoportal/c2cgeoportal_geoportal/scaffolds/create/front_dev/localhost.pem \
		geoportal/c2cgeoportal_geoportal/scaffolds/create/front_dev/haproxy.cfg.tmpl
	$(PRERULE_CMD)
	rm -rf $@ || true
	cp -r $< $@

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

# HA proxy on localhost on https

geoportal/c2cgeoportal_geoportal/scaffolds/create/front_dev/localhost.pem: $(BUILD_DIR)/ngeo.timestamp
	$(PRERULE_CMD)
	mkdir -p $(dir $@)
	cat geoportal/node_modules/ngeo/private.crt geoportal/node_modules/ngeo/private.key | tee $@

geoportal/c2cgeoportal_geoportal/scaffolds/create/front_dev/haproxy.cfg.tmpl: \
		geoportal/c2cgeoportal_geoportal/scaffolds/create/front/haproxy.cfg.tmpl
	$(PRERULE_CMD)
	mkdir -p $(dir $@)
	sed 's#bind :80#bind *:443 ssl crt /etc/haproxy_dev/localhost.pem#g' $< > $@
	echo '    http-request set-header X-Forwarded-Proto https' >> $@
