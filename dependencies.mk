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
