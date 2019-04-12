# Convert to tmpl

TEMPLATE_EXCLUDE += node_modules CONST_create_template \
	geoportal/$(PACKAGE)_geoportal/static/lib
FIND_OPTS = $(foreach ELEM, $(TEMPLATE_EXCLUDE),-path ./$(ELEM) -prune -o) -type f
ALL_TMPL_MAKO_FILES = $(shell find $(FIND_OPTS) -name "*.tmpl.mako" -print)

.PHONY: to-tmpl
to-tmpl: $(ALL_TMPL_MAKO_FILES:.mako=)

%.tmpl: %.tmpl.mako
	sed -e 's#/\$${instanceid}/#${entry_point}#g' -i $<
	c2c-template --vars vars_convert2tmpl.yaml --engine mako \
		--runtime-environment-pattern '$${{{}}}' --files $<
	rm $<
