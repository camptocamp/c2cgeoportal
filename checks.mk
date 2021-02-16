VALIDATE_PY_FOLDERS = commons admin \
	geoportal/setup.py \
	geoportal/c2cgeoportal_geoportal/*.py \
	geoportal/c2cgeoportal_geoportal/lib \
	geoportal/c2cgeoportal_geoportal/scripts \
	geoportal/c2cgeoportal_geoportal/views
VALIDATE_TEMPLATE_PY_FOLDERS = geoportal/c2cgeoportal_geoportal/scaffolds
VALIDATE_PY_TEST_FOLDERS = geoportal/tests

.PHONY: checks
checks: prospector additionallint

.PHONY: prospector
prospector:
	@prospector --version
	@mypy --version
	@pylint --version --rcfile=/dev/null
	@echo pyflakes $(shell pyflakes --version)
	prospector

.PHONY: additionallint
additionallint:
	# Verify that we don't directly use the CI project name in the scaffolds
	if [ "`grep --recursive testgeomapfish geoportal/c2cgeoportal_geoportal/scaffolds`" != "" ]; \
	then \
		echo "ERROR: You still have a testgeomapfish in one of your scaffolds"; \
		grep --recursive testgeomapfish geoportal/c2cgeoportal_geoportal/scaffolds; \
		false; \
	fi
