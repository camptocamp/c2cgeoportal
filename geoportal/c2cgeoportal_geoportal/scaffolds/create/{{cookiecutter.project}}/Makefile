PROJECT_PUBLIC_URL=https://example.camptocamp.com/
PACKAGE={{cookiecutter.package}}
LANGUAGES=en fr de it

.PHONY: update-po-url
update-po-url:
	curl $(PROJECT_PUBLIC_URL)locale.pot > geoportal/${PACKAGE}_geoportal/locale/${PACKAGE}_geoportal-client${SUFFIX}.pot
	docker-compose run --rm -T tools update-po-only `id --user` `id --group` $(LANGUAGES)

.PHONY: update-po
update-po:
	docker-compose exec -T tools sh -c "USER_ID=`id --user` GROUP_ID=`id --group` make -C geoportal update-po"
