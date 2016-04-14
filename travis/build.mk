INSTANCE_ID = travis

MOBILE = FALSE
TILECLOUD_CHAIN = FALSE

REQUIREMENTS += -e ${TRAVIS_FOLDER}

PRINT_OUTPUT = /var/lib/tomcat7/webapps

PIP_CMD = ${TRAVIS_FOLDER}/travis/pip.sh

TOMCAT_SERVICE_COMMAND =
APACHE_CONF_DIR = /etc/apache2/sites-enabled

VARS_FILE = vars_travis.yaml

include testgeomapfish.mk
