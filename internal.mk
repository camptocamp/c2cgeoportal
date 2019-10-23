VALIDATE_PY_FOLDERS = commons admin \
	geoportal/setup.py \
	geoportal/c2cgeoportal_geoportal/*.py \
	geoportal/c2cgeoportal_geoportal/lib \
	geoportal/c2cgeoportal_geoportal/scripts \
	geoportal/c2cgeoportal_geoportal/views
VALIDATE_TEMPLATE_PY_FOLDERS = geoportal/c2cgeoportal_geoportal/scaffolds
VALIDATE_PY_TEST_FOLDERS = geoportal/tests

export TX_VERSION = $(shell echo $(MAJOR_VERSION) | awk -F . '{{print $$1"_"$$2}}')
TX_DEPENDENCIES = $(HOME)/.transifexrc .tx/config
LANGUAGES = fr de it
export LANGUAGES
ALL_LANGUAGES = en $(LANGUAGES)
GEOPORTAL_PO_FILES = $(addprefix geoportal/c2cgeoportal_geoportal/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal_geoportal.po, $(LANGUAGES)))
NGEO_PO_FILES = $(addprefix geoportal/c2cgeoportal_geoportal/locale/,$(addsuffix /LC_MESSAGES/ngeo.po, $(LANGUAGES)))
GMF_PO_FILES = $(addprefix geoportal/c2cgeoportal_geoportal/locale/,$(addsuffix /LC_MESSAGES/gmf.po, $(LANGUAGES)))
ADMIN_PO_FILES = $(addprefix admin/c2cgeoportal_admin/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal_admin.po, $(LANGUAGES)))
APPLICATION_PO_FILES = $(addprefix geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/,$(addsuffix /LC_MESSAGES/+package+_geoportal-client.po, $(ALL_LANGUAGES)))
PYTHON_PO_FILES = $(GEOPORTAL_PO_FILES) $(ADMIN_PO_FILES)
JAVASCRIPT_PO_FILES = $(NGEO_PO_FILES) $(GMF_PO_FILES) $(APPLICATION_PO_FILES)
TRANSIFEX_PO_FILES = $(PYTHON_PO_FILES) $(JAVASCRIPT_PO_FILES)
L10N_PO_FILES = $(JAVASCRIPT_PO_FILES) \
	geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot \
	admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot
MO_FILES = $(addsuffix .mo,$(basename $(PYTHON_PO_FILES)))
SRC_FILES = $(shell ls -1 geoportal/c2cgeoportal_geoportal/*.py 2> /dev/null) \
	$(shell find geoportal/c2cgeoportal_geoportal/lib -name "*.py" -print 2> /dev/null) \
	$(shell find geoportal/c2cgeoportal_geoportal/views -name "*.py" -print 2> /dev/null) \
	$(filter-out geoportal/c2cgeoportal_geoportal/scripts/theme2fts.py, $(shell find geoportal/c2cgeoportal_geoportal/scripts -name "*.py" -print 2> /dev/null))
ADMIN_SRC_FILES = $(shell ls -1 commons/c2cgeoportal_commons/models/*.py 2> /dev/null) \
	$(shell find admin/c2cgeoportal_admin -name "*.py" -print 2> /dev/null) \
	$(shell find admin/c2cgeoportal_admin/templates -name "*.jinja2" -print 2> /dev/null) \
	$(shell find admin/c2cgeoportal_admin/templates/widgets -name "*.pt" -print 2> /dev/null)

APPS += desktop mobile iframe_api
APPS_PACKAGE_PATH = geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal
APPS_HTML_FILES = $(addprefix $(APPS_PACKAGE_PATH)/static-ngeo/js/apps/, $(addsuffix .html.ejs_tmpl, $(APPS)))
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

APPS_ALT += desktop_alt mobile_alt oeedit
APPS_PACKAGE_PATH_ALT = geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/geoportal/+package+_geoportal
APPS_HTML_FILES_ALT = $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/, $(addsuffix .html.ejs_tmpl, $(APPS_ALT)))
APPS_JS_FILES_ALT += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/Controller, $(addsuffix .js_tmpl, $(APPS_ALT)))
APPS_SASS_FILES_ALT += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/sass/, $(addsuffix .scss, $(APPS_ALT)))
APPS_SASS_FILES_ALT += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/sass/vars_, $(addsuffix .scss, $(APPS_ALT)))
APPS_FILES_ALT = $(APPS_HTML_FILES_ALT) $(APPS_JS_FILES_ALT) $(APPS_SASS_FILES_ALT)

API_FILES = $(APPS_PACKAGE_PATH)/static-ngeo/api/api.css $(APPS_PACKAGE_PATH)/static/apihelp

.PHONY: dependencies
dependencies: $(TRANSIFEX_PO_FILES)

.PHONY: dependencies-touch
dependencies-touch:
	touch $(TRANSIFEX_PO_FILES)

.PHONY: build
build: \
	geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/ \
	$(APPS_FILES_ALT) \
	$(MO_FILES)

.PHONY: checks
checks: flake8 mypy pylint bandit black additionallint

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
	grep --recursive --files-with-match '/usr/bin/env python' | grep -v internal.mk | grep -v node_modules \
		| xargs flake8 \
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
pylint:
	pylint --errors-only commons/c2cgeoportal_commons
	pylint --errors-only commons/tests
	pylint --errors-only --disable=assignment-from-no-return geoportal/c2cgeoportal_geoportal
	pylint --errors-only geoportal/tests
	pylint --errors-only admin/c2cgeoportal_admin
	pylint --errors-only admin/tests

.PHONY: mypy
mypy:
	MYPYPATH=/opt/c2cwsgiutils \
		mypy --ignore-missing-imports --disallow-untyped-defs --strict-optional --follow-imports skip \
			commons/c2cgeoportal_commons
	# TODO: add --disallow-untyped-defs
	mypy --ignore-missing-imports --strict-optional --follow-imports skip \
		geoportal/c2cgeoportal_geoportal \
		admin/c2cgeoportal_admin

.PHONY: bandit
bandit:
	bandit --recursive -ll .

.PHONY: black
black:
	black --line-length=110 --target-version py37 --exclude=.*/node_modules/.* --check --diff .

