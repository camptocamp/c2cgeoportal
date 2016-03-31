INSTANCE_ID = test

MOBILE = FALSE
TILECLOUD_CHAIN = FALSE

PRINT_OUTPUT = /var/lib/tomcat7/webapps

PIP_CMD = /home/travis/build/${TRAVIS_REPO_SLUG}/travis/pip.sh

TOMCAT_SERVICE_COMMAND =
APACHE_CONF_DIR = /etc/apache2/sites-enabled/

VARS_FILE = vars_travis.yaml

include testgeomapfish.mk
