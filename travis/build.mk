INSTANCE_ID = test

MOBILE = FALSE
#NGEO = TRUE
TILECLOUD_CHAIN = FALSE

REQUIREMENTS += -e /home/travis/build/camptocamp/c2cgeoportal
PRINT_OUTPUT = /var/lib/tomcat7/webapps

PIP_CMD = /home/travis/build/camptocamp/c2cgeoportal/travis/pip.sh

include test.mk