.PHONY: black-fix
black-fix:
	black --line-length=110 --target-version py37 --exclude=.*/node_modules/.* /src

.PHONY: additionallint
additionallint:
	# Verify that we don't directly use the CI project name in the scaffolds
	if [ "`grep --recursive testgeomapfish geoportal/c2cgeoportal_geoportal/scaffolds`" != "" ]; \
	then \
		echo "ERROR: You still have a testgeomapfish in one of your scaffolds"; \
		grep --recursive testgeomapfish geoportal/c2cgeoportal_geoportal/scaffolds; \
		false; \
	fi

# i18n
$(HOME)/.transifexrc:
	mkdir --parent $(dir $@)
	echo "[https://www.transifex.com]" > $@
	echo "hostname = https://www.transifex.com" >> $@
	echo "username = c2c" >> $@
	echo "password = c2cc2c" >> $@
	echo "token =" >> $@

.PHONY: transifex-send
transifex-send: $(TX_DEPENDENCIES) \
		geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot \
		admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot
	tx push --source --resource=geomapfish.c2cgeoportal_geoportal-$(TX_VERSION)
	tx push --source --resource=geomapfish.c2cgeoportal_admin-$(TX_VERSION)

.PHONY: transifex-init
transifex-init: $(TX_DEPENDENCIES) \
		geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot \
		admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot
	tx push --source --force --no-interactive --resource=geomapfish.c2cgeoportal_geoportal-$(TX_VERSION)
	tx push --source --force --no-interactive --resource=geomapfish.c2cgeoportal_admin-$(TX_VERSION)
	tx push --translations --force --no-interactive --resource=geomapfish.c2cgeoportal_geoportal-$(TX_VERSION)
	tx push --translations --force --no-interactive --resource=geomapfish.c2cgeoportal_admin-$(TX_VERSION)

# Import ngeo templates

.PHONY: import-ngeo-apps
import-ngeo-apps: $(API_FILES) $(APPS_FILES) $(APPS_FILES_ALT)

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/%.html.ejs_tmpl: /usr/lib/node_modules/ngeo/contribs/gmf/apps/%/index.html.ejs
	mkdir --parent $(dir $@)
	import-ngeo-apps --html $* $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/Controller%.js_tmpl: /usr/lib/node_modules/ngeo/contribs/gmf/apps/%/Controller.js
	mkdir --parent $(dir $@)
	import-ngeo-apps --js $* $< $@

