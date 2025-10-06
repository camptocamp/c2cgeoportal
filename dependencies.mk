TX_DEPENDENCIES = $(HOME)/.transifexrc .tx/config

# rm is Romansh
LANGUAGES = fr de it rm
export LANGUAGES
ALL_LANGUAGES = en $(LANGUAGES)

GEOPORTAL_PO_FILES = $(addprefix geoportal/c2cgeoportal_geoportal/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal_geoportal.po, $(LANGUAGES)))
NGEO_PO_FILES = $(addprefix geoportal/c2cgeoportal_geoportal/locale/,$(addsuffix /LC_MESSAGES/ngeo.po, $(LANGUAGES)))
ADMIN_PO_FILES = $(addprefix admin/c2cgeoportal_admin/locale/,$(addsuffix /LC_MESSAGES/c2cgeoportal_admin.po, $(LANGUAGES)))
APPLICATION_PO_FILES = $(addprefix geoportal/c2cgeoportal_geoportal/scaffolds/create/{{cookiecutter.project}}/geoportal/{{cookiecutter.package}}_geoportal/locale/,$(addsuffix /LC_MESSAGES/{{cookiecutter.package}}_geoportal-client.po, $(ALL_LANGUAGES)))
WEBCOMPONENTS_L10N_FILES = $(addprefix geoportal/c2cgeoportal_geoportal/static/locales/,$(addsuffix .json, $(ALL_LANGUAGES)))
PYTHON_PO_FILES = $(GEOPORTAL_PO_FILES) $(ADMIN_PO_FILES)
JAVASCRIPT_PO_FILES = $(NGEO_PO_FILES) $(APPLICATION_PO_FILES)
TRANSIFEX_PO_FILES = $(PYTHON_PO_FILES) $(JAVASCRIPT_PO_FILES) ${WEBCOMPONENTS_L10N_FILES}

.PHONY: dependencies
dependencies: $(TRANSIFEX_PO_FILES)

# Templates

/tmp/c2ctemplate-cache.json: vars.yaml
	c2c-template --vars $< --get-cache $@

%: %.mako /tmp/c2ctemplate-cache.json
	c2c-template --cache /tmp/c2ctemplate-cache.json --engine mako --files $<

# i18n
$(HOME)/.transifexrc:
	mkdir --parent $(dir $@)
	echo "[https://www.transifex.com]" > $@
	echo "api_hostname  = https://api.transifex.com" >> $@
	echo "rest_hostname = https://rest.api.transifex.com" >> $@
	echo "hostname = https://www.transifex.com" >> $@
	echo "token = 1/dc02578696187cc29e4e6486f8611fdbfe60b235" >> $@

.PHONY: transifex-send
transifex-send: $(TX_DEPENDENCIES) \
		geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot \
		admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot
	tx push --branch=$(MAJOR_VERSION) --source --resources=geomapfish.c2cgeoportal_geoportal
	tx push --branch=$(MAJOR_VERSION) --source --resources=geomapfish.c2cgeoportal_admin

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
	tx pull --translations --branch=$(MAJOR_VERSION) --languages=$* --resources=geomapfish.c2cgeoportal_geoportal --force
	sed -i 's/[[:space:]]\+$$//' $@
	test -s $@

.PRECIOUS: geoportal/c2cgeoportal_geoportal/locale/%/LC_MESSAGES/ngeo.po
geoportal/c2cgeoportal_geoportal/locale/%/LC_MESSAGES/ngeo.po: $(TX_DEPENDENCIES)
	mkdir --parent $(dir $@)
	tx pull --translations --branch=$(MAJOR_VERSION) --languages=$* --resources=ngeo.ngeo --force
	sed -i 's/[[:space:]]\+$$//' $@
	test -s $@

admin/c2cgeoportal_admin/locale/%/LC_MESSAGES/c2cgeoportal_admin.po: $(TX_DEPENDENCIES)
	mkdir --parent $(dir $@)
	tx pull --translations --branch=$(MAJOR_VERSION) --languages=$* --resources=geomapfish.c2cgeoportal_admin --force
	sed -i 's/[[:space:]]\+$$//' $@
	test -s $@

.PRECIOUS: geoportal/c2cgeoportal_geoportal/scaffolds/create/{{cookiecutter.project}}/geoportal/{{cookiecutter.package}}_geoportal/locale/%/LC_MESSAGES/{{cookiecutter.package}}_geoportal-client.po
geoportal/c2cgeoportal_geoportal/scaffolds/create/{{cookiecutter.project}}/geoportal/{{cookiecutter.package}}_geoportal/locale/%/LC_MESSAGES/{{cookiecutter.package}}_geoportal-client.po: \
		$(TX_DEPENDENCIES)
	mkdir --parent $(dir $@)
	tx pull --translations --branch=$(MAJOR_VERSION) --languages=$* --resources=ngeo.gmf-apps --force
	sed -i 's/[[:space:]]\+$$//' $@
	test -s $@

.PRECIOUS: geoportal/c2cgeoportal_geoportal/static/locales/%.json
geoportal/c2cgeoportal_geoportal/static/locales/%.json: $(TX_DEPENDENCIES)
	mkdir --parent $(dir $@)
	tx pull --translations --branch=$(MAJOR_VERSION) --languages=$* --resources=ngeo.webcomponent --force
	touch $@

geoportal/c2cgeoportal_geoportal/scaffolds/create/{{cookiecutter.project}}/geoportal/{{cookiecutter.package}}_geoportal/locale/en/LC_MESSAGES/{{cookiecutter.package}}_geoportal-client.po:
	@echo "Nothing to be done for $@"
