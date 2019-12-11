VALIDATE_PY_FOLDERS = commons admin \
	geoportal/setup.py \
	geoportal/c2cgeoportal_geoportal/*.py \
	geoportal/c2cgeoportal_geoportal/lib \
	geoportal/c2cgeoportal_geoportal/scripts \
	geoportal/c2cgeoportal_geoportal/views
VALIDATE_TEMPLATE_PY_FOLDERS = geoportal/c2cgeoportal_geoportal/scaffolds
VALIDATE_PY_TEST_FOLDERS = geoportal/tests

.PHONY: checks
checks: prospector bandit black isort additionallint

.PHONY: prospector
prospector:
	prospector

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
	isort --check-only --diff --settings-path=`pwd` \
		 --recursive commons geoportal admin/c2cgeoportal_admin admin/tests bin docker

.PHONY: isort-fix
isort-fix:
	isort --apply --settings-path=`pwd` \
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
