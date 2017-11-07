# This file is used to finalise non Docker production environment

OPERATING_SYSTEM ?= LINUX
INSTANCE_ID ?= $(shell python -c 'print(__import__("yaml").load(open("geoportal/config.yaml").read())["vars"]["instanceid"])')

ifeq ($(OPERATING_SYSTEM), WINDOWS)
FIND ?= find.exe
else
FIND ?= find
endif

# Print

PRINT_WAR ?= print-$(INSTANCE_ID).war
PRINT_OUTPUT ?= /srv/tomcat/tomcat1/webapps
JASPERREPORTS_VERSION ?= 6.1.1
TOMCAT_SERVICE_COMMAND ?= sudo /etc/init.d/tomcat-tomcat1
ifneq ($(TOMCAT_SERVICE_COMMAND),)
TOMCAT_STOP_COMMAND ?= $(TOMCAT_SERVICE_COMMAND) stop
TOMCAT_START_COMMAND ?= $(TOMCAT_SERVICE_COMMAND) start
endif
PRINT_OUTPUT_WAR = $(PRINT_OUTPUT)/$(PRINT_WAR)
PRINT_INPUT += print-apps WEB-INF
PRINT_REQUIREMENT += $(PRINT_EXTRA_LIBS) \
	print/WEB-INF/classes/logback.xml \
	print/WEB-INF/classes/mapfish-spring-application-context-override.xml \
	print/print-servlet.war \
	$(shell $(FIND) print/print-apps)

# Apache

APACHE_VHOST ?= $(PACKAGE)
APACHE_CONF_DIR ?= /var/www/vhosts/$(APACHE_VHOST)/conf
APACHE_GRACEFUL ?= sudo /usr/sbin/apache2ctl graceful


.PHONY: help
help:
	@echo  "Usage: make <target>"
	@echo
	@echo  "Main targets:"
	@echo
	@echo  "- build			Build and configure the project"
	@echo  "- clean-all		Remove all the build artefacts"

.PHONY: clean-all
clean-all:
	rm -f $(APACHE_CONF_DIR)/$(INSTANCE_ID).conf
	$(TOMCAT_OUTPUT_CMD_PREFIX) rm -rf $(PRINT_OUTPUT)/$(PRINT_WAR)
	$(TOMCAT_OUTPUT_CMD_PREFIX) rm -rf $(PRINT_OUTPUT)/$(PRINT_WAR:.war=) 2> /dev/null || true
	rm -rf .build

.PHONY: build
build: $(PRINT_OUTPUT_WAR) \
	.build/apache.timestamp

# Apache

$(APACHE_CONF_DIR)/$(INSTANCE_ID).conf:
	$(PRERULE_CMD)
	echo "Include $(shell pwd)/apache/*.conf" > $@

.build/apache.timestamp: \
		$(APACHE_CONF_DIR)/$(INSTANCE_ID).conf \
		geoportal/config.yaml \
		.build/venv \
		geoportal/development.ini geoportal/production.ini
	$(PRERULE_CMD)
	$(APACHE_GRACEFUL)
	touch $@

# Print

.PHONY: print
print: $(PRINT_OUTPUT)/$(PRINT_WAR)

print/print-servlet.war: print_url
	$(PRERULE_CMD)
	curl --max-redirs 0 --location --output $@ $(shell cat $<)

$(PRINT_OUTPUT)/$(PRINT_WAR): $(PRINT_REQUIREMENT) print/print-servlet.war
	$(PRERULE_CMD)
ifeq ($(OPERATING_SYSTEM), WINDOWS)
	mkdir --parent print/tmp
	cp print/print-servlet.war print/tmp/$(PRINT_WAR)
	zip -d print/tmp/$(PRINT_WAR) print-apps/
	cd print && jar -uf tmp/$(PRINT_WAR) $(PRINT_INPUT)
else
	cp print/print-servlet.war /tmp/$(PRINT_WAR)
	zip -d /tmp/$(PRINT_WAR) print-apps/
	cd print && jar -uf /tmp/$(PRINT_WAR) $(PRINT_INPUT)
	chmod g+r,o+r /tmp/$(PRINT_WAR)
