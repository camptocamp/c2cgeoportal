include Makefile  # travis/create-new-project.s need $MAJOR_VERSION

.PHONY: test_app
test_app:
	./docker-run make docker-build-test
	./docker-run make docker-build-testdb
	./docker-run make docker-build-testexternaldb

	DOCKER_RUN_ARGS="--env=C2CGEOPORTAL_PATH=$PWD --volume=$PWD/geoportal/c2cgeoportal_geoportal:/opt/c2cgeoportal_geoportal/c2cgeoportal_geoportal" \
	SCAFFOLDS="c2cgeoportal_create c2cgeoportal_update c2cgeoportal_testapp" \
	MAKEFILE=testapp.mk \
	C2CGEOPORTAL_PATH=${PWD} \
	travis/create-new-project.sh ${HOME}/workspace testgeomapfishapp

	chmod -R o+w ${HOME}/workspace/testgeomapfishapp/geoportal/testgeomapfishapp_geoportal/static-ngeo/build/

	cd ${HOME}/workspace/testgeomapfishapp && docker-compose up -d

	@echo You can open http://localhost:8080/ in your favorite browser
