FROM camptocamp/postgis:9.5
MAINTAINER Camptocamp "info@camptocamp.com"

ADD *.sql *.csv *.sh /docker-entrypoint-initdb.d/
