include Makefile  # travis/create-new-project.s need $MAJOR_VERSION

TESTAPP=${HOME}/workspace/testgeomapfishapp
SCAFFOLDS_PATH=${PWD}/geoportal/c2cgeoportal_geoportal/scaffolds

.PHONY: testapp
testapp: \
		${SCAFFOLDS_PATH}/testapp/ssl/localhost.pem  \
		${SCAFFOLDS_PATH}/testapp/+dot+dockerignore  \
		${SCAFFOLDS_PATH}/testapp/Dockerfile  \
		${SCAFFOLDS_PATH}/testapp/front/haproxy.cfg.tmpl \

	./docker-run make docker-build-test
	./docker-run make docker-build-testdb
	./docker-run make docker-build-testexternaldb

	DOCKER_RUN_ARGS="--env=C2CGEOPORTAL_PATH=${PWD} --volume=${PWD}/geoportal/c2cgeoportal_geoportal:/opt/c2cgeoportal_geoportal/c2cgeoportal_geoportal" \
	SCAFFOLDS="c2cgeoportal_create c2cgeoportal_update c2cgeoportal_testapp" \
	MAKEFILE=testapp.mk \
	C2CGEOPORTAL_PATH=${PWD} \
	travis/create-new-project.sh ${HOME}/workspace testgeomapfishapp

	# Allow eval_templates to write in source folder
	chmod -R o+w ${TESTAPP}/geoportal/testgeomapfishapp_geoportal/static-ngeo/build

	cd ${TESTAPP} && docker-compose up -d

	@echo You can open http://localhost:8080/ in your favorite browser


# Switch to HTTPS

${SCAFFOLDS_PATH}/testapp/ssl/localhost.pem:
	mkdir -p $(dir $@)
	openssl genrsa -out $(dir $@)/rsa.key 1024
	openssl req -new -key $(dir $@)/rsa.key -out $(dir $@)/localhost.crt \
		-subj "/C=CH/ST=Switzerland/L=Lausanne/O=Camptocamp SA/OU=Geospatial division/CN=localhost/emailAddress=info@camptocamp.com"
	cat $(dir $@)/localhost.crt $(dir $@)/rsa.key | tee $@

${SCAFFOLDS_PATH}/testapp/+dot+dockerignore: ${SCAFFOLDS_PATH}/create/+dot+dockerignore
	cp $< $@
	echo '!ssl' >> $@

${SCAFFOLDS_PATH}/testapp/Dockerfile: ${SCAFFOLDS_PATH}/create/Dockerfile
	cp $< $@
	echo "COPY ssl/localhost.pem /etc/ssl/localhost.pem" >> $@

${SCAFFOLDS_PATH}/testapp/front/haproxy.cfg.tmpl:
	cp ${SCAFFOLDS_PATH}/create/front/haproxy.cfg.tmp ${SCAFFOLDS_PATH}/testapp/front/haproxy.cfg.tmp
	sed -i "s_bind :80_bind *:443 ssl crt /etc/ssl/localhost.pem_g" ${TESTAPP}/front/haproxy.cfg.tmpl
