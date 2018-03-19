PRINT_OUTPUT = /var/lib/tomcat7/webapps
TOMCAT_SERVICE_COMMAND = sudo /etc/init.d/tomcat7
APACHE_CONF_DIR = /etc/apache2/sites-enabled
VARS_FILE = vars_travis.yaml
TILECLOUD_CHAIN = FALSE

include testgeomapfish.mk
