INSTANCE_ID = test

MOBILE = FALSE
#NGEO = TRUE
TILECLOUD_CHAIN = FALSE

REQUIREMENTS += -e /home/travis/build/camptocamp/c2cgeoportal
PRINT_OUTPUT = /var/lib/tomcat7/webapps

PIP_CMD = /home/travis/build/camptocamp/c2cgeoportal/travis/pip.sh

TOMCAT_SERVICE_COMMAND =

# TODO remove it ...
testgeomapfish/static-ngeo/build/locale/%/testgeomapfish.json:
	mkdir -p $(dir $@)
	touch $@

include testgeomapfish.mk
