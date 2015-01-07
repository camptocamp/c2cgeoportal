SITE_PACKAGES = $(shell .build/venv/bin/python -c "import distutils; print(distutils.sysconfig.get_python_lib())" 2> /dev/null)

TEMPLATE_EXCLUDE = MANIFEST.in .build .eggs c2cgeoportal/scaffolds c2cgeoportal/tests/testegg
FIND_OPTS = $(foreach ELEM, $(TEMPLATE_EXCLUDE),-path ./$(ELEM) -prune -o) -type f
TEMPLATE_FILES = $(shell find $(FIND_OPTS) -name "*.in" -print)
VARS_FILE ?= vars.yaml
VARS_FILES += vars.yaml
C2C_TEMPLATE_CMD = .build/venv/bin/c2c-template --vars $(VARS_FILE)

DEVELOPPEMENT ?= FALSE

JSBUILD_MAIN_FILES = $(shell find c2cgeoportal/static/lib c2cgeoportal/static/adminapp -name "*.js" -print)
JSBUILD_MAIN_CONFIG = jsbuild/app.cfg
JSBUILD_MAIN_OUTPUT_DIR = c2cgeoportal/static/build/admin/
JSBUILD_MAIN_OUTPUT_FILES = $(addprefix $(JSBUILD_MAIN_OUTPUT_DIR),admin.js)
JSBUILD_ARGS = $(if ifeq($(DEVELOPPEMENT), ‘TRUE’),-u,)

CSS_BASE_FILES = c2cgeoportal/static/adminapp/css/admin.css c2cgeoportal/static/lib/openlayers/theme/default/style.css c2cgeoportal/static/lib/checkboxtree-r253/jquery.checkboxtree.css
CSS_BASE_OUTPUT = c2cgeoportal/static/build/admin/admin.css

VALIDATE_PY_FOLDERS = c2cgeoportal/*.py c2cgeoportal/lib c2cgeoportal/scripts c2cgeoportal/views
VALIDATE_PY_TEST_FOLDERS = c2cgeoportal/tests

SPHINX_FILES = $(shell find doc -name "*.rst" -print)

PO_FILES = $(shell find c2cgeoportal/locale -name "*.po" -print)
MO_FILES = $(addsuffix .mo,$(basename $(PO_FILES)))
SRC_FILES = $(shell find c2cgeoportal -name "*.py" -print)

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
build: $(TEMPLATE_FILES:.in=) \
		c2c-egg \
		$(JSBUILD_MAIN_OUTPUT_FILES) \
		$(CSS_BASE_OUTPUT) \
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
	rm -f $(TEMPLATE_FILES:.in=)

.PHONY: cleanall
cleanall: clean
	rm -rf .build

.PHONY: c2c-egg
c2c-egg: $(SITE_PACKAGES)/c2cgeoportal.egg-link

doc/_build/html:
	mkdir $@

.build/sphinx.timestamp: .build/dev-requirements.timestamp doc/_build/html $(SPHINX_FILES)
	doc/build.sh
	touch $@

.PHONY: nose
nose: .build/dev-requirements.timestamp $(TEMPLATE_FILES:.in=)
	.build/venv/bin/python setup.py nosetests

.PHONY: flake8
flake8: .build/venv/bin/flake8
	# E712 is not compatible with SQLAlchemy
	find $(VALIDATE_PY_FOLDERS) -name \*.py | xargs .build/venv/bin/flake8 --ignore=E712 --max-complexity=20 --max-line-length=100
	find $(VALIDATE_PY_TEST_FOLDERS) -name \*.py | xargs .build/venv/bin/flake8 --ignore=E501

$(TEMPLATE_FILES:.in=): $(TEMPLATE_FILES) .build/venv/bin/c2c-template ${VARS_FILES}
	$(C2C_TEMPLATE_CMD) --engine template --files $@.in

c2cgeoportal/locale/c2cgeoportal.pot: $(SRC_FILES) .build/dev-requirements.timestamp
	.build/venv/bin/python setup.py extract_messages

$(PO_FILES): c2cgeoportal/locale/c2cgeoportal.pot .build/dev-requirements.timestamp
	.build/venv/bin/python setup.py update_catalog

c2cgeoportal/locale/fr/LC_MESSAGES/c2cgeoportal.mo: ./c2cgeoportal/locale/fr/LC_MESSAGES/c2cgeoportal.po .build/dev-requirements.timestamp
	.build/venv/bin/pybabel compile -D c2cgeoportal -d c2cgeoportal/locale -l fr

c2cgeoportal/locale/en/LC_MESSAGES/c2cgeoportal.mo: ./c2cgeoportal/locale/en/LC_MESSAGES/c2cgeoportal.po .build/dev-requirements.timestamp
	.build/venv/bin/pybabel compile -D c2cgeoportal -d c2cgeoportal/locale -l en

c2cgeoportal/locale/de/LC_MESSAGES/c2cgeoportal.mo: ./c2cgeoportal/locale/de/LC_MESSAGES/c2cgeoportal.po .build/dev-requirements.timestamp
	.build/venv/bin/pybabel compile -D c2cgeoportal -d c2cgeoportal/locale -l de

.build/venv/bin/flake8: .build/dev-requirements.timestamp

.build/venv/bin/c2c-template: .build/dev-requirements.timestamp

.build/venv/bin/jsbuild: .build/dev-requirements.timestamp

.build/venv/bin/cssmin: .build/dev-requirements.timestamp

.build/dev-requirements.timestamp: .build/venv.timestamp dev-requirements.txt
	.build/venv/bin/pip install -r dev-requirements.txt
	touch $@

.build/venv.timestamp:
	mkdir -p $(dir $@)
	virtualenv --no-site-packages .build/venv
	touch $@

$(SITE_PACKAGES)/c2cgeoportal.egg-link: .build/venv.timestamp setup.py \
		requirements.txt
	.build/venv/bin/pip install -r requirements.txt
	touch -m $@ | true

$(JSBUILD_MAIN_OUTPUT_FILES): $(JSBUILD_MAIN_FILES) $(JSBUILD_MAIN_CONFIG)
	.build/venv/bin/jsbuild $(JSBUILD_MAIN_CONFIG) $(JSBUILD_ARGS) -j $(notdir $@) -o $(JSBUILD_MAIN_OUTPUT_DIR)

$(CSS_BASE_OUTPUT): .build/venv/bin/cssmin
ifeq ($(DEVELOPPEMENT), ‘TRUE’)
	cat $(CSS_BASE_FILES) > $(CSS_BASE_OUTPUT)
else
	cat $(CSS_BASE_FILES) | .build/venv/bin/cssmin > $(CSS_BASE_OUTPUT)
endif
