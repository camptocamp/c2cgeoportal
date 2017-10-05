# This file is used to finalise non Docker production environment

OPERATING_SYSTEM ?= LINUX
INSTANCE_ID ?= $(shell python -c 'print(__import__("yaml").load(open("config.yaml").read())["vars"]["instanceid"])')

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
PRINT_EXTRA_LIBS += \
	print/WEB-INF/lib/jasperreports-functions-$(JASPERREPORTS_VERSION).jar \
	print/WEB-INF/lib/joda-time-1.6.jar \
	print/WEB-INF/lib/postgresql-9.3-1102.jdbc41.jar
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
		config.yaml \
		.build/venv \
		development.ini production.ini
	$(PRERULE_CMD)
	$(APACHE_GRACEFUL)
	touch $@

# Print

.PHONY: print
print: $(PRINT_OUTPUT)/$(PRINT_WAR)

print/print-servlet.war: CONST_print_url
	$(PRERULE_CMD)
	curl --max-redirs 0 --location --output $@ $(shell cat $<)

$(PRINT_OUTPUT)/$(PRINT_WAR): $(PRINT_REQUIREMENT)
	$(PRERULE_CMD)
ifeq ($(OPERATING_SYSTEM), WINDOWS)
	mkdir -p print/tmp
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

print/WEB-INF/lib/jasperreports-functions-$(JASPERREPORTS_VERSION).jar:
	$(PRERULE_CMD)
	mkdir -p $(dir $@)
	curl --location --output $@ http://central.maven.org/maven2/net/sf/jasperreports/jasperreports/$(JASPERREPORTS_VERSION)/jasperreports-$(JASPERREPORTS_VERSION).jar
	unzip -t -q $@

print/WEB-INF/lib/joda-time-1.6.jar:
	$(PRERULE_CMD)
	mkdir -p $(dir $@)
	curl --max-redirs 0 --location --output $@ http://central.maven.org/maven2/joda-time/joda-time/1.6/joda-time-1.6.jar
	unzip -t -q $@

print/WEB-INF/lib/postgresql-9.3-1102.jdbc41.jar:
	$(PRERULE_CMD)
	mkdir -p $(dir $@)
	curl --max-redirs 0 --location --output $@ https://jdbc.postgresql.org/download/postgresql-9.3-1102.jdbc41.jar
	unzip -t -q $@

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
	mkdir -p .build
	rm -rf .build/venv
	virtualenv --python=python3 .build/venv
ifeq ($(OPERATING_SYSTEM), WINDOWS)
	.build/venv/Scripts/python -m pip install `./get-pip-dependencies pyramid-closure c2cgeoportal Shapely`
	.build/venv/Scripts/python -m pip install wheels/Shapely-1.5.13-cp27-none-win32.whl
else
	.build/venv/bin/python -m pip install `./get-pip-dependencies pyramid-closure c2cgeoportal GDAL`
endif
	./docker-run cp -r /opt/c2cgeoportal c2cgeoportal
	.build/venv/bin/python -m pip install https://github.com/camptocamp/pyramid_closure/archive/23b45f7989cf471dce46dabb8516537bae0a2789.zip#egg=pyramid_closure
	.build/venv/bin/python -m pip install -e c2cgeoportal
	.build/venv/bin/python -m pip install -e .
