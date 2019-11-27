VALIDATE_PY_FOLDERS = commons admin \
	geoportal/setup.py \
	geoportal/c2cgeoportal_geoportal/*.py \
	geoportal/c2cgeoportal_geoportal/lib \
	geoportal/c2cgeoportal_geoportal/scripts \
	geoportal/c2cgeoportal_geoportal/views
VALIDATE_TEMPLATE_PY_FOLDERS = geoportal/c2cgeoportal_geoportal/scaffolds
VALIDATE_PY_TEST_FOLDERS = geoportal/tests

.PHONY: checks
checks: flake8 pylint bandit black isort additionallint

.PHONY: flake8
flake8:
	MYPYPATH=/opt/c2cwsgiutils flake8 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"
	grep --recursive --files-with-match '/usr/bin/env python' | grep -v checks.mk | grep -v node_modules | \
		xargs flake8 \
		--copyright-regexp="Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?$(shell date +%Y), Camptocamp SA"

.PHONY: pylint
pylint:
	pylint --errors-only commons/c2cgeoportal_commons
	pylint --errors-only commons/tests
	pylint --errors-only --disable=assignment-from-no-return geoportal/c2cgeoportal_geoportal
	pylint --errors-only geoportal/tests
	pylint --errors-only admin/c2cgeoportal_admin
	pylint --errors-only admin/tests

.PHONY: bandit
bandit:
	bandit --recursive -ll .

.PHONY: black
black:
	black --line-length=110 --target-version py37 --exclude=.*/node_modules/.* --check --diff .

.PHONY: black-fix
black-fix:
	black --line-length=110 --target-version py37 --exclude=.*/node_modules/.* /src

.PHONY: isort
isort:
	isort --check-only --diff --multi-line=3 --trailing-comma \
	--force-grid-wrap=0 --use-parentheses --line-width=110 --force-sort-within-sections \
	--recursive commons geoportal admin/c2cgeoportal_admin admin/tests bin docker

.PHONY: isort-fix
isort-fix:
	isort --apply --multi-line=3 --trailing-comma \
	--force-grid-wrap=0 --use-parentheses --line-width=110 --force-sort-within-sections \
	--recursive commons geoportal admin/c2cgeoportal_admin admin/tests bin docker

.PHONY: additionallint
additionallint:
	# Verify that we don't directly use the CI project name in the scaffolds
	if [ "`grep --recursive testgeomapfish geoportal/c2cgeoportal_geoportal/scaffolds`" != "" ]; \
	then \
		echo "ERROR: You still have a testgeomapfish in one of your scaffolds"; \
		grep --recursive testgeomapfish geoportal/c2cgeoportal_geoportal/scaffolds; \
		false; \
	fi
