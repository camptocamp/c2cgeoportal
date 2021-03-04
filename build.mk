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
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/logo.png \
	$(APPS_PACKAGE_PATH)/static-ngeo/js/apps/image/logo.svg \
	$(APPS_PACKAGE_PATH)/static/images/favicon.ico

APPS_ALT += desktop_alt mobile_alt oeedit
APPS_PACKAGE_PATH_ALT = geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/geoportal/+package+_geoportal
APPS_HTML_FILES_ALT = $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/, $(addsuffix .html.ejs_tmpl, $(APPS_ALT)))
APPS_JS_FILES_ALT += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/Controller, $(addsuffix .js_tmpl, $(APPS_ALT)))
APPS_SASS_FILES_ALT += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/sass/, $(addsuffix .scss, $(APPS_ALT)))
APPS_SASS_FILES_ALT += $(addprefix $(APPS_PACKAGE_PATH_ALT)/static-ngeo/js/apps/sass/vars_, $(addsuffix .scss, $(APPS_ALT)))
APPS_FILES_ALT = $(APPS_HTML_FILES_ALT) $(APPS_JS_FILES_ALT) $(APPS_SASS_FILES_ALT)

API_FILES = $(APPS_PACKAGE_PATH)/static-ngeo/api/api.css $(APPS_PACKAGE_PATH)/static/apihelp

include dependencies.mk

.PHONY: dependencies-touch
dependencies-touch:
	touch $(TRANSIFEX_PO_FILES)

.PHONY: build
build: \
	geoportal/c2cgeoportal_geoportal/scaffolds/update/CONST_create_template/ \
	$(APPS_FILES_ALT) \
	$(MO_FILES)

# Import ngeo templates

.PHONY: import-ngeo-apps
import-ngeo-apps: $(API_FILES) $(APPS_FILES) $(APPS_FILES_ALT) $(APPS_PACKAGE_PATH)/static/header.html

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

$(APPS_PACKAGE_PATH)/static/header.html:  /usr/lib/node_modules/ngeo/contribs/gmf/apps/desktop/header.html
	mkdir --parent $(dir $@)
	cp $< $@

$(APPS_PACKAGE_PATH)/static/images/%: /usr/lib/node_modules/ngeo/contribs/gmf/apps/desktop/image/%
	$(PRERULE_CMD)
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
	sed -i -e 's#https://geomapfish-demo-2-[0-9].camptocamp.com/#$${VISIBLE_WEB_PROTOCOL}://$${VISIBLE_WEB_HOST}$${VISIBLE_ENTRY_POINT}#g' $@/index.html.tmpl_tmpl
	sed -i -e 's# = new demo.Map# = new {{package}}.Map#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#\.\./api\.js#../api.js?version=2#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#github\.css#../static/$${CACHE_VERSION}/apihelp/github.css#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#rainbow-custom\.min\.js#../static/$${CACHE_VERSION}/apihelp/rainbow-custom.min.js#g' $@/index.html.tmpl_tmpl
	sed -i -e 's#"data\.txt"#"../static/$${CACHE_VERSION}/apihelp/data.txt"#g' $@/index.html.tmpl_tmpl
	sed -i -e "s#'data\.txt'#'../static/\$${CACHE_VERSION}/apihelp/data.txt'#g" $@/index.html.tmpl_tmpl
	sed -i -e 's#img/#../static/$${CACHE_VERSION}/apihelp/img/#g' $@/index.html.tmpl_tmpl

.PRECIOUS: geoportal/c2cgeoportal_geoportal/scaffolds%update/CONST_create_template/
geoportal/c2cgeoportal_geoportal/scaffolds%update/CONST_create_template/: \
		geoportal/c2cgeoportal_geoportal/scaffolds%create/ \
		$(addprefix geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/,$(addsuffix /LC_MESSAGES/+package+_geoportal-client.po, $(ALL_LANGUAGES))) \
		$(API_FILES) \
		$(APPS_FILES) \
		$(APPS_PACKAGE_PATH)/static/header.html
	rm -rf $@ || true
	cp -r $< $@

geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot: \
		lingua.cfg $(SRC_FILES)
	mkdir --parent $(dir $@)
	pot-create --config $< --keyword _ --output $@ $(SRC_FILES)

admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot: \
		lingua.cfg $(ADMIN_SRC_FILES)
	mkdir --parent $(dir $@)
	pot-create --config $< --keyword _ --output $@ $(ADMIN_SRC_FILES)

.PRECIOUS: %.mo
%.mo: %.po
	mkdir --parent $(dir $@)
	msgfmt -o $*.mo $<