$(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/%.html.ejs_tmpl: \
		/usr/lib/node_modules/ngeo/contribs/gmf/apps/%/index.html.ejs \
		geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/
	mkdir --parent $(dir $@)
	import-ngeo-apps --html $* $< $@

$(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/Controller%.js_tmpl: \
		/usr/lib/node_modules/ngeo/contribs/gmf/apps/%/Controller.js \
		geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/
	mkdir --parent $(dir $@)
	import-ngeo-apps --js $* $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/sass/%.scss:
	mkdir --parent $(dir $@)
	cp /usr/lib/node_modules/ngeo/contribs/gmf/apps/$*/sass/$*.scss $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/sass/vars_%.scss:
	mkdir --parent $(dir $@)
	cp /usr/lib/node_modules/ngeo/contribs/gmf/apps/$*/sass/vars_$*.scss $@

$(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/sass/%.scss: \
		geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/
	mkdir --parent $(dir $@)
	cp /usr/lib/node_modules/ngeo/contribs/gmf/apps/$*/sass/$*.scss $@

$(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/sass/vars_%.scss: \
		geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/
	mkdir --parent $(dir $@)
	cp /usr/lib/node_modules/ngeo/contribs/gmf/apps/$*/sass/vars_$*.scss $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/contextualdata.html: /usr/lib/node_modules/ngeo/contribs/gmf/apps/desktop/contextualdata.html
	mkdir --parent $(dir $@)
	cp $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/%: /usr/lib/node_modules/ngeo/contribs/gmf/apps/desktop/image/%
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/%: /usr/lib/node_modules/ngeo/contribs/gmf/apps/desktop_alt/image/%
	$(PRERULE_CMD)
	mkdir --parent $(dir $@)
	cp $< $@

$(APPS_PACKAGE_PATH)/static-ngeo/api/api.css: /usr/lib/node_modules/ngeo/api/src/api.css
	mkdir --parent $(dir $@)
	cp $< $@

$(APPS_PACKAGE_PATH)/static/apihelp: /usr/lib/node_modules/ngeo/api/dist/apihelp
	rm --recursive --force $@
	cp -r $< $@
	mv $@/apihelp.html $@/index.html.tmpl_tmpl
	sed -i -e 's#https://geomapfish-demo-2-4.camptocamp.com/#$${VISIBLE_WEB_PROTOCOL}://$${VISIBLE_WEB_HOST}$${VISIBLE_ENTRY_POINT}#g' $@/index.html.tmpl_tmpl
	sed -i -e 's# = new demo.Map# = new {{package}}.Map#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#\.\./api\.js#../api.js?version=2#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#github\.css#../static/{CACHE_VERSION}/apihelp/github.css#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#rainbow-custom\.min\.js#../static/{CACHE_VERSION}/apihelp/rainbow-custom.min.js#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#"data\.txt"#"../static/{CACHE_VERSION}/apihelp/data.txt"#g' $@/index.html.tmpl_tmpl
	sed -i -e "s#'data\.txt'#'../static/{CACHE_VERSION}/apihelp/data.txt'#g" $@/index.html.tmpl_tmpl
	sed -i -e 's#img/#../static/{CACHE_VERSION}/apihelp/img/#g' $@/index.html.tmpl_tmpl

.PRECIOUS: geoportal/c2cgeoportal_geoportal/scaffolds%update/CONST_create_template/
geoportal/c2cgeoportal_geoportal/scaffolds%update/CONST_create_template/: \
		geoportal/c2cgeoportal_geoportal/scaffolds%create/ \
		$(addprefix geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/,$(addsuffix /LC_MESSAGES/+package+_geoportal-client.po, $(ALL_LANGUAGES))) \
		$(API_FILES) \
		$(APPS_FILES) \
		$(L10N_PO_FILES) \
		geoportal/c2cgeoportal_geoportal/scaffolds/create/front_dev/localhost.pem \
		geoportal/c2cgeoportal_geoportal/scaffolds/create/front_dev/haproxy.cfg.tmpl
	rm -rf $@ || true
	cp -r $< $@

# Templates

/tmp/c2ctemplate-cache.json: vars.yaml
	c2c-template --vars $< --get-cache $@

%: %.mako /tmp/c2ctemplate-cache.json
	c2c-template --cache /tmp/c2ctemplate-cache.json --engine mako --files $<

geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot: \
		lingua.cfg $(SRC_FILES)
	mkdir --parent $(dir $@)
	pot-create --config $< --keyword _ --output $@ $(SRC_FILES)

admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot: \
		lingua.cfg $(ADMIN_SRC_FILES)
	mkdir --parent $(dir $@)
	pot-create --config $< --keyword _ --output $@ $(ADMIN_SRC_FILES)

geoportal/c2cgeoportal_geoportal/locale/en/LC_MESSAGES/c2cgeoportal_geoportal.po: geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot
	mkdir --parent $(dir $@)
	touch $@
	msgmerge --update $@ $<

admin/c2cgeoportal_admin/locale/en/LC_MESSAGES/c2cgeoportal_admin.po: admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot
	mkdir --parent $(dir $@)
	touch $@
	msgmerge --update $@ $<

geoportal/c2cgeoportal_geoportal/locale/%/LC_MESSAGES/c2cgeoportal_geoportal.po: $(TX_DEPENDENCIES)
	mkdir --parent $(dir $@)
	tx pull --language $* --resource geomapfish.c2cgeoportal_geoportal-$(TX_VERSION) --force
	sed -i 's/[[:space:]]\+$$//' $@
	test -s $@

.PRECIOUS: geoportal/c2cgeoportal_geoportal/locale/%/LC_MESSAGES/ngeo.po
geoportal/c2cgeoportal_geoportal/locale/%/LC_MESSAGES/ngeo.po: $(TX_DEPENDENCIES)
	mkdir --parent $(dir $@)
	tx pull --language $* --resource ngeo.ngeo-$(TX_VERSION) --force
	sed -i 's/[[:space:]]\+$$//' $@
	test -s $@

.PRECIOUS: geoportal/c2cgeoportal_geoportal/locale/%/LC_MESSAGES/gmf.po
geoportal/c2cgeoportal_geoportal/locale/%/LC_MESSAGES/gmf.po: $(TX_DEPENDENCIES)
	mkdir --parent $(dir $@)
	tx pull --language $* --resource ngeo.gmf-$(TX_VERSION) --force
	sed -i 's/[[:space:]]\+$$//' $@
	test -s $@

admin/c2cgeoportal_admin/locale/%/LC_MESSAGES/c2cgeoportal_admin.po: $(TX_DEPENDENCIES)
	mkdir --parent $(dir $@)
	tx pull --language $* --resource geomapfish.c2cgeoportal_admin-$(TX_VERSION) --force
	sed -i 's/[[:space:]]\+$$//' $@
	test -s $@

.PRECIOUS: geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/%/LC_MESSAGES/+package+_geoportal-client.po
geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/%/LC_MESSAGES/+package+_geoportal-client.po: \
		$(TX_DEPENDENCIES)
	mkdir --parent $(dir $@)
	tx pull --language $* --resource ngeo.gmf-apps-$(TX_VERSION) --force
	sed -i 's/[[:space:]]\+$$//' $@
	test -s $@

geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/en/LC_MESSAGES/+package+_geoportal-client.po:
	@echo "Nothing to be done for $@"

.PRECIOUS: %.mo
%.mo: %.po
	mkdir --parent $(dir $@)
	msgfmt -o $*.mo $<

# HA proxy on localhost on https

geoportal/c2cgeoportal_geoportal/scaffolds/create/front_dev/localhost.pem:
	mkdir -p $(dir $@)
	cat /usr/lib/node_modules/ngeo/private.crt /usr/lib/node_modules/ngeo/private.key | tee $@

geoportal/c2cgeoportal_geoportal/scaffolds/create/front_dev/haproxy.cfg.tmpl: \
		geoportal/c2cgeoportal_geoportal/scaffolds/create/front/haproxy.cfg.tmpl
	mkdir -p $(dir $@)
	sed 's#bind :80#bind *:443 ssl crt /etc/haproxy_dev/localhost.pem#g' $< > $@
	echo '    http-request set-header X-Forwarded-Proto https' >> $@