endif

ifneq ($(TOMCAT_STOP_COMMAND),)
	$(TOMCAT_STOP_COMMAND)
endif
	$(TOMCAT_OUTPUT_CMD_PREFIX) rm -f $(PRINT_OUTPUT)/$(PRINT_WAR)
	$(TOMCAT_OUTPUT_CMD_PREFIX) rm -rf $(PRINT_OUTPUT)/$(PRINT_WAR:.war=)
ifeq ($(OPERATING_SYSTEM), WINDOWS)
	mv print/tmp/$(PRINT_WAR) $(PRINT_OUTPUT)
	cd print && rm -fd tmp
else
	$(TOMCAT_OUTPUT_CMD_PREFIX) cp /tmp/$(PRINT_WAR) $(PRINT_OUTPUT)
	rm -f /tmp/$(PRINT_WAR)
endif
ifneq ($(TOMCAT_START_COMMAND),)
	$(TOMCAT_START_COMMAND)
endif

# Deploy branch

.PHONY: deploy-branch
deploy-branch:
	@read -p "Are you sure to deploy the branch in $(DEPLOY_BRANCH_DIR)/$(GIT_BRANCH) (Y/n)?" RESP; RESP=`echo $$RESP | tr '[:upper:]' '[:lower:]'`; /usr/bin/test "$$RESP" == "y" -o "$$RESP" == "yes" -o "$$RESP" == ""
	rm -f $(APACHE_CONF_DIR)/$(GIT_BRANCH).conf
	rm -rf $(DEPLOY_BRANCH_DIR)/$(GIT_BRANCH)
	mkdir --parents $(DEPLOY_BRANCH_DIR)/$(GIT_BRANCH)
	git clone $(GIT_REMOTE_URL) -b $(GIT_BRANCH) $(DEPLOY_BRANCH_DIR)/$(GIT_BRANCH)
	cd $(DEPLOY_BRANCH_DIR)/$(GIT_BRANCH); INSTANCE_ID=$(GIT_BRANCH) APACHE_CONF_DIR=$(APACHE_CONF_DIR) APACHE_ENTRY_POINT=/$(GIT_BRANCH)/ $(MAKE) -f $(DEPLOY_BRANCH_MAKEFILE) build
	@echo Now open $(DEPLOY_BRANCH_BASE_URL)/$(GIT_BRANCH)

.PHONY: remove-branch
remove-branch:
	rm -f $(APACHE_CONF_DIR)/$(GIT_BRANCH).conf
	rm -fr $(DEPLOY_BRANCH_DIR)/$(GIT_BRANCH)
	$(APACHE_GRACEFUL)

# Extract

.build/venv:
	mkdir --parent .build
	rm -rf .build/venv
	virtualenv --python=python3 --system-site-packages .build/venv
ifeq ($(OPERATING_SYSTEM), WINDOWS)
	.build/venv/Scripts/python -m pip install `./get-pip-dependencies pyramid-closure c2cgeoportal Shapely`
	.build/venv/Scripts/python -m pip install wheels/Shapely-1.5.13-cp27-none-win32.whl
else
	# FIXME c2cgeoform
	.build/venv/bin/python -m pip install `./get-pip-dependencies pyramid-closure c2cgeoportal-commons c2cgeoportal-geoportal GDAL c2cgeoform`
endif
	./docker-run cp -r /opt/c2cgeoportal_commons c2cgeoportal_commons
	./docker-run cp -r /opt/c2cgeoportal_geoportal c2cgeoportal_geoportal
	.build/venv/bin/python -m pip install https://github.com/camptocamp/c2cgeoform/archive/87a4191ef3330b76497bd009e9c0220cbc73c625.zip#egg=c2cgeoform
	.build/venv/bin/python -m pip install https://github.com/camptocamp/pyramid_closure/archive/23b45f7989cf471dce46dabb8516537bae0a2789.zip#egg=pyramid_closure
	.build/venv/bin/python -m pip install --editable=c2cgeoportal_commons --editable=c2cgeoportal_geoportal
	.build/venv/bin/python -m pip install --editable=commons --editable=geoportal
