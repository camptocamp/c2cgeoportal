INSTANCE_ID = test

MOBILE = FALSE
#NGEO = TRUE
TILECLOUD_CHAIN = FALSE

REQUIREMENTS += -e /home/travis/build/camptocamp/c2cgeoportal
PRINT_OUTPUT = /var/lib/tomcat7/webapps

include test.mk
