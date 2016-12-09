INSTANCE_ID = travis

TILECLOUD_CHAIN = FALSE

REQUIREMENTS += ${TRAVIS_FOLDER}

PRINT_OUTPUT = /var/lib/tomcat7/webapps

PIP_CMD = ${TRAVIS_FOLDER}/travis/pip-project.sh

TOMCAT_SERVICE_COMMAND =
APACHE_CONF_DIR = /etc/apache2/sites-enabled

VARS_FILE = vars_travis.yaml

include testgeomapfish.mk
