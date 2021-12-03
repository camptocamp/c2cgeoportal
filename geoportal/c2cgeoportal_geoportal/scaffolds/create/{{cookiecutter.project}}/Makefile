.PHONY: update-po
update-po:
	docker-compose exec -T tools sh -c "USER_ID=`id --user` GROUP_ID=`id --group` make -C geoportal update-po"
