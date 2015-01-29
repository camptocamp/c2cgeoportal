TEMPLATE_EXCLUDE = MANIFEST.in .build .eggs c2cgeoportal/scaffolds c2cgeoportal/tests/testegg c2cgeoportal/templates
FIND_OPTS = $(foreach ELEM, $(TEMPLATE_EXCLUDE),-path ./$(ELEM) -prune -o) -type f
MAKO_FILES = $(shell find $(FIND_OPTS) -name "*.mako" -print)
VARS_FILE ?= vars.yaml
VARS_FILES += vars.yaml
C2C_TEMPLATE_CMD = .build/venv/bin/c2c-template --vars $(VARS_FILE)

DEVELOPPEMENT ?= FALSE

ADMIN_OUTPUT_DIR = c2cgeoportal/static/build/admin/

JSBUILD_ADMIN_FILES = $(shell find c2cgeoportal/static/lib c2cgeoportal/static/adminapp -name "*.js" -print)
JSBUILD_ADMIN_CONFIG = jsbuild/app.cfg
JSBUILD_ADMIN_OUTPUT_FILES = $(addprefix $(ADMIN_OUTPUT_DIR),admin.js)
JSBUILD_ARGS = $(if ifeq($(DEVELOPPEMENT), ‘TRUE’),-u,)

CSS_ADMIN_FILES = c2cgeoportal/static/adminapp/css/admin.css c2cgeoportal/static/lib/openlayers/theme/default/style.css c2cgeoportal/static/lib/checkboxtree-r253/jquery.checkboxtree.css
CSS_ADMIN_OUTPUT = c2cgeoportal/static/build/admin/admin.css

VALIDATE_PY_FOLDERS = c2cgeoportal/*.py c2cgeoportal/lib c2cgeoportal/scripts c2cgeoportal/views
VALIDATE_PY_TEST_FOLDERS = c2cgeoportal/tests

SPHINX_FILES = $(shell find doc -name "*.rst" -print)

PO_FILES = $(shell find c2cgeoportal/locale -name "*.po" -print)
MO_FILES = $(addsuffix .mo,$(basename $(PO_FILES)))
SRC_FILES = $(shell ls -1 c2cgeoportal/*.py) \
	$(shell find c2cgeoportal/lib -name "*.py" -print) \
	$(shell find c2cgeoportal/views -name "*.py" -print) \
	$(shell find c2cgeoportal/scripts -name "*.py" -print)

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Main targets:"
	@echo
	@echo "- build 		Build and configure the project"
	@echo "- buildall	Build, check and test the project"
	@echo "- doc 		Build the project documentation"
	@echo "- tests 		Perform a number of tests on the code"
	@echo "- checks		Perform a number of checks on the code"
	@echo "- clean 		Remove generated files"
	@echo "- cleanall 	Remove all the build artefacts"

.PHONY: build
build: $(MAKO_FILES:.mako=) \
		c2c-egg \
		$(JSBUILD_ADMIN_OUTPUT_FILES) \
		$(CSS_ADMIN_OUTPUT) \
		$(MO_FILES)

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
	rm -rf c2cgeoportal/static/build
	rm -f $(MAKO_FILES:.mako=)

.PHONY: cleanall
cleanall: clean
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
		--copyright-regexp="Copyright \(c\) [0-9\-]*$(shell date +%Y), Camptocamp SA"
	find $(VALIDATE_PY_TEST_FOLDERS) -name \*.py | xargs .build/venv/bin/flake8 --ignore=E501


# Templates

$(MAKO_FILES:.mako=): .build/venv/bin/c2c-template ${VARS_DEPENDS}

%: %.mako
	$(C2C_TEMPLATE_CMD) --engine template --files $<

c2cgeoportal/locale/c2cgeoportal.pot: $(SRC_FILES) .build/dev-requirements.timestamp
	.build/venv/bin/pot-create -c lingua.cfg -o $@ $(SRC_FILES)
	# removes the always changed date line
	sed -i '/^"POT-Creation-Date: /d' $@
	sed -i '/^"PO-Revision-Date: /d' $@

c2cgeoportal/locale/%/LC_MESSAGES/c2cgeoportal.po: c2cgeoportal/locale/c2cgeoportal.pot .build/dev-requirements.timestamp
	touch $@
	msgmerge --update $@ $<

%.mo: %.po
	msgfmt -o $@ $<
	touch $@

.build/venv/bin/flake8: .build/dev-requirements.timestamp

.build/venv/bin/c2c-template: .build/dev-requirements.timestamp

.build/venv/bin/jsbuild: .build/dev-requirements.timestamp

.build/venv/bin/cssmin: .build/dev-requirements.timestamp

.build/dev-requirements.timestamp: .build/venv.timestamp dev-requirements.txt
	.build/venv/bin/pip install --trusted-host pypi.camptocamp.net -r dev-requirements.txt
	touch $@

.build/venv.timestamp:
	mkdir -p $(dir $@)
	virtualenv --setuptools --no-site-packages .build/venv
	.build/venv/bin/pip install \
		--index-url http://pypi.camptocamp.net/pypi \
		'pip>=6' 'setuptools>=12'
	touch $@

.build/requirements.timestamp: .build/venv.timestamp setup.py \
		requirements.txt
	$(PIP_CMD) $(PIP_INSTALL_ARGS) -r requirements.txt $(PIP_REDIRECT)
	touch $@

$(JSBUILD_ADMIN_OUTPUT_FILES): $(JSBUILD_ADMIN_FILES) $(JSBUILD_ADMIN_CONFIG)
	mkdir -p $(dir $@)
	.build/venv/bin/jsbuild $(JSBUILD_ADMIN_CONFIG) $(JSBUILD_ARGS) -j $(notdir $@) -o $(ADMIN_OUTPUT_DIR)

$(CSS_ADMIN_OUTPUT): .build/venv/bin/cssmin
	mkdir -p $(dir $@)
ifeq ($(DEVELOPPEMENT), ‘TRUE’)
	cat $(CSS_ADMIN_FILES) > $(CSS_ADMIN_OUTPUT)
else
	cat $(CSS_ADMIN_FILES) | .build/venv/bin/cssmin > $(CSS_ADMIN_OUTPUT)
endif
